#!/usr/bin/env python3
"""
输出组织器
负责保存各种格式的输出文件
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict


class OutputOrganizer:
    """输出组织器"""
    
    def __init__(self, output_dir: Path):
        """
        初始化组织器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self._create_directories()
    
    def _create_directories(self):
        """创建目录结构"""
        directories = ['images', 'data', 'reports', 'logs']
        for dir_name in directories:
            (self.output_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    def save_all(self, figures: List, stats: Dict, title: str):
        """
        保存所有输出格式
        
        Args:
            figures: 图片列表
            stats: 统计信息
            title: 标题
        """
        # 准备数据
        data = self._prepare_data(figures, stats, title)
        
        # 保存JSON
        self._save_json(data)
        
        # 保存Markdown
        self._save_markdown(data)
        
        # 保存CSV
        self._save_csv(figures)
        
        # 保存HTML
        self._save_html(data)
        
        # 保存TXT
        self._save_txt(data)
    
    def _prepare_data(self, figures: List, stats: Dict, title: str) -> Dict:
        """准备输出数据"""
        return {
            'title': title,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'stats': stats,
            'figures': [self._figure_to_dict(f) for f in figures],
            'by_chapter': self._group_by_chapter(figures)
        }
    
    def _figure_to_dict(self, fig) -> Dict:
        """转换图片对象为字典"""
        return {
            'index': fig.index,
            'page': fig.page,
            'figure_number': fig.figure_number,
            'caption': fig.caption,
            'chapter': fig.chapter,
            'section': fig.section,
            'filename': fig.filename,
            'file_path': fig.file_path,
            'relative_path': f"images/{fig.filename}",
            'image_type': fig.image_type,
            'width': fig.width,
            'height': fig.height,
            'file_size_kb': round(fig.file_size_kb, 2),
            'hash': fig.hash
        }
    
    def _group_by_chapter(self, figures: List) -> Dict:
        """按章节分组"""
        by_chapter = defaultdict(list)
        for fig in figures:
            by_chapter[fig.chapter].append(self._figure_to_dict(fig))
        return dict(by_chapter)
    
    def _save_json(self, data: Dict):
        """保存JSON文件"""
        filepath = self.output_dir / 'data' / 'figures.json'
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  📄 JSON: {filepath}")
    
    def _save_markdown(self, data: Dict):
        """保存Markdown文件"""
        filepath = self.output_dir / 'data' / '图片索引.md'
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # 标题
            f.write(f"# {data['title']} - 图片索引\n\n")
            
            # 统计信息
            f.write(f"**提取时间**: {data['timestamp']}  \n")
            f.write(f"**总图片数**: {data['stats']['total_images']}  \n")
            f.write(f"**总页数**: {data['stats']['total_pages']}  \n\n")
            
            f.write("---\n\n")
            
            # 按章节浏览
            for chapter, figures in data['by_chapter'].items():
                f.write(f"## {chapter}\n\n")
                
                for fig in figures:
                    f.write(f"**{fig['figure_number']}** (第{fig['page']}页)\n\n")
                    f.write(f"{fig['caption']}\n\n")
                    f.write(f"![{fig['caption'][:50]}]({fig['relative_path']})\n\n")
                    f.write(f"<!-- 尺寸: {fig['width']}x{fig['height']}, 类型: {fig['image_type']} -->\n\n")
                    f.write("---\n\n")
        
        print(f"  📄 Markdown: {filepath}")
    
    def _save_csv(self, figures: List):
        """保存CSV文件"""
        filepath = self.output_dir / 'data' / 'figures.csv'
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = ['序号', '页码', '章节', '小节', '图号', '标题', '文件名', '类型', '宽度', '高度', '大小(KB)']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for i, fig in enumerate(figures, 1):
                writer.writerow({
                    '序号': i,
                    '页码': fig.page,
                    '章节': fig.chapter,
                    '小节': fig.section,
                    '图号': fig.figure_number,
                    '标题': fig.caption,
                    '文件名': fig.filename,
                    '类型': fig.image_type,
                    '宽度': fig.width,
                    '高度': fig.height,
                    '大小(KB)': round(fig.file_size_kb, 2)
                })
        
        print(f"  📄 CSV: {filepath}")
    
    def _save_html(self, data: Dict):
        """保存HTML报告"""
        filepath = self.output_dir / 'reports' / 'extraction_report.html'
        
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data['title']} - 图片提取报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: #f9f9f9; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #4CAF50; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .chapter {{ margin: 30px 0; }}
        .chapter h2 {{ background: #e8f5e9; padding: 10px; border-radius: 5px; }}
        .figure {{ border: 1px solid #ddd; margin: 15px 0; padding: 15px; border-radius: 5px; }}
        .figure img {{ max-width: 300px; max-height: 200px; margin: 10px 0; }}
        .figure-info {{ color: #666; font-size: 0.9em; }}
        .footer {{ margin-top: 30px; text-align: center; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{data['title']} - 图片提取报告</h1>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{data['stats']['total_images']}</div>
                <div class="stat-label">总图片数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{data['stats']['total_pages']}</div>
                <div class="stat-label">总页数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{data['stats']['total_size_mb']:.1f}</div>
                <div class="stat-label">总大小(MB)</div>
            </div>
        </div>
        
        <p><strong>提取时间:</strong> {data['timestamp']}</p>
        
        <hr>
        
        {self._generate_html_chapters(data['by_chapter'])}
        
        <div class="footer">
            <p>生成时间: {data['timestamp']}</p>
        </div>
    </div>
</body>
</html>"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        print(f"  📄 HTML: {filepath}")
    
    def _generate_html_chapters(self, by_chapter: Dict) -> str:
        """生成HTML章节内容"""
        html = ""
        for chapter, figures in by_chapter.items():
            html += f'<div class="chapter">\n'
            html += f'<h2>{chapter}</h2>\n'
            
            for fig in figures:
                html += f'''
                <div class="figure">
                    <strong>{fig['figure_number']}</strong> (第{fig['page']}页)<br>
                    <em>{fig['caption']}</em><br>
                    <img src="../{fig['relative_path']}" alt="{fig['caption'][:50]}"><br>
                    <div class="figure-info">
                        尺寸: {fig['width']}x{fig['height']} | 
                        类型: {fig['image_type']} | 
                        大小: {fig['file_size_kb']}KB
                    </div>
                </div>
                '''
            
            html += '</div>\n'
        
        return html
    
    def _save_txt(self, data: Dict):
        """保存文本文件"""
        filepath = self.output_dir / 'data' / '图片列表.txt'
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"{data['title']} - 图片列表\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"提取时间: {data['timestamp']}\n")
            f.write(f"总图片数: {data['stats']['total_images']}\n\n")
            f.write("=" * 60 + "\n\n")
            
            for fig in data['figures']:
                f.write(f"【{fig['figure_number']}】第{fig['page']}页\n")
                f.write(f"  章节: {fig['chapter']}\n")
                if fig['section']:
                    f.write(f"  小节: {fig['section']}\n")
                f.write(f"  标题: {fig['caption']}\n")
                f.write(f"  文件: {fig['filename']}\n")
                f.write(f"  尺寸: {fig['width']}x{fig['height']}\n")
                f.write("-" * 40 + "\n")
        
        print(f"  📄 TXT: {filepath}")