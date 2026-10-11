#!/usr/bin/env python3
"""
Atomarer Disk-Cache für german-law-kit.
Nutzt tempfile + os.replace für sichere POSIX- und Windows-Dateisystemmutationen.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional


class AtomicDiskCache:
    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_path(self, key: str) -> Path:
        # Sanitize filename key
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.cache_dir / safe_key

    def has(self, key: str) -> bool:
        path = self.get_path(key)
        return path.exists() and path.stat().st_size > 0

    def get_text(self, key: str, encoding: str = "utf-8") -> Optional[str]:
        path = self.get_path(key)
        if not path.exists():
            return None
        try:
            return path.read_text(encoding=encoding)
        except Exception:
            return None

    def put_text(self, key: str, content: str, encoding: str = "utf-8") -> Path:
        target_path = self.get_path(key)
        # Atomic write with tempfile in same directory
        temp_fd, temp_path = tempfile.mkstemp(dir=str(self.cache_dir), prefix="tmp_gii_")
        try:
            with os.fdopen(temp_fd, "w", encoding=encoding) as f:
                f.write(content)
            os.replace(temp_path, target_path)
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise
        return target_path

    def get_bytes(self, key: str) -> Optional[bytes]:
        path = self.get_path(key)
        if not path.exists():
            return None
        try:
            return path.read_bytes()
        except Exception:
            return None

    def put_bytes(self, key: str, data: bytes) -> Path:
        target_path = self.get_path(key)
        temp_fd, temp_path = tempfile.mkstemp(dir=str(self.cache_dir), prefix="tmp_gii_")
        try:
            with os.fdopen(temp_fd, "wb") as f:
                f.write(data)
            os.replace(temp_path, target_path)
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise
        return target_path
