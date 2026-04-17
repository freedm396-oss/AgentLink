#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSI超卖反弹分析器
识别和分析RSI超卖后的技术性反弹机会
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


class RSIOversoldAnalyzer:
    """RSI超卖反弹分析器"""
    
    def __init__(self, data_source: str = "auto"):
        self.name = "RSI超卖反弹策略"
        self.version = "v1.0.0"
        self.win_rate = 0.58
        
        # RSI参数
        self.rsi_period = 14
        self.oversold_level = 30
        self.overbought_level = 70
        
        # 评分权重
        self.weights = {
            'rsi_oversold': 0.30,
            'price_recovery': 0.25,
            'volume_confirm': 0.20,
            'trend_reversal': 0.15,
            'market_environment': 0.10
        }
        
        self.data_adapter = DataSourceAdapter(data_source)
        if not self.data_adapter.data_source:
            raise RuntimeError("没有可用的数据源")

    def calculate_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算RSI指标"""
        df = df.copy()
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        df['rsi'] = df['rsi'].fillna(50)
        
        return df

    def find_oversold(self, df: pd.DataFrame, lookback: int = 60) -> List[Dict]:
        """查找RSI超卖信号"""
        if len(df) < 20:
            return []
        
        df = self.calculate_rsi(df)
        oversold_signals = []
        
        for i in range(self.rsi_period, len(df)):
            rsi = df.iloc[i]['rsi']
            
            # 检查是否超卖
            if rsi < self.oversold_level:
                # 检查之前是否处于正常或超买状态
                prev_rsi = df['rsi'].iloc[max(0, i-10):i].mean()
                
                if prev_rsi > self.oversold_level:
                    # 确认从高位进入超卖区域
                    oversold_signals.append({
                        'index': i,
                        'date': df.index[i] if hasattr(df.index[i], 'strftime') else str(df.index[i]),
                        'rsi': rsi,
                        'price': df.iloc[i]['close'],
                        'prev_rsi': prev_rsi
                    })
        
        return oversold_signals

    def analyze_recovery(self, df: pd.DataFrame, signal_idx: int) -> Dict:
        """分析反弹情况"""
        if signal_idx >= len(df) - 1:
            return {'has_recovery': False}
        
        recovery_window = df.iloc[signal_idx:min(signal_idx+5, len(df))]
        
        # 计算价格变化
        price_start = df.iloc[signal_idx]['close']
        price_end = recovery_window.iloc[-1]['close']
        price_change = (price_end - price_start) / price_start * 100
        
        # RSI恢复程度
        rsi_start = df.iloc[signal_idx]['rsi']
        rsi_end = recovery_window.iloc[-1]['rsi']
        rsi_recovery = rsi_end - rsi_start
        
        has_recovery = rsi_recovery > 10 and price_change > 0
        
        return {
            'has_recovery': has_recovery,
            'price_change': price_change,
            'rsi_recovery': rsi_recovery
        }

    def calculate_score(self, df: pd.DataFrame, signal: Dict, recovery: Dict) -> Tuple[float, str]:
        """计算评分"""
        score = 0
        reasons = []
        
        # 1. RSI超卖程度得分 (0-30)
        rsi = signal['rsi']
        if rsi < 20:
            score += 30
            reasons.append("RSI严重超卖(<20)")
        elif rsi < 25:
            score += 25
            reasons.append("RSI深度超卖(<25)")
        elif rsi < 30:
            score += 20
            reasons.append("RSI超卖(<30)")
        
        # 2. 反弹强度得分 (0-25)
        if recovery['has_recovery']:
            score += 25
            reasons.append("已出现明显反弹")
        elif recovery['price_change'] > 3:
            score += 18
            reasons.append("价格开始回升")
        elif recovery['price_change'] > 0:
            score += 12
            reasons.append("价格企稳")
        
        # 3. 量能确认得分 (0-20)
        if signal['index'] < len(df) - 1:
            vol_ratio = df.iloc[signal['index'] + 1]['volume'] / df.iloc[signal['index']]['volume'] if df.iloc[signal['index']]['volume'] > 0 else 1
            if vol_ratio > 1.5:
                score += 20
                reasons.append("成交量大幅放大")
            elif vol_ratio > 1.2:
                score += 15
                reasons.append("成交量温和放大")
            elif vol_ratio > 1.0:
                score += 10
                reasons.append("成交量有所放大")
        
        # 4. 趋势反转确认 (0-15)
        if signal['index'] >= 3:
            recent_prices = df['close'].iloc[signal['index']-3:signal['index']].values
            current_price = df.iloc[signal['index']]['close']
            if all(current_price > p for p in recent_prices):
                score += 15
                reasons.append("价格连涨，确认反转")
            elif current_price > recent_prices[-1]:
                score += 10
                reasons.append("价格有所反弹")
        
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
            
            signals = self.find_oversold(df)
            
            if not signals:
                return None
            
            signal = signals[-1]
            recovery = self.analyze_recovery(df, signal['index'])
            
            score, reasons = self.calculate_score(df, signal, recovery)
            
            current = df.iloc[-1]
            
            return {
                'code': stock_code,
                'name': stock_name or stock_code,
                'score': score,
                'reasons': reasons,
                'current_price': round(current['close'], 2),
                'current_rsi': round(current['rsi'], 2),
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
    analyzer = RSIOversoldAnalyzer()
    
    test_stocks = [('平安银行', '000001'), ('万科A', '000002')]
    
    print("RSI超卖策略测试")
    print("-" * 60)
    
    for name, code in test_stocks:
        result = analyzer.analyze_stock(code, name)
        if result:
            print(f"{name}({code}): 评分={result['score']}, RSI={result['current_rsi']}")
        else:
            print(f"{name}({code}): 未发现超卖信号")
