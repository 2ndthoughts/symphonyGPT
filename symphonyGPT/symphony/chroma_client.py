import importlib.metadata
import os
import threading

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import chromadb
from chromadb.config import Settings

_lock = threading.Lock()
_settings = None


def chroma_client():
    """Return the process Chroma client.

    Ephemeral Chroma keeps its schema in a per-thread memory database. Flask
    drops the request thread when the response finishes, which deletes that
    database while the client singleton stays behind. The next request then
    fails with "no such table: tenants". A file under the cache directory
    keeps the schema available to later threads.

    The app process and the chat process can run different Chroma versions.
    Each version gets its own directory so one does not open the other's file.
    """
    global _settings
    with _lock:
        if _settings is None:
            from symphonyGPT.symphony.symphony_cache import get_default_cache_dir
            try:
                chroma_version = importlib.metadata.version("chromadb")
            except importlib.metadata.PackageNotFoundError:
                chroma_version = "unknown"
            directory = os.path.abspath(
                os.path.join(get_default_cache_dir(), f"chroma-{chroma_version}")
            )
            os.makedirs(directory, exist_ok=True)
            _settings = Settings(
                anonymized_telemetry=False,
                is_persistent=True,
                persist_directory=directory,
            )
        return chromadb.Client(_settings)
