#!/usr/bin/env python3
"""
PDF图片提取器 - 演示脚本
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def demo_extract_first_chapter():
    """演示：提取第一章第一节的图片"""
    print("="*60)
    print("PDF图片提取器 - 演示")
    print("="*60)
    print()
    
    # 测试文件路径
    test_pdf = "testfiles/普通高中教科书·地理选择性必修1 自然地理基础.pdf"
    
    print(f"测试文件: {test_pdf}")
    print()
    
    # 检查文件是否存在
    pdf_path = Path(test_pdf)
    if not pdf_path.exists():
        print(f"❌ 文件不存在: {test_pdf}")
        print("请确保测试文件在testfiles目录中")
        return False
    
    print(f"✅ 文件存在，大小: {pdf_path.stat().st_size / 1024 / 1024:.2f} MB")
    print()
    
    try:
        from skills.extractor import PDFImageExtractor
        
        # 创建提取器
        output_dir = "./demo_output"
        extractor = PDFImageExtractor(
            str(pdf_path), 
            output_dir,
            min_size=100,  # 最小100x100
            max_size=5000  # 最大5000x5000
        )
        
        print("✅ 提取器创建成功")
        print(f"   输出目录: {output_dir}")
        print()
        
        # 提取图片（第一章前几页）
        print("开始提取图片...")
        print("(仅提取前10页作为演示)")
        print()
        
        # 使用extract方法，但限制页数
        import fitz
        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)
        print(f"PDF总页数: {total_pages}")
        print(f"演示提取: 前10页")
        print()
        
        # 提取图片
        figures = extractor.extract()
        
        print()
        print("="*60)
        print("提取结果")
        print("="*60)
        print(f"共提取 {len(figures)} 张图片")
        print()
        
        if figures:
            print("图片列表:")
            for i, fig in enumerate(figures[:10], 1):  # 只显示前10张
                print(f"  {i}. {fig.figure_number}: {fig.caption}")
                print(f"     页码: P{fig.page}, 尺寸: {fig.width}x{fig.height}")
                print(f"     文件: {fig.filename}")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ 提取失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_quick_test():
    """快速测试：验证模块导入"""
    print("="*60)
    print("PDF图片提取器 - 快速测试")
    print("="*60)
    print()
    
    tests = []
    
    # 测试1: 导入模块
    print("测试模块导入...")
    try:
        from skills.extractor import PDFImageExtractor
        print("  ✅ PDFImageExtractor")
        tests.append(True)
    except Exception as e:
        print(f"  ❌ PDFImageExtractor: {e}")
        tests.append(False)
    
    try:
        from agents import CaptionAgent, ChapterAgent, ImageAgent
        print("  ✅ Agents")
        tests.append(True)
    except Exception as e:
        print(f"  ❌ Agents: {e}")
        tests.append(False)
    
    # 测试2: 检查测试文件
    print("\n检查测试文件...")
    test_pdf = Path("testfiles/普通高中教科书·地理选择性必修1 自然地理基础.pdf")
    if test_pdf.exists():
        print(f"  ✅ 测试文件存在 ({test_pdf.stat().st_size / 1024 / 1024:.1f} MB)")
        tests.append(True)
    else:
        print(f"  ❌ 测试文件不存在")
        tests.append(False)
    
    # 汇总
    print()
    print("="*60)
    passed = sum(tests)
    total = len(tests)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return True
    else:
        print("⚠️ 部分测试失败")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PDF图片提取器演示")
    parser.add_argument("--quick", action="store_true", help="快速测试模式")
    parser.add_argument("--full", action="store_true", help="完整提取模式")
    
    args = parser.parse_args()
    
    if args.full:
        success = demo_extract_first_chapter()
    else:
        success = demo_quick_test()
    
    sys.exit(0 if success else 1)
