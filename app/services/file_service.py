import os
import hashlib
from typing import List, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self, invoice_dir: str = "invoices"):
        self.invoice_dir = Path(invoice_dir)
        self.image_dir = self.invoice_dir / "imge"
        self.pdf_dir = self.invoice_dir / "pdf"
        
        # 支持的文件格式
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        self.pdf_extensions = {'.pdf'}
    
    def scan_files(self) -> List[Tuple[str, str]]:
        """扫描发票目录，返回文件路径和类型的列表"""
        files = []
        
        # 扫描图片文件
        if self.image_dir.exists():
            for file_path in self.image_dir.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in self.image_extensions:
                    files.append((str(file_path), 'image'))
        
        # 扫描PDF文件
        if self.pdf_dir.exists():
            for file_path in self.pdf_dir.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in self.pdf_extensions:
                    files.append((str(file_path), 'pdf'))
        
        logger.info(f"Found {len(files)} invoice files")
        return files
    
    def get_file_hash(self, file_path: str) -> str:
        """计算文件的MD5哈希值，用于去重"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def is_valid_file(self, file_path: str) -> bool:
        """检查文件是否有效"""
        try:
            path = Path(file_path)
            return path.exists() and path.is_file() and path.stat().st_size > 0
        except Exception:
            return False
    
    def get_file_info(self, file_path: str) -> dict:
        """获取文件基本信息"""
        try:
            path = Path(file_path)
            stat = path.stat()
            return {
                'name': path.name,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'extension': path.suffix.lower()
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {}
