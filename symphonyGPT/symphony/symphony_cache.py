import atexit
import logging
import os
import shutil
import sqlite3
import time
from urllib.parse import quote
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
        or 'corrupt' in message
    )


def _remove_named_cache_files(cache_dir, names):
    for name in names:
        path = os.path.join(cache_dir, name)
        if os.path.lexists(path):
            try:
                os.unlink(path)
            except OSError as exc:
                logging.warning("Failed to remove cache file %s: %s", path, exc)


def reset_cache_db(cache_dir):
    _remove_named_cache_files(cache_dir, _CACHE_DB_FILES)


def _remove_cache_db_files(cache_dir):
    reset_cache_db(cache_dir)


def cache_db_path(cache_dir):
    return os.path.join(cache_dir, 'cache.db')


def _short_cache_label(cache_dir):
    path = os.path.abspath(cache_dir or "")
    parts = path.replace("\\", "/").rstrip("/").split("/")
    if parts[-1:] == ["cache"] and len(parts) >= 2:
        return "/".join(parts[-2:])
    if len(parts) >= 2 and parts[-2] == "cache":
        return "/".join(parts[-2:])
    return parts[-1] if parts else path


def _notify_cache_event(cache_dir, message, *, level=logging.WARNING, flash=True):
    text = str(message).strip()
    if not text:
        return
    logging.log(level, text)
    if not flash:
        return
    flash_text = text.replace("\n", " ").strip()
    try:
        print(f"flash_message: {flash_text}", flush=True)
    except Exception:
        pass
    try:
        from flask import current_app, has_app_context, has_request_context, session
        if not has_app_context():
            return
        socketio = current_app.config.get("socketio")
        if socketio is None:
            return
        payload = {"message": flash_text, "timeout": 20000, "clear_wait": True}
        session_id = session.get("session_id") if has_request_context() else None
        if session_id:
            socketio.emit(f"flash_message.{session_id}", payload)
            return
        store = current_app.config.get("subprocess_store") or {}
        for sid in list(store.keys()):
            socketio.emit(f"flash_message.{sid}", payload)
    except Exception:
        logging.debug("Cache flash notify skipped for %s", cache_dir, exc_info=True)


def cache_db_health_issue(cache_dir, immutable=False):
    db_path = cache_db_path(cache_dir)
    if not os.path.isfile(db_path):
        return None
    quoted = quote(os.path.abspath(db_path), safe="/")
    params = "mode=ro"
    if immutable:
        params += "&immutable=1&nolock=1"
    try:
        con = sqlite3.connect(f"file:{quoted}?{params}", uri=True, timeout=5.0)
        try:
            row = con.execute("PRAGMA quick_check").fetchone()
            if row and str(row[0]).lower() == "ok":
                return None
            return str(row[0]) if row else "quick_check failed"
        finally:
            con.close()
    except sqlite3.Error as exc:
        return str(exc)


def is_cache_db_healthy(cache_dir, immutable=False):
    issue = cache_db_health_issue(cache_dir, immutable=immutable)
    if issue:
        logging.warning("Cache health check failed at %s: %s", cache_db_path(cache_dir), issue)
        return False
    return True

# default cache expiration time
TWO_DAYS = 2 * 60 * 60 * 24  # 2 days in seconds
_USE_DEFAULT_EXPIRE = object()
CACHE_EXPIRE_FILE = "cache_expire"
CACHE_EXPIRE_NEVER = "Never"
CACHE_EXPIRE_OPTIONS = (
    (CACHE_EXPIRE_NEVER, None),
    ("1 hour", 60 * 60),
    ("1 day", 24 * 60 * 60),
    ("2 days", 2 * 24 * 60 * 60),
    ("7 days", 7 * 24 * 60 * 60),
    ("30 days", 30 * 24 * 60 * 60),
    ("90 days", 90 * 24 * 60 * 60),
)
_CACHE_EXPIRE_BY_LABEL = {label.lower(): seconds for label, seconds in CACHE_EXPIRE_OPTIONS}

DEFAULT_CACHE_DIR = "/tmp/symphonyGPT_cache"
_default_cache_dir = None
_expire_file_cache = (None, None, None)  # path, mtime, seconds


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


def parse_expire_label(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value) if value > 0 else None

    text = str(value).strip()
    if not text:
        return None

    lowered = text.lower()
    if lowered in _CACHE_EXPIRE_BY_LABEL:
        return _CACHE_EXPIRE_BY_LABEL[lowered]
    if lowered in ("none", "off"):
        return None

    try:
        seconds = float(text)
    except ValueError:
        raise ValueError(f"Unknown cache expiration: {value}") from None
    return int(seconds) if seconds > 0 else None


def format_expire_env(expire_seconds):
    return "never" if expire_seconds is None else str(int(expire_seconds))


def _expire_file_path(cache_dir=None):
    return os.path.join(cache_dir or get_default_cache_dir(), CACHE_EXPIRE_FILE)


