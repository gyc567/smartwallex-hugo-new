#!/usr/bin/env node

import fs from 'fs-extra';
import path from 'path';
import { execSync } from 'child_process';
import ArticleGenerator from '../src/generators/ArticleGenerator.js';
import FileWriter from '../src/utils/FileWriter.js';
import Logger from '../src/utils/Logger.js';

/**
 * Hugo Integration Validation Script
 * Tests the complete integration with the existing Hugo site
 */

const logger = new Logger('HugoValidation');

class HugoIntegrationValidator {
  constructor() {
    this.testDir = path.join(process.cwd(), 'test-hugo-integration');
    this.contentDir = path.join(this.testDir, 'content', 'posts');
    this.publicDir = path.join(this.testDir, 'public');
  }

  async validateAll() {
    logger.info('Starting Hugo integration validation...');
    
    try {
      await this.setupTestEnvironment();
      await this.validateTemplateCompatibility();
      await this.validateArticleGeneration();
      await this.validateHugoBuild();
      await this.validateSiteNavigation();
      await this.validateContentQuality();
      await this.validatePerformance();
      
      logger.info('✅ All Hugo integration tests passed!');
      return true;
    } catch (error) {
      logger.error('❌ Hugo integration validation failed:', error);
      return false;
    } finally {
      await this.cleanup();
    }
  }

  async setupTestEnvironment() {
    logger.info('Setting up test environment...');
    
    // Create test directory structure
    await fs.ensureDir(this.contentDir);
    await fs.ensureDir(this.publicDir);
    
    // Copy Hugo configuration and templates from project root
    const projectRoot = path.resolve(process.cwd(), '..');
    const filesToCopy = [
      'hugo.toml',
      'md-template.md',
      'layouts',
      'static',
      'archetypes'
    ];
    
    for (const file of filesToCopy) {
      const sourcePath = path.join(projectRoot, file);
      if (await fs.pathExists(sourcePath)) {
        const dest = path.join(this.testDir, file);
        await fs.copy(sourcePath, dest);
        logger.info(`Copied ${file} to test environment`);
      } else {
        logger.warn(`Source file not found: ${sourcePath}`);
      }
    }
  }

  async validateTemplateCompatibility() {
    logger.info('Validating template compatibility...');
    
    const templatePath = path.join(this.testDir, 'md-template.md');
    const articleGenerator = new ArticleGenerator(templatePath);
    
    // Test template loading
    await articleGenerator.loadTemplate();
    if (!articleGenerator.template) {
      throw new Error('Failed to load md-template.md');
    }
    
    // Validate template structure
    const template = articleGenerator.template;
    if (!template.data || !template.content) {
      throw new Error('Invalid template structure');
    }
    
    logger.info('✅ Template compatibility validated');
  }

