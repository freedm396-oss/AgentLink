#!/usr/bin/env python3
"""
结果验证器
负责验证提取结果的完整性和正确性
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collections import Counter


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    stats: Dict[str, Any]


class ResultValidator:
    """结果验证器"""
    
    def __init__(self):
        """初始化验证器"""
        self.errors = []
        self.warnings = []
    
    def validate(self, figures: List) -> ValidationResult:
        """
        验证提取结果
        
        Args:
            figures: 图片列表
            
        Returns:
            ValidationResult
        """
        self.errors = []
        self.warnings = []
        
        # 检查空结果
        if not figures:
            self.warnings.append("未提取到任何图片")
        
        # 检查必要字段
        for i, fig in enumerate(figures):
            self._validate_figure(fig, i + 1)
        
        # 检查重复
        self._check_duplicates(figures)
        
        # 统计信息
        stats = self._calculate_stats(figures)
        
        return ValidationResult(
            is_valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings,
            stats=stats
        )
    
    def _validate_figure(self, fig, index: int):
        """验证单个图片"""
        # 检查文件路径
        if not fig.file_path:
            self.errors.append(f"图片 {index}: 文件路径为空")
        
        # 检查标题
        if not fig.caption:
            self.warnings.append(f"图片 {index}: 未找到标题")
        
        # 检查尺寸
        if fig.width <= 0 or fig.height <= 0:
            self.errors.append(f"图片 {index}: 无效尺寸 {fig.width}x{fig.height}")
        
        # 检查文件大小
        if fig.file_size_kb <= 0:
            self.warnings.append(f"图片 {index}: 文件大小为0")
    
    def _check_duplicates(self, figures: List):
        """检查重复图片"""
        hashes = [fig.hash for fig in figures if fig.hash]
        duplicate_hashes = [h for h, count in Counter(hashes).items() if count > 1]
        
        if duplicate_hashes:
            self.warnings.append(f"发现 {len(duplicate_hashes)} 组重复图片")
    
    def _calculate_stats(self, figures: List) -> Dict:
        """计算统计信息"""
        if not figures:
            return {}
        
        return {
            'total': len(figures),
            'with_caption': sum(1 for f in figures if f.caption),
            'with_figure_number': sum(1 for f in figures if f.figure_number),
            'caption_rate': sum(1 for f in figures if f.caption) / len(figures) * 100,
            'avg_file_size_kb': sum(f.file_size_kb for f in figures) / len(figures),
            'unique_pages': len(set(f.page for f in figures))
        }
    
    def print_report(self, result: ValidationResult):
        """打印验证报告"""
        print("\n" + "=" * 60)
        print("验证报告")
        print("=" * 60)
        
        if result.is_valid:
            print("✅ 验证通过")
        else:
            print("❌ 验证失败")
        
        print(f"\n统计信息:")
        for key, value in result.stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        
        if result.warnings:
            print(f"\n⚠️  警告 ({len(result.warnings)}):")
            for warning in result.warnings[:5]:  # 只显示前5条
                print(f"  • {warning}")
            if len(result.warnings) > 5:
                print(f"  ... 还有 {len(result.warnings) - 5} 条警告")
        
        if result.errors:
            print(f"\n❌ 错误 ({len(result.errors)}):")
            for error in result.errors:
                print(f"  • {error}")
        
        print("=" * 60 + "\n")