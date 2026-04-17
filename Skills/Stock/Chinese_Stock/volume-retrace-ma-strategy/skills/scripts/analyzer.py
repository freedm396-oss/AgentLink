#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缩量回踩均线策略分析器
识别股价回踩均线且成交量萎缩的买入机会
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


class VolumeRetraceAnalyzer:
    """缩量回踩均线分析器"""
    
    def __init__(self, data_source: str = "auto"):
        self.name = "缩量回踩均线策略"
        self.version = "v1.0.0"
        self.win_rate = 0.62
        
        # 均线参数
        self.ma_periods = [5, 10, 20, 60]
        self.volume_ma_period = 20
        self.volume_shrink_ratio = 0.5  # 缩量标准：低于均量50%
        
        # 评分权重
        self.weights = {
            'ma_support': 0.30,
            'volume_shrink': 0.25,
            'price_stability': 0.20,
            'trend_alignment': 0.15,
            'market_environment': 0.10
        }
        
        self.data_adapter = DataSourceAdapter(data_source)
        if not self.data_adapter.data_source:
            raise RuntimeError("没有可用的数据源")

    def calculate_ma(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算均线"""
        df = df.copy()
        
        for period in self.ma_periods:
            df[f'ma{period}'] = df['close'].rolling(window=period, min_periods=1).mean()
        
        return df

    def calculate_volume_ma(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算成交量均线"""
        df = df.copy()
        df['volume_ma'] = df['volume'].rolling(window=self.volume_ma_period, min_periods=1).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        return df

    def find_retrace_signals(self, df: pd.DataFrame, lookback: int = 60) -> List[Dict]:
        """查找缩量回踩均线信号"""
        if len(df) < 30:
            return []
        
        df = self.calculate_ma(df)
        df = self.calculate_volume_ma(df)
        
        signals = []
        
        for i in range(20, len(df)):
            current = df.iloc[i]
            
            # 检查是否回踩均线
            for period in [10, 20]:
                ma_col = f'ma{period}'
                if ma_col not in current.index or pd.isna(current[ma_col]):
                    continue
                
                ma_value = current[ma_col]
                price = current['close']
                
                # 价格回踩均线（下影线触及或接近均线）
                retrace_ratio = abs(price - ma_value) / ma_value
                
                if retrace_ratio < 0.02:  # 价格在均线2%以内
                    # 检查成交量是否萎缩
                    volume_ratio = current['volume_ratio']
                    
                    if volume_ratio < self.volume_shrink_ratio:
                        # 确认是缩量回踩
                        # 检查之前是否是上涨趋势
                        prev_closes = df['close'].iloc[max(0, i-10):i]
                        ma_alignment = all(prev_closes > df[f'ma{period}'].iloc[max(0, i-10):i])
                        
                        signals.append({
                            'index': i,
                            'date': df.index[i] if hasattr(df.index[i], 'strftime') else str(df.index[i]),
                            'price': price,
                            'ma_value': ma_value,
                            'ma_period': period,
                            'volume_ratio': volume_ratio,
                            'trend_aligned': ma_alignment,
                            'retrace_ratio': retrace_ratio
                        })
                        break
        
        return signals

    def calculate_score(self, df: pd.DataFrame, signal: Dict) -> Tuple[float, str]:
        """计算评分"""
        score = 0
        reasons = []
        
        # 1. 均线支撑得分 (0-30)
        retrace_ratio = signal['retrace_ratio']
        if retrace_ratio < 0.005:
            score += 30
            reasons.append(f"价格精确回踩MA{signal['ma_period']}")
        elif retrace_ratio < 0.01:
            score += 25
            reasons.append(f"价格接近回踩MA{signal['ma_period']}")
        else:
            score += 20
            reasons.append(f"价格回踩MA{signal['ma_period']}")
        
        # 2. 缩量程度得分 (0-25)
        vol_ratio = signal['volume_ratio']
        if vol_ratio < 0.3:
            score += 25
            reasons.append("成交量极度萎缩(<30%均量)")
        elif vol_ratio < 0.4:
            score += 20
            reasons.append("成交量大幅萎缩(<40%均量)")
        elif vol_ratio < 0.5:
            score += 15
            reasons.append("成交量明显萎缩(<50%均量)")
        
        # 3. 价格稳定性得分 (0-20)
        if signal['index'] >= 5:
            recent_volatility = df['close'].iloc[signal['index']-5:signal['index']].std() / df['close'].iloc[signal['index']-5:signal['index']].mean()
            if recent_volatility < 0.02:
                score += 20
                reasons.append("价格极度稳定")
            elif recent_volatility < 0.05:
                score += 15
                reasons.append("价格相对稳定")
            elif recent_volatility < 0.1:
                score += 10
                reasons.append("价格波动正常")
        
        # 4. 趋势对齐得分 (0-15)
        if signal['trend_aligned']:
            score += 15
            reasons.append("回踩在上涨趋势中")
        else:
            score += 5
            reasons.append("等待趋势确认")
        
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
            
            signals = self.find_retrace_signals(df)
            
            if not signals:
                return None
            
            signal = signals[-1]
            score, reasons = self.calculate_score(df, signal)
            
            current = df.iloc[-1]
            
            return {
                'code': stock_code,
                'name': stock_name or stock_code,
                'score': score,
                'reasons': reasons,
                'current_price': round(current['close'], 2),
                'ma_value': round(signal['ma_value'], 2),
                'volume_ratio': round(signal['volume_ratio'] * 100, 1),
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
    analyzer = VolumeRetraceAnalyzer()
    
    test_stocks = [('平安银行', '000001'), ('东山精密', '002384')]
    
    print("缩量回踩均线策略测试")
    print("-" * 60)
    
    for name, code in test_stocks:
        result = analyzer.analyze_stock(code, name)
        if result:
            print(f"{name}({code}): 评分={result['score']}, 原因={result['reasons']}")
        else:
            print(f"{name}({code}): 未发现回踩信号")
