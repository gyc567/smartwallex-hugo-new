#!/usr/bin/env python3
"""
项目历史记录管理工具
"""

import json
import os
import sys
from datetime import datetime

def load_history():
    """加载项目历史记录"""
    history_file = 'data/analyzed_projects.json'
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def show_stats():
    """显示统计信息"""
    history = load_history()
    if not history:
        print("❌ 未找到历史记录文件")
        return
    
    print("📊 项目分析统计")
    print("=" * 50)
    print(f"总分析项目数: {history.get('total_projects', 0)}")
    print(f"最后更新时间: {history.get('last_updated', 'Unknown')}")
    print()

def list_projects():
    """列出所有已分析的项目"""
    history = load_history()
    if not history:
        print("❌ 未找到历史记录文件")
        return
    
    projects = history.get('analyzed_projects', [])
    print(f"📚 已分析项目列表 (共 {len(projects)} 个)")
    print("=" * 50)
    
    for i, project in enumerate(projects, 1):
        print(f"{i:3d}. {project}")

def search_project(query):
    """搜索项目"""
    history = load_history()
    if not history:
        print("❌ 未找到历史记录文件")
        return
    
    projects = history.get('analyzed_projects', [])
    matches = [p for p in projects if query.lower() in p.lower()]
    
    print(f"🔍 搜索结果: '{query}' (找到 {len(matches)} 个)")
    print("=" * 50)
    
    for i, project in enumerate(matches, 1):
        print(f"{i:3d}. {project}")

def clear_history():
    """清空历史记录"""
    history_file = 'data/analyzed_projects.json'
    
    confirm = input("⚠️  确定要清空所有历史记录吗？(y/N): ")
    if confirm.lower() == 'y':
        if os.path.exists(history_file):
            os.remove(history_file)
            print("✅ 历史记录已清空")
        else:
            print("ℹ️  历史记录文件不存在")
    else:
        print("❌ 操作已取消")

def remove_project(project_name):
    """移除特定项目"""
    history_file = 'data/analyzed_projects.json'
    history = load_history()
    
    if not history:
        print("❌ 未找到历史记录文件")
        return
    
    projects = history.get('analyzed_projects', [])
    
    if project_name in projects:
        projects.remove(project_name)
        history['analyzed_projects'] = projects
        history['total_projects'] = len(projects)
        history['last_updated'] = datetime.now().isoformat()
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已移除项目: {project_name}")
    else:
        print(f"❌ 未找到项目: {project_name}")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("📋 项目历史记录管理工具")
        print("=" * 50)
        print("使用方法:")
        print("  python scripts/manage-history.py stats          # 显示统计信息")
        print("  python scripts/manage-history.py list           # 列出所有项目")
        print("  python scripts/manage-history.py search <query> # 搜索项目")
        print("  python scripts/manage-history.py remove <name>  # 移除项目")
        print("  python scripts/manage-history.py clear          # 清空历史")
        return
    
    command = sys.argv[1]
    
    if command == "stats":
        show_stats()
    elif command == "list":
        list_projects()
    elif command == "search":
        if len(sys.argv) < 3:
            print("❌ 请提供搜索关键词")
            return
        search_project(sys.argv[2])
    elif command == "remove":
        if len(sys.argv) < 3:
            print("❌ 请提供要移除的项目名")
            return
        remove_project(sys.argv[2])
    elif command == "clear":
        clear_history()
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == "__main__":
    main()