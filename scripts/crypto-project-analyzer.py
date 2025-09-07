#!/usr/bin/env python3
"""
加密货币项目自动分析和评测生成器
每日抓取GitHub上最热门的加密货币项目，生成专业评测文章
"""

import requests
import json
import os
import datetime
from typing import List, Dict, Any, Set, Optional, Tuple
import time
import re
import hashlib
import config
from openai_client import create_openai_client, extract_content_from_response
try:
    from glm_logger import GLMLogger
except ImportError:
    from openai_client import GLMLogger

class CryptoProjectAnalyzer:
    def __init__(self, github_token: str = None, openai_api_key: str = None):
        self.github_token = github_token
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'SmartWallex-Analyzer/1.0'
        }
        if github_token:
            self.headers['Authorization'] = f'token {github_token}'
        
        # AI客户端初始化
        self.ai_enabled = config.AI_ENABLED and openai_api_key
        if self.ai_enabled:
            try:
                # 初始化日志记录器
                self.ai_logger = GLMLogger()
                
                # 使用OpenAI兼容客户端
                self.ai_client = create_openai_client(
                    api_key=openai_api_key,
                    base_url=config.OPENAI_BASE_URL,
                    model=config.OPENAI_MODEL,
                    logger=self.ai_logger
                )
                
                if self.ai_client:
                    print("✅ AI分析已启用（含日志记录）")
                else:
                    self.ai_enabled = False
                    print("❌ AI客户端创建失败")
                    
            except Exception as e:
                print(f"⚠️  AI客户端初始化失败: {e}")
                self.ai_enabled = False
                self.ai_client = None
                self.ai_logger = None
        else:
            self.ai_client = None
            self.ai_logger = None
            print("ℹ️  AI分析未启用")
        
        # 项目历史记录文件路径
        self.history_file = 'data/analyzed_projects.json'
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """确保data目录存在"""
        os.makedirs('data', exist_ok=True)
    
    def load_analyzed_projects(self) -> Set[str]:
        """加载已分析的项目历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('analyzed_projects', []))
            return set()
        except Exception as e:
            print(f"⚠️  加载项目历史记录失败: {e}")
            return set()
    
    def save_analyzed_projects(self, analyzed_projects: Set[str]):
        """保存已分析的项目历史记录"""
        try:
            data = {
                'last_updated': datetime.datetime.now().isoformat(),
                'total_projects': len(analyzed_projects),
                'analyzed_projects': list(analyzed_projects)
            }
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ 已保存 {len(analyzed_projects)} 个项目记录")
        except Exception as e:
            print(f"⚠️  保存项目历史记录失败: {e}")
    
    def get_project_key(self, project: Dict[str, Any]) -> str:
        """生成项目的唯一标识符"""
        # 使用项目的full_name作为唯一标识
        return project.get('full_name', f"{project.get('owner', {}).get('login', 'unknown')}/{project.get('name', 'unknown')}")
    
    def is_project_analyzed(self, project: Dict[str, Any], analyzed_projects: Set[str]) -> bool:
        """检查项目是否已经被分析过"""
        project_key = self.get_project_key(project)
        return project_key in analyzed_projects
    
    def ai_analyze_project_quality(self, project_details: Dict[str, Any]) -> Tuple[float, str]:
        """使用AI分析项目质量和价值"""
        if not self.ai_enabled:
            return 0.7, "AI分析未启用"
        
        try:
            basic_info = project_details['basic_info']
            readme_content = project_details.get('readme_content', '').strip()
            recent_commits = project_details.get('recent_commits', [])
            languages = project_details.get('languages', {})
            topics = project_details.get('topics', [])
            
            # 构建分析提示
            project_summary = f"""
项目名称: {basic_info['name']}
项目描述: {basic_info.get('description', '无描述')}
GitHub Stars: {basic_info['stargazers_count']}
Fork数量: {basic_info['forks_count']}
主要语言: {basic_info.get('language', '未知')}
项目标签: {', '.join(topics) if topics else '无标签'}
创建时间: {basic_info['created_at'][:10]}
最后更新: {basic_info['updated_at'][:10]}

README摘要: {readme_content[:800] if readme_content else '无README内容'}

最近提交情况: {len(recent_commits)}个最近提交
代码语言分布: {list(languages.keys())[:5] if languages else '无语言数据'}
"""
            
            system_prompt = """你是一个专业的区块链和加密货币项目分析专家。请基于提供的GitHub项目信息，从以下维度进行评估：

1. 技术创新性和实用性
2. 代码质量和活跃度
3. 社区关注和参与度
4. 项目完整性和成熟度
5. 市场潜力和应用价值

