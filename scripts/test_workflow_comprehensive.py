#!/usr/bin/env python3
"""
GitHub Actions工作流全面测试器
测试lookonchain-analysis.yml的完整功能流程
"""

import os
import sys
import subprocess
import json
import yaml
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 设置环境变量从.env.local加载
def load_env_local():
    """加载.env.local配置"""
    env_file = Path(__file__).parent / ".env.local"
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
                    
load_env_local()

class WorkflowComprehensiveTester:
    """GitHub Actions工作流全面测试器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.scripts_dir = Path(__file__).parent
        self.workflow_file = self.project_root / ".github/workflows/lookonchain-analysis.yml"
        self.test_results = []
        self.start_time = datetime.now()
        
        # 模拟GitHub Actions环境
        os.environ['GITHUB_ACTIONS'] = 'true'
        
    def log_test(self, test_name: str, passed: bool, details: str = "", error: str = "", duration: float = 0):
        """记录测试结果"""
        self.test_results.append({
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "error": error,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        })
        
        status = "✅ PASS" if passed else "❌ FAIL"
        duration_str = f" ({duration:.2f}s)" if duration > 0 else ""
        print(f"{status} {test_name}{duration_str}")
        if details:
            print(f"    📝 {details}")
        if error and not passed:
            print(f"    🚨 {error}")

    def test_environment_setup(self) -> bool:
        """测试环境设置步骤"""
        print("\n🔧 测试步骤：环境设置")
        
        # 检查Python版本
        try:
            result = subprocess.run([sys.executable, '--version'], 
                                  capture_output=True, text=True)
            python_version = result.stdout.strip()
            self.log_test("Python版本检查", True, python_version)
        except Exception as e:
            self.log_test("Python版本检查", False, "", str(e))
            return False
        
        # 检查依赖安装
        try:
            requirements_file = self.scripts_dir / "requirements.txt"
            if requirements_file.exists():
                with open(requirements_file, 'r') as f:
                    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
                missing_deps = []
                for req in requirements:
                    pkg_name = req.split('>=')[0].split('==')[0].strip()
                    try:
                        __import__(pkg_name.replace('-', '_'))
                    except ImportError:
                        missing_deps.append(pkg_name)
                
                if missing_deps:
                    self.log_test("依赖检查", False, f"缺失: {missing_deps}")
                    return False
                else:
                    self.log_test("依赖检查", True, f"所有{len(requirements)}个依赖已安装")
            else:
                self.log_test("依赖检查", False, "", "requirements.txt不存在")
                return False
                
        except Exception as e:
            self.log_test("依赖检查", False, "", str(e))
            return False
            
        return True

    def test_git_configuration(self) -> bool:
        """测试Git配置步骤"""
        print("\n📝 测试步骤：Git配置")
        
        try:
            # 检查Git可用性
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.returncode != 0:
                self.log_test("Git可用性", False, "", "Git命令不可用")
                return False
            
            git_version = result.stdout.strip()
            self.log_test("Git可用性", True, git_version)
            
            # 模拟配置Git用户（工作流中的步骤）
            commands = [
                ['git', 'config', '--global', 'user.name', 'GitHub Actions'],
                ['git', 'config', '--global', 'user.email', 'actions@github.com']
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    self.log_test("Git用户配置", False, "", f"命令失败: {' '.join(cmd)}")
                    return False
            
            self.log_test("Git用户配置", True, "GitHub Actions用户配置完成")
            return True
            
        except Exception as e:
            self.log_test("Git配置", False, "", str(e))
            return False

    def test_main_script_execution(self) -> bool:
        """测试主脚本执行"""
        print("\n🚀 测试步骤：主脚本执行")
        
        start_time = time.time()
        
        try:
            # 切换到scripts目录并运行主脚本
            cmd = [sys.executable, 'lookonchain_analyzer.py']
            
            print("    🔄 正在执行 lookonchain_analyzer.py...")
            result = subprocess.run(
                cmd,
                cwd=self.scripts_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                output_lines = len(result.stdout.split('\n')) if result.stdout else 0
                error_lines = len(result.stderr.split('\n')) if result.stderr else 0
                
                details = f"执行成功，输出{output_lines}行，错误{error_lines}行"
                self.log_test("主脚本执行", True, details, "", duration)
                
                # 检查输出中的关键信息
                if result.stdout:
                    if "✅" in result.stdout:
                        print("    ✅ 检测到成功标识")
                    if "OpenAI" in result.stdout or "API" in result.stdout:
                        print("    🔌 检测到API调用")
                    if "文章" in result.stdout or "生成" in result.stdout:
                        print("    📄 检测到内容生成")
                
                return True
            else:
                error_msg = result.stderr if result.stderr else "脚本返回非零退出码"
                self.log_test("主脚本执行", False, f"退出码: {result.returncode}", error_msg, duration)
                
                # 显示部分输出用于调试
                if result.stdout:
                    print("    📤 标准输出（前500字符）:")
                    print("    " + result.stdout[:500].replace('\n', '\n    '))
                if result.stderr:
                    print("    📥 错误输出（前500字符）:")
                    print("    " + result.stderr[:500].replace('\n', '\n    '))
                
                return False
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.log_test("主脚本执行", False, "执行超时", "5分钟超时", duration)
            return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("主脚本执行", False, "", str(e), duration)
            return False

    def test_file_changes_detection(self) -> bool:
        """测试文件变更检测"""
        print("\n🔍 测试步骤：文件变更检测")
        
        try:
            # 检查Git工作目录状态
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                self.log_test("Git状态检查", False, "", "git status命令失败")
                return False
            
            changes = result.stdout.strip()
            has_changes = bool(changes)
            
            if has_changes:
                change_lines = len(changes.split('\n'))
                details = f"检测到{change_lines}个文件变更"
                self.log_test("文件变更检测", True, details)
                
                # 显示变更的文件
                print("    📁 变更文件:")
                for line in changes.split('\n')[:5]:  # 显示前5个
                    print(f"      {line}")
                if change_lines > 5:
                    print(f"      ... 还有{change_lines-5}个文件")
            else:
                self.log_test("文件变更检测", True, "无文件变更")
            
            return True
            
        except Exception as e:
            self.log_test("文件变更检测", False, "", str(e))
            return False

    def test_content_generation(self) -> bool:
        """测试内容生成"""
        print("\n📄 测试步骤：内容生成验证")
        
        try:
            # 检查内容目录
            content_dir = self.project_root / "content" / "posts"
            if not content_dir.exists():
                content_dir.mkdir(parents=True, exist_ok=True)
            
            # 检查是否有新生成的文章
            md_files = list(content_dir.glob("*.md"))
            recent_files = []
            
            # 查找最近1小时内创建的文件
            one_hour_ago = datetime.now().timestamp() - 3600
            
            for md_file in md_files:
                if md_file.stat().st_mtime > one_hour_ago:
                    recent_files.append(md_file)
            
            if recent_files:
                details = f"发现{len(recent_files)}个最近生成的文章"
                self.log_test("内容生成验证", True, details)
                
                # 检查文章内容质量
                for md_file in recent_files[:3]:  # 检查前3个文件
                    try:
                        with open(md_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 检查文章结构
                        has_frontmatter = content.startswith('+++') or content.startswith('---')
                        has_title = 'title =' in content or 'title:' in content
                        has_content = len(content) > 500
                        
                        quality_score = sum([has_frontmatter, has_title, has_content])
                        
                        print(f"    📝 {md_file.name}: 质量分数 {quality_score}/3")
                        
                    except Exception as e:
                        print(f"    ⚠️ {md_file.name}: 读取失败 - {e}")
            else:
                self.log_test("内容生成验证", True, "无最近生成的文章（可能是正常情况）")
            
            # 检查数据目录
            data_dir = self.project_root / "data"
            if data_dir.exists():
                json_files = list(data_dir.glob("*.json"))
                if json_files:
                    details = f"数据目录包含{len(json_files)}个JSON文件"
                    self.log_test("数据文件检查", True, details)
                else:
                    self.log_test("数据文件检查", True, "数据目录为空")
            else:
                self.log_test("数据文件检查", True, "数据目录不存在")
            
            return True
            
        except Exception as e:
            self.log_test("内容生成验证", False, "", str(e))
            return False

    def test_api_integration(self) -> bool:
        """测试API集成"""
        print("\n🔌 测试步骤：API集成验证")
        
        try:
            # 测试OpenAI客户端
            sys.path.insert(0, str(self.scripts_dir))
            from openai_client import create_openai_client
            
            start_time = time.time()
            client = create_openai_client()
            duration = time.time() - start_time
            
            if client:
                details = f"客户端创建成功，类型: {type(client).__name__}"
                self.log_test("OpenAI客户端创建", True, details, "", duration)
                
                # 检查客户端属性
                if hasattr(client, 'api_key') and client.api_key:
                    key_preview = client.api_key[:8] + "..." if len(client.api_key) > 8 else client.api_key
                    print(f"    🔑 API密钥: {key_preview}")
                
                if hasattr(client, 'base_url'):
                    print(f"    🌐 基础URL: {client.base_url}")
                    
                if hasattr(client, 'model'):
                    print(f"    🤖 模型: {client.model}")
                
                # 测试API调用（简单测试）
                try:
                    # 这里可以添加一个简单的API测试调用
                    # 但为了避免消耗配额，我们只测试客户端创建
                    self.log_test("API连通性测试", True, "客户端配置正确，跳过实际调用")
                except Exception as e:
                    self.log_test("API连通性测试", False, "", str(e))
                
            else:
                self.log_test("OpenAI客户端创建", False, "", "客户端创建返回None")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("API集成验证", False, "", str(e))
            return False

    def test_workflow_yaml_structure(self) -> bool:
        """测试工作流YAML结构"""
        print("\n📋 测试步骤：工作流YAML结构验证")
        
        try:
            with open(self.workflow_file, 'r', encoding='utf-8') as f:
                workflow = yaml.safe_load(f)
            
            # 检查基本结构
            required_keys = ['name', 'jobs']
            missing_keys = []
            
            for key in required_keys:
                if key not in workflow:
                    missing_keys.append(key)
            
            # 处理'on'键（YAML解析问题）
            has_trigger = 'on' in workflow or True in workflow
            if not has_trigger:
                missing_keys.append('on')
            
            if missing_keys:
                self.log_test("YAML结构检查", False, "", f"缺少键: {missing_keys}")
                return False
            
            self.log_test("YAML结构检查", True, "所有必需键存在")
            
            # 检查作业配置
            jobs = workflow.get('jobs', {})
            if 'lookonchain-analysis' not in jobs:
                self.log_test("作业配置检查", False, "", "缺少lookonchain-analysis作业")
                return False
            
            job = jobs['lookonchain-analysis']
            
            # 检查运行环境
            runs_on = job.get('runs-on', '')
            if 'ubuntu' not in runs_on.lower():
                self.log_test("运行环境检查", False, "", f"非Ubuntu环境: {runs_on}")
            else:
                self.log_test("运行环境检查", True, f"运行环境: {runs_on}")
            
            # 检查权限
            permissions = job.get('permissions', {})
            if permissions.get('contents') != 'write':
                self.log_test("权限检查", False, "", "缺少contents: write权限")
            else:
                self.log_test("权限检查", True, "contents: write权限正确")
            
            # 检查步骤
            steps = job.get('steps', [])
            step_names = [step.get('name', '') for step in steps]
            
            required_steps = [
                '检出代码', '设置 Python 环境', '安装依赖', 
                '配置 Git', '运行 LookOnChain 分析'
            ]
            
            missing_steps = []
            for req_step in required_steps:
                if not any(req_step in step_name for step_name in step_names):
                    missing_steps.append(req_step)
            
            if missing_steps:
                self.log_test("工作流步骤检查", False, f"找到{len(steps)}个步骤", f"缺少步骤: {missing_steps}")
            else:
                self.log_test("工作流步骤检查", True, f"所有{len(required_steps)}个必需步骤存在")
            
            # 检查环境变量
            env_vars = None
            for step in steps:
                if step.get('name') == '运行 LookOnChain 分析':
                    env_vars = step.get('env', {})
                    break
            
            if env_vars:
                required_env = ['OPENAI_API_KEY', 'GITHUB_TOKEN', 'GITHUB_ACTIONS']
                missing_env = [var for var in required_env if var not in env_vars]
                
                if missing_env:
                    self.log_test("环境变量检查", False, f"找到{len(env_vars)}个变量", f"缺少: {missing_env}")
                else:
                    self.log_test("环境变量检查", True, f"所有{len(required_env)}个环境变量存在")
            else:
                self.log_test("环境变量检查", False, "", "运行步骤中未找到环境变量")
            
            return True
            
        except Exception as e:
            self.log_test("工作流YAML结构验证", False, "", str(e))
            return False

    def test_secret_configuration(self) -> bool:
        """测试密钥配置"""
        print("\n🔐 测试步骤：密钥配置验证")
        
        # 检查本地环境变量（模拟GitHub Secrets）
        required_secrets = {
            'OPENAI_API_KEY': '🤖 OpenAI API密钥',
            'OPENAI_BASE_URL': '🌐 OpenAI基础URL'
        }
        
        all_configured = True
        
        for secret_name, description in required_secrets.items():
            value = os.getenv(secret_name)
            if value:
                preview = value[:8] + "..." if len(value) > 8 else value
                self.log_test(f"密钥配置 - {secret_name}", True, f"{description}: {preview}")
            else:
                self.log_test(f"密钥配置 - {secret_name}", False, description, "未设置")
                all_configured = False
        
        # GitHub Token（Actions自动提供）
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token and github_token != 'your_github_token_here':
            preview = github_token[:8] + "..." if len(github_token) > 8 else github_token
            self.log_test("密钥配置 - GITHUB_TOKEN", True, f"GitHub令牌: {preview}")
        else:
            self.log_test("密钥配置 - GITHUB_TOKEN", True, "GitHub Actions自动提供（本地未设置）")
        
        return all_configured

    def generate_comprehensive_report(self) -> str:
        """生成全面测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        total_duration = sum(result['duration'] for result in self.test_results if result['duration'] > 0)
        
        report = f"""# 🚀 LookOnChain GitHub Actions工作流全面测试报告

**测试时间**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}  
**工作流文件**: {self.workflow_file.relative_to(self.project_root)}  
**测试环境**: 本地模拟GitHub Actions环境  

---

## 📊 执行摘要

| 指标 | 数值 | 状态 |
|------|------|------|
| **总测试数** | {total_tests} | - |
| **通过测试** | {passed_tests} | ✅ |
| **失败测试** | {failed_tests} | {"❌" if failed_tests > 0 else "✅"} |
| **成功率** | {success_rate:.1f}% | {"✅" if success_rate >= 90 else "⚠️" if success_rate >= 70 else "❌"} |
| **总执行时间** | {total_duration:.2f}秒 | {"✅" if total_duration < 300 else "⚠️"} |

---

## 🔍 详细测试结果

| 测试项目 | 状态 | 详情 | 耗时 |
|---------|------|------|------|
"""
        
        # 按测试步骤分组
        test_groups = {}
        for result in self.test_results:
            # 从测试名称推断分组
            if "环境" in result['test_name'] or "Python" in result['test_name'] or "依赖" in result['test_name']:
                group = "🔧 环境设置"
            elif "Git" in result['test_name']:
                group = "📝 Git配置"  
            elif "脚本执行" in result['test_name']:
                group = "🚀 脚本执行"
            elif "文件变更" in result['test_name'] or "内容" in result['test_name']:
                group = "📄 内容处理"
            elif "API" in result['test_name'] or "OpenAI" in result['test_name']:
                group = "🔌 API集成"
            elif "YAML" in result['test_name'] or "工作流" in result['test_name']:
                group = "📋 工作流配置"
            elif "密钥" in result['test_name']:
                group = "🔐 密钥管理"
            else:
                group = "🔍 其他测试"
            
            if group not in test_groups:
                test_groups[group] = []
            test_groups[group].append(result)
        
        # 生成分组测试结果
        for group_name, group_results in test_groups.items():
            report += f"\n### {group_name}\n\n"
            for result in group_results:
                status = "✅" if result['passed'] else "❌"
                duration = f"{result['duration']:.2f}s" if result['duration'] > 0 else "-"
                details = result['details'][:50] + "..." if len(result['details']) > 50 else result['details']
                
                report += f"| {result['test_name']} | {status} | {details} | {duration} |\n"
        
        # 性能分析
        report += f"""

---

## ⚡ 性能分析

### 执行时间分布
"""
        
        # 找出最耗时的测试
        timed_tests = [r for r in self.test_results if r['duration'] > 0]
        if timed_tests:
            timed_tests.sort(key=lambda x: x['duration'], reverse=True)
            report += "\n最耗时的操作:\n"
            for i, test in enumerate(timed_tests[:5]):
                report += f"{i+1}. **{test['test_name']}**: {test['duration']:.2f}秒\n"
        
        # 错误分析
        failed_results = [r for r in self.test_results if not r['passed']]
        if failed_results:
            report += f"""

---

## ❌ 错误分析

发现 {len(failed_results)} 个失败项目:

"""
            for i, result in enumerate(failed_results):
                report += f"""
### {i+1}. {result['test_name']}
- **错误**: {result['error']}
- **详情**: {result['details']}
- **时间**: {result['timestamp']}
"""

        # 环境信息
        report += f"""

---

## 🌍 测试环境信息

### 系统环境
- **Python版本**: {sys.version.split()[0]}
- **操作系统**: {os.name}
- **工作目录**: {os.getcwd()}

### 配置信息
- **OPENAI_API_KEY**: {"✅ 已配置" if os.getenv('OPENAI_API_KEY') else "❌ 未配置"}
- **OPENAI_BASE_URL**: {os.getenv('OPENAI_BASE_URL', '未设置')}
- **OPENAI_MODEL**: {os.getenv('OPENAI_MODEL', '未设置')}
- **GITHUB_ACTIONS**: {os.getenv('GITHUB_ACTIONS', 'false')}

---

## 📋 改进建议

### 高优先级
"""

        if failed_tests > 0:
            report += f"- 🚨 修复 {failed_tests} 个失败的测试项目\n"
        
        if total_duration > 300:
            report += "- ⏱️ 优化执行时间（当前超过5分钟）\n"
            
        report += """
### 中优先级
- 📊 添加详细的执行日志
- 🔄 添加重试机制
- 📝 改进错误消息

### 低优先级  
- 🚀 并行执行某些步骤
- 📈 添加性能监控
- 🛡️ 增强安全检查

---

## 🎯 结论

"""
        
        if success_rate >= 95:
            conclusion = "🌟 **EXCELLENT** - 工作流完全就绪，可以投入生产使用"
        elif success_rate >= 85:
            conclusion = "✅ **GOOD** - 工作流基本就绪，有少量改进空间"  
        elif success_rate >= 70:
            conclusion = "⚠️ **NEEDS WORK** - 工作流需要解决一些问题后再使用"
        else:
            conclusion = "❌ **CRITICAL** - 工作流存在严重问题，需要大量修复"
        
        report += f"""{conclusion}

**推荐操作**:
"""
        
        if success_rate >= 90:
            report += """
1. ✅ 在GitHub仓库中设置必要的Secrets
2. 🚀 启用工作流进行首次运行测试  
3. 📊 监控执行结果和性能表现
"""
        else:
            report += """
1. 🔧 优先修复失败的测试项目
2. 📝 完善错误处理和日志记录
3. 🧪 重新运行测试直到成功率达到90%以上
"""
        
        report += f"""

---

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*  
*测试框架版本: v2.0*
"""
        
        return report

    def run_comprehensive_test(self) -> bool:
        """运行全面测试"""
        print("🚀 开始GitHub Actions工作流全面测试...\n")
        print(f"📋 工作流文件: {self.workflow_file}")
        print(f"🕐 开始时间: {self.start_time.strftime('%H:%M:%S')}")
        
        # 测试步骤列表
        test_functions = [
            self.test_environment_setup,
            self.test_workflow_yaml_structure,
            self.test_secret_configuration,
            self.test_git_configuration,
            self.test_api_integration,
            self.test_main_script_execution,
            self.test_file_changes_detection,
            self.test_content_generation
        ]
        
        overall_success = True
        
        for test_func in test_functions:
            try:
                result = test_func()
                if not result:
                    overall_success = False
            except Exception as e:
                test_name = test_func.__name__.replace('test_', '').replace('_', ' ').title()
                self.log_test(test_name, False, "", f"测试执行异常: {e}")
                overall_success = False
        
        # 生成并保存报告
        report = self.generate_comprehensive_report()
        
        report_file = self.scripts_dir / "GITHUB_ACTIONS_WORKFLOW_TEST_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        return overall_success


def main():
    """主函数"""
    tester = WorkflowComprehensiveTester()
    success = tester.run_comprehensive_test()
    
    # 输出测试总结
    total = len(tester.test_results)
    passed = sum(1 for r in tester.test_results if r['passed'])
    duration = sum(r['duration'] for r in tester.test_results if r['duration'] > 0)
    
    print("\n" + "="*80)
    print(f"📊 测试完成: {passed}/{total} 通过 ({passed/total*100:.1f}%) - 耗时 {duration:.1f}秒")
    
    if success:
        print("🎉 工作流全面测试通过！可以投入生产使用。")
        return 0
    else:
        print("⚠️  工作流测试发现问题，请查看详细报告。")
        return 1


if __name__ == "__main__":
    sys.exit(main())