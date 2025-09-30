#!/usr/bin/env python3
"""
获取Telegram频道ID的工具
用于获取私人频道的真实数字ID
"""

import os
import requests
import json

def get_updates():
    """获取机器人的更新，包括频道信息"""
    # 从环境变量获取TOKEN
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    
    if not bot_token:
        print("❌ 未找到 TELEGRAM_BOT_TOKEN 环境变量")
        print("请先设置: export TELEGRAM_BOT_TOKEN='你的机器人token'")
        return
    
    print(f"使用Token: {bot_token[:10]}...")
    
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    try:
        print("正在获取更新信息...")
        response = requests.get(url)
        data = response.json()
        
        print(f"\n=== API响应状态 ===")
        print(f"状态: {'成功' if data.get('ok') else '失败'}")
        print(f"响应码: {data.get('ok', 'unknown')}")
        
        if data.get("ok"):
            results = data.get("result", [])
            print(f"\n=== 找到 {len(results)} 条更新 ===")
            
            if not results:
                print("⚠️  没有收到任何更新")
                print("请确保：")
                print("  1. 机器人已添加到频道作为管理员")
                print("  2. 在频道中发送了一条测试消息")
                print("  3. 机器人隐私模式已关闭（通过@BotFather设置）")
                return
            
            # 解析频道信息
            for i, result in enumerate(results, 1):
                print(f"\n--- 更新 #{i} ---")
                print(f"原始数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                if "channel_post" in result:
                    chat = result["channel_post"]["chat"]
                    print(f"\n🎯 <b>发现频道信息！</b>")
                    print(f"频道ID: {chat['id']}")
                    print(f"频道标题: {chat.get('title', 'N/A')}")
                    print(f"频道类型: {chat['type']}")
                    print(f"用户名: {chat.get('username', '无（私人频道）')}")
                    
                    # 特别关注私人频道
                    if chat['id'] < 0:
                        print(f"\n✅ <b>这是私人频道ID: {chat['id']}</b>")
                        print(f"请在你的配置中使用: TELEGRAM_CHANNEL_ID={chat['id']}")
                    else:
                        print(f"\n✅ <b>这是公开频道ID: {chat['id']}</b>")
                        if chat.get('username'):
                            print(f"也可以使用: @{chat['username']}")
                            
                elif "message" in result:
                    chat = result["message"]["chat"]
                    print(f"\n💬 发现聊天信息:")
                    print(f"聊天ID: {chat['id']}")
                    print(f"聊天类型: {chat['type']}")
                    print(f"标题: {chat.get('title', chat.get('first_name', 'N/A'))}")
                
                else:
                    print(f"其他类型的更新: {list(result.keys())}")
        else:
            print(f"❌ API错误: {data.get('description', '未知错误')}")
            
            # 常见错误处理
            error_desc = data.get('description', '')
            if 'unauthorized' in error_desc.lower():
                print("\n🔧 解决方案:")
                print("  1. 检查机器人TOKEN是否正确")
                print("  2. 确保机器人没有被封禁")
            elif 'not found' in error_desc.lower():
                print("\n🔧 解决方案:")
                print("  1. 机器人可能还没有收到任何更新")
                print("  2. 在频道中发送一条消息，然后重新运行")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        print("请检查网络连接")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        print(f"错误类型: {type(e).__name__}")

def main():
    """主函数"""
    print("=== Telegram频道ID获取工具 ===")
    print("用于获取私人频道的真实数字ID\n")
    
    get_updates()
    
    print("\n" + "="*50)
    print("如果以上信息中没有找到频道ID，请:")
    print("1. 确保机器人已添加到频道管理员")
    print("2. 在频道中发送一条测试消息")
    print("3. 重新运行此脚本")
    print("4. 如仍有问题，检查机器人隐私模式设置")

if __name__ == "__main__":
    main()