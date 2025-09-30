#!/usr/bin/env python3
"""
私人频道配置检查工具
"""

import requests
import json

def check_bot_status(bot_token):
    """检查机器人状态"""
    print("=== 机器人状态检查 ===")
    
    # 获取机器人信息
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    response = requests.get(url)
    data = response.json()
    
    if data.get("ok"):
        result = data["result"]
        print(f"机器人用户名: @{result['username']}")
        print(f"机器人ID: {result['id']}")
        print(f"可以加入群组: {'✅' if result.get('can_join_groups') else '❌'}")
        print(f"可以读取所有消息: {'✅' if result.get('can_read_all_group_messages') else '❌'}")
        
        if not result.get('can_read_all_group_messages'):
            print("⚠️  警告: 隐私模式可能开启，需要通过@BotFather关闭")
        
        return True
    else:
        print(f"❌ 无法获取机器人信息: {data.get('description')}")
        return False

def check_recent_updates(bot_token):
    """检查最近的更新"""
    print("\n=== 检查最近的更新 ===")
    
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url)
    data = response.json()
    
    if data.get("ok"):
        results = data.get("result", [])
        print(f"找到 {len(results)} 条更新")
        
        if results:
            for i, result in enumerate(results[-3:], 1):  # 只显示最近3条
                print(f"\n更新 #{i}:")
                if "channel_post" in result:
                    chat = result["channel_post"]["chat"]
                    print(f"  类型: 频道消息")
                    print(f"  频道ID: {chat['id']}")
                    print(f"  频道标题: {chat.get('title', 'N/A')}")
                    print(f"  消息文本: {result['channel_post'].get('text', '无文本')[:50]}...")
                elif "message" in result:
                    chat = result["message"]["chat"]
                    print(f"  类型: 私聊/群聊消息")
                    print(f"  聊天ID: {chat['id']}")
                    print(f"  聊天标题: {chat.get('title', chat.get('first_name', 'N/A'))}")
        else:
            print("⚠️  没有收到任何更新")
            print("\n🔧 解决步骤:")
            print("1. 确保机器人已添加到频道作为管理员")
            print("2. 在频道中发送一条测试消息")
            print("3. 通过@BotFather关闭机器人隐私模式(/setprivacy)")
            print("4. 等待几分钟让更新生效")

def main():
    # 你的TOKEN
    bot_token = "8209835379:AAEarEFcbfR8fDJMFw16A0h1MqWHliFTnYE"
    
    print("🔍 Telegram私人频道配置诊断工具")
    print("=" * 50)
    
    # 检查机器人状态
    bot_ok = check_bot_status(bot_token)
    
    if bot_ok:
        # 检查更新
        check_recent_updates(bot_token)
    
    print("\n" + "=" * 50)
    print("📋 配置检查清单:")
    print("1. ✅ 机器人TOKEN有效")
    print("2. 🔄 机器人已添加到私人频道管理员")
    print("3. 🔄 通过@BotFather关闭隐私模式(/setprivacy)")
    print("4. 🔄 在私人频道发送测试消息")
    print("5. 🔄 等待1-2分钟让更新生效")
    print("\n完成上述步骤后，重新运行get_channel_id.py")

if __name__ == "__main__":
    main()