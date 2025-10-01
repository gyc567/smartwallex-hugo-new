#!/usr/bin/env python3
"""
Telegram Bot Sender Module
Simple, focused module for sending messages to Telegram channels
"""

import os
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class TelegramSender:
    """Simple Telegram bot sender with minimal dependencies"""
    
    def __init__(self, bot_token: str, channel_id: str):
        """
        Initialize Telegram sender
        
        Args:
            bot_token: Telegram bot token from @BotFather
            channel_id: Telegram channel ID (with @ prefix for public channels)
        """
        self.bot_token = bot_token.strip()
        self.channel_id = channel_id.strip()
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send message to Telegram channel
        
        Args:
            message: Message text to send
            parse_mode: Parse mode ('HTML' or 'Markdown')
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not message or not message.strip():
            logger.error("Empty message provided")
            return False
            
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.channel_id,
                "text": message.strip(),
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                logger.info(f"Message sent successfully to {self.channel_id}")
                return True
            else:
                logger.error(f"Telegram API error: {result.get('description')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {e}")
            return False
    
    def send_trading_signal(self, signal_data: Dict[str, Any]) -> bool:
        """
        Send formatted trading signal to Telegram
        
        Args:
            signal_data: Dictionary containing signal information
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not signal_data:
            logger.error("Empty signal data provided")
            return False
            
        try:
            message = self._format_trading_signal(signal_data)
            return self.send_message(message, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error formatting trading signal: {e}")
            return False
    
    def _format_trading_signal(self, data: Dict[str, Any]) -> str:
        """Format trading signal data into Telegram message"""
        try:
            # 优先使用新的专业合约策略分析格式
            from professional_chinese_formatter import ProfessionalChineseFormatter
            formatter = ProfessionalChineseFormatter()
            
            # 使用专业合约策略分析格式
            return formatter.format_contract_analysis(data)
            
        except ImportError:
            logger.warning("Professional formatter not available, falling back to simple format")
            try:
                from signal_translator import SignalTranslator
                translator = SignalTranslator()
                return translator.format_professional_chinese(data)
            except ImportError:
                logger.warning("Chinese translator not available, falling back to English format")
                return self._format_english_signal(data)
        except Exception as e:
            logger.error(f"Error using professional formatter: {e}, falling back to English format")
            return self._format_english_signal(data)
    
    def _format_english_signal(self, data: Dict[str, Any]) -> str:
        """Format trading signal data into English Telegram message (fallback)"""
        symbol = data.get("symbol", "Unknown")
        signal = data.get("signal", "Unknown")
        entry_price = data.get("entry_price", "N/A")
        stop_loss = data.get("stop_loss", "N/A")
        take_profit = data.get("take_profit", "N/A")
        confidence = data.get("confidence", "N/A")
        timestamp = data.get("timestamp", "")
        
        # Simple HTML formatting for Telegram
        message = f"""📊 <b>SmartWallex Trading Signal</b>

🪙 <b>Symbol:</b> {symbol}
📈 <b>Signal:</b> {signal}
💰 <b>Entry:</b> {entry_price}
🛑 <b>Stop Loss:</b> {stop_loss}
🎯 <b>Take Profit:</b> {take_profit}
🎯 <b>Confidence:</b> {confidence}
"""
        
        if timestamp:
            message += f"\n⏰ <b>Time:</b> {timestamp}"
            
        message += "\n\n⚠️ <i>Risk Warning: Trading involves risk. Only invest what you can afford to lose.</i>"
        
        return message
    
    def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result.get("ok", False)
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


def create_sender_from_env() -> Optional[TelegramSender]:
    """
    Create TelegramSender from environment variables
    
    Returns:
        TelegramSender instance or None if env vars not set
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID", "").strip()
    
    if not bot_token or not channel_id:
        logger.warning("Telegram environment variables not configured")
        return None
        
    return TelegramSender(bot_token, channel_id)


if __name__ == "__main__":
    # Simple CLI for testing
    import argparse
    
    parser = argparse.ArgumentParser(description="Send Telegram messages")
    parser.add_argument("--token", required=True, help="Telegram bot token")
    parser.add_argument("--channel", required=True, help="Telegram channel ID")
    parser.add_argument("--message", required=True, help="Message to send")
    parser.add_argument("--test", action="store_true", help="Test connection only")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    sender = TelegramSender(args.token, args.channel)
    
    if args.test:
        success = sender.test_connection()
        print(f"Connection test: {'✅ Success' if success else '❌ Failed'}")
    else:
        success = sender.send_message(args.message)
        print(f"Message sent: {'✅ Success' if success else '❌ Failed'}")