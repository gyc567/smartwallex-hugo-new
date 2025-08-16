import ErrorHandler, { ErrorTypes, ErrorSeverity, TwitterAutomationError } from '../../src/utils/ErrorHandler.js';
import Logger from '../../src/utils/Logger.js';

describe('ErrorHandler', () => {
  let errorHandler;
  let mockLogger;
  let mockNotificationService;

  beforeEach(() => {
    mockLogger = {
      info: jest.fn(),
      warn: jest.fn(),
      error: jest.fn(),
      debug: jest.fn()
    };

    mockNotificationService = {
      sendCriticalAlert: jest.fn().mockResolvedValue({ success: true })
    };

    errorHandler = new ErrorHandler(mockLogger, mockNotificationService);
  });

  describe('Error Classification', () => {
    test('should classify rate limit errors correctly', () => {
      const error = new Error('Rate limit exceeded');
      const classified = errorHandler.classifyError(error);
      expect(classified).toBe(ErrorTypes.RATE_LIMIT);
    });

    test('should classify authentication errors correctly', () => {
      const error = { message: 'Unauthorized access', response: { status: 401 } };
      const classified = errorHandler.classifyError(error);
      expect(classified).toBe(ErrorTypes.AUTHENTICATION);
    });

    test('should classify network errors correctly', () => {
      const error = { message: 'Network timeout', code: 'ECONNABORTED' };
      const classified = errorHandler.classifyError(error);
      expect(classified).toBe(ErrorTypes.NETWORK);
    });

    test('should classify file system errors correctly', () => {
      const error = { message: 'File not found', code: 'ENOENT' };
      const classified = errorHandler.classifyError(error);
      expect(classified).toBe(ErrorTypes.FILE_SYSTEM);
    });

    test('should classify translation errors correctly', () => {
      const error = new Error('Translation service failed');
      const classified = errorHandler.classifyError(error);
      expect(classified).toBe(ErrorTypes.TRANSLATION);
    });

    test('should classify build errors correctly', () => {
      const error = new Error('Hugo build failed');
      const classified = errorHandler.classifyError(error);
      expect(classified).toBe(ErrorTypes.BUILD);
    });

    test('should classify unknown errors as UNKNOWN', () => {
      const error = new Error('Some random error');
      const classified = errorHandler.classifyError(error);
      expect(classified).toBe(ErrorTypes.UNKNOWN);
    });
  });

  describe('Error Severity Determination', () => {
    test('should assign CRITICAL severity to authentication errors', () => {
      const severity = errorHandler.determineSeverity(
        new Error('Authentication failed'),
        ErrorTypes.AUTHENTICATION
      );
      expect(severity).toBe(ErrorSeverity.CRITICAL);
    });

    test('should assign HIGH severity to API errors', () => {
      const severity = errorHandler.determineSeverity(
        new Error('API call failed'),
        ErrorTypes.API_ERROR
      );
      expect(severity).toBe(ErrorSeverity.HIGH);
    });

    test('should assign MEDIUM severity to rate limit errors', () => {
      const severity = errorHandler.determineSeverity(
        new Error('Rate limit exceeded'),
        ErrorTypes.RATE_LIMIT
      );
      expect(severity).toBe(ErrorSeverity.MEDIUM);
    });

    test('should assign LOW severity to unknown errors', () => {
      const severity = errorHandler.determineSeverity(
        new Error('Unknown error'),
        ErrorTypes.UNKNOWN
      );
      expect(severity).toBe(ErrorSeverity.LOW);
    });
  });

  describe('Error Enhancement', () => {
    test('should enhance regular errors with metadata', () => {
      const originalError = new Error('Test error');
      const enhanced = errorHandler.enhanceError(originalError, 'test_context', { extra: 'data' });

      expect(enhanced).toBeInstanceOf(TwitterAutomationError);
      expect(enhanced.message).toBe('Test error');
      expect(enhanced.metadata.context).toBe('test_context');
      expect(enhanced.metadata.extra).toBe('data');
      expect(enhanced.timestamp).toBeDefined();
    });

    test('should not re-enhance TwitterAutomationError', () => {
      const originalError = new TwitterAutomationError('Test error', ErrorTypes.API_ERROR);
      const enhanced = errorHandler.enhanceError(originalError, 'test_context');

      expect(enhanced).toBe(originalError);
    });
  });

  describe('Recovery Strategy Determination', () => {
    test('should provide recovery strategy for rate limit errors', () => {
      const error = new TwitterAutomationError('Rate limit', ErrorTypes.RATE_LIMIT);
      const strategy = errorHandler.determineRecoveryStrategy(error);

      expect(strategy.canRecover).toBe(true);
      expect(strategy.strategy).toBe('wait_and_retry');
    });

    test('should provide recovery strategy for network errors', () => {
      const error = new TwitterAutomationError('Network error', ErrorTypes.NETWORK);
      const strategy = errorHandler.determineRecoveryStrategy(error);

      expect(strategy.canRecover).toBe(true);
      expect(strategy.strategy).toBe('exponential_backoff');
    });

    test('should not provide recovery for authentication errors', () => {
      const error = new TwitterAutomationError('Auth error', ErrorTypes.AUTHENTICATION);
      const strategy = errorHandler.determineRecoveryStrategy(error);

      expect(strategy.canRecover).toBe(false);
      expect(strategy.strategy).toBe('manual_intervention');
    });
  });

  describe('Error Handling', () => {
    test('should handle error and update statistics', async () => {
      const error = new Error('Test error');
      const result = await errorHandler.handleError(error, 'test_context');

      expect(result.error).toBeInstanceOf(TwitterAutomationError);
      expect(errorHandler.errorStats.totalErrors).toBe(1);
      expect(mockLogger.error).toHaveBeenCalled();
    });

    test('should send critical error notifications', async () => {
      const criticalError = new TwitterAutomationError(
        'Critical error',
        ErrorTypes.AUTHENTICATION,
        ErrorSeverity.CRITICAL
      );

      await errorHandler.handleError(criticalError, 'test_context');

      expect(mockNotificationService.sendCriticalAlert).toHaveBeenCalledWith(
        expect.objectContaining({
          title: expect.stringContaining('Critical Error'),
          message: 'Critical error'
        })
      );
    });

    test('should not send notifications for non-critical errors', async () => {
      const error = new Error('Non-critical error');
      await errorHandler.handleError(error, 'test_context');

      expect(mockNotificationService.sendCriticalAlert).not.toHaveBeenCalled();
    });
  });

  describe('Retry Logic', () => {
    test('should execute operation with retry on failure', async () => {
      let attempts = 0;
      const operation = jest.fn().mockImplementation(() => {
        attempts++;
        if (attempts < 3) {
          throw new Error('Temporary failure');
        }
        return 'success';
      });

      const result = await errorHandler.executeWithRetry(
        operation,
        'test_operation',
        ErrorTypes.API_ERROR
      );

      expect(result).toBe('success');
      expect(operation).toHaveBeenCalledTimes(3);
    });

    test('should fail after max retries', async () => {
      const operation = jest.fn().mockRejectedValue(new Error('Persistent failure'));

      await expect(
        errorHandler.executeWithRetry(operation, 'test_operation', ErrorTypes.API_ERROR)
      ).rejects.toThrow('Persistent failure');

      expect(operation).toHaveBeenCalledTimes(4); // 1 initial + 3 retries
    });

    test('should succeed on first attempt', async () => {
      const operation = jest.fn().mockResolvedValue('immediate_success');

      const result = await errorHandler.executeWithRetry(
        operation,
        'test_operation',
        ErrorTypes.API_ERROR
      );

      expect(result).toBe('immediate_success');
      expect(operation).toHaveBeenCalledTimes(1);
    });
  });

  describe('Backoff Calculation', () => {
    test('should calculate exponential backoff correctly', () => {
      const config = {
        baseDelay: 1000,
        backoffMultiplier: 2,
        maxDelay: 10000
      };

      expect(errorHandler.calculateBackoffDelay(0, config)).toBe(1000);
      expect(errorHandler.calculateBackoffDelay(1, config)).toBe(2000);
      expect(errorHandler.calculateBackoffDelay(2, config)).toBe(4000);
      expect(errorHandler.calculateBackoffDelay(3, config)).toBe(8000);
    });

    test('should respect maximum delay', () => {
      const config = {
        baseDelay: 1000,
        backoffMultiplier: 2,
        maxDelay: 5000
      };

      expect(errorHandler.calculateBackoffDelay(10, config)).toBe(5000);
    });
  });

  describe('Recovery Execution', () => {
    test('should execute rate limit recovery', async () => {
      const error = new TwitterAutomationError(
        'Rate limit',
        ErrorTypes.RATE_LIMIT,
        ErrorSeverity.MEDIUM,
        { resetTime: Date.now() + 1000 }
      );

      const strategy = { strategy: 'wait_and_retry' };
      const result = await errorHandler.executeRecovery(error, strategy);

      expect(result.success).toBe(true);
    });

    test('should execute network recovery', async () => {
      const error = new TwitterAutomationError('Network error', ErrorTypes.NETWORK);
      const strategy = { strategy: 'exponential_backoff' };
      
      const result = await errorHandler.executeRecovery(error, strategy);

      expect(result.success).toBe(true);
    });

    test('should execute translation recovery', async () => {
      const error = new TwitterAutomationError('Translation error', ErrorTypes.TRANSLATION);
      const strategy = { strategy: 'fallback_translation' };
      
      const result = await errorHandler.executeRecovery(error, strategy);

      expect(result.success).toBe(true);
      expect(result.fallbackMode).toBe(true);
    });

    test('should handle unknown recovery strategy', async () => {
      const error = new TwitterAutomationError('Unknown error', ErrorTypes.UNKNOWN);
      const strategy = { strategy: 'unknown_strategy' };
      
      const result = await errorHandler.executeRecovery(error, strategy);

      expect(result.success).toBe(false);
    });
  });

  describe('Error Statistics', () => {
    test('should track error statistics correctly', async () => {
      await errorHandler.handleError(new Error('Error 1'), 'context1');
      await errorHandler.handleError(new Error('Error 2'), 'context2');
      
      const stats = errorHandler.getErrorStats();

      expect(stats.totalErrors).toBe(2);
      expect(stats.recoveryRate).toBe('0%');
    });

    test('should calculate recovery rate correctly', async () => {
      // Simulate some recovered errors
      errorHandler.errorStats.totalErrors = 10;
      errorHandler.errorStats.recoveredErrors = 3;

      const stats = errorHandler.getErrorStats();

      expect(stats.recoveryRate).toBe('30.00%');
    });
  });

  describe('TwitterAutomationError', () => {
    test('should create error with all properties', () => {
      const error = new TwitterAutomationError(
        'Test message',
        ErrorTypes.API_ERROR,
        ErrorSeverity.HIGH,
        { extra: 'data' }
      );

      expect(error.message).toBe('Test message');
      expect(error.type).toBe(ErrorTypes.API_ERROR);
      expect(error.severity).toBe(ErrorSeverity.HIGH);
      expect(error.metadata.extra).toBe('data');
      expect(error.timestamp).toBeDefined();
    });

    test('should serialize to JSON correctly', () => {
      const error = new TwitterAutomationError(
        'Test message',
        ErrorTypes.API_ERROR,
        ErrorSeverity.HIGH,
        { extra: 'data' }
      );

      const json = error.toJSON();

      expect(json.name).toBe('TwitterAutomationError');
      expect(json.message).toBe('Test message');
      expect(json.type).toBe(ErrorTypes.API_ERROR);
      expect(json.severity).toBe(ErrorSeverity.HIGH);
      expect(json.metadata.extra).toBe('data');
    });
  });
});