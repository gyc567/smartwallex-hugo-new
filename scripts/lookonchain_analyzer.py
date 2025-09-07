#!/usr/bin/env python3
"""
LookOnChain 文章抓取分析器
每日定时抓取 LookOnChain 前3篇文章，翻译为中文并生成 Hugo 文章
运行时间：每日早上6点（北京时间）
"""

import os
import sys
import datetime
from typing import List, Dict

# 添加当前目录到路径，确保能导入模块
sys.path.insert(0, os.path.dirname(__file__))

# 在 GitHub Actions 环境外尝试加载 .env.local 文件
if not os.getenv('GITHUB_ACTIONS'):
    env_local_path = os.path.join(os.path.dirname(__file__), '.env.local')
    if os.path.exists(env_local_path):
        try:
            with open(env_local_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # 只有当环境变量不存在时才设置
                        if not os.getenv(key.strip()):
                            os.environ[key.strip()] = value.strip()
        except Exception as e:
            print(f"⚠️ 警告: 无法加载 .env.local 文件: {e}")

from lookonchain import LookOnChainScraper, ChineseTranslator, ArticleGenerator
from lookonchain.config import OPENAI_API_KEY, MAX_ARTICLES_PER_DAY


class LookOnChainAnalyzer:
    """LookOnChain 文章分析器主类"""
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or OPENAI_API_KEY
        
        # 初始化各个组件
        self.scraper = LookOnChainScraper()
        self.translator = ChineseTranslator(self.openai_api_key)
        self.generator = ArticleGenerator()
        
        print("🚀 LookOnChain 分析器初始化完成")
    
    def run_daily_analysis(self) -> Dict[str, any]:
        """执行每日分析任务"""
        print(f"\n🕕 开始执行 LookOnChain 每日分析任务 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 步骤1: 爬取文章
            print("\n" + "="*50)
            print("📰 步骤1: 爬取 LookOnChain 文章")
            print("="*50)
            
            raw_articles = self.scraper.scrape_top_articles()
            if not raw_articles:
                return {
                    "success": False,
                    "error": "未能爬取到任何文章",
                    "stage": "scraping"
                }
            
            print(f"✅ 成功爬取 {len(raw_articles)} 篇文章")
            
            # 步骤2: 翻译和总结
            print("\n" + "="*50)
            print("🔄 步骤2: 翻译文章为中文")
            print("="*50)
            
            if not self.translator.client:
                return {
                    "success": False,
                    "error": "翻译客户端未初始化，请检查OPENAI_API_KEY",
                    "stage": "translation_init"
                }
            
            processed_articles = []
            failed_articles = 0
            
            for i, article in enumerate(raw_articles[:MAX_ARTICLES_PER_DAY], 1):
                print(f"\n📝 处理文章 {i}/{min(len(raw_articles), MAX_ARTICLES_PER_DAY)}")
                
                try:
                    processed_article = self.translator.process_article(article)
                    
                    if processed_article:
                        processed_articles.append(processed_article)
                        
                        # 检查处理质量
                        stats = processed_article.get('processing_stats', {})
                        successful_steps = sum(stats.values())
                        if successful_steps == len(stats):
                            print(f"✅ 文章 {i} 完全处理成功")
                        elif successful_steps > 0:
                            print(f"⚠️ 文章 {i} 部分处理成功")
                        else:
                            print(f"⚠️ 文章 {i} 基本处理完成（使用fallback）")
                    else:
                        failed_articles += 1
                        print(f"❌ 文章 {i} 处理失败")
                        
                except Exception as e:
                    failed_articles += 1
                    print(f"❌ 文章 {i} 处理时发生异常: {e}")
            
            # 即使部分失败，只要有成功处理的文章就继续
            if not processed_articles:
                return {
                    "success": False,
                    "error": f"所有 {len(raw_articles)} 篇文章处理均失败",
                    "failed_articles": failed_articles,
                    "stage": "translation"
                }
            
            if failed_articles > 0:
                print(f"✅ 成功处理 {len(processed_articles)} 篇文章，失败 {failed_articles} 篇")
            else:
                print(f"✅ 成功处理 {len(processed_articles)} 篇文章")
            
            # 步骤3: 生成Hugo文章
            print("\n" + "="*50)
            print("📄 步骤3: 生成 Hugo 文章")
            print("="*50)
            
            generation_result = self.generator.generate_daily_articles(processed_articles)
            
            # 收集统计信息
            result = {
                "success": generation_result["success"],
                "scrapped_articles": len(raw_articles),
                "translated_articles": len(processed_articles),
                "failed_articles": failed_articles,
                "generated_articles": generation_result["generated"],
                "total_processed": generation_result["total_processed"],
                "generated_files": generation_result.get("files", []),
                "message": generation_result["message"],
                "execution_time": datetime.datetime.now().isoformat(),
                "stage": "completed"
            }
            
            # 如果有错误，添加到结果中
            if not generation_result["success"]:
                result["error"] = generation_result["message"]
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"执行过程中发生错误: {str(e)}",
                "stage": "execution",
                "execution_time": datetime.datetime.now().isoformat()
            }
    
    def print_summary(self, result: Dict[str, any]):
        """打印执行结果摘要"""
        print("\n" + "="*60)
        print("📊 LookOnChain 分析任务执行摘要")
        print("="*60)
        
        if result["success"]:
            print(f"✅ 任务执行成功")
            print(f"📰 爬取文章数: {result.get('scrapped_articles', 0)}")
            print(f"🔄 翻译文章数: {result.get('translated_articles', 0)}")
            
            failed_count = result.get('failed_articles', 0)
            if failed_count > 0:
                print(f"❌ 失败文章数: {failed_count}")
            
            print(f"📄 生成文章数: {result.get('generated_articles', 0)}")
            print(f"💬 结果信息: {result.get('message', '')}")
            
            if result.get('generated_files'):
                print(f"\n📁 生成的文件:")
                for file_path in result['generated_files']:
                    print(f"   • {os.path.basename(file_path)}")
        else:
            print(f"❌ 任务执行失败")
            print(f"🛑 错误阶段: {result.get('stage', 'unknown')}")
            print(f"❗ 错误信息: {result.get('error', 'Unknown error')}")
        
        print(f"⏰ 执行时间: {result.get('execution_time', 'Unknown')}")
        
        # 显示API使用统计
        if hasattr(self.translator, 'logger') and self.translator.logger:
            print("\n🤖 OpenAI API 使用统计:")
            stats = self.translator.get_api_usage_stats()
            if "error" not in stats:
                print(f"   📞 总调用次数: {stats.get('total_calls', 0)}")
                print(f"   ✅ 成功调用: {stats.get('successful_calls', 0)}")
                print(f"   ❌ 失败调用: {stats.get('failed_calls', 0)}")
                print(f"   🔢 消耗Token: {stats.get('total_tokens', 0):,}")
            else:
                print(f"   ❌ 无法获取统计: {stats.get('error', 'Unknown')}")
        
        print("="*60)


def main():
    """主函数"""
    
    print("🌅 LookOnChain 每日文章分析器启动")
    print(f"⏰ 当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查API密钥
    openai_api_key = OPENAI_API_KEY
    if not openai_api_key:
        print("❌ 错误: 未设置 OPENAI_API_KEY 环境变量")
        print("💡 请设置环境变量或在 scripts/.env.local 文件中配置")
        sys.exit(1)
    
    if not os.getenv('GITHUB_ACTIONS'):
        print(f"✅ OpenAI API Key 已配置: {openai_api_key[:8]}...")
    
    # 创建分析器并执行任务
    analyzer = LookOnChainAnalyzer(openai_api_key)
    result = analyzer.run_daily_analysis()
    
    # 打印结果摘要
    analyzer.print_summary(result)
    
    # 根据执行结果设置退出码
    if result["success"]:
        print("\n🎉 任务完成！")
        sys.exit(0)
    else:
        print("\n💥 任务失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()