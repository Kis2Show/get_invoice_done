#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import logging
from datetime import datetime
from typing import Dict, Optional, List, Tuple
import json

logger = logging.getLogger(__name__)

class ErrorHandlingService:
    """发票识别错误处理和纠错服务"""
    
    def __init__(self, base_dir: str = "invoices"):
        self.base_dir = base_dir
        self.unrecognized_dir = os.path.join(base_dir, "unrecognized")
        self.error_log_file = os.path.join(base_dir, "error_log.json")
        
        # 创建必要的目录
        self._ensure_directories()
        
        # 识别质量阈值
        self.quality_thresholds = {
            'min_fields_required': 4,  # 至少需要4个关键字段
            'critical_fields': ['buyer_name', 'total_amount'],  # 关键字段
            'min_confidence_score': 0.6,  # 最低置信度分数
        }
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        os.makedirs(self.unrecognized_dir, exist_ok=True)
        
        # 创建子目录
        subdirs = [
            'missing_critical_fields',  # 缺少关键字段
            'low_confidence',          # 置信度低
            'parsing_errors',          # 解析错误
            'validation_failed',       # 验证失败
            'manual_review'           # 需要人工审核
        ]
        
        for subdir in subdirs:
            os.makedirs(os.path.join(self.unrecognized_dir, subdir), exist_ok=True)
    
    def evaluate_recognition_quality(self, invoice_info: Dict, file_path: str) -> Tuple[bool, str, float]:
        """评估发票识别质量
        
        Returns:
            (is_valid, error_reason, confidence_score)
        """
        
        error_reasons = []
        confidence_score = 0.0
        
        # 1. 检查关键字段
        critical_missing = []
        for field in self.quality_thresholds['critical_fields']:
            if not invoice_info.get(field):
                critical_missing.append(field)
        
        if critical_missing:
            error_reasons.append(f"缺少关键字段: {', '.join(critical_missing)}")
        
        # 2. 计算字段完整性分数
        total_fields = len(invoice_info)
        filled_fields = sum(1 for v in invoice_info.values() if v is not None and v != "")
        field_completeness = filled_fields / total_fields if total_fields > 0 else 0
        
        # 3. 检查必需字段数量
        if filled_fields < self.quality_thresholds['min_fields_required']:
            error_reasons.append(f"识别字段过少: {filled_fields}/{total_fields}")
        
        # 4. 验证金额逻辑
        amount_valid, amount_error = self._validate_amounts(invoice_info)
        if not amount_valid:
            error_reasons.append(f"金额验证失败: {amount_error}")
        
        # 5. 验证税号格式
        tax_valid, tax_error = self._validate_tax_numbers(invoice_info)
        if not tax_valid:
            error_reasons.append(f"税号验证失败: {tax_error}")
        
        # 6. 计算综合置信度分数
        confidence_score = self._calculate_confidence_score(invoice_info, field_completeness, amount_valid, tax_valid)
        
        # 7. 判断是否通过质量检查
        is_valid = (
            len(critical_missing) == 0 and
            filled_fields >= self.quality_thresholds['min_fields_required'] and
            confidence_score >= self.quality_thresholds['min_confidence_score']
        )
        
        error_reason = "; ".join(error_reasons) if error_reasons else "通过质量检查"
        
        logger.info(f"质量评估 {file_path}: 有效={is_valid}, 置信度={confidence_score:.2f}, 原因={error_reason}")
        
        return is_valid, error_reason, confidence_score
    
    def _validate_amounts(self, invoice_info: Dict) -> Tuple[bool, str]:
        """验证金额逻辑"""
        
        total = invoice_info.get('total_amount')
        no_tax = invoice_info.get('amount_without_tax')
        tax = invoice_info.get('tax_amount')
        
        # 如果没有金额信息，认为无效
        if not total:
            return False, "缺少总金额"
        
        # 如果有不含税金额和税额，验证加法关系
        if no_tax is not None and tax is not None:
            calculated_total = no_tax + tax
            if abs(calculated_total - total) > 0.01:
                return False, f"金额计算错误: {no_tax} + {tax} ≠ {total}"
            
            # 验证税额不能大于不含税金额
            if tax > no_tax:
                return False, f"税额大于不含税金额: {tax} > {no_tax}"
        
        # 验证金额合理性
        if total <= 0 or total > 999999.99:
            return False, f"总金额不合理: {total}"
        
        return True, "金额验证通过"
    
    def _validate_tax_numbers(self, invoice_info: Dict) -> Tuple[bool, str]:
        """验证税号格式"""
        
        buyer_tax = invoice_info.get('buyer_tax_number')
        seller_tax = invoice_info.get('seller_tax_number')
        
        errors = []
        
        # 验证购买方税号
        if buyer_tax:
            if not self._is_valid_tax_number(buyer_tax):
                errors.append(f"购买方税号格式错误: {buyer_tax}")
        
        # 验证销售方税号
        if seller_tax:
            if not self._is_valid_tax_number(seller_tax):
                errors.append(f"销售方税号格式错误: {seller_tax}")
        
        # 验证税号不能相同
        if buyer_tax and seller_tax and buyer_tax == seller_tax:
            errors.append("买卖方税号相同")
        
        if errors:
            return False, "; ".join(errors)
        
        return True, "税号验证通过"
    
    def _is_valid_tax_number(self, tax_number: str) -> bool:
        """检查税号格式是否有效"""
        if not tax_number:
            return False
        
        # 统一社会信用代码：18位，字母数字组合
        if len(tax_number) == 18:
            return tax_number.isalnum()
        
        # 旧版税号：15位数字
        if len(tax_number) == 15:
            return tax_number.isdigit()
        
        return False
    
    def _calculate_confidence_score(self, invoice_info: Dict, field_completeness: float, 
                                  amount_valid: bool, tax_valid: bool) -> float:
        """计算综合置信度分数"""
        
        score = 0.0
        
        # 字段完整性权重 40%
        score += field_completeness * 0.4
        
        # 关键字段存在性权重 30%
        critical_score = 0.0
        for field in self.quality_thresholds['critical_fields']:
            if invoice_info.get(field):
                critical_score += 1
        critical_score /= len(self.quality_thresholds['critical_fields'])
        score += critical_score * 0.3
        
        # 金额验证权重 20%
        if amount_valid:
            score += 0.2
        
        # 税号验证权重 10%
        if tax_valid:
            score += 0.1
        
        return min(score, 1.0)
    
    def handle_unrecognized_invoice(self, file_path: str, invoice_info: Dict, 
                                  error_reason: str, confidence_score: float) -> str:
        """处理无法识别的发票"""
        
        # 确定错误类型和目标目录
        error_type, target_subdir = self._categorize_error(error_reason, confidence_score)
        
        # 生成新的文件路径
        filename = os.path.basename(file_path)
        target_dir = os.path.join(self.unrecognized_dir, target_subdir)
        target_path = os.path.join(target_dir, filename)
        
        # 如果目标文件已存在，添加时间戳
        if os.path.exists(target_path):
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_path = os.path.join(target_dir, f"{name}_{timestamp}{ext}")
        
        try:
            # 移动文件
            shutil.move(file_path, target_path)
            
            # 记录错误信息
            self._log_error(file_path, target_path, invoice_info, error_reason, confidence_score, error_type)
            
            logger.warning(f"发票移入未识别目录: {file_path} -> {target_path} (原因: {error_reason})")
            
            return target_path
            
        except Exception as e:
            logger.error(f"移动文件失败: {file_path} -> {target_path}, 错误: {e}")
            return file_path
    
    def _categorize_error(self, error_reason: str, confidence_score: float) -> Tuple[str, str]:
        """根据错误原因分类错误类型"""
        
        error_reason_lower = error_reason.lower()
        
        if "缺少关键字段" in error_reason:
            return "missing_critical_fields", "missing_critical_fields"
        elif "金额验证失败" in error_reason or "金额计算错误" in error_reason:
            return "validation_failed", "validation_failed"
        elif "税号验证失败" in error_reason:
            return "validation_failed", "validation_failed"
        elif "识别字段过少" in error_reason:
            return "parsing_errors", "parsing_errors"
        elif confidence_score < self.quality_thresholds['min_confidence_score']:
            return "low_confidence", "low_confidence"
        else:
            return "manual_review", "manual_review"
    
    def _log_error(self, original_path: str, new_path: str, invoice_info: Dict,
                   error_reason: str, confidence_score: float, error_type: str):
        """记录错误信息到日志文件"""
        
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'original_path': original_path,
            'new_path': new_path,
            'error_type': error_type,
            'error_reason': error_reason,
            'confidence_score': confidence_score,
            'invoice_info': invoice_info,
            'file_size': os.path.getsize(new_path) if os.path.exists(new_path) else 0
        }
        
        # 读取现有日志
        error_log = []
        if os.path.exists(self.error_log_file):
            try:
                with open(self.error_log_file, 'r', encoding='utf-8') as f:
                    error_log = json.load(f)
            except:
                error_log = []
        
        # 添加新记录
        error_log.append(error_entry)
        
        # 保持最近1000条记录
        if len(error_log) > 1000:
            error_log = error_log[-1000:]
        
        # 写入日志文件
        try:
            with open(self.error_log_file, 'w', encoding='utf-8') as f:
                json.dump(error_log, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"写入错误日志失败: {e}")
    
    def get_error_statistics(self) -> Dict:
        """获取错误统计信息"""
        
        if not os.path.exists(self.error_log_file):
            return {}
        
        try:
            with open(self.error_log_file, 'r', encoding='utf-8') as f:
                error_log = json.load(f)
        except:
            return {}
        
        # 统计各类错误
        stats = {
            'total_errors': len(error_log),
            'error_types': {},
            'recent_errors': error_log[-10:] if error_log else [],
            'avg_confidence': 0.0
        }
        
        if error_log:
            # 按错误类型统计
            for entry in error_log:
                error_type = entry.get('error_type', 'unknown')
                stats['error_types'][error_type] = stats['error_types'].get(error_type, 0) + 1
            
            # 计算平均置信度
            confidences = [entry.get('confidence_score', 0) for entry in error_log]
            stats['avg_confidence'] = sum(confidences) / len(confidences)
        
        return stats
    
    def create_manual_review_report(self) -> str:
        """创建人工审核报告"""
        
        report_path = os.path.join(self.unrecognized_dir, "manual_review_report.txt")
        
        stats = self.get_error_statistics()
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("发票识别错误处理报告\n")
            f.write("=" * 50 + "\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"总错误数量: {stats.get('total_errors', 0)}\n")
            f.write(f"平均置信度: {stats.get('avg_confidence', 0):.2f}\n\n")
            
            f.write("错误类型分布:\n")
            for error_type, count in stats.get('error_types', {}).items():
                f.write(f"  {error_type}: {count}\n")
            
            f.write("\n未识别文件目录结构:\n")
            for root, dirs, files in os.walk(self.unrecognized_dir):
                level = root.replace(self.unrecognized_dir, '').count(os.sep)
                indent = ' ' * 2 * level
                f.write(f"{indent}{os.path.basename(root)}/\n")
                subindent = ' ' * 2 * (level + 1)
                for file in files:
                    if not file.endswith('.txt'):
                        f.write(f"{subindent}{file}\n")
        
        logger.info(f"人工审核报告已生成: {report_path}")
        return report_path
