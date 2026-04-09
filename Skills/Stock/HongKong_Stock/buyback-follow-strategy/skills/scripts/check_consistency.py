#!/usr/bin/env python3
"""
一致性检查脚本
"""

import os

skill_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_consistency():
    errors = []
    warnings = []

    skill_md = os.path.join(skill_root, 'SKILL.md')
    if not os.path.exists(skill_md):
        errors.append("SKILL.md 不存在")

    config_dir = os.path.join(skill_root, 'config')
    for cfg in ['strategy_config.yaml', 'scoring_weights.yaml', 'risk_rules.yaml']:
        if not os.path.exists(os.path.join(config_dir, cfg)):
            errors.append(f"配置文件缺失: {cfg}")

    scripts_dir = os.path.join(skill_root, 'skills', 'scripts')
    for script in ['hk_buyback_analyzer.py', 'hk_buyback_scanner.py']:
        if not os.path.exists(os.path.join(scripts_dir, script)):
            errors.append(f"脚本缺失: {script}")

    return errors, warnings


if __name__ == "__main__":
    print("=" * 50)
    print("一致性检查")
    print("=" * 50)

    errors, warnings = check_consistency()

    if errors:
        print("\n❌ 错误:")
        for e in errors:
            print(f"  - {e}")

    if warnings:
        print("\n⚠️ 警告:")
        for w in warnings:
            print(f"  - {w}")

    if not errors and not warnings:
        print("\n✅ 所有检查通过")
