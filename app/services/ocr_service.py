#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

from .invoice_recognition_engine import InvoiceRecognitionEngine
from .error_handling_service import ErrorHandlingService
from .pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)

class OCRService:
    """OCR服务 - 基于基本规则的发票识别"""
    
    def __init__(self):
        self.engine = InvoiceRecognitionEngine()
        self.error_handler = ErrorHandlingService()
        self.pdf_processor = PDFProcessor()
        # 配置Tesseract路径（如果需要）
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    def extract_text_from_image(self, image_path: str) -> str:
        """从图片中提取文本"""
        if not TESSERACT_AVAILABLE:
            logger.warning("Tesseract不可用，无法处理图片文件")
            return ""

        try:
            # 使用PIL打开图片
            image = Image.open(image_path)

            # 使用Tesseract进行OCR识别
            # 配置OCR参数，优化中文识别
            custom_config = r'--oem 3 --psm 6 -l chi_sim+eng'
            text = pytesseract.image_to_string(image, config=custom_config)

            logger.info(f"从图片 {image_path} 提取文本成功，长度: {len(text)}")
            return text

        except Exception as e:
            logger.error(f"从图片 {image_path} 提取文本失败: {e}")
            return ""
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """从PDF中提取文本 - 使用轻量级PDF处理器"""
        try:
            return self.pdf_processor.extract_text_from_pdf(pdf_path)
        except Exception as e:
            logger.error(f"从PDF {pdf_path} 提取文本失败: {e}")
            return ""
    
    def extract_text_from_file(self, file_path: str) -> str:
        """根据文件类型提取文本"""
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return ""
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            return self.extract_text_from_image(file_path)
        else:
            logger.error(f"不支持的文件类型: {file_ext}")
            return ""
    
    def extract_invoice_info(self, text: str) -> Dict[str, Optional[str]]:
        """从文本中提取发票关键信息 - 基于基本规则的新引擎"""
        
        # 使用新的基于规则的识别引擎
        info = self.engine.extract_invoice_info(text)
        
        # 转换为OCR服务期望的格式
        result = {
            'invoice_number': info.get('invoice_number'),
            'invoice_date': info.get('invoice_date'),
            'total_amount': info.get('total_amount'),
            'tax_amount': info.get('tax_amount'),
            'amount_without_tax': info.get('amount_without_tax'),
            'seller_name': info.get('seller_name'),
            'seller_tax_number': info.get('seller_tax_number'),
            'buyer_name': info.get('buyer_name'),
            'buyer_tax_number': info.get('buyer_tax_number'),
            'invoice_content': info.get('invoice_content'),
            'recognition_attempts': info.get('recognition_attempts', 1)
        }
        
        # 应用后处理和验证
        result = self._post_process_invoice_info(result)
        
        return result
    
    def _post_process_invoice_info(self, info: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
        """后处理发票信息"""
        # 这里可以添加额外的验证和清理逻辑
        return info
    
    def process_invoice_file(self, file_path: str) -> Dict[str, Optional[str]]:
        """处理发票文件，返回提取的信息，包含错误处理"""

        try:
            # 1. 提取文本
            text = self.extract_text_from_file(file_path)

            if not text.strip():
                logger.warning(f"从文件 {file_path} 中未提取到文本")
                # 移动到解析错误目录
                self.error_handler.handle_unrecognized_invoice(
                    file_path, {}, "无法提取文本内容", 0.0
                )
                return {}

            # 2. 提取发票信息
            invoice_info = self.extract_invoice_info(text)

            # 3. 添加原始文本和文件信息
            invoice_info['raw_text'] = text
            invoice_info['file_path'] = file_path
            invoice_info['file_name'] = os.path.basename(file_path)
            invoice_info['file_type'] = os.path.splitext(file_path)[1].lower()

            # 4. 质量检查和错误处理
            is_valid, error_reason, confidence_score = self.error_handler.evaluate_recognition_quality(
                invoice_info, file_path
            )

            # 添加质量评估信息
            invoice_info['recognition_quality'] = {
                'is_valid': is_valid,
                'confidence_score': confidence_score,
                'error_reason': error_reason
            }

            # 5. 如果识别质量不合格，移动到未识别目录
            if not is_valid:
                new_path = self.error_handler.handle_unrecognized_invoice(
                    file_path, invoice_info, error_reason, confidence_score
                )
                invoice_info['file_path'] = new_path
                invoice_info['status'] = 'unrecognized'
                logger.warning(f"发票识别质量不合格，已移动到: {new_path}")
            else:
                invoice_info['status'] = 'recognized'
                logger.info(f"发票识别成功: {file_path} (置信度: {confidence_score:.2f})")

            return invoice_info

        except Exception as e:
            logger.error(f"处理发票文件时出错: {file_path}, 错误: {e}")
            # 移动到解析错误目录
            try:
                self.error_handler.handle_unrecognized_invoice(
                    file_path, {}, f"处理异常: {str(e)}", 0.0
                )
            except:
                pass
            return {}
    
    def _preprocess_image_text(self, text: str) -> str:
        """预处理图片OCR文本"""
        # 清理常见的OCR错误
        text = text.replace('壬', '¥')  # OCR常将¥识别为壬
        text = text.replace('垩', '¥')  # OCR常将¥识别为垩
        text = text.replace('￥', '¥')  # 统一货币符号
        
        # 清理多余的空格和换行
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """解析日期字符串"""
        if not date_str:
            return None
        
        try:
            # 处理中文日期格式
            if '年' in date_str and '月' in date_str and '日' in date_str:
                date_str = re.sub(r'(\d{4})年(\d{1,2})月(\d{1,2})日', r'\1-\2-\3', date_str)
            
            # 尝试解析日期
            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d']:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            return date_str  # 如果无法解析，返回原字符串
            
        except Exception as e:
            logger.warning(f"日期解析失败: {date_str}, 错误: {e}")
            return None
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """解析金额字符串"""
        if not amount_str:
            return None
        
        try:
            # 清理金额字符串
            amount_str = str(amount_str).strip()
            amount_str = amount_str.replace('¥', '').replace('￥', '').replace(',', '')
            amount_str = amount_str.replace('壬', '').replace('垩', '')  # 清理OCR错误
            
            # 转换为浮点数
            return float(amount_str)
        except (ValueError, TypeError):
            return None
