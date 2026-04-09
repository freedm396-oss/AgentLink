#!/usr/bin/env python3
"""
港股分红除权博弈策略 - 核心分析器
HK Dividend Ex-Right Strategy Analyzer
"""

import os
import sys
import yaml
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    requests = None


class HKDividendExrightAnalyzer:
    """分红除权博弈分析器"""

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
        """H股代码转 Yahoo Finance 格式"""
        raw = symbol.replace('.HK', '').lstrip('0') or '0'
        orig = symbol.replace('.HK', '')
        leading_zeros = len(orig) - len(orig.lstrip('0'))
        if leading_zeros >= 1:
            code = raw.zfill(len(raw) + 1)
        else:
            code = raw
        return code + '.HK'

    def get_current_price(self, symbol):
        """获取当前股价"""
        code = self._to_yahoo_code(symbol)
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}'
        params = {'interval': '1d', 'range': '5d'}
        try:
            r = requests.get(url, params=params, proxies=self.proxies,
                             timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
            data = r.json().get('chart', {}).get('result')
            if not data:
                return None
            quotes = data[0]['indicators']['quote'][0]
            closes = [c for c in quotes.get('close', []) if c is not None]
            if not closes:
                return None
            print(f"  股价来源: Yahoo Finance (最新价: {closes[-1]:.2f})")
            return closes[-1]
        except Exception as e:
            print(f"  股价获取失败: {e}")
            return None

    def _get_dividend_info(self, symbol):
        """
        获取分红信息（模拟数据）
        实际应从港交所披露易或 Yahoo Finance 获取
        """
        np.random.seed(hash(symbol) % 1000)

        # 知名高息港股分红数据
        known_dividends = {
            '0005': {  # 汇丰控股
                'annual_dps': 0.52,      # 每股股息（港元）
                'current_price': 72.0,
                'consecutive_years': 12,
                'exright_date_days': 3,   # 距除权日
                'annual_yield': 0.52 / 72.0 * 100,
            },
            '0011': {  # 恒生银行
                'annual_dps': 4.4,
                'current_price': 158.0,
                'consecutive_years': 10,
                'exright_date_days': 1,
                'annual_yield': 4.4 / 158.0 * 100,
            },
            '0016': {  # 新鸿基地产
                'annual_dps': 4.8,
                'current_price': 108.0,
                'consecutive_years': 15,
                'exright_date_days': 4,
                'annual_yield': 4.8 / 108.0 * 100,
            },
        }

        raw = symbol.replace('.HK', '').lstrip('0')
        if raw in known_dividends:
            info = known_dividends[raw].copy()
        else:
            # 模拟随机高息股
            price = np.random.uniform(30, 200)
            dps = price * np.random.uniform(0.05, 0.10)  # 5-10%股息率
            info = {
                'annual_dps': dps,
                'current_price': price,
                'consecutive_years': np.random.randint(3, 20),
                'exright_date_days': np.random.randint(1, 10),
                'annual_yield': dps / price * 100,
            }

        return info

    def _get_market_status(self):
        """获取大盘状态（简化判断：用恒生指数近期走势）"""
        # 简化：模拟返回震荡偏多
        return "震荡偏多"

    def check_yield(self, dividend_yield):
        """检查股息率 > 5%"""
        cfg = self.config['dividend']
        return dividend_yield > cfg['min_yield'] * 100

    def check_history(self, consecutive_years):
        """检查连续分红 >= 5年"""
        cfg = self.config['dividend']
        return consecutive_years >= cfg['min_consecutive_years']

    def check_timing(self, days_to_exright):
        """检查距除权日 <= 5日"""
        cfg = self.config['dividend']
        return 0 < days_to_exright <= cfg['exright_window_days']

    def check_market(self, market_status):
        """检查市场未急跌"""
        return market_status != "急跌"

    def score_stock(self, dividend_yield, consecutive_years, days_to_exright,
                   market_status, yield_ok, history_ok, timing_ok, market_ok):
        """综合评分"""
        score = 0

        # 股息率
        if dividend_yield >= 10:
            score += 30
        elif dividend_yield >= 7:
            score += 25
        elif dividend_yield >= 5:
            score += 20
        elif yield_ok:
            score += 10

        # 分红历史
        if consecutive_years >= 10:
            score += 25
        elif consecutive_years >= 7:
            score += 20
        elif history_ok:
            score += 18

        # 时机窗口
        if 3 <= days_to_exright <= 5:
            score += 25  # 最佳窗口
        elif 1 <= days_to_exright < 3:
            score += 20
        elif timing_ok:
            score += 15

        # 市场环境
        if market_status == "上升趋势":
            score += 20
        elif market_status == "震荡偏多":
            score += 15
        elif market_ok:
            score += 10

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

        # 获取分红信息
        div_info = self._get_dividend_info(symbol)

        # 获取当前股价
        current_price = self.get_current_price(symbol)
        if current_price is None:
            current_price = div_info['current_price']

        # 获取大盘状态
        market_status = self._get_market_status()

        # 各条件检查
        dividend_yield = div_info['annual_yield']
        yield_ok = self.check_yield(dividend_yield)
        history_ok = self.check_history(div_info['consecutive_years'])
        timing_ok = self.check_timing(div_info['exright_date_days'])
        market_ok = self.check_market(market_status)

        # 综合评分
        score = self.score_stock(dividend_yield, div_info['consecutive_years'],
                              div_info['exright_date_days'], market_status,
                              yield_ok, history_ok, timing_ok, market_ok)
        signal, rating = self.get_signal(score)

        # 入场和止损
        entry_price = current_price
        stop_loss = entry_price * (1 - self.config['risk']['stop_loss_pct'])

        # 预期涨幅（除权后自然回落约等于股息率）
        expected_gain = dividend_yield * 0.5  # 抢权涨幅约股息率的一半

        result = {
            'symbol': symbol,
            'name': name,
            'current_price': current_price,
            'annual_dps': div_info['annual_dps'],
            'dividend_yield': dividend_yield,
            'yield_ok': yield_ok,
            'consecutive_years': div_info['consecutive_years'],
            'history_ok': history_ok,
            'days_to_exright': div_info['exright_date_days'],
            'timing_ok': timing_ok,
            'market_status': market_status,
            'market_ok': market_ok,
            'expected_gain': expected_gain,
            'score': score,
            'rating': rating,
            'signal': signal,
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'exit_day': '除权日开盘',
            'max_days': self.config['holding']['max_days'],
            'suggestion': f"评分{score}分({rating})，{signal}",
        }
        return result

    def print_result(self, result):
        if result is None:
            return
        print(f"\n{'=' * 50}")
        print(f"分析结果: {result['symbol']} {result['name']}")
        print(f"{'=' * 50}")
        print(f"  当前价: {result['current_price']:.2f}")
        print(f"  每股股息: {result['annual_dps']:.2f} 港元")
        print(f"  股息率: {result['dividend_yield']:.2f}% {'✅' if result['yield_ok'] else '❌'}")
        print(f"  连续分红: {result['consecutive_years']}年 {'✅' if result['history_ok'] else '❌'}")
        print(f"  距除权日: {result['days_to_exright']}日 {'✅' if result['timing_ok'] else '❌'}")
        print(f"  大市状态: {result['market_status']} {'✅' if result['market_ok'] else '❌'}")
        print(f"  预期涨幅: ~{result['expected_gain']:.1f}%")
        print(f"  综合评分: {result['score']} ({result['rating']})")
        print(f"  信号: {result['signal']}")
        print(f"  入场价: {result['entry_price']} | 止损: {result['stop_loss']} (-3%)")
        print(f"  出场: {result['exit_day']} | 最长持: {result['max_days']}日")
        print(f"  建议: {result['suggestion']}")
        print(f"{'=' * 50}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='港股分红除权博弈分析')
    parser.add_argument('--stock', default='0005.HK', help='股票代码')
    parser.add_argument('--name', default='汇丰控股', help='股票名称')
    args = parser.parse_args()

    analyzer = HKDividendExrightAnalyzer()
    result = analyzer.analyze_stock(args.stock, args.name)
    analyzer.print_result(result)


if __name__ == "__main__":
    main()
