#!/usr/bin/env python3
"""
重构验证测试 - 确保重构后的功能正常
测试实际的API调用路径和响应处理
"""

import sys
import os
from unittest.mock import Mock, patch

# 添加脚本目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

def test_crypto_analyzer_integration():
    """测试crypto-project-analyzer集成"""
    try:
        # 模拟环境变量
        with patch.dict(os.environ, {'GLM_API_KEY': 'test-key'}):
            # 导入时使用连字符替换为下划线
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "crypto_project_analyzer", 
                "crypto-project-analyzer.py"
            )
            if spec and spec.loader:
                crypto_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(crypto_module)
                CryptoProjectAnalyzer = crypto_module.CryptoProjectAnalyzer
            
            # 创建分析器实例
            analyzer = CryptoProjectAnalyzer(glm_api_key='test-key')
            
            print("✅ CryptoProjectAnalyzer 初始化成功")
            print(f"   - AI启用状态: {analyzer.ai_enabled}")
            print(f"   - 客户端类型: {type(analyzer.ai_client)}")
            
            return True
            
    except Exception as e:
        print(f"❌ CryptoProjectAnalyzer 集成测试失败: {e}")
        return False


def test_translator_integration():
    """测试翻译器集成"""
    try:
        # 模拟环境变量
        with patch.dict(os.environ, {'GLM_API_KEY': 'test-key'}):
            # 添加lookonchain模块路径
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lookonchain'))
            from lookonchain.translator import ChineseTranslator
            
            # 创建翻译器实例
            translator = ChineseTranslator(glm_api_key='test-key')
            
            print("✅ ChineseTranslator 初始化成功")
            print(f"   - 客户端存在: {translator.client is not None}")
            print(f"   - 客户端类型: {type(translator.client)}")
            
            return True
            
    except Exception as e:
        print(f"❌ ChineseTranslator 集成测试失败: {e}")
        return False


def test_config_compatibility():
    """测试配置兼容性"""
    try:
        import config
        
        # 检查必要的配置项存在
        required_configs = [
            'GLM_API_KEY', 'GLM_API_BASE', 'GLM_MODEL',
            'OPENAI_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_MODEL'
        ]
        
        for config_name in required_configs:
            if not hasattr(config, config_name):
                print(f"❌ 配置项 {config_name} 不存在")
                return False
        
        # 检查向后兼容别名
        if config.OPENAI_API_KEY != config.GLM_API_KEY:
            print("❌ OPENAI_API_KEY 别名不正确")
            return False
            
        if config.OPENAI_BASE_URL != config.GLM_API_BASE:
            print("❌ OPENAI_BASE_URL 别名不正确")
            return False
            
        if config.OPENAI_MODEL != config.GLM_MODEL:
            print("❌ OPENAI_MODEL 别名不正确")
            return False
        
        print("✅ 配置兼容性测试通过")
        print(f"   - 默认API基础URL: {config.GLM_API_BASE}")
        print(f"   - 默认模型: {config.GLM_MODEL}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置兼容性测试失败: {e}")
        return False


def test_openai_client_basic_functionality():
    """测试OpenAI客户端基础功能"""
    try:
        from openai_client import create_openai_client, extract_content_from_response
        
        # 模拟环境变量
        with patch.dict(os.environ, {'GLM_API_KEY': 'test-key'}):
            client = create_openai_client()
            
        if not client:
            print("❌ 客户端创建失败")
            return False
            
        print("✅ OpenAI客户端基础功能测试通过")
        print(f"   - 客户端类型: {type(client)}")
        print(f"   - API密钥: {client.api_key[:8]}...")
        print(f"   - 基础URL: {client.base_url}")
        print(f"   - 模型: {client.model}")
        
        # 测试响应提取函数
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "测试内容"
        
        content = extract_content_from_response(mock_response, "功能测试")
        if content != "测试内容":
            print(f"❌ 响应提取失败: {content}")
            return False
            
        print("✅ 响应提取功能正常")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI客户端基础功能测试失败: {e}")
        return False


def test_backward_compatibility():
    """测试向后兼容性"""
    try:
        from openai_client import GLMClientWrapper, OpenAIClientWrapper
        
        # 检查别名是否正确
        if GLMClientWrapper is not OpenAIClientWrapper:
            print("❌ GLMClientWrapper 别名不正确")
            return False
            
        print("✅ 向后兼容性测试通过")
        print("   - GLMClientWrapper 别名正确")
        
        return True
        
    except Exception as e:
        print(f"❌ 向后兼容性测试失败: {e}")
        return False


def main():
    """运行所有验证测试"""
    print("🚀 开始验证重构后功能...\n")
    
    test_results = []
    
    # 运行各项测试
    test_functions = [
        ("配置兼容性", test_config_compatibility),
        ("OpenAI客户端基础功能", test_openai_client_basic_functionality),
        ("向后兼容性", test_backward_compatibility),
        ("翻译器集成", test_translator_integration),
        ("加密项目分析器集成", test_crypto_analyzer_integration),
    ]
    
    for test_name, test_func in test_functions:
        print(f"\n📋 {test_name}测试:")
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            test_results.append((test_name, False))
    
    # 输出测试总结
    print("\n" + "="*50)
    print("📊 重构验证测试总结")
    print("="*50)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    total = passed + failed
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    print(f"\n总结: {passed}/{total} 通过 ({success_rate:.1f}%)")
    
    if failed == 0:
        print("\n🎉 所有重构验证测试通过！")
        print("重构成功完成，功能正常。")
        return True
    else:
        print(f"\n⚠️  {failed} 个测试失败，需要进一步检查。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)