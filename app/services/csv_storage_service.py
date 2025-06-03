#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class CSVStorageService:
    """CSV存储服务 - 替代pandas+Excel，极致轻量"""
    
    def __init__(self, csv_file_path: str = "./data/invoices.csv"):
        self.csv_file_path = Path(csv_file_path)
        self.csv_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 定义CSV列结构
        self.columns = [
            'id', 'file_path', 'file_name', 'file_type',
            'invoice_number', 'invoice_date', 'total_amount', 
            'tax_amount', 'amount_without_tax',
            'seller_name', 'seller_tax_number',
            'buyer_name', 'buyer_tax_number',
            'raw_text', 'processed', 'created_at', 'updated_at',
            'recognition_quality', 'confidence_score', 'error_reason'
        ]
        
        # 初始化CSV文件
        self._initialize_csv_file()
    
    def _initialize_csv_file(self):
        """初始化CSV文件"""
        if not self.csv_file_path.exists():
            with open(self.csv_file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.columns)
                writer.writeheader()
            logger.info(f"创建新的CSV文件: {self.csv_file_path}")
        else:
            logger.info(f"使用现有CSV文件: {self.csv_file_path}")
    
    def _load_data(self) -> List[Dict[str, Any]]:
        """加载CSV数据"""
        try:
            if not self.csv_file_path.exists():
                return []
            
            data = []
            with open(self.csv_file_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 处理数据类型
                    if row.get('id'):
                        row['id'] = int(row['id']) if row['id'].isdigit() else None
                    if row.get('total_amount'):
                        try:
                            row['total_amount'] = float(row['total_amount'])
                        except (ValueError, TypeError):
                            row['total_amount'] = None
                    if row.get('tax_amount'):
                        try:
                            row['tax_amount'] = float(row['tax_amount'])
                        except (ValueError, TypeError):
                            row['tax_amount'] = None
                    if row.get('confidence_score'):
                        try:
                            row['confidence_score'] = float(row['confidence_score'])
                        except (ValueError, TypeError):
                            row['confidence_score'] = 0.0
                    
                    data.append(row)
            
            return data
        except Exception as e:
            logger.error(f"加载CSV文件失败: {e}")
            return []
    
    def _save_data(self, data: List[Dict[str, Any]]):
        """保存数据到CSV"""
        try:
            # 确保目录存在
            self.csv_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.csv_file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.columns)
                writer.writeheader()
                for row in data:
                    # 确保所有字段都存在
                    clean_row = {}
                    for col in self.columns:
                        value = row.get(col, '')
                        # 处理复杂对象（如recognition_quality）
                        if isinstance(value, (dict, list)):
                            value = json.dumps(value, ensure_ascii=False)
                        clean_row[col] = value
                    writer.writerow(clean_row)
            
            logger.info(f"数据已保存到CSV: {self.csv_file_path}")
        except Exception as e:
            logger.error(f"保存CSV文件失败: {e}")
            raise
    
    def add_invoice(self, invoice_data: Dict[str, Any]) -> int:
        """添加发票记录"""
        try:
            data = self._load_data()
            
            # 生成新的ID
            if data:
                max_id = max([row.get('id', 0) for row in data if row.get('id')])
                new_id = max_id + 1
            else:
                new_id = 1
            
            # 准备新记录
            new_record = {
                'id': new_id,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'processed': True
            }
            
            # 添加发票数据
            for key, value in invoice_data.items():
                if key in self.columns:
                    new_record[key] = value
            
            # 添加到数据列表
            data.append(new_record)
            
            # 保存
            self._save_data(data)
            
            logger.info(f"添加发票记录成功，ID: {new_id}")
            return new_id
            
        except Exception as e:
            logger.error(f"添加发票记录失败: {e}")
            raise
    
    def get_invoice_by_file_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """根据文件路径获取发票记录"""
        try:
            data = self._load_data()
            for row in data:
                if row.get('file_path') == file_path:
                    return row
            return None
        except Exception as e:
            logger.error(f"查询发票记录失败: {e}")
            return None
    
    def get_all_invoices(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取所有发票记录"""
        try:
            data = self._load_data()
            
            # 按创建时间降序排序
            data.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # 分页
            start_idx = offset
            end_idx = offset + limit
            return data[start_idx:end_idx]
            
        except Exception as e:
            logger.error(f"获取发票列表失败: {e}")
            return []
    
    def get_invoice_stats(self) -> Dict[str, Any]:
        """获取发票统计信息"""
        try:
            data = self._load_data()
            
            if not data:
                return {
                    'total_invoices': 0,
                    'total_amount': 0.0,
                    'avg_amount': 0.0,
                    'processed_count': 0
                }
            
            # 计算统计信息
            total_invoices = len(data)
            processed_count = len([row for row in data if row.get('processed')])
            
            # 金额统计
            valid_amounts = []
            for row in data:
                amount = row.get('total_amount')
                if amount and isinstance(amount, (int, float)):
                    valid_amounts.append(amount)
            
            total_amount = sum(valid_amounts) if valid_amounts else 0.0
            avg_amount = total_amount / len(valid_amounts) if valid_amounts else 0.0
            
            return {
                'total_invoices': total_invoices,
                'total_amount': float(total_amount),
                'avg_amount': float(avg_amount),
                'processed_count': processed_count
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                'total_invoices': 0,
                'total_amount': 0.0,
                'avg_amount': 0.0,
                'processed_count': 0
            }
    
    def delete_invoice_by_file_path(self, file_path: str) -> bool:
        """根据文件路径删除发票记录"""
        try:
            data = self._load_data()
            original_len = len(data)
            
            # 删除匹配的记录
            data = [row for row in data if row.get('file_path') != file_path]
            
            if len(data) < original_len:
                self._save_data(data)
                logger.info(f"删除发票记录成功: {file_path}")
                return True
            else:
                logger.warning(f"未找到要删除的发票记录: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"删除发票记录失败: {e}")
            return False
    
    def export_to_csv(self, export_path: str = None) -> str:
        """导出数据到CSV文件"""
        try:
            if export_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = f"./data/invoices_export_{timestamp}.csv"
            
            data = self._load_data()
            
            # 创建导出目录
            Path(export_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 导出到CSV
            with open(export_path, 'w', newline='', encoding='utf-8') as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=self.columns)
                    writer.writeheader()
                    for row in data:
                        clean_row = {}
                        for col in self.columns:
                            value = row.get(col, '')
                            if isinstance(value, (dict, list)):
                                value = json.dumps(value, ensure_ascii=False)
                            clean_row[col] = value
                        writer.writerow(clean_row)
            
            logger.info(f"数据导出成功: {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            raise
    
    def get_csv_file_path(self) -> str:
        """获取CSV文件路径"""
        return str(self.csv_file_path)
