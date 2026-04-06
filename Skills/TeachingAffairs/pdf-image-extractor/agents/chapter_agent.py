#!/usr/bin/env python3
"""
章节检测代理
负责识别PDF中的章节结构
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ChapterInfo:
    """章节信息"""
    level: int
    number: str
    title: str
    page: int
    full_path: str


class ChapterAgent:
    """章节检测代理"""
    
    # 章节模式
    CHAPTER_PATTERNS = [
        # 中文章节
        (r'^\s*第\s*([一二三四五六七八九十\d]+)\s*章\s*[.\s]*([^\n]{1,100})', 'chinese', 0.95, 1),
        (r'^\s*第\s*([一二三四五六七八九十]+)\s*节\s*([^\n]{1,100})', 'chinese_section', 0.90, 2),
        
        # 英文章节
        (r'^\s*Chapter\s+(\d+)[.\s]+([^\n]{1,100})', 'english', 0.95, 1),
        (r'^\s*Section\s+(\d+)[.\s]+([^\n]{1,100})', 'english_section', 0.90, 2),
        
        # 编号章节
        (r'^\s*(\d+)\s*\.\s*([A-Z][^\n]{1,100})', 'numbered_chapter', 0.85, 1),
        (r'^\s*(\d+\.\d+)\s+([A-Z][^\n]{1,100})', 'numbered_section', 0.85, 2),
        (r'^\s*(\d+\.\d+\.\d+)\s+([^\n]{1,100})', 'numbered_subsection', 0.80, 3),
        
        # 其他格式
        (r'^\s*(\d+)\s+([A-Z][^\n]{1,100})', 'simple_numbered', 0.75, 1),
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化章节检测代理
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.patterns = self._load_patterns()
        self.current_chapter = None
        self.chapter_stack = []
        self.min_confidence = self.config.get('min_confidence', 0.7)
    
    def _load_patterns(self) -> List[Tuple]:
        """加载章节模式"""
        custom_patterns = self.config.get('custom_chapter_patterns', [])
        return self.CHAPTER_PATTERNS + custom_patterns
    
    def detect_chapter(self, text: str, page_num: int) -> Optional[ChapterInfo]:
        """
        检测文本中的章节标题
        
        Args:
            text: 页面文本
            page_num: 页码
            
        Returns:
            ChapterInfo 或 None
        """
        lines = text.split('\n')
        
        # 只检查前30行（章节标题通常在页面顶部）
        for line in lines[:30]:
            line = line.strip()
            if not line:
                continue
            
            for pattern, ptype, confidence, level in self.patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match and confidence >= self.min_confidence:
                    chapter_num = match.group(1)
                    chapter_title = match.group(2).strip()
                    
                    # 清理标题
                    chapter_title = self._clean_title(chapter_title)
                    
                    # 构建完整路径
                    full_path = self._build_full_path(level, chapter_num, chapter_title)
                    
                    chapter_info = ChapterInfo(
                        level=level,
                        number=chapter_num,
                        title=chapter_title,
                        page=page_num + 1,
                        full_path=full_path
                    )
                    
                    # 更新当前章节
                    self._update_stack(chapter_info)
                    
                    return chapter_info
        
        return None
    
    def _clean_title(self, title: str) -> str:
        """清理章节标题"""
        # 移除多余空格
        title = re.sub(r'\s+', ' ', title)
        
        # 移除末尾标点
        title = re.sub(r'[：:;；。，,]$', '', title)
        
        return title.strip()
    
    def _build_full_path(self, level: int, number: str, title: str) -> str:
        """构建完整的章节路径"""
        # 更新栈
        while len(self.chapter_stack) >= level:
            self.chapter_stack.pop()
        
        # 创建当前级别
        current = f"{number} {title}"
        
        if len(self.chapter_stack) >= level:
            self.chapter_stack[level - 1] = current
        else:
            self.chapter_stack.append(current)
        
        # 构建完整路径
        return ' > '.join(self.chapter_stack)
    
    def _update_stack(self, chapter_info: ChapterInfo):
        """更新章节栈"""
        self.current_chapter = chapter_info
    
    def get_current_chapter(self) -> Optional[str]:
        """获取当前章节路径"""
        if self.current_chapter:
            return self.current_chapter.full_path
        return None
    
    def detect_all_chapters(self, pages_text: List[str]) -> List[ChapterInfo]:
        """检测所有页面中的章节"""
        chapters = []
        for i, text in enumerate(pages_text):
            chapter = self.detect_chapter(text, i)
            if chapter:
                chapters.append(chapter)
        return chapters
    
    def extract_toc(self, pages_text: List[str]) -> Dict[int, str]:
        """
        提取目录结构
        
        Returns:
            {页码: 章节路径}
        """
        toc = {}
        current_path = "前言"
        
        for i, text in enumerate(pages_text):
            chapter = self.detect_chapter(text, i)
            if chapter:
                current_path = chapter.full_path
            toc[i] = current_path
        
        return toc
    
    def add_pattern(self, pattern: str, pattern_type: str, level: int, confidence: float = 0.85):
        """添加自定义章节模式"""
        self.patterns.append((pattern, pattern_type, confidence, level))