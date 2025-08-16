import { jest } from '@jest/globals';
import { TwitterCryptoAutomation, Logger } from '../../src/index.js';

describe('TwitterCryptoAutomation Integration Tests', () => {
  let automation;

  beforeEach(() => {
    automation = new TwitterCryptoAutomation();
  });

  describe('Initialization', () => {
    test('should create automation instance', () => {
      expect(automation).toBeDefined();
      expect(automation.stats).toBeDefined();
      expect(automation.logger).toBeDefined();
    });

    test('should have proper initial state', () => {
      expect(automation.config).toBeNull();
      expect(automation.components).toEqual({});
      expect(automation.stats.startTime).toBeNull();
      expect(automation.stats.endTime).toBeNull();
      expect(automation.stats.tweetsFound).toBe(0);
      expect(automation.stats.tweetsProcessed).toBe(0);
      expect(automation.stats.articlesGenerated).toBe(0);
      expect(automation.stats.duplicatesSkipped).toBe(0);
      expect(automation.stats.errors).toEqual([]);
    });
  });

  describe('Report Generation', () => {
    test('should generate execution report', () => {
      automation.stats.startTime = new Date('2025-08-16T10:00:00Z');
      automation.stats.endTime = new Date('2025-08-16T10:01:00Z');
      automation.stats.tweetsFound = 5;
      automation.stats.tweetsProcessed = 4;
      automation.stats.articlesGenerated = 3;
      automation.stats.duplicatesSkipped = 1;
      automation.stats.errors = [];

      const report = automation.generateReport();

      expect(report).toHaveProperty('executionTime');
      expect(report).toHaveProperty('startTime');
      expect(report).toHaveProperty('endTime');
      expect(report).toHaveProperty('statistics');
      expect(report).toHaveProperty('errors');
      expect(report).toHaveProperty('success');
      
      expect(report.statistics.tweetsFound).toBe(5);
      expect(report.statistics.tweetsProcessed).toBe(4);
      expect(report.statistics.articlesGenerated).toBe(3);
      expect(report.statistics.duplicatesSkipped).toBe(1);
      expect(report.statistics.errorsEncountered).toBe(0);
      expect(report.success).toBe(true);
    });

    test('should mark as failed when no articles generated', () => {
      automation.stats.startTime = new Date();
      automation.stats.endTime = new Date();
      automation.stats.articlesGenerated = 0;
      automation.stats.errors = [];

      const report = automation.generateReport();

      expect(report.success).toBe(false);
    });

    test('should mark as failed when errors occurred', () => {
      automation.stats.startTime = new Date();
      automation.stats.endTime = new Date();
      automation.stats.articlesGenerated = 1;
      automation.stats.errors = [{ step: 'test', error: 'test error' }];

      const report = automation.generateReport();

      expect(report.success).toBe(false);
      expect(report.statistics.errorsEncountered).toBe(1);
    });
  });


});

describe('Logger', () => {
  let logger;
  let consoleSpy;

  beforeEach(() => {
    logger = new Logger();
    consoleSpy = jest.spyOn(console, 'log').mockImplementation();
  });

  afterEach(() => {
    consoleSpy.mockRestore();
  });

  test('should log messages with timestamp and level', () => {
    logger.info('Test message');

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringMatching(/\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\] \[INFO\]/),
      'Test message'
    );
  });

  test('should respect log level filtering', () => {
    logger.logLevel = 'warn';
    
    logger.debug('Debug message');
    logger.info('Info message');
    logger.warn('Warn message');
    logger.error('Error message');

    expect(consoleSpy).not.toHaveBeenCalledWith(
      expect.stringContaining('[DEBUG]'),
      'Debug message'
    );
    expect(consoleSpy).not.toHaveBeenCalledWith(
      expect.stringContaining('[INFO]'),
      'Info message'
    );
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('[WARN]'),
      'Warn message'
    );
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('[ERROR]'),
      'Error message'
    );
  });

  test('should handle additional arguments', () => {
    const errorObj = new Error('Test error');
    logger.error('Error occurred:', errorObj);

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('[ERROR]'),
      'Error occurred:',
      errorObj
    );
  });
});