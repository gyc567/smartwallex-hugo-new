#!/usr/bin/env python3
"""
AI功能测试脚本
用于验证GLM-4.5集成是否正常工作
"""

import os
import sys
from openai import OpenAI
import config

def test_ai_connection():
    """测试AI连接"""
    print("🧪 测试GLM-4.5 AI连接...")
    
    # 检查API密钥
    api_key = config.GLM_API_KEY
    if not api_key:
        print("❌ GLM_API_KEY未设置")
        print("💡 请设置环境变量: GLM_API_KEY=your_api_key")
        return False
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=config.GLM_API_BASE
        )
        
        # 测试简单调用
        completion = client.chat.completions.create(
            model=config.GLM_MODEL,
            messages=[
                {"role": "system", "content": "你是一个测试助手。"},
                {"role": "user", "content": "请回复：AI连接测试成功"}
            ],
            temperature=0.1,
            max_tokens=100
        )
        
        response = completion.choices[0].message.content.strip()
        print(f"✅ AI连接成功")
        print(f"📝 AI响应: {response}")
        return True
        
    except Exception as e:
        print(f"❌ AI连接失败: {e}")
        return False

def test_project_analysis():
    """测试项目分析功能"""
    print("\n🧪 测试项目分析功能...")
    
    # 模拟项目数据
    mock_project = {
        'basic_info': {
            'name': 'test-crypto-project',
            'description': 'A test cryptocurrency project for DeFi applications',
            'stargazers_count': 1500,
            'forks_count': 300,
            'language': 'Solidity',
            'created_at': '2023-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z',
            'html_url': 'https://github.com/test/test-crypto-project'
        },
        'readme_content': 'This is a DeFi protocol for decentralized lending and borrowing.',
        'recent_commits': [
            {'message': 'Add liquidity pool', 'date': '2024-01-01', 'author': 'developer'}
        ],
        'languages': {'Solidity': 80000, 'JavaScript': 20000},
        'topics': ['defi', 'ethereum', 'smart-contracts']
    }
    
    try:
        # 导入分析器
        from crypto_project_analyzer import CryptoProjectAnalyzer
        
        # 创建分析器实例
        analyzer = CryptoProjectAnalyzer(glm_api_key=config.GLM_API_KEY)
        
        if not analyzer.ai_enabled:
            print("❌ AI功能未启用")
            return False
        
        # 测试AI质量分析
        print("🔍 测试AI质量分析...")
        score, analysis = analyzer.ai_analyze_project_quality(mock_project)
        print(f"📊 AI评分: {score:.2f}")
        print(f"📝 AI分析: {analysis[:100]}...")
        
        # 测试AI摘要生成
        print("📄 测试AI摘要生成...")
        summary = analyzer.ai_generate_project_summary(mock_project, analysis)
        print(f"📝 AI摘要: {summary[:100]}...")
        
        # 测试数据分析
        print("📈 测试数据分析...")
        data_analysis = analyzer.ai_analyze_stars_and_forks(mock_project)
        print(f"📝 数据分析: {data_analysis[:100]}...")
        
        print("✅ 项目分析功能测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 项目分析测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始AI功能测试")
    print("=" * 50)
    
    # 测试AI连接
    connection_ok = test_ai_connection()
    
    if connection_ok:
        # 测试项目分析
        analysis_ok = test_project_analysis()
        
        print("\n" + "=" * 50)
        if analysis_ok:
            print("🎉 所有测试通过！AI功能正常工作")
        else:
            print("⚠️  部分测试失败，请检查配置")
    else:
        print("\n⚠️  AI连接失败，无法进行进一步测试")
        print("💡 请检查GLM_API_KEY设置")

if __name__ == "__main__":
    main()