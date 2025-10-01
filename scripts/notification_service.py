#!/usr/bin/env python3
"""
用户通知服务
提供实时数据失败时的用户通知功能
支持多种通知方式：控制台、日志、可选的邮件/短信等
"""

import logging
import datetime
import sys
from typing import Optional, Dict, Any
from pathlib import Path

# 添加scripts目录到Python路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

# 从现有的telegram_sender导入相关功能
try:
    from telegram_sender import TelegramSender
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False


class NotificationService:
    """用户通知服务类"""
    
    def __init__(self):
        """初始化通知服务"""
        self.logger = logging.getLogger(__name__)
        self.telegram_sender = None
        
        # 初始化Telegram发送器（如果可用）
        if TELEGRAM_AVAILABLE:
            try:
                self.telegram_sender = TelegramSender()
                self.logger.info("Telegram通知服务已初始化")
            except Exception as e:
                self.logger.warning(f"Telegram通知服务初始化失败: {e}")
                self.telegram_sender = None
    
    def notify_realtime_data_failure(self, symbol: str, error_message: str, context: Optional[Dict[str, Any]] = None):
        """通知用户实时数据获取失败
        
        Args:
            symbol: 失败的币种符号
            error_message: 错误信息
            context: 额外的上下文信息
        """
        try:
            # 构建通知消息
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            title = f"🚨 交易程序紧急通知 - {timestamp}"
            
            message = f"""
{title}

❌ CRITICAL: 实时数据获取失败

📊 失败币种: {symbol}
🔍 错误原因: {error_message}

⚠️  重要提醒:
• 为确保交易安全，程序已自动暂停
• 所有交易信号生成已停止
• 请立即检查Bitget API连接和配置

🔧 建议操作:
1. 检查网络连接
2. 验证Bitget API密钥配置
3. 查看详细日志了解具体错误
4. 修复问题后重启程序

💡 风险提示:
在没有实时数据的情况下进行交易极其危险，
程序自动暂停是为了保护您的资金安全。

⏰ 时间: {timestamp}
🤖 系统: SmartWallex交易信号生成器
"""

            # 控制台通知
            self._notify_console(message)
            
            # 日志记录
            self._notify_log(symbol, error_message, context)
            
            # Telegram通知（如果可用）
            self._notify_telegram(title, message)
            
            # 可选：其他通知方式（邮件、短信等）
            # self._notify_email(title, message)
            # self._notify_sms(message)
            
        except Exception as e:
            self.logger.error(f"通知发送失败: {e}")
    
    def notify_trading_pause(self, reason: str, details: Optional[Dict[str, Any]] = None):
        """通知用户交易程序已暂停
        
        Args:
            reason: 暂停原因
            details: 详细信息
        """
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            title = f"⏸️ 交易程序暂停通知 - {timestamp}"
            
            message = f"""
{title}

🛑 交易程序已自动暂停

📋 暂停原因: {reason}

🔒 安全状态:
• 所有交易信号生成已停止
• 未平仓头寸不受影响（如有）
• 程序将在问题解决后自动恢复

⏰ 暂停时间: {timestamp}
🤖 系统: SmartWallex交易信号生成器
"""

            if details:
                message += f"\n🔍 详细信息:\n"
                for key, value in details.items():
                    message += f"• {key}: {value}\n"

            # 发送各种通知
            self._notify_console(message)
            self._notify_log("TRADING_PAUSED", reason, details)
            self._notify_telegram(title, message)
            
        except Exception as e:
            self.logger.error(f"暂停通知发送失败: {e}")
    
    def notify_trading_resume(self, recovered_data: Dict[str, Any]):
        """通知用户交易程序已恢复
        
        Args:
            recovered_data: 恢复的数据信息
        """
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            title = f"✅ 交易程序恢复通知 - {timestamp}"
            
            message = f"""
{title}

🟢 交易程序已恢复正常运行

📊 恢复状态:
• 实时数据连接已重新建立
• 交易信号生成已恢复
• 系统运行状态良好

⏰ 恢复时间: {timestamp}
🤖 系统: SmartWallex交易信号生成器
"""

            if recovered_data:
                message += f"\n📈 数据状态:\n"
                for key, value in recovered_data.items():
                    message += f"• {key}: {value}\n"

            self._notify_console(message)
            self._notify_log("TRADING_RESUMED", "系统恢复正常", recovered_data)
            self._notify_telegram(title, message)
            
        except Exception as e:
            self.logger.error(f"恢复通知发送失败: {e}")
    
    def _notify_console(self, message: str):
        """控制台通知"""
        try:
            print("\n" + "="*80)
            print(message.strip())
            print("="*80 + "\n")
        except Exception as e:
            self.logger.error(f"控制台通知失败: {e}")
    
    def _notify_log(self, symbol: str, error_message: str, context: Optional[Dict[str, Any]] = None):
        """日志记录通知"""
        try:
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "symbol": symbol,
                "error": error_message,
                "context": context or {},
                "type": "REALTIME_DATA_FAILURE"
            }
            
            self.logger.error(f"实时数据失败通知: {log_entry}")
            
        except Exception as e:
            self.logger.error(f"日志通知失败: {e}")
    
    def _notify_telegram(self, title: str, message: str):
        """Telegram通知"""
        try:
            if self.telegram_sender and TELEGRAM_AVAILABLE:
                # 发送简短版本到Telegram（避免消息过长）
                short_message = f"""
🚨 SmartWallex交易通知

{title}

{message[:500]}...  # 截断消息避免过长

详情请查看日志文件。
"""
                
                self.telegram_sender.send_message(short_message)
                self.logger.info("Telegram通知已发送")
            else:
                self.logger.info("Telegram通知不可用，跳过")
                
        except Exception as e:
            self.logger.error(f"Telegram通知失败: {e}")
    
    def test_notification(self):
        """测试通知功能"""
        try:
            print("🔔 测试通知系统...")
            
            # 测试实时数据失败通知
            self.notify_realtime_data_failure(
                "BTC", 
                "测试错误 - 网络连接超时",
                {"test": True, "timestamp": datetime.datetime.now().isoformat()}
            )
            
            print("✅ 通知系统测试完成")
            return True
            
        except Exception as e:
            self.logger.error(f"通知系统测试失败: {e}")
            return False


# 全局通知服务实例
notification_service = NotificationService()

def notify_realtime_data_failure(symbol: str, error_message: str, context: Optional[Dict[str, Any]] = None):
    """全局函数：通知实时数据失败"""
    return notification_service.notify_realtime_data_failure(symbol, error_message, context)

def notify_trading_pause(reason: str, details: Optional[Dict[str, Any]] = None):
    """全局函数：通知交易暂停"""
    return notification_service.notify_trading_pause(reason, details)

def notify_trading_resume(recovered_data: Dict[str, Any]):
    """全局函数：通知交易恢复"""
    return notification_service.notify_trading_resume(recovered_data)


def main():
    """测试通知服务"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🔔 通知服务测试")
    print("="*60)
    
    # 测试通知系统
    success = notification_service.test_notification()
    
    if success:
        print("\n🎉 通知服务测试通过！")
        return 0
    else:
        print("\n❌ 通知服务测试失败！")
        return 1


if __name__ == "__main__":
    exit(main())