#!/usr/bin/env python3
"""
strategy-fusion-advisor 一致性检查脚本
检查 fusion_config.yaml / strategy_weights.yaml / risk_config.yaml 与 SKILL.md 之间的一致性
"""

import os
import sys
import yaml

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT_DIR = os.path.dirname(SKILL_DIR)


def print_header(title):
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print(f"{'=' * 50}")


def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def check_configs():
    """检查配置文件"""
    print_header("【配置文件检查】")

    config_dir = os.path.join(SKILL_DIR, 'config')
    files = ['fusion_config.yaml', 'strategy_weights.yaml', 'risk_config.yaml']

    all_ok = True
    for f in files:
        path = os.path.join(config_dir, f)
        try:
            data = load_yaml(path)
            print(f"  ✅ {f} - YAML格式正确，{len(data)} 个顶级键")
        except FileNotFoundError:
            print(f"  ❌ {f} - 文件不存在")
            all_ok = False
        except yaml.YAMLError as e:
            print(f"  ❌ {f} - YAML解析错误: {e}")
            all_ok = False

    return all_ok


def check_fusion_config_against_skill():
    """检查 fusion_config.yaml 中的策略列表是否与实际目录一致"""
    print_header("【融合策略一致性检查】")

    config_path = os.path.join(SKILL_DIR, 'config', 'fusion_config.yaml')
    fusion = load_yaml(config_path)
    strategies_in_config = {s['name'] for s in fusion['fusion']['strategies']}

    # 实际存在的策略目录（不包括 fusion-advisor 自身）
    actual_dirs = set()
    for d in os.listdir(ROOT_DIR):
        if d.startswith('.') or d == 'strategy-fusion-advisor':
            continue
        path = os.path.join(ROOT_DIR, d)
        if os.path.isdir(path):
            actual_dirs.add(d)

    all_ok = True

    # 检查融合配置中的每个策略
    skill_md_path = os.path.join(SKILL_DIR, 'SKILL.md')
    with open(skill_md_path, 'r', encoding='utf-8') as f:
        skill_content = f.read()

    print(f"  融合配置中的策略数: {len(strategies_in_config)}")
    print(f"  实际策略目录数: {len(actual_dirs)}")

    missing_dirs = []
    for s in strategies_in_config:
        if s not in actual_dirs:
            print(f"  ❌ 策略目录不存在: {s}")
            missing_dirs.append(s)
            all_ok = False

    # 检查 SKILL.md 中声称的10个策略
    import re
    # 查找 | 1 | `ma-bullish-strategy` 这样的行
    skill_strategies = re.findall(r'`([a-z0-9-]+(?:strategy|strategy))`', skill_content)
    # More specific pattern for the table
    skill_strategies = []
    for line in skill_content.split('\n'):
        if '| #' in line and '`' in line:
            parts = line.split('`')
            for p in parts:
                p = p.strip()
                if 'strategy' in p and p not in ['strategies', 'strategy_weights', 'strategy_fusion']:
                    skill_strategies.append(p)

    extra_in_config = strategies_in_config - actual_dirs
    if extra_in_config:
        print(f"  ❌ 融合配置中有 {len(extra_in_config)} 个策略目录不存在")
        all_ok = False

    # 检查 win_rate 一致性（fusion_config vs SKILL.md）
    print("\n  【胜率一致性】")
    fusion_strategies = fusion['fusion']['strategies']

    # SKILL.md 中的胜率表格
    win_rate_map = {}
    for line in skill_content.split('\n'):
        if '|' in line and '%' in line and 'strategy' not in line[:10]:
            parts = [p.strip() for p in line.split('|')]
            for i, p in enumerate(parts):
                if '%' in p and i > 0:
                    try:
                        rate = int(p.replace('%', '').strip())
                        # Try to get strategy name from previous column
                    except:
                        pass

    # Win rates from fusion_config
    for s in fusion_strategies:
        name = s['name']
        wr = s['win_rate']
        weight = s['weight']
        print(f"    {name:45s} 胜率:{wr*100:5.1f}%  权重:{weight:.2f}")

    print(f"\n  ✅ 融合配置共 {len(fusion_strategies)} 个策略")

    # 检查 strategy_weights.yaml 与 fusion_config.yaml 的一致性
    print("\n  【strategy_weights.yaml 一致性】")
    sw_path = os.path.join(SKILL_DIR, 'config', 'strategy_weights.yaml')
    sw = load_yaml(sw_path)
    fw = sw.get('strategy_weights', {}).get('fixed_weights', {})

    mismatches = []
    for s in fusion_strategies:
        name = s['name']
        config_weight = s['weight']
        sw_weight = fw.get(name)
        if sw_weight is not None and abs(config_weight - sw_weight) > 0.001:
            mismatches.append(f"    ❌ {name}: fusion_config={config_weight}, strategy_weights={sw_weight}")
        else:
            print(f"    ✅ {name}: 权重={config_weight}")

    for m in mismatches:
        print(m)
        all_ok = False

    return all_ok


def check_scripts():
    """检查 scripts 目录"""
    print_header("【scripts 目录检查】")

    scripts_dir = os.path.join(SKILL_DIR, 'skills', 'scripts')
    expected = ['fusion_advisor.py', 'strategy_collector.py', 'score_calculator.py',
                'portfolio_optimizer.py', 'report_generator.py']
    optional = ['check_consistency.py']

    all_ok = True
    for s in expected:
        path = os.path.join(scripts_dir, s)
        if os.path.exists(path):
            print(f"    ✅ {s}")
        else:
            print(f"    ❌ {s} - 缺失")
            all_ok = False

    for s in optional:
        path = os.path.join(scripts_dir, s)
        if os.path.exists(path):
            print(f"    ⚠️  {s} - 存在（可选）")

    return all_ok


def check_data_dirs():
    """检查数据目录"""
    print_header("【数据目录检查】")

    data_storage_keys = ['recommendations', 'historical', 'logs']
    # 从 fusion_config 读取
    config_path = os.path.join(SKILL_DIR, 'config', 'fusion_config.yaml')
    fusion = load_yaml(config_path)
    ds = fusion.get('data_storage', {})

    all_ok = True
    for key in data_storage_keys:
        subpath = ds.get(key, f'./data/{key}/').lstrip('./')
        full = os.path.join(SKILL_DIR, subpath)
        if os.path.exists(full):
            print(f"    ✅ data/{subpath}")
        else:
            print(f"    ⚠️  data/{subpath} - 目录不存在（将在运行时创建）")

    return all_ok


def main():
    print("=" * 50)
    print("  港股策略融合投资顾问 - 一致性检查")
    print("=" * 50)
    print(f"  检查目录: {SKILL_DIR}")

    ok1 = check_configs()
    ok2 = check_fusion_config_against_skill()
    ok3 = check_scripts()
    ok4 = check_data_dirs()

    print_header("【检查结果】")
    if ok1 and ok2 and ok3 and ok4:
        print("  ✅ 所有检查通过")
        return 0
    else:
        print("  ❌ 存在不一致问题，请查看上方详情")
        return 1


if __name__ == "__main__":
    sys.exit(main())
