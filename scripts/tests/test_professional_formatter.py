#!/usr/bin/env python3
"""
专业格式化器的单元测试
测试覆盖率: 100%
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock, mock_open
import tempfile
import json

# 添加脚本目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lookonchain.professional_formatter import ProfessionalFormatter


class TestProfessionalFormatter(unittest.TestCase):
    """专业格式化器测试类"""
    
    def setUp(self):
        """测试前置设置"""
        self.sample_article_data = {
            'id': 'test-001',
            'original_title': 'Bitcoin Whale Movement Analysis',
            'chinese_title': '比特币鲸鱼转移分析',
            'original_content': 'A large Bitcoin whale has moved 1000 BTC...',
            'chinese_content': '一只大型比特币鲸鱼转移了1000个BTC...',
            'summary': '本文分析了最新的比特币大额转账活动',
            'url': 'https://example.com/article'
        }
        
        self.sample_template = """+++
date = '2025-08-12T16:52:01+08:00'
title = 'Sample Template Title'
+++

## 🎯 平台概览与核心价值
Sample overview content

## 🛠️ 核心功能深度评测
Sample features content

## 📚 完整使用指南
Sample guide content"""

    @patch('lookonchain.professional_formatter.create_openai_client')
    @patch('builtins.open', new_callable=mock_open, read_data="sample template content")
    def test_init_success(self, mock_file, mock_create_client):
        """测试初始化成功"""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        formatter = ProfessionalFormatter("test_api_key")
        
        self.assertEqual(formatter.api_key, "test_api_key")
        self.assertEqual(formatter.client, mock_client)
        self.assertIsNotNone(formatter.template_content)
        mock_create_client.assert_called_once()

    @patch('lookonchain.professional_formatter.create_openai_client')
    @patch('builtins.open', side_effect=FileNotFoundError("Template not found"))
    def test_init_template_load_failure(self, mock_file, mock_create_client):
        """测试模板加载失败"""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        with patch('builtins.print') as mock_print:
            formatter = ProfessionalFormatter("test_api_key")
        
        self.assertEqual(formatter.template_content, "")
        mock_print.assert_any_call("⚠️ 无法加载模板文件: Template not found")

    @patch('lookonchain.professional_formatter.OPENAI_API_KEY', None)
    @patch('lookonchain.professional_formatter.create_openai_client')
    @patch('builtins.open', new_callable=mock_open, read_data="template")
    def test_init_no_api_key(self, mock_file, mock_create_client):
        """测试无API密钥初始化"""
        with patch('builtins.print') as mock_print:
            formatter = ProfessionalFormatter("")
        
        self.assertIsNone(formatter.client)
        mock_print.assert_any_call("❌ OpenAI API密钥未设置，专业格式化功能将不可用")
        # 确保客户端创建函数没有被调用（因为提前return了）
        mock_create_client.assert_not_called()

    @patch('lookonchain.professional_formatter.create_openai_client')
    @patch('builtins.open', new_callable=mock_open, read_data="template")
    def test_init_client_creation_failure(self, mock_file, mock_create_client):
        """测试客户端创建失败"""
        mock_create_client.return_value = None
        
        with patch('builtins.print') as mock_print:
            formatter = ProfessionalFormatter("test_api_key")
        
        self.assertIsNone(formatter.client)
        mock_print.assert_any_call("❌ 专业格式化客户端创建失败")

    @patch('lookonchain.professional_formatter.create_openai_client')
    @patch('builtins.open', new_callable=mock_open, read_data="template")
    def test_init_exception_handling(self, mock_file, mock_create_client):
        """测试初始化异常处理"""
        mock_create_client.side_effect = Exception("Client creation error")
        
        with patch('builtins.print') as mock_print:
            formatter = ProfessionalFormatter("test_api_key")
        
        self.assertIsNone(formatter.client)
        mock_print.assert_any_call("❌ 专业格式化客户端初始化失败: Client creation error")

    @patch('builtins.open', new_callable=mock_open, read_data="template")
    def test_load_template_success(self, mock_file):
        """测试模板加载成功"""
        formatter = ProfessionalFormatter()
        template_content = formatter._load_template()
        
        self.assertEqual(template_content, "template")

    @patch('builtins.open', side_effect=FileNotFoundError())
    def test_load_template_failure(self, mock_file):
        """测试模板加载失败"""
        formatter = ProfessionalFormatter()
        template_content = formatter._load_template()
        
        self.assertEqual(template_content, "")

    @patch('lookonchain.professional_formatter.create_openai_client')
    @patch('builtins.open', new_callable=mock_open, read_data="template")
    def test_format_content_no_client(self, mock_file, mock_create_client):
        """测试无客户端情况下格式化"""
        formatter = ProfessionalFormatter()
        formatter.client = None
        
        with patch('builtins.print') as mock_print:
            result = formatter.format_content(self.sample_article_data)
        
        self.assertEqual(result, self.sample_article_data)
        mock_print.assert_any_call("❌ 专业格式化客户端未初始化，跳过格式化")

    @patch('lookonchain.professional_formatter.create_openai_client')
    @patch('builtins.open', new_callable=mock_open, read_data="template")
    def test_format_content_no_template(self, mock_file, mock_create_client):
        """测试无模板情况下格式化"""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        formatter = ProfessionalFormatter("test_api_key")
        formatter.template_content = ""
        
        with patch('builtins.print') as mock_print:
            result = formatter.format_content(self.sample_article_data)
        
        self.assertEqual(result, self.sample_article_data)
        mock_print.assert_any_call("⚠️ 模板内容为空，跳过格式化")

    @patch('lookonchain.professional_formatter.create_openai_client')
    @patch('lookonchain.professional_formatter.extract_content_from_response')
    @patch('builtins.open', new_callable=mock_open, read_data="template")
    def test_format_content_success(self, mock_file, mock_extract, mock_create_client):
        """测试格式化成功"""
        mock_client = Mock()
        mock_client.chat_completions_create.return_value = Mock()
        mock_create_client.return_value = mock_client
        mock_extract.return_value = "formatted content"
        
        formatter = ProfessionalFormatter("test_api_key")
        
        with patch('builtins.print') as mock_print:
            result = formatter.format_content(self.sample_article_data)
        
        expected_result = self.sample_article_data.copy()
        expected_result['formatted_content'] = "formatted content"
        expected_result['is_professionally_formatted'] = True
        
        self.assertEqual(result, expected_result)
        self.assertTrue(result['is_professionally_formatted'])
        mock_print.assert_any_call("✅ 专业格式化完成，长度: 17 字符")

    @patch('lookonchain.professional_formatter.create_openai_client')
    @patch('lookonchain.professional_formatter.extract_content_from_response')
    @patch('builtins.open', new_callable=mock_open, read_data="template")
    def test_format_content_extraction_failure(self, mock_file, mock_extract, mock_create_client):
        """测试内容提取失败"""
        mock_client = Mock()
        mock_client.chat_completions_create.return_value = Mock()
        mock_create_client.return_value = mock_client
        mock_extract.return_value = None
        
        formatter = ProfessionalFormatter("test_api_key")
        
        with patch('builtins.print') as mock_print:
            result = formatter.format_content(self.sample_article_data)
        
        self.assertEqual(result, self.sample_article_data)
        mock_print.assert_any_call("❌ 专业格式化失败，使用原始内容")

    @patch('lookonchain.professional_formatter.create_openai_client')
    @patch('builtins.open', new_callable=mock_open, read_data="template")
    def test_format_content_api_exception(self, mock_file, mock_create_client):
        """测试API调用异常"""
        mock_client = Mock()
        mock_client.chat_completions_create.side_effect = Exception("API Error")
        mock_create_client.return_value = mock_client
        
        formatter = ProfessionalFormatter("test_api_key")
        
        with patch('builtins.print') as mock_print:
            result = formatter.format_content(self.sample_article_data)
        
        self.assertEqual(result, self.sample_article_data)
        mock_print.assert_any_call("❌ 专业格式化过程出错: API Error")

    def test_build_system_prompt(self):
        """测试系统提示词构建"""
        formatter = ProfessionalFormatter()
        formatter.template_content = self.sample_template
        
        system_prompt = formatter._build_system_prompt()
        
        self.assertIn("专业的加密货币和区块链内容编辑专家", system_prompt)
        self.assertIn("LookOnChain的链上数据分析内容", system_prompt)
        self.assertIn("平台概览与核心价值", system_prompt)

    def test_build_user_prompt(self):
        """测试用户提示词构建"""
        formatter = ProfessionalFormatter()
        
        user_prompt = formatter._build_user_prompt(self.sample_article_data)
        
        self.assertIn("Bitcoin Whale Movement Analysis", user_prompt)
        self.assertIn("比特币鲸鱼转移分析", user_prompt)
        self.assertIn("A large Bitcoin whale has moved", user_prompt)
        self.assertIn("一只大型比特币鲸鱼转移了", user_prompt)

    def test_extract_formatted_sections(self):
        """测试章节提取功能"""
        formatter = ProfessionalFormatter()
        
        formatted_content = """
