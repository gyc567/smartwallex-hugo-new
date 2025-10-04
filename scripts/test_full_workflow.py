#!/usr/bin/env python3
"""
完整工作流测试脚本
模拟GitHub Actions的完整流程
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def run_command(cmd, cwd=None):
    """运行shell命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_signal_generation():
    """测试信号生成器"""
    print("=== 测试交易信号生成器 ===")
    
    os.environ['GITHUB_ACTIONS'] = 'true'
    
    success, stdout, stderr = run_command(
        'python scripts/trading_signal_generator.py --count 3 --output signals.json --include-summary',
        cwd='/Users/guoyingcheng/claude_pro/smartwallex-hugo-new'
    )
    
    if success:
        print("✅ 交易信号生成成功")
        
        # 检查生成的文件
        signals_file = Path('/Users/guoyingcheng/claude_pro/smartwallex-hugo-new/signals.json')
        if signals_file.exists():
            with open(signals_file) as f:
                data = json.load(f)
            
            signals_count = len(data.get('signals', []))
            print(f"📊 生成了 {signals_count} 个交易信号")
            
            # 显示市场摘要
            summary = data.get('market_summary', {})
            print(f"🎯 市场情绪: {summary.get('market_sentiment', 'N/A')}")
            print(f"📈 波动性: {summary.get('volatility', 'N/A')}")
            print(f"📊 主导趋势: {summary.get('dominant_trend', 'N/A')}")
            
            return True, signals_count
        else:
            print("❌ 信号文件未生成")
            return False, 0
    else:
        print(f"❌ 信号生成失败: {stderr}")
        return False, 0

def test_telegram_sending():
    """测试Telegram消息发送"""
    print("\n=== 测试Telegram消息发送 ===")
    
    # 设置环境变量
    os.environ['TELEGRAM_BOT_TOKEN'] = '8209835379:AAEarEFcbfR8fDJMFw16A0h1MqWHliFTnYE'
    os.environ['TELEGRAM_CHANNEL_ID'] = '-1003168613592'
    
    # 测试连接
    success, stdout, stderr = run_command(
        'python scripts/telegram_sender.py --token "$TELEGRAM_BOT_TOKEN" --channel "$TELEGRAM_CHANNEL_ID" --message "🧪 完整流程测试" --test',
        cwd='/Users/guoyingcheng/claude_pro/smartwallex-hugo-new'
    )
    
    if success:
        print("✅ Telegram连接测试成功")
        return True
    else:
        print(f"❌ Telegram连接测试失败: {stderr}")
        return False

def test_signal_sending():
    """测试发送交易信号到Telegram"""
    print("\n=== 测试发送交易信号 ===")
    
    # 创建发送脚本（模拟工作流中的脚本）
    send_script = '''
import json
import sys
sys.path.append('scripts')
from telegram_sender import TelegramSender

def main():
    sender = TelegramSender(sys.argv[1], sys.argv[2])
    
    # 读取信号数据
    with open('signals.json', 'r') as f:
        data = json.load(f)
    
    # 直接发送每个信号，不发送汇总统计
    signals_sent = 0
    for signal in data['signals']:
        signal_msg = f"""📈 <b>{signal['signal']} Signal: {signal['symbol']}</b>

💰 <b>Entry:</b> {signal['entry_price']}
🛑 <b>Stop Loss:</b> {signal['stop_loss']}
🎯 <b>Take Profit:</b> {signal['take_profit']}
📊 <b>Confidence:</b> {signal['confidence']}
⚖️ <b>Risk/Reward:</b> {signal['risk_reward_ratio']}
📊 <b>RSI:</b> {signal['indicators']['rsi']} | <b>MACD:</b> {signal['indicators']['macd']}
⏰ <b>Timeframe:</b> {signal['timeframe']}
📝 <b>Condition:</b> {signal['market_condition']}"""
        
        if sender.send_message(signal_msg):
            signals_sent += 1
    
    print(f"✅ 已发送 {signals_sent} 个交易信号")
    return signals_sent > 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
'''
    
    # 保存脚本
    script_path = Path('/Users/guoyingcheng/claude_pro/smartwallex-hugo-new/test_send_signals.py')
    with open(script_path, 'w') as f:
        f.write(send_script)
    
    # 执行发送
    success, stdout, stderr = run_command(
        'python test_send_signals.py "$TELEGRAM_BOT_TOKEN" "$TELEGRAM_CHANNEL_ID"',
        cwd='/Users/guoyingcheng/claude_pro/smartwallex-hugo-new'
    )
    
    # 清理临时文件
    if script_path.exists():
        script_path.unlink()
    
    if success:
        print("✅ 交易信号发送成功")
        print(f"输出: {stdout}")
        return True
    else:
        print(f"❌ 交易信号发送失败: {stderr}")
        return False

def main():
    """主函数 - 运行完整流程测试"""
    print("🚀 开始完整工作流测试")
    print("=" * 50)
    
    # 1. 测试信号生成
    signals_success, signals_count = test_signal_generation()
    
    if not signals_success:
        print("\n❌ 工作流测试失败：信号生成失败")
        return False
    
    # 2. 测试Telegram连接
    telegram_success = test_telegram_sending()
    
    if not telegram_success:
        print("\n❌ 工作流测试失败：Telegram连接失败")
        return False
    
    # 3. 测试信号发送
    sending_success = test_signal_sending()
    
    if not sending_success:
        print("\n❌ 工作流测试失败：信号发送失败")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 完整工作流测试成功！")
    print(f"✅ 生成了 {signals_count} 个交易信号")
    print("✅ Telegram连接正常")
    print("✅ 信号发送功能正常")
    print("\n📱 请检查你的私人频道是否收到了测试信号")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)