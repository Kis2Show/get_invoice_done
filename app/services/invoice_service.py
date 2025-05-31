from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.models.invoice import Invoice, InvoiceFilter
from app.services.ocr_service import OCRService
from app.services.file_service import FileService

logger = logging.getLogger(__name__)

class InvoiceService:
    def __init__(self, db: Session):
        self.db = db
        self.ocr_service = OCRService()
        self.file_service = FileService()
    
    def process_all_invoices(self) -> Dict[str, int]:
        """处理所有发票文件"""
        files = self.file_service.scan_files()
        stats = {'total': len(files), 'processed': 0, 'failed': 0, 'skipped': 0}
        
        for file_path, file_type in files:
            try:
                # 检查文件是否已经处理过
                existing = self.db.query(Invoice).filter(Invoice.file_path == file_path).first()
                if existing:
                    stats['skipped'] += 1
                    continue
                
                # 处理文件
                if self.process_single_invoice(file_path, file_type):
                    stats['processed'] += 1
                else:
                    stats['failed'] += 1
                    
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                stats['failed'] += 1
        
        return stats
    
    def process_single_invoice(self, file_path: str, file_type: str) -> bool:
        """处理单个发票文件"""
        try:
            # 验证文件
            if not self.file_service.is_valid_file(file_path):
                logger.warning(f"Invalid file: {file_path}")
                return False
            
            # 提取文本
            if file_type == 'image':
                raw_text = self.ocr_service.extract_text_from_image(file_path)
            elif file_type == 'pdf':
                raw_text = self.ocr_service.extract_text_from_pdf(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_type}")
                return False
            
            if not raw_text.strip():
                logger.warning(f"No text extracted from {file_path}")
                return False
            
            # 提取发票信息
            invoice_info = self.ocr_service.extract_invoice_info(raw_text)
            
            # 获取文件信息
            file_info = self.file_service.get_file_info(file_path)
            
            # 创建发票记录
            invoice = Invoice(
                file_path=file_path,
                file_name=file_info.get('name', ''),
                file_type=file_type,
                raw_text=raw_text,
                invoice_number=invoice_info.get('invoice_number'),
                invoice_date=self._parse_datetime(invoice_info.get('invoice_date')),
                total_amount=invoice_info.get('total_amount'),
                tax_amount=invoice_info.get('tax_amount'),
                amount_without_tax=invoice_info.get('amount_without_tax'),
                seller_name=invoice_info.get('seller_name'),
                seller_tax_number=invoice_info.get('seller_tax_number'),
                buyer_name=invoice_info.get('buyer_name'),
                buyer_tax_number=invoice_info.get('buyer_tax_number'),
                processed=True
            )
            
            self.db.add(invoice)
            self.db.commit()
            
            logger.info(f"Successfully processed {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            self.db.rollback()
            return False
    
    def get_invoices(self, filter_params: InvoiceFilter) -> List[Invoice]:
        """根据筛选条件获取发票列表"""
        query = self.db.query(Invoice)
        
        # 应用筛选条件
        if filter_params.invoice_number:
            query = query.filter(Invoice.invoice_number.like(f"%{filter_params.invoice_number}%"))
        
        if filter_params.seller_name:
            query = query.filter(Invoice.seller_name.like(f"%{filter_params.seller_name}%"))
        
        if filter_params.buyer_name:
            query = query.filter(Invoice.buyer_name.like(f"%{filter_params.buyer_name}%"))
        
        if filter_params.min_amount is not None:
            query = query.filter(Invoice.total_amount >= filter_params.min_amount)
        
        if filter_params.max_amount is not None:
            query = query.filter(Invoice.total_amount <= filter_params.max_amount)
        
        if filter_params.start_date:
            query = query.filter(Invoice.invoice_date >= filter_params.start_date)
        
        if filter_params.end_date:
            query = query.filter(Invoice.invoice_date <= filter_params.end_date)
        
        # 排序
        if filter_params.sort_by:
            sort_column = getattr(Invoice, filter_params.sort_by, Invoice.created_at)
            if filter_params.sort_order == 'asc':
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
        
        # 分页
        query = query.offset(filter_params.offset).limit(filter_params.limit)
        
        return query.all()
    
    def get_invoice_by_id(self, invoice_id: int) -> Optional[Invoice]:
        """根据ID获取发票"""
        return self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    def delete_invoice(self, invoice_id: int) -> bool:
        """删除发票记录"""
        try:
            invoice = self.get_invoice_by_id(invoice_id)
            if invoice:
                self.db.delete(invoice)
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting invoice {invoice_id}: {e}")
            self.db.rollback()
            return False

    def clear_all_invoices(self) -> int:
        """清空所有发票数据"""
        try:
            count = self.db.query(Invoice).count()
            self.db.query(Invoice).delete()
            self.db.commit()
            logger.info(f"Cleared {count} invoices from database")
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error clearing all invoices: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_count = self.db.query(Invoice).count()
        processed_count = self.db.query(Invoice).filter(Invoice.processed == True).count()
        
        # 按文件类型统计
        image_count = self.db.query(Invoice).filter(Invoice.file_type == 'image').count()
        pdf_count = self.db.query(Invoice).filter(Invoice.file_type == 'pdf').count()
        
        # 金额统计
        total_amount_sum = self.db.query(Invoice.total_amount).filter(
            Invoice.total_amount.isnot(None)
        ).all()
        total_amount_sum = sum([amount[0] for amount in total_amount_sum if amount[0]])
        
        return {
            'total_invoices': total_count,
            'processed_invoices': processed_count,
            'image_invoices': image_count,
            'pdf_invoices': pdf_count,
            'total_amount_sum': total_amount_sum
        }
    
    def remove_duplicates(self) -> int:
        """移除重复的发票记录"""
        # 基于文件名去重
        duplicates = self.db.query(Invoice).filter(
            Invoice.file_name.isnot(None)
        ).all()

        seen = set()
        removed_count = 0

        for invoice in duplicates:
            key = invoice.file_name
            if key in seen:
                self.db.delete(invoice)
                removed_count += 1
            else:
                seen.add(key)

        self.db.commit()
        return removed_count
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """解析日期字符串为datetime对象"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return None