请给出0-1之间的质量分数（保留2位小数），其中：
- 0.0-0.3: 低质量项目（空项目、demo项目、过时项目）
- 0.4-0.6: 普通质量项目（基础功能完整但创新性不足）
- 0.7-0.8: 高质量项目（技术先进、功能完整、有实际应用价值）
- 0.9-1.0: 顶级项目（技术领先、社区活跃、商业价值高）

请以JSON格式回复：{"score": 分数, "analysis": "详细分析原因（中文，200字以内）"}"""
            
            user_prompt = f"请分析以下加密货币/区块链GitHub项目：\n\n{project_summary}"
            
            completion = self.ai_client.chat_completions_create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config.AI_TEMPERATURE,
                top_p=config.AI_TOP_P,
                max_tokens=config.AI_ANALYSIS_MAX_TOKENS
            )
            
            response_text = extract_content_from_response(completion, "AI项目质量分析")
            
            # 解析JSON响应
            if not response_text:
                print("⚠️  AI响应为空")
                return 0.5, "AI响应为空"
                
            try:
                result = json.loads(response_text)
                score = float(result.get('score', 0.5))
                analysis = result.get('analysis', '分析内容解析失败')
                
                # 确保分数在有效范围内
                score = max(0.0, min(1.0, score))
                
                return score, analysis
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️  AI响应解析失败: {e}")
                # 尝试从响应中提取数字
                import re
                score_match = re.search(r'"score":\s*([0-9.]+)', response_text)
                if score_match:
                    score = float(score_match.group(1))
                    return max(0.0, min(1.0, score)), "AI分析完成，但详细分析解析失败"
                else:
                    return 0.5, "AI响应格式错误"
        
        except Exception as e:
            print(f"⚠️  AI分析失败: {e}")
            return 0.5, f"AI分析出错: {str(e)}"
    
    def ai_generate_project_summary(self, project_details: Dict[str, Any], ai_analysis: str) -> str:
        """使用AI生成项目摘要"""
        if not self.ai_enabled:
            return "AI摘要生成未启用"
        
        try:
            basic_info = project_details['basic_info']
            category = self.analyze_project_category(project_details)
            
            system_prompt = """你是一个专业的区块链技术写作专家。请基于项目信息生成一个简洁有力的项目摘要，要求：

1. 中文输出，150字以内
2. 突出项目的核心功能和技术特点
3. 结合GitHub数据说明项目热度
4. 适合作为评测文章的开头段落
5. 语言要专业且吸引人

格式要求：直接输出摘要文字，不要JSON格式。"""
            
            user_prompt = f"""请为以下项目生成专业摘要：

项目名称: {basic_info['name']}
项目类型: {category}
项目描述: {basic_info.get('description', '无描述')}
GitHub Stars: {basic_info['stargazers_count']:,}
主要语言: {basic_info.get('language', '未知')}
AI质量分析: {ai_analysis}

请生成一个适合评测文章开头的专业摘要。"""
            
            completion = self.ai_client.chat_completions_create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config.AI_TEMPERATURE,
                top_p=config.AI_TOP_P,
                max_tokens=500
            )
            
            summary = extract_content_from_response(completion, "AI项目摘要生成")
            return summary or "摘要生成失败，请查看日志获取详细信息"
        
        except Exception as e:
            print(f"⚠️  AI摘要生成失败: {e}")
            return f"{basic_info['name']}是一个{self.analyze_project_category(project_details)}项目，在GitHub上获得{basic_info['stargazers_count']:,}个星标。"
    
    def ai_analyze_stars_and_forks(self, project_details: Dict[str, Any]) -> str:
        """使用AI分析项目的star和fork数据"""
        if not self.ai_enabled:
            return "基于GitHub数据的标准分析"
        
        try:
            basic_info = project_details['basic_info']
            created_days = (datetime.datetime.now() - datetime.datetime.strptime(basic_info['created_at'], '%Y-%m-%dT%H:%M:%SZ')).days
            
            system_prompt = """你是一个GitHub数据分析专家。请基于项目的stars、forks数据和创建时间，分析项目的社区表现，要求：

1. 分析stars和forks的比例关系
2. 评估项目的增长速度（基于创建时间）
3. 对比同类项目的平均水平
4. 给出社区活跃度评价
5. 中文输出，100字以内

直接输出分析结果，不要JSON格式。"""
            
            user_prompt = f"""请分析以下项目的GitHub数据表现：

