#!/usr/bin/env python3
"""
本地测试 LookOnChain 分析器
测试文章生成功能并确保输出到正确目录
"""

import os
import sys
import datetime

# 确保可以导入模块
sys.path.insert(0, os.path.dirname(__file__))

from lookonchain.scraper import LookOnChainScraper
from lookonchain.translator import ChineseTranslator
from lookonchain.article_generator import ArticleGenerator


def create_test_articles():
    """创建测试文章数据"""
    test_articles = [
        {
            'title': 'Whale Alert: 10,000 ETH Transferred to Binance',
            'url': 'https://www.lookonchain.com/test/article1',
            'summary': 'Large Ethereum whale moves significant funds to exchange',
            'content': '''A crypto whale has just transferred 10,000 ETH (approximately $25 million) to Binance exchange. This massive transfer was detected by our on-chain monitoring systems at block height 18,500,000. 

The whale address, which has been accumulating ETH for over 2 years, suddenly became active during the early Asian trading session. Market analysts are closely monitoring this movement as it could signal a potential major sell-off.

The transfer occurred when Ethereum was trading at $2,500, and similar large movements in the past have often preceded significant price volatility. The whale's wallet still contains over 50,000 ETH worth approximately $125 million.

On-chain data suggests this could be part of a larger institutional rebalancing strategy, as several other high-value addresses have shown similar activity patterns this week.''',
            'id': 'test001'
        },
        {
            'title': 'DeFi Flash Loan Attack Nets $2M in Profits',
            'url': 'https://www.lookonchain.com/test/article2', 
            'summary': 'Sophisticated flash loan exploit targets vulnerable DeFi protocol',
            'content': '''A sophisticated attacker successfully exploited a DeFi protocol using flash loans, netting approximately $2 million in profits within a single transaction. The attack targeted a newly launched yield farming protocol with over $50 million in total value locked.

The exploit utilized a complex multi-step process involving flash loans from Aave, price manipulation on decentralized exchanges, and arbitrage opportunities across different protocols. The entire attack was executed within one block, making it difficult to prevent.

Security researchers have identified the vulnerability as a classic price oracle manipulation attack. The protocol relied on a single price source, which the attacker manipulated using large trades on low-liquidity DEX pairs.

The attack has highlighted ongoing security challenges in the DeFi space, particularly for newer protocols with limited security audits. The affected protocol has since paused its smart contracts and is working on implementing additional security measures.''',
            'id': 'test002'
        },
        {
            'title': 'Bitcoin Mining Pool Consolidation Accelerates',
            'url': 'https://www.lookonchain.com/test/article3',
            'summary': 'Top 5 mining pools now control over 65% of Bitcoin hashrate',
            'content': '''Bitcoin mining pool consolidation has accelerated significantly, with the top 5 mining pools now controlling over 65% of the total network hashrate. This concentration has raised concerns about network decentralization and security.

Foundry USA leads with 28.5% of the hashrate, followed by AntPool with 18.2%, and F2Pool with 12.8%. The consolidation trend has intensified following recent mining difficulty adjustments and the ongoing bear market in cryptocurrency prices.

Smaller mining pools have struggled to remain competitive due to increased operational costs and reduced mining rewards. Many individual miners have migrated to larger pools to ensure more consistent payouts.

Industry experts warn that excessive mining pool consolidation could potentially threaten Bitcoin's decentralized nature. However, they note that individual miners can switch pools relatively easily if concerns arise about centralization.

The situation is being closely monitored by Bitcoin developers and the broader cryptocurrency community, with discussions ongoing about potential solutions to encourage mining decentralization.''',
            'id': 'test003'
        }
    ]
    
    return test_articles

def test_translation_mock(articles):
    """模拟翻译过程"""
    print("🔄 模拟文章翻译过程...")
    
    translation_map = {
        'Whale Alert: 10,000 ETH Transferred to Binance': '鲸鱼警报：10,000 ETH转入币安交易所',
        'DeFi Flash Loan Attack Nets $2M in Profits': 'DeFi闪电贷攻击获利200万美元',
        'Bitcoin Mining Pool Consolidation Accelerates': '比特币矿池整合加速，去中心化引担忧'
    }
    
    translated_articles = []
    for article in articles:
        chinese_title = translation_map.get(article['title'], f"{article['title']} - 翻译标题")
        
        # 模拟中文翻译内容
        chinese_content = f"""根据LookOnChain链上数据监测，{chinese_title}成为当前市场关注焦点。

{article['content'][:200]}...（此处为完整中文翻译内容）

这一事件反映了当前加密货币市场的重要动态，值得投资者密切关注。链上数据显示，类似的大额转账往往预示着市场的重要变化。

我们将持续监控相关地址的活动情况，为读者提供最新的市场分析和投资建议。"""

        summary = f"本文深入分析了{chinese_title}的市场影响，基于LookOnChain专业链上数据监测，为投资者提供重要的市场洞察。"
        
        translated_article = {
            'original_title': article['title'],
            'chinese_title': chinese_title,
            'original_content': article['content'],
            'chinese_content': chinese_content,
            'summary': summary,
            'url': article['url'],
            'id': article['id'],
            'original_summary': article['summary']
        }
        translated_articles.append(translated_article)
        print(f"   ✅ 已翻译: {chinese_title}")
    
    return translated_articles

