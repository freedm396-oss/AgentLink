#!/usr/bin/env python3
"""earnings-surprise-strategy 功能测试"""

import sys
sys.path.insert(0, '/home/qinliming/.npm-global/lib/node_modules/openclaw/skills/Stock/Chinese_Stock/earnings-surprise-strategy')

print('='*80)
print('财报超预期策略 - 功能测试')
print('='*80)
print()

# 测试1: 导入所有模块
print('1. 测试模块导入...')
try:
    from skills.scripts.earnings_scanner import EarningsSurpriseScanner
    from skills.scripts.surprise_analyzer import SurpriseAnalyzer
    from skills.scripts.quality_analyzer import QualityAnalyzer
    from skills.scripts.report_generator import EarningsReportGenerator
    from skills.scripts.risk_assessor import RiskAssessor
    print('   ✅ 所有模块导入成功')
except Exception as e:
    print(f'   ❌ 导入失败: {e}')

# 测试2: 扫描器创建
print()
print('2. 测试扫描器创建...')
try:
    scanner = EarningsSurpriseScanner()
    print(f'   ✅ 扫描器创建成功: {scanner.name}')
except Exception as e:
    print(f'   ❌ 错误: {e}')

# 测试3: 配置一致性
print()
print('3. 测试配置一致性...')
try:
    import yaml
    with open('/home/qinliming/.npm-global/lib/node_modules/openclaw/skills/Stock/Chinese_Stock/earnings-surprise-strategy/config/scoring_weights.yaml', 'r') as f:
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