项目名称: {basic_info['name']}
GitHub Stars: {basic_info['stargazers_count']:,}
Fork数量: {basic_info['forks_count']:,}
创建天数: {created_days}天
Star/Fork比例: {basic_info['stargazers_count'] / max(1, basic_info['forks_count']):.1f}:1
日均Stars: {basic_info['stargazers_count'] / max(1, created_days):.2f}个/天"""
            
            completion = self.ai_client.chat_completions_create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config.AI_TEMPERATURE,
                top_p=config.AI_TOP_P,
                max_tokens=300
            )
            
            analysis = extract_content_from_response(completion, "AI数据分析")
            return analysis or f"该项目获得{basic_info['stargazers_count']:,}个星标，显示出良好的社区关注度。"
        
        except Exception as e:
            print(f"⚠️  AI数据分析失败: {e}")
            stars = basic_info['stargazers_count']
            forks = basic_info['forks_count']
            ratio = stars / max(1, forks)
            return f"该项目获得{stars:,}个星标和{forks:,}个Fork，星Fork比为{ratio:.1f}:1，显示出良好的社区关注度。"
    
    def search_crypto_projects(self, days_back: int = 7, max_projects: int = 3) -> List[Dict[str, Any]]:
        """搜索加密货币项目，确保不重复已分析的项目"""
        
        # 加载已分析的项目历史
        analyzed_projects = self.load_analyzed_projects()
        print(f"📚 已分析项目数量: {len(analyzed_projects)}")
        
        # 多种搜索策略
        search_strategies = [
            self._search_by_creation_date,
            self._search_by_recent_activity,
            self._search_by_trending,
            self._search_by_language_specific
        ]
        
        all_projects = []
        
        for strategy in search_strategies:
            try:
                projects = strategy(days_back)
                all_projects.extend(projects)
                time.sleep(2)  # 避免API限制
            except Exception as e:
                print(f"⚠️  搜索策略执行失败: {e}")
                continue
        
        # 去重并过滤已分析的项目
        unique_projects = {}
        new_projects = []
        
        for project in all_projects:
            repo_id = project['id']
            project_key = self.get_project_key(project)
            
            # 跳过重复项目
            if repo_id in unique_projects:
                continue
                
            # 跳过已分析的项目
            if project_key in analyzed_projects:
                print(f"⏭️  跳过已分析项目: {project['name']}")
                continue
            
            # 基本质量过滤
            if self._is_quality_project(project):
                unique_projects[repo_id] = project
                new_projects.append(project)
        
        # AI质量过滤（如果启用）
        if self.ai_enabled and new_projects:
            print(f"🤖 开始AI质量分析，候选项目: {len(new_projects)}个")
            ai_filtered_projects = []
            
            for project in new_projects:
                try:
                    print(f"🔍 AI分析项目: {project['name']}")
                    
                    # 获取项目详情用于AI分析
                    project_details = self.get_project_details(project)
                    ai_score, ai_analysis = self.ai_analyze_project_quality(project_details)
                    
                    print(f"📊 AI评分: {ai_score:.2f} - {project['name']}")
                    
                    if ai_score >= config.AI_FILTER_THRESHOLD:
                        # 将AI分析结果存储到项目详情中，供后续使用
                        project['ai_score'] = ai_score
                        project['ai_analysis'] = ai_analysis
                        ai_filtered_projects.append(project)
                        print(f"✅ 通过AI过滤: {project['name']} (评分: {ai_score:.2f})")
                    else:
                        print(f"❌ 被AI过滤: {project['name']} (评分: {ai_score:.2f}, 阈值: {config.AI_FILTER_THRESHOLD})")
                    
                    # 避免API限制
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"⚠️  AI分析失败: {project['name']} - {e}")
                    # AI分析失败的项目仍然保留
                    ai_filtered_projects.append(project)
            
            new_projects = ai_filtered_projects
            print(f"🎯 AI过滤后剩余项目: {len(new_projects)}个")
        
        # 按多个维度排序（优先考虑AI评分）
        sorted_projects = sorted(
            new_projects,
            key=lambda x: (
                x.get('ai_score', 0.5),  # AI评分（优先级最高）
                x['stargazers_count'],   # 星标数
                x['forks_count'],        # Fork数
                -self._days_since_created(x),  # 创建时间（越新越好）
                -self._days_since_updated(x)   # 更新时间（越新越好）
            ),
            reverse=True
        )
        
        print(f"🔍 找到 {len(sorted_projects)} 个新项目候选")
        
        return sorted_projects[:max_projects]
    
    def _search_by_creation_date(self, days_back: int) -> List[Dict[str, Any]]:
        """按创建日期搜索新项目（最近半年活跃）"""
        end_date = datetime.datetime.now()
        # 搜索最近半年有活动的项目
        activity_date = end_date - datetime.timedelta(days=180)
        activity_filter = activity_date.strftime('%Y-%m-%d')
        
        crypto_keywords = [
            'cryptocurrency', 'blockchain', 'bitcoin', 'ethereum', 
            'defi', 'web3', 'crypto', 'dapp', 'smart-contract'
        ]
        
        projects = []
        for keyword in crypto_keywords[:3]:
            # 搜索最近半年活跃且stars>1000的项目
            projects.extend(self._search_github(f'{keyword} pushed:>{activity_filter} stars:>1000'))
        
        return projects
    
    def _search_by_recent_activity(self, days_back: int) -> List[Dict[str, Any]]:
        """按最近活动搜索项目（最近半年活跃）"""
        end_date = datetime.datetime.now()
        # 搜索最近半年有活动的项目
        activity_date = end_date - datetime.timedelta(days=180)
        activity_filter = activity_date.strftime('%Y-%m-%d')
        
        activity_keywords = ['trading', 'wallet', 'exchange', 'nft', 'dao']
        
        projects = []
        for keyword in activity_keywords[:2]:
            projects.extend(self._search_github(f'{keyword} pushed:>{activity_filter} stars:>1000'))
        
        return projects
    
    def _search_by_trending(self, days_back: int) -> List[Dict[str, Any]]:
        """搜索趋势项目（最近半年活跃）"""
        end_date = datetime.datetime.now()
        # 搜索最近半年有活动的项目
        activity_date = end_date - datetime.timedelta(days=180)
        activity_filter = activity_date.strftime('%Y-%m-%d')
        
        trending_keywords = ['mev', 'arbitrage', 'yield', 'staking', 'bridge']
        
        projects = []
        for keyword in trending_keywords[:2]:
            projects.extend(self._search_github(f'{keyword} pushed:>{activity_filter} stars:>1000'))
        
        return projects
    
    def _search_by_language_specific(self, days_back: int) -> List[Dict[str, Any]]:
        """按编程语言搜索（最近半年活跃）"""
        end_date = datetime.datetime.now()
        # 搜索最近半年有活动的项目
        activity_date = end_date - datetime.timedelta(days=180)
        activity_filter = activity_date.strftime('%Y-%m-%d')
        
        language_queries = [
            f'solidity cryptocurrency pushed:>{activity_filter} stars:>1000',
            f'rust blockchain pushed:>{activity_filter} stars:>1000',
            f'javascript web3 pushed:>{activity_filter} stars:>1000'
        ]
        
        projects = []
        for query in language_queries[:2]:
            projects.extend(self._search_github(query))
        
        return projects
    
    def _search_github(self, query: str, per_page: int = 10) -> List[Dict[str, Any]]:
        """执行GitHub搜索"""
        try:
            search_url = 'https://api.github.com/search/repositories'
            params = {
                'q': query,
                'sort': 'stars',
                'order': 'desc',
                'per_page': per_page
            }
            
            response = requests.get(search_url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('items', [])
            else:
                print(f"⚠️  搜索失败: {query}, 状态码: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ 搜索执行失败: {e}")
            return []
    
    def _is_quality_project(self, project: Dict[str, Any]) -> bool:
        """判断项目是否符合质量标准"""
        # 基本质量检查
        if project['stargazers_count'] < 1000:
            return False
        
        # 检查是否有描述
        if not project.get('description'):
            return False
        
        # 检查是否太老（超过2年）
        created_at = datetime.datetime.strptime(project['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        if (datetime.datetime.now() - created_at).days > 730:
            return False
        
        # 检查最近是否有更新（6个月内）
        updated_at = datetime.datetime.strptime(project['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
        if (datetime.datetime.now() - updated_at).days > 180:
            return False
        
        return True
    
    def _days_since_created(self, project: Dict[str, Any]) -> int:
        """计算项目创建天数"""
        created_at = datetime.datetime.strptime(project['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        return (datetime.datetime.now() - created_at).days
    
    def _days_since_updated(self, project: Dict[str, Any]) -> int:
        """计算项目最后更新天数"""
        updated_at = datetime.datetime.strptime(project['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
        return (datetime.datetime.now() - updated_at).days
    
    def get_project_details(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """获取项目详细信息"""
        
        repo_url = project['url']
        
        try:
            # 获取README内容
            readme_url = f"{repo_url}/readme"
            readme_response = requests.get(readme_url, headers=self.headers)
            readme_content = ""
            
            if readme_response.status_code == 200:
                readme_data = readme_response.json()
                if readme_data.get('encoding') == 'base64':
                    import base64
                    readme_content = base64.b64decode(readme_data['content']).decode('utf-8')
            
            # 获取最近的提交信息
            commits_url = f"{repo_url}/commits"
            commits_response = requests.get(f"{commits_url}?per_page=5", headers=self.headers)
            recent_commits = []
            
            if commits_response.status_code == 200:
                commits_data = commits_response.json()
                recent_commits = [
                    {
                        'message': commit['commit']['message'][:100],
                        'date': commit['commit']['author']['date'],
                        'author': commit['commit']['author']['name']
                    }
                    for commit in commits_data[:3]
                ]
            
            # 获取语言统计
            languages_url = f"{repo_url}/languages"
            languages_response = requests.get(languages_url, headers=self.headers)
            languages = {}
            
            if languages_response.status_code == 200:
                languages = languages_response.json()
            
            return {
                'basic_info': project,
                'readme_content': readme_content[:2000],  # 限制长度
                'recent_commits': recent_commits,
                'languages': languages,
                'topics': project.get('topics', [])
            }
            
        except Exception as e:
            print(f"获取项目详情失败: {e}")
            return {'basic_info': project}
    
    def analyze_project_category(self, project_details: Dict[str, Any]) -> str:
        """分析项目类别"""
        
        basic_info = project_details['basic_info']
        readme = project_details.get('readme_content', '').lower()
        topics = project_details.get('topics', [])
        description = basic_info.get('description', '').lower()
        
        # 关键词分类
        categories = {
            'DeFi协议': ['defi', 'decentralized finance', 'yield', 'liquidity', 'amm', 'dex', 'lending'],
            '区块链基础设施': ['blockchain', 'consensus', 'validator', 'node', 'network', 'protocol'],
            '交易工具': ['trading', 'exchange', 'arbitrage', 'bot', 'strategy'],
            '钱包应用': ['wallet', 'custody', 'keys', 'seed', 'mnemonic'],
            'NFT平台': ['nft', 'non-fungible', 'collectible', 'marketplace', 'art'],
            '开发工具': ['sdk', 'api', 'framework', 'library', 'development'],
            '数据分析': ['analytics', 'data', 'metrics', 'dashboard', 'monitoring']
        }
        
        text_to_analyze = f"{description} {readme} {' '.join(topics)}"
        
        for category, keywords in categories.items():
            if any(keyword in text_to_analyze for keyword in keywords):
                return category
        
        return '其他工具'
    
    def generate_review_content(self, project_details: Dict[str, Any]) -> str:
        """生成评测文章内容"""
        
        basic_info = project_details['basic_info']
        category = self.analyze_project_category(project_details)
        
        # 基本信息
        name = basic_info['name']
        description = basic_info.get('description', '暂无描述')
        stars = basic_info['stargazers_count']
        forks = basic_info['forks_count']
        language = basic_info.get('language', '未知')
        created_at = basic_info['created_at'][:10]
        updated_at = basic_info['updated_at'][:10]
        homepage = basic_info.get('homepage', '')
        github_url = basic_info['html_url']
        
        # 获取zread.ai解析信息
        zread_info = self.get_zread_info(github_url)
        
        # 获取AI分析结果
        ai_score = basic_info.get('ai_score')
        ai_analysis = basic_info.get('ai_analysis', '')
        ai_summary = ""
        ai_data_analysis = ""
        
        # 生成AI内容
        if self.ai_enabled:
            try:
                ai_summary = self.ai_generate_project_summary(project_details, ai_analysis)
                ai_data_analysis = self.ai_analyze_stars_and_forks(project_details)
            except Exception as e:
                print(f"⚠️  AI内容生成失败: {e}")
        
        # 生成快览信息
        alert_content = f"**项目快览**: {name}是一个{category}项目，GitHub上{stars:,}个⭐，主要使用{language}开发"
        if ai_score is not None:
            alert_content += f"，AI质量评分: {ai_score:.2f}/1.0"
        
        # 生成文章开头
        if ai_summary and ai_summary != "AI摘要生成未启用":
            opening_paragraph = ai_summary
        else:
            opening_paragraph = f"**{name}**是一个备受关注的{category}项目，在GitHub上已获得{stars:,}个星标，展现出强劲的社区关注度和发展潜力。该项目主要使用{language}开发，为加密货币生态系统提供创新解决方案。"
        
        # 生成文章内容
        content = f"""{{{{< alert >}}}}
{alert_content}
{{{{< /alert >}}}}

