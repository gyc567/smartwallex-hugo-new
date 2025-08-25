#!/bin/bash

# Hugo文章索引验证脚本
# 用于验证特定文章是否正确地被Hugo索引到各个系统文件中

echo "🔍 Hugo文章索引验证开始..."
echo "验证目标文章: aixbt-pendle-tvl-migration-analysis-2025-08-18"
echo "====================================================="

# 定义验证变量
TARGET_ARTICLE="aixbt-pendle-tvl-migration-analysis-2025-08-18"
TARGET_TITLE="Pendle协议TVL迁移分析"
BASE_DIR="/Users/guoyingcheng/claude_pro/smartwallex-hugo-new"
PUBLIC_DIR="$BASE_DIR/public"

# 验证结果数组
CHECKS=()

echo "📍 1. 验证HTML页面生成..."
if [ -f "$PUBLIC_DIR/posts/$TARGET_ARTICLE/index.html" ]; then
    echo "✅ HTML页面已生成: $TARGET_ARTICLE/index.html"
    CHECKS+=("HTML页面:✅")
else
    echo "❌ HTML页面未生成"
    CHECKS+=("HTML页面:❌")
fi

echo ""
echo "📍 2. 验证sitemap.xml索引..."
if grep -q "$TARGET_ARTICLE" "$PUBLIC_DIR/sitemap.xml"; then
    echo "✅ sitemap.xml 包含目标文章"
    CHECKS+=("sitemap.xml:✅")
else
    echo "❌ sitemap.xml 缺失目标文章"
    CHECKS+=("sitemap.xml:❌")
fi

echo ""
echo "📍 3. 验证index.json搜索索引..."
if grep -q "$TARGET_TITLE" "$PUBLIC_DIR/index.json"; then
    echo "✅ index.json 包含目标文章"
    CHECKS+=("index.json:✅")
else
    echo "❌ index.json 缺失目标文章"
    CHECKS+=("index.json:❌")
fi

echo ""
echo "📍 4. 验证主页文章列表..."
if grep -q "$TARGET_ARTICLE" "$PUBLIC_DIR/index.html"; then
    echo "✅ 主页列表包含目标文章"
    CHECKS+=("主页列表:✅")
else
    echo "❌ 主页列表缺失目标文章"
    CHECKS+=("主页列表:❌")
fi

echo ""
echo "📍 5. 验证posts列表页面..."
if grep -q "$TARGET_ARTICLE" "$PUBLIC_DIR/posts/index.html"; then
    echo "✅ posts列表包含目标文章"
    CHECKS+=("posts列表:✅")
else
    echo "❌ posts列表缺失目标文章"
    CHECKS+=("posts列表:❌")
fi

echo ""
echo "====================================================="
echo "📊 验证结果汇总:"
echo "====================================================="

SUCCESS_COUNT=0
TOTAL_COUNT=${#CHECKS[@]}

for check in "${CHECKS[@]}"; do
    echo "  $check"
    if [[ $check == *"✅"* ]]; then
        ((SUCCESS_COUNT++))
    fi
done

echo ""
echo "🎯 总体评分: $SUCCESS_COUNT/$TOTAL_COUNT ($(($SUCCESS_COUNT * 100 / $TOTAL_COUNT))%)"

if [ $SUCCESS_COUNT -eq $TOTAL_COUNT ]; then
    echo "🎉 所有检查项目通过！文章索引正常。"
    exit 0
elif [ $SUCCESS_COUNT -ge 3 ]; then
    echo "⚠️  部分检查项目通过，需要进一步修复。"
    exit 1
else
    echo "❌ 大部分检查项目失败，需要重新构建和修复。"
    exit 2
fi