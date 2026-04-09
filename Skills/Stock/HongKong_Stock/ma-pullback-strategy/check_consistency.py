# skills/scripts/check_consistency.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
港股缩量回踩均线策略一致性检查脚本
"""

import os
import sys
import yaml


def check_imports():
    """检查依赖导入"""
    print("\n【依赖检查】")
    
    packages = ['akshare', 'pandas', 'numpy']
    
    for pkg in packages:
        try:
            module = __import__(pkg)
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {pkg} - {version}")
        except ImportError:
            print(f"❌ {pkg} - 未安装")


def check_config():
    """检查配置文件"""
    print("\n【配置文件检查】")
    
    # check_consistency.py 位于 hk-ma-pullback-strategy/ 根目录，config/ 是其子目录
    config_dir = os.path.join(os.path.dirname(__file__), 'config')
    
    config_files = ['strategy_config.yaml', 'scoring_weights.yaml', 'risk_rules.yaml']
    
    for f in config_files:
        path = os.path.join(config_dir, f)
        if os.path.exists(path):
            print(f"✅ {f}")
            with open(path, 'r', encoding='utf-8') as file:
                try:
                    yaml.safe_load(file)
                    print(f"   └─ YAML格式正确")
                except Exception as e:
                    print(f"   └─ YAML格式错误: {e}")
        else:
            print(f"❌ {f} - 不存在")


def check_hk_parameters():
    """检查港股特化参数"""
    print("\n【港股特化参数检查】")
    
    config_path = os.path.join(
        os.path.dirname(__file__),
        'config', 'strategy_config.yaml'
    )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    liquidity = config.get('strategy', {}).get('liquidity_filters', {})
    
    print(f"最小股价: {liquidity.get('min_price', 'N/A')}港元")
    print(f"最小市值: {liquidity.get('min_market_cap', 'N/A')/1e8:.0f}亿港元")
    print(f"最小成交额: {liquidity.get('min_avg_turnover', 'N/A')/1e4:.0f}万港元")
    print(f"排除仙股: {liquidity.get('exclude_penny_stocks', 'N/A')}")


def check_data_dirs():
    """检查数据目录"""
    print("\n【数据目录检查】")
    
    # data 目录放在 hk-ma-pullback-strategy/data/
    base_dir = os.path.dirname(__file__)
    
    dirs = ['data/recommendations', 'data/backtest_results', 'data/logs']
    
    for d in dirs:
        full_path = os.path.join(base_dir, d)
        if os.path.exists(full_path):
            print(f"✅ {d}")
        else:
            print(f"⚠️ {d} - 目录不存在，将自动创建")
            os.makedirs(full_path, exist_ok=True)
            print(f"   └─ 已创建")


if __name__ == '__main__':
    print("=" * 50)
    print("港股缩量回踩均线策略一致性检查")
    print("=" * 50)
    
    check_imports()
    check_config()
    check_hk_parameters()
    check_data_dirs()
    
    print("\n✅ 检查完成")