{opening_paragraph}

## 🎯 项目概览

### 基本信息
- **项目名称**: {name}
- **项目类型**: {category}
- **开发语言**: {language}
- **GitHub地址**: [{github_url}]({github_url}){f" | [zread.ai解析]({zread_info['url']})" if zread_info['url'] else ""}
- **GitHub Stars**: {stars:,}
- **Fork数量**: {forks:,}
- **创建时间**: {created_at}
- **最近更新**: {updated_at}
- **官方网站**: {homepage if homepage else '暂无'}

### 项目描述
{description}

{f"**智能解析**: {zread_info['description']}" if zread_info['description'] else ""}

## 🛠️ 技术特点

### 开发活跃度
该项目在GitHub上表现出良好的开发活跃度：
- ⭐ **社区关注**: {stars:,}个星标显示了强劲的社区支持
- 🔄 **代码贡献**: {forks:,}个Fork表明开发者积极参与
- 📅 **持续更新**: 最近更新于{updated_at}，保持活跃开发状态"""
        
        # 添加AI数据分析
        if ai_data_analysis and ai_data_analysis != "基于GitHub数据的标准分析":
            content += f"""

### 🤖 AI数据分析
{ai_data_analysis}"""
        
        content += """

### 技术栈分析"""

        # 添加语言统计
        if 'languages' in project_details and project_details['languages']:
            content += "\n\n**主要编程语言构成**:\n"
            total_bytes = sum(project_details['languages'].values())
            for lang, bytes_count in sorted(project_details['languages'].items(), key=lambda x: x[1], reverse=True)[:5]:
                percentage = (bytes_count / total_bytes) * 100
                content += f"- {lang}: {percentage:.1f}%\n"

        # 添加最近提交信息
        if 'recent_commits' in project_details and project_details['recent_commits']:
            content += "\n\n### 最近开发动态\n"
            for commit in project_details['recent_commits']:
                commit_date = commit['date'][:10]
                content += f"- **{commit_date}**: {commit['message']} (by {commit['author']})\n"

        # 添加项目标签
        if 'topics' in project_details and project_details['topics']:
            content += f"\n\n### 🏷️ 项目标签\n"
            topics_badges = []
            for topic in project_details['topics'][:10]:
                topics_badges.append(f"`{topic}`")
            content += f"该项目被标记为: {' '.join(topics_badges)}\n"

        # 添加评测分析
        content += f"""

## 📊 项目评测
"""
        
        # 添加AI质量分析部分
        if ai_score is not None and ai_analysis:
            quality_level = "优秀" if ai_score >= 0.8 else "良好" if ai_score >= 0.6 else "一般"
            content += f"""
### 🤖 AI智能评测
**综合质量评分**: {ai_score:.2f}/1.0 ({quality_level})

**AI分析报告**: {ai_analysis}

基于AI深度分析，该项目在技术创新性、代码质量、社区活跃度、项目完整性和市场潜力等多个维度获得了{ai_score:.2f}的综合评分。"""
        
        content += f"""

### 🎯 核心优势
1. **社区认可度高**: {stars:,}个GitHub星标证明了项目的受欢迎程度
2. **开发活跃**: 持续的代码更新显示项目处于积极开发状态
3. **技术创新**: 在{category}领域提供独特的解决方案
4. **开源透明**: 完全开源，代码可审计，增强用户信任

### ⚠️ 潜在考虑
1. **项目成熟度**: 作为相对较新的项目，需要时间验证稳定性
2. **生态建设**: 需要持续建设开发者和用户生态
3. **市场竞争**: 在{category}领域面临激烈竞争
4. **技术风险**: 新兴技术可能存在未知风险

### 💡 使用建议
- **开发者**: 适合关注{category}技术发展的开发者学习和贡献
- **投资者**: 建议深入研究项目技术和团队背景后谨慎评估
- **用户**: 可以关注项目发展，但建议等待更多实际应用案例

## 🔮 发展前景

基于当前的GitHub数据和社区反响，{name}展现出以下发展潜力：

1. **技术创新**: 在{category}领域的技术创新可能带来突破性进展
2. **社区增长**: 快速增长的星标数显示强劲的社区兴趣
3. **生态扩展**: 有潜力在加密货币生态系统中占据重要位置
4. **商业应用**: 技术成熟后可能产生实际的商业应用价值

## 📈 数据表现

| 指标 | 数值 | 说明 |
|------|------|------|
| GitHub Stars | {stars:,} | 社区关注度指标 |
| Fork数量 | {forks:,} | 开发者参与度 |
| 主要语言 | {language} | 技术栈核心 |
| 项目年龄 | {(datetime.datetime.now() - datetime.datetime.strptime(created_at, '%Y-%m-%d')).days}天 | 项目成熟度参考 |"""
        
        # 如果有AI评分，添加到表格中
        if ai_score is not None:
            content += f"""
| AI质量评分 | {ai_score:.2f}/1.0 | 综合技术质量评估 |"""
        
        content += """

---

*本评测基于GitHub公开数据分析生成，不构成投资建议。加密货币项目投资存在高风险，请谨慎决策并做好充分研究。*"""

        return content

    def get_zread_info(self, github_url: str) -> Dict[str, str]:
        """获取zread.ai的项目解析信息"""
        try:
            # 从GitHub URL提取owner/repo
            # 例如: https://github.com/moeru-ai/airi -> moeru-ai/airi
            if 'github.com/' in github_url:
                parts = github_url.split('github.com/')[-1].strip('/')
                if '/' in parts:
                    owner_repo = '/'.join(parts.split('/')[:2])  # 只取前两部分
                    zread_url = f"https://zread.ai/{owner_repo}"
                    
                    # 简单获取描述信息（这里可以扩展为实际的网页抓取）
                    # 为了保持简单，先返回构造的URL和占位符描述
                    return {
                        'url': zread_url,
                        'description': f"通过zread.ai查看{owner_repo}项目的智能解析"
                    }
        except Exception as e:
            print(f"⚠️ 生成zread.ai信息失败: {e}")
        
        return {'url': '', 'description': ''}

