#!/usr/bin/env python3
"""
测试脚本 - 验证分析器功能
"""

import os
import sys
import importlib.util

# 动态导入分析器模块
script_dir = os.path.dirname(__file__)
analyzer_path = os.path.join(script_dir, 'crypto-project-analyzer.py')

spec = importlib.util.spec_from_file_location("crypto_project_analyzer", analyzer_path)
crypto_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crypto_module)

CryptoProjectAnalyzer = crypto_module.CryptoProjectAnalyzer

def test_analyzer():
    """测试分析器基本功能"""
    
    print("🧪 开始测试加密货币项目分析器...")
    
    # 创建分析器实例
    github_token = os.getenv('GITHUB_TOKEN')
    analyzer = CryptoProjectAnalyzer(github_token)
    
    # 测试搜索功能
    print("\n1️⃣ 测试项目搜索...")
    try:
        projects = analyzer.search_crypto_projects(days_back=30)  # 扩大搜索范围
        if projects:
            print(f"✅ 找到 {len(projects)} 个项目")
            for i, project in enumerate(projects[:3], 1):
                print(f"   {i}. {project['name']} - {project['stargazers_count']} stars")
        else:
            print("⚠️  未找到项目")
            return False
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        return False
    
    # 测试项目详情获取
    print("\n2️⃣ 测试项目详情获取...")
    try:
        test_project = projects[0]
        details = analyzer.get_project_details(test_project)
        print(f"✅ 获取项目详情: {test_project['name']}")
        print(f"   - README长度: {len(details.get('readme_content', ''))}")
        print(f"   - 最近提交: {len(details.get('recent_commits', []))}")
        print(f"   - 编程语言: {len(details.get('languages', {}))}")
    except Exception as e:
        print(f"❌ 获取详情失败: {e}")
        return False
    
    # 测试项目分类
    print("\n3️⃣ 测试项目分类...")
    try:
        category = analyzer.analyze_project_category(details)
        print(f"✅ 项目分类: {category}")
    except Exception as e:
        print(f"❌ 分类失败: {e}")
        return False
    
    # 测试内容生成
    print("\n4️⃣ 测试内容生成...")
    try:
        content = analyzer.generate_review_content(details)
        print(f"✅ 生成内容长度: {len(content)} 字符")
        print(f"   - 包含项目名: {'✅' if test_project['name'] in content else '❌'}")
        print(f"   - 包含星标数: {'✅' if str(test_project['stargazers_count']) in content else '❌'}")
    except Exception as e:
        print(f"❌ 内容生成失败: {e}")
        return False
    
    print("\n🎉 所有测试通过！")
    return True

if __name__ == "__main__":
    success = test_analyzer()
    sys.exit(0 if success else 1)