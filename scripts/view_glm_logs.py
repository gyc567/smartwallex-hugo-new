#!/usr/bin/env python3
"""
GLM-4.5 API日志查看工具
用于查看和分析GLM API调用日志
"""

import json
import argparse
import datetime
import os
from typing import Dict, Any, List
from glm_logger import GLMLogger

def format_timestamp(timestamp_str: str) -> str:
    """格式化时间戳"""
    try:
        dt = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%H:%M:%S')
    except:
        return timestamp_str

def print_stats(stats: Dict[str, Any]):
    """打印统计信息"""
    print(f"\n📊 GLM-4.5 API调用统计 ({stats['date']})")
    print("=" * 50)
    
    if "error" in stats:
        print(f"❌ 错误: {stats['error']}")
        return
    
    print(f"总调用次数: {stats['total_calls']}")
    print(f"成功调用: {stats['successful_calls']}")
    print(f"失败调用: {stats['failed_calls']}")
    print(f"成功率: {(stats['successful_calls'] / max(1, stats['total_calls']) * 100):.1f}%")
    
    print(f"\n🔢 Token使用情况:")
    print(f"总Token消耗: {stats['total_tokens']:,}")
    print(f"输入Token: {stats['prompt_tokens']:,}")
    print(f"输出Token: {stats['completion_tokens']:,}")
    
    if stats['total_tokens'] > 0:
        avg_tokens = stats['total_tokens'] / max(1, stats['successful_calls'])
        print(f"平均每次调用Token: {avg_tokens:.1f}")
    
    print(f"\n📈 各功能调用统计:")
    if stats['functions']:
        for func_name, func_stats in stats['functions'].items():
            tokens = func_stats['tokens']
            calls = func_stats['calls']
            avg = tokens / max(1, calls)
            print(f"  • {func_name}: {calls}次调用, {tokens:,}个tokens (平均{avg:.1f}/次)")
    else:
        print("  无功能调用记录")
    
    if stats['errors']:
        print(f"\n❌ 错误记录 ({len(stats['errors'])}个):")
        for error in stats['errors'][-5:]:  # 只显示最近5个错误
            time_str = format_timestamp(error['timestamp'])
            print(f"  • {time_str} - {error['function']}: {error['error']}")

def print_detailed_logs(date: str, limit: int = 10, function_filter: str = None):
    """打印详细日志"""
    logger = GLMLogger()
    detail_log_file = os.path.join(logger.log_dir, f"glm_api_details_{date}.jsonl")
    
    if not os.path.exists(detail_log_file):
        print(f"❌ 找不到日期 {date} 的详细日志文件")
        return
    
    print(f"\n📋 详细调用日志 ({date})")
    print("=" * 80)
    
    count = 0
    try:
        with open(detail_log_file, 'r', encoding='utf-8') as f:
            logs = []
            for line in f:
                entry = json.loads(line.strip())
                if function_filter and function_filter not in entry['function']:
                    continue
                logs.append(entry)
            
            # 显示最近的日志
            for entry in logs[-limit:]:
                count += 1
                time_str = format_timestamp(entry['timestamp'])
                func_name = entry['function']
                success = "✅" if entry['response']['success'] else "❌"
                
                print(f"\n[{count}] {time_str} {success} {func_name}")
                
                # 显示请求信息
                req = entry['request']
                if req.get('messages'):
                    user_msg = ""
                    for msg in req['messages']:
                        if msg.get('role') == 'user':
                            user_msg = msg.get('content', '')[:100] + "..."
                            break
                    print(f"    📝 请求: {user_msg}")
                
                print(f"    🔧 参数: model={req.get('model', 'N/A')}, temp={req.get('temperature', 'N/A')}, max_tokens={req.get('max_tokens', 'N/A')}")
                
                # 显示响应信息
                if entry['response']['success']:
                    content = entry['response'].get('content', '')
                    print(f"    📤 响应: {content[:100]}...")
                else:
                    print(f"    ❌ 错误: {entry['response'].get('error', 'Unknown error')}")
                
                # 显示Token使用
                usage = entry.get('usage', {})
                if usage:
                    print(f"    🔢 Tokens: {usage.get('total_tokens', 0)} (输入:{usage.get('prompt_tokens', 0)}, 输出:{usage.get('completion_tokens', 0)})")
                
    except Exception as e:
        print(f"❌ 读取日志文件时出错: {e}")

