#!/usr/bin/env python3
"""
语法检查脚本
"""

import py_compile
import sys
import os

def check_python_files():
    """检查Python文件语法"""
    
    python_files = [
        'scripts/crypto-project-analyzer.py',
        'scripts/manage-history.py',
        'scripts/test-analyzer.py',
        'scripts/test-different-date.py',
        'scripts/test-env.py'
    ]
    
    print("🔍 检查Python文件语法...")
    
    all_passed = True
    
    for file_path in python_files:
        if os.path.exists(file_path):
            try:
                py_compile.compile(file_path, doraise=True)
                print(f"✅ {file_path}")
            except py_compile.PyCompileError as e:
                print(f"❌ {file_path}: {e}")
                all_passed = False
        else:
            print(f"⚠️  {file_path}: 文件不存在")
    
    return all_passed

def check_imports():
    """检查导入是否正常"""
    
    print("\n🔍 检查模块导入...")
    
    try:
        import requests
        print("✅ requests")
    except ImportError as e:
        print(f"❌ requests: {e}")
        return False
    
    try:
        from dateutil import parser
        print("✅ python-dateutil")
    except ImportError as e:
        print(f"❌ python-dateutil: {e}")
        return False
    
    return True

def main():
    """主函数"""
    
    print("🧪 开始语法和依赖检查...")
    
    syntax_ok = check_python_files()
    imports_ok = check_imports()
    
    if syntax_ok and imports_ok:
        print("\n🎉 所有检查通过！")
        return True
    else:
        print("\n❌ 检查失败，请修复错误")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)