#!/usr/bin/env python3
"""
测试不同日期的文章生成
"""

import os
import sys
import datetime
import importlib.util

# 动态导入分析器模块
script_dir = os.path.dirname(__file__)
analyzer_path = os.path.join(script_dir, 'crypto-project-analyzer.py')

spec = importlib.util.spec_from_file_location("crypto_project_analyzer", analyzer_path)
crypto_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crypto_module)

def test_with_different_date():
    """测试使用不同日期生成文章"""
    
    # 临时修改日期为昨天，这样就不会被跳过
    original_datetime = datetime.datetime
    
    class MockDateTime(datetime.datetime):
        @classmethod
        def now(cls):
            # 返回昨天的日期
            return original_datetime.now() - datetime.timedelta(days=1)
    
    # 替换datetime模块中的datetime类
    crypto_module.datetime.datetime = MockDateTime
    
    print("🧪 测试使用不同日期生成文章...")
    
    try:
        # 运行主函数
        crypto_module.main()
        print("✅ 测试完成")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        # 恢复原始的datetime
        crypto_module.datetime.datetime = original_datetime

if __name__ == "__main__":
    test_with_different_date()