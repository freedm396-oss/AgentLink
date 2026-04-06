#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
策略融合投资顾问演示脚本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills', 'scripts'))

from datetime import datetime


def print_header():
    """打印标题"""
    print("="*80)
    print("策略融合投资顾问 - 演示")
    print("="*80)
    print()
    print(f"演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def print_strategy_list():
    """打印策略列表"""
    strategies = [
        ("ma-bullish-strategy", "均线多头排列", 0.65, 1.0),
        ("limit-up-analysis", "涨停板连板分析", 0.65, 1.0),
        ("earnings-surprise-strategy", "财报超预期", 0.70, 1.2),
        ("volume-retrace-ma-strategy", "缩量回踩均线", 0.62, 0.9),
        ("limit-up-retrace-strategy", "涨停首次回调", 0.60, 0.9),
        ("macd-divergence-strategy", "MACD底背离", 0.58, 0.8),
        ("morning-star-strategy", "早晨之星", 0.58, 0.8),
        ("breakout-high-strategy", "突破高点", 0.60, 0.9),
        ("rsi-oversold-strategy", "RSI超卖", 0.58, 0.8),
        ("volume-extreme-strategy", "地量见底", 0.62, 0.8),
        ("gap-fill-strategy", "缺口回补", 0.62, 0.8),
    ]
    
    print("="*80)
    print("融合的策略列表 (11个)")
    print("="*80)
    print()
    print(f"{'策略名称':<20} {'胜率':<10} {'权重系数':<10}")
    print("-"*80)
    
    for name, display, win_rate, weight in strategies:
        print(f"{display:<20} {win_rate*100:>6.0f}%    {weight}")
    
    print()
    print("="*80)
    print()


def print_fusion_process():
    """打印融合过程"""
    print("="*80)
    print("策略融合过程")
    print("="*80)
    print()
    
    print("步骤1: 收集所有策略推荐")
    print("  ✅ 均线多头排列: 5只")
    print("  ✅ 涨停板连板分析: 5只")
    print("  ✅ 财报超预期: 5只")
    print("  ✅ 缩量回踩均线: 5只")
    print("  ✅ 涨停首次回调: 5只")
    print("  ✅ MACD底背离: 5只")
    print("  ✅ 早晨之星: 5只")
    print("  ✅ 突破高点: 5只")
    print("  ✅ RSI超卖: 5只")
    print("  ✅ 地量见底: 5只")
    print("  ✅ 缺口回补: 5只")
    print("  📊 共收集到 55 条推荐记录")
    print()
    
    print("步骤2: 计算综合得分")
    print("  📊 去重后共 10 只股票")
    print("  📊 计算每只股票的综合得分:")
    print("     综合得分 = Σ(策略评分 × 策略权重 × 策略胜率)")
    print()
    
    print("步骤3: 优化投资组合")
    print("  📊 根据风险约束优化仓位分配")
    print("  📊 单只股票最大仓位: 30%")
    print("  📊 现金预留: 10%")
    print("  ✅ 选出 5 只股票")
    print()
    
    print("步骤4: 生成投资报告")
    print("  ✅ 保存JSON格式推荐")
    print("  ✅ 生成Markdown报告")
    print()
    
    print("="*80)
    print()


def print_recommendation_results():
    """打印推荐结果"""
    print("="*80)
    print("今日推荐投资组合 (Top 5)")
    print("="*80)
    print()
    
    recommendations = [
        ("海康威视", "002415", 576.8, 8, "21.3%", "强烈买入"),
        ("招商银行", "600036", 512.4, 7, "18.5%", "强烈买入"),
        ("中国平安", "601318", 506.8, 7, "18.3%", "强烈买入"),
        ("贵州茅台", "600519", 448.8, 7, "16.2%", "强烈买入"),
        ("宁德时代", "300750", 443.2, 6, "15.7%", "强烈买入"),
    ]
    
    print(f"{'排名':<6} {'股票':<10} {'代码':<10} {'综合得分':<12} {'策略数':<8} {'仓位':<10} {'建议':<10}")
    print("-"*80)
    
    for i, (name, code, score, count, position, advice) in enumerate(recommendations, 1):
        print(f"{i:<6} {name:<10} {code:<10} {score:<12.1f} {count:<8} {position:<10} {advice:<10}")
    
    print()
    print("组合汇总:")
    print("  股票数量: 5只")
    print("  总仓位: 90.0%")
    print("  现金预留: 10.0%")
    print()
    print("="*80)
    print()


def print_top_stock_detail():
    """打印Top股票详情"""
    print("="*80)
    print("Top 1 股票详情 - 海康威视 (002415)")
    print("="*80)
    print()
    
    print("📊 综合得分: 576.8分")
    print("📊 策略内平均分: 78.75分")
    print("📊 策略平均胜率: 62.1%")
    print("📊 推荐策略数: 8个")
    print()
    
    print("推荐策略列表:")
    strategies = [
        ("均线多头排列", 100, 0.65),
        ("财报超预期", 100, 0.70),
        ("缩量回踩均线", 60, 0.62),
        ("MACD底背离", 80, 0.58),
        ("早晨之星", 70, 0.58),
        ("突破高点", 60, 0.60),
        ("地量见底", 90, 0.62),
        ("缺口回补", 70, 0.62),
    ]
    
    print(f"  {'策略名称':<15} {'策略评分':<10} {'策略胜率':<10}")
    print("  " + "-"*50)
    for name, score, win_rate in strategies:
        print(f"  {name:<15} {score:<10} {win_rate*100:>6.0f}%")
    
    print()
    print("💰 投资建议:")
    print("  当前价格: 35.6元")
    print("  建议仓位: 21.3%")
    print("  预期收益: 9.6%")
    print("  止损价位: 33.82元")
    print("  目标价位: 39.16元")
    print("  操作建议: 强烈买入")
    print()
    
    print("="*80)
    print()


def print_usage():
    """打印使用方法"""
    print("="*80)
    print("使用方法")
    print("="*80)
    print()
    print("1. 生成每日推荐:")
    print("   python3 skills/scripts/fusion_advisor.py --daily")
    print()
    print("2. 保存推荐结果:")
    print("   python3 skills/scripts/fusion_advisor.py --daily --save")
    print()
    print("3. 查看推荐报告:")
    print("   cat data/recommendations/20260406_report.md")
    print()
    print("4. 查看JSON数据:")
    print("   cat data/recommendations/20260406_recommendation.json")
    print()
    print("="*80)
    print()


def print_features():
    """打印功能特性"""
    print("="*80)
    print("功能特性")
    print("="*80)
    print()
    print("🔄 策略融合:")
    print("  • 融合11个交易策略的推荐")
    print("  • 智能去重和汇总")
    print("  • 多维度综合评分")
    print()
    print("📊 评分算法:")
    print("  • 综合得分 = Σ(策略评分 × 策略权重 × 策略胜率)")
    print("  • 考虑策略历史表现")
    print("  • 动态权重调整")
    print()
    print("💼 投资组合优化:")
    print("  • 风险约束下的仓位分配")
    print("  • 单只股票仓位限制")
    print("  • 现金预留管理")
    print()
    print("📈 投资报告:")
    print("  • 详细的股票分析")
    print("  • 买入卖出建议")
    print("  • 风险提示")
    print()
    print("="*80)
    print()


def main():
    print_header()
    print_strategy_list()
    print_fusion_process()
    print_recommendation_results()
    print_top_stock_detail()
    print_features()
    print_usage()
    
    print("演示完成!")
    print()
    print("注意: 以上数据基于模拟策略推荐数据")
    print("实际使用请确保各策略有真实的推荐输出")


if __name__ == '__main__':
    main()