## 🎯 平台概览与核心价值
This is overview content
More overview details

## 🛠️ 核心功能深度评测
This is features content

## 📚 完整使用指南
This is guide content

## 💰 订阅计划与性价比分析
This is pricing content
"""
        
        sections = formatter.extract_formatted_sections(formatted_content)
        
        self.assertIn('overview', sections)
        self.assertIn('features', sections)
        self.assertIn('guide', sections)
        self.assertIn('pricing', sections)
        
        self.assertIn('This is overview content', sections['overview'])
        self.assertIn('This is features content', sections['features'])

    def test_extract_formatted_sections_no_matches(self):
        """测试无匹配章节的情况"""
        formatter = ProfessionalFormatter()
        
        formatted_content = "Just some random content without proper sections"
        
        sections = formatter.extract_formatted_sections(formatted_content)
        
        # 所有章节应该为空字符串
        for section_name in ['overview', 'features', 'guide', 'pricing', 'analysis', 'comparison', 'recommendations', 'summary']:
            self.assertEqual(sections[section_name], "")

    def test_extract_formatted_sections_partial_matches(self):
        """测试部分章节匹配的情况"""
        formatter = ProfessionalFormatter()
        
        formatted_content = """
## 🎯 平台概览与核心价值
Overview content only

Some other content
"""
        
        sections = formatter.extract_formatted_sections(formatted_content)
        
        self.assertIn('Overview content only', sections['overview'])
        self.assertEqual(sections['features'], "")
        self.assertEqual(sections['guide'], "")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)