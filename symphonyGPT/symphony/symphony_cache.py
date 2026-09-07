import atexit
import logging
import os
import shutil
import sqlite3
from diskcache import Cache

from symphonyGPT.symphony.util import Util

_CACHE_DB_FILES = ('cache.db', 'cache.db-shm', 'cache.db-wal', 'cache.db-journal')
_CACHE_SIDECARS = ('cache.db-shm', 'cache.db-wal', 'cache.db-journal')


def _is_corrupt_cache_error(exc):
    message = str(exc).lower()
    return (
        'malformed' in message
        or 'not a database' in message
        or 'disk i/o error' in message
        or 'protocol' in message
    )


def _remove_named_cache_files(cache_dir, names):
    for name in names:
        path = os.path.join(cache_dir, name)
        if os.path.lexists(path):
            try:
                os.unlink(path)
            except OSError as exc:
                logging.warning("Failed to remove cache file %s: %s", path, exc)


def _remove_cache_db_files(cache_dir):
    _remove_named_cache_files(cache_dir, _CACHE_DB_FILES)

# default cache expiration time
TWO_DAYS=2*60*60*24 # 2 days in seconds

DEFAULT_CACHE_DIR = "/tmp/symphonyGPT_cache"
_default_cache_dir = None


def get_default_cache_dir():
    if _default_cache_dir:
        return _default_cache_dir
    env_dir = os.environ.get("SYMPHONYGPT_CACHE_DIR")
    if env_dir:
        return env_dir
    return DEFAULT_CACHE_DIR


def set_default_cache_dir(cache_dir):
    global _default_cache_dir
    if not cache_dir:
        return
    os.makedirs(cache_dir, exist_ok=True)
    _default_cache_dir = cache_dir
    os.environ["SYMPHONYGPT_CACHE_DIR"] = cache_dir


def delete_old_cache_dirs():
    import os
    import shutil
    import time

    # Define the directory where the folders are located
    directory_path = '/tmp'

    # Define the prefix of the folders you want to delete
    folder_prefix = 'symphonyGPT_cache'

    # Define the age limit (in seconds)
    age_limit_seconds = 1 * 24 * 60 * 60  # 1 day in seconds

    # Get the current time in seconds since the epoch
    current_time = time.time()

    # List all the items in the directory
    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)

        # Check if the item is a directory
        if os.path.isdir(item_path) and item.startswith(folder_prefix):
            # Get the creation time of the folder
            creation_time = os.path.getctime(item_path)

            # Calculate the age of the folder
            folder_age = current_time - creation_time

            # Check if the folder is older than the age limit
            if folder_age > age_limit_seconds:
                # Delete the folder if it's older than 1 day
                shutil.rmtree(item_path)
                Util().debug_print(f"delete_old_cache_dirs deleted: {item_path}")


class SymphonyCache:
    def __init__(self, cache_dir=None):
        if cache_dir is not None:
            # self.cache_dir = cache_dir + "." + str(os.getpid())
            self.cache_dir = cache_dir
        else:
            self.cache_dir = get_default_cache_dir()

        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache = None
        # SHM files are machine-local lock maps. A copied cache.db-shm from another
        # OS can make SQLite treat the cache as empty or corrupt.
        try:
            self._open_cache(remove_shm=True)
        except sqlite3.DatabaseError as exc:
            if not _is_corrupt_cache_error(exc):
                raise
            self._recover_cache(exc)
        # Register the cleanup function to run on process exit
        # atexit.register(self.cleanup_cache_dir)

    def _close_cache(self):
        cache = getattr(self, "cache", None)
        if cache is None:
            return
        try:
            cache.close()
        except Exception as exc:
            logging.warning("Failed to close cache at %s: %s", self.cache_dir, exc)
        self.cache = None

    def _open_cache(self, *, remove_shm=False, sidecars_only=False, reset_files=False):
        self._close_cache()
        if reset_files:
            _remove_cache_db_files(self.cache_dir)
        elif sidecars_only:
            _remove_named_cache_files(self.cache_dir, _CACHE_SIDECARS)
        elif remove_shm:
            _remove_named_cache_files(self.cache_dir, ('cache.db-shm',))
        self.cache = Cache(self.cache_dir)

    def _recover_cache(self, exc):
        logging.warning("Retrying cache at %s after removing WAL/SHM: %s", self.cache_dir, exc)
        try:
            self._open_cache(sidecars_only=True)
            return
        except sqlite3.DatabaseError as retry_exc:
            if not _is_corrupt_cache_error(retry_exc):
                raise
            exc = retry_exc
        logging.warning("Resetting malformed cache at %s: %s", self.cache_dir, exc)
        self._open_cache(reset_files=True)

    def _run_cache_op(self, operation):
        try:
            return operation()
        except sqlite3.DatabaseError as exc:
            if not _is_corrupt_cache_error(exc):
                raise
            logging.warning("Retrying cache at %s after removing WAL/SHM: %s", self.cache_dir, exc)
            try:
                self._open_cache(sidecars_only=True)
                return operation()
            except sqlite3.DatabaseError as retry_exc:
                if not _is_corrupt_cache_error(retry_exc):
                    raise
                logging.warning("Resetting malformed cache at %s: %s", self.cache_dir, retry_exc)
                self._open_cache(reset_files=True)
                return operation()

    # Function to cleanup the cache directory
    def cleanup_cache_dir(self):
        if os.path.exists(self.cache_dir):
            # delete all files in the directory
            self.cache.clear()
            # delete the directory
            shutil.rmtree(self.cache_dir)
            Util().debug_print(f"Cache directory {self.cache_dir} has been deleted.")

    def set(self, key, value, expire_seconds=None):
        expire = expire_seconds if expire_seconds is not None else TWO_DAYS
        self._run_cache_op(lambda: self.cache.set(key, value, expire=expire))

    def get(self, key):
        def _get():
            answer = self.cache.get(key)
            if answer is None:
                return f"{key} not found"
            self.cache.touch(key, expire=TWO_DAYS)
            return answer

        return self._run_cache_op(_get)

    def touch(self, key, expire=TWO_DAYS):
        return self._run_cache_op(lambda: self.cache.touch(key, expire=expire))

    def get_all_keys(self):
        return self._run_cache_op(lambda: list(self.cache.iterkeys()))

    def delete(self, key):
        return self._run_cache_op(lambda: self.cache.delete(key, True))

    def clear(self):
        self._run_cache_op(lambda: self.cache.clear())

# test main
if __name__ == "__main__":
    symphony_cache = SymphonyCache()
    symphony_cache.set("key1", "value1")
    symphony_cache.set("key1", "valueX")
    symphony_cache = SymphonyCache()
    symphony_cache.set("key2", "value2")
    print(symphony_cache.get("key1"))