#!/usr/bin/env python3
"""
简化版融合策略推荐
使用腾讯股票接口获取实时数据，基于涨幅+板块热度推荐
"""

import yaml
import requests
from datetime import datetime

def load_watchlist():
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'my_stock_pool', 'watchlist.yaml')
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data.get('watchlist', {})

def get_stock_quotes(codes):
    tencent_codes = []
    for code in codes:
        if len(code) == 6:
            tencent_codes.append(f"sh{code}" if code.startswith('6') else f"sz{code}")
        elif len(code) == 5:
            tencent_codes.append(f"hk{code}")
    
    all_results = {}
    batch_size = 60
    
    for i in range(0, len(tencent_codes), batch_size):
        batch = tencent_codes[i:i+batch_size]
        url = f"https://qt.gtimg.cn/q={','.join(batch)}"
        
        try:
            resp = requests.get(url, timeout=30)
            resp.encoding = 'gb2312'
            
            for line in resp.text.strip().split(';'):
                line = line.strip()
                if not line or not line.startswith('v_'):
                    continue
                
                parts = line.split('~')
                if len(parts) < 45:
                    continue
                
                code_key = line.split('=')[0][2:]
                code = code_key[2:]
                
                name = parts[1]
                price = float(parts[3]) if parts[3] else 0
                change_pct = float(parts[32]) if parts[32] else 0
                volume = float(parts[36]) if parts[36] else 0  # 成交额
                
                all_results[code] = {
                    'name': name,
                    'code': code,
                    'price': price,
                    'change': change_pct,
                    'volume': volume
                }
        except Exception as e:
            print(f"获取批次失败: {e}")
    
    return all_results

def calculate_sector_score(stocks_data):
    """计算板块热度得分"""
    sector_scores = {}
    sector_count = {}
    
    for stock in stocks_data:
        sector = stock['sector']
        if sector not in sector_scores:
            sector_scores[sector] = 0
            sector_count[sector] = 0
        sector_scores[sector] += stock['change']
        sector_count[sector] += 1
    
    # 平均涨幅
    for sector in sector_scores:
        sector_scores[sector] = sector_scores[sector] / sector_count[sector]
    
    return sector_scores

def fusion_recommend(stocks_data, sector_scores, top_n=5):
    """融合推荐算法"""
    for stock in stocks_data:
        sector = stock['sector']
        change = stock['change']
        is_core = stock['category'] == 'core'
        
        # 基础得分：涨幅得分 (0-50分)
        change_score = min(max(change * 3, 0), 50) if change > 0 else 0
        
        # 板块热度得分 (0-20分)
        sector_score = min(max(sector_scores.get(sector, 0) * 2, 0), 20)
        
        # 核心股加分 (0-15分)
        core_score = 15 if is_core else 0
        
        # 成交额加分 (0-15分) - 成交量大代表关注度高
        volume_score = min(stock['volume'] / 100000000, 15)  # 1亿以上得满分
        
        # 综合得分
        total_score = change_score + sector_score + core_score + volume_score
        
        stock['fusion_score'] = round(total_score, 2)
        stock['score_breakdown'] = {
            'change_score': round(change_score, 2),
            'sector_score': round(sector_score, 2),
            'core_score': core_score,
            'volume_score': round(volume_score, 2)
        }
    
    # 排序
    stocks_data.sort(key=lambda x: x['fusion_score'], reverse=True)
    
    # 计算仓位建议
    top_stocks = stocks_data[:top_n]
    for i, stock in enumerate(top_stocks):
        # 排名越靠前，仓位越高
        base_position = 0.20 - i * 0.03
        # 根据得分调整
        score_adj = (stock['fusion_score'] - 50) / 100 * 0.10
        position = max(0.08, min(0.25, base_position + score_adj))
        stock['position_pct'] = round(position * 100, 1)
    
    return top_stocks

