#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class ExcelStorageService:
    """Excel存储服务 - 替代数据库存储"""
    
    def __init__(self, excel_file_path: str = "./data/invoices.xlsx"):
        self.excel_file_path = Path(excel_file_path)
        self.excel_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 定义Excel列结构
        self.columns = [
            'id', 'file_path', 'file_name', 'file_type',
            'invoice_number', 'invoice_date', 'total_amount', 
            'tax_amount', 'amount_without_tax',
            'seller_name', 'seller_tax_number',
            'buyer_name', 'buyer_tax_number',
            'raw_text', 'processed', 'created_at', 'updated_at',
            'recognition_quality', 'confidence_score', 'error_reason'
        ]
        
        # 初始化Excel文件
        self._initialize_excel_file()
    
    def _initialize_excel_file(self):
        """初始化Excel文件"""
        if not self.excel_file_path.exists():
            # 创建空的DataFrame
            df = pd.DataFrame(columns=self.columns)
            df.to_excel(self.excel_file_path, index=False, engine='openpyxl')
            logger.info(f"创建新的Excel文件: {self.excel_file_path}")
        else:
            logger.info(f"使用现有Excel文件: {self.excel_file_path}")
    
    def _load_data(self) -> pd.DataFrame:
        """加载Excel数据"""
        try:
            if self.excel_file_path.exists():
                df = pd.read_excel(self.excel_file_path, engine='openpyxl')
                # 确保所有必要的列都存在
                for col in self.columns:
                    if col not in df.columns:
                        df[col] = None
                return df
            else:
                return pd.DataFrame(columns=self.columns)
        except Exception as e:
            logger.error(f"加载Excel文件失败: {e}")
            return pd.DataFrame(columns=self.columns)
    
    def _save_data(self, df: pd.DataFrame):
        """保存数据到Excel"""
        try:
            # 确保目录存在
            self.excel_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存到Excel
            df.to_excel(self.excel_file_path, index=False, engine='openpyxl')
            logger.info(f"数据已保存到Excel: {self.excel_file_path}")
        except Exception as e:
            logger.error(f"保存Excel文件失败: {e}")
            raise
    
    def add_invoice(self, invoice_data: Dict[str, Any]) -> int:
        """添加发票记录"""
        try:
            df = self._load_data()
            
            # 生成新的ID
            if len(df) > 0:
                new_id = df['id'].max() + 1 if pd.notna(df['id'].max()) else 1
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
            
            # 添加到DataFrame
            new_df = pd.DataFrame([new_record])
            df = pd.concat([df, new_df], ignore_index=True)
            
            # 保存
            self._save_data(df)
            
            logger.info(f"添加发票记录成功，ID: {new_id}")
            return new_id
            
        except Exception as e:
            logger.error(f"添加发票记录失败: {e}")
            raise
    
    def get_invoice_by_file_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """根据文件路径获取发票记录"""
        try:
            df = self._load_data()
            result = df[df['file_path'] == file_path]
            
            if len(result) > 0:
                return result.iloc[0].to_dict()
            return None
            
        except Exception as e:
            logger.error(f"查询发票记录失败: {e}")
            return None
    
    def get_all_invoices(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取所有发票记录"""
        try:
            df = self._load_data()
            
            # 按创建时间降序排序
            df = df.sort_values('created_at', ascending=False)
            
            # 分页
            start_idx = offset
            end_idx = offset + limit
            result_df = df.iloc[start_idx:end_idx]
            
            return result_df.to_dict('records')
            
        except Exception as e:
            logger.error(f"获取发票列表失败: {e}")
            return []
    
    def get_invoice_stats(self) -> Dict[str, Any]:
        """获取发票统计信息"""
        try:
            df = self._load_data()
            
            if len(df) == 0:
                return {
                    'total_invoices': 0,
                    'total_amount': 0.0,
                    'avg_amount': 0.0,
                    'processed_count': 0
                }
            
            # 计算统计信息
            total_invoices = len(df)
            processed_count = len(df[df['processed'] == True])
            
            # 金额统计（过滤掉空值）
            amount_series = pd.to_numeric(df['total_amount'], errors='coerce')
            valid_amounts = amount_series.dropna()
            
            total_amount = valid_amounts.sum() if len(valid_amounts) > 0 else 0.0
            avg_amount = valid_amounts.mean() if len(valid_amounts) > 0 else 0.0
            
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
            df = self._load_data()
            
            # 删除匹配的记录
            original_len = len(df)
            df = df[df['file_path'] != file_path]
            
            if len(df) < original_len:
                self._save_data(df)
                logger.info(f"删除发票记录成功: {file_path}")
                return True
            else:
                logger.warning(f"未找到要删除的发票记录: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"删除发票记录失败: {e}")
            return False
    
    def export_to_excel(self, export_path: str = None) -> str:
        """导出数据到Excel文件"""
        try:
            if export_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = f"./data/invoices_export_{timestamp}.xlsx"
            
            df = self._load_data()
            
            # 创建导出目录
            Path(export_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 导出到Excel
            df.to_excel(export_path, index=False, engine='openpyxl')
            
            logger.info(f"数据导出成功: {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            raise
    
    def get_excel_file_path(self) -> str:
        """获取Excel文件路径"""
        return str(self.excel_file_path)
