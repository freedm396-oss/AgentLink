#!/usr/bin/env python3
"""
港股均线多头排列策略 - 核心分析器
HK MA Bullish Arrangement Analyzer
"""

import sys
import os
import yaml
import numpy as np
import pandas as pd

try:
    import requests
except ImportError:
    requests = None

try:
    import akshare as ak
except ImportError:
    ak = None


class HKBullishAnalyzer:
    """均线多头排列分析器"""

    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "config", "strategy_config.yaml"
            )
        self.config = self._load_config(config_path)
        self.ma_periods = self.config["ma"]["periods"]

    def _load_config(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _get_yahoo_data(self, symbol):
        """通过 Yahoo Finance 获取港股数据（HK股票代码需加 .HK 后缀）"""
        if requests is None:
            return None
        # 转换代码：00700 → 0700.HK，9988 → 9988.HK
        raw = symbol.replace('.HK', '').lstrip('0') or '0'
        orig = symbol.replace('.HK', '')
        leading_zeros = len(orig) - len(orig.lstrip('0'))
        if leading_zeros >= 1:
            code = raw.zfill(len(raw) + 1)
        else:
            code = raw
        code = code + '.HK'
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}'
        params = {'interval': '1d', 'range': '90d'}
        proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
        try:
            r = requests.get(url, params=params, proxies=proxies,
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
            return df.tail(90)
        except Exception as e:
            print(f"Yahoo Finance 获取失败: {e}")
            return None

    def get_stock_data(self, symbol):
        """获取港股数据，优先 Yahoo Finance，备选 akshare，最后 mock"""
        # 优先使用 Yahoo Finance（支持港股）
        df = self._get_yahoo_data(symbol)
        if df is not None and not df.empty:
            print(f"  数据来源: Yahoo Finance ({len(df)} 条)")
            return df

        # 备选 akshare
        if ak is not None:
            try:
                # akshare 港股接口
                df = ak.stock_hk_spot_em()
                print(f"  akshare 获取成功 ({len(df)} 只港股实时行情)")
                return df.tail(60)
            except Exception as e:
                print(f"akshare 获取失败: {e}")

        # 兜底模拟数据
        print("  使用模拟数据")
        return self._get_mock_data(symbol)

    def _get_mock_data(self, symbol):
        """返回模拟数据用于演示"""
        dates = pd.date_range(end=pd.Timestamp.today(), periods=60, freq='D')
        np.random.seed(hash(symbol) % 1000)
        base = 100
        data = {
            'date': dates,
            'open': base + np.random.randn(60).cumsum(),
            'high': base + 2 + np.random.randn(60).cumsum(),
            'low': base - 2 + np.random.randn(60).cumsum(),
            'close': base + np.random.randn(60).cumsum(),
            'volume': np.random.randint(1000000, 10000000, 60),
        }
        return pd.DataFrame(data)

    def calculate_ma(self, df):
        """计算均线"""
        result = {}
        for period in self.ma_periods:
            result[f'ma{period}'] = df['close'].rolling(window=period).mean()
        return result

    def calculate_volume_ma(self, df):
        """计算成交量均线"""
        result = {}
        result['vol_ma5'] = df['volume'].rolling(window=5).mean()
        result['vol_ma20'] = df['volume'].rolling(window=20).mean()
        return result

    def check_ma_arrangement(self, ma_values):
        """检查均线多头排列: MA5 > MA10 > MA20 > MA60"""
        ma5, ma10, ma20, ma60 = (
            ma_values['ma5'].iloc[-1],
            ma_values['ma10'].iloc[-1],
            ma_values['ma20'].iloc[-1],
            ma_values['ma60'].iloc[-1],
        )
        return ma5 > ma10 > ma20 > ma60

    def check_ma_spread(self, ma_values):
        """检查均线发散度: (MA5-MA60)/MA60 > 5%"""
        ma5 = ma_values['ma5'].iloc[-1]
        ma60 = ma_values['ma60'].iloc[-1]
        if ma60 == 0:
            return 0.0
        return (ma5 - ma60) / ma60

    def check_volume_trend(self, vol_values):
        """检查成交量趋势: MA5(量) > MA20(量)"""
        vol_ma5 = vol_values['vol_ma5'].iloc[-1]
        vol_ma20 = vol_values['vol_ma20'].iloc[-1]
        return vol_ma5 > vol_ma20

    def get_southbound_holding(self, symbol):
        """获取港股通持股比例（模拟数据）"""
        # 实际应调用 akshare 或其他数据源获取港股通数据
        # 这里返回模拟值
        np.random.seed(hash(symbol) % 1000)
        return np.random.uniform(0.03, 0.15)

    def score_stock(self, ma_arrangement_ok, ma_spread, southbound, volume_ok):
        """综合评分"""
        score = 0
        if ma_arrangement_ok:
            score += 30
        if ma_spread > 0.05:
            score += 25
        elif ma_spread > 0.03:
            score += 15
        if southbound > 0.05:
            score += 25
        elif southbound > 0.03:
            score += 15
        if volume_ok:
            score += 20
        return score

    def get_signal(self, score):
        """根据评分给出信号"""
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

        # 获取数据
        df = self.get_stock_data(symbol)
        if df is None or df.empty:
            print(f"  无法获取 {symbol} 的数据")
            return None

        # 计算均线
        ma_values = self.calculate_ma(df)
        vol_values = self.calculate_volume_ma(df)

        # 检查条件
        ma_arrangement_ok = self.check_ma_arrangement(ma_values)
        ma_spread = self.check_ma_spread(ma_values)
        southbound = self.get_southbound_holding(symbol)
        volume_ok = self.check_volume_trend(vol_values)

        # 综合评分
        score = self.score_stock(ma_arrangement_ok, ma_spread, southbound, volume_ok)
        signal, rating = self.get_signal(score)

        # 计算建议价格
        entry_price = df['close'].iloc[-1]
        stop_loss = entry_price * (1 - self.config['risk']['stop_loss_pct'])
        take_profit = entry_price * (1 + self.config['risk']['take_profit_pct'])

        # 结果
        result = {
            'symbol': symbol,
            'name': name,
            'close': entry_price,
            'ma_arrangement': 'MA5>MA10>MA20>MA60' if ma_arrangement_ok else '未满足',
            'ma_spread': ma_spread,
            'southbound_holding': southbound,
            'volume_status': '多头' if volume_ok else '空头',
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
        """打印分析结果"""
        if result is None:
            return
        print(f"\n{'=' * 50}")
        print(f"分析结果: {result['symbol']} {result['name']}")
        print(f"{'=' * 50}")
        print(f"  当前价: {result['close']:.2f}")
        print(f"  均线排列: {result['ma_arrangement']}")
        print(f"  均线发散度: {result['ma_spread']:.2%}")
        print(f"  港股通持股: {result['southbound_holding']:.2%}")
        print(f"  量能状态: {result['volume_status']}")
        print(f"  综合评分: {result['score']} ({result['rating']})")
        print(f"  信号: {result['signal']}")
        print(f"  入场价: {result['entry_price']}")
        print(f"  止损价: {result['stop_loss']} (-6%)")
        print(f"  止盈价: {result['take_profit']} (+20%)")
        print(f"  建议: {result['suggestion']}")
        print(f"{'=' * 50}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='港股均线多头排列分析')
    parser.add_argument('--stock', default='00700', help='股票代码')
    parser.add_argument('--name', default='腾讯控股', help='股票名称')
    args = parser.parse_args()

    analyzer = HKBullishAnalyzer()
    result = analyzer.analyze_stock(args.stock, args.name)
    analyzer.print_result(result)


if __name__ == "__main__":
    main()
