#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

from .invoice_recognition_engine import InvoiceRecognitionEngine
from .error_handling_service import ErrorHandlingService
from .pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)

class OCRServiceLite:
    """轻量级OCR服务 - 移除OpenCV依赖"""
    
    def __init__(self):
        self.engine = InvoiceRecognitionEngine()
        self.error_handler = ErrorHandlingService()
        self.pdf_processor = PDFProcessor()
        
        # 初始化EasyOCR
        self.easyocr_reader = None
        if EASYOCR_AVAILABLE:
            try:
                # 使用预下载的模型
                model_storage_dir = os.getenv('EASYOCR_MODULE_PATH', '/home/appuser/.EasyOCR')
                self.easyocr_reader = easyocr.Reader(
                    ['ch_sim', 'en'], 
                    gpu=False,  # 强制使用CPU
                    model_storage_directory=model_storage_dir,
                    download_enabled=False  # 不下载，使用预下载的模型
                )
                logger.info("EasyOCR初始化成功")
            except Exception as e:
                logger.error(f"EasyOCR初始化失败: {e}")
                self.easyocr_reader = None
    
    def extract_text_from_image(self, image_path: str) -> str:
        """从图片中提取文本 - 使用EasyOCR"""
        if not EASYOCR_AVAILABLE or not self.easyocr_reader:
            logger.warning("EasyOCR不可用，无法处理图片文件")
            return ""

        try:
            # 使用EasyOCR进行文本识别
            results = self.easyocr_reader.readtext(image_path)
            
            # 提取文本内容
            text_lines = []
            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # 置信度阈值
                    text_lines.append(text)
            
            text = '\n'.join(text_lines)
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
        """从文本中提取发票信息"""
        try:
            return self.engine.extract_invoice_info(text)
        except Exception as e:
            logger.error(f"提取发票信息失败: {e}")
            return {}
    
    def process_invoice_file(self, file_path: str) -> Dict:
        """处理发票文件 - 完整流程"""
        logger.info(f"开始处理发票文件: {file_path}")

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
    
    def get_ocr_capabilities(self) -> Dict[str, bool]:
        """获取OCR能力信息"""
        return {
            'easyocr_available': EASYOCR_AVAILABLE and self.easyocr_reader is not None,
            'pil_available': PIL_AVAILABLE,
            'pdf_processor_available': len(self.pdf_processor.available_methods) > 0,
            'supported_image_formats': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff'],
            'supported_pdf_formats': ['.pdf']
        }
