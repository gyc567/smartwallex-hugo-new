#!/usr/bin/env node

import fs from 'fs-extra';
import path from 'path';
import { execSync } from 'child_process';
import ArticleGenerator from '../src/generators/ArticleGenerator.js';
import FileWriter from '../src/utils/FileWriter.js';
import Logger from '../src/utils/Logger.js';

/**
 * Final Integration Test for Hugo Site
 * Tests the core article generation and Hugo build functionality
 */

const logger = new Logger('FinalIntegrationTest');

class FinalIntegrationTest {
  constructor() {
    this.testDir = path.join(process.cwd(), 'test-final-integration');
    this.contentDir = path.join(this.testDir, 'content', 'posts');
    this.publicDir = path.join(this.testDir, 'public');
  }

  async runTest() {
    logger.info('Starting final integration test...');
    
    try {
      await this.setupTestEnvironment();
      await this.testArticleGeneration();
      await this.testHugoBuild();
      await this.validateFinalOutput();
      
      logger.info('✅ Final integration test completed successfully!');
      return true;
    } catch (error) {
      logger.error('❌ Final integration test failed:', error);
      return false;
    } finally {
      await this.cleanup();
    }
  }

  async setupTestEnvironment() {
    logger.info('Setting up final test environment...');
    
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
      }
    }
  }

  async testArticleGeneration() {
    logger.info('Testing article generation with real template...');
    
    const templatePath = path.join(this.testDir, 'md-template.md');
    const articleGenerator = new ArticleGenerator(templatePath);
    const fileWriter = new FileWriter(this.contentDir);

    // Test with realistic crypto tweet data
    const testTweet = {
      id: '1234567890',
      text: 'BREAKING: Bitcoin ETF approval sends BTC to new all-time high of $80,000! 🚀 This is the moment we\'ve all been waiting for. Institutional adoption is here! #Bitcoin #ETF #crypto',
      author: {
        username: 'cryptonews',
        displayName: 'Crypto News 📰',
        verified: true,
        followerCount: 500000
      },
      metrics: {
        retweetCount: 8500,
        likeCount: 25600,
        replyCount: 1200,
        quoteCount: 2100
      },
      createdAt: '2025-08-16T12:00:00Z',
      url: 'https://twitter.com/cryptonews/status/1234567890'
    };

    const translatedContent = '突发：比特币ETF获批推动BTC创下80,000美元历史新高！🚀 这是我们一直在等待的时刻。机构采用已经到来！';
    
    const enhancedContent = `突发：比特币ETF获批推动BTC创下80,000美元历史新高！🚀 这是我们一直在等待的时刻。机构采用已经到来！

## 历史性突破

比特币ETF的正式获批标志着加密货币行业的一个重要里程碑。这一决定为传统金融机构和散户投资者提供了更便捷的比特币投资渠道，预计将带来大量资金流入。

### 市场反应

- **价格飙升**：比特币价格在消息公布后迅速突破80,000美元大关
- **交易量激增**：24小时交易量创下历史新高
- **市场情绪**：恐惧贪婪指数达到"极度贪婪"水平

## 技术分析

从技术角度来看，比特币的突破具有以下特征：

1. **强劲支撑**：75,000美元形成新的强支撑位
2. **成交量确认**：大幅放量确认突破有效性
3. **趋势延续**：上升趋势线保持完好

## 机构影响

ETF获批对机构投资者的影响深远：

### 投资便利性
- 无需直接持有比特币
- 通过传统券商即可投资
- 符合机构合规要求

### 资金流入预期
- 预计首年将有100-500亿美元资金流入
- 养老基金和保险公司开始配置
- 散户投资门槛大幅降低

## 长期展望

比特币ETF的获批可能带来以下长期影响：

1. **价格稳定性提升**：机构资金的进入将减少价格波动
2. **监管环境改善**：为其他加密货币产品铺平道路
3. **主流接受度提高**：加速加密货币的主流化进程

## 投资建议

在当前市场环境下，建议投资者：

- **理性看待**：避免FOMO情绪，制定合理投资计划
- **分散投资**：不要将所有资金投入单一资产
- **长期持有**：关注比特币的长期价值而非短期波动
- **风险管理**：设置合理的止损和止盈位

## 风险提示

尽管前景乐观，投资者仍需注意以下风险：

- 监管政策可能发生变化
- 市场可能出现技术性回调
- 全球宏观经济环境的不确定性
- 加密货币市场固有的高波动性

*本文仅供参考，不构成投资建议。投资有风险，入市需谨慎。*`;

    // Generate article
    const article = await articleGenerator.generateArticle(testTweet, translatedContent, enhancedContent);
    
    // Validate article structure
    this.validateArticleStructure(article);
    
    // Write article file
    await fileWriter.writeArticleFile(article.fullContent, article.filename);
    
    // Verify file was created
    const filePath = path.join(this.contentDir, article.filename);
    if (!await fs.pathExists(filePath)) {
      throw new Error(`Article file was not created: ${filePath}`);
    }
    
    // Validate file content
    const fileContent = await fs.readFile(filePath, 'utf-8');
    this.validateFileContent(fileContent);
    
    logger.info(`✅ Article generated successfully: ${article.filename}`);
    return article;
  }

  validateArticleStructure(article) {
    // Check front matter
    const requiredFields = ['date', 'draft', 'title', 'description', 'tags', 'categories', 'keywords'];
    for (const field of requiredFields) {
      if (!article.frontMatter.hasOwnProperty(field)) {
        throw new Error(`Missing front matter field: ${field}`);
      }
    }
    
    // Check content sections
    const requiredSections = ['## 原始推文信息', '## 关于作者'];
    for (const section of requiredSections) {
      if (!article.content.includes(section)) {
        throw new Error(`Missing content section: ${section}`);
      }
    }
    
    // Validate Chinese content
    if (!article.frontMatter.title.match(/[\u4e00-\u9fff]/)) {
      throw new Error('Title should contain Chinese characters');
    }
    
    // Validate categories
    if (!article.frontMatter.categories.includes('推文分析')) {
      throw new Error('Should include 推文分析 category');
    }
  }

  validateFileContent(content) {
    // Check TOML front matter
    if (!content.startsWith('+++')) {
      throw new Error('Content should start with TOML front matter');
    }
    
    const frontMatterEnd = content.indexOf('+++', 3);
    if (frontMatterEnd === -1) {
      throw new Error('Content missing closing front matter delimiter');
    }
    
    // Check for required content
    const requiredContent = [
      'title =',
      'date =',
      'tags =',
      '## 原始推文信息',
      '## 关于作者',
      'ERIC',
      'gyc567@gmail.com',
      'smartwallex.com'
    ];
    
    for (const required of requiredContent) {
      if (!content.includes(required)) {
        throw new Error(`Content missing required element: ${required}`);
      }
    }
  }

  async testHugoBuild() {
    logger.info('Testing Hugo build with generated content...');
    
    try {
      // Change to test directory
      const originalCwd = process.cwd();
      process.chdir(this.testDir);
      
      // Check if Hugo is available
      try {
        const hugoVersion = execSync('hugo version', { encoding: 'utf-8', stdio: 'pipe' });
        logger.info(`Using Hugo: ${hugoVersion.trim()}`);
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
      
      logger.info('Hugo build completed successfully');
      
      // Validate build output
      const publicDir = path.join(this.testDir, 'public');
      if (!await fs.pathExists(publicDir)) {
        throw new Error('Hugo build did not create public directory');
      }
      
      // Check for essential files
      const essentialFiles = [
        'index.html',
        'index.xml',
        'sitemap.xml'
      ];
      
      for (const file of essentialFiles) {
        const filePath = path.join(publicDir, file);
        if (!await fs.pathExists(filePath)) {
          throw new Error(`Hugo build missing essential file: ${file}`);
        }
      }
      
      process.chdir(originalCwd);
      logger.info('✅ Hugo build validation completed');
      
    } catch (error) {
      process.chdir(process.cwd());
      throw new Error(`Hugo build failed: ${error.message}`);
    }
  }

  async validateFinalOutput() {
    logger.info('Validating final output...');
    
    const publicDir = path.join(this.testDir, 'public');
    
    // Check index page
    const indexPath = path.join(publicDir, 'index.html');
    const indexContent = await fs.readFile(indexPath, 'utf-8');
    
    // Validate site title and branding
    if (!indexContent.includes('SmartWallex')) {
      throw new Error('Index page missing site branding');
    }
    
    // Check for Chinese language support
    if (!indexContent.includes('lang="zh-cn"') && !indexContent.includes('lang="zh"')) {
      logger.warn('Site language configuration may need verification');
      // Don't fail the test for this, just warn
    }
    
    // Check for posts directory
    const postsDir = path.join(publicDir, 'posts');
    if (await fs.pathExists(postsDir)) {
      const postDirs = await fs.readdir(postsDir);
      if (postDirs.length > 0) {
        logger.info(`Generated ${postDirs.length} post pages`);
        
        // Validate first post
        const firstPostDir = path.join(postsDir, postDirs[0]);
        const postIndexPath = path.join(firstPostDir, 'index.html');
        
        if (await fs.pathExists(postIndexPath)) {
          const postContent = await fs.readFile(postIndexPath, 'utf-8');
          
          // Check for required post elements
          const requiredElements = [
            'post-header',
            'post-content',
            '原始推文信息',
            '关于作者'
          ];
          
          for (const element of requiredElements) {
            if (!postContent.includes(element)) {
              logger.warn(`Post missing element: ${element}`);
            }
          }
          
          // Check for Chinese content
          if (!postContent.match(/[\u4e00-\u9fff]/)) {
            throw new Error('Post content missing Chinese text');
          }
        }
      }
    }
    
    // Check RSS feed
    const rssPath = path.join(publicDir, 'index.xml');
    const rssContent = await fs.readFile(rssPath, 'utf-8');
    if (!rssContent.includes('<rss') || !rssContent.includes('SmartWallex')) {
      throw new Error('RSS feed is invalid or missing site information');
    }
    
    // Check sitemap
    const sitemapPath = path.join(publicDir, 'sitemap.xml');
    const sitemapContent = await fs.readFile(sitemapPath, 'utf-8');
    if (!sitemapContent.includes('<urlset') || !sitemapContent.includes('<url>')) {
      throw new Error('Sitemap is invalid or empty');
    }
    
    logger.info('✅ Final output validation completed');
  }

  async cleanup() {
    logger.info('Cleaning up final test environment...');
    
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

// Run test if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const test = new FinalIntegrationTest();
  const success = await test.runTest();
  process.exit(success ? 0 : 1);
}

export default FinalIntegrationTest;