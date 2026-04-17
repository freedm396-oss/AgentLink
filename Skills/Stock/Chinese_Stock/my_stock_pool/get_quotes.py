#!/usr/bin/env python3
"""
获取自选股池实时行情并排序
使用腾讯股票接口
"""

import yaml
import requests
from datetime import datetime

def load_watchlist():
    """加载自选股池"""
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'my_stock_pool', 'watchlist.yaml')
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data.get('watchlist', {})

def get_stock_quotes(codes):
    """批量获取股票行情"""
    # 构建腾讯API代码格式
    tencent_codes = []
    for code in codes:
        if len(code) == 6:
            if code.startswith('6'):
                tencent_codes.append(f"sh{code}")
            else:
                tencent_codes.append(f"sz{code}")
        elif len(code) == 5:  # 港股
            tencent_codes.append(f"hk{code}")
    
    # 分批获取（每批60只）
    all_results = {}
    batch_size = 60
    
    for i in range(0, len(tencent_codes), batch_size):
        batch = tencent_codes[i:i+batch_size]
        url = f"https://qt.gtimg.cn/q={','.join(batch)}"
        
        try:
            resp = requests.get(url, timeout=30)
            resp.encoding = 'gb2312'
            
            # 解析返回数据
            for line in resp.text.strip().split(';'):
                line = line.strip()
                if not line or not line.startswith('v_'):
                    continue
                
                # 提取代码和名称
                parts = line.split('~')
                if len(parts) < 45:
                    continue
                
                # v_sh600519="1~贵州茅台~600519...
                code_key = line.split('=')[0][2:]  # sh600519
                code = code_key[2:]  # 600519
                
                name = parts[1]
                price = parts[3]  # 当前价
                change_pct = parts[32]  # 涨跌幅
                
                all_results[code] = {
                    'name': name,
                    'code': code,
                    'price': float(price) if price else 0,
                    'change': float(change_pct) if change_pct else 0
                }
        except Exception as e:
            print(f"获取批次 {i//batch_size + 1} 失败: {e}")
    
    return all_results

def main():
    # 加载股票池
    watchlist = load_watchlist()
    
    # 收集所有股票
    stocks = []
    for sector, categories in watchlist.items():
        for category, stock_list in categories.items():
            for name, code in stock_list:
                stocks.append({
                    'name': name,
                    'code': str(code),
                    'sector': sector,
                    'category': category
                })
    
    print(f"共加载 {len(stocks)} 只股票")
    
    # 获取行情
    codes = [s['code'] for s in stocks]
    quotes = get_stock_quotes(codes)
    
    # 合并数据
    results = []
    for stock in stocks:
        code = stock['code']
        quote = quotes.get(code)
        if quote:
            results.append({
                'name': stock['name'],
                'code': code,
                'sector': stock['sector'],
                'category': stock['category'],
                'price': quote['price'],
                'change': quote['change']
            })
    
    print(f"成功获取 {len(results)} 只股票行情")
    
    # 排序
    results.sort(key=lambda x: x['change'], reverse=True)
    
    # 输出
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print('\n' + '='*100)
    print(f'自选股池涨幅排行榜 - {now}')
    print('='*100)
    print(f'{"排名":<6} {"股票名称":<12} {"代码":<10} {"当前价":<10} {"涨幅%":<10} {"板块":<18} {"类型":<8}')
    print('-'*100)
    
    for i, r in enumerate(results[:50], 1):
        emoji = '++' if r['change'] >= 5 else '+' if r['change'] > 0 else '-' if r['change'] < 0 else '='
        print(f'{emoji} {i:<4} {r["name"]:<12} {r["code"]:<10} {r["price"]:<10.2f} {r["change"]:>+7.2f}%   {r["sector"]:<18} {r["category"]:<8}')
    
    if len(results) > 50:
        print(f'\n... (显示前50名，共 {len(results)} 只)')
    
    # 跌幅榜
    print('\n' + '='*100)
    print('跌幅榜 (后15名)')
    print('='*100)
    for i, r in enumerate(results[-15:], len(results)-14):
        print(f'{i:<6} {r["name"]:<12} {r["code"]:<10} {r["price"]:<10.2f} {r["change"]:>+7.2f}%   {r["sector"]:<18} {r["category"]:<8}')
    
    # 统计
    up = sum(1 for r in results if r['change'] > 0)
    down = sum(1 for r in results if r['change'] < 0)
    flat = sum(1 for r in results if r['change'] == 0)
    avg_change = sum(r['change'] for r in results) / len(results) if results else 0
    
    print('\n' + '='*100)
    print(f'统计: 上涨 {up} 只 | 下跌 {down} 只 | 平盘 {flat} 只 | 平均涨幅: {avg_change:+.2f}%')
    print('='*100)

if __name__ == '__main__':
    main()
