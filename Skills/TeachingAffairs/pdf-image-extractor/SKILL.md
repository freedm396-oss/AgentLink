# PDF图片提取技能 (pdf-image-extractor)

## 技能ID
`pdf-image-extractor`

## 技能描述
从电子版教材PDF中智能提取所有图片（包括图表、插图等），自动识别图片标题/图注，按照原始章节结构组织输出。

## 触发条件
当用户需要从PDF教材中提取图片、整理教学素材、制作PPT时触发。

## 输入参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| pdf_path | string | 是 | PDF文件路径 |
| output_dir | string | 否 | 输出目录（默认./output） |
| min_size | int | 否 | 最小图片尺寸（默认50） |
| max_size | int | 否 | 最大图片尺寸（默认5000） |
| deduplicate | bool | 否 | 是否去重（默认true） |

## 输出格式

### 文件输出
- `images/` - 提取的图片文件
- `data/figures.json` - 完整JSON数据
- `data/图片索引.md` - Markdown索引
- `data/figures.csv` - CSV表格
- `reports/extraction_report.html` - HTML报告

### 数据结构
```json
{
  "figure_number": "图1-1",
  "caption": "函数关系示意图",
  "page": 3,
  "chapter": "第1章 函数与极限",
  "file_path": "images/p003_xxx.png"
}

使用示例
基础使用
text
用户: 帮我从高等数学.pdf中提取所有图片
助手: [执行提取命令]
指定输出目录
text
用户: 提取数据结构.pdf的图片，保存到./ds_images
助手: [执行提取命令]
自定义尺寸
text
用户: 提取大尺寸的图片（最小200x200）
助手: [执行提取命令]
错误处理
错误	处理方式
文件不存在	提示用户检查路径
无图片	提示PDF可能没有图片
内存不足	建议分批处理
编码错误	自动尝试其他编码
性能说明
处理速度: ~20页/秒

内存占用: ~200MB/1000页

支持文件: 最大2GB

注意事项
提取的图片仅限个人学习使用

扫描版PDF需要OCR预处理

大文件处理需要足够内存