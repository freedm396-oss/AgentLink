#!/usr/bin/env python3
"""breakout-high-strategy 功能测试"""

import sys
sys.path.insert(0, '/home/qinliming/.npm-global/lib/node_modules/openclaw/skills/Stock/Chinese_Stock/breakout-high-strategy')

print('='*80)
print('突破前高策略 - 功能测试')
print('='*80)
print()

print('1. 测试模块导入...')
try:
    from skills.scripts.analyzer import BreakoutHighAnalyzer
    from skills.scripts.scanner import main as scanner_main
    from skills.scripts.data_source_adapter import DataSourceAdapter
    print('   ✅ 所有模块导入成功')
except Exception as e:
    print(f'   ❌ 导入失败: {e}')

print()
print('2. 测试数据源适配器...')
try:
    adapter = DataSourceAdapter('baostock')
    if adapter.data_source:
        print(f'   ✅ 数据源: {adapter.source}')
    else:
        print('   ❌ 无可用数据源')
except Exception as e:
    print(f'   ❌ 错误: {e}')

print()
print('3. 测试配置一致性...')
try:
    import yaml
    with open('/home/qinliming/.npm-global/lib/node_modules/openclaw/skills/Stock/Chinese_Stock/breakout-high-strategy/config/scoring_weights.yaml', 'r') as f:
        scoring = yaml.safe_load(f)
    weights = scoring.get('weights', {})
    total = sum(weights.values())
    print(f'   评分权重总和: {total} (应为1.0)')
    if abs(total - 1.0) < 0.01:
        print('   ✅ 权重配置正确')
    else:
        print('   ❌ 权重配置错误')
except Exception as e:
    print(f'   ❌ 错误: {e}')

print()
print('='*80)
print('测试完成')
print('='*80)
