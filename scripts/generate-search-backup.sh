#!/bin/bash

# 生成备用搜索索引脚本
# 将 index.json 内容嵌入到 JavaScript 文件中作为备用方案

set -e

echo "🔄 生成备用搜索索引..."

# 检查 public/index.json 是否存在
if [ ! -f "public/index.json" ]; then
    echo "❌ public/index.json 文件不存在，请先运行 hugo 构建"
    exit 1
fi

# 读取 index.json 内容
INDEX_CONTENT=$(cat public/index.json)

# 创建备用搜索索引文件
cat > static/search-index.js << EOF
// 备用搜索索引数据 - 自动生成于 $(date)
window.searchIndexData = $INDEX_CONTENT;

// 获取搜索索引数据的统一接口
window.getSearchIndex = function() {
    // 优先尝试加载 index.json
    return fetch('/index.json')
        .then(response => {
            if (!response.ok) {
                throw new Error('index.json unavailable');
            }
            return response.json();
        })
        .catch(error => {
            console.warn('index.json 加载失败，使用备用搜索数据');
            return window.searchIndexData || [];
        });
};
EOF

echo "✅ 备用搜索索引已生成: static/search-index.js"
echo "📊 索引包含 $(echo "$INDEX_CONTENT" | jq '. | length') 篇文章"

# 复制到 public 目录
cp static/search-index.js public/search-index.js
echo "✅ 已复制到 public/search-index.js"