def get_default_expire_seconds():
    global _expire_file_cache
    path = _expire_file_path()
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        mtime = None
    else:
        cached_path, cached_mtime, cached_value = _expire_file_cache
        if cached_path == path and cached_mtime == mtime:
            return cached_value
        try:
            with open(path, "r", encoding="utf-8") as handle:
                expire_seconds = parse_expire_label(handle.read())
        except (OSError, ValueError):
            expire_seconds = None
        else:
            _expire_file_cache = (path, mtime, expire_seconds)
            return expire_seconds

    env_value = os.environ.get("SYMPHONYGPT_CACHE_EXPIRE")
    if env_value is not None:
        try:
            return parse_expire_label(env_value)
        except ValueError:
            return None
    return None


def set_default_expire_seconds(expire_seconds, cache_dir=None):
    global _expire_file_cache
    expire_seconds = parse_expire_label(expire_seconds)
    label = format_expire_env(expire_seconds)
    os.environ["SYMPHONYGPT_CACHE_EXPIRE"] = label

    cache_root = cache_dir or get_default_cache_dir()
    os.makedirs(cache_root, exist_ok=True)
    path = _expire_file_path(cache_root)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(label)
        handle.write("\n")
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        mtime = None
    _expire_file_cache = (path, mtime, expire_seconds)
    return expire_seconds


def iter_cache_dirs(cache_root=None):
    cache_root = cache_root or get_default_cache_dir()
    if not cache_root or not os.path.isdir(cache_root):
        return
    skip_names = {"zboot", "zboot-local", "backups", "__pycache__"}
    for dirpath, dirnames, filenames in os.walk(cache_root):
        dirnames[:] = [name for name in dirnames if name not in skip_names and not name.startswith(".")]
        if "cache.db" in filenames:
            yield dirpath


def checkpoint_cache_dir(cache_dir):
    """Flush WAL into cache.db and drop sidecar files so a later copy is safe."""
    db_path = cache_db_path(cache_dir)
    if not os.path.isfile(db_path):
        return False
    try:
        con = sqlite3.connect(db_path, timeout=30.0)
        try:
            con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            con.execute("PRAGMA journal_mode=DELETE")
            con.commit()
        finally:
            con.close()
        _remove_named_cache_files(cache_dir, _CACHE_SIDECARS)
        logging.info("Checkpointed cache at %s", db_path)
        return True
    except sqlite3.Error as exc:
        logging.warning("Failed to checkpoint cache at %s: %s", db_path, exc)
        return False


_live_caches = []
_caches_closed = False


def close_all_caches(cache_root=None):
    """Close open SymphonyCache objects and checkpoint every cache.db under cache_root."""
    global _caches_closed
    if _caches_closed:
        return
    _caches_closed = True
    for inst in list(_live_caches):
        try:
            inst._close_cache()
        except Exception:
            logging.exception("Failed to close cache at %s", getattr(inst, "cache_dir", None))
    _live_caches.clear()
    root = cache_root or get_default_cache_dir()
    for cache_dir in list(iter_cache_dirs(root)):
        checkpoint_cache_dir(cache_dir)


atexit.register(close_all_caches)


