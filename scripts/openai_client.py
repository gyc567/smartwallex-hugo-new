"""
OpenAI兼容接口统一客户端模块
支持ModelScope等OpenAI兼容的API服务
保持高内聚低耦合设计，遵循KISS原则
"""

import os
import time
from typing import Optional, Dict, Any
from openai import OpenAI

try:
    from glm_logger import GLMLogger as OriginalGLMLogger
    
    # 扩展原始GLMLogger，添加stats属性以保持兼容性
    class GLMLogger(OriginalGLMLogger):
        def __init__(self, log_dir: str = "logs"):
            super().__init__(log_dir)
            self.stats = {
                "total_calls": 0, 
                "successful_calls": 0, 
                "failed_calls": 0, 
                "total_tokens": 0, 
                "prompt_tokens": 0, 
                "completion_tokens": 0
            }
        
        def get_daily_stats(self):
            return self.stats
            
except ImportError:
    # 如果glm_logger不存在，创建简化版本
    class GLMLogger:
        def __init__(self, log_dir: str = "logs"):
            self.stats = {
                "total_calls": 0, 
                "successful_calls": 0, 
                "failed_calls": 0, 
                "total_tokens": 0, 
                "prompt_tokens": 0, 
                "completion_tokens": 0
            }
        
        def get_daily_stats(self):
            return self.stats


class OpenAIClientWrapper:
    """
    OpenAI兼容接口客户端包装器
    统一处理所有OpenAI兼容的API调用，包含日志记录功能
    """
    
    def __init__(self, api_key: str, base_url: str, model: str, logger: Optional[GLMLogger] = None):
        """
        初始化OpenAI兼容客户端
        
        Args:
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称
            logger: 可选的日志记录器
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.logger = logger or GLMLogger()
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    def chat_completions_create(self, **kwargs) -> Any:
        """
        创建聊天完成请求的统一接口
        自动记录API调用统计
        
        Returns:
            OpenAI ChatCompletion响应对象
        """
        # 确保使用配置的模型（如果没有指定）
        if 'model' not in kwargs:
            kwargs['model'] = self.model
        
        try:
            # 记录API调用开始
            start_time = time.time()
            self.logger.stats["total_calls"] += 1
            
            # 发起API请求
            response = self.client.chat.completions.create(**kwargs)
            
            # 记录成功调用
            self.logger.stats["successful_calls"] += 1
            
            # 记录token使用情况
            if hasattr(response, 'usage') and response.usage:
                self.logger.stats["total_tokens"] += response.usage.total_tokens or 0
                self.logger.stats["prompt_tokens"] += response.usage.prompt_tokens or 0
                self.logger.stats["completion_tokens"] += response.usage.completion_tokens or 0
            
            # 记录响应时间
            response_time = time.time() - start_time
            
            return response
            
        except Exception as e:
            # 记录失败调用
            self.logger.stats["failed_calls"] += 1
            # 重新抛出异常，保持原有错误处理逻辑
            raise e
    
    def get_stats(self) -> Dict[str, Any]:
        """获取API使用统计"""
        return self.logger.get_daily_stats()


def create_openai_client(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    logger: Optional[GLMLogger] = None
) -> Optional[OpenAIClientWrapper]:
    """
    创建OpenAI兼容客户端的工厂函数
    
    Args:
        api_key: API密钥，默认从环境变量获取
        base_url: API基础URL，默认使用ModelScope
        model: 模型名称，默认使用Qwen2.5-Coder
        logger: 日志记录器
    
    Returns:
        OpenAIClientWrapper实例或None（初始化失败时）
    """
    # 默认配置
    api_key = api_key or os.getenv('OPENAI_API_KEY')
    base_url = base_url or os.getenv('OPENAI_BASE_URL', 'https://api-inference.modelscope.cn/v1/')
    model = model or os.getenv('OPENAI_MODEL', 'Qwen/Qwen2.5-Coder-32B-Instruct')
    
    if not api_key:
        print("❌ API密钥未设置，请设置OPENAI_API_KEY环境变量")
        return None
    
    if api_key in ['your_openai_api_key_here', 'your_api_key_here', '']:
        print("❌ 检测到示例API密钥，请设置有效的OPENAI_API_KEY")
        return None
    
    try:
        client = OpenAIClientWrapper(
            api_key=api_key,
            base_url=base_url,
            model=model,
            logger=logger
        )
        print(f"✅ OpenAI兼容客户端初始化成功")
        print(f"   - 基础URL: {base_url}")
        print(f"   - 模型: {model}")
        
        return client
        
    except Exception as e:
        print(f"❌ OpenAI兼容客户端初始化失败: {e}")
        return None


def extract_content_from_response(response: Any, debug_context: str = "") -> Optional[str]:
    """
    稳健地从OpenAI API响应中提取文本内容
    支持多种可能的响应格式，提供详细的调试信息
    
    Args:
        response: API响应对象
        debug_context: 调试上下文信息
    
    Returns:
        提取的文本内容或None
    """
    if not response:
        print(f"⚠️ [{debug_context}] 响应为空")
        return None
    
    try:
        # 检查标准OpenAI响应格式
        if hasattr(response, 'choices') and response.choices:
            if not response.choices:
                print(f"⚠️ [{debug_context}] choices为空列表")
                return None
                
            choice = response.choices[0]
            
            # 检查message结构
            if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                content = choice.message.content
                if content and content.strip():
                    return content.strip()
                else:
                    print(f"⚠️ [{debug_context}] choices[0].message.content 为空")
        
        # 如果是字典格式
        if isinstance(response, dict):
            for key in ['content', 'text', 'output', 'result', 'choices']:
                if key in response and response[key]:
                    content = str(response[key]).strip()
                    if content:
                        print(f"✅ [{debug_context}] 从字典 {key} 找到内容")
                        return content
        
        # 尝试其他可能的响应格式 (非Mock对象)
        if not str(type(response)).endswith("Mock'>"):
            for attr_name in ['content', 'text', 'output', 'result']:
                if hasattr(response, attr_name):
                    content = getattr(response, attr_name)
                    if content and str(content).strip():
                        print(f"✅ [{debug_context}] 从 {attr_name} 字段找到内容")
                        return str(content).strip()
                    else:
                        print(f"⚠️ [{debug_context}] response.{attr_name} 为空")
        
        # 记录响应结构用于调试
        if hasattr(response, '__dict__'):
            print(f"🔍 [{debug_context}] 响应结构分析:")
            for key, value in response.__dict__.items():
                if key not in ['_client', '_request_id']:
                    value_str = str(value)[:100] if len(str(value)) > 100 else str(value)
                    print(f"    {key}: {type(value)} = {value_str}")
        
        print(f"❌ [{debug_context}] 无法提取内容")
        return None
        
    except Exception as e:
        print(f"❌ [{debug_context}] 解析响应时发生错误: {e}")
        return None


# 向后兼容的别名，保持与现有代码的兼容性
GLMClientWrapper = OpenAIClientWrapper