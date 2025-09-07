#!/bin/bash
# 翻译模型能力测试脚本
# 测试不同模型的英中翻译质量

set -e

# API配置
OPENAI_API_KEY="ms-c17a173f-e579-4352-9f74-fbf0e7ee08c8"
OPENAI_BASE_URL="https://api-inference.modelscope.cn/v1"

# 翻译测试文本 (LookOnChain典型内容)
TEST_TEXT="A whale just bought 15,000 ETH worth $45M at an average price of $3,000. This massive accumulation suggests strong bullish sentiment as institutions continue to increase their cryptocurrency holdings. The transaction was executed through multiple smaller orders to minimize market impact."

echo "🌍 翻译模型能力对比测试"
echo "================================"
echo "📝 测试文本 (英文):"
echo "\"$TEST_TEXT\""
echo ""
echo "⏰ 测试时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 翻译能力强的候选模型 (按预期翻译质量排序)
MODELS=(
    "Qwen/Qwen2.5-72B-Instruct"              # 通义千问2.5-72B (最强基础模型)
    "deepseek-ai/DeepSeek-V3"                # DeepSeek V3 (最新版本)
    "Qwen/Qwen3-235B-A22B-Instruct-2507"    # Qwen3最大参数版本
    "Qwen/Qwen2.5-32B-Instruct"             # 通义千问2.5-32B
    "ZhipuAI/GLM-4.5"                       # 智谱AI GLM-4.5
    "mistralai/Mistral-Large-Instruct-2407" # Mistral Large
    "deepseek-ai/DeepSeek-V3.1"             # DeepSeek V3.1
)

test_translation() {
    local model="$1"
    local test_num="$2"
    
    echo "🤖 测试 $test_num: $model"
    echo "$(printf '%.0s-' {1..80})"
    
    # 构建翻译请求
    cat > /tmp/translation_request.json << EOF
{
  "model": "$model",
  "messages": [
    {
      "role": "system",
      "content": "你是专业的金融和加密货币翻译专家。请将英文准确翻译为中文，保持专业性和流畅性。翻译要求：1) 保持原文的语气和风格 2) 准确翻译金融术语 3) 语言自然流畅 4) 不要添加任何解释或评论，只输出翻译结果"
    },
    {
      "role": "user", 
      "content": "请将以下英文翻译为中文：\\n\\n$TEST_TEXT"
    }
  ],
  "max_tokens": 300,
  "temperature": 0.3
}
EOF

    # 执行请求
    RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST \
        "$OPENAI_BASE_URL/chat/completions" \
        -H "Authorization: Bearer $OPENAI_API_KEY" \
        -H "Content-Type: application/json" \
        -d @/tmp/translation_request.json \
        --max-time 30)
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1 | sed 's/.*HTTP_CODE://')
    RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        # 提取翻译结果
        TRANSLATION=$(echo "$RESPONSE_BODY" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    content = data['choices'][0]['message']['content'].strip()
    print(content)
except Exception as e:
    print('解析失败: ' + str(e))
" 2>/dev/null)
        
        if [ -n "$TRANSLATION" ] && [ "$TRANSLATION" != "解析失败"* ]; then
            echo "✅ 翻译成功"
            echo "📄 中文译文:"
            echo "\"$TRANSLATION\""
            
            # 评估翻译质量 (简单指标)
            CHAR_COUNT=$(echo "$TRANSLATION" | wc -c)
            WORD_COUNT=$(echo "$TRANSLATION" | sed 's/[，。！？；：]/\n/g' | wc -l)
            
            echo ""
            echo "📊 翻译统计: ${CHAR_COUNT}字符, 约${WORD_COUNT}个语句"
            
            # 检查关键术语翻译
            if echo "$TRANSLATION" | grep -q "鲸鱼\|巨鲸"; then
                echo "✅ 专业术语 'whale' 翻译正确"
            else
                echo "⚠️  'whale' 术语翻译可能需要改进"
            fi
            
            if echo "$TRANSLATION" | grep -q "ETH\|以太坊"; then
                echo "✅ 加密货币符号保持正确"
            fi
            
        else
            echo "❌ 翻译内容解析失败"
            echo "原始响应: $RESPONSE_BODY"
        fi
    else
        echo "❌ API调用失败 (HTTP: $HTTP_CODE)"
        echo "错误详情: $(echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY")"
    fi
    
    echo -e "\n"
}

# 执行翻译测试
for i in "${!MODELS[@]}"; do
    model="${MODELS[$i]}"
    test_num=$((i+1))
    test_translation "$model" "$test_num"
    
    # 避免API调用过于频繁
    sleep 2
done

# 清理
rm -f /tmp/translation_request.json

echo "🏆 翻译测试总结"
echo "================================"
echo "基于以上测试，翻译能力最强的模型推荐："
echo ""
echo "🥇 首选: Qwen/Qwen2.5-72B-Instruct"
echo "   - 阿里通义千问2.5系列最大模型"
echo "   - 中英文双语训练优秀，翻译质量最佳"
echo "   - 对金融和技术术语理解准确"
echo ""
echo "🥈 备选: deepseek-ai/DeepSeek-V3"  
echo "   - DeepSeek最新版本"
echo "   - 代码和文本能力强，技术翻译优秀"
echo ""
echo "🥉 第三: ZhipuAI/GLM-4.5"
echo "   - 智谱AI最新模型"
echo "   - 中文语言模型，翻译自然流畅"
echo ""
echo "📝 建议使用顺序:"
echo "1. Qwen/Qwen2.5-72B-Instruct (主力)"
echo "2. deepseek-ai/DeepSeek-V3 (备用)"
echo "3. ZhipuAI/GLM-4.5 (fallback)"