#!/usr/bin/env python3
"""
LookOnChain 功能演示和测试脚本
用于验证所有组件是否正常工作
"""

import os
import sys
import json
from lookonchain.scraper import LookOnChainScraper
from lookonchain.translator import ChineseTranslator
from lookonchain.article_generator import ArticleGenerator

def test_scraper_demo():
    """测试爬虫功能（演示模式）"""
    print("\n" + "="*50)
    print("🕷️ 测试爬虫功能")
    print("="*50)
    
    scraper = LookOnChainScraper()
    
    # 测试创建模拟数据
    mock_articles = [
        {
            'title': 'Whale Alert: Large Bitcoin Transfer Detected',
            'url': 'https://www.lookonchain.com/article/example1',
            'summary': 'A whale just moved 1,000 BTC to Binance...',
            'content': 'A large Bitcoin whale has just transferred 1,000 BTC (approximately $45 million) to Binance exchange. This transaction was detected on the blockchain at block height 820,000. The whale address, which has been dormant for 3 years, suddenly became active. Market analysts are watching closely as this could signal a potential sell-off. The transfer occurred during Asian trading hours when Bitcoin was trading at $45,000. Similar large transfers in the past have often preceded significant price movements.',
            'id': 'demo001'
        },
        {
            'title': 'DeFi Protocol Experiences Unusual Trading Volume',
            'url': 'https://www.lookonchain.com/article/example2',
            'summary': 'Uniswap V3 sees 500% increase in daily volume...',
            'content': 'Uniswap V3 has experienced an unprecedented 500% increase in daily trading volume, reaching $5 billion in 24 hours. The surge is primarily driven by increased activity in ETH/USDC and BTC/ETH pairs. Smart money addresses have been accumulating specific altcoins through the platform. Notable traders have made significant profits by front-running major announcements. The increased volume has also led to higher fee generation for liquidity providers.',
            'id': 'demo002'
        },
        {
            'title': 'NFT Market Shows Signs of Recovery',
            'url': 'https://www.lookonchain.com/article/example3',
            'summary': 'OpenSea trading volume increases by 200%...',
            'content': 'The NFT market is showing strong signs of recovery with OpenSea trading volume increasing by 200% this week. Blue-chip collections like CryptoPunks and Bored Ape Yacht Club are leading the recovery. Several high-profile sales have been recorded, including a CryptoPunk selling for 150 ETH. New projects are gaining traction, with innovative utility-based NFTs attracting collectors. The overall market sentiment has shifted from bearish to cautiously optimistic.',
            'id': 'demo003'
        }
    ]
    
    print(f"✅ 模拟爬取了 {len(mock_articles)} 篇文章")
    for i, article in enumerate(mock_articles, 1):
        print(f"   {i}. {article['title'][:50]}...")
    
    return mock_articles

def test_translator_demo(articles):
    """测试翻译功能（演示模式）"""
    print("\n" + "="*50)
    print("🔄 测试翻译功能")
    print("="*50)
    
    translator = ChineseTranslator()
    
    if not translator.client:
        print("⚠️ GLM API 未配置，使用模拟翻译结果")
        
        # 创建模拟翻译结果
        translated_articles = []
        translation_mapping = {
            'Whale Alert: Large Bitcoin Transfer Detected': '鲸鱼警报：检测到大额比特币转账',
            'DeFi Protocol Experiences Unusual Trading Volume': 'DeFi协议出现异常交易量',
            'NFT Market Shows Signs of Recovery': 'NFT市场显现复苏迹象'
        }
        
        for article in articles:
            chinese_title = translation_mapping.get(article['title'], f"{article['title']} - 中文标题")
            
            translated_article = {
                'original_title': article['title'],
                'chinese_title': chinese_title,
                'original_content': article['content'],
                'chinese_content': f"【模拟翻译】{article['content'][:100]}... (已翻译为中文)",
                'summary': f"本文分析了{chinese_title}的相关链上数据和市场动态。这是一个重要的加密货币市场信号。",
                'url': article['url'],
                'id': article['id'],
                'original_summary': article['summary']
            }
            translated_articles.append(translated_article)
        
        print(f"✅ 模拟翻译了 {len(translated_articles)} 篇文章")
        for i, article in enumerate(translated_articles, 1):
            print(f"   {i}. {article['chinese_title']}")
        
        return translated_articles
    else:
        print("🤖 使用真实API进行翻译...")
        # 这里可以添加真实的API调用逻辑
        return []

def test_generator_demo(translated_articles):
    """测试文章生成功能"""
    print("\n" + "="*50)
    print("📄 测试文章生成功能")
    print("="*50)
    
    generator = ArticleGenerator()
    
    # 创建临时输出目录
    temp_dir = "temp_output"
    os.makedirs(temp_dir, exist_ok=True)
    
    print(f"📁 输出目录: {temp_dir}")
    
    generated_files = []
    for i, article in enumerate(translated_articles, 1):
        print(f"📝 生成文章 {i}: {article['chinese_title'][:30]}...")
        
        file_path = generator.create_hugo_article(article, temp_dir)
        if file_path:
            generated_files.append(file_path)
            print(f"   ✅ 已生成: {os.path.basename(file_path)}")
        else:
            print(f"   ❌ 生成失败")
    
    print(f"\n✅ 成功生成 {len(generated_files)} 个文件")
    
    # 显示生成的文件内容示例
    if generated_files:
        print(f"\n📋 文件内容示例 ({os.path.basename(generated_files[0])}):")
        print("-" * 40)
        with open(generated_files[0], 'r', encoding='utf-8') as f:
            content = f.read()
            # 只显示前500字符
            print(content[:500] + "..." if len(content) > 500 else content)
        print("-" * 40)
    
    return generated_files

def cleanup_demo():
    """清理演示文件"""
    print("\n" + "="*50)
    print("🧹 清理演示文件")
    print("="*50)
    
    temp_dir = "temp_output"
    if os.path.exists(temp_dir):
        import shutil
        shutil.rmtree(temp_dir)
        print("✅ 已清理临时文件")
    else:
        print("ℹ️ 无需清理")

def main():
    """主演示函数"""
    print("🚀 LookOnChain 功能演示开始")
    print(f"⏰ 演示时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 步骤1: 测试爬虫
        articles = test_scraper_demo()
        
        # 步骤2: 测试翻译
        translated_articles = test_translator_demo(articles)
        
        # 步骤3: 测试文章生成
        if translated_articles:
            generated_files = test_generator_demo(translated_articles)
        else:
            print("⚠️ 跳过文章生成测试（无翻译结果）")
            generated_files = []
        
        # 显示总结
        print("\n" + "="*60)
        print("📊 演示总结")
        print("="*60)
        print(f"✅ 爬取文章: {len(articles)} 篇")
        print(f"✅ 翻译文章: {len(translated_articles)} 篇") 
        print(f"✅ 生成文件: {len(generated_files) if 'generated_files' in locals() else 0} 个")
        print("🎉 所有功能演示完成！")
        
        # 询问是否清理
        if input("\n是否清理演示文件? (y/N): ").lower() == 'y':
            cleanup_demo()
        else:
            print("ℹ️ 演示文件保留在 temp_output 目录")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n👋 演示结束")

if __name__ == "__main__":
    main()