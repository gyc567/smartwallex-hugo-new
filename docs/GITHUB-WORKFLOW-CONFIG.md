# GitHub Workflows 配置说明

## 概述

本项目使用 GitHub Actions 自动化工作流程来实现每日加密货币项目分析和内容生成。主要包含以下工作流：

1. **Daily Crypto Analysis** - 每日加密货币项目分析
2. **Twitter Automation** - Twitter 自动化发布
3. **Test Setup** - 测试环境配置

## 主要工作流详解

### 1. Daily Crypto Analysis (`.github/workflows/daily-crypto-analysis.yml`)

#### 功能描述
每日自动分析 GitHub 上的热门加密货币项目，生成评测文章并发布到 Hugo 站点。

#### 触发条件
- **定时触发**: 每天 UTC 16:00 (北京时间 00:00)
- **手动触发**: 支持通过 GitHub Actions 界面手动运行

#### 工作流程
1. **环境准备**
   - 检出代码仓库
   - 设置 Python 3.11 环境
   - 缓存 Python 依赖
   - 安装依赖包

2. **代码质量检查**
   - 运行语法检查脚本
   - 验证 Python 模块导入

3. **Hugo 环境配置**
   - 安装最新版 Hugo (Extended)
   - 配置 Git 用户信息

4. **项目分析**
   - 运行加密货币项目分析器
   - 生成 Markdown 格式的评测文章

5. **内容发布**
   - 检查是否有新文章生成
   - 构建 Hugo 静态站点
   - 提交并推送更改

6. **结果汇总**
   - 生成执行摘要
   - 显示统计信息

#### 权限要求
```yaml
permissions:
  contents: write  # 允许写仓库内容
```

#### 环境变量
- `GITHUB_TOKEN`: GitHub API 访问令牌（自动提供）
- `GITHUB_ACTIONS`: 标识运行环境

### 2. Twitter Automation (`.github/workflows/twitter-automation.yml`)

#### 功能描述
自动化 Twitter 内容发布和管理。

#### 所需密钥
需要在 GitHub 仓库设置中配置以下 Secrets：
- `TWITTER_API_KEY`
- `TWITTER_API_SECRET`
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_ACCESS_TOKEN_SECRET`

### 3. Test Setup (`.github/workflows/test-setup.yml`)

#### 功能描述
验证项目配置和依赖环境。

## 配置要求

### 必需的文件结构
```
.github/
├── workflows/
│   ├── daily-crypto-analysis.yml
│   ├── twitter-automation.yml
│   └── test-setup.yml
└── scripts/
    ├── setup-secrets.js
    └── validate-secrets.js

scripts/
├── crypto-project-analyzer.py
├── check-syntax.py
├── requirements.txt
└── config.py

content/
└── posts/          # 生成的文章存放目录
```

### Python 依赖
```txt
requests>=2.28.0
python-dateutil>=2.8.0
```

### Hugo 要求
- Hugo Extended 版本
- 支持 TOML 前置元数据
- 自定义 shortcodes (如 alert)

## 安全配置

### GitHub Secrets 配置

#### 必需的 Secrets
1. **GITHUB_TOKEN** (自动提供)
   - 用途: GitHub API 访问
   - 权限: 读写仓库内容

2. **TWITTER_API_KEY** (需手动配置)
   - 用途: Twitter API 访问
   - 获取: Twitter Developer Portal

3. **TWITTER_API_SECRET** (需手动配置)
   - 用途: Twitter API 认证
   - 获取: Twitter Developer Portal

4. **TWITTER_ACCESS_TOKEN** (需手动配置)
   - 用途: Twitter 账户访问
   - 获取: Twitter Developer Portal

5. **TWITTER_ACCESS_TOKEN_SECRET** (需手动配置)
   - 用途: Twitter 账户认证
   - 获取: Twitter Developer Portal

#### 配置步骤
1. 进入 GitHub 仓库设置
2. 选择 "Secrets and variables" → "Actions"
3. 点击 "New repository secret"
4. 添加上述必需的 secrets

### 权限配置

#### 仓库权限
```yaml
permissions:
  contents: write    # 写入文件
  actions: read      # 读取 Actions
  checks: write      # 写入检查结果
```

#### Token 权限
确保 GITHUB_TOKEN 具有以下权限：
- Repository contents (write)
- Metadata (read)
- Pull requests (write)

## 监控和调试

### 日志查看
1. 进入 GitHub 仓库
2. 点击 "Actions" 标签
3. 选择对应的工作流运行记录
4. 查看详细日志

### 常见问题排查

#### 1. 权限错误
```
Error: Permission denied
```
**解决方案**: 检查 GITHUB_TOKEN 权限和仓库设置

#### 2. Python 依赖错误
```
ModuleNotFoundError: No module named 'requests'
```
**解决方案**: 检查 requirements.txt 文件和缓存配置

#### 3. Hugo 构建失败
```
Error: failed to extract shortcode
```
**解决方案**: 检查 shortcode 定义和模板文件

#### 4. Git 提交失败
```
Error: nothing to commit
```
**解决方案**: 正常情况，表示没有新内容生成

### 性能优化

#### 缓存策略
```yaml
- name: Cache Python dependencies
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

#### 条件执行
```yaml
- name: Build Hugo site
  if: steps.check_articles.outputs.new_articles > 0
```

## 自定义配置

### 修改执行时间
```yaml
schedule:
  # 修改 cron 表达式
  - cron: '0 8 * * *'  # UTC 8:00 (北京时间 16:00)
```

### 调整文章数量限制
在 `crypto-project-analyzer.py` 中修改：
```python
MAX_ARTICLES_PER_DAY = 5  # 每日最大文章数
```

### 自定义 Git 提交信息
```yaml
git commit -m "🤖 Auto: Custom message $(date +%Y-%m-%d)"
```

## 最佳实践

### 1. 错误处理
- 使用 `continue-on-error: true` 防止单步失败影响整个流程
- 添加 `if: always()` 确保摘要步骤总是执行

### 2. 资源管理
- 合理使用缓存减少构建时间
- 设置超时时间防止无限等待

### 3. 安全考虑
- 不在日志中输出敏感信息
- 使用 GitHub Secrets 管理密钥
- 定期轮换 API 密钥

### 4. 监控告警
- 设置工作流失败通知
- 监控 API 配额使用情况
- 定期检查生成内容质量

## 故障恢复

### 手动触发
如果自动执行失败，可以：
1. 进入 Actions 页面
2. 选择对应工作流
3. 点击 "Run workflow" 手动触发

### 回滚操作
如果需要回滚更改：
```bash
git revert <commit-hash>
git push
```

### 紧急停止
如果需要紧急停止工作流：
1. 进入正在运行的工作流
2. 点击 "Cancel workflow"

## 扩展功能

### 添加新的分析器
1. 在 `scripts/` 目录添加新脚本
2. 更新 `check-syntax.py` 包含新文件
3. 在工作流中添加执行步骤

### 集成其他服务
可以添加步骤集成：
- Slack 通知
- 邮件发送
- 数据库更新
- CDN 刷新

---

*最后更新: 2025-08-16*
*维护者: ERIC*