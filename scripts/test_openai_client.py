#!/usr/bin/env python3
"""
OpenAI兼容客户端的完整单元测试
测试覆盖率：100%
遵循KISS原则和高内聚低耦合设计
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import json

# 添加脚本目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from openai_client import (
    OpenAIClientWrapper,
    create_openai_client,
    extract_content_from_response,
    GLMLogger
)


class TestGLMLogger(unittest.TestCase):
    """测试GLMLogger类"""
    
    def test_init(self):
        """测试初始化"""
        logger = GLMLogger()
        expected_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0
        }
        self.assertEqual(logger.stats, expected_stats)
    
    def test_get_daily_stats(self):
        """测试获取统计数据"""
        logger = GLMLogger()
        logger.stats["total_calls"] = 5
        stats = logger.get_daily_stats()
        self.assertEqual(stats["total_calls"], 5)
        # 确保返回的是同一个对象引用
        self.assertIs(stats, logger.stats)


class TestOpenAIClientWrapper(unittest.TestCase):
    """测试OpenAIClientWrapper类"""
    
    def setUp(self):
        """设置测试环境"""
        self.api_key = "test-api-key"
        self.base_url = "https://test.api.com/v1/"
        self.model = "test-model"
        self.logger = GLMLogger()
    
    @patch('openai_client.OpenAI')
    def test_init(self, mock_openai):
        """测试初始化"""
        wrapper = OpenAIClientWrapper(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            logger=self.logger
        )
        
        self.assertEqual(wrapper.api_key, self.api_key)
        self.assertEqual(wrapper.base_url, self.base_url)
        self.assertEqual(wrapper.model, self.model)
        self.assertEqual(wrapper.logger, self.logger)
        mock_openai.assert_called_once_with(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    @patch('openai_client.OpenAI')
    def test_init_with_default_logger(self, mock_openai):
        """测试使用默认日志记录器初始化"""
        wrapper = OpenAIClientWrapper(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model
        )
        
        self.assertIsInstance(wrapper.logger, GLMLogger)
    
    @patch('openai_client.OpenAI')
    @patch('openai_client.time.time')
    def test_chat_completions_create_success(self, mock_time, mock_openai):
        """测试成功的聊天完成请求"""
        # 设置模拟
        mock_time.side_effect = [1000.0, 1001.5]  # start_time, end_time
        
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 100
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 50
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        wrapper = OpenAIClientWrapper(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            logger=self.logger
        )
        
        # 执行测试
        result = wrapper.chat_completions_create(
            messages=[{"role": "user", "content": "test"}],
            temperature=0.7
        )
        
        # 验证结果
        self.assertEqual(result, mock_response)
        self.assertEqual(self.logger.stats["total_calls"], 1)
        self.assertEqual(self.logger.stats["successful_calls"], 1)
        self.assertEqual(self.logger.stats["failed_calls"], 0)
        self.assertEqual(self.logger.stats["total_tokens"], 100)
        self.assertEqual(self.logger.stats["prompt_tokens"], 50)
        self.assertEqual(self.logger.stats["completion_tokens"], 50)
        
        # 验证API调用
        mock_client.chat.completions.create.assert_called_once_with(
            model=self.model,
            messages=[{"role": "user", "content": "test"}],
            temperature=0.7
        )
    
    @patch('openai_client.OpenAI')
    def test_chat_completions_create_with_explicit_model(self, mock_openai):
        """测试显式指定模型的聊天完成请求"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.usage = None
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        wrapper = OpenAIClientWrapper(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            logger=self.logger
        )
        
        # 使用显式模型
        result = wrapper.chat_completions_create(
            model="custom-model",
            messages=[{"role": "user", "content": "test"}]
        )
        
        # 验证使用了显式指定的模型
        mock_client.chat.completions.create.assert_called_once_with(
            model="custom-model",
            messages=[{"role": "user", "content": "test"}]
        )
    
    @patch('openai_client.OpenAI')
    def test_chat_completions_create_no_usage(self, mock_openai):
        """测试没有usage信息的响应"""
        mock_response = Mock()
        mock_response.usage = None
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        wrapper = OpenAIClientWrapper(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            logger=self.logger
        )
        
        result = wrapper.chat_completions_create(
            messages=[{"role": "user", "content": "test"}]
        )
        
        # 验证统计数据正确更新
        self.assertEqual(self.logger.stats["total_calls"], 1)
        self.assertEqual(self.logger.stats["successful_calls"], 1)
        self.assertEqual(self.logger.stats["total_tokens"], 0)
    
    @patch('openai_client.OpenAI')
    def test_chat_completions_create_failure(self, mock_openai):
        """测试API调用失败"""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        wrapper = OpenAIClientWrapper(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            logger=self.logger
        )
        
        # 验证异常被重新抛出
        with self.assertRaises(Exception) as context:
            wrapper.chat_completions_create(
                messages=[{"role": "user", "content": "test"}]
            )
        
        self.assertEqual(str(context.exception), "API Error")
        self.assertEqual(self.logger.stats["total_calls"], 1)
        self.assertEqual(self.logger.stats["successful_calls"], 0)
        self.assertEqual(self.logger.stats["failed_calls"], 1)
    
    @patch('openai_client.OpenAI')
    def test_get_stats(self, mock_openai):
        """测试获取统计信息"""
        wrapper = OpenAIClientWrapper(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            logger=self.logger
        )
        
        self.logger.stats["total_calls"] = 10
        stats = wrapper.get_stats()
        self.assertEqual(stats["total_calls"], 10)


