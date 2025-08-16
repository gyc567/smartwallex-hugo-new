import Logger, { LogLevels, LogLevelNames } from '../../src/utils/Logger.js';
import fs from 'fs-extra';
import path from 'path';

// Mock fs-extra
jest.mock('fs-extra');

describe('Logger', () => {
  let logger;
  let consoleSpy;
  const testLogDir = 'test-logs';

  beforeEach(() => {
    // Mock console methods
    consoleSpy = {
      log: jest.spyOn(console, 'log').mockImplementation(),
      error: jest.spyOn(console, 'error').mockImplementation(),
      warn: jest.spyOn(console, 'warn').mockImplementation(),
      info: jest.spyOn(console, 'info').mockImplementation()
    };

    // Mock fs-extra methods
    fs.ensureDir.mockResolvedValue();
    fs.readdir.mockResolvedValue([]);
    fs.stat.mockResolvedValue({ mtime: new Date(), size: 1000 });
    fs.appendFile.mockResolvedValue();
    fs.remove.mockResolvedValue();
    fs.move.mockResolvedValue();

    logger = new Logger({
      level: 'DEBUG',
      logDir: testLogDir,
      enableFile: false // Disable file logging for most tests
    });
  });

  afterEach(() => {
    // Restore console methods
    Object.values(consoleSpy).forEach(spy => spy.mockRestore());
    jest.clearAllMocks();
  });

  describe('Log Level Parsing', () => {
    test('should parse valid log levels correctly', () => {
      expect(new Logger({ level: 'ERROR' }).logLevel).toBe(LogLevels.ERROR);
      expect(new Logger({ level: 'WARN' }).logLevel).toBe(LogLevels.WARN);
      expect(new Logger({ level: 'INFO' }).logLevel).toBe(LogLevels.INFO);
      expect(new Logger({ level: 'DEBUG' }).logLevel).toBe(LogLevels.DEBUG);
      expect(new Logger({ level: 'TRACE' }).logLevel).toBe(LogLevels.TRACE);
    });

    test('should default to INFO for invalid log levels', () => {
      expect(new Logger({ level: 'INVALID' }).logLevel).toBe(LogLevels.INFO);
    });

    test('should handle lowercase log levels', () => {
      expect(new Logger({ level: 'debug' }).logLevel).toBe(LogLevels.DEBUG);
    });
  });

  describe('Log Entry Creation', () => {
    test('should create structured log entry', () => {
      const entry = logger.createLogEntry(LogLevels.INFO, 'Test message', { extra: 'data' });

      expect(entry.timestamp).toBeDefined();
      expect(entry.level).toBe('INFO');
      expect(entry.message).toBe('Test message');
      expect(entry.extra).toBe('data');
      expect(entry.process).toBeDefined();
      expect(entry.process.pid).toBe(process.pid);
    });

    test('should include stack trace for errors', () => {
      const errorLogger = new Logger({ includeStackTrace: true });
      const entry = errorLogger.createLogEntry(LogLevels.ERROR, 'Error message');

      expect(entry.stack).toBeDefined();
      expect(Array.isArray(entry.stack)).toBe(true);
    });

    test('should not include stack trace when disabled', () => {
      const errorLogger = new Logger({ includeStackTrace: false });
      const entry = errorLogger.createLogEntry(LogLevels.ERROR, 'Error message');

      expect(entry.stack).toBeUndefined();
    });
  });

  describe('Log Formatting', () => {
    test('should format log entry as JSON', () => {
      const jsonLogger = new Logger({ format: 'json' });
      const entry = { timestamp: '2023-01-01T00:00:00.000Z', level: 'INFO', message: 'Test' };
      const formatted = jsonLogger.formatLogEntry(entry);

      expect(() => JSON.parse(formatted)).not.toThrow();
      const parsed = JSON.parse(formatted);
      expect(parsed.level).toBe('INFO');
      expect(parsed.message).toBe('Test');
    });

    test('should format log entry as text', () => {
      const textLogger = new Logger({ format: 'text' });
      const entry = { 
        timestamp: '2023-01-01T00:00:00.000Z', 
        level: 'INFO', 
        message: 'Test message',
        extra: 'data'
      };
      const formatted = textLogger.formatLogEntry(entry);

      expect(formatted).toContain('[2023-01-01T00:00:00.000Z]');
      expect(formatted).toContain('[INFO ]');
      expect(formatted).toContain('Test message');
      expect(formatted).toContain('"extra":"data"');
    });

    test('should include stack trace in text format', () => {
      const textLogger = new Logger({ format: 'text' });
      const entry = { 
        timestamp: '2023-01-01T00:00:00.000Z', 
        level: 'ERROR', 
        message: 'Error message',
        stack: ['line1', 'line2', 'line3']
      };
      const formatted = textLogger.formatLogEntry(entry);

      expect(formatted).toContain('line1\nline2\nline3');
    });
  });

  describe('Console Output', () => {
    test('should write to console when enabled', async () => {
      await logger.info('Test message');

      expect(consoleSpy.info).toHaveBeenCalledWith(
        expect.stringContaining('[INFO ]'),
        expect.stringContaining('Test message')
      );
    });

    test('should not write to console when disabled', async () => {
      const noConsoleLogger = new Logger({ enableConsole: false });
      await noConsoleLogger.info('Test message');

      expect(consoleSpy.info).not.toHaveBeenCalled();
    });

    test('should use appropriate console method for each level', async () => {
      await logger.error('Error message');
      await logger.warn('Warning message');
      await logger.info('Info message');
      await logger.debug('Debug message');

      expect(consoleSpy.error).toHaveBeenCalled();
      expect(consoleSpy.warn).toHaveBeenCalled();
      expect(consoleSpy.info).toHaveBeenCalled();
      expect(consoleSpy.log).toHaveBeenCalled(); // debug uses console.log
    });
  });

  describe('Log Level Filtering', () => {
    test('should filter logs based on level', async () => {
      const infoLogger = new Logger({ level: 'INFO' });

      await infoLogger.error('Error message');
      await infoLogger.warn('Warning message');
      await infoLogger.info('Info message');
      await infoLogger.debug('Debug message');

      expect(consoleSpy.error).toHaveBeenCalled();
      expect(consoleSpy.warn).toHaveBeenCalled();
      expect(consoleSpy.info).toHaveBeenCalled();
      expect(consoleSpy.log).not.toHaveBeenCalled(); // debug should be filtered
    });

    test('should allow all logs at TRACE level', async () => {
      const traceLogger = new Logger({ level: 'TRACE' });

      await traceLogger.error('Error message');
      await traceLogger.warn('Warning message');
      await traceLogger.info('Info message');
      await traceLogger.debug('Debug message');
      await traceLogger.trace('Trace message');

      expect(consoleSpy.error).toHaveBeenCalled();
      expect(consoleSpy.warn).toHaveBeenCalled();
      expect(consoleSpy.info).toHaveBeenCalled();
      expect(consoleSpy.log).toHaveBeenCalledTimes(2); // debug and trace
    });
  });

  describe('Error Object Handling', () => {
    test('should handle Error objects in metadata', async () => {
      const error = new Error('Test error');
      error.code = 'TEST_CODE';

      await logger.error('Error occurred', error);

      expect(consoleSpy.error).toHaveBeenCalledWith(
        expect.stringContaining('Error occurred'),
        expect.objectContaining({
          errorName: 'Error',
          errorMessage: 'Test error'
        })
      );
    });

    test('should handle regular metadata objects', async () => {
      await logger.info('Info message', { key: 'value', number: 42 });

      expect(consoleSpy.info).toHaveBeenCalledWith(
        expect.stringContaining('Info message'),
        expect.objectContaining({
          key: 'value',
          number: 42
        })
      );
    });
  });

  describe('File Logging', () => {
    test('should initialize file logging when enabled', async () => {
      const fileLogger = new Logger({ 
        enableFile: true, 
        logDir: testLogDir 
      });

      await fileLogger.initializeFileLogging();

      expect(fs.ensureDir).toHaveBeenCalledWith(testLogDir);
    });

    test('should write to file when enabled', async () => {
      const fileLogger = new Logger({ 
        enableFile: true, 
        logDir: testLogDir 
      });
      
      // Mock the file paths
      fileLogger.logFiles.combined = path.join(testLogDir, 'test.log');
      
      await fileLogger.info('Test message');

      expect(fs.appendFile).toHaveBeenCalledWith(
        fileLogger.logFiles.combined,
        expect.stringContaining('Test message')
      );
    });

    test('should write errors to separate error log', async () => {
      const fileLogger = new Logger({ 
        enableFile: true, 
        logDir: testLogDir 
      });
      
      // Mock the file paths
      fileLogger.logFiles.combined = path.join(testLogDir, 'test.log');
      fileLogger.logFiles.error = path.join(testLogDir, 'error.log');
      
      await fileLogger.error('Error message');

      expect(fs.appendFile).toHaveBeenCalledWith(
        fileLogger.logFiles.combined,
        expect.stringContaining('Error message')
      );
      expect(fs.appendFile).toHaveBeenCalledWith(
        fileLogger.logFiles.error,
        expect.stringContaining('Error message')
      );
    });

    test('should handle file write errors gracefully', async () => {
      const fileLogger = new Logger({ 
        enableFile: true, 
        logDir: testLogDir 
      });
      
      fileLogger.logFiles.combined = path.join(testLogDir, 'test.log');
      fs.appendFile.mockRejectedValue(new Error('Write failed'));

      // Should not throw
      await expect(fileLogger.info('Test message')).resolves.not.toThrow();
      expect(consoleSpy.error).toHaveBeenCalledWith(
        expect.stringContaining('Failed to write to log file')
      );
    });
  });

  describe('Child Logger', () => {
    test('should create child logger with additional context', async () => {
      const childLogger = logger.child({ component: 'test', requestId: '123' });

      await childLogger.info('Child message');

      expect(consoleSpy.info).toHaveBeenCalledWith(
        expect.stringContaining('Child message'),
        expect.objectContaining({
          component: 'test',
          requestId: '123'
        })
      );
    });

    test('should merge context with log metadata', async () => {
      const childLogger = logger.child({ component: 'test' });

      await childLogger.info('Child message', { extra: 'data' });

      expect(consoleSpy.info).toHaveBeenCalledWith(
        expect.stringContaining('Child message'),
        expect.objectContaining({
          component: 'test',
          extra: 'data'
        })
      );
    });
  });

  describe('Performance Timer', () => {
    test('should create and end timer', async () => {
      const timer = logger.timer('test-operation');

      // Simulate some work
      await new Promise(resolve => setTimeout(resolve, 10));

      const duration = await timer.end({ result: 'success' });

      expect(duration).toBeGreaterThan(0);
      expect(consoleSpy.info).toHaveBeenCalledWith(
        expect.stringContaining('Timer: test-operation'),
        expect.objectContaining({
          duration: expect.stringMatching(/\d+\.\d+ms/),
          result: 'success'
        })
      );
    });
  });

  describe('System Information Logging', () => {
    test('should log system information', async () => {
      await logger.logSystemInfo();

      expect(consoleSpy.info).toHaveBeenCalledWith(
        expect.stringContaining('System Information'),
        expect.objectContaining({
          nodeVersion: process.version,
          platform: process.platform,
          arch: process.arch
        })
      );
    });
  });

  describe('Log Rotation', () => {
    test('should rotate logs when files exceed size limit', async () => {
      const fileLogger = new Logger({ 
        enableFile: true, 
        logDir: testLogDir,
        maxFileSize: 1000,
        maxFiles: 3
      });

      // Mock file stats to simulate large files
      fs.stat.mockResolvedValue({ mtime: new Date(), size: 2000 });
      fs.readdir.mockResolvedValue(['automation-2023-01-01.log']);

      await fileLogger.rotateLogs();

      expect(fs.move).toHaveBeenCalled();
    });

    test('should remove old files when exceeding maxFiles', async () => {
      const fileLogger = new Logger({ 
        enableFile: true, 
        logDir: testLogDir,
        maxFiles: 2
      });

      // Mock multiple log files
      fs.readdir.mockResolvedValue([
        'automation-2023-01-01.log',
        'automation-2023-01-02.log',
        'automation-2023-01-03.log'
      ]);

      fs.stat.mockImplementation((filePath) => {
        const fileName = path.basename(filePath);
        const date = fileName.includes('01-01') ? new Date('2023-01-01') :
                     fileName.includes('01-02') ? new Date('2023-01-02') :
                     new Date('2023-01-03');
        return Promise.resolve({ mtime: date, size: 1000 });
      });

      await fileLogger.rotateLogs();

      expect(fs.remove).toHaveBeenCalledWith(
        expect.stringContaining('automation-2023-01-01.log')
      );
    });
  });

  describe('Resource Management', () => {
    test('should flush logs', async () => {
      await expect(logger.flush()).resolves.not.toThrow();
    });

    test('should close logger', async () => {
      await expect(logger.close()).resolves.not.toThrow();
    });
  });
});