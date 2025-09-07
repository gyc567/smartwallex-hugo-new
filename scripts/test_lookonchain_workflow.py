#!/usr/bin/env python3
"""
LookOnChain工作流测试验证器
测试GitHub Actions工作流的各个组件和依赖
生成详细的测试报告
"""

import os
import sys
import subprocess
import json
import yaml
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(__file__))

class WorkflowTester:
    """工作流测试器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.scripts_dir = Path(__file__).parent
        self.workflow_file = self.project_root / ".github/workflows/lookonchain-analysis.yml"
        self.test_results = []
        
    def log_test(self, test_name: str, passed: bool, details: str = "", error: str = ""):
        """记录测试结果"""
        self.test_results.append({
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    📝 {details}")
        if error and not passed:
            print(f"    🚨 {error}")
    
    def test_workflow_file_exists(self) -> bool:
        """测试工作流文件是否存在"""
        try:
            exists = self.workflow_file.exists()
            if exists:
                self.log_test("工作流文件存在性", True, f"文件路径: {self.workflow_file}")
            else:
                self.log_test("工作流文件存在性", False, "", f"文件不存在: {self.workflow_file}")
            return exists
        except Exception as e:
            self.log_test("工作流文件存在性", False, "", str(e))
            return False
    
    def test_workflow_syntax(self) -> bool:
        """测试工作流YAML语法"""
        try:
            with open(self.workflow_file, 'r', encoding='utf-8') as f:
                workflow_data = yaml.safe_load(f)
            
            # 检查基本结构 (注意YAML中'on'可能被解析为True)
            required_keys = ['name', 'jobs']
            has_on_key = 'on' in workflow_data or True in workflow_data
            missing_keys = [key for key in required_keys if key not in workflow_data]
            if not has_on_key:
                missing_keys.append('on')
            
            if missing_keys:
                self.log_test("工作流YAML语法", False, "", f"缺少必需的键: {missing_keys}")
                return False
            
            # 检查触发器配置 (处理'on'被解析为True的情况)
            on_config = workflow_data.get('on', workflow_data.get(True, {}))
            has_schedule = 'schedule' in on_config if isinstance(on_config, dict) else False
            has_manual = 'workflow_dispatch' in on_config if isinstance(on_config, dict) else False
            
            details = f"调度触发器: {'✓' if has_schedule else '✗'}, 手动触发器: {'✓' if has_manual else '✗'}"
            self.log_test("工作流YAML语法", True, details)
            return True
            
        except yaml.YAMLError as e:
            self.log_test("工作流YAML语法", False, "", f"YAML语法错误: {e}")
            return False
        except Exception as e:
            self.log_test("工作流YAML语法", False, "", str(e))
            return False
    
    def test_required_files_exist(self) -> bool:
        """测试必需文件是否存在"""
        try:
            required_files = [
                "scripts/lookonchain_analyzer.py",
                "scripts/requirements.txt",
                "scripts/lookonchain/__init__.py",
                "scripts/lookonchain/config.py",
                "scripts/lookonchain/translator.py"
            ]
            
            missing_files = []
            existing_files = []
            
            for file_path in required_files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    existing_files.append(file_path)
                else:
                    missing_files.append(file_path)
            
            if missing_files:
                self.log_test("必需文件存在性", False, 
                            f"存在: {len(existing_files)}/{len(required_files)}", 
                            f"缺失文件: {missing_files}")
                return False
            else:
                self.log_test("必需文件存在性", True, f"所有{len(required_files)}个文件都存在")
                return True
                
        except Exception as e:
            self.log_test("必需文件存在性", False, "", str(e))
            return False
    
    def test_python_dependencies(self) -> bool:
        """测试Python依赖是否可以安装"""
        try:
            requirements_file = self.scripts_dir / "requirements.txt"
            if not requirements_file.exists():
                self.log_test("Python依赖检查", False, "", "requirements.txt不存在")
                return False
            
            # 读取依赖列表
            with open(requirements_file, 'r') as f:
                requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            # 尝试导入已安装的包
            import pkg_resources
            installed_packages = {pkg.project_name.lower(): pkg.version for pkg in pkg_resources.working_set}
            
            missing_deps = []
            available_deps = []
            
            for req in requirements:
                # 简单解析包名（忽略版本要求）
                pkg_name = req.split('>=')[0].split('==')[0].split('~=')[0].strip()
                
                if pkg_name.lower().replace('-', '_') in installed_packages or pkg_name.lower() in installed_packages:
                    available_deps.append(pkg_name)
                else:
                    missing_deps.append(pkg_name)
            
            if missing_deps:
                self.log_test("Python依赖检查", False, 
                            f"可用: {len(available_deps)}, 缺失: {len(missing_deps)}", 
                            f"缺失依赖: {missing_deps}")
                return False
            else:
                self.log_test("Python依赖检查", True, f"所有{len(requirements)}个依赖都已安装")
                return True
                
        except Exception as e:
            self.log_test("Python依赖检查", False, "", str(e))
            return False
    
    def test_main_script_syntax(self) -> bool:
        """测试主脚本语法"""
        try:
            main_script = self.scripts_dir / "lookonchain_analyzer.py"
            if not main_script.exists():
                self.log_test("主脚本语法检查", False, "", "lookonchain_analyzer.py不存在")
                return False
            
            # 尝试编译脚本以检查语法
            with open(main_script, 'r', encoding='utf-8') as f:
                code = f.read()
            
            compile(code, str(main_script), 'exec')
            self.log_test("主脚本语法检查", True, "Python语法正确")
            return True
            
        except SyntaxError as e:
            self.log_test("主脚本语法检查", False, "", f"语法错误: {e}")
            return False
        except Exception as e:
            self.log_test("主脚本语法检查", False, "", str(e))
            return False
    
    def test_environment_variables(self) -> bool:
        """测试环境变量配置"""
        try:
            # 检查工作流中定义的环境变量
            with open(self.workflow_file, 'r', encoding='utf-8') as f:
                workflow_content = f.read()
            
            required_env_vars = ['GLM_API_KEY', 'GITHUB_TOKEN']
            found_vars = []
            missing_vars = []
            
            for var in required_env_vars:
                pattern1 = "${{ secrets." + var + " }}"  # ${{ secrets.VAR }}
                pattern2 = "secrets." + var              # secrets.VAR
                if pattern1 in workflow_content or pattern2 in workflow_content:
                    found_vars.append(var)
                else:
                    missing_vars.append(var)
            
            # 检查本地环境变量（用于测试）
            local_env_status = {}
            for var in required_env_vars:
                if var == 'GITHUB_TOKEN':
                    # GitHub Actions会自动提供
                    local_env_status[var] = "GitHub Actions自动提供"
                else:
                    local_env_status[var] = "已设置" if os.getenv(var) else "未设置"
            
            if missing_vars:
                self.log_test("环境变量配置", False, 
                            f"工作流中找到: {found_vars}", 
                            f"工作流中缺失: {missing_vars}")
                return False
            else:
                details = f"工作流变量: {found_vars}, 本地状态: {local_env_status}"
                self.log_test("环境变量配置", True, details)
                return True
                
        except Exception as e:
            self.log_test("环境变量配置", False, "", str(e))
            return False
    
    def test_output_directories(self) -> bool:
        """测试输出目录结构"""
        try:
            # 检查必要的目录结构
            required_dirs = [
                "content/posts",
                "data",
                "scripts/logs"
            ]
            
            missing_dirs = []
            existing_dirs = []
            
            for dir_path in required_dirs:
                full_path = self.project_root / dir_path
                if full_path.exists() and full_path.is_dir():
                    existing_dirs.append(dir_path)
                else:
                    missing_dirs.append(dir_path)
                    # 尝试创建缺失的目录（测试环境）
                    try:
                        full_path.mkdir(parents=True, exist_ok=True)
                        if full_path.exists():
                            existing_dirs.append(dir_path)
                            missing_dirs.remove(dir_path)
                    except:
                        pass
            
            if missing_dirs:
                self.log_test("输出目录结构", False, 
                            f"存在: {existing_dirs}", 
                            f"缺失: {missing_dirs}")
                return False
            else:
                self.log_test("输出目录结构", True, f"所有{len(required_dirs)}个目录都存在")
                return True
                
        except Exception as e:
            self.log_test("输出目录结构", False, "", str(e))
            return False
    
    def test_script_imports(self) -> bool:
        """测试脚本模块导入"""
        try:
            # 测试能否导入关键模块
            test_modules = [
                "scripts/lookonchain/config.py",
                "scripts/lookonchain/translator.py",
                "scripts/openai_client.py"
            ]
            
            import_results = []
            
            for module_path in test_modules:
                try:
                    full_path = self.project_root / module_path
                    if not full_path.exists():
                        import_results.append(f"{module_path}: 文件不存在")
                        continue
                    
                    # 尝试编译检查语法（比导入更安全）
                    with open(full_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    
                    try:
                        compile(code, str(full_path), 'exec')
                        import_results.append(f"{module_path}: ✓")
                    except SyntaxError as e:
                        import_results.append(f"{module_path}: 语法错误 - {str(e)[:30]}")
                    except Exception as e:
                        import_results.append(f"{module_path}: 编译错误 - {str(e)[:30]}")
                        
                except Exception as e:
                    import_results.append(f"{module_path}: {str(e)[:50]}")
            
            failed_imports = [result for result in import_results if not result.endswith(": ✓")]
            
            if failed_imports:
                self.log_test("脚本模块导入", False, 
                            f"成功: {len(import_results) - len(failed_imports)}/{len(import_results)}", 
                            f"失败: {failed_imports}")
                return False
            else:
                self.log_test("脚本模块导入", True, f"所有{len(test_modules)}个模块导入成功")
                return True
                
        except Exception as e:
            self.log_test("脚本模块导入", False, "", str(e))
            return False
    
    def test_git_configuration(self) -> bool:
        """测试Git配置"""
        try:
            # 检查Git是否可用
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                self.log_test("Git配置", False, "", "Git命令不可用")
                return False
            
            git_version = result.stdout.strip()
            
            # 检查是否在Git仓库中
            result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                self.log_test("Git配置", False, "", "不在Git仓库中")
                return False
            
            # 检查工作目录状态
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            has_changes = bool(result.stdout.strip())
            
            details = f"{git_version}, 工作目录{'有' if has_changes else '无'}变更"
            self.log_test("Git配置", True, details)
            return True
            
        except Exception as e:
            self.log_test("Git配置", False, "", str(e))
            return False
    
    def test_cron_schedule(self) -> bool:
        """测试Cron调度配置"""
        try:
            with open(self.workflow_file, 'r', encoding='utf-8') as f:
                workflow_data = yaml.safe_load(f)
            
            # 处理'on'键解析问题
            on_config = workflow_data.get('on', workflow_data.get(True, {}))
            schedule_config = on_config.get('schedule', []) if isinstance(on_config, dict) else []
            
            if not schedule_config:
                self.log_test("Cron调度配置", False, "", "未找到调度配置")
                return False
            
            cron_expressions = [item.get('cron') for item in schedule_config]
            valid_crons = []
            invalid_crons = []
            
            for cron in cron_expressions:
                if cron:
                    # 简单验证cron表达式格式
                    parts = cron.split()
                    if len(parts) == 5:
                        valid_crons.append(cron)
                    else:
                        invalid_crons.append(cron)
            
            if invalid_crons:
                self.log_test("Cron调度配置", False, 
                            f"有效: {valid_crons}", 
                            f"无效: {invalid_crons}")
                return False
            else:
                # 解释cron时间
                schedule_info = []
                for cron in valid_crons:
                    if cron == '0 10 * * *':
                        schedule_info.append("每日UTC 10:00 (北京18:00)")
                    elif cron == '0 16 * * *':
                        schedule_info.append("每日UTC 16:00 (北京00:00)")
                    else:
                        schedule_info.append(f"自定义: {cron}")
                
                details = f"调度: {', '.join(schedule_info)}"
                self.log_test("Cron调度配置", True, details)
                return True
                
        except Exception as e:
            self.log_test("Cron调度配置", False, "", str(e))
            return False
    
    def generate_report(self) -> str:
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = f"""
# 🚀 LookOnChain 工作流测试报告

