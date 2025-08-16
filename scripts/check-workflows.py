#!/usr/bin/env python3
"""
GitHub Actions 工作流状态检查工具
"""

import requests
import json
import os
from datetime import datetime, timedelta

def check_workflow_status():
    """检查GitHub Actions工作流状态"""
    
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("⚠️  未设置GITHUB_TOKEN环境变量")
        return
    
    # 这里需要替换为实际的仓库信息
    owner = "your-username"  # 替换为实际用户名
    repo = "smartwallex-hugo"  # 替换为实际仓库名
    
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    print("🔍 检查GitHub Actions工作流状态...")
    print("=" * 50)
    
    # 获取工作流列表
    workflows_url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows"
    
    try:
        response = requests.get(workflows_url, headers=headers)
        if response.status_code != 200:
            print(f"❌ 获取工作流列表失败: {response.status_code}")
            return
        
        workflows = response.json()['workflows']
        
        for workflow in workflows:
            workflow_name = workflow['name']
            workflow_id = workflow['id']
            state = workflow['state']
            
            print(f"\n📋 工作流: {workflow_name}")
            print(f"   状态: {'✅ 活跃' if state == 'active' else '❌ 非活跃'}")
            
            # 获取最近的运行记录
            runs_url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
            runs_response = requests.get(f"{runs_url}?per_page=5", headers=headers)
            
            if runs_response.status_code == 200:
                runs = runs_response.json()['workflow_runs']
                
                if runs:
                    latest_run = runs[0]
                    status = latest_run['status']
                    conclusion = latest_run['conclusion']
                    created_at = datetime.fromisoformat(latest_run['created_at'].replace('Z', '+00:00'))
                    
                    print(f"   最近运行: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   运行状态: {get_status_emoji(status, conclusion)} {status}")
                    if conclusion:
                        print(f"   运行结果: {get_conclusion_emoji(conclusion)} {conclusion}")
                    
                    # 显示最近5次运行的统计
                    success_count = sum(1 for run in runs if run['conclusion'] == 'success')
                    failure_count = sum(1 for run in runs if run['conclusion'] == 'failure')
                    
                    print(f"   最近5次: ✅ {success_count} 成功, ❌ {failure_count} 失败")
                else:
                    print("   最近运行: 无运行记录")
            else:
                print(f"   ⚠️  获取运行记录失败: {runs_response.status_code}")
    
    except Exception as e:
        print(f"❌ 检查失败: {e}")

def get_status_emoji(status, conclusion):
    """获取状态表情符号"""
    if status == 'completed':
        if conclusion == 'success':
            return '✅'
        elif conclusion == 'failure':
            return '❌'
        elif conclusion == 'cancelled':
            return '⏹️'
        else:
            return '⚠️'
    elif status == 'in_progress':
        return '🔄'
    elif status == 'queued':
        return '⏳'
    else:
        return '❓'

def get_conclusion_emoji(conclusion):
    """获取结论表情符号"""
    emoji_map = {
        'success': '✅',
        'failure': '❌',
        'cancelled': '⏹️',
        'skipped': '⏭️',
        'timed_out': '⏰',
        'action_required': '🔔'
    }
    return emoji_map.get(conclusion, '❓')

def show_usage():
    """显示使用说明"""
    print("📋 GitHub Actions 工作流状态检查工具")
    print("=" * 50)
    print("使用方法:")
    print("1. 设置环境变量: export GITHUB_TOKEN=your_token")
    print("2. 修改脚本中的owner和repo变量")
    print("3. 运行: python scripts/check-workflows.py")
    print()
    print("功能:")
    print("- 检查所有工作流的状态")
    print("- 显示最近的运行记录")
    print("- 统计成功/失败次数")

if __name__ == "__main__":
    if not os.getenv('GITHUB_TOKEN'):
        show_usage()
    else:
        check_workflow_status()