def main():
    """主函数"""
    
    # 从环境变量获取参数
    days_back = int(os.getenv('DAYS_BACK', '7'))
    max_projects = int(os.getenv('MAX_PROJECTS', '3'))
    
    print(f"🔍 搜索参数: 最近 {days_back} 天, 最多 {max_projects} 个项目")
    
    # 从环境变量获取GitHub token
    github_token = os.getenv('GITHUB_TOKEN')
    
    if github_token:
        # 在GitHub Actions环境中，不显示token内容
        if os.getenv('GITHUB_ACTIONS'):
            print("✅ 使用GitHub Actions内置Token")
        else:
            print(f"✅ 已获取GitHub Token: {github_token[:8]}...")
    else:
        print("⚠️  警告: 未设置GITHUB_TOKEN环境变量，API调用可能受限")
        if not os.getenv('GITHUB_ACTIONS'):
            print("💡 提示: 请在 .env.local 文件中设置 GITHUB_TOKEN=your_token")
    
    # 从环境变量获取OpenAI API key
    openai_api_key = config.OPENAI_API_KEY
    
    if openai_api_key:
        if not os.getenv('GITHUB_ACTIONS'):
            print(f"✅ 已获取OpenAI API Key: {openai_api_key[:8]}...")
    else:
        print("⚠️  警告: 未设置OPENAI_API_KEY环境变量，AI分析功能将被禁用")
        if not os.getenv('GITHUB_ACTIONS'):
            print("💡 提示: 请设置环境变量 OPENAI_API_KEY=your_openai_api_key")
    
    analyzer = CryptoProjectAnalyzer(github_token, openai_api_key)
    
    print("🔍 开始搜索热门加密货币项目...")
    
    # 加载已分析项目历史
    analyzed_projects = analyzer.load_analyzed_projects()
    
    try:
        projects = analyzer.search_crypto_projects(days_back=days_back, max_projects=max_projects)
    except Exception as e:
        print(f"❌ 搜索项目时出错: {e}")
        return
    
    if not projects:
        print("❌ 未找到符合条件的新项目")
        print("💡 提示: 所有最近的项目可能都已经分析过了")
        return
    
    print(f"✅ 找到 {len(projects)} 个新项目")
    
    # 生成今日日期用于文件名
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # 检查今日是否已生成文章（更宽松的检查）
    existing_articles = []
    content_posts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'content', 'posts')
    if os.path.exists(content_posts_dir):
        existing_articles = [f for f in os.listdir(content_posts_dir) if today in f and f.endswith('.md')]
    
    if len(existing_articles) >= 3:  # 每日最多3篇
        print(f"ℹ️  今日已存在 {len(existing_articles)} 篇文章，达到每日限制")
        return
    
    generated_count = 0
    newly_analyzed = set()
    
    for i, project in enumerate(projects, 1):
        try:
            print(f"\n📊 分析项目 {i}: {project['name']}")
            
            # 获取详细信息
            project_details = analyzer.get_project_details(project)
            
            # 生成评测内容
            review_content = analyzer.generate_review_content(project_details)
            
            # 生成文件名和标题（处理特殊字符）
            project_name = re.sub(r'[^\w\-]', '-', project['name'].lower())
            project_name = re.sub(r'-+', '-', project_name).strip('-')
            filename = f"github-crypto-{project_name}-review-{today}.md"
            
            # 确保文件名不重复
            counter = 1
            original_filename = filename
            while os.path.exists(os.path.join(content_posts_dir, filename)):
                name_part = original_filename.replace('.md', '')
                filename = f"{name_part}-{counter}.md"
                counter += 1
            
            title = f"GitHub热门项目评测：{project['name']} - {analyzer.analyze_project_category(project_details)}深度分析"
            
            # 处理描述中的特殊字符
            description = project.get('description', '')
            if description:
                # 先处理转义字符，避免在f-string中使用反斜杠
                description = description.replace("'", "''").replace('"', '""')[:150]
            else:
                description = f"{project['name']}项目深度评测分析"
            
            # 处理标题中的特殊字符
            safe_title = title.replace("'", "''")
            safe_project_name = project['name'].replace("'", "''")
            
            # 创建Hugo文章
            hugo_content = f"""+++
date = '{datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')}'
draft = false
title = '{safe_title}'
description = '{description}。GitHub {project['stargazers_count']:,} stars，{analyzer.analyze_project_category(project_details)}领域热门开源项目深度评测。'
summary = '{safe_project_name}是一个备受关注的{analyzer.analyze_project_category(project_details)}项目，在GitHub上已获得{project['stargazers_count']:,}个星标。'
tags = ['GitHub', '开源项目', '加密货币', '{analyzer.analyze_project_category(project_details)}', '{project.get('language', 'Unknown')}', '项目评测']
categories = ['GitHub热门']
keywords = ['{safe_project_name}评测', 'GitHub加密货币项目', '{analyzer.analyze_project_category(project_details)}工具', '开源区块链项目']
author = 'ERIC'
ShowToc = true
TocOpen = false
ShowReadingTime = true
ShowBreadCrumbs = true
ShowPostNavLinks = true
ShowWordCount = true
ShowShareButtons = true

[cover]
image = ""
alt = "{project['name']} - {analyzer.analyze_project_category(project_details)}项目评测"
caption = "GitHub热门加密货币项目深度分析"
relative = false
hidden = false
+++

{review_content}

---

## 📞 关于作者

**ERIC** - 《区块链核心技术与应用》作者之一，前火币机构事业部|矿池技术主管，比特财商|Nxt Venture Capital 创始人

### 🔗 联系方式与平台

- **📧 邮箱**: [gyc567@gmail.com](mailto:gyc567@gmail.com)
- **🐦 Twitter**: [@EricBlock2100](https://twitter.com/EricBlock2100)
- **💬 微信**: 360369487
- **📱 Telegram**: [https://t.me/fatoshi_block](https://t.me/fatoshi_block)
- **📢 Telegram频道**: [https://t.me/cryptochanneleric](https://t.me/cryptochanneleric)
- **👥 加密情报TG群**: [https://t.me/btcgogopen](https://t.me/btcgogopen)
- **🎥 YouTube频道**: [https://www.youtube.com/@0XBitFinance](https://www.youtube.com/@0XBitFinance)

### 🌐 相关平台

- **📊 加密货币信息聚合网站**: [https://www.smartwallex.com/](https://www.smartwallex.com/)
- **📖 公众号**: 比特财商

*欢迎关注我的各个平台，获取最新的加密货币市场分析和投资洞察！*
"""
            
            # 确保目录存在
            os.makedirs(content_posts_dir, exist_ok=True)
            
            # 保存文章文件
            output_path = os.path.join(content_posts_dir, filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(hugo_content)
            
            print(f"✅ 已生成文章: {output_path}")
            generated_count += 1
            
            # 记录已分析的项目
            project_key = analyzer.get_project_key(project)
            newly_analyzed.add(project_key)
            
            # 避免API限制
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ 处理项目 {project['name']} 时出错: {e}")
            continue
    
    # 更新项目历史记录
    if newly_analyzed:
        all_analyzed = analyzed_projects.union(newly_analyzed)
        analyzer.save_analyzed_projects(all_analyzed)
        print(f"📝 新增分析项目: {', '.join(newly_analyzed)}")
    
    if generated_count > 0:
        print(f"\n🎉 完成！共生成 {generated_count} 篇评测文章")
        print(f"📊 累计已分析项目: {len(analyzed_projects) + len(newly_analyzed)} 个")
        
        # 显示GLM API使用统计
        if analyzer.ai_enabled and analyzer.glm_logger:
            print("\n🤖 GLM-4.5 API使用统计:")
            stats = analyzer.glm_logger.get_daily_stats()
            if "error" not in stats:
                print(f"   ✅ 总调用次数: {stats['total_calls']}")
                print(f"   ✅ 成功调用: {stats['successful_calls']}")
                print(f"   ❌ 失败调用: {stats['failed_calls']}")
                print(f"   🔢 消耗Token总数: {stats['total_tokens']:,}")
                print(f"   📝 输入Token: {stats['prompt_tokens']:,}")
                print(f"   📤 输出Token: {stats['completion_tokens']:,}")
                
                # 显示各函数调用统计
                if stats['functions']:
                    print("   📊 各功能调用统计:")
                    for func_name, func_stats in stats['functions'].items():
                        print(f"      • {func_name}: {func_stats['calls']}次调用, {func_stats['tokens']}个tokens")
                
                # 显示错误（如果有）
                if stats['errors']:
                    print(f"   ⚠️  发生 {len(stats['errors'])} 个错误")
            else:
                print(f"   ❌ 无法获取统计信息: {stats.get('error', '未知错误')}")
    else:
        print(f"\n⚠️  未能生成任何文章")
        print(f"💡 建议: 尝试扩大搜索范围或等待新项目出现")

if __name__ == "__main__":
    main()