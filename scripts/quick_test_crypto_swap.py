#!/usr/bin/env python3
"""
加密货币合约分析器快速测试

提供基础功能验证，确保代码能正常运行
"""

import sys
import tempfile
import unittest.mock as mock
from pathlib import Path

# 添加scripts目录到Python路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))


def test_imports():
    """测试模块导入"""
    try:
        import crypto_swap_config
        import crypto_swap_analyzer
        print("✅ 模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False


def test_config():
    """测试配置验证"""
    try:
        from crypto_swap_config import validate_config, get_crypto_list
        
        # 测试配置验证
        if not validate_config():
            print("❌ 配置验证失败")
            return False
            
        # 测试加密货币列表
        cryptos = get_crypto_list()
        if len(cryptos) != 5:
            print(f"❌ 加密货币数量错误: {len(cryptos)}")
            return False
            
        expected = {'BTC', 'ETH', 'BNB', 'SOL', 'BCH'}
        if set(cryptos) != expected:
            print(f"❌ 加密货币列表不匹配: {set(cryptos)} != {expected}")
            return False
            
        print("✅ 配置测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False


def test_analyzer_basic():
    """测试分析器基础功能"""
    try:
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 创建专家提示词文件
            expert_file = temp_path / '加密货币合约专家.md'
            with open(expert_file, 'w', encoding='utf-8') as f:
                f.write("测试专家提示词HYPE")
            
            # Mock OpenAI 客户端和日志
            with mock.patch('crypto_swap_analyzer.create_openai_client') as mock_client, \
                 mock.patch('crypto_swap_analyzer.script_dir') as mock_script_dir, \
                 mock.patch('logging.FileHandler'):
                
                mock_script_dir.parent = temp_path
                mock_client.return_value = mock.Mock()
                
                # 导入并测试
                from crypto_swap_analyzer import CryptoSwapAnalyzer
                
                analyzer = CryptoSwapAnalyzer()
                
                # 基本属性检查
                if not hasattr(analyzer, 'logger'):
                    print("❌ 分析器缺少logger属性")
                    return False
                    
                if not hasattr(analyzer, 'openai_client'):
                    print("❌ 分析器缺少openai_client属性")
                    return False
                    
                if not hasattr(analyzer, 'expert_prompt'):
                    print("❌ 分析器缺少expert_prompt属性")
                    return False
                    
                print("✅ 分析器基础功能测试通过")
                return True
                
    except Exception as e:
        print(f"❌ 分析器测试失败: {e}")
        return False


def test_combine_analyses():
    """测试分析合并功能"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 创建专家提示词文件
            expert_file = temp_path / '加密货币合约专家.md'
            with open(expert_file, 'w', encoding='utf-8') as f:
                f.write("测试专家提示词")
            
            with mock.patch('crypto_swap_analyzer.create_openai_client') as mock_client, \
                 mock.patch('crypto_swap_analyzer.script_dir') as mock_script_dir, \
                 mock.patch('logging.FileHandler'):
                
                mock_script_dir.parent = temp_path
                mock_client.return_value = mock.Mock()
                
                from crypto_swap_analyzer import CryptoSwapAnalyzer
                
                analyzer = CryptoSwapAnalyzer()
                
                # 测试合并功能
                test_analyses = {
                    'BTC': 'BTC合约分析内容',
                    'ETH': 'ETH合约分析内容'
                }
                
                result = analyzer.combine_analyses(test_analyses, '2025-09-23')
                
                # 检查结果
                if 'BTC合约分析内容' not in result:
                    print("❌ 合并结果缺少BTC内容")
                    return False
                    
                if 'ETH合约分析内容' not in result:
                    print("❌ 合并结果缺少ETH内容")
                    return False
                    
                if '加密货币永续合约交易信号日报' not in result:
                    print("❌ 合并结果缺少标题")
                    return False
                    
                if '风险提示' not in result:
                    print("❌ 合并结果缺少风险提示")
                    return False
                    
                print("✅ 分析合并功能测试通过")
                return True
                
    except Exception as e:
        print(f"❌ 分析合并测试失败: {e}")
        return False


def run_quick_tests():
    """运行快速测试套件"""
    print("🚀 开始快速测试...")
    print("="*50)
    
    tests = [
        ("模块导入", test_imports),
        ("配置验证", test_config),
        ("分析器基础", test_analyzer_basic),
        ("分析合并", test_combine_analyses)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n🧪 {name}:")
        if test_func():
            passed += 1
        else:
            break  # 如果有测试失败，停止后续测试
    
    print("\n" + "="*50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有快速测试通过！")
        return True
    else:
        print("⚠️ 部分测试失败")
        return False


if __name__ == "__main__":
    success = run_quick_tests()
    sys.exit(0 if success else 1)