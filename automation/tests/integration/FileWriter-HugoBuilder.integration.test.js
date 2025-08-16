import { jest } from '@jest/globals';
import { beforeEach, afterEach, describe, test, expect } from '@jest/globals';
import fs from 'fs/promises';
import path from 'path';

// Import the classes
import FileWriter from '../../src/utils/FileWriter.js';
import HugoBuilder from '../../src/builders/HugoBuilder.js';

describe('FileWriter and HugoBuilder Integration', () => {
  const testContentDir = 'test-integration/content/posts';
  const testSiteRoot = 'test-integration';
  let fileWriter;
  let hugoBuilder;

  beforeEach(async () => {
    fileWriter = new FileWriter(testContentDir);
    hugoBuilder = new HugoBuilder(testSiteRoot);
    
    // Create test directory structure
    await fs.mkdir(testSiteRoot, { recursive: true });
    await fs.mkdir(path.join(testSiteRoot, 'content'), { recursive: true });
    
    // Create a minimal hugo.toml for testing
    const hugoConfig = `
baseURL = 'https://example.org/'
languageCode = 'en-us'
title = 'Test Site'
`;
    await fs.writeFile(path.join(testSiteRoot, 'hugo.toml'), hugoConfig);
  });

  afterEach(async () => {
    // Clean up test directory
    try {
      await fs.rm(testSiteRoot, { recursive: true, force: true });
    } catch (error) {
      // Ignore cleanup errors
    }
  });

  describe('File Management Integration', () => {
    test('should create article file with proper Hugo structure', async () => {
      const articleContent = `+++
title = "Test Bitcoin Analysis"
date = "2025-08-14T10:00:00Z"
draft = false
description = "Test article description"
tags = ["bitcoin", "analysis"]
categories = ["crypto"]
+++

# Test Article

This is a test article about Bitcoin analysis.

## Market Overview

Bitcoin is showing interesting patterns...
`;

      const filename = await fileWriter.generateUniqueFilename('Test Bitcoin Analysis');
      const filePath = await fileWriter.writeArticleFile(articleContent, filename);

      // Verify file was created
      expect(await fileWriter.fileExists(filename)).toBe(true);
      
      // Verify content is valid
      const writtenContent = await fs.readFile(filePath, 'utf8');
      expect(writtenContent).toBe(articleContent);
      expect(fileWriter.validateFileContent(writtenContent)).toBe(true);
    });

    test('should generate unique filenames for multiple articles', async () => {
      const baseTitle = 'Bitcoin Market Analysis';
      const date = new Date('2025-08-14T10:00:00Z');
      const mockContent = `+++
title = "Test Article"
date = "2025-08-14T10:00:00Z"
draft = false
+++

Test content`;

      // Generate and write first file
      const filename1 = await fileWriter.generateUniqueFilename(baseTitle, date);
      await fileWriter.writeArticleFile(mockContent, filename1);

      // Generate and write second file
      const filename2 = await fileWriter.generateUniqueFilename(baseTitle, date);
      await fileWriter.writeArticleFile(mockContent, filename2);

      // Generate and write third file
      const filename3 = await fileWriter.generateUniqueFilename(baseTitle, date);
      await fileWriter.writeArticleFile(mockContent, filename3);

      expect(filename1).toMatch(/crypto-twitter-.*-20250814-001\.md/);
      expect(filename2).toMatch(/crypto-twitter-.*-20250814-002\.md/);
      expect(filename3).toMatch(/crypto-twitter-.*-20250814-003\.md/);

      // Verify all filenames are different
      expect(filename1).not.toBe(filename2);
      expect(filename2).not.toBe(filename3);
      expect(filename1).not.toBe(filename3);
    });

    test('should handle Chinese titles correctly', async () => {
      const chineseTitle = '比特币价格分析：市场趋势报告';
      const filename = fileWriter.generateFilename(chineseTitle);
      
      expect(filename).toMatch(/^crypto-twitter-.*\.md$/);
      expect(filename).toContain('比特币价格分析');
    });
  });

  describe('Hugo Integration', () => {
    test('should validate site configuration', async () => {
      const isValid = await hugoBuilder.validateSiteConfiguration();
      expect(isValid).toBe(true);
    });

    test('should read site configuration', async () => {
      const config = await hugoBuilder.getSiteConfig();
      expect(config.baseURL).toBe('https://example.org/');
      expect(config.title).toBe('Test Site');
      expect(config.languageCode).toBe('en-us');
    });

    test('should extract config values correctly', () => {
      const content = "baseURL = 'https://test.com/'\ntitle = 'My Test Site'";
      
      expect(hugoBuilder.extractConfigValue(content, 'baseURL')).toBe('https://test.com/');
      expect(hugoBuilder.extractConfigValue(content, 'title')).toBe('My Test Site');
      expect(hugoBuilder.extractConfigValue(content, 'nonexistent')).toBeNull();
    });

    test('should parse build output statistics', () => {
      const mockOutput = `
                                | EN  
-------------------+-----
  Pages            |  15  
  Paginator pages  |   0  
  Non-page files   |   0  
  Static files     |   8  
  Processed images |   0  
  Aliases          |   1  
  Sitemaps         |   1  
  Cleaned          |   0  

Total in 123 ms
`;

      const stats = hugoBuilder.parseBuildOutput(mockOutput);
      expect(stats.duration).toBe(123);
    });
  });

  describe('End-to-End Workflow', () => {
    test('should create article and validate Hugo compatibility', async () => {
      // Step 1: Create article content using template structure
      const articleData = {
        title: 'DeFi协议分析：Uniswap V4新特性解读',
        date: new Date('2025-08-14T10:00:00Z'),
        description: 'Uniswap V4协议的新特性分析和市场影响评估',
        tags: ['DeFi', 'Uniswap', '协议分析', '去中心化交易'],
        categories: ['推文分析'],
        content: `
# DeFi协议分析：Uniswap V4新特性解读

## 概述

Uniswap V4协议引入了多项创新特性，将进一步巩固其在去中心化交易领域的领导地位。

## 主要特性

### 1. 自定义流动性池
- 支持自定义手续费结构
- 灵活的价格曲线设计
- 增强的资本效率

### 2. 原生多链支持
- 跨链流动性共享
- 统一的用户体验
- 降低跨链成本

## 市场影响

这些新特性预计将：
- 提升DEX交易效率
- 吸引更多机构参与
- 推动DeFi生态发展

## 投资建议

建议关注相关代币的价格表现和生态项目的发展机会。
`
      };

      // Step 2: Generate article content with proper front matter
      const frontMatter = `+++
title = "${articleData.title}"
date = "${articleData.date.toISOString()}"
draft = false
description = "${articleData.description}"
tags = [${articleData.tags.map(tag => `"${tag}"`).join(', ')}]
categories = [${articleData.categories.map(cat => `"${cat}"`).join(', ')}]
+++`;

      const fullContent = frontMatter + articleData.content;

      // Step 3: Generate filename and write file
      const filename = await fileWriter.generateUniqueFilename(articleData.title, articleData.date);
      const filePath = await fileWriter.writeArticleFile(fullContent, filename);

      // Step 4: Validate file structure
      expect(await fileWriter.fileExists(filename)).toBe(true);
      expect(fileWriter.validateFileContent(fullContent)).toBe(true);

      // Step 5: Verify Hugo can read the configuration
      const siteConfig = await hugoBuilder.getSiteConfig();
      expect(siteConfig.title).toBe('Test Site');

      // Step 6: Verify site structure is valid for Hugo
      const isValidSite = await hugoBuilder.validateSiteConfiguration();
      expect(isValidSite).toBe(true);

      console.log(`Successfully created article: ${filename}`);
      console.log(`File path: ${filePath}`);
      console.log(`Content length: ${fullContent.length} characters`);
    });
  });
});