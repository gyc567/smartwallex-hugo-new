#!/usr/bin/env python3
"""
ChineseTranslator 类测试套件
测试翻译器的各种功能，包括正常情况、异常情况和边界情况
"""

import sys
import os
import json
import time
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock

# 添加 lookonchain 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lookonchain'))

# 修复相对导入问题 - 临时修改 translator.py 的导入
import importlib.util

def load_translator_module():
    """动态加载 translator 模块并修复导入问题"""
    translator_path = os.path.join(os.path.dirname(__file__), 'lookonchain', 'translator.py')
    config_path = os.path.join(os.path.dirname(__file__), 'lookonchain', 'config.py')
    
    # 先加载 config 模块
    config_spec = importlib.util.spec_from_file_location("config", config_path)
    config_module = importlib.util.module_from_spec(config_spec)
    sys.modules['config'] = config_module
    config_spec.loader.exec_module(config_module)
    
    # 读取 translator.py 内容并修复导入
    with open(translator_path, 'r', encoding='utf-8') as f:
        translator_code = f.read()
    
    # 修复相对导入
    translator_code = translator_code.replace(
        'from .config import (',
        'from config import ('
    )
    
    # 创建临时模块
    translator_spec = importlib.util.spec_from_loader("translator", loader=None)
    translator_module = importlib.util.module_from_spec(translator_spec)
    sys.modules['translator'] = translator_module
    
    # 设置模块环境
    translator_module.__file__ = translator_path
    translator_module.__dict__['__file__'] = translator_path
    
    # 执行修复后的代码
    exec(translator_code, translator_module.__dict__)
    
    return translator_module

# 加载修复后的模块
translator_module = load_translator_module()

# 模拟响应对象，用于测试
class MockResponse:
    def __init__(self, content: str = None, has_choices: bool = True, has_usage: bool = True):
        self.content = content
        self.text = content
        
        if has_choices and content:
            mock_message = Mock()
            mock_message.content = content
            mock_choice = Mock()
            mock_choice.message = mock_message
            self.choices = [mock_choice]
        elif has_choices:
            # 模拟空响应
            mock_message = Mock()
            mock_message.content = ""
            mock_choice = Mock()
            mock_choice.message = mock_message
            self.choices = [mock_choice]
        else:
            self.choices = []
        
        if has_usage:
            mock_usage = Mock()
            mock_usage.total_tokens = 100
            mock_usage.prompt_tokens = 50
            mock_usage.completion_tokens = 50
            self.usage = mock_usage


