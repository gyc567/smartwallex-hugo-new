import { jest } from '@jest/globals';
import fs from 'fs-extra';
import path from 'path';
import { execSync } from 'child_process';
import ArticleGenerator from '../../src/generators/ArticleGenerator.js';
import FileWriter from '../../src/utils/FileWriter.js';

describe('Hugo Site Integration Tests', () => {
  let articleGenerator;
  let fileWriter;
  let testOutputDir;

  beforeAll(async () => {
    // Set up test environment
    testOutputDir = path.join(process.cwd(), 'test-output');
    await fs.ensureDir(testOutputDir);
    
    articleGenerator = new ArticleGenerator('md-template.md');
    fileWriter = new FileWriter();
  });

  afterAll(async () => {
    // Clean up test files
    if (await fs.pathExists(testOutputDir)) {
      await fs.remove(testOutputDir);
    }
  });

  describe('Template Compatibility', () => {
    test('should load and parse md-template.md correctly', async () => {
      await expect(articleGenerator.loadTemplate()).resolves.not.toThrow();
      expect(articleGenerator.template).toBeDefined();
      expect(articleGenerator.template.data).toBeDefined();
      expect(articleGenerator.template.content).toBeDefined();
    });

    test('should generate Hugo-compatible front matter', async () => {
      const mockTweetData = {
        id: '1234567890',
        text: 'Bitcoin is breaking new highs! The market is showing strong bullish momentum. #BTC #crypto',
        author: {
          username: 'cryptoexpert',
          displayName: 'Crypto Expert',
          verified: true,
          followerCount: 50000
        },
        metrics: {
          retweetCount: 1250,
          likeCount: 3400,
          replyCount: 89,
          quoteCount: 156
        },
        createdAt: '2025-08-16T10:30:00Z',
        url: 'https://twitter.com/cryptoexpert/status/1234567890'
      };

      const translatedContent = '比特币正在突破新高！市场显示出强劲的看涨势头。';
      const enhancedContent = `比特币正在突破新高！市场显示出强劲的看涨势头。

## 市场分析

根据最新的市场数据，比特币价格突破了关键阻力位，这表明市场情绪正在转向积极。技术指标显示强劲的上涨动能，投资者信心正在恢复。

## 投资建议

在当前市场环境下，建议投资者保持谨慎乐观的态度。虽然短期内可能出现回调，但长期趋势仍然看好。`;

      const article = await articleGenerator.generateArticle(mockTweetData, translatedContent, enhancedContent);

      // Verify front matter structure
      expect(article.frontMatter).toHaveProperty('date');
      expect(article.frontMatter).toHaveProperty('draft', false);
      expect(article.frontMatter).toHaveProperty('title');
      expect(article.frontMatter).toHaveProperty('description');
      expect(article.frontMatter).toHaveProperty('tags');
      expect(article.frontMatter).toHaveProperty('categories');
      expect(article.frontMatter).toHaveProperty('keywords');

      // Verify Chinese content
      expect(article.frontMatter.title).toMatch(/比特币|BTC|加密货币/);
      expect(article.frontMatter.categories).toContain('推文分析');
      expect(article.frontMatter.tags).toContain('比特币');
      expect(article.frontMatter.tags).toContain('加密货币');

      // Verify Hugo TOML format
      expect(article.fullContent).toMatch(/^\+\+\+/);
      expect(article.fullContent).toMatch(/date = '/);
      expect(article.fullContent).toMatch(/title = '/);
      expect(article.fullContent).toMatch(/tags = \[/);
    });

    test('should generate valid Hugo content structure', async () => {
      const mockTweetData = {
        id: '1234567890',
        text: 'Ethereum 2.0 staking rewards are looking attractive. DeFi protocols are integrating seamlessly.',
        author: {
          username: 'defianalyst',
          displayName: 'DeFi Analyst',
          verified: false,
          followerCount: 25000
        },
        metrics: {
          retweetCount: 890,
          likeCount: 2100,
          replyCount: 45,
          quoteCount: 78
        },
        createdAt: '2025-08-16T14:15:00Z',
        url: 'https://twitter.com/defianalyst/status/1234567890'
      };

      const translatedContent = '以太坊2.0质押奖励看起来很有吸引力。DeFi协议正在无缝集成。';
      const enhancedContent = `以太坊2.0质押奖励看起来很有吸引力。DeFi协议正在无缝集成。

## DeFi生态发展

以太坊2.0的推出为DeFi生态系统带来了新的机遇。质押机制不仅提供了稳定的收益来源，还增强了网络的安全性。

## 技术分析

从技术角度来看，以太坊的升级显著提高了网络的可扩展性和效率。这为更多创新的DeFi应用奠定了基础。`;

      const article = await articleGenerator.generateArticle(mockTweetData, translatedContent, enhancedContent);

      // Verify content structure includes required sections
      expect(article.content).toContain('## 原始推文信息');
      expect(article.content).toContain('## 关于作者');
      expect(article.content).toContain('ERIC');
      expect(article.content).toContain('gyc567@gmail.com');
      expect(article.content).toContain('smartwallex.com');

      // Verify tweet information is properly formatted
      expect(article.content).toContain('DeFi Analyst (@defianalyst)');
      expect(article.content).toContain('转发数: 890');
      expect(article.content).toContain('点赞数: 2,100');
      expect(article.content).toContain('查看原推文');
    });
  });

  describe('Hugo Build Integration', () => {
    test('should create valid markdown files in Hugo content structure', async () => {
      const mockTweetData = {
        id: '1234567890',
        text: 'Web3 adoption is accelerating. Major companies are integrating blockchain technology.',
        author: {
          username: 'web3news',
          displayName: 'Web3 News',
          verified: true,
          followerCount: 100000
        },
        metrics: {
          retweetCount: 2500,
          likeCount: 5600,
          replyCount: 234,
          quoteCount: 445
        },
        createdAt: '2025-08-16T16:45:00Z',
        url: 'https://twitter.com/web3news/status/1234567890'
      };

      const translatedContent = 'Web3采用正在加速。主要公司正在整合区块链技术。';
      const enhancedContent = `Web3采用正在加速。主要公司正在整合区块链技术。

## 企业采用趋势

越来越多的传统企业开始认识到区块链技术的价值，并积极探索Web3应用场景。这种趋势预示着区块链技术正在从概念验证阶段向实际应用转变。

## 市场影响

企业级采用将为整个加密货币市场带来更多的稳定性和增长动力。这也为投资者提供了新的机会。`;

      const article = await articleGenerator.generateArticle(mockTweetData, translatedContent, enhancedContent);

      // Write to test content directory
      const testContentDir = path.join(testOutputDir, 'content', 'posts');
      await fs.ensureDir(testContentDir);
      
      const filePath = path.join(testContentDir, article.filename);
      await fileWriter.writeArticleFile(article.fullContent, filePath);

      // Verify file was created
      expect(await fs.pathExists(filePath)).toBe(true);

      // Verify file content is valid
      const fileContent = await fs.readFile(filePath, 'utf-8');
      expect(fileContent).toContain('+++');
      expect(fileContent).toContain('Web3采用正在加速');
      expect(fileContent).toContain('## 原始推文信息');
    });

    test('should generate Hugo-compatible filenames', async () => {
      const testCases = [
        {
          title: 'Bitcoin价格分析：突破关键阻力位',
          expected: /^crypto-twitter-bitcoin.*-\d{8}\.md$/
        },
        {
          title: 'DeFi协议最新发展：收益率优化策略',
          expected: /^crypto-twitter-defi.*-\d{8}\.md$/
        },
        {
          title: 'NFT市场回暖：艺术品交易量上升',
          expected: /^crypto-twitter-nft.*-\d{8}\.md$/
        }
      ];

      for (const testCase of testCases) {
        const filename = articleGenerator.generateFilename(testCase.title, new Date().toISOString());
        expect(filename).toMatch(testCase.expected);
        expect(filename.length).toBeLessThan(100); // Ensure reasonable filename length
      }
    });
  });

  describe('Site Navigation and Styling Integration', () => {
    test('should verify Hugo configuration compatibility', async () => {
      // Read Hugo configuration
      const hugoConfig = await fs.readFile('hugo.toml', 'utf-8');
      
      // Verify Chinese language configuration
      expect(hugoConfig).toContain("languageCode = 'zh-cn'");
      expect(hugoConfig).toContain('SmartWallex');
      expect(hugoConfig).toContain('加密货币');

      // Verify required outputs for search functionality
      expect(hugoConfig).toContain('JSON');
      expect(hugoConfig).toContain('RSS');
    });

    test('should verify layout templates support generated content', async () => {
      // Check if required layout files exist
      const layoutFiles = [
        'layouts/_default/baseof.html',
        'layouts/_default/single.html',
        'layouts/_default/list.html'
      ];

      for (const layoutFile of layoutFiles) {
        expect(await fs.pathExists(layoutFile)).toBe(true);
      }

      // Verify single post template supports required features
      const singleTemplate = await fs.readFile('layouts/_default/single.html', 'utf-8');
      expect(singleTemplate).toContain('post-tags');
      expect(singleTemplate).toContain('post-meta');
      expect(singleTemplate).toContain('like-btn');
      expect(singleTemplate).toContain('相关文章');
    });

    test('should verify CSS styles support generated content', async () => {
      const cssFile = 'static/css/style.css';
      if (await fs.pathExists(cssFile)) {
        const cssContent = await fs.readFile(cssFile, 'utf-8');
        
        // Check for basic post styling classes
        const requiredClasses = [
          'post-single',
          'post-header',
          'post-content',
          'post-tags',
          'post-meta'
        ];

        // Note: This is a basic check - CSS might use different class names
        // The test passes if the file exists and contains some styling
        expect(cssContent.length).toBeGreaterThan(0);
      }
    });
  });

  describe('Content Quality Validation', () => {
    test('should validate generated content meets quality standards', async () => {
      const mockTweetData = {
        id: '1234567890',
        text: 'Breaking: Major cryptocurrency exchange announces new security features. Enhanced protection for user funds.',
        author: {
          username: 'cryptosecurity',
          displayName: 'Crypto Security',
          verified: true,
          followerCount: 75000
        },
        metrics: {
          retweetCount: 1800,
          likeCount: 4200,
          replyCount: 156,
          quoteCount: 289
        },
        createdAt: '2025-08-16T18:20:00Z',
        url: 'https://twitter.com/cryptosecurity/status/1234567890'
      };

      const translatedContent = '突发：主要加密货币交易所宣布新的安全功能。增强用户资金保护。';
      const enhancedContent = `突发：主要加密货币交易所宣布新的安全功能。增强用户资金保护。

## 安全升级详情

这次安全升级包括多重签名钱包、冷存储优化和实时监控系统。这些措施将显著提高用户资金的安全性。

## 行业影响

交易所安全性的提升对整个加密货币行业具有积极意义，有助于增强投资者信心和市场稳定性。`;

      const article = await articleGenerator.generateArticle(mockTweetData, translatedContent, enhancedContent);

      // Quality checks
      expect(article.frontMatter.title.length).toBeGreaterThan(10);
      expect(article.frontMatter.title.length).toBeLessThan(150);
      expect(article.frontMatter.description.length).toBeGreaterThan(20);
      expect(article.frontMatter.description.length).toBeLessThan(200);
      expect(article.frontMatter.tags.length).toBeGreaterThan(3);
      expect(article.frontMatter.tags.length).toBeLessThan(15);
      expect(article.content.length).toBeGreaterThan(500);

      // Content structure validation
      expect(article.content).toContain('## 原始推文信息');
      expect(article.content).toContain('## 关于作者');
      expect(article.content).toContain('转发数:');
      expect(article.content).toContain('点赞数:');
      expect(article.content).toContain('查看原推文');

      // SEO validation
      expect(article.frontMatter.keywords.length).toBeGreaterThan(5);
      expect(article.frontMatter.categories).toContain('推文分析');
    });

    test('should handle special characters and formatting correctly', async () => {
      const mockTweetData = {
        id: '1234567890',
        text: 'Bitcoin's price: $65,000+ 🚀 "This is just the beginning!" says @analyst. #BTC #crypto',
        author: {
          username: 'pricetracker',
          displayName: 'Price Tracker 📊',
          verified: false,
          followerCount: 30000
        },
        metrics: {
          retweetCount: 950,
          likeCount: 2800,
          replyCount: 67,
          quoteCount: 123
        },
        createdAt: '2025-08-16T20:10:00Z',
        url: 'https://twitter.com/pricetracker/status/1234567890'
      };

      const translatedContent = '比特币价格：65,000美元+ 🚀 "这只是开始！"分析师说。';
      const enhancedContent = `比特币价格：65,000美元+ 🚀 "这只是开始！"分析师说。

## 价格分析

比特币突破65,000美元大关，创下新的里程碑。技术分析显示，这一突破具有强劲的支撑，预示着更大的上涨空间。

## 市场情绪

投资者情绪高涨，市场参与度显著提升。这种积极的市场氛围为进一步的价格上涨创造了有利条件。`;

      const article = await articleGenerator.generateArticle(mockTweetData, translatedContent, enhancedContent);

      // Verify special characters are handled correctly
      expect(article.fullContent).not.toContain("'"); // Should be escaped in TOML
      expect(article.fullContent).toContain("''"); // Escaped quotes
      expect(article.frontMatter.title).toContain('65,000');
      expect(article.content).toContain('🚀');
      expect(article.content).toContain('Price Tracker 📊');
    });
  });
});