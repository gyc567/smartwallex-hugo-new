# TradingView 图表分析系统

## 功能概述

基于TradingView链接的BTC技术分析系统，结合传统图表分析和斐波那契理论，提供智能交易建议。

## 核心功能

- **URL解析**：解析TradingView图表链接
- **数据获取**：从多个API源获取K线数据
- **技术分析**：传统技术指标计算
- **斐波那契分析**：回撤位和目标位计算
- **AI分析**：集成GLM-4.5智能决策
- **报告生成**：生成Hugo格式的分析文章

## 目录结构

```
TradingView/
├── src/                    # 源代码
│   ├── __init__.py
│   ├── url_parser.py      # URL解析器
│   ├── data_fetcher.py    # 数据获取
│   ├── technical_analyzer.py  # 技术分析
│   ├── fibonacci_analyzer.py  # 斐波那契分析
│   ├── ai_analyst.py      # AI分析
│   └── report_generator.py    # 报告生成
├── config/                # 配置文件
│   ├── __init__.py
│   ├── settings.py        # 基础配置
│   └── api_config.py      # API配置
├── tests/                 # 测试文件
├── logs/                  # 日志文件
├── requirements.txt       # Python依赖
└── main.py               # 主入口程序
```

## 使用方法

```bash
# 安装依赖
pip install -r requirements.txt

# 分析TradingView图表
python main.py --url "https://www.tradingview.com/chart/xxx/?symbol=BTCUSDT&interval=4h"

# 生成Hugo文章
python main.py --url "tradingview_url" --generate-article
```

## 环境配置

复制 `.env.example` 到 `.env` 并配置：
- GLM_API_KEY: 智谱AI API密钥
- API配置: 交易所API密钥（可选）