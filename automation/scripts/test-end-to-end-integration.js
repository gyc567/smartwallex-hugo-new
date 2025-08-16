#!/usr/bin/env node

import fs from 'fs-extra';
import path from 'path';
import { execSync } from 'child_process';
import { TwitterClient } from '../src/clients/TwitterClient.js';
import ContentProcessor from '../src/processors/ContentProcessor.js';
import TranslationService from '../src/services/TranslationService.js';
import ArticleGenerator from '../src/generators/ArticleGenerator.js';
import DuplicateChecker from '../src/utils/DuplicateChecker.js';
import FileWriter from '../src/utils/FileWriter.js';
import Logger from '../src/utils/Logger.js';

/**
 * End-to-End Integration Test
 * Tests the complete workflow from mock Twitter data to Hugo site generation
 */

const logger = new Logger('E2ETest');

class EndToEndIntegrationTest {
  constructor() {
    this.testDir = path.join(process.cwd(), 'test-e2e-integration');
    this.contentDir = path.join(this.testDir, 'content', 'posts');
    this.publicDir = path.join(this.testDir, 'public');
    this.dataDir = path.join(this.testDir, 'automation', 'data');
  }

  async runFullTest() {
    logger.info('Starting end-to-end integration test...');
    
    try {
      await this.setupTestEnvironment();
      await this.testCompleteWorkflow();
      await this.validateGeneratedSite();
      await this.testDuplicateDetection();
      await this.validateSitePerformance();
      
      logger.info('✅ End-to-end integration test completed successfully!');
      return true;
    } catch (error) {
      logger.error('❌ End-to-end integration test failed:', error);
      return false;
    } finally {
      await this.cleanup();
    }
  }

  async setupTestEnvironment() {
    logger.info('Setting up end-to-end test environment...');
    
    // Create test directory structure
    await fs.ensureDir(this.contentDir);
    await fs.ensureDir(this.publicDir);
    await fs.ensureDir(this.dataDir);
    
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

    // Create empty processed tweets file
    const processedTweetsPath = path.join(this.dataDir, 'processed-tweets.json');
    await fs.writeJson(processedTweetsPath, { processedTweets: [] });
  }

