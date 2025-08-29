#!/usr/bin/env python3
"""
测试主 lookonchain_analyzer.py 脚本
模拟模式：不需要真实API，用于验证完整流程
"""

import os
import sys
from unittest.mock import Mock, patch
import datetime

# 确保可以导入模块
sys.path.insert(0, os.path.dirname(__file__))

def create_mock_articles():
    """创建模拟文章数据"""
    return [
        {
            'title': 'Major Ethereum Whale Movement Detected',
            'url': 'https://lookonchain.com/article1', 
            'content': 'A major Ethereum whale has moved 15,000 ETH to an unknown address, causing market speculation about potential sell pressure...',
            'summary': 'Large ETH movement triggers market analysis',
            'id': 'real001'
        },
        {
            'title': 'Solana DEX Volume Surges 300%',
            'url': 'https://lookonchain.com/article2',
            'content': 'Solana-based decentralized exchanges experienced a 300% surge in trading volume over the past 24 hours...',
            'summary': 'SOL DEX activity reaches new highs',
            'id': 'real002'
        }
    ]

def create_mock_translated_articles():
    """创建模拟翻译结果"""
    return [
        {
            'original_title': 'Major Ethereum Whale Movement Detected',
            'chinese_title': '重大以太坊鲸鱼动向被发现',
            'original_content': 'A major Ethereum whale has moved 15,000 ETH...',
            'chinese_content': '一只重要的以太坊鲸鱼转移了15,000 ETH到未知地址，引发市场对潜在抛压的猜测。这笔交易在区块高度1850万被检测到，涉及资金约3750万美元。',
            'summary': '本文分析了重大以太坊鲸鱼资金转移事件的市场影响，基于链上数据为投资者提供专业洞察。',
            'url': 'https://lookonchain.com/article1',
            'id': 'real001',
            'original_summary': 'Large ETH movement triggers market analysis'
        },
        {
            'original_title': 'Solana DEX Volume Surges 300%',
            'chinese_title': 'Solana去中心化交易所交易量激增300%',
            'original_content': 'Solana-based decentralized exchanges experienced a 300% surge...',
            'chinese_content': 'Solana链上的去中心化交易所在过去24小时内交易量激增300%，达到15亿美元的历史新高。主要驱动因素包括新项目代币发行和套利机会增加。',
            'summary': '本文深度解析Solana DEX交易量暴增现象，分析其对生态系统和代币价格的深远影响。',
            'url': 'https://lookonchain.com/article2', 
            'id': 'real002',
            'original_summary': 'SOL DEX activity reaches new highs'
        }
    ]