def main():
    print('='*70)
    print('融合策略推荐报告 [基于实时行情]')
    print(f'生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('='*70)
    
    # 加载股票池
    watchlist = load_watchlist()
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
    
    print(f'📋 自选股池共 {len(stocks)} 只股票')
    
    # 获取行情
    codes = [s['code'] for s in stocks]
    quotes = get_stock_quotes(codes)
    
    # 合并数据
    stocks_data = []
    for stock in stocks:
        code = stock['code']
        quote = quotes.get(code)
        if quote:
            stocks_data.append({
                'name': stock['name'],
                'code': code,
                'sector': stock['sector'],
                'category': stock['category'],
                'price': quote['price'],
                'change': quote['change'],
                'volume': quote['volume']
            })
    
    print(f'✅ 成功获取 {len(stocks_data)} 只股票行情')
    
    # 计算板块热度
    sector_scores = calculate_sector_score(stocks_data)
    
    print('\n📊 板块热度排名:')
    sorted_sectors = sorted(sector_scores.items(), key=lambda x: x[1], reverse=True)
    for i, (sector, score) in enumerate(sorted_sectors[:5], 1):
        print(f'   {i}. {sector}: {score:+.2f}%')
    
    # 融合推荐
    recommendations = fusion_recommend(stocks_data, sector_scores, top_n=5)
    
    # 输出推荐
    print('\n' + '='*70)
    print('🎯 TOP 5 融合推荐')
    print('='*70)
    
    for i, stock in enumerate(recommendations, 1):
        emoji = '🔥' if i == 1 else '✅' if i == 2 else '📌'
        bd = stock['score_breakdown']
        
        print(f'\n{emoji} {i}. {stock["name"]} ({stock["code"]})')
        print(f'   综合得分: {stock["fusion_score"]:.1f} 分')
        print(f'   当前价格: ¥{stock["price"]:.2f}  |  涨幅: {stock["change"]:+.2f}%')
        print(f'   所属板块: {stock["sector"]}  |  类型: {stock["category"]}')
        print(f'   得分构成: 涨幅{bd["change_score"]:.1f} + 板块{bd["sector_score"]:.1f} + 核心{bd["core_score"]:.0f} + 成交{bd["volume_score"]:.1f}')
        print(f'   建议仓位: {stock["position_pct"]:.0f}%')
        
        # 生成买入理由
        reasons = []
        if stock['change'] > 5:
            reasons.append("强势上涨，资金关注度高")
        if stock['category'] == 'core':
            reasons.append("核心持仓标的，基本面扎实")
        if sector_scores.get(stock['sector'], 0) > 2:
            reasons.append(f"所属{stock['sector']}板块热度高")
        if i <= 3:
            reasons.append("综合评分靠前，趋势确认")
        
        print(f'   买入理由: {"；".join(reasons)}')
    
    # 统计
    total_position = sum(s['position_pct'] for s in recommendations)
    up_count = sum(1 for s in stocks_data if s['change'] > 0)
    
    print('\n' + '='*70)
    print(f'📈 统计: 上涨 {up_count}/{len(stocks_data)} 只 | 总建议仓位: {total_position:.0f}%')
    print('='*70)
    print('⚠️  仅供参考，不构成投资建议。股市有风险，投资需谨慎。')
    
    # 保存结果
    import json
    result = {
        'date': datetime.now().strftime('%Y%m%d'),
        'session': 'FUSION_REALTIME',
        'generated_at': datetime.now().isoformat(),
        'recommendations': [
            {
                'rank': i+1,
                'code': s['code'],
                'name': s['name'],
                'sector': s['sector'],
                'price': s['price'],
                'change': s['change'],
                'fusion_score': s['fusion_score'],
                'position_pct': s['position_pct']
            }
            for i, s in enumerate(recommendations)
        ]
    }
    
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'recommendations', r'fusion_realtime_recommendation.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'\n💾 推荐已保存至: {output_path}')

if __name__ == '__main__':
    main()