  async validateArticleGeneration() {
    logger.info('Validating article generation...');
    
    const templatePath = path.join(this.testDir, 'md-template.md');
    const articleGenerator = new ArticleGenerator(templatePath);
    const fileWriter = new FileWriter();
    
    // Test data for different scenarios
    const testCases = [
      {
        name: 'Bitcoin Analysis',
        tweetData: {
          id: '1234567890',
          text: 'Bitcoin breaks $70,000! This bull run is just getting started. Major institutions are buying the dip. #BTC #crypto #bullrun',
          author: {
            username: 'bitcoinbull',
            displayName: 'Bitcoin Bull 🚀',
            verified: true,
            followerCount: 150000
          },
          metrics: {
            retweetCount: 3500,
            likeCount: 8900,
            replyCount: 456,
            quoteCount: 789
          },
          createdAt: '2025-08-16T10:30:00Z',
          url: 'https://twitter.com/bitcoinbull/status/1234567890'
        },
        translatedContent: '比特币突破70,000美元！这轮牛市才刚刚开始。主要机构正在逢低买入。',
        enhancedContent: `比特币突破70,000美元！这轮牛市才刚刚开始。主要机构正在逢低买入。

## 市场分析

比特币价格突破70,000美元大关，创下历史新高。这一突破得到了强劲的交易量支撑，表明市场对比特币的信心正在增强。

### 技术指标分析

- **RSI指标**：目前处于70附近，显示强劲的上涨动能
- **移动平均线**：价格站稳在所有主要移动平均线之上
- **成交量**：突破伴随着大幅放量，确认了突破的有效性

## 机构采用趋势

越来越多的机构投资者开始将比特币纳入其投资组合。这种趋势为比特币价格提供了强有力的支撑。

### 主要机构动向

1. **特斯拉**：继续持有大量比特币
2. **MicroStrategy**：持续增持比特币
3. **灰度基金**：比特币信托基金规模不断扩大

## 投资建议

在当前市场环境下，建议投资者：

1. **长期持有**：比特币的长期趋势依然向好
2. **分批建仓**：避免一次性大额投入
3. **风险管理**：设置合理的止损位
4. **关注宏观**：密切关注宏观经济政策变化

## 风险提示

虽然比特币表现强劲，但投资者仍需注意以下风险：

- 监管政策变化
- 市场情绪波动
- 技术面回调风险
- 宏观经济不确定性

*投资有风险，入市需谨慎。本文仅供参考，不构成投资建议。*`
      },
      {
        name: 'DeFi Protocol Update',
        tweetData: {
          id: '1234567891',
          text: 'Uniswap V4 is launching with revolutionary features! Hooks will change everything in DeFi. Liquidity providers will love the new fee structures. #DeFi #Uniswap #Web3',
          author: {
            username: 'defidev',
            displayName: 'DeFi Developer',
            verified: false,
            followerCount: 45000
          },
          metrics: {
            retweetCount: 1200,
            likeCount: 2800,
            replyCount: 189,
            quoteCount: 234
          },
          createdAt: '2025-08-16T14:15:00Z',
          url: 'https://twitter.com/defidev/status/1234567891'
        },
        translatedContent: 'Uniswap V4即将推出革命性功能！Hooks将改变DeFi的一切。流动性提供者会喜欢新的费用结构。',
        enhancedContent: `Uniswap V4即将推出革命性功能！Hooks将改变DeFi的一切。流动性提供者会喜欢新的费用结构。

## Uniswap V4 技术创新

Uniswap V4的推出标志着去中心化交易所技术的重大突破。新版本引入了多项创新功能，将为DeFi生态系统带来深远影响。

### 核心功能特性

#### 1. Hooks机制
- **自定义逻辑**：允许开发者在交易过程中插入自定义逻辑
- **灵活性提升**：支持更复杂的交易策略和风险管理
- **创新空间**：为新型DeFi产品创造无限可能

#### 2. 费用结构优化
- **动态费率**：根据市场条件自动调整交易费用
- **收益分配**：为流动性提供者提供更公平的收益分配
- **成本降低**：通过优化算法降低整体交易成本

## 对DeFi生态的影响

### 流动性提供者受益
1. **收益提升**：新的费用结构将提高LP收益
2. **风险管理**：更好的无常损失保护机制
3. **资本效率**：提高资金利用效率

### 开发者机会
1. **创新工具**：Hooks为开发者提供强大的创新工具
2. **生态扩展**：支持更多样化的DeFi应用
3. **集成便利**：简化与其他协议的集成

## 市场前景分析

Uniswap V4的推出预计将：

- **提升交易量**：更低的费用和更好的用户体验
- **吸引资金**：机构和散户资金的进一步流入
- **推动创新**：催生新一代DeFi产品和服务

## 投资机会与风险

### 机会
- **UNI代币**：协议升级可能推动代币价值增长
- **生态项目**：基于V4构建的新项目值得关注
- **流动性挖矿**：新的收益机会

### 风险
- **技术风险**：新功能可能存在未知漏洞
- **竞争加剧**：其他DEX可能推出类似功能
- **监管不确定性**：DeFi监管政策仍在发展中

*DeFi投资风险较高，请充分了解相关风险后谨慎参与。*`
      }
    ];

    for (const testCase of testCases) {
      logger.info(`Testing article generation for: ${testCase.name}`);
      
      const article = await articleGenerator.generateArticle(
        testCase.tweetData,
        testCase.translatedContent,
        testCase.enhancedContent
      );
      
      // Validate article structure
      this.validateArticleStructure(article);
      
      // Write to test content directory
      const testFileWriter = new FileWriter(this.contentDir);
      await testFileWriter.writeArticleFile(article.fullContent, article.filename);
      
      // Verify file was created and is valid
      const filePath = path.join(this.contentDir, article.filename);
      if (!await fs.pathExists(filePath)) {
        throw new Error(`Failed to create article file: ${filePath}`);
      }
      
      const fileContent = await fs.readFile(filePath, 'utf-8');
      if (!fileContent.includes('+++') || !fileContent.includes('## 原始推文信息')) {
        throw new Error(`Invalid article content in: ${filePath}`);
      }
      
      logger.info(`✅ Article generated successfully: ${article.filename}`);
    }
    
    logger.info('✅ Article generation validated');
  }

