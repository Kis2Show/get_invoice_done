#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .ocr_service_lite import OCRServiceLite
from .file_service import FileService
from .csv_storage_service import CSVStorageService

logger = logging.getLogger(__name__)

class InvoiceServiceMinimal:
    """极简发票服务 - 使用CSV存储，无pandas依赖"""
    
    def __init__(self, csv_file_path: str = "./data/invoices.csv"):
        self.ocr_service = OCRServiceLite()
        self.file_service = FileService()
        self.storage = CSVStorageService(csv_file_path)
    
    def process_all_invoices(self) -> Dict[str, int]:
        """处理所有发票文件"""
        files = self.file_service.scan_files()
        stats = {'total': len(files), 'processed': 0, 'failed': 0, 'skipped': 0}
        
        for file_path, file_type in files:
            try:
                # 检查文件是否已经处理过
                existing = self.storage.get_invoice_by_file_path(file_path)
                if existing:
                    stats['skipped'] += 1
                    logger.info(f"文件已处理，跳过: {file_path}")
                    continue
                
                # 处理文件
                if self.process_single_invoice(file_path, file_type):
                    stats['processed'] += 1
                else:
                    stats['failed'] += 1
                    
            except Exception as e:
                logger.error(f"处理文件出错 {file_path}: {e}")
                stats['failed'] += 1
        
        logger.info(f"处理完成: 总计{stats['total']}个文件，成功{stats['processed']}个，失败{stats['failed']}个，跳过{stats['skipped']}个")
        return stats
    
    def process_single_invoice(self, file_path: str, file_type: str) -> bool:
        """处理单个发票文件"""
        try:
            # 验证文件
            if not self.file_service.is_valid_file(file_path):
                logger.warning(f"无效文件: {file_path}")
                return False
            
            # 使用OCR服务处理文件
            invoice_info = self.ocr_service.process_invoice_file(file_path)
            
            if not invoice_info:
                logger.warning(f"OCR处理失败: {file_path}")
                return False
            
            # 获取文件信息
            file_info = self.file_service.get_file_info(file_path)
            
            # 准备存储数据
            storage_data = {
                'file_path': file_path,
                'file_name': file_info.get('name', ''),
                'file_type': file_type,
                'raw_text': invoice_info.get('raw_text', ''),
                'invoice_number': invoice_info.get('invoice_number'),
                'invoice_date': invoice_info.get('invoice_date'),
                'total_amount': invoice_info.get('total_amount'),
                'tax_amount': invoice_info.get('tax_amount'),
                'amount_without_tax': invoice_info.get('amount_without_tax'),
                'seller_name': invoice_info.get('seller_name'),
                'seller_tax_number': invoice_info.get('seller_tax_number'),
                'buyer_name': invoice_info.get('buyer_name'),
                'buyer_tax_number': invoice_info.get('buyer_tax_number'),
                'recognition_quality': invoice_info.get('recognition_quality', {}),
                'confidence_score': invoice_info.get('recognition_quality', {}).get('confidence_score', 0.0),
                'error_reason': invoice_info.get('recognition_quality', {}).get('error_reason', ''),
                'processed': True
            }
            
            # 保存到CSV
            invoice_id = self.storage.add_invoice(storage_data)
            
            logger.info(f"发票处理成功: {file_path} -> ID: {invoice_id}")
            return True
            
        except Exception as e:
            logger.error(f"处理发票文件失败: {file_path}, 错误: {e}")
            return False
    
    def get_invoices(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取发票列表"""
        try:
            return self.storage.get_all_invoices(limit=limit, offset=offset)
        except Exception as e:
            logger.error(f"获取发票列表失败: {e}")
            return []
    
    def get_invoice_by_file_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """根据文件路径获取发票"""
        try:
            return self.storage.get_invoice_by_file_path(file_path)
        except Exception as e:
            logger.error(f"查询发票失败: {e}")
            return None
    
    def delete_invoice_by_file_path(self, file_path: str) -> bool:
        """删除发票记录"""
        try:
            return self.storage.delete_invoice_by_file_path(file_path)
        except Exception as e:
            logger.error(f"删除发票记录失败: {e}")
            return False
    
    def get_invoice_stats(self) -> Dict[str, Any]:
        """获取发票统计信息"""
        try:
            return self.storage.get_invoice_stats()
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                'total_invoices': 0,
                'total_amount': 0.0,
                'avg_amount': 0.0,
                'processed_count': 0
            }
    
    def export_to_csv(self, export_path: str = None) -> str:
        """导出数据到CSV文件"""
        try:
            return self.storage.export_to_csv(export_path)
        except Exception as e:
            logger.error(f"导出CSV失败: {e}")
            raise
    
    def get_csv_file_path(self) -> str:
        """获取CSV文件路径"""
        return self.storage.get_csv_file_path()
    
    def upload_invoice_file(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """上传并处理发票文件"""
        try:
            # 检查文件是否已存在
            existing = self.storage.get_invoice_by_file_path(file_path)
            if existing:
                return {
                    'success': False,
                    'message': '文件已存在',
                    'file_path': file_path,
                    'existing_id': existing.get('id')
                }
            
            # 处理文件
            success = self.process_single_invoice(file_path, file_type)
            
            if success:
                # 获取处理结果
                invoice_data = self.storage.get_invoice_by_file_path(file_path)
                return {
                    'success': True,
                    'message': '文件上传并处理成功',
                    'file_path': file_path,
                    'invoice_id': invoice_data.get('id') if invoice_data else None,
                    'invoice_data': invoice_data
                }
            else:
                return {
                    'success': False,
                    'message': '文件处理失败',
                    'file_path': file_path
                }
                
        except Exception as e:
            logger.error(f"上传文件处理失败: {e}")
            return {
                'success': False,
                'message': f'处理异常: {str(e)}',
                'file_path': file_path
            }
    
    def get_processing_status(self) -> Dict[str, Any]:
        """获取处理状态"""
        try:
            # 获取文件统计
            files = self.file_service.scan_files()
            total_files = len(files)
            
            # 获取处理统计
            stats = self.storage.get_invoice_stats()
            processed_files = stats.get('processed_count', 0)
            
            return {
                'total_files': total_files,
                'processed_files': processed_files,
                'failed_files': max(0, total_files - processed_files),
                'status': 'completed' if processed_files >= total_files else 'processing'
            }
            
        except Exception as e:
            logger.error(f"获取处理状态失败: {e}")
            return {
                'total_files': 0,
                'processed_files': 0,
                'failed_files': 0,
                'status': 'error'
            }
