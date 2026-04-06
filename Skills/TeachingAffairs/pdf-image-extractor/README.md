# PDF图片提取工具

从电子版教材PDF中智能提取所有图片，自动识别图片标题，按章节组织输出。

## 功能特性

- 🖼️ **智能提取**: 自动提取PDF中的所有图片（矢量图+位图）
- 📝 **标题识别**: 智能识别中英文图片标题/图注
- 📚 **章节追踪**: 自动识别章节结构，按章节组织输出
- 🗂️ **多格式输出**: JSON、Markdown、CSV、HTML、TXT
- 🔄 **去重处理**: 基于内容哈希自动去重
- ⚡ **高性能**: 支持并行处理，逐页提取

## 快速开始

### 安装

```bash
# 运行安装脚本
bash setup.sh

# 或手动安装
pip install PyMuPDF pillow pyyaml jinja2 tqdm
使用
bash
# 命令行使用
python -m skills.extractor 教材.pdf -o ./output

# Python代码使用
from skills.extractor import PDFImageExtractor

extractor = PDFImageExtractor("教材.pdf", "./output")
figures = extractor.extract()
输出结构
text
output/
├── images/          # 提取的图片文件
├── data/            # JSON、CSV、Markdown数据
├── reports/         # HTML报告
└── logs/            # 处理日志
配置
编辑 config/ 目录下的配置文件：

default.yaml: 主配置

patterns.yaml: 匹配模式

output.yaml: 输出格式

依赖
Python 3.8+

PyMuPDF

Pillow

PyYAML

Jinja2

许可证
MIT License