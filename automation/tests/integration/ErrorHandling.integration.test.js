import { TwitterCryptoAutomation } from '../../src/index.js';
import ErrorHandler, { ErrorTypes, ErrorSeverity } from '../../src/utils/ErrorHandler.js';
import Logger from '../../src/utils/Logger.js';
import NotificationService from '../../src/services/NotificationService.js';

// Mock external dependencies
jest.mock('../../src/clients/TwitterClient.js');
jest.mock('../../src/processors/ContentProcessor.js');
jest.mock('../../src/services/TranslationService.js');
jest.mock('../../src/generators/ArticleGenerator.js');
jest.mock('../../src/utils/DuplicateChecker.js');
jest.mock('../../src/utils/FileWriter.js');
jest.mock('../../src/builders/HugoBuilder.js');
jest.mock('../../src/config/ConfigLoader.js');
jest.mock('fs-extra');

describe('Error Handling Integration Tests', () => {
  let automation;
  let mockConfig;

  beforeEach(() => {
    // Mock configuration
    mockConfig = {
      twitter: {
        searchKeywords: ['crypto', 'bitcoin'],
        maxResults: 10
      },
      content: {},
      translation: {},
      template: { path: 'template.md' },
      storage: { processedTweetsPath: 'processed.json' },
      hugo: { contentDir: 'content', siteRoot: '.', outputDir: 'public' },
      notifications: {
        enabled: true,
        channels: [
          { type: 'slack', webhookUrl: 'https://hooks.slack.com/test' }
        ]
      }
    };

    // Mock ConfigLoader
    const ConfigLoader = require('../../src/config/ConfigLoader.js').default;
    ConfigLoader.load.mockResolvedValue(mockConfig);

    automation = new TwitterCryptoAutomation();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Initialization Error Handling', () => {
    test('should handle configuration loading errors', async () => {
      const ConfigLoader = require('../../src/config/ConfigLoader.js').default;
      ConfigLoader.load.mockRejectedValue(new Error('Config file not found'));

      await expect(automation.initialize()).rejects.toThrow('Config file not found');
    });

    test('should handle component initialization errors with recovery', async () => {
      const TwitterClient = require('../../src/clients/TwitterClient.js').TwitterClient;
      TwitterClient.mockImplementation(() => {
        throw new Error('Twitter API key missing');
      });

      await expect(automation.initialize()).rejects.toThrow();
    });

    test('should initialize error handler and notification service', async () => {
      await automation.initialize();

      expect(automation.errorHandler).toBeInstanceOf(ErrorHandler);
      expect(automation.notificationService).toBeInstanceOf(NotificationService);
    });
  });

  describe('Workflow Error Handling', () => {
    beforeEach(async () => {
      // Setup successful initialization
      const TwitterClient = require('../../src/clients/TwitterClient.js').TwitterClient;
      const ContentProcessor = require('../../src/processors/ContentProcessor.js').default;
      const TranslationService = require('../../src/services/TranslationService.js').default;
      const ArticleGenerator = require('../../src/generators/ArticleGenerator.js').default;
      const DuplicateChecker = require('../../src/utils/DuplicateChecker.js').default;
      const FileWriter = require('../../src/utils/FileWriter.js').default;
      const HugoBuilder = require('../../src/builders/HugoBuilder.js').default;

      TwitterClient.mockImplementation(() => ({
        searchTweets: jest.fn().mockResolvedValue([]),
        getRateLimitStatus: jest.fn().mockReturnValue({ windowRemainingMs: 0 })
      }));

      ContentProcessor.mockImplementation(() => ({
        processAndFilterTweets: jest.fn().mockReturnValue([])
      }));

      TranslationService.mockImplementation(() => ({
        translateText: jest.fn().mockResolvedValue('translated'),
        enhanceContent: jest.fn().mockResolvedValue('enhanced')
      }));

      ArticleGenerator.mockImplementation(() => ({
        generateArticle: jest.fn().mockResolvedValue({
          filename: 'test.md',
          fullContent: 'content',
          frontMatter: { title: 'Test' }
        })
      }));

      DuplicateChecker.mockImplementation(() => ({
        checkDuplicate: jest.fn().mockResolvedValue({ isDuplicate: false, contentHash: 'hash' }),
        updateProcessedList: jest.fn().mockResolvedValue(),
        cleanupOldEntries: jest.fn().mockResolvedValue()
      }));

      FileWriter.mockImplementation(() => ({
        validateFileContent: jest.fn().mockReturnValue(true),
        generateUniqueFilename: jest.fn().mockResolvedValue('unique.md'),
        writeArticleFile: jest.fn().mockResolvedValue('/path/to/file')
      }));

      HugoBuilder.mockImplementation(() => ({
        validateSiteConfiguration: jest.fn().mockResolvedValue(true),
        buildSite: jest.fn().mockResolvedValue({ success: true, buildTime: 1000, stats: { pages: 5 } })
      }));

      await automation.initialize();
    });

    test('should handle Twitter API errors with retry', async () => {
      const twitterClient = automation.components.twitterClient;
      
      // First call fails, second succeeds
      twitterClient.searchTweets
        .mockRejectedValueOnce(new Error('API temporarily unavailable'))
        .mockResolvedValueOnce([
          {
            id: '123',
            text: 'Test tweet',
            author: { username: 'test' },
            metrics: { retweetCount: 10, likeCount: 5, replyCount: 2 }
          }
        ]);

      const report = await automation.executeWorkflow();

      expect(report.success).toBe(true);
      expect(report.statistics.recoveredErrors).toBeGreaterThan(0);
      expect(twitterClient.searchTweets).toHaveBeenCalledTimes(2);
    });

    test('should handle rate limiting gracefully', async () => {
      const twitterClient = automation.components.twitterClient;
      
      const rateLimitError = new Error('Rate limit exceeded');
      rateLimitError.response = { status: 429 };
      
      twitterClient.searchTweets
        .mockRejectedValueOnce(rateLimitError)
        .mockResolvedValueOnce([]);

      twitterClient.getRateLimitStatus.mockReturnValue({
        windowRemainingMs: 100 // Short wait for testing
      });

      const report = await automation.executeWorkflow();

      expect(report.success).toBe(true);
      expect(twitterClient.searchTweets).toHaveBeenCalledTimes(2);
    });

    test('should handle translation failures with fallback', async () => {
      // Setup tweets to process
      automation.components.twitterClient.searchTweets.mockResolvedValue([
        {
          id: '123',
          text: 'Test tweet about crypto',
          author: { username: 'test' },
          metrics: { retweetCount: 10, likeCount: 5, replyCount: 2 }
        }
      ]);

      automation.components.contentProcessor.processAndFilterTweets.mockReturnValue([
        {
          id: '123',
          text: 'Test tweet about crypto',
          author: { username: 'test' },
          metrics: { retweetCount: 10, likeCount: 5, replyCount: 2 }
        }
      ]);

      // Translation fails
      automation.components.translationService.translateText
        .mockRejectedValue(new Error('Translation service unavailable'));

      const report = await automation.executeWorkflow();

      expect(report.success).toBe(true);
      expect(report.statistics.articlesGenerated).toBe(1);
      expect(report.statistics.recoveredErrors).toBeGreaterThan(0);
    });

    test('should handle file writing errors with retry', async () => {
      // Setup tweets and successful processing
      automation.components.twitterClient.searchTweets.mockResolvedValue([
        {
          id: '123',
          text: 'Test tweet',
          author: { username: 'test' },
          metrics: { retweetCount: 10, likeCount: 5, replyCount: 2 }
        }
      ]);

      automation.components.contentProcessor.processAndFilterTweets.mockReturnValue([
        {
          id: '123',
          text: 'Test tweet',
          author: { username: 'test' },
          metrics: { retweetCount: 10, likeCount: 5, replyCount: 2 }
        }
      ]);

      // File writing fails first time, succeeds second time
      automation.components.fileWriter.writeArticleFile
        .mockRejectedValueOnce(new Error('Disk full'))
        .mockResolvedValueOnce('/path/to/file');

      const report = await automation.executeWorkflow();

      expect(report.success).toBe(true);
      expect(report.statistics.articlesGenerated).toBe(1);
      expect(automation.components.fileWriter.writeArticleFile).toHaveBeenCalledTimes(2);
    });

    test('should handle Hugo build failures', async () => {
      // Setup successful article generation
      automation.components.twitterClient.searchTweets.mockResolvedValue([
        {
          id: '123',
          text: 'Test tweet',
          author: { username: 'test' },
          metrics: { retweetCount: 10, likeCount: 5, replyCount: 2 }
        }
      ]);

      automation.components.contentProcessor.processAndFilterTweets.mockReturnValue([
        {
          id: '123',
          text: 'Test tweet',
          author: { username: 'test' },
          metrics: { retweetCount: 10, likeCount: 5, replyCount: 2 }
        }
      ]);

      // Hugo build fails
      automation.components.hugoBuilder.buildSite
        .mockRejectedValue(new Error('Hugo not found'));

      await expect(automation.executeWorkflow()).rejects.toThrow('Hugo not found');
    });

    test('should send critical error notifications', async () => {
      const mockSendCriticalAlert = jest.fn().mockResolvedValue({ success: true });
      automation.notificationService.sendCriticalAlert = mockSendCriticalAlert;

      // Cause a critical error (authentication failure)
      const criticalError = new Error('Twitter API authentication failed');
      criticalError.response = { status: 401 };
      
      automation.components.twitterClient.searchTweets.mockRejectedValue(criticalError);

      await expect(automation.executeWorkflow()).rejects.toThrow();

      // Should have sent critical error notification
      expect(mockSendCriticalAlert).toHaveBeenCalledWith(
        expect.objectContaining({
          title: expect.stringContaining('Critical Error'),
          errorType: ErrorTypes.AUTHENTICATION
        })
      );
    });
  });

  describe('Error Statistics and Reporting', () => {
    beforeEach(async () => {
      // Setup basic mocks for initialization
      const TwitterClient = require('../../src/clients/TwitterClient.js').TwitterClient;
      TwitterClient.mockImplementation(() => ({
        searchTweets: jest.fn().mockResolvedValue([]),
        getRateLimitStatus: jest.fn().mockReturnValue({ windowRemainingMs: 0 })
      }));

      await automation.initialize();
    });

    test('should track error statistics correctly', async () => {
      // Simulate multiple errors
      automation.components.twitterClient.searchTweets
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Rate limit'))
        .mockResolvedValueOnce([]);

      const report = await automation.executeWorkflow();

      expect(report.statistics.errorsEncountered).toBeGreaterThan(0);
      expect(report.errorStatistics).toBeDefined();
      expect(report.hasErrors).toBe(true);
    });

    test('should include recovery statistics in report', async () => {
      // Simulate recoverable error
      automation.components.twitterClient.searchTweets
        .mockRejectedValueOnce(new Error('Temporary failure'))
        .mockResolvedValueOnce([]);

      const report = await automation.executeWorkflow();

      expect(report.statistics.recoveredErrors).toBeGreaterThan(0);
      expect(report.errorStatistics.recoveryRate).toBeDefined();
    });

    test('should format execution duration correctly', () => {
      automation.stats.startTime = new Date('2023-01-01T00:00:00.000Z');
      automation.stats.endTime = new Date('2023-01-01T00:01:30.500Z');

      const report = automation.generateReport();

      expect(report.executionTimeFormatted).toBe('1m 30s');
    });
  });

  describe('Cleanup and Resource Management', () => {
    beforeEach(async () => {
      // Setup basic mocks
      const TwitterClient = require('../../src/clients/TwitterClient.js').TwitterClient;
      TwitterClient.mockImplementation(() => ({
        searchTweets: jest.fn().mockResolvedValue([]),
        getRateLimitStatus: jest.fn().mockReturnValue({ windowRemainingMs: 0 })
      }));

      await automation.initialize();
    });

    test('should perform cleanup even when errors occur', async () => {
      const mockCleanupOldEntries = automation.components.duplicateChecker.cleanupOldEntries;
      
      // Cause an error in the workflow
      automation.components.twitterClient.searchTweets
        .mockRejectedValue(new Error('Fatal error'));

      try {
        await automation.executeWorkflow();
      } catch (error) {
        // Expected to fail
      }

      // Cleanup should still be called
      expect(mockCleanupOldEntries).toHaveBeenCalled();
    });

    test('should handle cleanup errors gracefully', async () => {
      automation.components.duplicateChecker.cleanupOldEntries
        .mockRejectedValue(new Error('Cleanup failed'));

      // Should not throw even if cleanup fails
      await expect(automation.executeWorkflow()).resolves.toBeDefined();
    });
  });

  describe('Concurrent Error Handling', () => {
    beforeEach(async () => {
      // Setup mocks for multiple tweets
      const TwitterClient = require('../../src/clients/TwitterClient.js').TwitterClient;
      TwitterClient.mockImplementation(() => ({
        searchTweets: jest.fn().mockResolvedValue([
          { id: '1', text: 'Tweet 1', author: { username: 'user1' }, metrics: { retweetCount: 10, likeCount: 5, replyCount: 2 } },
          { id: '2', text: 'Tweet 2', author: { username: 'user2' }, metrics: { retweetCount: 15, likeCount: 8, replyCount: 3 } },
          { id: '3', text: 'Tweet 3', author: { username: 'user3' }, metrics: { retweetCount: 20, likeCount: 12, replyCount: 5 } }
        ]),
        getRateLimitStatus: jest.fn().mockReturnValue({ windowRemainingMs: 0 })
      }));

      const ContentProcessor = require('../../src/processors/ContentProcessor.js').default;
      ContentProcessor.mockImplementation(() => ({
        processAndFilterTweets: jest.fn().mockImplementation(tweets => tweets)
      }));

      await automation.initialize();
    });

    test('should handle partial failures in article generation', async () => {
      // Setup translation to fail for second tweet only
      automation.components.translationService.translateText
        .mockResolvedValueOnce('Translation 1')
        .mockRejectedValueOnce(new Error('Translation failed'))
        .mockResolvedValueOnce('Translation 3');

      automation.components.translationService.enhanceContent
        .mockResolvedValue('Enhanced content');

      automation.components.articleGenerator.generateArticle
        .mockResolvedValue({
          filename: 'test.md',
          fullContent: 'content',
          frontMatter: { title: 'Test' }
        });

      const report = await automation.executeWorkflow();

      expect(report.success).toBe(true);
      expect(report.statistics.articlesGenerated).toBe(2); // 2 out of 3 succeeded
      expect(report.statistics.errorsEncountered).toBe(1);
    });
  });
});