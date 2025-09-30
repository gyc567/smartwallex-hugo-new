#!/usr/bin/env python3
"""
测试私人频道消息发送
用于验证私人频道配置是否正确
"""

import os
import sys
import requests
import json
from typing import Optional, Dict, Any

# 将脚本目录添加到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram_sender import TelegramSender

def test_private_channel(bot_token: str, channel_id: str) -> bool:
    """
    测试私人频道消息发送
    
    Args:
        bot_token: 机器人TOKEN
        channel_id: 频道ID（数字格式，如-1001234567890）
        
    Returns:
        bool: 测试是否成功
    """
    print(f"正在测试私人频道连接...")
    print(f"频道ID: {channel_id}")
    
    try:
        sender = TelegramSender(bot_token, channel_id)
        
        # 测试消息
        test_message = """🔧 <b>私人频道连接测试</b>

✅ 机器人配置正确
✅ 频道权限设置完成
✅ 消息发送功能正常

<em>如果看到此消息，说明私人频道配置成功！</em>

🤖 <b>SmartWallex Trading Bot</b>"""
        
        success = sender.send_message(test_message)
        
        if success:
            print("✅ 私人频道消息发送成功！")
            return True
        else:
            print("❌ 私人频道消息发送失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def get_channel_info(bot_token: str, channel_id: str) -> Optional[Dict[str, Any]]:
    """
    获取频道基本信息
    
    Args:
        bot_token: 机器人TOKEN
        channel_id: 频道ID
        
    Returns:
        频道信息或None
    """
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getChat"
        params = {"chat_id": channel_id}
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get("ok"):
            chat = data["result"]
            print(f"=== 频道信息 ===")
            print(f"ID: {chat['id']}")
            print(f"类型: {chat['type']}")
            print(f"标题: {chat.get('title', 'N/A')}")
            print(f"描述: {chat.get('description', 'N/A')}")
            print(f"成员数: {chat.get('member_count', '未知')}")
            return chat
        else:
            print(f"获取频道信息失败: {data.get('description')}")
            return None
            
    except Exception as e:
        print(f"获取频道信息出错: {e}")
        return None

def main():
    """主函数"""
    print("=== 私人频道配置测试工具 ===\n")
    
    # 从环境变量获取配置
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID", "").strip()
    
    if not bot_token:
        print("❌ 未找到 TELEGRAM_BOT_TOKEN 环境变量")
        print("请设置: export TELEGRAM_BOT_TOKEN='你的机器人token'")
        return
        
    if not channel_id:
        print("❌ 未找到 TELEGRAM_CHANNEL_ID 环境变量")
        print("请设置: export TELEGRAM_CHANNEL_ID='-1001234567890'")
        return
    
    print(f"机器人Token: {bot_token[:10]}...")
    print(f"频道ID: {channel_id}")
    print()
    
    # 获取频道信息
    print("1. 获取频道信息...")
    channel_info = get_channel_info(bot_token, channel_id)
    
    if not channel_info:
        print("❌ 无法获取频道信息，请检查配置")
        return
    
    print()
    
    # 测试消息发送
    print("2. 测试消息发送...")
    success = test_private_channel(bot_token, channel_id)
    
    if success:
        print("\n🎉 私人频道配置成功！")
        print("你现在可以使用这个频道接收交易信号了。")
    else:
        print("\n❌ 私人频道配置失败")
        print("请检查：")
        print("  - 机器人是否已添加到频道管理员")
        print("  - 机器人权限是否足够（至少需要发送消息权限）")
        print("  - 频道ID是否正确（私人频道ID为负数）")
        print("  - 机器人隐私模式是否已关闭")

if __name__ == "__main__":
    main()