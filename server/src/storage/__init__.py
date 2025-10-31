"""Storage module initialization."""

from src.storage.handlers import (
    StorageHandler,
    DiskStorageHandler,
    MemoryStorageHandler,
    get_storage_handler
)

__all__ = [
    "StorageHandler",
    "DiskStorageHandler",
    "MemoryStorageHandler",
    "get_storage_handler",
]