  async testCompleteWorkflow() {
    logger.info('Testing complete workflow...');
    
    // Mock tweet data representing different scenarios
    const mockTweets = [
      {
        id: '1234567890',
        text: 'BREAKING: Bitcoin just hit $75,000! 🚀 This is the biggest breakthrough in crypto history. Institutional adoption is accelerating faster than ever. The future is here! #Bitcoin #BTC #crypto #bullrun',
        author: {
          username: 'cryptoking',
          displayName: 'Crypto King 👑',
          verified: true,
          followerCount: 250000
        },
        metrics: {
          retweetCount: 5600,
          likeCount: 12400,
          replyCount: 890,
          quoteCount: 1200
        },
        createdAt: '2025-08-16T09:30:00Z',
        url: 'https://twitter.com/cryptoking/status/1234567890'
      },
      {
        id: '1234567891',
        text: 'Ethereum 2.0 staking rewards are now at 8% APY! 📈 The merge was just the beginning. Layer 2 solutions are scaling beautifully. DeFi summer 2.0 is coming! #Ethereum #ETH #DeFi #staking',
        author: {
          username: 'ethdev',
          displayName: 'Ethereum Developer',
          verified: false,
          followerCount: 85000
        },
        metrics: {
          retweetCount: 2800,
          likeCount: 6700,
          replyCount: 345,
          quoteCount: 567
        },
        createdAt: '2025-08-16T11:15:00Z',
        url: 'https://twitter.com/ethdev/status/1234567891'
      },
      {
        id: '1234567892',
        text: 'Major update: Solana network processed 65,000 TPS yesterday without any downtime! 🔥 The ecosystem is thriving with new projects launching daily. Web3 gaming is exploding! #Solana #SOL #Web3',
        author: {
          username: 'solanabuilder',
          displayName: 'Solana Builder 🛠️',
          verified: true,
          followerCount: 120000
        },
        metrics: {
          retweetCount: 3400,
          likeCount: 8900,
          replyCount: 456,
          quoteCount: 789
        },
        createdAt: '2025-08-16T13:45:00Z',
        url: 'https://twitter.com/solanabuilder/status/1234567892'
      }
    ];

    // Initialize components
    const contentProcessor = new ContentProcessor();
    const translationService = new TranslationService();
    const templatePath = path.join(this.testDir, 'md-template.md');
    const articleGenerator = new ArticleGenerator(templatePath);
    const duplicateChecker = new DuplicateChecker(path.join(this.dataDir, 'processed-tweets.json'));
    const fileWriter = new FileWriter(this.contentDir);

    // Process tweets through the complete workflow
    logger.info('Processing tweets through complete workflow...');
    
    // Step 1: Rank tweets by engagement
    const rankedTweets = contentProcessor.rankTweetsByEngagement(mockTweets);
    expect(rankedTweets.length).toBe(3);
    expect(rankedTweets[0].id).toBe('1234567890'); // Highest engagement
    
    // Step 2: Process top 3 tweets
    const processedArticles = [];
    
    for (let i = 0; i < Math.min(3, rankedTweets.length); i++) {
      const tweet = rankedTweets[i];
      logger.info(`Processing tweet ${i + 1}: ${tweet.id}`);
      
      // Check for duplicates
      const isDuplicate = await duplicateChecker.checkDuplicate(tweet.id, tweet.text);
      if (isDuplicate) {
        logger.info(`Skipping duplicate tweet: ${tweet.id}`);
        continue;
      }
      
      // Translate content
      const translatedContent = await translationService.translateText(tweet.text, 'zh-CN');
      logger.info(`Translated content: ${translatedContent.substring(0, 50)}...`);
      
      // Enhance content
      const enhancedContent = await translationService.enhanceContent(tweet, translatedContent);
      logger.info(`Enhanced content length: ${enhancedContent.length} characters`);
      
      // Generate article
      const article = await articleGenerator.generateArticle(tweet, translatedContent, enhancedContent);
      logger.info(`Generated article: ${article.filename}`);
      
      // Write article file
      await fileWriter.writeArticleFile(article.fullContent, article.filename);
      logger.info(`Written article file: ${article.filename}`);
      
      // Update duplicate checker
      await duplicateChecker.updateProcessedList(tweet.id, article.filename);
      
      processedArticles.push({
        tweet,
        article,
        filename: article.filename
      });
    }
    
    logger.info(`✅ Processed ${processedArticles.length} articles successfully`);
    return processedArticles;
  }

