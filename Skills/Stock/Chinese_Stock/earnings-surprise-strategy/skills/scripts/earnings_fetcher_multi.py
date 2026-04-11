#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财报超预期策略 - 多数据源获取器
优先级: baostock > akshare > tushare > yfinance

baostock: 免费，稳定，有历史季度财务数据（利润表、成长能力、杜邦分析）
akshare: 实时行情可用，财报接口部分被墙
tushare: 需token（未配置则跳过）
yfinance: 支持A股（需安装）
"""
import sys
import os
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# 缓存
_CACHE: Dict = {}
_CACHE_TTL = 300  # 5分钟


def _cache_get(key: str) -> Optional[any]:
    if key in _CACHE:
        item, ts = _CACHE[key]
        if time.time() - ts < _CACHE_TTL:
            return item
    return None


def _cache_set(key: str, val: any):
    _CACHE[key] = (val, time.time())


class MultiSourceEarningsFetcher:
    """多数据源财报获取器"""

    # 数据源
    SOURCE_BAOSTOCK = 'baostock'
    SOURCE_AKSHARE = 'akshare'
    SOURCE_TUSHARE = 'tushare'
    SOURCE_YFINANCE = 'yfinance'

    def __init__(self, preferred_source: str = 'auto'):
        self.preferred_source = preferred_source
        self.available_sources: List[str] = []
        self._probe_sources()

    def _probe_sources(self):
        """探测可用数据源"""
        sources_tested = []

        # 1. baostock - 最稳定
        try:
            import baostock as bs
            lg = bs.login()
            if lg.error_code == '0':
                rs = bs.query_profit_data('sh.600519', 2024, 1)
                self.available_sources.append(self.SOURCE_BAOSTOCK)
                sources_tested.append(('baostock', True, '正常'))
        except Exception as e:
            sources_tested.append(('baostock', False, str(e)))

        # 2. akshare - 实时行情
        try:
            import akshare as ak
            # 测试实时行情
            spot = ak.stock_zh_a_spot_em()
            if spot is not None and not spot.empty:
                self.available_sources.append(self.SOURCE_AKSHARE)
                sources_tested.append(('akshare', True, f'实时行情 {len(spot)}只'))
            else:
                sources_tested.append(('akshare', False, '行情数据为空'))
        except Exception as e:
            sources_tested.append(('akshare', False, str(e)[:50]))

        # 3. tushare - 需要token
        try:
            import tushare as ts
            token = os.environ.get('TUSHARE_TOKEN', '')
            if token:
                ts.set_token(token)
                pro = ts.pro_api(token)
                df = pro.trade_cal(exchange='SSE', start_date='20260401', end_date='20260409')
                self.available_sources.append(self.SOURCE_TUSHARE)
                sources_tested.append(('tushare', True, '已配置token'))
            else:
                sources_tested.append(('tushare', False, '未配置TUSHARE_TOKEN'))
        except Exception as e:
            sources_tested.append(('tushare', False, str(e)[:50]))

        # 4. yfinance
        try:
            import yfinance as yf
            t = yf.Ticker('600519.SS')
            hist = t.history(period='5d')
            if hist is not None and not hist.empty:
                self.available_sources.append(self.SOURCE_YFINANCE)
                sources_tested.append(('yfinance', True, '正常'))
            else:
                sources_tested.append(('yfinance', False, '无数据'))
        except Exception as e:
            sources_tested.append(('yfinance', False, str(e)[:50]))

        print(f"  数据源探测: ", end='')
        for name, ok, msg in sources_tested:
            status = '✅' if ok else '❌'
            print(f"{status}{name}({msg}) ", end='')
        print()

        if not self.available_sources:
            print("  ⚠️ 警告: 没有可用的数据源!")

    # ─── 股票列表 ───────────────────────────────────────────────

    def get_stock_list(self) -> pd.DataFrame:
        """获取A股股票列表"""
        cache_key = 'stock_list'
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        # 优先用 baostock
        if self.SOURCE_BAOSTOCK in self.available_sources:
            try:
                df = self._get_stock_list_baostock()
                if df is not None and not df.empty:
                    _cache_set(cache_key, df)
                    return df
            except Exception as e:
                print(f"  baostock 股票列表失败: {e}")

        # fallback 用 akshare
        if self.SOURCE_AKSHARE in self.available_sources:
            try:
                import akshare as ak
                df = ak.stock_zh_a_spot_em()
                if df is not None and not df.empty:
                    df = df[['代码', '名称']].rename(columns={'代码': 'code', '名称': 'name'})
                    _cache_set(cache_key, df)
                    return df
            except Exception as e:
                print(f"  akshare 股票列表失败: {e}")

        return pd.DataFrame(columns=['code', 'name'])

    def _get_stock_list_baostock(self) -> Optional[pd.DataFrame]:
        """baostock 获取股票列表"""
        import baostock as bs
        today = datetime.now()
        if today.weekday() >= 5:
            today = today - timedelta(days=today.weekday() - 4)
        else:
            today = today - timedelta(days=1)

        rs = bs.query_all_stock(day=today.strftime('%Y-%m-%d'))
        data = []
        while rs.next():
            data.append(rs.get_row_data())
        if not data:
            return None

        df = pd.DataFrame(data, columns=rs.fields)
        df['code'] = df['code'].str.extract(r'\.(\d{6})$')[0]
        # 只保留A股
        df = df[df['code'].str.match(r'^[036]\d{5}$', na=False)].copy()
        # 尝试从 akshare 获取名称
        df['name'] = df['code']
        return df[['code', 'name']]

    # ─── 单股财务数据 ──────────────────────────────────────────

    def get_earnings(self, stock_code: str, year: int = None, quarter: int = None) -> Optional[Dict]:
        """获取单只股票财报数据"""
        cache_key = f'earnings_{stock_code}_{year}_{quarter}'
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        result = None

        if self.SOURCE_BAOSTOCK in self.available_sources:
            result = self._get_earnings_baostock(stock_code, year, quarter)

        if result is None and self.SOURCE_AKSHARE in self.available_sources:
            result = self._get_earnings_akshare(stock_code, year, quarter)

        if result is not None:
            _cache_set(cache_key, result)

        return result

    def _get_earnings_baostock(self, stock_code: str, year: int = None, quarter: int = None) -> Optional[Dict]:
        """baostock 获取个股财务数据"""
        import baostock as bs

        # 转换代码格式
        if len(stock_code) == 6:
            prefix = 'sh.' if stock_code.startswith(('6', '5')) else 'sz.'
            bs_code = f'{prefix}{stock_code}'
        else:
            bs_code = stock_code

        lg = bs.login()

        if year is None:
            year = 2024

        # profit_data 是「本报告期」数据，不累加，逐季度获取
        # 获取近两年共8个季度原始数据
        all_profit = {}   # key: (year, quarter) -> net_profit
        all_revenue = {}  # key: (year, quarter) -> MBRevenue
        latest_key = None

        for y in [year, year - 1, year - 2]:
            for q in [1, 2, 3, 4]:
                try:
                    rs = bs.query_profit_data(bs_code, y, q)
                    rows = []
                    while rs.next():
                        rows.append(rs.get_row_data())
                    if rows and rows[0][6]:  # netProfit field
                        net_p = float(rows[0][6])
                        mb_rev = float(rows[0][8]) if rows[0][8] else 0
                        stat = rows[0][2]  # statDate
                        all_profit[(y, q)] = {'net_profit': net_p, 'MBRevenue': mb_rev, 'statDate': stat}
                        # 最新的（statDate最大）
                        if latest_key is None or (y, q) > latest_key:
                            latest_key = (y, q)
                except:
                    pass

        if not latest_key:
            bs.logout()
            return None

        # 当前季度和去年同期
        y, q = latest_key
        prev_y = y - 1 if q == 1 else y
        prev_q = 4 if q == 1 else q - 1
        prev_key = (prev_y, prev_q)

        curr = all_profit.get(latest_key, {})
        prev = all_profit.get(prev_key, {})

        net_profit = curr.get('net_profit', 0)
        net_profit_yoy = 0.0
        if prev.get('net_profit') and prev['net_profit'] != 0:
            net_profit_yoy = (curr['net_profit'] - prev['net_profit']) / abs(prev['net_profit']) * 100

        # 营收 YoY
        revenue_yoy = 0.0
        if prev.get('MBRevenue') and prev['MBRevenue'] != 0:
            revenue_yoy = (curr.get('MBRevenue', 0) - prev['MBRevenue']) / abs(prev['MBRevenue']) * 100

        # 获取 ROE、毛利率等（从 dupont / profit_data）
        try:
            rs_d = bs.query_dupont_data(bs_code, y, q)
            rows_d = []
            while rs_d.next():
                rows_d.append(rs_d.get_row_data())
            roe = 0.0
            if rows_d and rows_d[0][3]:
                roe = float(rows_d[0][3]) * 100  # dupontROE 是小数
        except:
            roe = 0.0

        try:
            rs_p = bs.query_profit_data(bs_code, y, q)
            rows_p = []
            while rs_p.next():
                rows_p.append(rs_p.get_row_data())
            if rows_p:
                gp_margin = float(rows_p[0][5]) * 100 if rows_p[0][5] else 0  # gpMargin
                np_margin = float(rows_p[0][4]) * 100 if rows_p[0][4] else 0  # npMargin
                eps_ttm = float(rows_p[0][7]) if rows_p[0][7] else 0
        except:
            gp_margin, np_margin, eps_ttm = 0, 0, 0

        # 获取成长数据
        revenue_yoy_from_growth = 0.0
        net_profit_yoy_from_growth = 0.0
        try:
            rs_g = bs.query_growth_data(bs_code, y, q)
            rows_g = []
            while rs_g.next():
                rows_g.append(rs_g.get_row_data())
            if rows_g:
                gf = rs_g.fields
                gd = rows_g[0]
                if 'YOYNI' in gf:
                    net_profit_yoy_from_growth = float(gd[gf.index('YOYNI')]) * 100 if gd[gf.index('YOYNI')] else 0
                if 'YOYPNI' in gf:
                    revenue_yoy_from_growth = float(gd[gf.index('YOYPNI')]) * 100 if gd[gf.index('YOYPNI')] else 0
        except:
            pass

        # 优先用 growth_data 的 YoY（来自财报披露），其次自己计算
        if net_profit_yoy_from_growth != 0:
            net_profit_yoy = net_profit_yoy_from_growth
        if revenue_yoy_from_growth != 0:
            revenue_yoy = revenue_yoy_from_growth

        # 获取股票名称（从 akshare 实时行情）
        stock_name = stock_code
        try:
            if self.SOURCE_AKSHARE in self.available_sources:
                import akshare as ak
                spot = ak.stock_zh_a_spot_em()
                row = spot[spot['代码'] == stock_code]
                if not row.empty:
                    stock_name = row['名称'].iloc[0]
        except:
            pass

        result = {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'year': y,
            'quarter': q,
            'pub_date': curr.get('statDate', ''),
            'stat_date': curr.get('statDate', ''),
            'net_profit': net_profit,
            'net_profit_yoy': round(net_profit_yoy, 2),
            'revenue_yoy': round(revenue_yoy, 2),
            'eps': eps_ttm,
            'roe': round(roe, 2),
            'gross_margin': round(gp_margin, 2),
            'net_margin': round(np_margin, 2),
            'source': 'baostock',
        }

        bs.logout()
        return result

    def _get_earnings_akshare(self, stock_code: str, year: int = None, quarter: int = None) -> Optional[Dict]:
        """akshare 获取财务数据（备用）"""
        import akshare as ak

        try:
            # 获取财务指标
            df = ak.stock_financial_analysis_indicator(symbol=stock_code)
            if df is None or df.empty:
                return None

            latest = df.iloc[0]
            return {
                'stock_code': stock_code,
                'stock_name': stock_code,
                'year': year or 2024,
                'quarter': quarter or 4,
                'net_profit': float(latest.get('净利润', 0) or 0),
                'net_profit_yoy': float(latest.get('净利润同比增长率', 0) or 0),
                'revenue_yoy': float(latest.get('营业收入同比增长率', 0) or 0),
                'eps': float(latest.get('基本每股收益', 0) or 0),
                'roe': float(latest.get('净资产收益率', 0) or 0),
                'gross_margin': float(latest.get('销售毛利率', 0) or 0),
                'net_margin': float(latest.get('销售净利率', 0) or 0),
                'source': 'akshare',
            }
        except Exception as e:
            print(f"  akshare earnings error: {e}")
            return None

    # ─── 实时行情 ──────────────────────────────────────────────

    def get_realtime_price(self, stock_code: str) -> Optional[float]:
        """获取实时股价"""
        cache_key = f'price_{stock_code}'
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        price = None

        if self.SOURCE_AKSHARE in self.available_sources:
            try:
                import akshare as ak
                spot = ak.stock_zh_a_spot_em()
                row = spot[spot['代码'] == stock_code]
                if not row.empty:
                    price = float(row['最新价'].iloc[0])
                    _cache_set(cache_key, price)
                    return price
            except:
                pass

        if self.SOURCE_BAOSTOCK in self.available_sources:
            try:
                import baostock as bs
                bs.login()
                if len(stock_code) == 6:
                    prefix = 'sh.' if stock_code.startswith(('6', '5')) else 'sz.'
                    bs_code = f'{prefix}{stock_code}'
                else:
                    bs_code = stock_code

                today = datetime.now()
                start = (today - timedelta(days=10)).strftime('%Y-%m-%d')
                end = today.strftime('%Y-%m-%d')
                rs = bs.query_history_k_data_plus(bs_code, 'date,close', start_date=start, end_date=end)
                data = []
                while rs.next():
                    data.append(rs.get_row_data())
                if data:
                    price = float(data[-1][1]) if data[-1][1] else None  # data[-1] is latest row: [date, close]
                    if price:
                        _cache_set(cache_key, price)
                bs.logout()
            except:
                pass

        return price

    # ─── 扫描 ─────────────────────────────────────────────────

    def scan_market(self, year: int = None, quarter: int = None, top_n: int = 20,
                    min_score: float = 65) -> List[Dict]:
        """
        扫描全市场财报超预期股票

        Args:
            year: 财报年度，默认2025
            quarter: 季度，默认4
            top_n: 返回前N名
            min_score: 最低综合评分
        """
        if year is None:
            year = 2024  # 用已发布的最新财报
        if quarter is None:
            quarter = 4

        print(f"  扫描范围: {year}Q{quarter} (评分≥{min_score})")
        print(f"  可用数据源: {', '.join(self.available_sources) or '无'}")

        # 获取股票列表
        stocks = self.get_stock_list()
        if stocks.empty:
            print("  ❌ 无法获取股票列表")
            return []

        # 过滤 A 股（排除指数）
        stocks = stocks[stocks['code'].str.match(r'^[036]\d{5}$', na=False)]
        total = len(stocks)
        print(f"  A股数量: {total} 只")
        print("-" * 60)

        results = []
        counted = 0

        for _, row in stocks.iterrows():
            code = row['code']
            name = row.get('name', code)
            counted += 1

            if counted % 200 == 0:
                print(f"  进度: {counted}/{total} ({counted/total*100:.1f}%)")

            try:
                earnings = self.get_earnings(code, year, quarter)
                if not earnings:
                    continue

                # 计算超预期评分
                score = self._calc_score(earnings)
                earnings['total_score'] = score

                if score >= min_score:
                    price = self.get_realtime_price(code)
                    if price:
                        earnings['current_price'] = price
                    results.append(earnings)
                    print(f"  ✅ {name}({code}): 综合{score}分 | 净利润YOY:{earnings['net_profit_yoy']:.1f}% | 营收YOY:{earnings['revenue_yoy']:.1f}%")

            except Exception as e:
                pass  # 静默跳过，单股失败不影响全局

            # 避免请求过快
            time.sleep(0.05)

        # 按评分排序
        results.sort(key=lambda x: x['total_score'], reverse=True)

        print("-" * 60)
        print(f"  扫描完成: 共 {len(results)} 只符合条件（{year}Q{quarter}，评分≥{min_score}）")
        return results[:top_n]

    def _calc_score(self, e: Dict) -> float:
        """
        计算财报超预期综合评分
        维度: 业绩超预期(30%) + 增长质量(25%) + 市场反应(20%) + 估值安全(15%) + 机构态度(10%)
        """
        # 1. 超预期程度
        surprise_score = 0
        if e.get('net_profit_yoy', 0) >= 50:
            surprise_score = 100
        elif e.get('net_profit_yoy', 0) >= 30:
            surprise_score = 85
        elif e.get('net_profit_yoy', 0) >= 20:
            surprise_score = 70
        elif e.get('net_profit_yoy', 0) >= 10:
            surprise_score = 55
        elif e.get('net_profit_yoy', 0) >= 0:
            surprise_score = 40
        else:
            surprise_score = 20

        # 2. 增长质量 (ROE、毛利率、净利率)
        quality_score = 0
        roe = e.get('roe', 0)
        gm = e.get('gross_margin', 0)
        nm = e.get('net_margin', 0)

        if roe >= 20 and gm >= 30:
            quality_score = 100
        elif roe >= 15 and gm >= 20:
            quality_score = 80
        elif roe >= 10:
            quality_score = 65
        elif roe >= 5:
            quality_score = 50
        else:
            quality_score = 30

        # 3. 营收增长（附加）
        revenue_score = 50
        if e.get('revenue_yoy', 0) >= 30:
            revenue_score = 100
        elif e.get('revenue_yoy', 0) >= 20:
            revenue_score = 80
        elif e.get('revenue_yoy', 0) >= 10:
            revenue_score = 60

        # 4. EPS
        eps_score = 50
        if e.get('eps', 0) > 1:
            eps_score = 100
        elif e.get('eps', 0) >= 0.5:
            eps_score = 70

        # 综合
        total = (surprise_score * 0.30 +
                 quality_score * 0.25 +
                 revenue_score * 0.20 +
                 eps_score * 0.15 +
                 75 * 0.10)  # 机构态度用模拟中性值

        return round(total, 2)

    def get_signal(self, score: float) -> Tuple[str, str]:
        """根据评分返回信号和操作建议"""
        if score >= 80:
            return '强烈买入', '🔥 强烈推荐'
        elif score >= 70:
            return '买入', '✅ 推荐'
        elif score >= 60:
            return '关注', '👀 关注'
        else:
            return '观望', '❌ 暂缓'


if __name__ == '__main__':
    print("=" * 60)
    print("多数据源财报获取器 - 自检")
    print("=" * 60)
    fetcher = MultiSourceEarningsFetcher()

    print("\n--- 获取单只股票测试 (600519 贵州茅台) ---")
    result = fetcher.get_earnings('600519', 2024, 4)
    if result:
        print(f"结果: {result}")
    else:
        result = fetcher.get_earnings('600519', 2024, 3)
        print(f"结果(Q3): {result}")

    print("\n--- 实时价格测试 ---")
    price = fetcher.get_realtime_price('600519')
    print(f"600519 最新价: {price}")

    print("\n--- 数据源状态 ---")
    print(f"可用数据源: {fetcher.available_sources}")
