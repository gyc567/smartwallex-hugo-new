#!/usr/bin/env python3
"""
验证GitHub Secrets配置的工具
"""

import os
import sys

def verify_secrets():
    """验证GitHub Secrets配置"""
    print("🔍 GitHub Secrets配置验证工具")
    print("=" * 50)
    
    # 检查环境变量
    secrets = {
        'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', ''),
        'TELEGRAM_CHANNEL_ID': os.getenv('TELEGRAM_CHANNEL_ID', ''),
        'TELEGRAM_TEST_CHANNEL_ID': os.getenv('TELEGRAM_TEST_CHANNEL_ID', '')
    }
    
    all_configured = True
    
    for secret_name, secret_value in secrets.items():
        if secret_value:
            print(f"✅ {secret_name}: 已配置")
            if secret_name == 'TELEGRAM_BOT_TOKEN':
                print(f"   Token预览: {secret_value[:10]}...")
            else:
                print(f"   频道ID: {secret_value}")
        else:
            print(f"❌ {secret_name}: 未配置")
            all_configured = False
    
    print("\n" + "=" * 50)
    
    if all_configured:
        print("🎉 所有Secrets已正确配置！")
        print("\n下一步:")
        print("1. 手动触发GitHub Actions工作流进行测试")
        print("2. 或等待明日的定时任务自动运行")
        return True
    else:
        print("⚠️  部分Secrets未配置")
        print("\n配置步骤:")
        print("1. 前往GitHub仓库: Settings → Secrets and variables → Actions")
        print("2. 点击 'New repository secret'")
        print("3. 添加缺失的Secrets:")
        for secret_name, secret_value in secrets.items():
            if not secret_value:
                print(f"   - {secret_name}")
        print("4. 重新运行工作流测试")
        return False

if __name__ == "__main__":
    # 模拟GitHub Actions环境
    if len(sys.argv) > 1 and sys.argv[1] == '--github-actions':
        # 在实际GitHub Actions中运行
        success = verify_secrets()
        sys.exit(0 if success else 1)
    else:
        # 本地测试模式
        print("💡 本地测试模式")
        print("在GitHub Actions中，Secrets会自动注入为环境变量")
        print("运行: python verify_github_secrets.py --github-actions")
        
        # 模拟环境变量进行测试
        os.environ['TELEGRAM_BOT_TOKEN'] = '8209835379:AAEarEFcbfR8fDJMFw16A0h1MqWHliFTnYE'
        os.environ['TELEGRAM_CHANNEL_ID'] = '-1003168613592'
        os.environ['TELEGRAM_TEST_CHANNEL_ID'] = '-1003168613592'
        
        verify_secrets()