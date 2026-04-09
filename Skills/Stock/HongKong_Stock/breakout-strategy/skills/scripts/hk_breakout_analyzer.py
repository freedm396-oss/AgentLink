#!/usr/bin/env python3
"""
港股突破高点策略 - 核心分析器
HK Breakout Strategy Analyzer
"""

import os
import sys
import yaml
import numpy as np
import pandas as pd

try:
    import requests
except ImportError:
    requests = None


class HKBreakoutAnalyzer:
    """突破高点分析器"""

    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "config", "strategy_config.yaml"
            )
        self.config = self._load_config(config_path)
        self.proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}

    def _load_config(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _to_yahoo_code(self, symbol):
        """转换代码为 Yahoo Finance 格式：0700 -> 0700.HK, 9988 -> 9988.HK"""
        # 移除 .HK 后缀和前导0
        raw = symbol.replace('.HK', '').lstrip('0')
        if not raw:
            raw = '0'
        # 前导0的数量决定 Yahoo 格式
        orig = symbol.replace('.HK', '')
        leading_zeros = len(orig) - len(orig.lstrip('0'))
        # Yahoo Finance 对香港股票用 .HK 后缀，4位数字前面保留必要的前导0
        # 00700 → 0700（1个前导0），09988 → 9988（不需要前导0）
        if leading_zeros >= 1:
            # 有前导0的，保持原始有效数字长度 + 1个前导0
            code = raw.zfill(len(raw) + 1)
        else:
            code = raw
        return code + '.HK'

    def get_stock_data(self, symbol):
        """获取港股数据"""
        code = self._to_yahoo_code(symbol)
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}'
        params = {'interval': '1d', 'range': '90d'}
        try:
            r = requests.get(url, params=params, proxies=self.proxies,
                             timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
            data = r.json().get('chart', {}).get('result')
            if not data:
                return None
            d = data[0]
            timestamps = d['timestamp']
            quotes = d['indicators']['quote'][0]
            df = pd.DataFrame({
                'date': pd.to_datetime(timestamps, unit='s'),
                'open': quotes.get('open'),
                'high': quotes.get('high'),
                'low': quotes.get('low'),
                'close': quotes.get('close'),
                'volume': quotes.get('volume'),
            })
            df = df.dropna()
            print(f"  数据来源: Yahoo Finance ({len(df)} 条)")
            return df.tail(90)
        except Exception as e:
            print(f"  数据获取失败: {e}，使用模拟数据")
            return self._get_mock_data(symbol)

    def _get_mock_data(self, symbol):
        """返回模拟数据"""
        dates = pd.date_range(end=pd.Timestamp.today(), periods=90, freq='D')
        np.random.seed(hash(symbol) % 1000)
        base = 100
        # 模拟一个先跌后突破的走势
        trend = np.concatenate([
            np.linspace(0, -15, 40),
            np.linspace(-15, 10, 30),
            np.linspace(10, 5, 20),
        ])
        data = {
            'date': dates,
            'open': base + trend + np.random.randn(90) * 2,
            'high': base + trend + 3 + np.random.randn(90) * 2,
            'low': base + trend - 3 + np.random.randn(90) * 2,
            'close': base + trend + np.random.randn(90) * 2,
            'volume': np.random.randint(5000000, 50000000, 90),
        }
        return pd.DataFrame(data)

    def calculate_rsi(self, prices, period=14):
        """计算 RSI"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def check_break_high(self, df):
        """检查是否突破60日最高价"""
        high_60d = df['high'].rolling(window=60).max().shift(1)
        current_high = df['high'].iloc[-1]
        prev_high = high_60d.iloc[-1]
        if pd.isna(prev_high):
            return False, 0, 0
        ratio = (current_high - prev_high) / prev_high if prev_high > 0 else 0
        return current_high > prev_high, prev_high, ratio

    def check_volume_confirm(self, df):
        """检查量能是否放大2倍"""
        vol_ma50 = df['volume'].rolling(window=50).mean()
        current_vol = df['volume'].iloc[-1]
        ma50_vol = vol_ma50.iloc[-1]
        if pd.isna(ma50_vol) or ma50_vol == 0:
            return False, 0
        ratio = current_vol / ma50_vol
        return ratio > 2.0, ratio

    def check_pullback_test(self, df):
        """检查3日内是否有回踩测试前高"""
        if len(df) < 4:
            return False, "数据不足"
        # 前高（突破前的高点）
        high_60d = df['high'].rolling(window=60).max()
        prev_high = high_60d.iloc[-2]  # 昨日的前高
        if pd.isna(prev_high):
            return False, "前高数据不足"
        # 近3日最低价
        low_3d = df['low'].iloc[-3:].min()
        # 允许2%偏差
        allowed = prev_high * (1 - 0.02)
        if low_3d >= allowed:
            return True, "回踩确认"
        elif low_3d > prev_high * 0.97:
            return True, "轻微穿透"
        else:
            return False, "跌破前高"

    def check_rsi_filter(self, df):
        """检查 RSI 是否在 50-75 区间"""
        rsi = self.calculate_rsi(df['close'], period=14)
        current_rsi = rsi.iloc[-1]
        if pd.isna(current_rsi):
            return False, 50, "数据不足"
        rsi_cfg = self.config['rsi']
        lower = rsi_cfg['lower_bound']
        upper = rsi_cfg['upper_bound']
        in_range = lower < current_rsi < upper
        return in_range, current_rsi, f"{current_rsi:.1f}"

    def score_stock(self, break_ok, volume_ok, pullback_ok, rsi_ok, break_ratio, vol_ratio, rsi_val):
        """综合评分"""
        score = 0
        if break_ok:
            score += 30 if break_ratio > 0.03 else 20
        if volume_ok:
            score += 30 if vol_ratio > 3 else (20 if vol_ratio > 2 else 10)
        if pullback_ok:
            score += 25
        elif rsi_ok:
            score += 15  # 未回踩但 RSI 正常
        if rsi_ok:
            score += 15
        elif 45 < rsi_val < 80:
            score += 8
        return min(score, 100)

    def get_signal(self, score):
        if score >= 85:
            return "强烈买入", "极强"
        elif score >= 75:
            return "买入", "强"
        elif score >= 70:
            return "观望", "中等"
        else:
            return "不建议", "弱"

    def analyze_stock(self, symbol, name=""):
        """分析单只股票"""
        print(f"\n分析 {symbol} {name}...")
        df = self.get_stock_data(symbol)
        if df is None or df.empty:
            print(f"  无法获取数据")
            return None

        # 各条件检查
        break_ok, highest_60d, break_ratio = self.check_break_high(df)
        volume_ok, vol_ratio = self.check_volume_confirm(df)
        pullback_ok, pullback_status = self.check_pullback_test(df)
        rsi_ok, rsi_val, rsi_str = self.check_rsi_filter(df)

        # 综合评分
        score = self.score_stock(break_ok, volume_ok, pullback_ok, rsi_ok,
                                  break_ratio, vol_ratio, rsi_val if not isinstance(rsi_val, str) else 50)
        signal, rating = self.get_signal(score)

        entry_price = df['close'].iloc[-1]
        stop_loss = entry_price * (1 - self.config['risk']['stop_loss_pct'])
        take_profit = entry_price * (1 + self.config['risk']['take_profit_pct'])

        result = {
            'symbol': symbol,
            'name': name,
            'close': entry_price,
            'break_status': '已突破' if break_ok else '未突破',
            'highest_60d': highest_60d,
            'break_ratio': break_ratio,
            'volume_ratio': vol_ratio,
            'volume_ok': volume_ok,
            'pullback_status': pullback_status,
            'pullback_ok': pullback_ok,
            'rsi': rsi_val if not isinstance(rsi_val, str) else 50,
            'rsi_str': rsi_str,
            'rsi_ok': rsi_ok,
            'score': score,
            'rating': rating,
            'signal': signal,
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'take_profit': round(take_profit, 2),
            'suggestion': f"评分{score}分({rating})，{signal}",
        }
        return result

    def print_result(self, result):
        if result is None:
            return
        print(f"\n{'=' * 50}")
        print(f"分析结果: {result['symbol']} {result['name']}")
        print(f"{'=' * 50}")
        print(f"  当前价: {result['close']:.2f}")
        print(f"  突破状态: {result['break_status']} (60日高:{result['highest_60d']:.2f} 超:{result['break_ratio']:.2%})")
        print(f"  量能: {result['volume_ratio']:.2f}x (MA50)  {'✅' if result['volume_ok'] else '❌'}")
        print(f"  回踩: {result['pullback_status']} {'✅' if result['pullback_ok'] else '❌'}")
        print(f"  RSI(14): {result['rsi_str']} {'✅' if result['rsi_ok'] else '❌'}")
        print(f"  综合评分: {result['score']} ({result['rating']})")
        print(f"  信号: {result['signal']}")
        print(f"  入场价: {result['entry_price']} | 止损: {result['stop_loss']} | 止盈: {result['take_profit']}")
        print(f"{'=' * 50}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='港股突破高点分析')
    parser.add_argument('--stock', default='0700.HK', help='股票代码')
    parser.add_argument('--name', default='腾讯控股', help='股票名称')
    args = parser.parse_args()

    analyzer = HKBreakoutAnalyzer()
    result = analyzer.analyze_stock(args.stock, args.name)
    analyzer.print_result(result)


if __name__ == "__main__":
    main()