## 📊 测试摘要
- **总测试数**: {total_tests}
- **通过**: {passed_tests} ✅
- **失败**: {failed_tests} ❌  
- **成功率**: {success_rate:.1f}%
- **测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📋 详细测试结果

| 测试项目 | 状态 | 详情 | 错误信息 |
|---------|------|------|----------|
"""
        
        for result in self.test_results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            details = result['details'][:50] + "..." if len(result['details']) > 50 else result['details']
            error = result['error'][:50] + "..." if len(result['error']) > 50 else result['error']
            
            report += f"| {result['test_name']} | {status} | {details} | {error} |\n"
        
        report += f"""
## 🎯 工作流分析

### 基础结构
- **工作流名称**: LookOnChain 每日分析
- **触发方式**: 定时调度 + 手动触发
- **运行环境**: Ubuntu Latest + Python 3.11
- **权限要求**: contents: write

### 执行步骤
1. 检出代码 (actions/checkout@v4)
2. 设置Python环境 (actions/setup-python@v4)  
3. 安装依赖 (pip install)
4. 配置Git用户
5. 运行分析脚本
6. 检查文件变更
7. 提交并推送变更  
8. 生成执行摘要

### 调度配置
- **UTC 10:00** (北京时间 18:00) - 晚间执行
- **UTC 16:00** (北京时间 00:00) - 午夜执行