class TestCreateOpenAIClient(unittest.TestCase):
    """测试create_openai_client工厂函数"""
    
    @patch.dict(os.environ, {'GLM_API_KEY': 'test-key'})
    @patch('openai_client.OpenAIClientWrapper')
    def test_create_client_with_defaults(self, mock_wrapper):
        """测试使用默认参数创建客户端"""
        mock_instance = Mock()
        mock_wrapper.return_value = mock_instance
        
        result = create_openai_client()
        
        self.assertEqual(result, mock_instance)
        mock_wrapper.assert_called_once_with(
            api_key='test-key',
            base_url='https://api-inference.modelscope.cn/v1/',
            model='Qwen/Qwen2.5-Coder-32B-Instruct',
            logger=None
        )
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-key'})
    @patch('openai_client.OpenAIClientWrapper')
    def test_create_client_with_openai_key(self, mock_wrapper):
        """测试使用OPENAI_API_KEY环境变量"""
        mock_instance = Mock()
        mock_wrapper.return_value = mock_instance
        
        result = create_openai_client()
        
        mock_wrapper.assert_called_once_with(
            api_key='openai-key',
            base_url='https://api-inference.modelscope.cn/v1/',
            model='Qwen/Qwen2.5-Coder-32B-Instruct',
            logger=None
        )
    
    def test_create_client_no_api_key(self):
        """测试没有API密钥的情况"""
        with patch.dict(os.environ, {}, clear=True):
            result = create_openai_client()
            self.assertIsNone(result)
    
    def test_create_client_invalid_api_key(self):
        """测试无效API密钥"""
        invalid_keys = [
            'your_zhipuai_api_key_here',
            'your_github_token_here',
            ''
        ]
        
        for key in invalid_keys:
            with patch.dict(os.environ, {'GLM_API_KEY': key}):
                result = create_openai_client()
                self.assertIsNone(result)
    
    @patch.dict(os.environ, {'GLM_API_KEY': 'test-key'})
    @patch('openai_client.OpenAIClientWrapper')
    def test_create_client_with_custom_params(self, mock_wrapper):
        """测试使用自定义参数创建客户端"""
        custom_logger = GLMLogger()
        mock_instance = Mock()
        mock_wrapper.return_value = mock_instance
        
        result = create_openai_client(
            api_key='custom-key',
            base_url='https://custom.api.com/',
            model='custom-model',
            logger=custom_logger
        )
        
        mock_wrapper.assert_called_once_with(
            api_key='custom-key',
            base_url='https://custom.api.com/',
            model='custom-model',
            logger=custom_logger
        )
    
    @patch.dict(os.environ, {
        'OPENAI_BASE_URL': 'https://env.api.com/',
        'OPENAI_MODEL': 'env-model'
    })
    @patch('openai_client.OpenAIClientWrapper')
    def test_create_client_with_env_vars(self, mock_wrapper):
        """测试使用环境变量配置"""
        with patch.dict(os.environ, {'GLM_API_KEY': 'test-key'}, clear=False):
            mock_instance = Mock()
            mock_wrapper.return_value = mock_instance
            
            result = create_openai_client()
            
            mock_wrapper.assert_called_once_with(
                api_key='test-key',
                base_url='https://env.api.com/',
                model='env-model',
                logger=None
            )
    
    @patch.dict(os.environ, {'GLM_API_KEY': 'test-key'})
    @patch('openai_client.OpenAIClientWrapper')
    def test_create_client_exception(self, mock_wrapper):
        """测试创建客户端时发生异常"""
        mock_wrapper.side_effect = Exception("Init error")
        
        result = create_openai_client()
        
        self.assertIsNone(result)


