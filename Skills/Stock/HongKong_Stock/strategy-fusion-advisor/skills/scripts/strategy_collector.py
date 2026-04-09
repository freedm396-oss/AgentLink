#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
港股策略收集器 - 收集10个港股策略的推荐结果
"""

import os
import sys
import json
import random
from datetime import datetime
from typing import Dict, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_ROOT = os.path.dirname(SKILLS_DIR)


class HKStrategyCollector:
    """港股策略推荐收集器"""

    def __init__(self, config: Dict):
        self.config = config
        self.strategies = config['fusion']['strategies']
        self.recommendations_per_strategy = config['fusion']['recommendations']['per_strategy']

    def collect_all_recommendations(self) -> List[Dict]:
        all_recommendations = []

        for strategy in self.strategies:
            if not strategy.get('enabled', True):
                continue
            recommendations = self._get_strategy_recommendations(strategy)
            if recommendations:
                all_recommendations.extend(recommendations)

        return all_recommendations

    def _get_strategy_recommendations(self, strategy: Dict) -> List[Dict]:
        """获取单个策略的推荐"""
        strategy_name = strategy['name']
        recommendations = self._load_from_strategy_dir(strategy_name)
        if recommendations:
            return recommendations
        return self._generate_mock_recommendations(strategy)

    def _load_from_strategy_dir(self, strategy_name: str) -> Optional[List[Dict]]:
        """从策略目录加载推荐"""
        strategy_path = os.path.join(SKILL_ROOT, strategy_name)
        if not os.path.exists(strategy_path):
            return None

        recommendations_dir = os.path.join(strategy_path, 'data', 'recommendations')
        if not os.path.exists(recommendations_dir):
            return None

        files = [f for f in os.listdir(recommendations_dir) if f.endswith('.json')]
        if not files:
            return None

        latest_file = max(files, key=lambda x: os.path.getmtime(
            os.path.join(recommendations_dir, x)))

        try:
            with open(os.path.join(recommendations_dir, latest_file),
                      'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'recommendations' in data:
                    return data['recommendations'][:self.recommendations_per_strategy]
                elif 'portfolio' in data:
                    return data['portfolio'][:self.recommendations_per_strategy]
        except Exception:
            pass

        return None

    def _generate_mock_recommendations(self, strategy: Dict) -> List[Dict]:
        """生成模拟推荐（港股）"""
        mock_stocks = [
            {'code': '0700.HK', 'name': '腾讯控股', 'price': 508.0},
            {'code': '9988.HK', 'name': '阿里巴巴', 'price': 126.5},
            {'code': '3690.HK', 'name': '美团-W', 'price': 88.5},
            {'code': '0941.HK', 'name': '中国移动', 'price': 72.0},
            {'code': '0939.HK', 'name': '建设银行', 'price': 8.51},
            {'code': '0992.HK', 'name': '联想集团', 'price': 10.5},
            {'code': '1024.HK', 'name': '快手-W', 'price': 58.0},
            {'code': '3888.HK', 'name': '金山软件', 'price': 32.0},
            {'code': '2382.HK', 'name': '舜宇光学', 'price': 88.0},
            {'code': '2018.HK', 'name': '瑞声科技', 'price': 18.5},
            {'code': '0011.HK', 'name': '恒生银行', 'price': 158.0},
            {'code': '0005.HK', 'name': '汇丰控股', 'price': 72.0},
            {'code': '0823.HK', 'name': '领展房产基金', 'price': 48.0},
            {'code': '0386.HK', 'name': '中国石化', 'price': 5.8},
            {'code': '1038.HK', 'name': '长江基建', 'price': 52.0},
        ]

        random.seed(hash(strategy['name']) % 1000)
        selected = random.sample(mock_stocks,
                                min(self.recommendations_per_strategy, len(mock_stocks)))

        recommendations = []
        for i, stock in enumerate(selected):
            base_score = 100 - i * 10
            strategy_score = max(60, base_score + random.randint(-10, 10))

            recommendations.append({
                'strategy_name': strategy['name'],
                'strategy_display': strategy['display_name'],
                'strategy_win_rate': strategy['win_rate'],
                'stock_code': stock['code'],
                'stock_name': stock['name'],
                'current_price': stock['price'],
                'strategy_score': strategy_score,
                'expected_return': round(random.uniform(5, 20), 1),
                'stop_loss': round(stock['price'] * 0.94, 2),
                'target_price': round(stock['price'] * 1.12, 2),
                'recommendation_time': datetime.now().isoformat()
            })

        return recommendations
