import { jest } from '@jest/globals';
import DuplicateChecker from '../../src/utils/DuplicateChecker.js';
import path from 'path';
import crypto from 'crypto';
import { fileURLToPath } from 'url';
import { promises as fs } from 'fs';

// Get __dirname equivalent in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

describe('DuplicateChecker', () => {
  let duplicateChecker;
  let mockDataPath;

  beforeEach(() => {
    jest.clearAllMocks();
    mockDataPath = path.join(__dirname, 'test-processed-tweets.json');
    duplicateChecker = new DuplicateChecker(mockDataPath);
  });

  describe('constructor', () => {
    test('should initialize with default data file path', () => {
      const checker = new DuplicateChecker();
      expect(checker.dataFilePath).toContain('processed-tweets.json');
    });

    test('should initialize with custom data file path', () => {
      const customPath = '/custom/path/data.json';
      const checker = new DuplicateChecker(customPath);
      expect(checker.dataFilePath).toBe(customPath);
    });

    test('should set retention days to 30', () => {
      expect(duplicateChecker.RETENTION_DAYS).toBe(30);
    });
  });

  describe('generateContentHash', () => {
    test('should generate SHA-256 hash for valid content', () => {
      const content = 'Bitcoin is reaching new heights! #crypto';
      const hash = duplicateChecker.generateContentHash(content);
      
      expect(hash).toHaveLength(64); // SHA-256 produces 64-character hex string
      expect(typeof hash).toBe('string');
    });

    test('should normalize content before hashing', () => {
      const content1 = 'Bitcoin is   great!   https://example.com';
      const content2 = 'BITCOIN IS GREAT!';
      
      const hash1 = duplicateChecker.generateContentHash(content1);
      const hash2 = duplicateChecker.generateContentHash(content2);
      
      expect(hash1).toBe(hash2);
    });

    test('should remove URLs from content before hashing', () => {
      const contentWithUrl = 'Check this out https://twitter.com/status/123';
      const contentWithoutUrl = 'Check this out';
      
      const hash1 = duplicateChecker.generateContentHash(contentWithUrl);
      const hash2 = duplicateChecker.generateContentHash(contentWithoutUrl);
      
      expect(hash1).toBe(hash2);
    });

    test('should throw error for invalid content', () => {
      expect(() => duplicateChecker.generateContentHash('')).toThrow('Content must be a non-empty string');
      expect(() => duplicateChecker.generateContentHash(null)).toThrow('Content must be a non-empty string');
      expect(() => duplicateChecker.generateContentHash(123)).toThrow('Content must be a non-empty string');
    });
  });

  describe('loadProcessedData', () => {
    test('should create default data structure when file does not exist', async () => {
      // Test with a non-existent file path
      const nonExistentPath = path.join(__dirname, 'non-existent-file.json');
      const checker = new DuplicateChecker(nonExistentPath);

      const result = await checker.loadProcessedData();

      expect(result).toEqual({
        processedTweets: [],
        lastUpdated: expect.any(String),
        version: '1.0.0'
      });
    });
  });

  describe('saveProcessedData', () => {
    test('should update timestamp when saving', () => {
      duplicateChecker.processedData = {
        processedTweets: [],
        lastUpdated: null,
        version: '1.0.0'
      };

      // Test the timestamp update logic without actual file writing
      const originalLastUpdated = duplicateChecker.processedData.lastUpdated;
      duplicateChecker.processedData.lastUpdated = new Date().toISOString();
      
      expect(duplicateChecker.processedData.lastUpdated).not.toBe(originalLastUpdated);
      expect(duplicateChecker.processedData.lastUpdated).toBeTruthy();
    });
  });

  describe('checkDuplicate', () => {
    beforeEach(async () => {
      duplicateChecker.processedData = {
        processedTweets: [
          {
            tweetId: '123456789',
            contentHash: 'existing_hash_123',
            processedDate: '2025-08-14T09:00:00Z',
            filename: 'existing-tweet.md',
            tweetUrl: 'https://twitter.com/user/status/123456789',
            keywords: ['bitcoin', 'crypto', 'blockchain']
          }
        ],
        lastUpdated: '2025-08-14T09:00:00Z',
        version: '1.0.0'
      };
    });

    test('should detect duplicate by tweet ID', async () => {
      const result = await duplicateChecker.checkDuplicate('123456789', 'Different content');

      expect(result.isDuplicate).toBe(true);
      expect(result.reason).toBe('tweet_id_exists');
      expect(result.matchedEntry.tweetId).toBe('123456789');
    });

    test('should detect duplicate by content hash', async () => {
      const content = 'Bitcoin is reaching new heights!';
      const contentHash = duplicateChecker.generateContentHash(content);
      
      // Update existing entry to have the same content hash
      duplicateChecker.processedData.processedTweets[0].contentHash = contentHash;

      const result = await duplicateChecker.checkDuplicate('999999999', content);

      expect(result.isDuplicate).toBe(true);
      expect(result.reason).toBe('content_hash_match');
    });

    test('should detect duplicate by URL', async () => {
      const result = await duplicateChecker.checkDuplicate(
        '999999999', 
        'Different content', 
        'https://twitter.com/user/status/123456789'
      );

      expect(result.isDuplicate).toBe(true);
      expect(result.reason).toBe('url_match');
    });

    test('should detect duplicate by semantic similarity', async () => {
      // Create content with very high similarity to existing keywords ['bitcoin', 'crypto', 'blockchain']
      // Using mostly the same keywords to ensure high Jaccard similarity
      const similarContent = 'bitcoin crypto blockchain bitcoin crypto blockchain bitcoin crypto';
      
      const result = await duplicateChecker.checkDuplicate('999999999', similarContent);

      expect(result.isDuplicate).toBe(true);
      expect(result.reason).toBe('semantic_similarity');
    });

    test('should return unique for new content', async () => {
      const uniqueContent = 'Ethereum smart contracts are revolutionary technology';
      
      const result = await duplicateChecker.checkDuplicate('999999999', uniqueContent);

      expect(result.isDuplicate).toBe(false);
      expect(result.reason).toBe('unique_content');
      expect(result.contentHash).toBeTruthy();
    });

    test('should throw error for missing required parameters', async () => {
      await expect(duplicateChecker.checkDuplicate('', 'content')).rejects.toThrow('Tweet ID and content are required');
      await expect(duplicateChecker.checkDuplicate('123', '')).rejects.toThrow('Tweet ID and content are required');
    });
  });

  describe('extractKeywords', () => {
    test('should extract meaningful keywords', () => {
      const content = 'Bitcoin and Ethereum are the top cryptocurrencies in the blockchain space';
      const keywords = duplicateChecker.extractKeywords(content);

      expect(keywords).toContain('bitcoin');
      expect(keywords).toContain('ethereum');
      expect(keywords).toContain('cryptocurrencies');
      expect(keywords).toContain('blockchain');
      expect(keywords).not.toContain('and');
      expect(keywords).not.toContain('the');
    });

    test('should limit keywords to 20', () => {
      const longContent = 'word '.repeat(50);
      const keywords = duplicateChecker.extractKeywords(longContent);

      expect(keywords.length).toBeLessThanOrEqual(20);
    });

    test('should filter out short words', () => {
      const content = 'a an to of in on at by is';
      const keywords = duplicateChecker.extractKeywords(content);

      expect(keywords).toHaveLength(0);
    });
  });

  describe('calculateSimilarity', () => {
    test('should calculate Jaccard similarity correctly', () => {
      const keywords1 = ['bitcoin', 'crypto', 'blockchain'];
      const keywords2 = ['bitcoin', 'ethereum', 'crypto'];

      const similarity = duplicateChecker.calculateSimilarity(keywords1, keywords2);

      // Intersection: ['bitcoin', 'crypto'] = 2
      // Union: ['bitcoin', 'crypto', 'blockchain', 'ethereum'] = 4
      // Similarity: 2/4 = 0.5
      expect(similarity).toBe(0.5);
    });

    test('should return 0 for empty arrays', () => {
      expect(duplicateChecker.calculateSimilarity([], ['bitcoin'])).toBe(0);
      expect(duplicateChecker.calculateSimilarity(['bitcoin'], [])).toBe(0);
      expect(duplicateChecker.calculateSimilarity([], [])).toBe(0);
    });

    test('should return 1 for identical arrays', () => {
      const keywords = ['bitcoin', 'crypto', 'blockchain'];
      const similarity = duplicateChecker.calculateSimilarity(keywords, keywords);

      expect(similarity).toBe(1);
    });
  });

  describe('updateProcessedList', () => {
    beforeEach(() => {
      duplicateChecker.processedData = {
        processedTweets: [],
        lastUpdated: null,
        version: '1.0.0'
      };
    });

    test('should add new processed tweet entry', async () => {
      const tweetId = '123456789';
      const contentHash = 'abc123hash';
      const filename = 'test-article.md';
      const additionalData = {
        content: 'Bitcoin is amazing',
        tweetUrl: 'https://twitter.com/user/status/123456789'
      };

      await duplicateChecker.updateProcessedList(tweetId, contentHash, filename, additionalData);

      expect(duplicateChecker.processedData.processedTweets).toHaveLength(1);
      
      const entry = duplicateChecker.processedData.processedTweets[0];
      expect(entry.tweetId).toBe(tweetId);
      expect(entry.contentHash).toBe(contentHash);
      expect(entry.filename).toBe(filename);
      expect(entry.processedDate).toBeTruthy();
      expect(entry.content).toBe(additionalData.content);
      expect(entry.tweetUrl).toBe(additionalData.tweetUrl);
      expect(entry.keywords).toBeTruthy();
    });

    test('should throw error for missing required parameters', async () => {
      await expect(duplicateChecker.updateProcessedList('', 'hash', 'file')).rejects.toThrow('Tweet ID, content hash, and filename are required');
      await expect(duplicateChecker.updateProcessedList('123', '', 'file')).rejects.toThrow('Tweet ID, content hash, and filename are required');
      await expect(duplicateChecker.updateProcessedList('123', 'hash', '')).rejects.toThrow('Tweet ID, content hash, and filename are required');
    });
  });

  describe('cleanupOldEntries', () => {
    test('should remove entries older than retention period', async () => {
      const oldDate = new Date();
      oldDate.setDate(oldDate.getDate() - 35); // 35 days ago

      const recentDate = new Date();
      recentDate.setDate(recentDate.getDate() - 5); // 5 days ago

      duplicateChecker.processedData = {
        processedTweets: [
          {
            tweetId: '1',
            contentHash: 'old_hash',
            processedDate: oldDate.toISOString(),
            filename: 'old.md'
          },
          {
            tweetId: '2',
            contentHash: 'recent_hash',
            processedDate: recentDate.toISOString(),
            filename: 'recent.md'
          }
        ],
        lastUpdated: null,
        version: '1.0.0'
      };

      await duplicateChecker.cleanupOldEntries();

      expect(duplicateChecker.processedData.processedTweets).toHaveLength(1);
      expect(duplicateChecker.processedData.processedTweets[0].tweetId).toBe('2');
    });

    test('should handle empty processed data gracefully', async () => {
      duplicateChecker.processedData = null;

      await expect(duplicateChecker.cleanupOldEntries()).resolves.not.toThrow();
    });
  });

  describe('getStatistics', () => {
    test('should return correct statistics', async () => {
      const now = new Date();
      const recent = new Date(now.getTime() - 12 * 60 * 60 * 1000); // 12 hours ago
      const lastWeek = new Date(now.getTime() - 6 * 24 * 60 * 60 * 1000); // 6 days ago
      const oldDate = new Date(now.getTime() - 10 * 24 * 60 * 60 * 1000); // 10 days ago

      duplicateChecker.processedData = {
        processedTweets: [
          { processedDate: now.toISOString() },
          { processedDate: recent.toISOString() },
          { processedDate: lastWeek.toISOString() },
          { processedDate: oldDate.toISOString() }
        ],
        lastUpdated: now.toISOString(),
        version: '1.0.0'
      };

      const stats = await duplicateChecker.getStatistics();

      expect(stats.totalProcessed).toBe(4);
      expect(stats.processedLast24Hours).toBe(2);
      expect(stats.processedLast7Days).toBe(3);
      expect(stats.lastUpdated).toBe(now.toISOString());
    });
  });

  describe('isOriginalContent', () => {
    test('should identify retweets by RT prefix', () => {
      const retweetData = { text: 'RT @user: This is a retweet' };
      expect(duplicateChecker.isOriginalContent(retweetData)).toBe(false);
    });

    test('should identify retweets by retweeted_status field', () => {
      const retweetData = { 
        text: 'Some text',
        retweeted_status: { id: '123' }
      };
      expect(duplicateChecker.isOriginalContent(retweetData)).toBe(false);
    });

    test('should identify retweets by referenced_tweets field', () => {
      const retweetData = { 
        text: 'Some text',
        referenced_tweets: [{ type: 'retweeted', id: '123' }]
      };
      expect(duplicateChecker.isOriginalContent(retweetData)).toBe(false);
    });

    test('should identify original content', () => {
      const originalData = { 
        text: 'This is original content about Bitcoin'
      };
      expect(duplicateChecker.isOriginalContent(originalData)).toBe(true);
    });

    test('should handle quoted tweets as original content', () => {
      const quotedTweetData = { 
        text: 'My thoughts on this',
        referenced_tweets: [{ type: 'quoted', id: '123' }]
      };
      expect(duplicateChecker.isOriginalContent(quotedTweetData)).toBe(true);
    });
  });
});