class TranslatorTester:
    """翻译器测试类"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = time.time()
        
    def log_test(self, test_name: str, passed: bool, message: str = "", error: str = ""):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "message": message,
            "error": error,
            "timestamp": time.time() - self.start_time
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if error:
            print(f"      错误详情: {error}")
    
    def test_extract_content_from_response(self):
        """测试响应内容提取函数"""
        extract_content_from_response = translator_module.extract_content_from_response
        
        print("\n🔍 测试 extract_content_from_response 函数")
        print("-" * 50)
        
        # 测试1: 标准OpenAI格式
        try:
            mock_response = MockResponse("测试内容", has_choices=True)
            result = extract_content_from_response(mock_response, "测试1")
            expected = "测试内容"
            self.log_test("标准OpenAI格式", result == expected, f"期望: {expected}, 实际: {result}")
        except Exception as e:
            self.log_test("标准OpenAI格式", False, "", str(e))
        
        # 测试2: 空响应处理
        try:
            result = extract_content_from_response(None, "测试2")
            self.log_test("空响应处理", result is None, "正确返回None")
        except Exception as e:
            self.log_test("空响应处理", False, "", str(e))
        
        # 测试3: 空内容处理
        try:
            mock_response = MockResponse("", has_choices=True)
            result = extract_content_from_response(mock_response, "测试3")
            self.log_test("空内容处理", result is None, "正确处理空内容")
        except Exception as e:
            self.log_test("空内容处理", False, "", str(e))
        
        # 测试4: 字典格式
        try:
            dict_response = {"content": "字典格式内容"}
            result = extract_content_from_response(dict_response, "测试4")
            expected = "字典格式内容"
            self.log_test("字典格式", result == expected, f"期望: {expected}, 实际: {result}")
        except Exception as e:
            self.log_test("字典格式", False, "", str(e))
        
        # 测试5: 多种字典键
        try:
            for key in ['content', 'text', 'output', 'result']:
                dict_response = {key: f"{key}内容"}
                result = extract_content_from_response(dict_response, f"测试5-{key}")
                expected = f"{key}内容"
                self.log_test(f"字典键-{key}", result == expected, f"期望: {expected}, 实际: {result}")
        except Exception as e:
            self.log_test("多种字典键", False, "", str(e))
    
    def test_translator_initialization(self):
        """测试翻译器初始化"""
        ChineseTranslator = translator_module.ChineseTranslator
        
        print("\n🔧 测试 ChineseTranslator 初始化")
        print("-" * 50)
        
        # 测试1: 无API密钥初始化
        try:
            with patch.dict(os.environ, {}, clear=True):
                # 清除环境变量
                translator = ChineseTranslator(glm_api_key=None)
                self.log_test("无API密钥初始化", 
                             translator.client is None, 
                             "正确处理缺失API密钥")
        except Exception as e:
            self.log_test("无API密钥初始化", False, "", str(e))
        
        # 测试2: 有API密钥初始化（模拟）
        try:
            fake_api_key = "fake-api-key-for-testing"
            with patch.object(translator_module, 'GLMClientWrapper') as mock_wrapper:
                mock_wrapper.return_value = Mock()
                translator = ChineseTranslator(glm_api_key=fake_api_key)
                self.log_test("有API密钥初始化", 
                             translator.client is not None, 
                             "成功创建客户端")
        except Exception as e:
            self.log_test("有API密钥初始化", False, "", str(e))
    
    def test_translate_title_fallback(self):
        """测试标题翻译的fallback机制"""
        ChineseTranslator = translator_module.ChineseTranslator
        
        print("\n🏷️ 测试标题翻译fallback机制")
        print("-" * 50)
        
        # 创建无API密钥的翻译器
        translator = ChineseTranslator(glm_api_key=None)
        
        # 测试1: 空标题处理
        try:
            result = translator.translate_title("")
            expected = "LookOnChain 链上数据分析"
            self.log_test("空标题处理", result == expected, f"期望: {expected}, 实际: {result}")
        except Exception as e:
            self.log_test("空标题处理", False, "", str(e))
        
        # 测试2: None标题处理
        try:
            result = translator.translate_title(None)
            expected = "LookOnChain 链上数据分析"
            self.log_test("None标题处理", result == expected, f"期望: {expected}, 实际: {result}")
        except Exception as e:
            self.log_test("None标题处理", False, "", str(e))
        
        # 测试3: 无客户端时使用原标题
        try:
            test_title = "Bitcoin Price Analysis"
            result = translator.translate_title(test_title)
            self.log_test("无客户端fallback", result == test_title, f"期望: {test_title}, 实际: {result}")
        except Exception as e:
            self.log_test("无客户端fallback", False, "", str(e))
    
    def test_translate_title_with_mock_api(self):
        """使用模拟API测试标题翻译"""
        ChineseTranslator = translator_module.ChineseTranslator
        
        print("\n🔄 测试标题翻译API调用")
        print("-" * 50)
        
        # 创建有API密钥的翻译器（模拟）
        fake_api_key = "fake-api-key"
        
        # 测试1: 成功翻译
        try:
            with patch.object(translator_module, 'GLMClientWrapper') as mock_wrapper:
                mock_client = Mock()
                mock_response = MockResponse("比特币价格分析")
                mock_client.chat_completions_create.return_value = mock_response
                mock_wrapper.return_value = mock_client
                
                translator = ChineseTranslator(glm_api_key=fake_api_key)
                result = translator.translate_title("Bitcoin Price Analysis")
                
                self.log_test("成功翻译标题", result == "比特币价格分析", f"翻译结果: {result}")
        except Exception as e:
            self.log_test("成功翻译标题", False, "", str(e))
        
        # 测试2: API返回空内容时的重试机制
        try:
            with patch.object(translator_module, 'GLMClientWrapper') as mock_wrapper:
                mock_client = Mock()
                # 第一次返回空，第二次返回内容
                mock_responses = [MockResponse("", has_choices=True), MockResponse("重试成功的标题")]
                mock_client.chat_completions_create.side_effect = mock_responses
                mock_wrapper.return_value = mock_client
                
                translator = ChineseTranslator(glm_api_key=fake_api_key)
                result = translator.translate_title("Test Title", max_retries=1)
                
                self.log_test("重试机制", result == "重试成功的标题", f"重试结果: {result}")
        except Exception as e:
            self.log_test("重试机制", False, "", str(e))
        
        # 测试3: 所有重试都失败，使用原标题
        try:
            with patch.object(translator_module, 'GLMClientWrapper') as mock_wrapper:
                mock_client = Mock()
                # 所有尝试都返回空内容
                mock_client.chat_completions_create.return_value = MockResponse("", has_choices=True)
                mock_wrapper.return_value = mock_client
                
                translator = ChineseTranslator(glm_api_key=fake_api_key)
                original_title = "Fallback Test Title"
                result = translator.translate_title(original_title, max_retries=1)
                
                self.log_test("重试失败fallback", result == original_title, f"使用原标题: {result}")
        except Exception as e:
            self.log_test("重试失败fallback", False, "", str(e))
    
    def test_process_article_resilience(self):
        """测试文章处理的容错性"""
        ChineseTranslator = translator_module.ChineseTranslator
        
        print("\n📄 测试文章处理容错性")
        print("-" * 50)
        
        # 创建无API密钥的翻译器（全部使用fallback）
        translator = ChineseTranslator(glm_api_key=None)
        
        # 测试数据
        test_article = {
            "title": "DeFi Protocol Security Analysis",
            "content": "This article analyzes the security aspects of DeFi protocols...",
            "summary": "Security analysis of major DeFi protocols",
            "url": "https://example.com/article",
            "id": "test-123"
        }
        
        # 测试1: 完全fallback处理
        try:
            result = translator.process_article(test_article)
            
            # 验证结果结构
            required_keys = ['original_title', 'chinese_title', 'original_content', 
                           'chinese_content', 'summary', 'processing_stats']
            has_all_keys = all(key in result for key in required_keys)
            
            self.log_test("完全fallback处理", 
                         result is not None and has_all_keys,
                         f"成功生成文章，标题: {result['chinese_title'] if result else 'None'}")
            
            if result:
                # 检查processing_stats
                stats = result['processing_stats']
                total_failed = sum(stats.values()) == 0  # 所有步骤都应该失败（使用fallback）
                self.log_test("处理统计正确", total_failed, f"统计: {stats}")
        except Exception as e:
            self.log_test("完全fallback处理", False, "", str(e))
        
        # 测试2: 空文章数据处理
        try:
            empty_article = {}
            result = translator.process_article(empty_article)
            
            self.log_test("空文章数据处理", 
                         result is not None,
                         "正确处理空数据")
        except Exception as e:
            self.log_test("空文章数据处理", False, "", str(e))
        
        # 测试3: 部分数据缺失
        try:
            partial_article = {"title": "Test Title Only"}
            result = translator.process_article(partial_article)
            
            self.log_test("部分数据处理", 
                         result is not None and result['chinese_title'] == "Test Title Only",
                         f"成功处理部分数据，标题: {result['chinese_title'] if result else 'None'}")
        except Exception as e:
            self.log_test("部分数据处理", False, "", str(e))
    
    def test_api_usage_stats(self):
        """测试API使用统计"""
        ChineseTranslator = translator_module.ChineseTranslator
        
        print("\n📊 测试API使用统计")
        print("-" * 50)
        
        # 测试1: 无客户端时的统计
        try:
            translator = ChineseTranslator(glm_api_key=None)
            stats = translator.get_api_usage_stats()
            
            self.log_test("无客户端统计", 
                         "error" in stats,
                         f"统计: {stats}")
        except Exception as e:
            self.log_test("无客户端统计", False, "", str(e))
        
        # 测试2: 有客户端时的统计
        try:
            fake_api_key = "fake-api-key"
            with patch.object(translator_module, 'GLMClientWrapper') as mock_wrapper:
                mock_client = Mock()
                mock_wrapper.return_value = mock_client
                
                translator = ChineseTranslator(glm_api_key=fake_api_key)
                stats = translator.get_api_usage_stats()
                
                # 应该返回统计信息而不是错误
                self.log_test("有客户端统计", 
                             "error" not in stats,
                             f"统计: {stats}")
        except Exception as e:
            self.log_test("有客户端统计", False, "", str(e))
    
    def generate_report(self):
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["passed"])
        failed_tests = total_tests - passed_tests
        
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": round(passed_tests / total_tests * 100, 2) if total_tests > 0 else 0,
                "execution_time": round(time.time() - self.start_time, 2)
            },
            "test_results": self.test_results,
            "detailed_analysis": {
                "extract_content_tests": [r for r in self.test_results if "extract_content" in r["test_name"] or "字典" in r["test_name"]],
                "initialization_tests": [r for r in self.test_results if "初始化" in r["test_name"]],
                "fallback_tests": [r for r in self.test_results if "fallback" in r["test_name"] or "重试" in r["test_name"]],
                "resilience_tests": [r for r in self.test_results if "容错" in r["test_name"] or "处理" in r["test_name"]],
                "stats_tests": [r for r in self.test_results if "统计" in r["test_name"]]
            }
        }
        
        return report
    
    def print_report(self, report):
        """打印测试报告"""
        print("\n" + "="*80)
        print("📋 ChineseTranslator 测试报告")
        print("="*80)
        
        summary = report["test_summary"]
        print(f"🎯 测试总览:")
        print(f"   • 总测试数: {summary['total_tests']}")
        print(f"   • 通过: {summary['passed']} ✅")
        print(f"   • 失败: {summary['failed']} ❌")
        print(f"   • 成功率: {summary['success_rate']}%")
        print(f"   • 执行时间: {summary['execution_time']}秒")
        
        print(f"\n🔍 分类统计:")
        analysis = report["detailed_analysis"]
        for category, tests in analysis.items():
            if tests:
                passed = sum(1 for t in tests if t["passed"])
                total = len(tests)
                print(f"   • {category}: {passed}/{total} 通过")
        
        # 显示失败的测试
        failed_tests = [r for r in report["test_results"] if not r["passed"]]
        if failed_tests:
            print(f"\n❌ 失败的测试:")
            for test in failed_tests:
                print(f"   • {test['test_name']}: {test['error']}")
        
        print("\n" + "="*80)
        
        return report

def main():
    """主测试函数"""
    print("🚀 开始测试 ChineseTranslator 类")
    print("="*80)
    
    tester = TranslatorTester()
    
    # 执行所有测试
    tester.test_extract_content_from_response()
    tester.test_translator_initialization()
    tester.test_translate_title_fallback()
    tester.test_translate_title_with_mock_api()
    tester.test_process_article_resilience()
    tester.test_api_usage_stats()
    
    # 生成并打印报告
    report = tester.generate_report()
    final_report = tester.print_report(report)
    
    # 保存报告到文件
    report_file = "translator_test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, ensure_ascii=False, indent=2)
    
    print(f"📄 详细报告已保存到: {report_file}")
    
    # 返回是否全部通过
    return final_report["test_summary"]["failed"] == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)