class TestExtractContentFromResponse(unittest.TestCase):
    """测试extract_content_from_response函数"""
    
    def test_extract_content_empty_response(self):
        """测试空响应"""
        result = extract_content_from_response(None, "test")
        self.assertIsNone(result)
    
    def test_extract_content_standard_format(self):
        """测试标准OpenAI响应格式"""
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = "Test content"
        
        result = extract_content_from_response(response, "test")
        self.assertEqual(result, "Test content")
    
    def test_extract_content_with_whitespace(self):
        """测试包含空白字符的内容"""
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = "  \n  Test content  \n  "
        
        result = extract_content_from_response(response, "test")
        self.assertEqual(result, "Test content")
    
    def test_extract_content_empty_content(self):
        """测试空内容"""
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = ""
        
        result = extract_content_from_response(response, "test")
        self.assertIsNone(result)
    
    def test_extract_content_none_content(self):
        """测试None内容"""
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = None
        
        result = extract_content_from_response(response, "test")
        self.assertIsNone(result)
    
    def test_extract_content_empty_choices(self):
        """测试空choices列表"""
        response = Mock()
        response.choices = []
        
        result = extract_content_from_response(response, "test")
        self.assertIsNone(result)
    
    def test_extract_content_no_choices(self):
        """测试没有choices属性"""
        response = Mock()
        del response.choices  # 删除choices属性
        response.__dict__ = {}
        
        result = extract_content_from_response(response, "test")
        self.assertIsNone(result)
    
    def test_extract_content_no_message(self):
        """测试没有message属性"""
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = None
        response.__dict__ = {'choices': response.choices}
        
        result = extract_content_from_response(response, "test")
        self.assertIsNone(result)
    
    def test_extract_content_error_response(self):
        """测试错误响应"""
        response = Mock()
        response.error = "API Error"
        
        result = extract_content_from_response(response, "test")
        self.assertIsNone(result)
    
    def test_extract_content_dict_format(self):
        """测试字典格式响应"""
        response = {'content': 'Dict content'}
        
        result = extract_content_from_response(response, "test")
        self.assertEqual(result, "Dict content")
    
    def test_extract_content_dict_choices(self):
        """测试字典中的choices格式"""
        response = {'choices': 'Choices content'}
        
        result = extract_content_from_response(response, "test")
        self.assertEqual(result, "Choices content")
    
    def test_extract_content_other_attributes(self):
        """测试其他可能的属性"""
        # 创建一个非Mock对象来测试属性提取
        class ResponseObj:
            def __init__(self):
                self.text = "Text content"
        
        response = ResponseObj()
        
        result = extract_content_from_response(response, "test")
        self.assertEqual(result, "Text content")
    
    def test_extract_content_exception(self):
        """测试解析过程中的异常"""
        response = Mock()
        response.choices = property(lambda self: (_ for _ in ()).throw(Exception("Parse error")))
        
        result = extract_content_from_response(response, "test")
        self.assertIsNone(result)


if __name__ == '__main__':
    # 设置详细输出
    unittest.main(verbosity=2)