def apply_expire_to_cache_dirs(cache_root=None, expire=_USE_DEFAULT_EXPIRE):
    expire_value = get_default_expire_seconds() if expire is _USE_DEFAULT_EXPIRE else parse_expire_label(expire)
    updated = 0
    directories = 0
    for cache_dir in iter_cache_dirs(cache_root):
        cache = Cache(cache_dir)
        try:
            for key in list(cache.iterkeys()):
                cache.touch(key, expire=expire_value, retry=True)
                updated += 1
            directories += 1
        finally:
            cache.close()
    return directories, updated


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
        global _caches_closed
        if cache_dir is not None:
            # self.cache_dir = cache_dir + "." + str(os.getpid())
            self.cache_dir = cache_dir
        else:
            self.cache_dir = get_default_cache_dir()

        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache = None
        # SHM files are machine-local lock maps. A leftover cache.db-shm from a
        # killed process (or another OS) can make SQLite report the cache as
        # empty or corrupt. Strip WAL/SHM and re-check before wiping cache.db.
        issue = cache_db_health_issue(self.cache_dir)
        if issue:
            self._recover_cache(issue)
        else:
            try:
                self._open_cache(remove_shm=True)
            except sqlite3.Error as exc:
                if not _is_corrupt_cache_error(exc):
                    raise
                self._recover_cache(exc)
        _live_caches.append(self)
        _caches_closed = False

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
        label = _short_cache_label(self.cache_dir)
        reason = str(exc).strip() or "unknown error"
        _notify_cache_event(
            self.cache_dir,
            f"Cache failure at {label}: {reason}",
        )
        _notify_cache_event(
            self.cache_dir,
            f"Cache recovery at {label}: removing WAL/SHM and re-checking cache.db",
        )
        self._close_cache()
        _remove_named_cache_files(self.cache_dir, _CACHE_SIDECARS)
        retry_issue = cache_db_health_issue(self.cache_dir)
        if not retry_issue:
            try:
                self._open_cache()
                _notify_cache_event(
                    self.cache_dir,
                    f"Cache recovered at {label} after removing WAL/SHM",
                )
                return
            except sqlite3.Error as retry_exc:
                if not _is_corrupt_cache_error(retry_exc):
                    raise
                retry_issue = str(retry_exc)
        _notify_cache_event(
            self.cache_dir,
            f"Cache recovery at {label} failed after removing WAL/SHM: {retry_issue}",
        )
        _notify_cache_event(
            self.cache_dir,
            f"Cache reset at {label}; previous cached analysis will be regenerated",
            level=logging.ERROR,
        )
        self._open_cache(reset_files=True)

    def _run_cache_op(self, operation, fallback=None):
        label = _short_cache_label(self.cache_dir)
        try:
            return operation()
        except sqlite3.Error as exc:
            if not _is_corrupt_cache_error(exc):
                if fallback is not None:
                    _notify_cache_event(
                        self.cache_dir,
                        f"Cache operation failed at {label}: {exc}",
                    )
                    return fallback
                raise
            _notify_cache_event(
                self.cache_dir,
                f"Cache failure at {label}: {exc}",
            )
            _notify_cache_event(
                self.cache_dir,
                f"Cache recovery at {label}: removing WAL/SHM and retrying",
            )
            try:
                self._open_cache(sidecars_only=True)
                result = operation()
                _notify_cache_event(
                    self.cache_dir,
                    f"Cache recovered at {label} after removing WAL/SHM",
                )
                return result
            except sqlite3.Error as retry_exc:
                if not _is_corrupt_cache_error(retry_exc):
                    if fallback is not None:
                        _notify_cache_event(
                            self.cache_dir,
                            f"Cache operation failed at {label}: {retry_exc}",
                        )
                        return fallback
                    raise
                _notify_cache_event(
                    self.cache_dir,
                    f"Cache recovery at {label} failed after removing WAL/SHM: {retry_exc}",
                )
                _notify_cache_event(
                    self.cache_dir,
                    f"Cache reset at {label}; previous cached analysis will be regenerated",
                    level=logging.ERROR,
                )
                self._open_cache(reset_files=True)
                try:
                    return operation()
                except sqlite3.Error as final_exc:
                    _notify_cache_event(
                        self.cache_dir,
                        f"Cache still unusable at {label}: {final_exc}",
                        level=logging.ERROR,
                    )
                    if fallback is not None:
                        return fallback
                    raise

    # Function to cleanup the cache directory
    def cleanup_cache_dir(self):
        if os.path.exists(self.cache_dir):
            # delete all files in the directory
            self.cache.clear()
            # delete the directory
            shutil.rmtree(self.cache_dir)
            Util().debug_print(f"Cache directory {self.cache_dir} has been deleted.")

    def set(self, key, value, expire_seconds=_USE_DEFAULT_EXPIRE):
        expire = get_default_expire_seconds() if expire_seconds is _USE_DEFAULT_EXPIRE else parse_expire_label(expire_seconds)
        self._run_cache_op(lambda: self.cache.set(key, value, expire=expire, retry=True))

    def get(self, key):
        def _get():
            answer = self.cache.get(key)
            if answer is None:
                return f"{key} not found"
            expire = get_default_expire_seconds()
            if expire is not None:
                self.cache.touch(key, expire=expire, retry=True)
            return answer

        return self._run_cache_op(_get, fallback=f"{key} not found")

    def get_store_time(self, key):
        """Unix time when `key` was last written, without refreshing that time."""
        def _get():
            db_key, raw = self.cache._disk.put(key)
            row = self.cache._sql(
                "SELECT store_time FROM Cache WHERE key = ? AND raw = ?"
                " AND (expire_time IS NULL OR expire_time > ?)",
                (db_key, raw, time.time()),
            ).fetchone()
            if not row or row[0] is None:
                return None
            return float(row[0])

        return self._run_cache_op(_get, fallback=None)

    def set_store_time(self, key, store_time):
        """Restore the write time after a copy so cache hits keep the original generation time."""
        if store_time is None:
            return False

        def _set():
            db_key, raw = self.cache._disk.put(key)
            with self.cache._transact(retry=True):
                self.cache._sql(
                    "UPDATE Cache SET store_time = ? WHERE key = ? AND raw = ?",
                    (float(store_time), db_key, raw),
                )
            return True

        return self._run_cache_op(_set, fallback=False)

    def touch(self, key, expire=_USE_DEFAULT_EXPIRE):
        expire_value = get_default_expire_seconds() if expire is _USE_DEFAULT_EXPIRE else parse_expire_label(expire)
        return self._run_cache_op(lambda: self.cache.touch(key, expire=expire_value, retry=True))

    def touch_all(self, expire=_USE_DEFAULT_EXPIRE):
        expire_value = get_default_expire_seconds() if expire is _USE_DEFAULT_EXPIRE else parse_expire_label(expire)
        keys = self.get_all_keys()
        for key in keys:
            self.touch(key, expire=expire_value)
        return len(keys)

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