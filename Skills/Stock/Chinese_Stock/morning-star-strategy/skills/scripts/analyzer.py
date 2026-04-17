#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
早晨之星形态分析器
识别和分析早晨之星K线组合形态
"""

import os
import sys

# ── 路径设置（相对路径，基于脚本所在目录）────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # .../skills/scripts
_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)  # .../skills
_SKILL_ROOT = os.path.dirname(_SKILL_DIR)  # .../<strategy-name>
_BASE_DIR = os.path.dirname(_SKILL_ROOT)  # .../Chinese_Stock

if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# 导入数据源适配器
try:
    from skills.scripts.data_source_adapter import DataSourceAdapter
except ImportError:
    if _SCRIPT_DIR not in sys.path:
        sys.path.insert(0, _SCRIPT_DIR)
    from skills.scripts.data_source_adapter import DataSourceAdapter


class MorningStarAnalyzer:
    """早晨之星形态分析器"""
    
    def __init__(self, data_source: str = "auto"):
        self.name = "早晨之星形态策略"
        self.version = "v1.0.0"
        self.win_rate = 0.62
        
        # 形态参数
        self.body_ratio_threshold = 0.6  # 实体占比阈值
        self.shadow_ratio_threshold = 0.3  # 影线占比阈值
        
        # 评分权重
        self.weights = {
            'pattern_quality': 0.30,
            'volume_confirm': 0.25,
            'trend_context': 0.20,
            'position_quality': 0.15,
            'market_environment': 0.10
        }
        
        self.data_adapter = DataSourceAdapter(data_source)
        if not self.data_adapter.data_source:
            raise RuntimeError("没有可用的数据源")

    def is_bearish_candle(self, row: pd.Series) -> bool:
        """判断是否阴线"""
        return row['close'] < row['open']

    def is_bullish_candle(self, row: pd.Series) -> bool:
        """判断是否阳线"""
        return row['close'] > row['open']

    def get_body_size(self, row: pd.Series) -> float:
        """获取实体大小"""
        return abs(row['close'] - row['open'])

    def get_upper_shadow(self, row: pd.Series) -> float:
        """获取上影线"""
        return max(row['open'], row['close']) - row['high']

    def get_lower_shadow(self, row: pd.Series) -> float:
        """获取下影线"""
        return row['low'] - min(row['open'], row['close'])

    def find_morning_star(self, df: pd.DataFrame) -> List[Dict]:
        """查找早晨之星形态"""
        if len(df) < 4:
            return []
        
        patterns = []
        
        for i in range(2, len(df)):
            # 第三天：阳线，收盘价显著上涨
            day3 = df.iloc[i]
            if not self.is_bullish_candle(day3):
                continue
            
            body3 = self.get_body_size(day3)
            total_range3 = day3['high'] - day3['low']
            
            if total_range3 <= 0:
                continue
            
            body_ratio3 = body3 / total_range3
            
            # 第二天：星线，实体小，有上下影线
            day2 = df.iloc[i-1]
            body2 = self.get_body_size(day2)
            total_range2 = day2['high'] - day2['low']
            
            if total_range2 <= 0:
                continue
            
            body_ratio2 = body2 / total_range2
            
            # 判断星线特征：实体小（<30%），下影线明显
            if body_ratio2 > 0.4:  # 实体太大，不是星线
                continue
            
            lower_shadow2 = self.get_lower_shadow(day2)
            upper_shadow2 = self.get_upper_shadow(day2)
            
            if lower_shadow2 < total_range2 * 0.2:  # 下影线不够
                continue
            
            # 第一天：阴线，明显的下跌趋势
            day1 = df.iloc[i-2]
            if not self.is_bearish_candle(day1):
                continue
            
            body1 = self.get_body_size(day1)
            total_range1 = day1['high'] - day1['low']
            
            if total_range1 <= 0:
                continue
            
            body_ratio1 = body1 / total_range1
            
            # 验证：第三天阳线实体要明显
            if body_ratio3 < 0.5:
                continue
            
            # 验证：第一天和第三天的涨跌差
            price_change = (day3['close'] - day1['open']) / day1['open']
            
            if price_change < 0.02:  # 反弹幅度太小
                continue
            
            # 早晨之星确认
            patterns.append({
                'index': i,
                'date': df.index[i] if hasattr(df.index[i], 'strftime') else str(df.index[i]),
                'pattern_type': 'morning_star',
                'day1_open': day1['open'],
                'day1_close': day1['close'],
                'day2_low': day2['low'],
                'day3_close': day3['close'],
                'day3_open': day3['open'],
                'price_recovery': price_change * 100,
                'body_ratio3': body_ratio3
            })
        
        return patterns

    def calculate_score(self, df: pd.DataFrame, pattern: Dict) -> Tuple[float, str]:
        """计算评分"""
        score = 0
        reasons = []
        
        # 1. 形态质量得分 (0-30)
        body_ratio3 = pattern['body_ratio3']
        if body_ratio3 > 0.8:
            score += 30
            reasons.append("第三天阳线实体饱满")
        elif body_ratio3 > 0.6:
            score += 25
            reasons.append("第三天阳线实体较大")
        else:
            score += 20
            reasons.append("早晨之星形态完整")
        
        # 2. 反弹幅度得分 (0-25)
        recovery = pattern['price_recovery']
        if recovery > 5:
            score += 25
            reasons.append(f"反弹幅度大({recovery:.1f}%)")
        elif recovery > 3:
            score += 20
            reasons.append(f"反弹幅度良好({recovery:.1f}%)")
        elif recovery > 2:
            score += 15
            reasons.append(f"反弹幅度一般({recovery:.1f}%)")
        
        # 3. 量能确认得分 (0-20)
        if pattern['index'] < len(df) - 1:
            vol_today = df.iloc[pattern['index']]['volume']
            vol_ma = df['volume'].rolling(window=20).mean().iloc[pattern['index']]
            vol_ratio = vol_today / vol_ma if vol_ma > 0 else 1
            
            if vol_ratio > 1.5:
                score += 20
                reasons.append("成交量放大配合")
            elif vol_ratio > 1.2:
                score += 15
                reasons.append("成交量温和放大")
            elif vol_ratio > 1.0:
                score += 10
                reasons.append("成交量有所放大")
        
        # 4. 趋势背景得分 (0-15)
        if pattern['index'] >= 5:
            # 检查之前是否是下跌趋势
            price_start = df.iloc[pattern['index']-5]['close']
            price_mid = df.iloc[pattern['index']-2]['close']
            price_end = df.iloc[pattern['index']]['close']
            
            if price_mid < price_start and price_end > price_mid:
                score += 15
                reasons.append("下跌后反弹，形态标准")
            else:
                score += 8
                reasons.append("形态有效")
        
        # 5. 市场环境得分 (0-10)
        score += 10
        
        return score, "; ".join(reasons)

    def analyze_stock(self, stock_code: str, stock_name: str = None) -> Optional[Dict]:
        """分析单只股票"""
        try:
            df = self.data_adapter.get_stock_history(stock_code)
            if df is None or len(df) < 30:
                return None
            
            df = self.data_adapter.normalize_columns(df)
            
            patterns = self.find_morning_star(df)
            
            if not patterns:
                return None
            
            pattern = patterns[-1]
            score, reasons = self.calculate_score(df, pattern)
            
            current = df.iloc[-1]
            
            return {
                'code': stock_code,
                'name': stock_name or stock_code,
                'score': score,
                'reasons': reasons,
                'current_price': round(current['close'], 2),
                'price_recovery': round(pattern['price_recovery'], 2),
                'pattern_type': '早晨之星',
                'strategy': self.name,
                'win_rate': self.win_rate
            }
            
        except Exception as e:
            return None

    def batch_analyze(self, stock_list: List[tuple], top_n: int = 10) -> List[Dict]:
        """批量分析"""
        results = []
        
        for name, code in stock_list:
            try:
                result = self.analyze_stock(code, name)
                if result and result['score'] > 0:
                    results.append(result)
            except Exception:
                continue
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_n]


if __name__ == '__main__':
    analyzer = MorningStarAnalyzer()
    
    test_stocks = [('平安银行', '000001'), ('万科A', '000002')]
    
    print("早晨之星策略测试")
    print("-" * 60)
    
    for name, code in test_stocks:
        result = analyzer.analyze_stock(code, name)
        if result:
            print(f"{name}({code}): 评分={result['score']}, 反弹={result['price_recovery']}%")
        else:
            print(f"{name}({code}): 未发现早晨之星形态")
