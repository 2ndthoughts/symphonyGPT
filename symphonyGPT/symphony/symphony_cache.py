import atexit
import os
import shutil
import tempfile
from diskcache import Cache

from symphonyGPT.symphony.util import Util

# default cache expiration time
TWO_DAYS=2*60*60*24 # 2 days in seconds


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
            # Create a temporary directory for the cache
            self.cache_dir = tempfile.mkdtemp()

        self.cache = Cache(self.cache_dir)
        # Register the cleanup function to run on process exit
        # atexit.register(self.cleanup_cache_dir)

    # Function to cleanup the cache directory
    def cleanup_cache_dir(self):
        if os.path.exists(self.cache_dir):
            # delete all files in the directory
            self.cache.clear()
            # delete the directory
            shutil.rmtree(self.cache_dir)
            Util().debug_print(f"Cache directory {self.cache_dir} has been deleted.")

    def set(self, key, value, expire_seconds=None):
        if expire_seconds is not None:
            self.cache.set(key, value, expire=expire_seconds)
        else:
            self.cache.set(key, value, expire=TWO_DAYS)  # Set expiration to 1 day

    def get(self, key):
        answer = self.cache.get(key)
        if answer is None:
            return f"{key} not found"
        else: # If the key exists, refresh its expiration time
            self.cache.touch(key, expire=TWO_DAYS)  # Refresh expiration time

        return answer

    def delete(self, key):
        self.cache.delete(key)

    def clear(self):
        self.cache.clear()

# test main
if __name__ == "__main__":
    symphony_cache = SymphonyCache("/tmp/symphonyGPT_cache")
    symphony_cache.set("key1", "value1")
    symphony_cache.set("key1", "valueX")
    symphony_cache = SymphonyCache("/tmp/symphonyGPT_cache")
    symphony_cache.set("key2", "value2")
    print(symphony_cache.get("key1"))