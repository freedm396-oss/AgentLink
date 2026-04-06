#!/usr/bin/env python3
"""
标题识别代理
负责识别PDF中的图片标题/图注
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CaptionMatch:
    """标题匹配结果"""
    text: str
    figure_number: str
    bbox: Tuple[float, float, float, float]
    confidence: float
    pattern_type: str


class CaptionAgent:
    """标题识别代理"""
    
    # 默认匹配模式
    DEFAULT_PATTERNS = [
        # 中文标准格式
        (r'[图圖]\s*(\d+[\.\\-]\d+)\s*[：:]\s*([^\n]{1,200}?)(?=\n|$)', 'chinese_standard', 0.95),
        (r'[图圖]\s*(\d+[\.\\-]\d+)\s+([^\n]{1,200}?)(?=\n|$)', 'chinese_standard_no_colon', 0.90),
        (r'[图圖]\s*(\d+)\s*[：:]\s*([^\n]{1,200}?)(?=\n|$)', 'chinese_single', 0.85),
        
        # 图片/插图变体
        (r'[图圖]片\s*(\d+[\.\\-]?\d*)\s*[：:]\s*([^\n]{1,200}?)(?=\n|$)', 'chinese_picture', 0.85),
        (r'插图\s*(\d+[\.\\-]?\d*)\s*[：:]\s*([^\n]{1,200}?)(?=\n|$)', 'chinese_illustration', 0.85),
        
        # 英文标准格式
        (r'Figure\s+(\d+[\.\\-]\d+)[\.:\-]\s*([^\n]{1,200}?)(?=\n|$)', 'english_standard', 0.95),
        (r'Figure\s+(\d+)[\.:\-]\s*([^\n]{1,200}?)(?=\n|$)', 'english_single', 0.90),
        (r'Fig\.\s*(\d+[\.\\-]\d+)[\.:\-]\s*([^\n]{1,200}?)(?=\n|$)', 'english_abbr', 0.90),
        (r'Fig\.\s*(\d+)[\.:\-]\s*([^\n]{1,200}?)(?=\n|$)', 'english_abbr_single', 0.85),
        
        # 其他格式
        (r'图解\s*(\d+[\.\\-]?\d*)\s*[：:]\s*([^\n]{1,200}?)(?=\n|$)', 'diagram', 0.80),
        (r'表\s*(\d+[\.\\-]?\d*)\s*[：:]\s*([^\n]{1,200}?)(?=\n|$)', 'table', 0.75),
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化标题识别代理
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.patterns = self._load_patterns()
        self.min_confidence = self.config.get('min_confidence', 0.6)
        self.max_distance = self.config.get('max_distance', 150)
    
    def _load_patterns(self) -> List[Tuple]:
        """加载匹配模式"""
        custom_patterns = self.config.get('custom_patterns', [])
        return self.DEFAULT_PATTERNS + custom_patterns
    
    def find_caption(self, text: str, img_bbox: Optional[Tuple] = None,
                    text_blocks: Optional[List] = None) -> Optional[CaptionMatch]:
        """
        在文本中查找图片标题
        
        Args:
            text: 页面文本
            img_bbox: 图片边界框 (x0, y0, x1, y1)
            text_blocks: 文本块列表（用于位置分析）
            
        Returns:
            CaptionMatch 或 None
        """
        best_match = None
        
        # 基于文本内容的匹配
        for pattern, ptype, base_conf in self.patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
            
            for match in matches:
                fig_num = match.group(1)
                caption_text = match.group(2).strip()
                
                # 计算置信度
                confidence = base_conf
                
                # 位置加分
                if img_bbox and text_blocks:
                    position_score = self._calculate_position_score(img_bbox, match.start(), text_blocks)
                    confidence += position_score * 0.1
                
                # 长度过滤
                if len(caption_text) < 3 or len(caption_text) > 200:
                    confidence -= 0.2
                
                # 内容质量检查
                if self._is_valid_caption(caption_text):
                    confidence += 0.05
                
                if confidence > self.min_confidence:
                    if best_match is None or confidence > best_match.confidence:
                        best_match = CaptionMatch(
                            text=caption_text,
                            figure_number=fig_num,
                            bbox=self._get_match_bbox(match, text_blocks),
                            confidence=min(confidence, 1.0),
                            pattern_type=ptype
                        )
        
        return best_match
    
    def _calculate_position_score(self, img_bbox: Tuple, match_pos: int,
                                  text_blocks: List) -> float:
        """计算位置匹配分数"""
        try:
            # 获取匹配位置的文本块
            for block in text_blocks:
                if block.get('bbox') and match_pos >= block.get('bbox')[1]:
                    text_bbox = block['bbox']
                    img_bottom = img_bbox[3]
                    text_top = text_bbox[1]
                    vertical_dist = text_top - img_bottom
                    
                    # 标题应该在图片下方 0-150 像素内
                    if 0 < vertical_dist < self.max_distance:
                        # 距离越近分数越高
                        return 1.0 - (vertical_dist / self.max_distance)
        except Exception:
            pass
        
        return 0.0
    
    def _get_match_bbox(self, match, text_blocks: Optional[List]) -> Optional[Tuple]:
        """获取匹配文本的边界框"""
        if not text_blocks:
            return None
        
        match_start = match.start()
        for block in text_blocks:
            if block.get('bbox') and block.get('text'):
                if match_start in block.get('text', ''):
                    return block['bbox']
        return None
    
    def _is_valid_caption(self, text: str) -> bool:
        """验证标题内容是否有效"""
        # 太短的标题
        if len(text) < 3:
            return False
        
        # 包含无效字符
        invalid_patterns = [
            r'^\s*$',  # 空字符串
            r'^\d+$',  # 纯数字
            r'^[.,;:!?]+$',  # 纯标点
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, text):
                return False
        
        return True
    
    def add_pattern(self, pattern: str, pattern_type: str, confidence: float = 0.85):
        """添加自定义匹配模式"""
        self.patterns.append((pattern, pattern_type, confidence))
    
    def batch_find(self, texts: List[str]) -> List[Optional[CaptionMatch]]:
        """批量查找标题"""
        return [self.find_caption(text) for text in texts]