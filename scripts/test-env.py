#!/usr/bin/env python3
"""
测试环境变量配置
"""

import os
import sys

def test_environment():
    """测试环境变量和配置"""
    
    print("🧪 测试环境变量配置...")
    
    # 测试Python版本
    print(f"\n📍 Python版本: {sys.version}")
    
    # 测试必要的模块
    print("\n📦 测试依赖模块:")
    try:
        import requests
        print(f"✅ requests: {requests.__version__}")
    except ImportError:
        print("❌ requests 未安装")
        return False
    
    try:
        import dateutil
        print(f"✅ python-dateutil: {dateutil.__version__}")
    except ImportError:
        print("❌ python-dateutil 未安装")
        return False
    
    # 测试GitHub Token
    print("\n🔑 测试GitHub Token:")
    github_token = os.getenv('GITHUB_TOKEN')
    if github_token:
        print(f"✅ GITHUB_TOKEN 已设置: {github_token[:8]}...")
    else:
        print("⚠️  GITHUB_TOKEN 未设置 (可选)")
    
    # 测试GitHub Actions环境
    print("\n🤖 测试GitHub Actions环境:")
    if os.getenv('GITHUB_ACTIONS'):
        print("✅ 运行在GitHub Actions环境")
    else:
        print("ℹ️  运行在本地环境")
    
    # 测试文件权限
    print("\n📁 测试文件权限:")
    try:
        # 测试content/posts目录
        os.makedirs('content/posts', exist_ok=True)
        test_file = 'content/posts/test-write.tmp'
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("✅ content/posts 目录可写")
    except Exception as e:
        print(f"❌ content/posts 目录写入失败: {e}")
        return False
    
    # 测试网络连接
    print("\n🌐 测试网络连接:")
    try:
        import requests
        response = requests.get('https://api.github.com/rate_limit', timeout=10)
        if response.status_code == 200:
            print("✅ GitHub API 连接正常")
            rate_limit = response.json()
            print(f"   - API限制: {rate_limit['rate']['remaining']}/{rate_limit['rate']['limit']}")
        else:
            print(f"⚠️  GitHub API 响应异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 网络连接失败: {e}")
        return False
    
    print("\n🎉 环境测试完成！")
    return True

if __name__ == "__main__":
    success = test_environment()
    sys.exit(0 if success else 1)