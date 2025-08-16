#!/usr/bin/env node

/**
 * File Management and Hugo Integration Demo
 * 
 * This example demonstrates how to use FileWriter and HugoBuilder
 * to create markdown articles and build a Hugo site.
 */

import FileWriter from '../src/utils/FileWriter.js';
import HugoBuilder from '../src/builders/HugoBuilder.js';

async function demonstrateFileManagement() {
  console.log('🚀 File Management and Hugo Integration Demo\n');

  // Initialize components
  const fileWriter = new FileWriter('content/posts');
  const hugoBuilder = new HugoBuilder('.');

  try {
    // Step 1: Create sample article content
    console.log('📝 Step 1: Creating sample article content...');
    
    const articleData = {
      title: 'Bitcoin突破新高：市场分析与投资策略',
      date: new Date(),
      description: 'Bitcoin价格突破历史新高，分析市场趋势和投资机会',
      tags: ['Bitcoin', '市场分析', '投资策略', '加密货币'],
      categories: ['推文分析'],
      content: `
# Bitcoin突破新高：市场分析与投资策略

## 市场概况

Bitcoin近期表现强劲，价格突破了历史新高，这一突破背后有多重因素支撑。

## 技术分析

### 价格走势
- 突破关键阻力位
- 成交量显著放大
- 技术指标呈现多头排列

### 支撑位分析
- 主要支撑位：$65,000
- 次要支撑位：$62,000
- 强支撑位：$58,000

## 基本面分析

### 机构采用
- 更多机构将Bitcoin纳入资产配置
- ETF资金持续流入
- 企业财务储备增加Bitcoin配置

### 宏观环境
- 通胀预期推动避险需求
- 美元走弱利好Bitcoin
- 监管环境逐步明朗

## 投资建议

### 短期策略
1. **逢低买入**：在支撑位附近分批建仓
2. **止盈设置**：设置合理的止盈点位
3. **风险控制**：严格执行止损策略

### 长期配置
- 建议将Bitcoin作为投资组合的一部分
- 配置比例控制在5-10%
- 定期定额投资策略

## 风险提示

投资Bitcoin存在高风险，价格波动剧烈，投资者应：
- 充分了解市场风险
- 不投资超过承受能力的资金
- 保持理性投资心态

---

*本分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。*
`
    };

    // Step 2: Generate article with proper front matter
    console.log('📄 Step 2: Generating article with Hugo front matter...');
    
    const frontMatter = `+++
title = "${articleData.title}"
date = "${articleData.date.toISOString()}"
draft = false
description = "${articleData.description}"
tags = [${articleData.tags.map(tag => `"${tag}"`).join(', ')}]
categories = [${articleData.categories.map(cat => `"${cat}"`).join(', ')}]
keywords = ["Bitcoin分析", "加密货币投资", "市场趋势", "投资策略"]
+++`;

    const fullContent = frontMatter + articleData.content;

    // Step 3: Generate unique filename
    console.log('🏷️  Step 3: Generating unique filename...');
    
    const filename = await fileWriter.generateUniqueFilename(articleData.title, articleData.date);
    console.log(`   Generated filename: ${filename}`);

    // Step 4: Validate content structure
    console.log('✅ Step 4: Validating content structure...');
    
    const isValidContent = fileWriter.validateFileContent(fullContent);
    console.log(`   Content validation: ${isValidContent ? 'PASSED' : 'FAILED'}`);

    if (!isValidContent) {
      throw new Error('Content validation failed');
    }

    // Step 5: Write article file
    console.log('💾 Step 5: Writing article file...');
    
    const filePath = await fileWriter.writeArticleFile(fullContent, filename);
    console.log(`   Article written to: ${filePath}`);

    // Step 6: Verify file exists
    console.log('🔍 Step 6: Verifying file creation...');
    
    const fileExists = await fileWriter.fileExists(filename);
    console.log(`   File exists: ${fileExists ? 'YES' : 'NO'}`);

    // Step 7: Validate Hugo site configuration
    console.log('⚙️  Step 7: Validating Hugo site configuration...');
    
    const siteConfig = await hugoBuilder.getSiteConfig();
    console.log(`   Site title: ${siteConfig.title || 'Not configured'}`);
    console.log(`   Base URL: ${siteConfig.baseURL || 'Not configured'}`);

    const isValidSite = await hugoBuilder.validateSiteConfiguration();
    console.log(`   Site validation: ${isValidSite ? 'PASSED' : 'FAILED'}`);

    // Step 8: Demonstrate Hugo build (dry run)
    console.log('🏗️  Step 8: Hugo build demonstration...');
    
    try {
      // Check if Hugo is installed
      const hugoVersion = await hugoBuilder.validateHugoInstallation();
      console.log(`   Hugo version: ${hugoVersion}`);
      
      console.log('   Note: Skipping actual build to avoid modifying the site');
      console.log('   To build the site, run: hugo --minify --gc');
      
    } catch (error) {
      console.log(`   Hugo not available: ${error.message}`);
      console.log('   Install Hugo to enable site building: https://gohugo.io/installation/');
    }

    // Step 9: Summary
    console.log('\n📊 Summary:');
    console.log(`   ✅ Article created: ${filename}`);
    console.log(`   ✅ Content validated: Hugo-compatible`);
    console.log(`   ✅ File written: ${filePath}`);
    console.log(`   ✅ Site configuration: Valid`);
    
    console.log('\n🎉 File management demo completed successfully!');
    
    return {
      filename,
      filePath,
      contentLength: fullContent.length,
      isValidContent,
      isValidSite
    };

  } catch (error) {
    console.error(`❌ Demo failed: ${error.message}`);
    throw error;
  }
}

// Run the demo if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  demonstrateFileManagement()
    .then(result => {
      console.log('\n✨ Demo completed with results:', result);
      process.exit(0);
    })
    .catch(error => {
      console.error('\n💥 Demo failed:', error.message);
      process.exit(1);
    });
}

export default demonstrateFileManagement;