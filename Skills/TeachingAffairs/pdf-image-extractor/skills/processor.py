#!/usr/bin/env python3
"""
图片处理器
负责后处理、优化和转换图片
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class ProcessedFigure:
    """处理后的图片信息"""
    original: Any
    processed: Any


class ImageProcessor:
    """图片处理器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化处理器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
    
    def post_process(self, figures: List) -> List:
        """
        后处理图片列表
        
        Args:
            figures: 原始图片列表
            
        Returns:
            处理后的图片列表
        """
        # 按页码和索引排序
        figures.sort(key=lambda f: (f.page, f.index))
        
        # 补充默认标题
        for i, fig in enumerate(figures, 1):
            if not fig.caption:
                fig.caption = f"[未识别标题] 第{fig.page}页第{fig.index}张图片"
            if not fig.figure_number:
                fig.figure_number = f"图{i}"
        
        # 去重（基于内容哈希）
        seen_hashes = set()
        unique_figures = []
        for fig in figures:
            if fig.hash not in seen_hashes:
                seen_hashes.add(fig.hash)
                unique_figures.append(fig)
        
        return unique_figures
    
    def merge_by_chapter(self, figures: List) -> Dict[str, List]:
        """按章节分组"""
        by_chapter = defaultdict(list)
        for fig in figures:
            by_chapter[fig.chapter].append(fig)
        return dict(by_chapter)
    
    def filter_by_size(self, figures: List, min_size: int = 0, max_size: int = float('inf')) -> List:
        """按尺寸过滤"""
        return [
            fig for fig in figures
            if min_size <= fig.width <= max_size and min_size <= fig.height <= max_size
        ]
    
    def filter_by_type(self, figures: List, image_type: str) -> List:
        """按类型过滤"""
        return [fig for fig in figures if fig.image_type == image_type]
    
    def add_metadata(self, figures: List, metadata: Dict) -> List:
        """添加元数据"""
        for fig in figures:
            if not hasattr(fig, 'metadata'):
                fig.metadata = {}
            fig.metadata.update(metadata)
        return figures
    
    def generate_thumbnails(self, figures: List, size: int = 100) -> List:
        """
        生成缩略图（占位实现）
        
        Args:
            figures: 图片列表
            size: 缩略图尺寸
            
        Returns:
            添加了缩略图路径的图片列表
        """
        # 实际实现需要 PIL 库支持
        # 这里只是占位
        for fig in figures:
            fig.thumbnail = f"{fig.file_path}_thumb_{size}.jpg"
        return figures