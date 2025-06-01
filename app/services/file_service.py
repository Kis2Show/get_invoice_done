import os
import hashlib
import shutil
import mimetypes
from typing import List, Tuple, Dict
from pathlib import Path
from fastapi import UploadFile
import logging

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self, invoice_dir: str = "invoices"):
        self.invoice_dir = Path(invoice_dir)
        self.image_dir = self.invoice_dir / "imge"
        self.pdf_dir = self.invoice_dir / "pdf"

        # 确保目录存在
        self._ensure_directories()

        # 支持的文件格式
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        self.pdf_extensions = {'.pdf'}

        # 需要忽略的文件
        self.ignored_files = {
            '.gitkeep',
            '.gitignore',
            '.DS_Store',
            'Thumbs.db',
            'desktop.ini'
        }

        # 需要忽略的文件扩展名
        self.ignored_extensions = {
            '.txt',
            '.log',
            '.json',
            '.xml',
            '.csv',
            '.md',
            '.tmp',
            '.temp',
            '.bak',
            '.backup'
        }

        # 支持的MIME类型
        self.supported_mime_types = {
            'application/pdf': 'pdf',
            'image/jpeg': 'image',
            'image/jpg': 'image',
            'image/png': 'image',
            'image/bmp': 'image',
            'image/tiff': 'image',
            'image/tif': 'image'
        }

    def _ensure_directories(self):
        """确保目录存在"""
        try:
            self.invoice_dir.mkdir(exist_ok=True)
            self.image_dir.mkdir(exist_ok=True)
            self.pdf_dir.mkdir(exist_ok=True)
            logger.info(f"目录已创建: {self.invoice_dir}")
        except Exception as e:
            logger.error(f"创建目录失败: {e}")
            raise

    def should_ignore_file(self, file_path: Path) -> bool:
        """检查文件是否应该被忽略"""
        file_name = file_path.name.lower()
        file_ext = file_path.suffix.lower()

        # 检查文件名
        if file_name in self.ignored_files:
            return True

        # 检查扩展名
        if file_ext in self.ignored_extensions:
            return True

        # 检查隐藏文件（以.开头的文件，除了已知的扩展名）
        if file_name.startswith('.') and file_ext not in self.image_extensions and file_ext not in self.pdf_extensions:
            return True

        # 检查文件大小（忽略空文件或过小的文件）
        try:
            if file_path.stat().st_size < 100:  # 小于100字节的文件
                return True
        except:
            return True

        return False

    def scan_files(self) -> List[Tuple[str, str]]:
        """扫描发票目录，返回文件路径和类型的列表"""
        files = []
        ignored_count = 0

        # 扫描图片文件
        if self.image_dir.exists():
            for file_path in self.image_dir.rglob('*'):
                if file_path.is_file():
                    if self.should_ignore_file(file_path):
                        ignored_count += 1
                        logger.debug(f"忽略文件: {file_path}")
                        continue

                    if file_path.suffix.lower() in self.image_extensions:
                        files.append((str(file_path), 'image'))

        # 扫描PDF文件
        if self.pdf_dir.exists():
            for file_path in self.pdf_dir.rglob('*'):
                if file_path.is_file():
                    if self.should_ignore_file(file_path):
                        ignored_count += 1
                        logger.debug(f"忽略文件: {file_path}")
                        continue

                    if file_path.suffix.lower() in self.pdf_extensions:
                        files.append((str(file_path), 'pdf'))

        logger.info(f"Found {len(files)} invoice files, ignored {ignored_count} non-invoice files")
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

    def is_supported_file(self, filename: str, content_type: str = None) -> Tuple[bool, str]:
        """检查文件是否支持（严格验证：只允许PDF和图片文件）"""
        if not filename:
            return False, ""

        # 检查扩展名（严格匹配）
        file_ext = Path(filename).suffix.lower()

        # 只允许PDF文件
        if file_ext in self.pdf_extensions:
            # 进一步验证MIME类型（如果提供）
            if content_type and content_type not in ['application/pdf']:
                logger.warning(f"文件扩展名为PDF但MIME类型不匹配: {filename}, MIME: {content_type}")
                return False, ""
            return True, 'pdf'

        # 只允许图片文件
        elif file_ext in self.image_extensions:
            # 进一步验证MIME类型（如果提供）
            if content_type and not content_type.startswith('image/'):
                logger.warning(f"文件扩展名为图片但MIME类型不匹配: {filename}, MIME: {content_type}")
                return False, ""
            return True, 'image'

        # 拒绝所有其他文件类型
        logger.info(f"拒绝不支持的文件类型: {filename}, 扩展名: {file_ext}, MIME: {content_type}")
        return False, ""

    def get_file_destination(self, filename: str, file_type: str) -> Path:
        """获取文件保存路径"""
        if file_type == 'pdf':
            return self.pdf_dir / filename
        else:
            return self.image_dir / filename

    def save_uploaded_file(self, upload_file: UploadFile) -> Dict[str, any]:
        """保存上传的文件"""
        try:
            # 检查文件类型
            is_supported, file_type = self.is_supported_file(
                upload_file.filename,
                upload_file.content_type
            )

            if not is_supported:
                return {
                    'success': False,
                    'message': f'不支持的文件类型: {upload_file.filename}',
                    'file_type': None,
                    'file_path': None,
                    'file_size': 0
                }

            # 检查文件名
            if not upload_file.filename:
                return {
                    'success': False,
                    'message': '文件名不能为空',
                    'file_type': None,
                    'file_path': None,
                    'file_size': 0
                }

            # 获取保存路径
            destination = self.get_file_destination(upload_file.filename, file_type)

            # 检查文件是否已存在
            if destination.exists():
                return {
                    'success': False,
                    'message': f'文件已存在: {upload_file.filename}',
                    'file_type': file_type,
                    'file_path': str(destination),
                    'file_size': 0
                }

            # 保存文件
            with open(destination, "wb") as buffer:
                content = upload_file.file.read()
                buffer.write(content)
                file_size = len(content)

            logger.info(f"文件上传成功: {destination}")

            return {
                'success': True,
                'message': '文件上传成功',
                'file_type': file_type,
                'file_path': str(destination),
                'file_size': file_size
            }

        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            return {
                'success': False,
                'message': f'保存文件失败: {str(e)}',
                'file_type': None,
                'file_path': None,
                'file_size': 0
            }

    def delete_file(self, file_path: str) -> Dict[str, any]:
        """删除文件"""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"文件删除成功: {file_path}")
                return {
                    'success': True,
                    'message': '文件删除成功'
                }
            else:
                return {
                    'success': False,
                    'message': '文件不存在'
                }
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return {
                'success': False,
                'message': f'删除文件失败: {str(e)}'
            }

    def list_files(self, file_type: str = None) -> List[Dict[str, any]]:
        """列出文件"""
        try:
            files = []

            # 扫描目录
            directories = []
            if file_type == 'pdf':
                directories = [self.pdf_dir]
            elif file_type == 'image':
                directories = [self.image_dir]
            else:
                directories = [self.pdf_dir, self.image_dir]

            for directory in directories:
                if directory.exists():
                    for file_path in directory.iterdir():
                        if file_path.is_file():
                            # 检查是否应该忽略此文件
                            if self.should_ignore_file(file_path):
                                logger.debug(f"忽略文件: {file_path}")
                                continue

                            file_ext = file_path.suffix.lower()
                            if file_ext in self.image_extensions:
                                file_type_detected = 'image'
                            elif file_ext in self.pdf_extensions:
                                file_type_detected = 'pdf'
                            else:
                                continue  # 跳过不支持的文件

                            try:
                                stat = file_path.stat()
                                file_info = {
                                    'file_name': file_path.name,
                                    'file_path': str(file_path),
                                    'file_size': stat.st_size,
                                    'file_type': file_type_detected,
                                    'created_time': stat.st_ctime,
                                    'modified_time': stat.st_mtime,
                                    'exists': True
                                }
                                files.append(file_info)
                            except Exception as e:
                                logger.warning(f"获取文件信息失败: {file_path}, 错误: {e}")

            return files

        except Exception as e:
            logger.error(f"列出文件失败: {e}")
            return []


# 全局文件服务实例
file_service = FileService()
