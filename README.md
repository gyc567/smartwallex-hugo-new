# Hugo博客网站

一个功能完整的Hugo静态网站，包含搜索、点赞、SEO优化和广告集成功能。

## 功能特色

- ✅ **站内搜索**: 实时搜索文章内容、标题和标签
- ✅ **文章点赞**: 用户可以为文章点赞，数据保存在本地
- ✅ **SEO优化**: 完整的meta标签、Open Graph、结构化数据
- ✅ **广告集成**: 支持Monetag广告平台，多个广告位
- ✅ **响应式设计**: 适配桌面和移动设备
- ✅ **现代化UI**: 简洁美观的用户界面

## 快速开始

### 1. 安装Hugo
```bash
# macOS
brew install hugo

# 或下载二进制文件
# https://github.com/gohugoio/hugo/releases
```

### 2. 启动开发服务器
```bash
hugo server -D
```

### 3. 构建生产版本
```bash
hugo
```

## 配置说明

### 基础配置
编辑 `hugo.toml` 文件：

```toml
baseURL = 'https://your-domain.com/'
title = '你的网站标题'

[params]
  description = "网站描述"
  author = "作者姓名"
  monetagId = "YOUR_MONETAG_ID"  # 替换为你的Monetag ID
```

### 广告配置
1. 注册Monetag账户
2. 获取你的发布商ID
3. 在 `hugo.toml` 中设置 `monetagId`
4. 在布局文件中替换广告位ID

## 内容管理

### 创建新文章
```bash
hugo new posts/my-article.md
```

### 文章前置数据格式
```toml
+++
title = '文章标题'
date = '2024-08-14T10:00:00+08:00'
draft = false
description = '文章描述'
tags = ['标签1', '标签2']
categories = ['分类']
+++
```

## 目录结构

```
├── archetypes/          # 内容模板
├── content/             # 网站内容
│   ├── posts/          # 博客文章
│   └── about.md        # 关于页面
├── layouts/             # HTML模板
│   ├── _default/       # 默认模板
│   └── partials/       # 部分模板
├── static/              # 静态文件
│   ├── css/            # 样式文件
│   └── js/             # JavaScript文件
└── hugo.toml           # 配置文件
```

## 自定义

### 修改样式
编辑 `static/css/style.css` 文件来自定义网站外观。

### 添加新功能
- 在 `layouts/` 目录中修改HTML模板
- 在 `static/js/` 目录中添加JavaScript功能

## 部署

### 静态托管
生成的网站在 `public/` 目录中，可以部署到：
- Netlify
- Vercel
- GitHub Pages
- 任何静态文件托管服务

### 自动部署
可以设置GitHub Actions或其他CI/CD工具进行自动部署。

## 许可证

MIT License