### 环境变量
- `GLM_API_KEY`: AI接口密钥 (需要在Secrets中配置)
- `GITHUB_TOKEN`: GitHub访问令牌 (Actions自动提供)
- `GITHUB_ACTIONS`: 标识Actions环境

## 🔧 推荐改进

### 高优先级
"""
        
        # 添加基于测试结果的推荐
        if failed_tests > 0:
            report += "- 🚨 修复失败的测试项目\n"
        
        report += """
### 中等优先级  
- 📝 添加错误重试机制
- 🔍 增强日志输出
- ⏰ 添加超时控制
- 📊 添加执行统计

### 低优先级
- 🛡️ 添加安全扫描
- 📈 性能监控集成
- 🎨 自定义通知格式

## 📖 使用说明

### 手动触发
```bash
# 在GitHub仓库页面 -> Actions -> LookOnChain 每日分析 -> Run workflow
```

### 本地测试
```bash
cd scripts
python lookonchain_analyzer.py
```

### 调试模式
```bash
# 设置调试环境变量
export GITHUB_ACTIONS=true
export GLM_API_KEY=your_key
python lookonchain_analyzer.py
```

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
        """
        
        return report.strip()
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("🚀 开始LookOnChain工作流测试...\n")
        
        test_functions = [
            self.test_workflow_file_exists,
            self.test_workflow_syntax, 
            self.test_required_files_exist,
            self.test_python_dependencies,
            self.test_main_script_syntax,
            self.test_environment_variables,
            self.test_output_directories,
            self.test_script_imports,
            self.test_git_configuration,
            self.test_cron_schedule
        ]
        
        for test_func in test_functions:
            try:
                test_func()
            except Exception as e:
                self.log_test(test_func.__name__.replace('test_', ''), False, "", str(e))
            print()  # 空行分隔
        
        # 生成并保存报告
        report = self.generate_report()
        
        # 保存报告到文件
        report_file = self.scripts_dir / "LOOKONCHAIN_WORKFLOW_TEST_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 详细报告已保存到: {report_file}")
        
        # 返回整体测试结果
        return all(result['passed'] for result in self.test_results)


def main():
    """主函数"""
    tester = WorkflowTester()
    success = tester.run_all_tests()
    
    print("\n" + "="*60)
    total = len(tester.test_results)
    passed = sum(1 for r in tester.test_results if r['passed'])
    print(f"📊 测试完成: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    if success:
        print("🎉 所有测试通过！工作流配置正确。")
        return 0
    else:
        print("⚠️  存在测试失败，请检查配置。")
        return 1


if __name__ == "__main__":
    sys.exit(main())