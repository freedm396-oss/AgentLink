#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自选股池加载模块
读取 my_stock_pool/watchlist.yaml，返回标准化的股票列表
"""

import os
import yaml
from typing import Dict, List, Tuple

# 默认路径
DEFAULT_WATCHLIST_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    'my_stock_pool',
    'watchlist.yaml'
)

# 也尝试相对路径
ALT_WATCHLIST_PATHS = [
    '/home/qinliming/.npm-global/lib/node_modules/openclaw/skills/Stock/Chinese_Stock/my_stock_pool/watchlist.yaml',
    os.path.expanduser('~/.npm-global/lib/node_modules/openclaw/skills/Stock/Chinese_Stock/my_stock_pool/watchlist.yaml'),
]


def find_watchlist_path() -> str:
    """查找 watchlist.yaml 的路径"""
    for path in ALT_WATCHLIST_PATHS:
        if os.path.exists(path):
            return path
    # 尝试相对于当前文件的位置
    base = '/home/qinliming/.npm-global/lib/node_modules/openclaw/skills/Stock/Chinese_Stock'
    candidate = os.path.join(base, 'my_stock_pool', 'watchlist.yaml')
    if os.path.exists(candidate):
        return candidate
    raise FileNotFoundError(f"找不到 watchlist.yaml，尝试过的路径: {ALT_WATCHLIST_PATHS}")


def load_watchlist(path: str = None) -> Dict[str, Dict[str, List[Tuple[str, str]]]]:
    """
    加载自选股池

    返回格式:
    {
        '板块名': {
            'core': [('股票名', '代码'), ...],
            'focus': [('股票名', '代码'), ...]
        },
        ...
    }
    """
    if path is None:
        path = find_watchlist_path()

    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    result = {}
    watchlist = data.get('watchlist', {})

    for sector_name, sector_data in watchlist.items():
        result[sector_name] = {
            'core': [],
            'focus': []
        }
        for entry in sector_data.get('core', []):
            if isinstance(entry, list) and len(entry) >= 2:
                result[sector_name]['core'].append((entry[0], entry[1]))
            elif isinstance(entry, str) and len(entry) == 6:
                # 兼容纯代码格式
                result[sector_name]['core'].append((entry, entry))
        for entry in sector_data.get('focus', []):
            if isinstance(entry, list) and len(entry) >= 2:
                result[sector_name]['focus'].append((entry[0], entry[1]))
            elif isinstance(entry, str) and len(entry) == 6:
                result[sector_name]['focus'].append((entry, entry))

    return result


def get_all_stocks_from_watchlist(watchlist: Dict = None) -> List[Tuple[str, str]]:
    """
    从自选股池获取所有股票（名称, 代码）列表
    包含 core + focus
    """
    if watchlist is None:
        watchlist = load_watchlist()

    all_stocks = []
    for sector_name, data in watchlist.items():
        all_stocks.extend(data['core'])
        all_stocks.extend(data['focus'])

    return all_stocks


def get_sector_stocks(watchlist: Dict, sector: str) -> List[Tuple[str, str]]:
    """获取指定板块的所有股票"""
    if sector not in watchlist:
        return []
    data = watchlist[sector]
    return data['core'] + data['focus']


def print_watchlist_summary(watchlist: Dict = None):
    """打印自选股池摘要"""
    if watchlist is None:
        watchlist = load_watchlist()

    total_core = sum(len(d['core']) for d in watchlist.values())
    total_focus = sum(len(d['focus']) for d in watchlist.values())

    print(f"📋 自选股池概览（共 {len(watchlist)} 个板块）")
    print(f"   core 标的: {total_core} 只")
    print(f"   focus 标的: {total_focus} 只")
    print()
    print("板块列表:")
    for sector, data in watchlist.items():
        core_n = len(data['core'])
        focus_n = len(data['focus'])
        print(f"   {sector}: core={core_n}, focus={focus_n}")


if __name__ == '__main__':
    wl = load_watchlist()
    print_watchlist_summary(wl)
    print()
    all_stocks = get_all_stocks_from_watchlist(wl)
    print(f"股票总数: {len(all_stocks)}")
