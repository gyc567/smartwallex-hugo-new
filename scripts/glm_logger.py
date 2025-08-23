"""
GLM-4.5 API调用日志模块
记录请求内容、返回内容和token消耗
"""

import os
import json
import datetime
import logging
from typing import Dict, Any, Optional
from functools import wraps
from openai import OpenAI

class GLMLogger:
    """GLM-4.5 API调用日志记录器"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.ensure_log_directory()
        self.setup_logger()
        
    def ensure_log_directory(self):
        """确保日志目录存在"""
        os.makedirs(self.log_dir, exist_ok=True)
        
    def setup_logger(self):
        """设置日志记录器"""
        # 创建今日日志文件
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(self.log_dir, f"glm_api_{today}.log")
        
        # 配置日志格式
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()  # 同时输出到控制台
            ]
        )
        
        self.logger = logging.getLogger('GLM_API')
        
    def log_api_call(self, 
                     function_name: str,
                     request_data: Dict[str, Any], 
                     response_data: Dict[str, Any],
                     usage_info: Optional[Dict[str, Any]] = None,
                     error: Optional[str] = None):
        """
        记录API调用详情
        
        Args:
            function_name: 调用的函数名称
            request_data: 请求数据
            response_data: 响应数据 
            usage_info: token使用信息
            error: 错误信息（如果有）
        """
        
        # 构建日志条目
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "function": function_name,
            "request": {
                "model": request_data.get("model"),
                "messages": request_data.get("messages"),
                "temperature": request_data.get("temperature"),
                "top_p": request_data.get("top_p"), 
                "max_tokens": request_data.get("max_tokens")
            },
            "response": {
                "success": error is None,
                "content": response_data.get("content") if not error else None,
                "error": error
            },
            "usage": usage_info or {}
        }
        
        # 记录到文件
        self._save_detailed_log(log_entry)
        
        # 记录摘要到标准日志
        if error:
            self.logger.error(f"API调用失败 - {function_name}: {error}")
        else:
            tokens_used = usage_info.get("total_tokens", 0) if usage_info else 0
            self.logger.info(f"API调用成功 - {function_name}: 消耗 {tokens_used} tokens")
            
    def _save_detailed_log(self, log_entry: Dict[str, Any]):
        """保存详细日志到JSON文件"""
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        detail_log_file = os.path.join(self.log_dir, f"glm_api_details_{today}.jsonl")
        
        with open(detail_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            
    def get_daily_stats(self, date: str = None) -> Dict[str, Any]:
        """
        获取指定日期的API调用统计
        
        Args:
            date: 日期字符串 (YYYY-MM-DD)，默认为今天
            
        Returns:
            统计信息字典
        """
        if not date:
            date = datetime.datetime.now().strftime('%Y-%m-%d')
            
        detail_log_file = os.path.join(self.log_dir, f"glm_api_details_{date}.jsonl")
        
        if not os.path.exists(detail_log_file):
            return {"error": f"找不到日期 {date} 的日志文件"}
            
        stats = {
            "date": date,
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "functions": {},
            "errors": []
        }
        
        try:
            with open(detail_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    entry = json.loads(line.strip())
                    stats["total_calls"] += 1
                    
                    # 统计函数调用
                    func_name = entry["function"]
                    if func_name not in stats["functions"]:
                        stats["functions"][func_name] = {"calls": 0, "tokens": 0}
                    stats["functions"][func_name]["calls"] += 1
                    
                    # 统计成功/失败
                    if entry["response"]["success"]:
                        stats["successful_calls"] += 1
                    else:
                        stats["failed_calls"] += 1
                        stats["errors"].append({
                            "function": func_name,
                            "error": entry["response"]["error"],
                            "timestamp": entry["timestamp"]
                        })
                    
                    # 统计token使用
                    usage = entry.get("usage", {})
                    if usage:
                        total = usage.get("total_tokens", 0)
                        prompt = usage.get("prompt_tokens", 0)
                        completion = usage.get("completion_tokens", 0)
                        
                        stats["total_tokens"] += total
                        stats["prompt_tokens"] += prompt
                        stats["completion_tokens"] += completion
                        stats["functions"][func_name]["tokens"] += total
                        
        except Exception as e:
            stats["error"] = f"解析日志文件时出错: {str(e)}"
            
        return stats


class GLMClientWrapper:
    """GLM客户端包装器，自动记录API调用"""
    
    def __init__(self, api_key: str, base_url: str, logger: GLMLogger = None):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.logger = logger or GLMLogger()
        
    def chat_completions_create(self, **kwargs):
        """
        包装OpenAI客户端的chat.completions.create方法，添加日志记录
        """
        function_name = "chat_completions_create"
        error = None
        response_data = {}
        usage_info = {}
        
        try:
            # 记录请求信息
            request_data = {
                "model": kwargs.get("model"),
                "messages": kwargs.get("messages"),
                "temperature": kwargs.get("temperature"),
                "top_p": kwargs.get("top_p"),
                "max_tokens": kwargs.get("max_tokens")
            }
            
            # 执行API调用
            completion = self.client.chat.completions.create(**kwargs)
            
            # 提取响应信息
            response_data = {
                "content": completion.choices[0].message.content if completion.choices else None,
                "finish_reason": completion.choices[0].finish_reason if completion.choices else None
            }
            
            # 提取使用信息
            if hasattr(completion, 'usage') and completion.usage:
                usage_info = {
                    "prompt_tokens": completion.usage.prompt_tokens,
                    "completion_tokens": completion.usage.completion_tokens,
                    "total_tokens": completion.usage.total_tokens
                }
            
            # 记录日志
            self.logger.log_api_call(
                function_name=function_name,
                request_data=request_data,
                response_data=response_data,
                usage_info=usage_info
            )
            
            return completion
            
        except Exception as e:
            error = str(e)
            # 记录错误日志
            self.logger.log_api_call(
                function_name=function_name,
                request_data=kwargs,
                response_data=response_data,
                error=error
            )
            raise


def log_glm_call(logger: GLMLogger = None):
    """
    装饰器，用于记录GLM API调用
    """
    if logger is None:
        logger = GLMLogger()
        
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            function_name = func.__name__
            error = None
            
            try:
                result = func(*args, **kwargs)
                
                # 记录成功调用
                logger.log_api_call(
                    function_name=function_name,
                    request_data={"args": str(args), "kwargs": str(kwargs)},
                    response_data={"result": str(result)[:500]}  # 限制长度
                )
                
                return result
                
            except Exception as e:
                error = str(e)
                # 记录失败调用
                logger.log_api_call(
                    function_name=function_name,
                    request_data={"args": str(args), "kwargs": str(kwargs)},
                    response_data={},
                    error=error
                )
                raise
                
        return wrapper
    return decorator


if __name__ == "__main__":
    # 测试日志功能
    logger = GLMLogger()
    
    # 模拟API调用
    test_request = {
        "model": "glm-4.5",
        "messages": [{"role": "user", "content": "测试消息"}],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    test_response = {
        "content": "测试响应内容"
    }
    
    test_usage = {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30
    }
    
    logger.log_api_call(
        function_name="test_function",
        request_data=test_request,
        response_data=test_response,
        usage_info=test_usage
    )
    
    print("日志测试完成")
    
    # 显示统计信息
    stats = logger.get_daily_stats()
    print(f"今日统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")