  validateArticleStructure(article) {
    // Validate front matter
    const requiredFrontMatterFields = ['date', 'draft', 'title', 'description', 'tags', 'categories', 'keywords'];
    for (const field of requiredFrontMatterFields) {
      if (!article.frontMatter.hasOwnProperty(field)) {
        throw new Error(`Missing front matter field: ${field}`);
      }
    }
    
    // Validate content structure
    const requiredContentSections = ['## 原始推文信息', '## 关于作者'];
    for (const section of requiredContentSections) {
      if (!article.content.includes(section)) {
        throw new Error(`Missing content section: ${section}`);
      }
    }
    
    // Validate Chinese content
    if (!article.frontMatter.title.match(/[\u4e00-\u9fff]/)) {
      throw new Error('Title should contain Chinese characters');
    }
    
    // Validate tags
    if (!Array.isArray(article.frontMatter.tags) || article.frontMatter.tags.length < 3) {
      throw new Error('Should have at least 3 tags');
    }
    
    // Validate categories
    if (!article.frontMatter.categories.includes('推文分析')) {
      throw new Error('Should include 推文分析 category');
    }
  }

  async validateHugoBuild() {
    logger.info('Validating Hugo build process...');
    
    try {
      // Change to test directory
      const originalCwd = process.cwd();
      process.chdir(this.testDir);
      
      // Check if Hugo is available
      try {
        execSync('hugo version', { stdio: 'pipe' });
      } catch (error) {
        logger.warn('Hugo not found, skipping build test');
        process.chdir(originalCwd);
        return;
      }
      
      // Run Hugo build
      const buildOutput = execSync('hugo --minify --destination public', { 
        encoding: 'utf-8',
        stdio: 'pipe'
      });
      
      logger.info('Hugo build output:', buildOutput);
      
      // Verify build output
      const publicDir = path.join(this.testDir, 'public');
      if (!await fs.pathExists(publicDir)) {
        throw new Error('Hugo build did not create public directory');
      }
      
      // Check for generated HTML files
      const indexPath = path.join(publicDir, 'index.html');
      if (!await fs.pathExists(indexPath)) {
        throw new Error('Hugo build did not create index.html');
      }
      
      // Check for post HTML files
      const postsDir = path.join(publicDir, 'posts');
      if (await fs.pathExists(postsDir)) {
        const postFiles = await fs.readdir(postsDir);
        logger.info(`Generated ${postFiles.length} post pages`);
      }
      
      process.chdir(originalCwd);
      logger.info('✅ Hugo build validated');
      
    } catch (error) {
      process.chdir(process.cwd());
      throw new Error(`Hugo build failed: ${error.message}`);
    }
  }

