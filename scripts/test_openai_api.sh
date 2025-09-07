#!/bin/bash
# OpenAI兼容API连通性测试脚本
# 测试ModelScope的OpenAI兼容接口

set -e  # 遇到错误立即退出

# API配置
OPENAI_API_KEY="ms-c17a173f-e579-4352-9f74-fbf0e7ee08c8"
OPENAI_BASE_URL="https://api-inference.modelscope.cn/v1"

echo "🚀 OpenAI兼容API连通性测试"
echo "================================"
echo "🔑 API Key: ${OPENAI_API_KEY:0:12}..."
echo "🌐 Base URL: $OPENAI_BASE_URL"
echo "⏰ 测试时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 测试1: 获取模型列表
echo "📋 测试1: 获取可用模型列表"
echo "--------------------------------"

curl -s -X GET \
  "$OPENAI_BASE_URL/models" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" | \
  python3 -m json.tool 2>/dev/null || echo "❌ 模型列表获取失败或返回非JSON格式"

echo -e "\n"

# 测试2: 简单的聊天补全测试
echo "💬 测试2: Chat Completions API测试"
echo "--------------------------------"

# 构建请求JSON
cat > /tmp/chat_request.json << 'EOF'
{
  "model": "Qwen/Qwen2.5-Coder-32B-Instruct",
  "messages": [
    {
      "role": "system",
      "content": "你是一个专业的AI助手。请用简洁的中文回答问题。"
    },
    {
      "role": "user", 
      "content": "请简单介绍一下区块链技术的核心特点，控制在50字以内。"
    }
  ],
  "max_tokens": 100,
  "temperature": 0.7
}
EOF

echo "📤 发送请求到: $OPENAI_BASE_URL/chat/completions"
echo ""

# 执行聊天补全请求
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST \
  "$OPENAI_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d @/tmp/chat_request.json)

# 分离响应体和状态码
HTTP_CODE=$(echo "$RESPONSE" | tail -n1 | sed 's/.*HTTP_CODE://')
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')

echo "📥 HTTP状态码: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ API调用成功！"
    echo "📄 响应内容:"
    echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || {
        echo "响应体:"
        echo "$RESPONSE_BODY"
    }
    
    # 提取AI回复内容
    echo ""
    echo "🤖 AI回复内容:"
    echo "$RESPONSE_BODY" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    content = data['choices'][0]['message']['content']
    print('\"' + content + '\"')
except:
    print('无法解析AI回复')
" 2>/dev/null || echo "解析失败"

else
    echo "❌ API调用失败"
    echo "📄 错误响应:"
    echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"
fi

echo -e "\n"

# 测试3: 错误处理测试
echo "🔧 测试3: 错误处理测试（错误的API Key）"
echo "--------------------------------"

INVALID_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST \
  "$OPENAI_BASE_URL/chat/completions" \
  -H "Authorization: Bearer invalid-key-test" \
  -H "Content-Type: application/json" \
  -d '{"model": "test", "messages": [{"role": "user", "content": "test"}]}')

INVALID_HTTP_CODE=$(echo "$INVALID_RESPONSE" | tail -n1 | sed 's/.*HTTP_CODE://')
echo "📥 错误请求状态码: $INVALID_HTTP_CODE"

if [ "$INVALID_HTTP_CODE" != "200" ]; then
    echo "✅ 错误处理正常（拒绝了无效的API Key）"
else
    echo "⚠️ 错误处理异常（接受了无效的API Key）"
fi

echo -e "\n"

# 清理临时文件
rm -f /tmp/chat_request.json

# 测试总结
echo "📊 测试总结"
echo "================================"
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ OpenAI兼容API连通性测试通过"
    echo "✅ ModelScope接口工作正常"
    echo "✅ 可以正常用于LookOnChain工作流"
else
    echo "❌ API连通性测试失败"
    echo "❌ 请检查API Key或网络连接"
fi

echo ""
echo "🎯 测试完成时间: $(date '+%Y-%m-%d %H:%M:%S')"