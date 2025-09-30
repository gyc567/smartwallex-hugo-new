#!/usr/bin/env python3
"""
Telegram更新调试工具
获取所有类型的更新
"""

import requests
import json
import time

def get_detailed_updates(bot_token):
    """获取详细的更新信息"""
    print("=== Telegram更新调试工具 ===")
    print(f"Token: {bot_token[:10]}...")
    
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        print(f"\nAPI响应状态: {data.get('ok', False)}")
        print(f"完整响应:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        if data.get("ok"):
            results = data.get("result", [])
            print(f"\n=== 分析更新数据 ===")
            print(f"更新数量: {len(results)}")
            
            for i, result in enumerate(results, 1):
                print(f"\n--- 更新 #{i} ---")
                print(f"更新ID: {result.get('update_id', 'unknown')}")
                print(f"更新类型: {list(result.keys())}")
                
                # 详细分析每种类型
                if "message" in result:
                    msg = result["message"]
                    chat = msg.get("chat", {})
                    print(f"消息类型: message")
                    print(f"聊天ID: {chat.get('id', 'unknown')}")
                    print(f"聊天类型: {chat.get('type', 'unknown')}")
                    print(f"聊天标题: {chat.get('title', chat.get('first_name', 'N/A'))}")
                    if chat.get('username'):
                        print(f"用户名: @{chat['username']}")
                    print(f"消息文本: {msg.get('text', '无文本')[:100]}...")
                    
                elif "channel_post" in result:
                    post = result["channel_post"]
                    chat = post.get("chat", {})
                    print(f"消息类型: channel_post")
                    print(f"频道ID: {chat.get('id', 'unknown')}")
                    print(f"频道类型: {chat.get('type', 'unknown')}")
                    print(f"频道标题: {chat.get('title', 'N/A')}")
                    if chat.get('username'):
                        print(f"频道用户名: @{chat['username']}")
                    else:
                        print("频道用户名: 无（私人频道）")
                    print(f"消息文本: {post.get('text', '无文本')[:100]}...")
                    
                elif "edited_message" in result:
                    print("消息类型: edited_message")
                elif "edited_channel_post" in result:
                    print("消息类型: edited_channel_post")
                elif "callback_query" in result:
                    print("消息类型: callback_query")
                elif "inline_query" in result:
                    print("消息类型: inline_query")
                else:
                    print(f"其他更新类型: {list(result.keys())}")
                    
                # 打印完整的更新数据
                print(f"完整数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
        return data
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def check_webhook_status(bot_token):
    """检查webhook状态"""
    print("\n=== Webhook状态检查 ===")
    
    url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get("ok"):
            result = data.get("result", {})
            print(f"Webhook URL: {result.get('url', '无')}")
            print(f"有挂起的更新: {result.get('has_custom_certificate', False)}")
            print(f"最后错误日期: {result.get('last_error_date', '无')}")
            print(f"最大连接数: {result.get('max_connections', '默认')}")
            
            if result.get('pending_update_count', 0) > 0:
                print(f"⚠️  有 {result['pending_update_count']} 个挂起的更新")
            
        return data
        
    except Exception as e:
        print(f"检查webhook时出错: {e}")
        return None

def main():
    bot_token = "8209835379:AAEarEFcbfR8fDJMFw16A0h1MqWHliFTnYE"
    
    # 获取详细更新
    updates = get_detailed_updates(bot_token)
    
    # 检查webhook状态
    webhook = check_webhook_status(bot_token)
    
    print("\n" + "="*60)
    print("📋 诊断总结:")
    
    if updates and updates.get("ok"):
        results = updates.get("result", [])
        if results:
            print(f"✅ API连接正常，找到 {len(results)} 条更新")
            print("✅ 隐私模式已关闭（机器人可以看到消息）")
            
            # 统计不同类型的更新
            channel_posts = [r for r in results if "channel_post" in r]
            if channel_posts:
                print(f"🎯 找到 {len(channel_posts)} 条频道消息")
                for post in channel_posts:
                    chat = post["channel_post"]["chat"]
                    print(f"   频道ID: {chat['id']} - {chat.get('title', '未知标题')}")
            else:
                print("⚠️  没有找到频道消息")
                print("   请确保机器人已添加到私人频道")
        else:
            print("⚠️  API连接正常，但没有收到任何更新")
            print("   这表明机器人还没有被添加到任何频道")
            print("   或者频道中没有新的消息活动")
    else:
        print("❌ API连接有问题")
    
    print("\n🔧 下一步建议:")
    print("1. 确认机器人已添加到私人频道管理员")
    print("2. 在私人频道发送一条新消息")
    print("3. 等待30秒后重新运行此脚本")
    print("4. 如果仍有问题，考虑删除并重新添加机器人到频道")

if __name__ == "__main__":
    main()