def test_local_generation():
    """测试本地文章生成功能"""
    print("🚀 开始本地 LookOnChain 文章生成测试")
    print(f"⏰ 测试时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 设置正确的输出目录
    current_dir = os.path.dirname(os.path.dirname(__file__))  # 上一级目录
    output_dir = os.path.join(current_dir, 'content', 'posts')
    
    print(f"📁 目标输出目录: {output_dir}")
    print(f"📁 目录是否存在: {os.path.exists(output_dir)}")
    
    if not os.path.exists(output_dir):
        print("❌ 目标目录不存在，创建目录...")
        os.makedirs(output_dir, exist_ok=True)
    
    # 步骤1: 创建测试数据
    print("\n" + "="*50)
    print("📰 步骤1: 创建测试文章数据")
    print("="*50)
    
    raw_articles = create_test_articles()
    print(f"✅ 创建了 {len(raw_articles)} 篇测试文章")
    for i, article in enumerate(raw_articles, 1):
        print(f"   {i}. {article['title']}")
    
    # 步骤2: 模拟翻译
    print("\n" + "="*50)
    print("🔄 步骤2: 模拟文章翻译")
    print("="*50)
    
    translated_articles = test_translation_mock(raw_articles)
    print(f"✅ 翻译完成 {len(translated_articles)} 篇文章")
    
    # 步骤3: 生成Hugo文章
    print("\n" + "="*50)
    print("📄 步骤3: 生成 Hugo 文章到目标目录")
    print("="*50)
    
    generator = ArticleGenerator()
    
    # 重要：修改输出目录为实际的 content/posts 目录
    generated_files = []
    
    for i, article in enumerate(translated_articles, 1):
        print(f"\n📝 生成文章 {i}: {article['chinese_title']}")
        
        # 使用正确的输出目录
        file_path = generator.create_hugo_article(article, output_dir)
        if file_path:
            generated_files.append(file_path)
            print(f"   ✅ 成功生成: {file_path}")
            
            # 验证文件是否真的创建了
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"   📊 文件大小: {file_size} 字节")
            else:
                print(f"   ❌ 文件创建失败: {file_path}")
        else:
            print(f"   ❌ 生成失败")
    
    # 步骤4: 验证结果
    print("\n" + "="*50)
    print("✅ 步骤4: 验证生成结果")
    print("="*50)
    
    print(f"📍 输出目录: {output_dir}")
    print(f"📝 生成文件数: {len(generated_files)}")
    
    if generated_files:
        print("\n📋 生成的文件列表:")
        for file_path in generated_files:
            filename = os.path.basename(file_path)
            print(f"   • {filename}")
        
        # 显示第一个文件的部分内容
        print(f"\n📄 文件内容示例 ({os.path.basename(generated_files[0])}):")
        print("-" * 60)
        with open(generated_files[0], 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            # 显示前30行
            for line in lines[:30]:
                print(line)
            if len(lines) > 30:
                print("...")
                print(f"（文件共{len(lines)}行，仅显示前30行）")
        print("-" * 60)
    
    # 检查目标目录中的所有LookOnChain文件
    print(f"\n🔍 检查目录中所有 LookOnChain 相关文件:")
    all_files = os.listdir(output_dir)
    lookonchain_files = [f for f in all_files if 'lookonchain' in f.lower()]
    
    if lookonchain_files:
        print(f"   找到 {len(lookonchain_files)} 个 LookOnChain 文件:")
        for f in sorted(lookonchain_files):
            print(f"   • {f}")
    else:
        print("   未找到任何 LookOnChain 文件")
    
    # 最终总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    print(f"✅ 测试文章: {len(raw_articles)} 篇")
    print(f"✅ 翻译文章: {len(translated_articles)} 篇")
    print(f"✅ 生成文件: {len(generated_files)} 个")
    print(f"📍 输出目录: {output_dir}")
    print(f"✅ 目录验证: {'通过' if os.path.exists(output_dir) else '失败'}")
    
    if generated_files:
        print("🎉 本地测试完全成功！文章已生成到正确目录")
        
        # 询问是否保留文件
        keep_files = input("\n是否保留生成的测试文件？(y/N): ").lower().strip()
        if keep_files != 'y':
            print("\n🧹 清理测试文件...")
            for file_path in generated_files:
                try:
                    os.remove(file_path)
                    print(f"   ✅ 已删除: {os.path.basename(file_path)}")
                except Exception as e:
                    print(f"   ❌ 删除失败: {os.path.basename(file_path)} - {e}")
            print("✅ 清理完成")
        else:
            print("📁 测试文件已保留")
    else:
        print("❌ 测试失败：未能生成任何文件")
    
    print("\n👋 测试结束")

if __name__ == "__main__":
    test_local_generation()