"""本地文件存储 - 替代 MinIO"""
import os
import uuid
from pathlib import Path
from datetime import datetime

class LocalFileStorage:
    def __init__(self, base_dir: str = "/data/lims/files"):
        self.base_dir = Path(base_dir)
        self.buckets = {
            "reports": self.base_dir / "reports",
            "attachments": self.base_dir / "attachments",
            "records": self.base_dir / "records",
            "backups": self.base_dir / "backups",
        }
        for b in self.buckets.values():
            b.mkdir(parents=True, exist_ok=True)

    def store(self, content: bytes, bucket: str, original_name: str) -> dict:
        sub_dir = self.buckets[bucket] / datetime.now().strftime("%Y/%m/%d")
        sub_dir.mkdir(parents=True, exist_ok=True)
        file_id = str(uuid.uuid4())
        ext = Path(original_name).suffix or ".bin"
        file_path = sub_dir / f"{file_id}{ext}"
        file_path.write_bytes(content)
        return {
            "id": file_id,
            "bucket": bucket,
            "original_name": original_name,
            "storage_path": str(file_path.relative_to(self.base_dir)),
            "size": len(content),
        }
