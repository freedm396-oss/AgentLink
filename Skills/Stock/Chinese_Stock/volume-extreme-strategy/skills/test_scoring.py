#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成交量地量见底策略 - 评分系统测试
验证五维评分体系和市场环境评分
"""

import sys
import os

# 路径设置
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = _SCRIPT_DIR
sys.path.insert(0, _SCRIPT_DIR)
sys.path.insert(0, os.path.join(_SCRIPT_DIR, 'scripts'))

try:
    from skills.scripts.analyzer import VolumeExtremeAnalyzer
except ImportError:
    from analyzer import VolumeExtremeAnalyzer
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_test_data(volume_extreme_ratio=0.25, price_position=0.2, has_recovery=True):
    """创建测试数据 - 模拟地量见底形态"""
    np.random.seed(42)  # 固定随机种子以便复现
    dates = pd.date_range(end=datetime.now(), periods=80, freq='D')
    
    # 基础价格（模拟下跌趋势后的低位）
    base_price = 10.0
    prices = []
    volumes = []
    
    for i in range(80):
        if i < 40:
            # 前40天：下跌趋势
            price = base_price * (1 - 0.30 * (i / 40)) + np.random.normal(0, 0.03)
        elif i < 70:
            # 中间30天：低位震荡，波动收窄
            price = base_price * 0.70 + np.random.normal(0, 0.015)
        else:
            # 最后10天：企稳回升
            if has_recovery:
                price = base_price * 0.70 * (1 + 0.015 * (i - 69)) + np.random.normal(0, 0.01)
            else:
                price = base_price * 0.70 + np.random.normal(0, 0.01)
        prices.append(max(price, 5.0))
    
    # 成交量：前60天正常，中间10天地量，最后10天恢复
    avg_volume = 1000000
    for i in range(80):
        if i < 60:
            # 正常成交量
            vol = avg_volume * (0.9 + np.random.random() * 0.3)
        elif i < 70:
            # 地量（极度缩量）
            vol = avg_volume * volume_extreme_ratio * (0.95 + np.random.random() * 0.1)
        else:
            # 恢复放量
            if has_recovery:
                vol = avg_volume * (0.5 + (i - 69) * 0.08)
            else:
                vol = avg_volume * 0.4
        volumes.append(int(vol))
    
    df = pd.DataFrame({
        'date': dates,
        'open': [p * (1 + np.random.normal(0, 0.003)) for p in prices],
        'high': [p * (1 + abs(np.random.normal(0, 0.008))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.008))) for p in prices],
        'close': prices,
        'volume': volumes
    })
    df.set_index('date', inplace=True)
    return df

def test_market_environment():
    """测试市场环境评分"""
    print("="*80)
    print("测试市场环境评分")
    print("="*80)
    
    try:
        analyzer = VolumeExtremeAnalyzer(data_source="baostock")
        market_env = analyzer._calc_market_environment()
        print(f"✅ 市场环境评分: {market_env:.1f}/100")
        
        # 获取详细数据
        market_data = analyzer._get_market_index_data()
        print(f"\n大盘指数数据:")
        print(f"  上证涨跌: {market_data['sh_change']:+.2f}%")
        print(f"  深证涨跌: {market_data['sz_change']:+.2f}%")
        print(f"  创业板涨跌: {market_data['cy_change']:+.2f}%")
        print(f"  科创板涨跌: {market_data['kc_change']:+.2f}%")
        print(f"  上证量比: {market_data['sh_volume_ratio']:.2f}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_scoring_system():
    """测试五维评分系统"""
    print("\n" + "="*80)
    print("测试五维评分系统")
    print("="*80)
    
    try:
        analyzer = VolumeExtremeAnalyzer(data_source="baostock")
        
        # 创建理想地量见底数据
        df = create_test_data(volume_extreme_ratio=0.2, price_position=0.2, has_recovery=True)
        
        # 查找地量
        extremes = analyzer.find_volume_extreme(df)
        print(f"找到 {len(extremes)} 个地量点")
        
        if extremes:
            extreme = extremes[-1]
            print(f"最近地量点索引: {extreme['index']}, 地量比例: {extreme['volume_ratio']*100:.1f}%")
            
            recovery = analyzer.analyze_volume_recovery(df, extreme['index'])
            print(f"恢复信号: {recovery}")
            
            scores = analyzer._calc_detailed_scores(df, extreme, recovery)
            
            print(f"\n测试股票: 模拟地量见底股票")
            print(f"地量比例: {extreme['volume_ratio']*100:.1f}%")
            print(f"\n五维评分:")
            print(f"  地量程度: {scores['volume_extreme']:.0f}/100 (权重30%)")
            print(f"  价格位置: {scores['price_position']:.0f}/100 (权重25%)")
            print(f"  企稳信号: {scores['stability_signal']:.0f}/100 (权重20%)")
            print(f"  后续确认: {scores['follow_up']:.0f}/100 (权重15%)")
            print(f"  市场环境: {scores['market_environment']:.0f}/100 (权重10%)")
            print(f"\n综合得分: {scores['total']:.1f}/100")
            
            rating = analyzer.get_rating(scores['total'])
            print(f"评级: {rating['label']} - {rating['description']}")
            
            recommendation = analyzer.get_recommendation(scores['total'])
            print(f"建议: {recommendation}")
        else:
            print("⚠️ 未找到地量信号，尝试手动计算...")
            # 手动测试评分计算
            extreme = {
                'index': 65,
                'volume_ratio': 0.20,
                'volume_ma': 1000000,
                'price': 7.0
            }
            recovery = {
                'has_recovery': True,
                'volume_increase_ratio': 1.8,
                'price_change': 0.04,
                'recovery_days': 3
            }
            scores = analyzer._calc_detailed_scores(df, extreme, recovery)
            
            print(f"\n手动测试评分:")
            print(f"  地量程度: {scores['volume_extreme']:.0f}/100 (假设地量20%)")
            print(f"  价格位置: {scores['price_position']:.0f}/100")
            print(f"  企稳信号: {scores['stability_signal']:.0f}/100")
            print(f"  后续确认: {scores['follow_up']:.0f}/100 (假设已恢复)")
            print(f"  市场环境: {scores['market_environment']:.0f}/100")
            print(f"\n综合得分: {scores['total']:.1f}/100")
            
            rating = analyzer.get_rating(scores['total'])
            print(f"评级: {rating['label']} - {rating['description']}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_rating_thresholds():
    """测试评分阈值"""
    print("\n" + "="*80)
    print("测试评分阈值")
    print("="*80)
    
    try:
        analyzer = VolumeExtremeAnalyzer(data_source="baostock")
        
        test_scores = [95, 82, 72, 62, 52, 45]
        print("\n评分等级测试:")
        for score in test_scores:
            rating = analyzer.get_rating(score)
            recommendation = analyzer.get_recommendation(score)
            print(f"  {score}分 -> {rating['label']}: {rating['description']}")
            print(f"           {recommendation}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def main():
    print("\n" + "="*80)
    print("成交量地量见底策略 - 评分系统测试")
    print("="*80 + "\n")
    
    # 测试市场环境评分
    test_market_environment()
    
    # 测试五维评分系统
    test_scoring_system()
    
    # 测试评分阈值
    test_rating_thresholds()
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)

if __name__ == '__main__':
    main()
