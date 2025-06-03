#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import subprocess
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class PDFProcessor:
    """PDF处理器 - 轻量级PDF文本提取"""
    
    def __init__(self):
        self.available_methods = self._check_available_methods()
        logger.info(f"可用的PDF处理方法: {self.available_methods}")
    
    def _check_available_methods(self) -> list:
        """检查可用的PDF处理方法"""
        methods = []
        
        # 检查PyMuPDF
        try:
            import fitz
            methods.append('pymupdf')
            logger.info("PyMuPDF可用")
        except ImportError:
            logger.info("PyMuPDF不可用")
        
        # 检查pdfplumber
        try:
            import pdfplumber
            methods.append('pdfplumber')
            logger.info("pdfplumber可用")
        except ImportError:
            logger.info("pdfplumber不可用")
        
        # 检查pdftotext命令行工具
        try:
            result = subprocess.run(['pdftotext', '-v'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 or 'pdftotext' in result.stderr.lower():
                methods.append('pdftotext')
                logger.info("pdftotext命令行工具可用")
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            logger.info("pdftotext命令行工具不可用")
        
        return methods
    
    def extract_text_with_pymupdf(self, pdf_path: str) -> str:
        """使用PyMuPDF提取文本"""
        try:
            import fitz
            
            text = ""
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                text += page_text + "\n"
            
            doc.close()
            
            logger.info(f"PyMuPDF提取文本成功，长度: {len(text)}")
            return text
            
        except Exception as e:
            logger.error(f"PyMuPDF提取文本失败: {e}")
            return ""
    
    def extract_text_with_pdfplumber(self, pdf_path: str) -> str:
        """使用pdfplumber提取文本"""
        try:
            import pdfplumber
            
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            logger.info(f"pdfplumber提取文本成功，长度: {len(text)}")
            return text
            
        except Exception as e:
            logger.error(f"pdfplumber提取文本失败: {e}")
            return ""
    
    def extract_text_with_pdftotext(self, pdf_path: str) -> str:
        """使用pdftotext命令行工具提取文本"""
        try:
            # 使用pdftotext命令
            result = subprocess.run([
                'pdftotext', 
                '-layout',  # 保持布局
                '-enc', 'UTF-8',  # 指定编码
                pdf_path, 
                '-'  # 输出到stdout
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                text = result.stdout
                logger.info(f"pdftotext提取文本成功，长度: {len(text)}")
                return text
            else:
                logger.error(f"pdftotext执行失败: {result.stderr}")
                return ""
                
        except subprocess.TimeoutExpired:
            logger.error("pdftotext执行超时")
            return ""
        except Exception as e:
            logger.error(f"pdftotext提取文本失败: {e}")
            return ""
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """从PDF提取文本 - 自动选择最佳方法"""
        if not os.path.exists(pdf_path):
            logger.error(f"PDF文件不存在: {pdf_path}")
            return ""
        
        if not self.available_methods:
            logger.error("没有可用的PDF处理方法")
            return ""
        
        # 按优先级尝试不同方法
        for method in self.available_methods:
            try:
                if method == 'pymupdf':
                    text = self.extract_text_with_pymupdf(pdf_path)
                elif method == 'pdfplumber':
                    text = self.extract_text_with_pdfplumber(pdf_path)
                elif method == 'pdftotext':
                    text = self.extract_text_with_pdftotext(pdf_path)
                else:
                    continue
                
                # 如果成功提取到文本，返回结果
                if text.strip():
                    logger.info(f"使用 {method} 成功提取PDF文本: {pdf_path}")
                    return text
                else:
                    logger.warning(f"{method} 提取的文本为空，尝试下一个方法")
                    
            except Exception as e:
                logger.warning(f"{method} 处理失败: {e}，尝试下一个方法")
                continue
        
        logger.error(f"所有PDF处理方法都失败了: {pdf_path}")
        return ""
    
    def is_pdf_processable(self, pdf_path: str) -> bool:
        """检查PDF是否可以处理"""
        if not os.path.exists(pdf_path):
            return False
        
        if not self.available_methods:
            return False
        
        # 检查文件大小（避免处理过大的文件）
        try:
            file_size = os.path.getsize(pdf_path)
            max_size = 50 * 1024 * 1024  # 50MB
            if file_size > max_size:
                logger.warning(f"PDF文件过大: {file_size} bytes > {max_size} bytes")
                return False
        except Exception as e:
            logger.error(f"检查文件大小失败: {e}")
            return False
        
        return True
    
    def get_pdf_info(self, pdf_path: str) -> dict:
        """获取PDF文件信息"""
        info = {
            'file_path': pdf_path,
            'file_size': 0,
            'page_count': 0,
            'processable': False,
            'available_methods': self.available_methods
        }
        
        try:
            # 文件大小
            info['file_size'] = os.path.getsize(pdf_path)
            
            # 页数（如果PyMuPDF可用）
            if 'pymupdf' in self.available_methods:
                import fitz
                doc = fitz.open(pdf_path)
                info['page_count'] = len(doc)
                doc.close()
            
            # 是否可处理
            info['processable'] = self.is_pdf_processable(pdf_path)
            
        except Exception as e:
            logger.error(f"获取PDF信息失败: {e}")
        
        return info