  async validateSiteNavigation() {
    logger.info('Validating site navigation and styling...');
    
    // Check layout templates
    const layoutFiles = [
      'layouts/_default/baseof.html',
      'layouts/_default/single.html',
      'layouts/_default/list.html'
    ];
    
    for (const layoutFile of layoutFiles) {
      const layoutPath = path.join(this.testDir, layoutFile);
      if (!await fs.pathExists(layoutPath)) {
        throw new Error(`Missing layout file: ${layoutFile}`);
      }
      
      const content = await fs.readFile(layoutPath, 'utf-8');
      
      // Validate template contains required elements
      if (layoutFile.includes('single.html')) {
        const requiredElements = ['post-header', 'post-content', 'post-tags', 'post-meta'];
        for (const element of requiredElements) {
          if (!content.includes(element)) {
            logger.warn(`Layout ${layoutFile} missing element: ${element}`);
          }
        }
      }
    }
    
    // Check CSS files
    const cssPath = path.join(this.testDir, 'static', 'css', 'style.css');
    if (await fs.pathExists(cssPath)) {
      const cssContent = await fs.readFile(cssPath, 'utf-8');
      if (cssContent.length === 0) {
        logger.warn('CSS file is empty');
      }
    }
    
    logger.info('✅ Site navigation and styling validated');
  }

  async validateContentQuality() {
    logger.info('Validating content quality...');
    
    const contentFiles = await fs.readdir(this.contentDir);
    
    for (const filename of contentFiles) {
      if (!filename.endsWith('.md')) continue;
      
      const filePath = path.join(this.contentDir, filename);
      const content = await fs.readFile(filePath, 'utf-8');
      
      // Quality checks
      const checks = [
        {
          name: 'Front matter format',
          test: () => content.startsWith('+++') && content.includes('+++\n')
        },
        {
          name: 'Chinese title',
          test: () => content.match(/title = '.*[\u4e00-\u9fff].*'/)
        },
        {
          name: 'Required sections',
          test: () => content.includes('## 原始推文信息') && content.includes('## 关于作者')
        },
        {
          name: 'Contact information',
          test: () => content.includes('gyc567@gmail.com') && content.includes('smartwallex.com')
        },
        {
          name: 'Minimum content length',
          test: () => content.length > 1000
        }
      ];
      
      for (const check of checks) {
        if (!check.test()) {
          throw new Error(`Quality check failed for ${filename}: ${check.name}`);
        }
      }
      
      logger.info(`✅ Quality validated for: ${filename}`);
    }
    
    logger.info('✅ Content quality validated');
  }

  async validatePerformance() {
    logger.info('Validating performance metrics...');
    
    const contentFiles = await fs.readdir(this.contentDir);
    const totalFiles = contentFiles.filter(f => f.endsWith('.md')).length;
    
    // Performance benchmarks
    const benchmarks = {
      maxFileSize: 100 * 1024, // 100KB
      maxFilenameLength: 100,
      minContentLength: 500,
      maxContentLength: 50 * 1024 // 50KB
    };
    
    for (const filename of contentFiles) {
      if (!filename.endsWith('.md')) continue;
      
      const filePath = path.join(this.contentDir, filename);
      const stats = await fs.stat(filePath);
      const content = await fs.readFile(filePath, 'utf-8');
      
      // File size check
      if (stats.size > benchmarks.maxFileSize) {
        logger.warn(`File ${filename} exceeds size limit: ${stats.size} bytes`);
      }
      
      // Filename length check
      if (filename.length > benchmarks.maxFilenameLength) {
        logger.warn(`Filename ${filename} exceeds length limit: ${filename.length} chars`);
      }
      
      // Content length checks
      if (content.length < benchmarks.minContentLength) {
        logger.warn(`Content ${filename} below minimum length: ${content.length} chars`);
      }
      
      if (content.length > benchmarks.maxContentLength) {
        logger.warn(`Content ${filename} exceeds maximum length: ${content.length} chars`);
      }
    }
    
    logger.info(`✅ Performance validated for ${totalFiles} files`);
  }

  async cleanup() {
    logger.info('Cleaning up test environment...');
    
    try {
      if (await fs.pathExists(this.testDir)) {
        await fs.remove(this.testDir);
        logger.info('✅ Test environment cleaned up');
      }
    } catch (error) {
      logger.warn('Failed to clean up test environment:', error.message);
    }
  }
}

// Run validation if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const validator = new HugoIntegrationValidator();
  const success = await validator.validateAll();
  process.exit(success ? 0 : 1);
}

export default HugoIntegrationValidator;