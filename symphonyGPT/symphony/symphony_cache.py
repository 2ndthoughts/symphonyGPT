import atexit
import os
import shutil
import tempfile
from diskcache import Cache

from symphonyGPT.symphony.util import Util


class SymphonyCache:
    def __init__(self, cache_dir=None):
        if cache_dir is not None:
            self.cache_dir = cache_dir + "." + str(os.getpid())
        else:
            # Create a temporary directory for the cache
            self.cache_dir = tempfile.mkdtemp()

        self.cache = Cache(self.cache_dir)
        # Register the cleanup function to run on process exit
        atexit.register(self.cleanup_cache_dir)

    # Function to cleanup the cache directory
    def cleanup_cache_dir(self):
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            Util().debug_print(f"Cache directory {self.cache_dir} has been deleted.")

    def set(self, key, value):
        self.cache.set(key, value)

    def get(self, key):
        answer = self.cache.get(key)
        if answer is None:
            return f"{key} not found"

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