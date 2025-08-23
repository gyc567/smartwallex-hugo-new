# GLM-4.5 API 日志系统使用文档

本文档介绍如何使用新增的 GLM-4.5 大模型调用日志系统。

## 功能概述

GLM 日志系统提供以下功能：

### 📊 自动日志记录
- ✅ **请求内容记录**：完整记录发送给GLM的提示词和参数
- ✅ **返回内容记录**：记录GLM返回的完整响应内容  
- ✅ **Token消耗统计**：精确记录输入、输出和总计Token使用量
- ✅ **错误日志**：记录API调用失败的详细错误信息
- ✅ **函数级统计**：按调用函数分类统计使用情况

### 📁 日志文件结构
```
logs/
├── glm_api_2025-08-23.log           # 标准日志文件（包含摘要信息）
└── glm_api_details_2025-08-23.jsonl # 详细日志文件（JSON格式）
```

## 使用方法

### 1. 自动记录（无需额外操作）

当运行 `crypto-project-analyzer.py` 时，所有 GLM API 调用会自动记录：

```bash
python crypto-project-analyzer.py
```

运行结束时会显示当日API使用统计：
```
🤖 GLM-4.5 API使用统计:
   ✅ 总调用次数: 9
   ✅ 成功调用: 9  
   ❌ 失败调用: 0
   🔢 消耗Token总数: 15,847
   📝 输入Token: 12,234
   📤 输出Token: 3,613
   📊 各功能调用统计:
      • chat_completions_create: 9次调用, 15847个tokens
```

### 2. 查看日志统计

使用 `view_glm_logs.py` 工具查看详细统计：

```bash
# 查看今日统计
python view_glm_logs.py --stats

# 查看指定日期统计
python view_glm_logs.py --stats --date 2025-08-22

# 列出所有可用日志日期
python view_glm_logs.py --list-dates
```

### 3. 查看详细日志

```bash
# 查看今日详细调用日志（最近10条）
python view_glm_logs.py --logs

# 查看更多日志条目
python view_glm_logs.py --logs --limit 20

# 查看指定日期的日志
python view_glm_logs.py --logs --date 2025-08-22

# 过滤特定函数的日志
python view_glm_logs.py --logs --function chat_completions_create
```

### 4. 导出数据

```bash
# 导出今日数据到CSV
python view_glm_logs.py --export-csv glm_logs_today.csv

# 导出指定日期数据
python view_glm_logs.py --export-csv logs_0822.csv --date 2025-08-22
```

## 日志内容详解

### 标准日志格式
```
2025-08-23 17:13:03,454 - GLM_API - INFO - API调用成功 - ai_analyze_project_quality: 消耗 1,245 tokens
```

### 详细日志格式（JSON）
```json
{
  "timestamp": "2025-08-23T17:13:03.454000",
  "function": "ai_analyze_project_quality", 
  "request": {
    "model": "glm-4.5",
    "messages": [
      {"role": "system", "content": "你是一个专业的区块链..."},
      {"role": "user", "content": "请分析以下加密货币项目..."}
    ],
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 2000
  },
  "response": {
    "success": true,
    "content": "{\"score\": 0.75, \"analysis\": \"该项目技术创新性较好...\"}",
    "error": null
  },
  "usage": {
    "prompt_tokens": 892,
    "completion_tokens": 353, 
    "total_tokens": 1245
  }
}
```

## 监控的函数

系统会记录以下三个核心AI分析函数的调用：

1. **`ai_analyze_project_quality`** - 项目质量评估
2. **`ai_generate_project_summary`** - 项目摘要生成  
3. **`ai_analyze_stars_and_forks`** - GitHub数据分析

## 统计指标说明

### Token统计
- **输入Token (prompt_tokens)**: 发送给GLM的文本内容消耗的token
- **输出Token (completion_tokens)**: GLM返回内容消耗的token
- **总Token (total_tokens)**: 输入 + 输出的总计

### 成本估算
根据智谱AI GLM-4.5的定价：
- 输入Token: ¥0.05/千tokens
- 输出Token: ¥0.05/千tokens

可以通过日志计算每日API成本。

## 故障排除

### 问题1: 日志文件不存在
```
❌ 找不到日期 2025-08-23 的日志文件
```
**解决方案**: 确认该日期是否运行过分析程序，可用 `--list-dates` 查看可用日期。

### 问题2: JSON解析错误
```
❌ 解析日志文件时出错: Expecting ',' delimiter
```
**解决方案**: 日志文件可能损坏，检查 `logs/` 目录下的文件完整性。

### 问题3: API调用失败记录
查看错误日志了解失败原因：
```bash
python view_glm_logs.py --logs | grep "❌"
```

## 文件管理

### 日志文件清理
日志文件会持续累积，建议定期清理：

```bash
# 删除30天前的日志文件
find logs/ -name "glm_api_*.log" -mtime +30 -delete
find logs/ -name "glm_api_details_*.jsonl" -mtime +30 -delete
```

### 备份重要日志
对于重要的分析日志，可以备份到其他位置：

```bash
# 备份指定月份的日志
tar -czf glm_logs_2025_08.tar.gz logs/glm_api*2025-08-*.log logs/glm_api_details*2025-08-*.jsonl
```

## 高级用法

### 编程接口
可以直接在Python代码中使用日志系统：

```python
from glm_logger import GLMLogger, GLMClientWrapper

# 创建日志记录器
logger = GLMLogger()

# 使用包装客户端
client = GLMClientWrapper(api_key="your_key", base_url="base_url", logger=logger)

# 调用会自动记录日志
completion = client.chat_completions_create(...)

# 获取统计信息
stats = logger.get_daily_stats()
print(f"今日消耗Token: {stats['total_tokens']}")
```

### 自定义日志目录
```python
# 指定自定义日志目录
logger = GLMLogger(log_dir="custom_logs")
```

## 技术实现

### 核心组件
1. **GLMLogger**: 核心日志记录器
2. **GLMClientWrapper**: OpenAI客户端包装器，自动记录API调用
3. **view_glm_logs.py**: 命令行日志查看工具

### 集成方式
- 修改 `crypto-project-analyzer.py` 使用 `GLMClientWrapper` 替代原生 `OpenAI` 客户端
- 在所有 `chat.completions.create` 调用处替换为 `chat_completions_create`
- 自动记录每次API调用的完整信息

---

*此文档随系统更新而更新，如有问题请查看代码注释或联系开发者。*