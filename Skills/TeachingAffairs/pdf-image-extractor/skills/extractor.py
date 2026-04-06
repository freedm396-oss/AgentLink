#!/usr/bin/env python3
"""
PDF图片提取器（主模块）
整合各个代理和处理器，完成图片提取工作
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import logging

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import fitz  # PyMuPDF
from agents import CaptionAgent, ChapterAgent, ImageAgent
from skills.processor import ImageProcessor
from skills.organizer import OutputOrganizer
from skills.validator import ResultValidator
from config import config


@dataclass
class ExtractedFigure:
    """提取的图片信息"""
    page: int
    index: int
    file_path: str
    filename: str
    caption: str
    figure_number: str
    chapter: str
    section: str
    image_type: str
    width: int
    height: int
    file_size_kb: float
    hash: str


class PDFImageExtractor:
    """PDF图片提取器"""
    
    def __init__(self, pdf_path: str, output_dir: str = "./output", **kwargs):
        """
        初始化提取器
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录
            **kwargs: 覆盖默认配置的参数
        """
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        
        # 验证PDF文件
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        # 更新配置
        for key, value in kwargs.items():
            if hasattr(config, 'update'):
                config.update('default', {key: value})
        
        # 初始化代理
        self.caption_agent = CaptionAgent(config.get('caption', {}))
        self.chapter_agent = ChapterAgent(config.get('chapter', {}))
        self.image_agent = ImageAgent(config.get('extraction', {}))
        
        # 初始化处理器
        self.processor = ImageProcessor()
        self.organizer = OutputOrganizer(self.output_dir)
        self.validator = ResultValidator()
        
        # 设置日志
        self._setup_logging()
        
        self.logger = logging.getLogger(__name__)
        
        # 存储结果
        self.figures = []
        self.stats = {}
    
    def _setup_logging(self):
        """设置日志"""
        log_config = config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        
        logging.basicConfig(
            level=log_level,
            format=log_config.get('format', '%(asctime)s - %(levelname)s - %(message)s'),
            handlers=[
                logging.StreamHandler() if log_config.get('console', True) else None,
                logging.FileHandler(self.output_dir / log_config.get('file', 'extraction.log')) if log_config.get('file') else None
            ]
        )
    
    def extract(self) -> List[ExtractedFigure]:
        """
        执行提取流程
        
        Returns:
            提取的图片列表
        """
        self.logger.info(f"开始处理: {self.pdf_path.name}")
        start_time = datetime.now()
        
        try:
            # 打开PDF
            doc = fitz.open(self.pdf_path)
            total_pages = len(doc)
            self.logger.info(f"总页数: {total_pages}")
            
            # 限制处理页数
            max_pages = config.get('extraction.max_pages')
            if max_pages:
                total_pages = min(total_pages, max_pages)
                self.logger.info(f"限制处理页数: {total_pages}")
            
            # 逐页处理
            for page_num in range(total_pages):
                self.logger.info(f"处理第 {page_num + 1}/{total_pages} 页")
                page = doc[page_num]
                
                # 获取页面文本
                page_text = page.get_text()
                
                # 检测章节
                if config.get('chapter.detect', True):
                    chapter = self.chapter_agent.detect_chapter(page_text, page_num)
                    if chapter:
                        self.logger.info(f"  检测到章节: {chapter.full_path}")
                
                # 提取图片
                images = self.image_agent.extract_from_page(page, page_num, doc)
                
                if not images:
                    continue
                
                # 获取文本块用于位置分析
                text_dict = page.get_text("dict")
                text_blocks = text_dict.get("blocks", [])
                
                # 处理每张图片
                for img_info in images:
                    # 查找标题
                    caption_match = None
                    if config.get('caption.enable', True):
                        caption_match = self.caption_agent.find_caption(
                            page_text, img_info.bbox, text_blocks
                        )
                    
                    # 生成文件名
                    filename = self._generate_filename(img_info, caption_match)
                    file_path = self.output_dir / "images" / filename
                    
                    # 保存图片
                    if self.image_agent.save_image(img_info, file_path):
                        # 创建提取结果
                        figure = ExtractedFigure(
                            page=img_info.page,
                            index=img_info.index,
                            file_path=str(file_path),
                            filename=filename,
                            caption=caption_match.text if caption_match else "",
                            figure_number=caption_match.figure_number if caption_match else f"图{img_info.index}",
                            chapter=self.chapter_agent.get_current_chapter() or "未分类",
                            section="",
                            image_type=img_info.image_type,
                            width=img_info.width,
                            height=img_info.height,
                            file_size_kb=len(img_info.data) / 1024,
                            hash=img_info.hash
                        )
                        
                        self.figures.append(figure)
                        self.logger.info(f"  ✅ 提取: {filename}")
                        if figure.caption:
                            self.logger.info(f"     📋 {figure.figure_number}: {figure.caption[:50]}")
                    else:
                        self.logger.warning(f"  ❌ 保存失败: {img_info.xref}")
            
            doc.close()
            
            # 计算统计信息
            self._calculate_stats()
            
            # 后处理
            self.figures = self.processor.post_process(self.figures)
            
            # 验证结果
            self.validator.validate(self.figures)
            
            # 保存输出
            self.organizer.save_all(self.figures, self.stats, self.pdf_path.name)
            
            # 打印完成信息
            elapsed = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"\n✨ 完成！共提取 {len(self.figures)} 张图片")
            self.logger.info(f"⏱️  耗时: {elapsed:.2f} 秒")
            self.logger.info(f"📁 输出目录: {self.output_dir}")
            
            return self.figures
            
        except Exception as e:
            self.logger.error(f"提取失败: {e}")
            raise
    
    def _generate_filename(self, img_info, caption_match) -> str:
        """生成文件名"""
        # 获取模板，确保是字符串
        template = config.get('output.filename_template')
        if not template or not isinstance(template, str):
            # 使用默认格式
            template = "p{page:03d}_{chapter_slug}_{hash:.8}.{ext}"
        
        # 准备变量
        page = img_info.page
        hash_val = img_info.hash
        ext = img_info.format
        
        # 章节slug
        chapter = self.chapter_agent.get_current_chapter() or "unknown"
        chapter_slug = self._slugify(chapter)
        
        # 格式化 - 使用f-string更安全
        filename = f"p{page:03d}_{chapter_slug[:30]}_{hash_val[:8]}.{ext}"
        
        return filename
    
    def _slugify(self, text: str) -> str:
        """转换为slug"""
        import re
        # 移除特殊字符
        text = re.sub(r'[\\/:*?"<>|]', '_', text)
        text = re.sub(r'\s+', '_', text)
        text = text.strip('_')
        return text
    
    def _calculate_stats(self):
        """计算统计信息"""
        self.stats = {
            'total_images': len(self.figures),
            'total_pages': 0,
            'by_chapter': {},
            'by_type': {'vector': 0, 'raster': 0},
            'total_size_mb': sum(f.file_size_kb for f in self.figures) / 1024,
            'avg_width': 0,
            'avg_height': 0
        }
        
        if self.figures:
            pages = set(f.page for f in self.figures)
            self.stats['total_pages'] = max(pages) if pages else 0
            self.stats['avg_width'] = sum(f.width for f in self.figures) / len(self.figures)
            self.stats['avg_height'] = sum(f.height for f in self.figures) / len(self.figures)
            
            for fig in self.figures:
                self.stats['by_type'][fig.image_type] += 1
                
                chapter = fig.chapter
                if chapter not in self.stats['by_chapter']:
                    self.stats['by_chapter'][chapter] = 0
                self.stats['by_chapter'][chapter] += 1


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='提取PDF中的图片和标题')
    parser.add_argument('pdf', help='PDF文件路径')
    parser.add_argument('-o', '--output', default='./output', help='输出目录')
    parser.add_argument('--min-size', type=int, help='最小图片尺寸')
    parser.add_argument('--max-size', type=int, help='最大图片尺寸')
    parser.add_argument('--no-deduplicate', action='store_true', help='禁用去重')
    parser.add_argument('--format', help='输出格式（逗号分隔）')
    
    args = parser.parse_args()
    
    # 构建配置
    kwargs = {}
    if args.min_size:
        kwargs['min_image_size'] = args.min_size
    if args.max_size:
        kwargs['max_image_size'] = args.max_size
    if args.no_deduplicate:
        kwargs['deduplicate'] = False
    
    # 执行提取
    extractor = PDFImageExtractor(args.pdf, args.output, **kwargs)
    figures = extractor.extract()
    
    print(f"\n✅ 提取完成！共 {len(figures)} 张图片")
    print(f"📁 输出目录: {args.output}")


if __name__ == "__main__":
    main()