  async validateGeneratedSite() {
    logger.info('Validating generated Hugo site...');
    
    try {
      // Change to test directory for Hugo build
      const originalCwd = process.cwd();
      process.chdir(this.testDir);
      
      // Check if Hugo is available
      try {
        execSync('hugo version', { stdio: 'pipe' });
      } catch (error) {
        logger.warn('Hugo not found, skipping build validation');
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
      
      // Check for generated files
      const indexPath = path.join(publicDir, 'index.html');
      if (!await fs.pathExists(indexPath)) {
        throw new Error('Hugo build did not create index.html');
      }
      
      // Validate index.html content
      const indexContent = await fs.readFile(indexPath, 'utf-8');
      if (!indexContent.includes('SmartWallex')) {
        throw new Error('Index page missing site title');
      }
      
      // Check for post pages
      const postsDir = path.join(publicDir, 'posts');
      if (await fs.pathExists(postsDir)) {
        const postFiles = await fs.readdir(postsDir);
        logger.info(`Generated ${postFiles.length} post pages`);
        
        // Validate at least one post page
        if (postFiles.length > 0) {
          const firstPostDir = path.join(postsDir, postFiles[0]);
          const postIndexPath = path.join(firstPostDir, 'index.html');
          
          if (await fs.pathExists(postIndexPath)) {
            const postContent = await fs.readFile(postIndexPath, 'utf-8');
            
            // Validate post content structure
            const requiredElements = [
              'post-header',
              'post-content',
              '原始推文信息',
              '关于作者',
              'ERIC'
            ];
            
            for (const element of requiredElements) {
              if (!postContent.includes(element)) {
                logger.warn(`Post page missing element: ${element}`);
              }
            }
          }
        }
      }
      
      // Check for RSS feed
      const rssPath = path.join(publicDir, 'index.xml');
      if (await fs.pathExists(rssPath)) {
        const rssContent = await fs.readFile(rssPath, 'utf-8');
        if (!rssContent.includes('<rss')) {
          logger.warn('RSS feed appears to be invalid');
        }
      }
      
      // Check for search index
      const searchIndexPath = path.join(publicDir, 'index.json');
      if (await fs.pathExists(searchIndexPath)) {
        const searchIndex = await fs.readJson(searchIndexPath);
        if (!Array.isArray(searchIndex)) {
          logger.warn('Search index is not an array');
        }
      }
      
      process.chdir(originalCwd);
      logger.info('✅ Generated site validation completed');
      
    } catch (error) {
      process.chdir(process.cwd());
      throw new Error(`Site validation failed: ${error.message}`);
    }
  }

  async testDuplicateDetection() {
    logger.info('Testing duplicate detection...');
    
    const duplicateChecker = new DuplicateChecker(path.join(this.dataDir, 'processed-tweets.json'));
    
    // Test with the same tweet ID (should be detected as duplicate)
    const isDuplicate1 = await duplicateChecker.checkDuplicate('1234567890', 'Some content');
    if (!isDuplicate1) {
      throw new Error('Duplicate detection failed - should detect existing tweet ID');
    }
    
    // Test with new tweet ID (should not be duplicate)
    const isDuplicate2 = await duplicateChecker.checkDuplicate('9999999999', 'New unique content');
    if (isDuplicate2) {
      throw new Error('Duplicate detection failed - should not detect new tweet as duplicate');
    }
    
    logger.info('✅ Duplicate detection working correctly');
  }

  async validateSitePerformance() {
    logger.info('Validating site performance...');
    
    const publicDir = path.join(this.testDir, 'public');
    if (!await fs.pathExists(publicDir)) {
      logger.warn('Public directory not found, skipping performance validation');
      return;
    }
    
    // Check file sizes
    const indexPath = path.join(publicDir, 'index.html');
    if (await fs.pathExists(indexPath)) {
      const stats = await fs.stat(indexPath);
      if (stats.size > 500 * 1024) { // 500KB
        logger.warn(`Index page is large: ${Math.round(stats.size / 1024)}KB`);
      }
    }
    
    // Check CSS file size
    const cssPath = path.join(publicDir, 'css', 'style.css');
    if (await fs.pathExists(cssPath)) {
      const stats = await fs.stat(cssPath);
      if (stats.size > 100 * 1024) { // 100KB
        logger.warn(`CSS file is large: ${Math.round(stats.size / 1024)}KB`);
      }
    }
    
    // Count total files
    const allFiles = await this.getAllFiles(publicDir);
    logger.info(`Generated ${allFiles.length} total files`);
    
    // Calculate total size
    let totalSize = 0;
    for (const file of allFiles) {
      const stats = await fs.stat(file);
      totalSize += stats.size;
    }
    
    logger.info(`Total site size: ${Math.round(totalSize / 1024)}KB`);
    
    if (totalSize > 10 * 1024 * 1024) { // 10MB
      logger.warn('Site size is quite large, consider optimization');
    }
    
    logger.info('✅ Site performance validation completed');
  }

  async getAllFiles(dir) {
    const files = [];
    const items = await fs.readdir(dir);
    
    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stats = await fs.stat(fullPath);
      
      if (stats.isDirectory()) {
        const subFiles = await this.getAllFiles(fullPath);
        files.push(...subFiles);
      } else {
        files.push(fullPath);
      }
    }
    
    return files;
  }

  async cleanup() {
    logger.info('Cleaning up end-to-end test environment...');
    
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

// Simple assertion helper
function expect(actual) {
  return {
    toBe: (expected) => {
      if (actual !== expected) {
        throw new Error(`Expected ${expected}, but got ${actual}`);
      }
    },
    toBeGreaterThan: (expected) => {
      if (actual <= expected) {
        throw new Error(`Expected ${actual} to be greater than ${expected}`);
      }
    }
  };
}

// Run test if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const test = new EndToEndIntegrationTest();
  const success = await test.runFullTest();
  process.exit(success ? 0 : 1);
}

export default EndToEndIntegrationTest;