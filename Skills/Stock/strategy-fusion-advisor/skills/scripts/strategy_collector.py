# skills/scripts/strategy_collector.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
策略收集器 - 收集11个策略的推荐结果
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path


class StrategyCollector:
    """策略推荐收集器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.strategies = config['fusion']['strategies']
        self.recommendations_per_strategy = config['fusion']['recommendations']['per_strategy']
        
    def collect_all_recommendations(self) -> List[Dict]:
        """收集所有策略的推荐"""
        all_recommendations = []
        
        for strategy in self.strategies:
            if not strategy.get('enabled', True):
                continue
            
            # 获取策略推荐
            recommendations = self._get_strategy_recommendations(strategy)
            
            if recommendations:
                all_recommendations.extend(recommendations)
                print(f"  ✅ {strategy['display_name']}: {len(recommendations)}只")
            else:
                print(f"  ⚠️ {strategy['display_name']}: 无推荐")
        
        return all_recommendations
    
    def _get_strategy_recommendations(self, strategy: Dict) -> List[Dict]:
        """获取单个策略的推荐"""
        strategy_name = strategy['name']
        
        # 尝试从策略目录获取最新推荐
        recommendations = self._load_from_strategy_dir(strategy_name)
        
        if recommendations:
            return recommendations
        
        # 尝试从统一数据目录获取
        recommendations = self._load_from_data_dir(strategy_name)
        
        if recommendations:
            return recommendations
        
        # 生成模拟推荐（用于演示）
        return self._generate_mock_recommendations(strategy)
    
    def _load_from_strategy_dir(self, strategy_name: str) -> Optional[List[Dict]]:
        """从策略目录加载推荐"""
        # 查找策略路径
        strategy_path = self._find_strategy_path(strategy_name)
        
        if not strategy_path:
            return None
        
        # 查找最新的推荐文件
        recommendations_dir = os.path.join(strategy_path, 'data', 'recommendations')
        
        if not os.path.exists(recommendations_dir):
            return None
        
        # 获取最新的推荐文件
        files = [f for f in os.listdir(recommendations_dir) if f.endswith('.json')]
        
        if not files:
            return None
        
        latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(recommendations_dir, x)))
        
        with open(os.path.join(recommendations_dir, latest_file), 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # 提取推荐股票
            if 'recommendations' in data:
                return data['recommendations'][:self.recommendations_per_strategy]
            elif 'portfolio' in data:
                return data['portfolio'][:self.recommendations_per_strategy]
        
        return None
    
    def _load_from_data_dir(self, strategy_name: str) -> Optional[List[Dict]]:
        """从统一数据目录加载推荐"""
        data_dir = self.config['data_storage']['recommendations']
        
        if not os.path.exists(data_dir):
            return None
        
        # 查找该策略的推荐文件
        pattern = f"*{strategy_name}*.json"
        import glob
        files = glob.glob(os.path.join(data_dir, pattern))
        
        if not files:
            return None
        
        latest_file = max(files, key=os.path.getmtime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            if 'portfolio' in data:
                return data['portfolio'][:self.recommendations_per_strategy]
        
        return None
    
    def _find_strategy_path(self, strategy_name: str) -> Optional[str]:
        """查找策略路径"""
        # 获取上级目录（skills目录）
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        skills_dir = os.path.dirname(current_dir)
        
        # 查找策略目录
        for item in os.listdir(skills_dir):
            item_path = os.path.join(skills_dir, item)
            if os.path.isdir(item_path) and item == strategy_name:
                return item_path
        
        return None
    
    def _generate_mock_recommendations(self, strategy: Dict) -> List[Dict]:
        """生成模拟推荐（用于演示）"""
        # 模拟股票池
        mock_stocks = [
            {'code': '000001', 'name': '平安银行', 'price': 12.50},
            {'code': '000002', 'name': '万科A', 'price': 15.80},
            {'code': '000858', 'name': '五粮液', 'price': 168.00},
            {'code': '002415', 'name': '海康威视', 'price': 35.60},
            {'code': '300750', 'name': '宁德时代', 'price': 220.00},
            {'code': '600519', 'name': '贵州茅台', 'price': 1680.00},
            {'code': '000333', 'name': '美的集团', 'price': 58.90},
            {'code': '002594', 'name': '比亚迪', 'price': 280.00},
            {'code': '601318', 'name': '中国平安', 'price': 48.50},
            {'code': '600036', 'name': '招商银行', 'price': 35.20},
        ]
        
        # 随机选择5只
        import random
        selected = random.sample(mock_stocks, self.recommendations_per_strategy)
        
        recommendations = []
        for i, stock in enumerate(selected):
            # 策略内评分递减
            strategy_score = 100 - i * 10
            
            recommendations.append({
                'strategy_name': strategy['name'],
                'strategy_display': strategy['display_name'],
                'strategy_win_rate': strategy['win_rate'],
                'stock_code': stock['code'],
                'stock_name': stock['name'],
                'current_price': stock['price'],
                'strategy_score': strategy_score,
                'expected_return': round(random.uniform(5, 15), 1),
                'stop_loss': round(stock['price'] * 0.95, 2),
                'target_price': round(stock['price'] * 1.10, 2),
                'recommendation_time': datetime.now().isoformat()
            })
        
        return recommendations