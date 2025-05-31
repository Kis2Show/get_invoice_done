#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class InvoiceRecognitionEngine:
    """基于基本规则的发票识别引擎 - 支持多种发票样式"""

    def __init__(self):
        self.mubo_tax_number = "91330225MA2J4X2M2B"
        self.mubo_company_name = "宁波牧柏科技咨询有限公司"

        # 发票类型识别关键词
        self.invoice_type_keywords = {
            'electronic': ['电子发票', '通用发票', '电子普通发票'],
            'special': ['增值税专用发票', '专用发票'],
            'fuel': ['成品油', '成品油发票']
        }
    
    def extract_invoice_info(self, text: str) -> Dict[str, Optional[str]]:
        """根据基本规则提取发票信息 - 支持多种发票样式"""

        info = {
            'invoice_number': None,
            'invoice_date': None,
            'seller_name': None,
            'seller_tax_number': None,
            'buyer_name': None,
            'buyer_tax_number': None,
            'amount_without_tax': None,
            'tax_amount': None,
            'total_amount': None,
            'invoice_content': None,
            'invoice_type': None,
            'recognition_attempts': 1,
        }

        try:
            # 步骤1: 识别发票类型
            invoice_type = self._identify_invoice_type(text)
            info['invoice_type'] = invoice_type
            logger.info(f"识别发票类型: {invoice_type}")

            # 步骤2: 发票号码和开票日期在右上角
            self._extract_basic_info(text, info, invoice_type)

            # 步骤3: 金额部分 - 先提取，因为其他规则可能依赖
            self._extract_amounts(text, info, invoice_type)

            # 步骤4: 根据发票类型选择布局模式提取公司信息
            self._extract_companies_by_layout(text, info, invoice_type)

            # 步骤5: 提取公司抬头与税号
            self._extract_tax_numbers(text, info)

            # 步骤6: 开票内容
            self._extract_invoice_content(text, info, invoice_type)

            # 步骤7: 多次识别纠错机制
            self._apply_correction_attempts(text, info, invoice_type)

            # 步骤8: 最终验证和修正
            self._validate_and_correct(info)

        except Exception as e:
            logger.error(f"发票信息提取出错: {e}")

        return info

    def _apply_correction_attempts(self, text: str, info: Dict[str, Optional[str]], invoice_type: str):
        """多次识别纠错机制 - 针对未识别的字段进行多次尝试"""
        max_attempts = 3
        unrecognized_fields = []

        # 检查哪些关键字段未识别
        critical_fields = ['invoice_number', 'invoice_date', 'seller_name', 'buyer_name', 'total_amount']
        for field in critical_fields:
            if not info.get(field) or info[field] in ['未识别', '未知', None, '']:
                unrecognized_fields.append(field)

        if not unrecognized_fields:
            return

        logger.info(f"发现未识别字段: {unrecognized_fields}, 开始多次识别纠错")

        for attempt in range(2, max_attempts + 1):
            info['recognition_attempts'] = attempt
            logger.info(f"第 {attempt} 次识别尝试")

            # 针对不同字段使用不同的纠错策略
            for field in unrecognized_fields[:]:  # 使用切片避免修改迭代中的列表
                if field == 'invoice_number':
                    self._retry_invoice_number_extraction(text, info)
                elif field == 'invoice_date':
                    self._retry_date_extraction(text, info)
                elif field == 'seller_name':
                    self._retry_seller_extraction(text, info, invoice_type)
                elif field == 'buyer_name':
                    self._retry_buyer_extraction(text, info, invoice_type)
                elif field == 'total_amount':
                    self._retry_amount_extraction(text, info, invoice_type)

                # 如果字段已识别，从未识别列表中移除
                if info.get(field) and info[field] not in ['未识别', '未知', None, '']:
                    unrecognized_fields.remove(field)
                    logger.info(f"字段 {field} 在第 {attempt} 次尝试中成功识别: {info[field]}")

            # 如果所有字段都已识别，退出
            if not unrecognized_fields:
                logger.info(f"所有字段在第 {attempt} 次尝试后成功识别")
                break

        if unrecognized_fields:
            logger.warning(f"经过 {max_attempts} 次尝试，仍有字段未识别: {unrecognized_fields}")

    def _retry_invoice_number_extraction(self, text: str, info: Dict[str, Optional[str]]):
        """重试发票号码提取 - 使用更宽松的模式"""
        patterns = [
            r'发票号码[：:\s]*(\d{8,12})',
            r'No[：:\s]*(\d{8,12})',
            r'号码[：:\s]*(\d{8,12})',
            r'(\d{8,12})',  # 最宽松的模式，匹配8-12位数字
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # 选择最可能的发票号码（通常是8位数字）
                for match in matches:
                    if 8 <= len(match) <= 12:
                        info['invoice_number'] = match
                        logger.info(f"重试识别发票号码成功: {match}")
                        return

    def _retry_date_extraction(self, text: str, info: Dict[str, Optional[str]]):
        """重试日期提取 - 使用更多日期格式"""
        patterns = [
            r'开票日期[：:\s]*(\d{4}年\d{1,2}月\d{1,2}日)',
            r'开票日期[：:\s]*(\d{4}-\d{1,2}-\d{1,2})',
            r'开票日期[：:\s]*(\d{4}/\d{1,2}/\d{1,2})',
            r'日期[：:\s]*(\d{4}年\d{1,2}月\d{1,2}日)',
            r'(\d{4}年\d{1,2}月\d{1,2}日)',
            r'(\d{4}-\d{1,2}-\d{1,2})',
            r'(\d{4}/\d{1,2}/\d{1,2})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                # 标准化日期格式
                date_str = re.sub(r'年|月', '-', date_str).replace('日', '')
                date_str = re.sub(r'/', '-', date_str)
                info['invoice_date'] = date_str
                logger.info(f"重试识别开票日期成功: {date_str}")
                return

    def _retry_seller_extraction(self, text: str, info: Dict[str, Optional[str]], invoice_type: str):
        """重试销售方提取 - 使用更灵活的模式"""
        # 成品油发票的特殊处理
        if '成品油' in invoice_type or '加油' in text:
            patterns = [
                r'销售方[：:\s]*([^购买方\n]{5,30})',
                r'开户行及账号[：:\s]*[^销售方]*销售方[：:\s]*([^购买方\n]{5,30})',
                r'([^购买方\n]*加油站[^购买方\n]*)',
                r'([^购买方\n]*石油[^购买方\n]*)',
                r'([^购买方\n]*能源[^购买方\n]*)',
            ]
        else:
            patterns = [
                r'销售方[：:\s]*([^购买方\n]{5,50})',
                r'卖方[：:\s]*([^购买方\n]{5,50})',
                r'开票方[：:\s]*([^购买方\n]{5,50})',
            ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                seller = match.group(1).strip()
                if len(seller) >= 5 and '宁波牧柏科技咨询有限公司' not in seller:
                    info['seller_name'] = seller
                    logger.info(f"重试识别销售方成功: {seller}")
                    return

    def _retry_buyer_extraction(self, text: str, info: Dict[str, Optional[str]], invoice_type: str):
        """重试购买方提取 - 特别处理宁波牧柏科技咨询有限公司"""
        patterns = [
            r'购买方[：:\s]*([^销售方\n]{5,50})',
            r'买方[：:\s]*([^销售方\n]{5,50})',
            r'(宁波牧柏科技咨询有限公司)',
            r'购买方[：:\s]*纳税人识别号[：:\s]*[^销售方]*([^销售方\n]{5,50})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                buyer = match.group(1).strip()
                if len(buyer) >= 5:
                    info['buyer_name'] = buyer
                    logger.info(f"重试识别购买方成功: {buyer}")
                    return

    def _retry_amount_extraction(self, text: str, info: Dict[str, Optional[str]], invoice_type: str):
        """重试金额提取 - 使用更多金额模式"""
        # 寻找小写金额（总金额）
        patterns = [
            r'小写[：:\s]*¥?(\d+\.?\d*)',
            r'价税合计[：:\s]*¥?(\d+\.?\d*)',
            r'合计[：:\s]*¥?(\d+\.?\d*)',
            r'总金额[：:\s]*¥?(\d+\.?\d*)',
            r'¥(\d+\.?\d*)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # 选择最大的金额作为总金额
                amounts = [float(m) for m in matches if float(m) > 0]
                if amounts:
                    total_amount = max(amounts)
                    info['total_amount'] = f"{total_amount:.2f}"
                    logger.info(f"重试识别总金额成功: {total_amount:.2f}")
                    return

    def _identify_invoice_type(self, text: str) -> str:
        """识别发票类型"""

        # 检查成品油发票 - 扩展关键词
        fuel_keywords = ['成品油', '加油', '汽油', '柴油', '燃油', '石油', '中石化', '中石油', '加油站', '能源']
        if any(keyword in text for keyword in fuel_keywords):
            return 'fuel'

        # 检查专用发票
        if any(keyword in text for keyword in self.invoice_type_keywords['special']):
            return 'special'

        # 检查电子发票
        if any(keyword in text for keyword in self.invoice_type_keywords['electronic']):
            return 'electronic'

        # 默认为电子发票
        return 'electronic'
    
    def _extract_basic_info(self, text: str, info: Dict[str, Optional[str]], invoice_type: str):
        """提取发票号码和开票日期 - 支持多种发票样式"""

        # 发票号码提取 - 适应不同样式
        number_patterns = [
            r'发票号码[：:]\s*(\d{8,20})',
            r'号码[：:]\s*(\d{8,20})',
            r'Invoice\s*No[：:]\s*(\d{8,20})',
        ]

        for pattern in number_patterns:
            match = re.search(pattern, text)
            if match:
                info['invoice_number'] = match.group(1)
                logger.info(f"发票号码: {match.group(1)}")
                break

        # 如果没有明确标识，查找合适长度的数字
        if not info['invoice_number']:
            # 根据发票类型选择不同的匹配策略
            if invoice_type == 'fuel':
                # 成品油发票号码通常较短
                short_numbers = re.findall(r'\b(\d{8,12})\b', text)
                for num in short_numbers:
                    info['invoice_number'] = num
                    logger.info(f"发票号码(成品油): {num}")
                    break
            else:
                # 电子发票通常是20位
                long_numbers = re.findall(r'\b(\d{20})\b', text)
                if long_numbers:
                    info['invoice_number'] = long_numbers[0]
                    logger.info(f"发票号码(20位): {long_numbers[0]}")

        # 开票日期提取
        date_patterns = [
            r'开票日期[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日)',
            r'开票日期[：:]\s*(\d{4}-\d{1,2}-\d{1,2})',
            r'(\d{4}年\d{1,2}月\d{1,2}日)',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                # 转换为标准格式
                if '年' in date_str:
                    date_str = re.sub(r'(\d{4})年(\d{1,2})月(\d{1,2})日', r'\1-\2-\3', date_str)
                info['invoice_date'] = date_str
                logger.info(f"开票日期: {date_str}")
                break
    
    def _extract_amounts(self, text: str, info: Dict[str, Optional[str]], invoice_type: str):
        """金额部分提取和验证 - 支持多种发票样式"""

        # 根据发票类型选择不同的金额提取策略
        if invoice_type == 'fuel':
            self._extract_amounts_fuel(text, info)
        else:
            self._extract_amounts_standard(text, info)

    def _extract_amounts_standard(self, text: str, info: Dict[str, Optional[str]]):
        """标准发票金额提取（电子发票、普通发票）"""

        # 优先查找"小写"后的金额
        total_amount = None

        # 方法1: 查找"小写"关键字后的金额
        if '小写' in text:
            small_case_patterns = [
                r'小写[：:]*\s*¥\s*([\d,]+\.?\d*)',
                r'\(小写\)\s*¥\s*([\d,]+\.?\d*)',
                r'小写.*?¥\s*([\d,]+\.?\d*)',
            ]

            for pattern in small_case_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    amount = self._parse_amount(match)
                    if amount and amount > 0:
                        total_amount = amount
                        info['total_amount'] = amount
                        logger.info(f"从'小写'提取总金额: {amount}")
                        break
                if total_amount:
                    break

        # 方法2: 查找所有金额并智能选择
        if not total_amount:
            all_amounts = []
            amount_patterns = [
                r'¥\s*([\d,]+\.\d{2})',  # ¥35.02
                r'([\d,]+\.\d{2})',      # 35.02
            ]

            for pattern in amount_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    amount = self._parse_amount(match)
                    if amount and 0.01 <= amount <= 999999.99:
                        all_amounts.append(amount)

            # 去重并排序
            all_amounts = sorted(list(set(all_amounts)))
            logger.info(f"发现所有合理金额: {all_amounts}")

            if all_amounts:
                total_amount = max(all_amounts)
                info['total_amount'] = total_amount
                logger.info(f"选择最大金额作为总金额: {total_amount}")

        # 智能金额组合匹配
        if total_amount:
            self._match_amount_combination(all_amounts if 'all_amounts' in locals() else [total_amount], total_amount, info)

    def _extract_amounts_fuel(self, text: str, info: Dict[str, Optional[str]]):
        """成品油发票金额提取 - 优化版本"""

        # 成品油发票通常有详细的表格结构
        # 优先查找"小写"后的金额
        total_amount = None

        # 方法1: 查找"小写"关键字后的金额 - 扩展模式
        if '小写' in text:
            small_case_patterns = [
                r'[（(]小写[）)]\s*¥\s*([\d,]+\.?\d*)',
                r'小写[：:]*\s*¥\s*([\d,]+\.?\d*)',
                r'小写.*?¥\s*([\d,]+\.?\d*)',
                r'小写[：:\s]*(\d+\.\d{2})',  # 不带¥符号
                r'小写[：:\s]*(\d+)',  # 整数金额
            ]

            for pattern in small_case_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    amount = self._parse_amount(match)
                    if amount and amount > 0:
                        total_amount = amount
                        info['total_amount'] = amount
                        logger.info(f"成品油发票从'小写'提取总金额: {amount}")
                        break
                if total_amount:
                    break

        # 方法2: 查找价税合计 - 扩展模式
        if not total_amount:
            total_patterns = [
                r'价税合计\s*[（(]大写[）)]\s*.*?[（(]小写[）)]\s*¥\s*([\d,]+\.?\d*)',
                r'价税合计.*?¥\s*([\d,]+\.?\d*)',
                r'合计.*?¥\s*([\d,]+\.?\d*)',
                r'价税合计[：:\s]*(\d+\.\d{2})',
                r'合\s*计[：:\s]*(\d+\.\d{2})',
            ]

            for pattern in total_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    amount = self._parse_amount(match)
                    if amount and amount > 0:
                        total_amount = amount
                        info['total_amount'] = amount
                        logger.info(f"成品油发票总金额: {amount}")
                        break
                if total_amount:
                    break

        # 方法3: 表格结构分析 - 针对复杂表格
        if not total_amount:
            total_amount = self._extract_amount_from_table_structure(text, info)

        # 查找金额和税额
        if total_amount:
            # 查找表格中的金额和税额 - 扩展模式
            amount_patterns = [
                r'金额[：:\s]*(\d+\.\d{2})',  # 明确的金额字段
                r'税额[：:\s]*(\d+\.\d{2})',  # 明确的税额字段
                r'不含税金额[：:\s]*(\d+\.\d{2})',
                r'税率[：:\s]*\d+%[：:\s]*(\d+\.\d{2})',  # 税率后的金额
                r'(\d+\.\d{2})',  # 表格中的金额
            ]

            all_amounts = []
            for pattern in amount_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    amount = self._parse_amount(match)
                    if amount and amount < total_amount and amount > 0:
                        all_amounts.append(amount)

            # 去重并排序
            all_amounts = sorted(list(set(all_amounts)), reverse=True)
            logger.info(f"成品油发票其他金额: {all_amounts}")

            self._match_amount_combination(all_amounts, total_amount, info)

    def _extract_amount_from_table_structure(self, text: str, info: Dict[str, Optional[str]]) -> Optional[float]:
        """从表格结构中提取金额 - 针对复杂成品油发票表格"""

        # 将文本按行分割，分析表格结构
        lines = text.split('\n')

        # 查找包含金额的行
        amount_lines = []
        for line_idx, line in enumerate(lines):
            # 查找包含多个金额的行（通常是表格数据行）
            amounts_in_line = re.findall(r'(\d+\.\d{2})', line)
            if len(amounts_in_line) >= 2:  # 至少包含2个金额
                amount_lines.append((line_idx, line, amounts_in_line))

        logger.info(f"发现包含金额的表格行: {len(amount_lines)}")

        # 分析最可能的总金额
        for line_idx, line, amounts in amount_lines:
            # 转换为浮点数
            float_amounts = []
            for amt_str in amounts:
                try:
                    float_amounts.append(float(amt_str))
                except ValueError:
                    continue

            if len(float_amounts) >= 2:
                # 选择最大的金额作为可能的总金额
                max_amount = max(float_amounts)

                # 验证是否合理（通常成品油发票金额在合理范围内）
                if 1.0 <= max_amount <= 10000.0:
                    logger.info(f"从表格结构提取总金额: {max_amount}")
                    return max_amount

        return None

    def _match_amount_combination(self, all_amounts: list, total_amount: float, info: Dict[str, Optional[str]]):
        """智能匹配金额组合"""

        # 规则1: 税额 < 不含税金额，且 不含税金额 + 税额 = 总金额
        best_combination = None
        min_diff = float('inf')

        for amount1 in all_amounts:
            for amount2 in all_amounts:
                if amount1 != amount2:
                    # 确保税额小于不含税金额
                    if amount2 < amount1:
                        no_tax_amount = amount1
                        tax_amount = amount2
                    else:
                        no_tax_amount = amount2
                        tax_amount = amount1

                    # 验证加法等式
                    calculated_total = no_tax_amount + tax_amount
                    diff = abs(calculated_total - total_amount)

                    if diff < min_diff and diff < 0.01:  # 允许0.01的误差
                        min_diff = diff
                        best_combination = (no_tax_amount, tax_amount)

        if best_combination:
            info['amount_without_tax'] = best_combination[0]
            info['tax_amount'] = best_combination[1]
            logger.info(f"最佳金额组合: 不含税={best_combination[0]}, 税额={best_combination[1]}, 合计={total_amount}")
        else:
            # 如果没有找到完美组合，尝试不征税发票
            if total_amount in all_amounts:
                info['amount_without_tax'] = total_amount
                info['tax_amount'] = 0.0
                logger.info(f"不征税发票: 不含税={total_amount}, 税额=0.0")
            else:
                # 尝试从总金额推算
                common_tax_rates = [0.13, 0.09, 0.06, 0.03]
                for rate in common_tax_rates:
                    no_tax_amount = total_amount / (1 + rate)
                    tax_amount = total_amount - no_tax_amount

                    # 检查计算出的金额是否在发现的金额列表中
                    no_tax_found = any(abs(amt - no_tax_amount) < 0.01 for amt in all_amounts)
                    tax_found = any(abs(amt - tax_amount) < 0.01 for amt in all_amounts)

                    if no_tax_found and tax_found:
                        info['amount_without_tax'] = round(no_tax_amount, 2)
                        info['tax_amount'] = round(tax_amount, 2)
                        logger.info(f"按税率{rate*100}%推算: 不含税={info['amount_without_tax']}, 税额={info['tax_amount']}")
                        break
    
    def _extract_companies_by_layout(self, text: str, info: Dict[str, Optional[str]], invoice_type: str):
        """根据发票类型选择布局模式提取公司信息"""

        if invoice_type == 'fuel':
            self._extract_companies_fuel_layout(text, info)
        else:
            self._extract_companies_standard_layout(text, info)

    def _extract_companies_standard_layout(self, text: str, info: Dict[str, Optional[str]]):
        """标准布局：购买方在左/上，销售方在右/下"""

        # 查找所有公司名称及其位置
        company_pattern = r'([^，。！？\s]{2,}(?:有限公司|股份有限公司|集团|公司|企业|商店|商行|厂|店))'
        company_matches = []

        for match in re.finditer(company_pattern, text):
            company_name = match.group(1)
            position = match.start()

            # 清理公司名称
            company_name = re.sub(r'^[名称：:]+', '', company_name)
            company_name = company_name.strip()

            if len(company_name) > 3:  # 过滤太短的匹配
                company_matches.append((company_name, position))

        # 按位置排序
        company_matches.sort(key=lambda x: x[1])
        logger.info(f"标准布局公司名称: {company_matches}")

        if len(company_matches) >= 2:
            # 规则: 购买方在前，销售方在后
            buyer_candidate = company_matches[0][0]
            seller_candidate = company_matches[1][0]

            # 特殊规则: 宁波牧柏始终是购买方
            if self.mubo_company_name in buyer_candidate:
                info['buyer_name'] = buyer_candidate
                info['seller_name'] = seller_candidate
            elif self.mubo_company_name in seller_candidate:
                info['buyer_name'] = seller_candidate
                info['seller_name'] = buyer_candidate
            else:
                # 按位置分配
                info['buyer_name'] = buyer_candidate
                info['seller_name'] = seller_candidate

            logger.info(f"标准布局分配: 购买方={info['buyer_name']}, 销售方={info['seller_name']}")

        elif len(company_matches) == 1:
            # 只有一个公司，通常是宁波牧柏
            company_name = company_matches[0][0]
            if self.mubo_company_name in company_name:
                info['buyer_name'] = company_name
                logger.info(f"单一公司识别为购买方: {company_name}")

    def _extract_companies_fuel_layout(self, text: str, info: Dict[str, Optional[str]]):
        """成品油发票布局：购买方在上方，销售方在下方 - 优化版本"""

        # 成品油发票的特殊布局识别
        # 购买方通常在发票上半部分
        # 销售方通常在发票下半部分（销售方信息区域）

        # 先找宁波牧柏（购买方）- 使用更多模式
        mubo_patterns = [
            r'(宁波牧柏科技咨询有限公司)',
            r'购买方.*?(宁波牧柏科技咨询有限公司)',
            r'买\s*方.*?(宁波牧柏科技咨询有限公司)',
            r'纳税人识别号.*?91330225MA2J4X2M2B.*?(宁波牧柏科技咨询有限公司)',
        ]

        for pattern in mubo_patterns:
            match = re.search(pattern, text)
            if match:
                info['buyer_name'] = self.mubo_company_name
                logger.info(f"成品油发票购买方: {self.mubo_company_name}")
                break

        # 查找销售方 - 优化模式，特别针对成品油发票的表格结构
        seller_patterns = [
            # 明确的销售方标识
            r'销售方[：:\s]*名称[：:\s]*([^，。！？\n\r\t购买方]{5,50}(?:有限公司|股份有限公司|集团|公司|企业|商店|商行|厂|店))',
            r'销\s*售\s*方[：:\s]*([^，。！？\n\r\t购买方]{5,50}(?:有限公司|股份有限公司|集团|公司|企业|商店|商行|厂|店))',

            # 加油站相关
            r'([^，。！？\s购买方]{2,30}(?:加油站|石油|能源|燃气)(?:有限公司|股份有限公司|集团|公司|企业))',

            # 表格中的公司名称（排除购买方区域）
            r'纳税人识别号[：:\s]*[A-Z0-9]{15,20}[^购买方]*?([^，。！？\n\r\t购买方]{5,50}(?:有限公司|股份有限公司|集团|公司|企业|商店|商行|厂|店))',

            # 开户行信息附近的公司名称
            r'开户行及账号[：:\s]*[^销售方]*?([^，。！？\n\r\t购买方]{5,50}(?:有限公司|股份有限公司|集团|公司|企业|商店|商行|厂|店))',
        ]

        for pattern in seller_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                seller_name = match.strip()
                # 清理可能的前缀
                seller_name = re.sub(r'^[名称：:\s]+', '', seller_name)
                seller_name = seller_name.strip()

                # 确保不是购买方且长度合理
                if (len(seller_name) >= 5 and
                    self.mubo_company_name not in seller_name and
                    '购买方' not in seller_name and
                    '买方' not in seller_name and
                    '纳税人' not in seller_name):
                    info['seller_name'] = seller_name
                    logger.info(f"成品油发票销售方: {seller_name}")
                    break
            if info.get('seller_name'):
                break

        # 如果还没找到销售方，使用位置分析方法
        if not info.get('seller_name'):
            self._extract_seller_by_position_analysis(text, info)

    def _extract_seller_by_position_analysis(self, text: str, info: Dict[str, Optional[str]]):
        """通过位置分析提取销售方 - 针对复杂表格结构"""

        # 将文本按行分割
        lines = text.split('\n')
        company_candidates = []

        # 查找所有公司名称及其行号
        company_pattern = r'([^，。！？\s]{3,50}(?:有限公司|股份有限公司|集团|公司|企业|商店|商行|厂|店))'

        for line_idx, line in enumerate(lines):
            matches = re.findall(company_pattern, line)
            for match in matches:
                company_name = match.strip()
                # 清理前缀
                company_name = re.sub(r'^[名称：:\s]+', '', company_name)
                company_name = company_name.strip()

                if (len(company_name) >= 5 and
                    self.mubo_company_name not in company_name and
                    '购买方' not in company_name and
                    '买方' not in company_name):
                    company_candidates.append((company_name, line_idx, line))

        logger.info(f"位置分析发现的公司候选: {[(name, idx) for name, idx, _ in company_candidates]}")

        # 选择最可能的销售方
        if company_candidates:
            # 优先选择包含加油站、石油、能源等关键词的公司
            fuel_keywords = ['加油站', '石油', '能源', '燃气', '中石化', '中石油']
            for company_name, line_idx, line in company_candidates:
                if any(keyword in company_name for keyword in fuel_keywords):
                    info['seller_name'] = company_name
                    logger.info(f"成品油发票销售方(关键词匹配): {company_name}")
                    return

            # 如果没有关键词匹配，选择第一个候选
            info['seller_name'] = company_candidates[0][0]
            logger.info(f"成品油发票销售方(位置分析): {company_candidates[0][0]}")
    
    def _extract_tax_numbers(self, text: str, info: Dict[str, Optional[str]]):
        """规则4: 提取税号"""
        
        # 查找所有税号
        tax_numbers = re.findall(r'([A-Z0-9]{15,20})', text)
        
        # 过滤掉发票号码
        filtered_tax_numbers = []
        for tax in tax_numbers:
            if not (len(tax) == 20 and tax.isdigit()):  # 排除20位纯数字（发票号码）
                filtered_tax_numbers.append(tax)
        
        logger.info(f"过滤后税号: {filtered_tax_numbers}")
        
        # 宁波牧柏税号识别和OCR纠错
        mubo_tax_found = False
        if self.mubo_tax_number in filtered_tax_numbers:
            info['buyer_tax_number'] = self.mubo_tax_number
            mubo_tax_found = True
        else:
            # OCR纠错：查找以91330225开头的税号
            for tax in filtered_tax_numbers:
                if tax.startswith("91330225") and len(tax) >= 15:
                    info['buyer_tax_number'] = self.mubo_tax_number  # 纠正为正确版本
                    mubo_tax_found = True
                    logger.info(f"OCR纠错: {tax} -> {self.mubo_tax_number}")
                    break
        
        # 分配销售方税号
        for tax in filtered_tax_numbers:
            if tax != info.get('buyer_tax_number') and not tax.startswith("91330225"):
                if len(tax) >= 15 and not tax.isdigit():
                    info['seller_tax_number'] = tax
                    logger.info(f"销售方税号: {tax}")
                    break
        
        # 如果没找到销售方税号，放宽条件
        if not info.get('seller_tax_number'):
            for tax in filtered_tax_numbers:
                if tax != info.get('buyer_tax_number') and not tax.startswith("91330225"):
                    info['seller_tax_number'] = tax
                    logger.info(f"销售方税号(放宽): {tax}")
                    break
    
    def _extract_invoice_content(self, text: str, info: Dict[str, Optional[str]], invoice_type: str):
        """提取开票内容 - 支持多种发票样式"""

        if invoice_type == 'fuel':
            self._extract_content_fuel(text, info)
        else:
            self._extract_content_standard(text, info)

    def _extract_content_standard(self, text: str, info: Dict[str, Optional[str]]):
        """标准发票开票内容提取"""

        content_patterns = [
            r'项目名称[：:]\s*([^\n\r\t]+)',
            r'货物或应税劳务、服务名称[：:]\s*([^\n\r\t]+)',
            r'货物或应税劳务名称[：:]\s*([^\n\r\t]+)',
            r'商品名称[：:]\s*([^\n\r\t]+)',
        ]

        for pattern in content_patterns:
            match = re.search(pattern, text)
            if match:
                content = match.group(1).strip()
                if len(content) > 1:
                    info['invoice_content'] = content
                    logger.info(f"标准发票开票内容: {content}")
                    break

    def _extract_content_fuel(self, text: str, info: Dict[str, Optional[str]]):
        """成品油发票开票内容提取"""

        # 成品油发票的商品信息更详细
        fuel_patterns = [
            r'货物或应税劳务、服务名称[：:]\s*([^\n\r\t]+)',
            r'(汽油\d+号[^，。！？\n\r\t]*)',
            r'(柴油[^，。！？\n\r\t]*)',
            r'(成品油[^，。！？\n\r\t]*)',
            r'([^，。！？\s]*油[^，。！？\n\r\t]*)',
        ]

        for pattern in fuel_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                content = match.strip()
                if len(content) > 2 and '油' in content:
                    info['invoice_content'] = content
                    logger.info(f"成品油发票开票内容: {content}")
                    return

        # 如果没找到特定内容，使用标准方法
        self._extract_content_standard(text, info)
    
    def _validate_and_correct(self, info: Dict[str, Optional[str]]):
        """最终验证和修正"""
        
        # 验证金额逻辑
        if (info.get('amount_without_tax') and info.get('tax_amount') and info.get('total_amount')):
            calculated = info['amount_without_tax'] + info['tax_amount']
            if abs(calculated - info['total_amount']) > 0.01:
                logger.warning(f"金额验证失败: {info['amount_without_tax']} + {info['tax_amount']} != {info['total_amount']}")
        
        # 确保宁波牧柏是购买方
        if info.get('buyer_name') and self.mubo_company_name not in info['buyer_name']:
            if info.get('seller_name') and self.mubo_company_name in info['seller_name']:
                # 交换买卖方
                info['buyer_name'], info['seller_name'] = info['seller_name'], info['buyer_name']
                info['buyer_tax_number'], info['seller_tax_number'] = info['seller_tax_number'], info['buyer_tax_number']
                logger.info("交换买卖方信息，确保宁波牧柏为购买方")
        
        # 确保购买方税号正确
        if info.get('buyer_name') and self.mubo_company_name in info['buyer_name']:
            info['buyer_tax_number'] = self.mubo_tax_number
        
        logger.info(f"最终结果: {info}")

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
