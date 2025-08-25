#!/bin/bash

# 自动发布脚本
# 运行项目分析器，生成文章，构建网站并推送到GitHub

set -e  # 遇到错误立即退出

echo "🚀 开始自动化内容生成和发布流程..."

# 检查是否在正确的目录
if [ ! -f "hugo.toml" ]; then
    echo "❌ 错误: 请在Hugo项目根目录运行此脚本"
    exit 1
fi

# 创建日志目录
mkdir -p logs
LOG_FILE="logs/auto-publish-$(date +%Y%m%d-%H%M%S).log"

echo "📝 日志文件: $LOG_FILE"

# 记录开始时间
echo "开始时间: $(date)" | tee -a "$LOG_FILE"

# 1. 运行Python分析器
echo "🔍 运行加密货币项目分析器..." | tee -a "$LOG_FILE"
if python3 scripts/crypto-project-analyzer.py >> "$LOG_FILE" 2>&1; then
    echo "✅ 项目分析完成" | tee -a "$LOG_FILE"
else
    echo "❌ 项目分析失败，查看日志: $LOG_FILE" | tee -a "$LOG_FILE"
    exit 1
fi

# 2. 检查是否有新文章生成
NEW_ARTICLES=$(find content/posts -name "*$(date +%Y-%m-%d)*" -type f | wc -l)
echo "📊 今日生成文章数量: $NEW_ARTICLES" | tee -a "$LOG_FILE"

if [ "$NEW_ARTICLES" -eq 0 ]; then
    echo "ℹ️  今日无新文章生成，退出流程" | tee -a "$LOG_FILE"
    exit 0
fi

# 3. 构建Hugo网站
echo "🏗️  构建Hugo网站..." | tee -a "$LOG_FILE"
if hugo --cleanDestinationDir --minify >> "$LOG_FILE" 2>&1; then
    echo "✅ 网站构建完成" | tee -a "$LOG_FILE"
else
    echo "❌ 网站构建失败，查看日志: $LOG_FILE" | tee -a "$LOG_FILE"
    exit 1
fi

# 3.1 生成备用搜索索引
echo "🔍 生成备用搜索索引..." | tee -a "$LOG_FILE"
if ./scripts/generate-search-backup.sh >> "$LOG_FILE" 2>&1; then
    echo "✅ 备用搜索索引生成完成" | tee -a "$LOG_FILE"
else
    echo "⚠️  备用搜索索引生成失败，但不影响主要流程" | tee -a "$LOG_FILE"
fi

# 4. Git操作
echo "📤 提交更改到Git..." | tee -a "$LOG_FILE"

# 添加所有更改
git add . >> "$LOG_FILE" 2>&1

# 检查是否有更改需要提交
if git diff --staged --quiet; then
    echo "ℹ️  没有更改需要提交" | tee -a "$LOG_FILE"
    exit 0
fi

# 生成提交信息
COMMIT_MSG="Auto-generated: Daily crypto project reviews for $(date +%Y-%m-%d)"
echo "📝 提交信息: $COMMIT_MSG" | tee -a "$LOG_FILE"

# 提交更改
if git commit -m "$COMMIT_MSG" >> "$LOG_FILE" 2>&1; then
    echo "✅ Git提交完成" | tee -a "$LOG_FILE"
else
    echo "❌ Git提交失败，查看日志: $LOG_FILE" | tee -a "$LOG_FILE"
    exit 1
fi

# 推送到远程仓库
echo "🚀 推送到GitHub..." | tee -a "$LOG_FILE"
if git push origin master >> "$LOG_FILE" 2>&1; then
    echo "✅ 推送完成" | tee -a "$LOG_FILE"
else
    echo "❌ 推送失败，查看日志: $LOG_FILE" | tee -a "$LOG_FILE"
    exit 1
fi

# 记录结束时间
echo "结束时间: $(date)" | tee -a "$LOG_FILE"
echo "🎉 自动化发布流程完成！" | tee -a "$LOG_FILE"

# 显示生成的文章
echo ""
echo "📚 今日生成的文章:"
find content/posts -name "*$(date +%Y-%m-%d)*" -type f -exec basename {} \;