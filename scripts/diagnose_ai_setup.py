#!/usr/bin/env python3
"""
AI设置诊断脚本
诊断AI客户端初始化问题
"""

import os
import sys
from pathlib import Path

# 添加scripts目录到Python路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

def diagnose_environment():
    """诊断环境变量"""
    print("🔍 环境变量诊断:")
    
    api_key = os.environ.get('OPENAI_API_KEY', '')
    base_url = os.environ.get('OPENAI_BASE_URL', '')
    model = os.environ.get('OPENAI_MODEL', '')
    
    print(f"OPENAI_API_KEY: {'已设置' if api_key else '未设置'} ({len(api_key)} 字符)")
    print(f"OPENAI_BASE_URL: {base_url if base_url else '未设置'}")
    print(f"OPENAI_MODEL: {model if model else '未设置'}")
    
    return api_key, base_url, model

def diagnose_ai_client():
    """诊断AI客户端"""
    print("\n🔍 AI客户端诊断:")
    
    try:
        from openai_client import create_openai_client
        
        client = create_openai_client()
        if client:
            print("✅ AI客户端初始化成功")
            
            # 测试API调用
            try:
                response = client.chat_completions_create(
                    messages=[{"role": "user", "content": "测试"}],
                    max_tokens=10,
                    temperature=0.1
                )
                if response:
                    print("✅ API调用测试成功")
                    return True
                else:
                    print("❌ API调用测试失败")
                    return False
            except Exception as e:
                print(f"❌ API调用测试失败: {e}")
                return False
        else:
            print("❌ AI客户端初始化失败")
            return False
            
    except Exception as e:
        print(f"❌ AI客户端诊断失败: {e}")
        return False

def diagnose_ai_generator():
    """诊断AI生成器"""
    print("\n🔍 AI生成器诊断:")
    
    try:
        from ai_trading_signal_generator import AITradingSignalGenerator
        
        generator = AITradingSignalGenerator()
        print("✅ AI生成器初始化成功")
        
        # 检查字段
        print(f"专家提示词长度: {len(generator.expert_prompt)} 字符")
        print(f"支持币种数量: {len(generator.symbols)}")
        print(f"AI客户端已初始化: {generator.openai_client is not None}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI生成器诊断失败: {e}")
        return False

def diagnose_wrapper():
    """诊断包装器"""
    print("\n🔍 包装器诊断:")
    
    try:
        from trading_signal_generator_wrapper import TradingSignalGeneratorWrapper
        
        wrapper = TradingSignalGeneratorWrapper(use_ai=True)
        print(f"包装器AI模式: {wrapper.use_ai}")
        print(f"底层生成器类型: {type(wrapper.generator).__name__}")
        
        # 检查生成器属性
        if hasattr(wrapper.generator, 'expert_prompt'):
            print("✅ 生成器包含专家提示词")
        else:
            print("❌ 生成器不包含专家提示词")
        
        return wrapper.use_ai
        
    except Exception as e:
        print(f"❌ 包装器诊断失败: {e}")
        return False

def test_workflow():
    """测试完整工作流"""
    print("\n🔍 完整工作流测试:")
    
    try:
        from trading_signal_generator_wrapper import TradingSignalGeneratorWrapper
        
        wrapper = TradingSignalGeneratorWrapper(use_ai=True)
        
        if not wrapper.use_ai:
            print("❌ 包装器未使用AI模式，跳过工作流测试")
            return False
        
        signals = wrapper.generate_signals(1)
        print(f"生成信号数量: {len(signals)}")
        
        if signals:
            signal = signals[0]
            print(f"信号分析类型: {signal.get('analysis_type')}")
            print(f"信号数据源: {signal.get('data_source')}")
            print(f"AI分析长度: {len(signal.get('ai_analysis', ''))}")
            print(f"MCP分析: {signal.get('mcp_analysis', 'N/A')[:50]}...")
            
            # 验证是否为AI信号
            is_ai = (
                signal.get('analysis_type') == 'AI Expert' and
                'AI Model' in signal.get('data_source', '') and
                len(signal.get('ai_analysis', '')) > 100 and
                signal.get('mcp_analysis')
            )
            
            if is_ai:
                print("✅ 成功生成AI信号")
                return True
            else:
                print("❌ 生成的信号不是AI信号")
                return False
        else:
            print("❌ 未生成任何信号")
            return False
            
    except Exception as e:
        print(f"❌ 工作流测试失败: {e}")
        return False

def main():
    """主诊断函数"""
    print("🚀 AI设置完整诊断")
    print("="*50)
    
    # 运行诊断
    env_ok = diagnose_environment()
    client_ok = diagnose_ai_client()
    generator_ok = diagnose_ai_generator()
    wrapper_ok = diagnose_wrapper()
    workflow_ok = test_workflow()
    
    # 汇总结果
    print(f"\n{'='*50}")
    print("📊 诊断结果汇总:")
    
    results = [
        ("环境变量", env_ok),
        ("AI客户端", client_ok),
        ("AI生成器", generator_ok),
        ("包装器", wrapper_ok),
        ("完整工作流", workflow_ok)
    ]
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 所有诊断通过！")
        print("✅ AI系统完全正常工作")
        return 0
    else:
        print("\n⚠️  部分诊断失败")
        print("🔧 请检查上述错误信息")
        return 1

if __name__ == "__main__":
    exit(main())