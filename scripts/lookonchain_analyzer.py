#!/usr/bin/env python3
"""
LookOnChain 文章抓取分析器
每日定时抓取 LookOnChain 最新文章，翻译为中文并生成 Hugo 文章
运行时间：每日北京时间18:00 (UTC 10:00) 和 00:00 (UTC 16:00)
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

from lookonchain.enhanced_scraper import EnhancedLookOnChainScraper
from lookonchain.enhanced_processor import EnhancedArticleProcessor
from lookonchain.config import OPENAI_API_KEY


class LookOnChainAnalyzer:
    """LookOnChain 文章分析器主类"""
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or OPENAI_API_KEY
        
        # 初始化增强组件
        self.scraper = EnhancedLookOnChainScraper()
        self.processor = EnhancedArticleProcessor(self.openai_api_key)
        
        print("🚀 LookOnChain 分析器初始化完成")
    
    def run_daily_analysis(self) -> Dict[str, any]:
        """执行每日分析任务"""
        print(f"\n🕕 开始执行 LookOnChain 每日分析任务 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 显示历史统计
            print("\n" + "="*50)
            print("📊 历史文章统计")
            print("="*50)
            self.processor.print_history_statistics()
            
            # 步骤1: 爬取最新文章
            print("\n" + "="*50)
            print("📰 步骤1: 爬取最新 LookOnChain 文章")
            print("="*50)
            
            raw_articles = self.scraper.scrape_latest_articles()
            if not raw_articles:
                return {
                    "success": False,
                    "error": "未能爬取到任何文章",
                    "stage": "scraping"
                }
            
            print(f"✅ 成功爬取 {len(raw_articles)} 篇最新文章")
            
            # 步骤2: 处理文章（翻译 + AI摘要 + 去重）
            print("\n" + "="*50)
            print("🔄 步骤2: 处理文章（翻译 + AI摘要 + 去重）")
            print("="*50)
            
            processed_articles = self.processor.process_articles_batch(raw_articles)
            
            if not processed_articles:
                return {
                    "success": False,
                    "error": "所有文章处理均失败或重复",
                    "failed_articles": len(raw_articles),
                    "stage": "processing"
                }
            
            # 步骤3: 生成Hugo文章
            print("\n" + "="*50)
            print("📄 步骤3: 生成 Hugo 文章")
            print("="*50)
            
            # 这里需要调用现有的文章生成器
            # 暂时简化处理，直接保存处理后的文章
            generation_result = self._save_processed_articles(processed_articles)
            
            # 收集统计信息
            result = {
                "success": generation_result["success"],
                "scrapped_articles": len(raw_articles),
                "processed_articles": len(processed_articles),
                "unique_articles": len(processed_articles),
                "generated_articles": generation_result.get("generated_files", []),
                "api_stats": self.processor.get_api_statistics(),
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
    
    def _save_processed_articles(self, processed_articles: List[Dict]) -> Dict[str, any]:
        """保存处理后的文章为Hugo格式"""
        try:
            import os
            from datetime import datetime
            
            # 确保内容目录存在
            content_dir = "../content/posts"
            os.makedirs(content_dir, exist_ok=True)
            
            generated_files = []
            
            for i, article in enumerate(processed_articles):
                try:
                    # 生成文件名
                    safe_title = "".join(c for c in article['title'][:50] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    safe_title = safe_title.replace(' ', '-')
                    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
                    filename = f"lookonchain-{timestamp}-{i+1}-{safe_title}.md"
                    filepath = os.path.join(content_dir, filename)
                    
                    # 生成Hugo格式内容
                    hugo_content = self._generate_hugo_content(article)
                    
                    # 保存文件
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(hugo_content)
                    
                    generated_files.append(filepath)
                    print(f"✅ 保存文章: {filename}")
                    
                except Exception as e:
                    print(f"❌ 保存文章失败: {e}")
                    continue
            
            return {
                "success": True,
                "generated_files": generated_files,
                "message": f"成功生成 {len(generated_files)} 篇文章"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"保存文章失败: {str(e)}"
            }
    
    def _generate_hugo_content(self, article: Dict) -> str:
        """生成Hugo格式的内容"""
        from datetime import datetime
        
        # 生成标签
        tags = ['LookOnChain', '链上数据', '加密货币分析']
        if 'summary' in article and article['summary']:
            tags.append('AI摘要')
        
        # 生成frontmatter
        frontmatter = {
            "title": article['title'],
            "description": article.get('summary', '')[:200] + '...' if len(article.get('summary', '')) > 200 else article.get('summary', ''),
            "date": datetime.now().isoformat(),
            "tags": tags,
            "categories": ["链上数据分析"],
            "keywords": ["LookOnChain分析", "链上数据追踪", "AI摘要"],
            "author": "ERIC",
            "showToc": True,
            "TocOpen": False,
            "draft": False,
            "slug": f"lookonchain-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        }
        
        # 生成YAML frontmatter
        yaml_frontmatter = "---\n"
        for key, value in frontmatter.items():
            if isinstance(value, list):
                yaml_frontmatter += f"{key}:\n"
                for item in value:
                    yaml_frontmatter += f"  - {item}\n"
            else:
                yaml_frontmatter += f"{key}: {value}\n"
        yaml_frontmatter += "---\n\n"
        
        # 生成正文
        content = yaml_frontmatter
        
        # 添加AI摘要
        if article.get('summary'):
            content += f"## 🤖 AI摘要\n\n{article['summary']}\n\n"
        
        # 添加原文翻译
        content += f"## 📝 原文翻译\n\n{article['content']}\n\n"
        
        # 添加原文链接
        content += f"---\n\n"
        content += f"**原文链接**: [{article.get('original_title', article['title'])}]({article['url']})\n\n"
        content += f"**数据来源**: [LookOnChain](https://www.lookonchain.com)\n\n"
        content += f"**处理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        return content
    
    def print_summary(self, result: Dict[str, any]):
        """打印执行结果摘要"""
        print("\n" + "="*60)
        print("📊 LookOnChain 分析任务执行摘要")
        print("="*60)
        
        if result["success"]:
            print(f"✅ 任务执行成功")
            print(f"📰 爬取文章数: {result.get('scrapped_articles', 0)}")
            print(f"🔄 处理文章数: {result.get('processed_articles', 0)}")
            print(f"🆔 去重后文章数: {result.get('unique_articles', 0)}")
            print(f"📄 生成文章数: {len(result.get('generated_articles', []))}")
            print(f"💬 结果信息: {result.get('message', '')}")
            
            if result.get('generated_articles'):
                print(f"\n📁 生成的文件:")
                for file_path in result['generated_articles']:
                    print(f"   • {os.path.basename(file_path)}")
            
            # 显示API使用统计
            if result.get('api_stats'):
                stats = result['api_stats']
                print(f"\n🤖 API使用统计:")
                print(f"   🔤 翻译调用: {stats.get('translation_calls', 0)} 次")
                print(f"   📝 摘要调用: {stats.get('summary_calls', 0)} 次")
                print(f"   ❌ 失败调用: {stats.get('failed_calls', 0)} 次")
                print(f"   📊 成功率: {stats.get('success_rate', 0):.1%}")
        else:
            print(f"❌ 任务执行失败")
            print(f"🛑 错误阶段: {result.get('stage', 'unknown')}")
            print(f"❗ 错误信息: {result.get('error', 'Unknown error')}")
        
        print(f"⏰ 执行时间: {result.get('execution_time', 'Unknown')}")
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