def list_available_dates():
    """列出可用的日志日期"""
    logger = GLMLogger()
    if not os.path.exists(logger.log_dir):
        print("❌ 日志目录不存在")
        return
    
    print("📅 可用的日志日期:")
    log_files = [f for f in os.listdir(logger.log_dir) if f.startswith('glm_api_details_') and f.endswith('.jsonl')]
    
    if not log_files:
        print("  无可用日志文件")
        return
    
    dates = []
    for filename in log_files:
        date_part = filename.replace('glm_api_details_', '').replace('.jsonl', '')
        dates.append(date_part)
    
    dates.sort(reverse=True)
    for date in dates:
        size = os.path.getsize(os.path.join(logger.log_dir, f'glm_api_details_{date}.jsonl'))
        print(f"  • {date} ({size} bytes)")

def export_to_csv(date: str, output_file: str = None):
    """导出日志到CSV文件"""
    import csv
    
    logger = GLMLogger()
    detail_log_file = os.path.join(logger.log_dir, f"glm_api_details_{date}.jsonl")
    
    if not os.path.exists(detail_log_file):
        print(f"❌ 找不到日期 {date} 的日志文件")
        return
    
    if not output_file:
        output_file = f"glm_api_logs_{date}.csv"
    
    try:
        with open(detail_log_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            
            writer = csv.writer(outfile)
            writer.writerow([
                'timestamp', 'function', 'success', 'model', 'temperature', 
                'max_tokens', 'prompt_tokens', 'completion_tokens', 'total_tokens', 
                'request_content', 'response_content', 'error'
            ])
            
            for line in infile:
                entry = json.loads(line.strip())
                
                # 提取用户输入内容
                request_content = ""
                for msg in entry['request'].get('messages', []):
                    if msg.get('role') == 'user':
                        request_content = msg.get('content', '')[:200]
                        break
                
                response_content = entry['response'].get('content', '')[:200]
                error = entry['response'].get('error', '')
                usage = entry.get('usage', {})
                
                writer.writerow([
                    entry['timestamp'],
                    entry['function'],
                    entry['response']['success'],
                    entry['request'].get('model', ''),
                    entry['request'].get('temperature', ''),
                    entry['request'].get('max_tokens', ''),
                    usage.get('prompt_tokens', 0),
                    usage.get('completion_tokens', 0),
                    usage.get('total_tokens', 0),
                    request_content,
                    response_content,
                    error
                ])
        
        print(f"✅ 已导出日志到: {output_file}")
        
    except Exception as e:
        print(f"❌ 导出CSV时出错: {e}")

def main():
    parser = argparse.ArgumentParser(description='GLM-4.5 API日志查看工具')
    parser.add_argument('--date', '-d', help='查看指定日期的日志 (YYYY-MM-DD)，默认为今天')
    parser.add_argument('--stats', '-s', action='store_true', help='显示统计信息')
    parser.add_argument('--logs', '-l', action='store_true', help='显示详细日志')
    parser.add_argument('--limit', type=int, default=10, help='限制显示的日志条数，默认10')
    parser.add_argument('--function', '-f', help='过滤指定函数的日志')
    parser.add_argument('--list-dates', action='store_true', help='列出所有可用的日志日期')
    parser.add_argument('--export-csv', help='导出到CSV文件')
    
    args = parser.parse_args()
    
    if args.list_dates:
        list_available_dates()
        return
    
    # 确定要查看的日期
    if args.date:
        target_date = args.date
    else:
        target_date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    logger = GLMLogger()
    
    # 显示统计信息
    if args.stats or (not args.logs and not args.export_csv):
        stats = logger.get_daily_stats(target_date)
        print_stats(stats)
    
    # 显示详细日志
    if args.logs:
        print_detailed_logs(target_date, args.limit, args.function)
    
    # 导出CSV
    if args.export_csv:
        export_to_csv(target_date, args.export_csv)

if __name__ == "__main__":
    main()