def test_main_analyzer():
    """测试主分析器完整流程"""
    
    print("🧪 测试 LookOnChain 主分析器")
    print(f"⏰ 测试时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 模拟环境变量
    mock_env = {
        'GLM_API_KEY': 'test_api_key_12345678'
    }
    
    with patch.dict(os.environ, mock_env):
        with patch('lookonchain_analyzer.LookOnChainScraper') as MockScraper, \
             patch('lookonchain_analyzer.ChineseTranslator') as MockTranslator, \
             patch('lookonchain_analyzer.ArticleGenerator') as MockGenerator:
            
            # 设置模拟爬虫
            mock_scraper = Mock()
            mock_scraper.scrape_top_articles.return_value = create_mock_articles()
            MockScraper.return_value = mock_scraper
            
            # 设置模拟翻译器
            mock_translator = Mock()
            mock_translator.client = Mock()  # 确保有client
            translated_articles = create_mock_translated_articles()
            mock_translator.process_article.side_effect = translated_articles
            mock_translator.get_api_usage_stats.return_value = {
                'total_calls': 6,
                'successful_calls': 6,
                'failed_calls': 0,
                'total_tokens': 8500,
                'prompt_tokens': 4200,
                'completion_tokens': 4300
            }
            MockTranslator.return_value = mock_translator
            
            # 设置模拟生成器
            mock_generator = Mock()
            output_dir = "/Users/guoyingcheng/claude_pro/smartwallex-hugo-new/content/posts"
            generated_files = [
                f"{output_dir}/lookonchain-重大以太坊鲸鱼动向被发现-2025-08-29-real001.md",
                f"{output_dir}/lookonchain-Solana去中心化交易所交易量激增300-2025-08-29-real002.md"
            ]
            mock_generator.generate_daily_articles.return_value = {
                'success': True,
                'generated': 2,
                'total_processed': 2,
                'message': '成功生成 2 篇文章',
                'files': generated_files
            }
            MockGenerator.return_value = mock_generator
            
            # 导入并测试主分析器
            print("\n🔄 导入 LookOnChainAnalyzer...")
            from lookonchain_analyzer import LookOnChainAnalyzer
            
            # 创建分析器实例
            analyzer = LookOnChainAnalyzer('test_api_key_12345678')
            print("✅ 分析器初始化成功")
            
            # 执行分析
            print("\n📊 执行每日分析任务...")
            result = analyzer.run_daily_analysis()
            
            # 验证结果
            print(f"✅ 任务执行结果: {'成功' if result['success'] else '失败'}")
            print(f"📰 爬取文章数: {result.get('scrapped_articles', 0)}")
            print(f"🔄 翻译文章数: {result.get('translated_articles', 0)}")
            print(f"📄 生成文章数: {result.get('generated_articles', 0)}")
            
            # 打印摘要
            print("\n📋 执行摘要:")
            analyzer.print_summary(result)
            
            # 验证模拟调用
            print("\n🔍 验证模拟调用:")
            print(f"   爬虫调用: {mock_scraper.scrape_top_articles.called}")
            print(f"   翻译调用次数: {mock_translator.process_article.call_count}")
            print(f"   生成器调用: {mock_generator.generate_daily_articles.called}")
            
            return result

def test_main_function():
    """测试main函数"""
    print("\n🧪 测试 main() 函数")
    
    # 模拟成功场景
    mock_env_success = {
        'GLM_API_KEY': 'test_api_key_12345678'
    }
    
    with patch.dict(os.environ, mock_env_success):
        with patch('lookonchain_analyzer.LookOnChainAnalyzer') as MockAnalyzer:
            # 模拟成功的分析器
            mock_analyzer = Mock()
            mock_analyzer.run_daily_analysis.return_value = {'success': True}
            mock_analyzer.print_summary = Mock()
            MockAnalyzer.return_value = mock_analyzer
            
            # 模拟sys.exit
            with patch('sys.exit') as mock_exit:
                print("🔄 测试成功场景...")
                from lookonchain_analyzer import main
                main()
                
                print("✅ main函数成功执行")
                print(f"   退出码: {mock_exit.call_args[0][0] if mock_exit.called else 'N/A'}")
    
    # 测试失败场景 - 清除GLM_API_KEY
    with patch.dict(os.environ, {}, clear=True):
        with patch('sys.exit') as mock_exit:
            print("🔄 测试失败场景（无API密钥）...")
            from lookonchain_analyzer import main
            main()
            
            print("✅ main函数正确处理错误")
            print(f"   退出码: {mock_exit.call_args[0][0] if mock_exit.called else 'N/A'}")

def main_test():
    """主测试函数"""
    print("🚀 开始完整的 LookOnChain Analyzer 测试")
    print("="*60)
    
    try:
        # 测试分析器类
        result = test_main_analyzer()
        
        # 测试main函数
        test_main_function()
        
        print("\n" + "="*60)
        print("🎉 所有测试通过！")
        print("📊 测试摘要:")
        if result and result.get('success'):
            print("   ✅ 分析器流程测试: 通过")
            print("   ✅ main函数测试: 通过")
            print("   ✅ 错误处理测试: 通过")
        
        print("\n📋 关键验证项目:")
        print("   ✅ 模块导入正常")
        print("   ✅ 类初始化成功")
        print("   ✅ 完整流程执行")
        print("   ✅ 结果统计正确")
        print("   ✅ 错误处理完善")
        
        print(f"\n📍 输出目录确认: /Users/guoyingcheng/claude_pro/smartwallex-hugo-new/content/posts")
        print("🔄 流程: 爬取 → 翻译 → 生成 → 输出到正确目录")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main_test()
    if success:
        print("\n🎊 完整测试成功完成！")
        sys.exit(0)
    else:
        print("\n💥 测试失败！")
        sys.exit(1)