#!/usr/bin/env python3
"""
LookOnChain 测试运行器
运行所有测试并生成覆盖率报告
"""

import unittest
import sys
import os
import coverage
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_tests():
    """运行所有测试"""
    print("🚀 开始运行 LookOnChain 测试套件...")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 初始化覆盖率测试
    cov = coverage.Coverage(
        source=['scripts/lookonchain'],
        omit=['*/__pycache__/*', '*/tests/*'],
        branch=True
    )
    cov.start()
    
    # 发现并运行测试
    test_dir = os.path.dirname(__file__)
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 停止覆盖率测试
    cov.stop()
    cov.save()
    
    # 生成覆盖率报告
    print("\n" + "="*60)
    print("📊 测试覆盖率报告")
    print("="*60)
    
    # 获取覆盖率数据
    coverage_data = cov.get_data()
    covered_files = coverage_data.measured_files()
    
    total_statements = 0
    total_missing = 0
    total_covered = 0
    
    file_reports = []
    
    for file_path in sorted(covered_files):
        if 'lookonchain' in file_path:
            # 分析每个文件的覆盖率
            file_analysis = cov.analysis2(file_path)
            file_statements = len(file_analysis[1])  # 总行数
            file_missing = len(file_analysis[2])     # 未覆盖行数
            file_covered = file_statements - file_missing
            file_percentage = (file_covered / file_statements * 100) if file_statements > 0 else 0
            
            file_reports.append({
                'file': os.path.basename(file_path),
                'statements': file_statements,
                'covered': file_covered,
                'missing': file_missing,
                'percentage': file_percentage
            })
            
            total_statements += file_statements
            total_missing += file_missing
            total_covered += file_covered
    
    # 打印每个文件的覆盖率
    for report in file_reports:
        print(f"📄 {report['file']}:")
        print(f"   📊 覆盖率: {report['percentage']:.1f}%")
        print(f"   📝 语句: {report['covered']}/{report['statements']}")
        print(f"   ❌ 缺失: {report['missing']} 行")
        print()
    
    # 计算总体覆盖率
    total_percentage = (total_covered / total_statements * 100) if total_statements > 0 else 0
    
    print("📈 总体覆盖率:")
    print(f"   📊 总覆盖率: {total_percentage:.1f}%")
    print(f"   📝 总语句: {total_covered}/{total_statements}")
    print(f"   ❌ 总缺失: {total_missing} 行")
    
    # 生成HTML覆盖率报告
    try:
        cov.html_report(directory='coverage_html')
        print(f"   🌐 HTML报告已生成: coverage_html/index.html")
    except Exception as e:
        print(f"   ⚠️ HTML报告生成失败: {e}")
    
    # 生成JSON报告
    try:
        coverage_json = {
            'timestamp': datetime.now().isoformat(),
            'total_percentage': total_percentage,
            'total_statements': total_statements,
            'total_covered': total_covered,
            'total_missing': total_missing,
            'files': file_reports,
            'test_results': {
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0
            }
        }
        
        with open('coverage_report.json', 'w', encoding='utf-8') as f:
            json.dump(coverage_json, f, ensure_ascii=False, indent=2)
        
        print(f"   📄 JSON报告已生成: coverage_report.json")
    except Exception as e:
        print(f"   ⚠️ JSON报告生成失败: {e}")
    
    # 打印测试结果摘要
    print("\n" + "="*60)
    print("📋 测试结果摘要")
    print("="*60)
    print(f"🧪 总测试数: {result.testsRun}")
    print(f"✅ 成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ 失败: {len(result.failures)}")
    print(f"💥 错误: {len(result.errors)}")
    print(f"⏭️ 跳过: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n💥 失败的测试:")
        for test, traceback in result.failures:
            print(f"   ❌ {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n💥 错误的测试:")
        for test, traceback in result.errors:
            print(f"   💥 {test}: {traceback.split('Error:')[-1].strip()}")
    
    # 判断测试结果
    success = len(result.failures) == 0 and len(result.errors) == 0
    coverage_success = total_percentage >= 80.0  # 要求80%覆盖率
    
    print("\n" + "="*60)
    if success and coverage_success:
        print("🎉 所有测试通过！覆盖率达标！")
    elif success:
        print("✅ 所有测试通过，但覆盖率不足！")
    else:
        print("❌ 测试未完全通过！")
    print("="*60)
    
    return success and coverage_success

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)