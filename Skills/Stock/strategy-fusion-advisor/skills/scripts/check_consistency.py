# skills/scripts/check_consistency.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
策略融合投资顾问一致性检查脚本
"""

import os
import sys
import yaml


def check_imports():
    """检查依赖导入"""
    print("\n【依赖检查】")
    
    packages = ['pandas', 'numpy', 'yaml']
    
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
    
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config')
    
    config_files = ['fusion_config.yaml', 'strategy_weights.yaml', 'risk_config.yaml']
    
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


def check_strategies():
    """检查策略配置"""
    print("\n【策略配置检查】")
    
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'config', 'fusion_config.yaml'
    )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    strategies = config.get('fusion', {}).get('strategies', [])
    
    print(f"共配置 {len(strategies)} 个策略:")
    
    for strategy in strategies:
        name = strategy.get('name')
        display = strategy.get('display_name')
        win_rate = strategy.get('win_rate')
        enabled = strategy.get('enabled')
        
        status = "✅" if enabled else "❌"
        print(f"  {status} {display}({name}) - 胜率: {win_rate*100:.0f}%")
    
    return strategies


def check_data_dirs():
    """检查数据目录"""
    print("\n【数据目录检查】")
    
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'config', 'fusion_config.yaml'
    )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    data_dirs = config.get('data_storage', {})
    
    for name, path in data_dirs.items():
        full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), path)
        if os.path.exists(full_path):
            print(f"✅ {name}: {path}")
        else:
            print(f"⚠️ {name}: {path} - 目录不存在，将自动创建")
            os.makedirs(full_path, exist_ok=True)
            print(f"   └─ 已创建")


if __name__ == '__main__':
    print("=" * 50)
    print("策略融合投资顾问一致性检查")
    print("=" * 50)
    
    check_imports()
    check_config()
    strategies = check_strategies()
    check_data_dirs()
    
    print("\n✅ 检查完成")
    print(f"\n📊 策略融合投资顾问已就绪，共融合 {len(strategies)} 个策略")