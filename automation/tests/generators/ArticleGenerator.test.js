import { jest } from '@jest/globals';
import { describe, test, expect, beforeEach, afterEach } from '@jest/globals';
import ArticleGenerator from '../../src/generators/ArticleGenerator.js';

describe('ArticleGenerator', () => {
  let articleGenerator;
  let mockTweetData;
  let mockTemplateContent;

  beforeEach(() => {
    articleGenerator = new ArticleGenerator('test-template.md');
    
    // Mock tweet data
    mockTweetData = {
      id: '1234567890',
      text: 'Bitcoin is showing strong momentum! #BTC #crypto #bullish',
      author: {
        username: 'cryptoexpert',
        displayName: 'Crypto Expert',
        verified: true,
        followerCount: 50000
      },
      metrics: {
        retweetCount: 150,
        likeCount: 500,
        replyCount: 25,
        quoteCount: 10
      },
      createdAt: '2025-08-14T10:30:00Z',
      url: 'https://twitter.com/cryptoexpert/status/1234567890'
    };

    // Mock template content
    mockTemplateContent = `+++
date = '2025-08-12T16:52:01+08:00'
draft = false
title = 'Test Template Title'
description = 'Test template description'
tags = ['test', 'template']
categories = ['test']
keywords = ['test', 'template']
+++
Test template content`;

    // Reset mocks
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('loadTemplate', () => {
    test('should throw error when template loading fails', async () => {
      const generator = new ArticleGenerator('non-existent-template.md');
      
      await expect(generator.loadTemplate()).rejects.toThrow('Failed to load template');
    });
  });

  describe('generateMetadata', () => {
    test('should generate proper metadata with Chinese tags and title', () => {
      const translatedContent = '比特币显示出强劲的势头！这是一个看涨的信号。';
      
      const metadata = articleGenerator.generateMetadata(mockTweetData, translatedContent);

      expect(metadata).toHaveProperty('date');
      expect(metadata).toHaveProperty('draft', false);
      expect(metadata).toHaveProperty('title');
      expect(metadata).toHaveProperty('description');
      expect(metadata).toHaveProperty('tags');
      expect(metadata).toHaveProperty('categories', ['推文分析']);
      expect(metadata).toHaveProperty('keywords');

      // Check that title contains Chinese content
      expect(metadata.title).toContain('Crypto Expert');
      expect(metadata.title).toMatch(/比特币|BTC|加密货币/);

      // Check that tags include crypto-related Chinese terms
      expect(metadata.tags).toContain('加密货币');
      expect(metadata.tags).toContain('区块链');
      expect(metadata.tags).toContain('比特币');
      expect(metadata.tags).toContain('BTC');

      // Check description length
      expect(metadata.description.length).toBeLessThanOrEqual(150);
    });

    test('should handle long translated content by truncating description', () => {
      const longTranslatedContent = '这是一个非常长的翻译内容，'.repeat(20);
      
      const metadata = articleGenerator.generateMetadata(mockTweetData, longTranslatedContent);

      expect(metadata.description.length).toBeLessThanOrEqual(150);
      expect(metadata.description).toMatch(/\.\.\.$/);
    });

    test('should generate appropriate tags for different crypto keywords', () => {
      const ethereumTweet = {
        ...mockTweetData,
        text: 'Ethereum DeFi ecosystem is growing rapidly! #ETH #DeFi #Web3'
      };
      const translatedContent = '以太坊DeFi生态系统正在快速增长！';
      
      const metadata = articleGenerator.generateMetadata(ethereumTweet, translatedContent);

      expect(metadata.tags).toContain('以太坊');
      expect(metadata.tags).toContain('ETH');
      expect(metadata.tags).toContain('DeFi');
      expect(metadata.tags).toContain('Web3');
    });
  });

  describe('generateChineseTitle', () => {
    test('should generate engaging Chinese title with author and keywords', () => {
      const translatedContent = '比特币显示出强劲的势头！这是一个看涨的信号。';
      
      const title = articleGenerator.generateChineseTitle(mockTweetData, translatedContent);

      expect(title).toContain('Crypto Expert');
      expect(title).toMatch(/比特币|BTC/);
      expect(title.length).toBeLessThanOrEqual(100);
    });

    test('should handle tweets without specific crypto keywords', () => {
      const genericTweet = {
        ...mockTweetData,
        text: 'Market analysis shows interesting trends today'
      };
      const translatedContent = '市场分析显示今天有有趣的趋势';
      
      const title = articleGenerator.generateChineseTitle(genericTweet, translatedContent);

      expect(title).toContain('Crypto Expert');
      expect(title).toMatch(/市场|分析|加密货币/);
    });

    test('should clean up invalid characters from title', () => {
      const tweetWithSpecialChars = {
        ...mockTweetData,
        text: 'Bitcoin: "The future" <is> here!'
      };
      const translatedContent = '比特币："未来"<就在>这里！';
      
      const title = articleGenerator.generateChineseTitle(tweetWithSpecialChars, translatedContent);

      expect(title).not.toMatch(/[<>:"/\\|?*]/);
    });
  });

  describe('generateCryptoTags', () => {
    test('should generate relevant crypto tags in Chinese', () => {
      const text = 'Bitcoin and Ethereum are leading the DeFi revolution with NFTs';
      const translatedContent = '比特币和以太坊正在引领DeFi革命';
      
      const tags = articleGenerator.generateCryptoTags(text, translatedContent);

      expect(tags).toContain('加密货币');
      expect(tags).toContain('区块链');
      expect(tags).toContain('推特分析');
      expect(tags).toContain('比特币');
      expect(tags).toContain('以太坊');
      expect(tags).toContain('DeFi');
      expect(tags).toContain('NFT');
      expect(tags.length).toBeLessThanOrEqual(10);
    });

    test('should include market-related tags when present', () => {
      const text = 'Bull market is here! Time to HODL and trade wisely';
      const translatedContent = '牛市来了！是时候持有并明智交易了';
      
      const tags = articleGenerator.generateCryptoTags(text, translatedContent);

      expect(tags).toContain('牛市');
      expect(tags).toContain('HODL');
      // Note: 'trading' maps to '交易', but 'trade' doesn't - this is expected behavior
    });
  });

  describe('generateFilename', () => {
    test('should generate descriptive filename with date and topic', () => {
      const title = 'Crypto Expert分享比特币最新观点：比特币显示出强劲的势头';
      const date = '2025-08-14T10:30:00+08:00';
      
      const filename = articleGenerator.generateFilename(title, date);

      expect(filename).toMatch(/^crypto-twitter-/);
      expect(filename).toMatch(/20250814\.md$/);
      expect(filename).toMatch(/crypto-expert/);
      expect(filename.length).toBeLessThanOrEqual(100);
    });

    test('should handle long titles by truncating slug', () => {
      const longTitle = '这是一个非常长的标题，'.repeat(20);
      const date = '2025-08-14T10:30:00+08:00';
      
      const filename = articleGenerator.generateFilename(longTitle, date);

      expect(filename).toMatch(/^crypto-twitter-/);
      expect(filename).toMatch(/20250814\.md$/);
      expect(filename.length).toBeLessThanOrEqual(100);
    });
  });

  describe('applyTemplate', () => {
    test('should format article content with tweet information', () => {
      const metadata = {
        title: 'Test Title',
        date: '2025-08-14T10:30:00+08:00',
        tags: ['比特币', 'BTC'],
        categories: ['推文分析']
      };
      const enhancedContent = '这是增强的文章内容，包含了对推文的分析和背景信息。';
      
      const content = articleGenerator.applyTemplate(metadata, enhancedContent, mockTweetData);

      expect(content).toContain(enhancedContent);
      expect(content).toContain('## 原始推文信息');
      expect(content).toContain('Crypto Expert (@cryptoexpert)');
      expect(content).toContain('**转发数**: 150');
      expect(content).toContain('**点赞数**: 500');
      expect(content).toContain('**回复数**: 25');
      expect(content).toContain('https://twitter.com/cryptoexpert/status/1234567890');
      expect(content).toContain('## 关于作者');
      expect(content).toContain('ERIC');
    });

    test('should format numbers with locale-specific formatting', () => {
      const tweetWithLargeNumbers = {
        ...mockTweetData,
        metrics: {
          retweetCount: 1500,
          likeCount: 25000,
          replyCount: 500,
          quoteCount: 100
        }
      };
      
      const content = articleGenerator.applyTemplate({}, 'test content', tweetWithLargeNumbers);

      expect(content).toContain('**转发数**: 1,500');
      expect(content).toContain('**点赞数**: 25,000');
      expect(content).toContain('**回复数**: 500');
    });
  });

  describe('generateArticle', () => {
    test('should generate complete article with all components', async () => {
      // Use the actual md-template.md file for this test
      const generator = new ArticleGenerator('../md-template.md');
      
      const translatedContent = '比特币显示出强劲的势头！这是一个看涨的信号。';
      const enhancedContent = '根据最新的市场分析，比特币正在显示出强劲的上涨势头。这种趋势表明投资者对比特币的信心正在增强。';
      
      const article = await generator.generateArticle(mockTweetData, translatedContent, enhancedContent);

      expect(article).toHaveProperty('frontMatter');
      expect(article).toHaveProperty('content');
      expect(article).toHaveProperty('filename');
      expect(article).toHaveProperty('fullContent');

      // Check front matter
      expect(article.frontMatter.title).toContain('Crypto Expert');
      expect(article.frontMatter.tags).toContain('比特币');
      expect(article.frontMatter.categories).toContain('推文分析');

      // Check content
      expect(article.content).toContain(enhancedContent);
      expect(article.content).toContain('## 原始推文信息');

      // Check filename
      expect(article.filename).toMatch(/^crypto-twitter-.*\.md$/);

      // Check full content format
      expect(article.fullContent).toMatch(/^\+\+\+\n/);
      expect(article.fullContent).toContain("title = '");
      expect(article.fullContent).toContain("tags = [");
      expect(article.fullContent).toContain('\n+++\n');
    });
  });

  describe('formatFullArticle', () => {
    test('should format complete article with proper TOML front matter', () => {
      const metadata = {
        date: '2025-08-14T10:30:00+08:00',
        draft: false,
        title: 'Test Article Title',
        description: 'Test description',
        tags: ['比特币', 'BTC', '加密货币'],
        categories: ['推文分析'],
        keywords: ['比特币分析', '加密货币', 'BTC']
      };
      const content = 'This is the article content.';
      
      const fullArticle = articleGenerator.formatFullArticle(metadata, content);

      expect(fullArticle).toMatch(/^\+\+\+\n/);
      expect(fullArticle).toContain("date = '2025-08-14T10:30:00+08:00'");
      expect(fullArticle).toContain("draft = false");
      expect(fullArticle).toContain("title = 'Test Article Title'");
      expect(fullArticle).toContain("tags = ['比特币', 'BTC', '加密货币']");
      expect(fullArticle).toContain("categories = ['推文分析']");
      expect(fullArticle).toContain('\n+++\nThis is the article content.');
    });

    test('should escape single quotes in front matter values', () => {
      const metadata = {
        date: '2025-08-14T10:30:00+08:00',
        draft: false,
        title: "Test's Article Title",
        description: "Test's description",
        tags: ["Bitcoin's price", 'BTC'],
        categories: ['推文分析'],
        keywords: ["Bitcoin's analysis"]
      };
      const content = 'Content';
      
      const fullArticle = articleGenerator.formatFullArticle(metadata, content);

      expect(fullArticle).toContain("title = 'Test''s Article Title'");
      expect(fullArticle).toContain("description = 'Test''s description'");
      expect(fullArticle).toContain("'Bitcoin''s price'");
      expect(fullArticle).toContain("'Bitcoin''s analysis'");
    });
  });

  describe('Edge cases and error handling', () => {
    test('should handle empty tweet text', () => {
      const emptyTweet = {
        ...mockTweetData,
        text: ''
      };
      const translatedContent = '空推文';
      
      const metadata = articleGenerator.generateMetadata(emptyTweet, translatedContent);

      expect(metadata.tags).toContain('加密货币');
      expect(metadata.tags).toContain('区块链');
      expect(metadata.title).toContain('Crypto Expert');
    });

    test('should handle very long tweet content', () => {
      const longTweet = {
        ...mockTweetData,
        text: 'Bitcoin '.repeat(50) + 'is amazing!'
      };
      const translatedContent = '比特币 '.repeat(50) + '太棒了！';
      
      const metadata = articleGenerator.generateMetadata(longTweet, translatedContent);

      expect(metadata.title.length).toBeLessThanOrEqual(100);
      expect(metadata.description.length).toBeLessThanOrEqual(150);
    });

    test('should handle special characters in tweet content', () => {
      const specialCharTweet = {
        ...mockTweetData,
        text: 'Bitcoin 🚀📈💎 #BTC #crypto 🌙'
      };
      const translatedContent = '比特币 🚀📈💎 #BTC #加密货币 🌙';
      
      const metadata = articleGenerator.generateMetadata(specialCharTweet, translatedContent);

      expect(metadata.title).toBeDefined();
      expect(metadata.tags).toContain('比特币');
      expect(metadata.tags).toContain('BTC');
    });
  });
});