#!/usr/bin/env python3
"""
港股AH溢价套利策略 - 一致性检查
"""

import os

skill_root = os.path.dirname(os.path.abspath(__file__))


def check_consistency():
    errors = []
    warnings = []

    # 1. SKILL.md
    skill_md = os.path.join(skill_root, 'SKILL.md')
    if not os.path.exists(skill_md):
        errors.append("SKILL.md 不存在")
    else:
        with open(skill_md, 'r', encoding='utf-8') as f:
            content = f.read()
        checks = [
            ("40%", "AH溢价买入阈值"),
            ("20%", "AH溢价止盈阈值"),
            ("30", "持仓最大天数"),
            ("8%", "止损阈值"),
            ("1000万", "H股量能阈值"),
            ("5000万", "A股量能阈值"),
        ]
        for check, name in checks:
            if check not in content:
                warnings.append(f"SKILL.md 中未找到 {name}")

    # 2. 配置文件
    config_dir = os.path.join(skill_root, 'config')
    for cfg in ['strategy_config.yaml', 'scoring_weights.yaml', 'risk_rules.yaml']:
        if not os.path.exists(os.path.join(config_dir, cfg)):
            errors.append(f"配置文件缺失: {cfg}")

    # 3. 脚本
    scripts_dir = os.path.join(skill_root, 'skills', 'scripts')
    for script in ['hk_ah_arbitrage_analyzer.py', 'hk_ah_arbitrage_scanner.py']:
        if not os.path.exists(os.path.join(scripts_dir, script)):
            errors.append(f"脚本缺失: {script}")

    return errors, warnings


def main():
    print("=" * 50)
    print("港股AH溢价套利策略 - 一致性检查")
    print("=" * 50)
    print(f"检查目录: {skill_root}\n")

    errors, warnings = check_consistency()

    if errors:
        print("❌ 错误:")
        for e in errors:
            print(f"  - {e}")

    if warnings:
        print("\n⚠️ 警告:")
        for w in warnings:
            print(f"  - {w}")

    if not errors and not warnings:
        print("✅ 所有检查通过")

    print()


if __name__ == "__main__":
    main()
