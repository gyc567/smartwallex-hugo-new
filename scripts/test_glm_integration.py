#!/usr/bin/env python3
"""
测试GLM日志集成
"""

import os
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

import config

# 使用importlib导入带连字符的模块
import importlib.util
spec = importlib.util.spec_from_file_location("crypto_project_analyzer", "crypto-project-analyzer.py")
crypto_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crypto_module)
CryptoProjectAnalyzer = crypto_module.CryptoProjectAnalyzer

def test_glm_integration():
    """测试GLM日志集成功能"""
    
    # 检查是否有GLM API Key
    glm_api_key = config.GLM_API_KEY
    if not glm_api_key:
        print("⚠️  警告: 未设置GLM_API_KEY，无法进行实际API测试")
        print("🧪 进行模拟测试...")
        
        # 创建分析器（无API密钥）
        analyzer = CryptoProjectAnalyzer(github_token=None, glm_api_key=None)
        
        if analyzer.ai_enabled:
            print("❌ 错误: AI应该被禁用")
        else:
            print("✅ AI正确禁用")
            
        if analyzer.glm_logger:
            print("❌ 错误: logger应该为None")
        else:
            print("✅ logger正确为None")
            
        return
    
    print("🧪 开始GLM集成测试...")
    
    # 创建分析器（有API密钥）
    analyzer = CryptoProjectAnalyzer(github_token=None, glm_api_key=glm_api_key)
    
    if not analyzer.ai_enabled:
        print("❌ 错误: AI应该被启用")
        return
        
    if not analyzer.glm_logger:
        print("❌ 错误: logger应该被创建")
        return
        
    print("✅ 分析器和日志记录器初始化成功")
    
    # 测试项目详情（模拟数据）
    mock_project_details = {
        'basic_info': {
            'name': 'test-crypto-project',
            'description': 'A test cryptocurrency project for blockchain development',
            'stargazers_count': 100,
            'forks_count': 20,
            'language': 'Python',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-08-20T12:00:00Z'
        },
        'readme_content': 'This is a test cryptocurrency project with blockchain features',
        'recent_commits': [
            {'message': 'Add new feature', 'date': '2024-08-20', 'author': 'test-author'}
        ],
        'languages': {'Python': 8000, 'JavaScript': 2000},
        'topics': ['blockchain', 'cryptocurrency', 'defi']
    }
    
    print("🔍 测试AI项目质量分析...")
    try:
        score, analysis = analyzer.ai_analyze_project_quality(mock_project_details)
        print(f"✅ AI分析成功: 评分 {score:.2f}, 分析: {analysis[:50]}...")
    except Exception as e:
        print(f"❌ AI分析失败: {e}")
        return
    
    print("📊 检查日志统计...")
    if analyzer.glm_logger:
        stats = analyzer.glm_logger.get_daily_stats()
        if "error" not in stats:
            print(f"✅ 日志统计: {stats['total_calls']}次调用, {stats['total_tokens']}个tokens")
        else:
            print(f"❌ 日志统计错误: {stats['error']}")
    
    print("🎉 集成测试完成!")

if __name__ == "__main__":
    test_glm_integration()