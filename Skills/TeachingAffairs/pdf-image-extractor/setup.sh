#!/bin/bash

# PDF图片提取工具安装脚本

echo "=========================================="
echo "PDF图片提取工具 - 安装脚本"
echo "=========================================="

# 检查Python版本
echo "检查Python版本..."
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
if [ -z "$python_version" ]; then
    echo "❌ 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

echo "✅ Python版本: $python_version"

# 创建虚拟环境（可选）
read -p "是否创建虚拟环境？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
fi

# 安装依赖
echo "安装依赖包..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ 依赖安装成功"
else
    echo "❌ 依赖安装失败"
    exit 1
fi

# 创建输出目录
mkdir -p output/images output/data output/reports output/logs

# 测试运行
echo ""
read -p "是否运行测试？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python test_skill.py
fi

echo ""
echo "=========================================="
echo "安装完成！"
echo "使用示例:"
echo "  python -m skills.extractor 教材.pdf -o ./output"
echo "=========================================="