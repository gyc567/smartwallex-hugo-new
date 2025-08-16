import fs from 'fs-extra';
import path from 'path';

/**
 * Log levels with numeric values for comparison
 */
export const LogLevels = {
  ERROR: 0,
  WARN: 1,
  INFO: 2,
  DEBUG: 3,
  TRACE: 4
};

/**
 * Log level names
 */
export const LogLevelNames = {
  0: 'ERROR',
  1: 'WARN',
  2: 'INFO',
  3: 'DEBUG',
  4: 'TRACE'
};

/**
 * Enhanced logging system with multiple outputs and structured logging
 */
export class Logger {
  constructor(options = {}) {
    this.options = {
      level: options.level || process.env.LOG_LEVEL || 'INFO',
      enableConsole: options.enableConsole !== false,
      enableFile: options.enableFile !== false,
      logDir: options.logDir || 'logs',
      maxFileSize: options.maxFileSize || 10 * 1024 * 1024, // 10MB
      maxFiles: options.maxFiles || 5,
      format: options.format || 'json', // 'json' or 'text'
      includeStackTrace: options.includeStackTrace !== false,
      ...options
    };

    this.logLevel = this.parseLogLevel(this.options.level);
    this.logFiles = {
      combined: null,
      error: null
    };

    this.initializeFileLogging();
  }

  /**
   * Parse log level string to numeric value
   * @param {string} level - Log level string
   * @returns {number} Numeric log level
   */
  parseLogLevel(level) {
    const upperLevel = level.toUpperCase();
    return LogLevels[upperLevel] !== undefined ? LogLevels[upperLevel] : LogLevels.INFO;
  }

  /**
   * Initialize file logging if enabled
   */
  async initializeFileLogging() {
    if (!this.options.enableFile) return;

    try {
      // Ensure log directory exists
      await fs.ensureDir(this.options.logDir);

      // Initialize log files
      const timestamp = new Date().toISOString().split('T')[0];
      this.logFiles.combined = path.join(this.options.logDir, `automation-${timestamp}.log`);
      this.logFiles.error = path.join(this.options.logDir, `automation-error-${timestamp}.log`);

      // Rotate logs if needed
      await this.rotateLogs();
    } catch (error) {
      console.error('Failed to initialize file logging:', error.message);
      this.options.enableFile = false;
    }
  }

  /**
   * Rotate log files if they exceed size limits
   */
  async rotateLogs() {
    try {
      const files = await fs.readdir(this.options.logDir);
      const logFiles = files.filter(file => file.startsWith('automation-') && file.endsWith('.log'));

      // Sort by modification time (newest first)
      const fileStats = await Promise.all(
        logFiles.map(async file => {
          const filePath = path.join(this.options.logDir, file);
          const stats = await fs.stat(filePath);
          return { file, path: filePath, mtime: stats.mtime, size: stats.size };
        })
      );

      fileStats.sort((a, b) => b.mtime - a.mtime);

      // Remove old files if we exceed maxFiles
      if (fileStats.length > this.options.maxFiles) {
        const filesToRemove = fileStats.slice(this.options.maxFiles);
        for (const fileInfo of filesToRemove) {
          await fs.remove(fileInfo.path);
        }
      }

      // Check if current files need rotation due to size
      for (const fileInfo of fileStats.slice(0, this.options.maxFiles)) {
        if (fileInfo.size > this.options.maxFileSize) {
          const rotatedName = fileInfo.file.replace('.log', `-${Date.now()}.log`);
          const rotatedPath = path.join(this.options.logDir, rotatedName);
          await fs.move(fileInfo.path, rotatedPath);
        }
      }
    } catch (error) {
      console.error('Log rotation failed:', error.message);
    }
  }

  /**
   * Create structured log entry
   * @param {number} level - Log level
   * @param {string} message - Log message
   * @param {Object} metadata - Additional metadata
   * @returns {Object} Structured log entry
   */
  createLogEntry(level, message, metadata = {}) {
    const timestamp = new Date().toISOString();
    const levelName = LogLevelNames[level];

    const entry = {
      timestamp,
      level: levelName,
      message,
      ...metadata
    };

    // Add stack trace for errors if enabled
    if (level === LogLevels.ERROR && this.options.includeStackTrace) {
      const stack = new Error().stack;
      entry.stack = stack.split('\n').slice(2); // Remove Error constructor lines
    }

    // Add process information
    entry.process = {
      pid: process.pid,
      memory: process.memoryUsage(),
      uptime: process.uptime()
    };

    return entry;
  }

  /**
   * Format log entry for output
   * @param {Object} entry - Log entry
   * @returns {string} Formatted log string
   */
  formatLogEntry(entry) {
    if (this.options.format === 'json') {
      return JSON.stringify(entry);
    }

    // Text format
    const timestamp = entry.timestamp;
    const level = entry.level.padEnd(5);
    const message = entry.message;
    
    let formatted = `[${timestamp}] [${level}] ${message}`;

    // Add metadata if present
    const metadata = { ...entry };
    delete metadata.timestamp;
    delete metadata.level;
    delete metadata.message;
    delete metadata.process;
    delete metadata.stack;

    if (Object.keys(metadata).length > 0) {
      formatted += ` | ${JSON.stringify(metadata)}`;
    }

    // Add stack trace for errors
    if (entry.stack && Array.isArray(entry.stack)) {
      formatted += '\n' + entry.stack.join('\n');
    }

    return formatted;
  }

  /**
   * Write log entry to console
   * @param {Object} entry - Log entry
   */
  writeToConsole(entry) {
    if (!this.options.enableConsole) return;

    const formatted = this.formatLogEntry(entry);

    switch (entry.level) {
      case 'ERROR':
        console.error(formatted);
        break;
      case 'WARN':
        console.warn(formatted);
        break;
      case 'INFO':
        console.info(formatted);
        break;
      case 'DEBUG':
      case 'TRACE':
        console.log(formatted);
        break;
      default:
        console.log(formatted);
    }
  }

  /**
   * Write log entry to file
   * @param {Object} entry - Log entry
   */
  async writeToFile(entry) {
    if (!this.options.enableFile || !this.logFiles.combined) return;

    try {
      const formatted = this.formatLogEntry(entry) + '\n';

      // Write to combined log
      await fs.appendFile(this.logFiles.combined, formatted);

      // Write errors to separate error log
      if (entry.level === 'ERROR' && this.logFiles.error) {
        await fs.appendFile(this.logFiles.error, formatted);
      }
    } catch (error) {
      console.error('Failed to write to log file:', error.message);
    }
  }

  /**
   * Core logging method
   * @param {number} level - Log level
   * @param {string} message - Log message
   * @param {Object} metadata - Additional metadata
   */
  async log(level, message, metadata = {}) {
    // Check if this log level should be output
    if (level > this.logLevel) return;

    const entry = this.createLogEntry(level, message, metadata);

    // Output to console
    this.writeToConsole(entry);

    // Output to file
    await this.writeToFile(entry);
  }

  /**
   * Log error message
   * @param {string} message - Error message
   * @param {Object|Error} metadata - Additional metadata or Error object
   */
  async error(message, metadata = {}) {
    // Handle Error objects
    if (metadata instanceof Error) {
      const errorMetadata = {
        errorName: metadata.name,
        errorMessage: metadata.message,
        errorStack: metadata.stack?.split('\n'),
        ...metadata
      };
      await this.log(LogLevels.ERROR, message, errorMetadata);
    } else {
      await this.log(LogLevels.ERROR, message, metadata);
    }
  }

  /**
   * Log warning message
   * @param {string} message - Warning message
   * @param {Object} metadata - Additional metadata
   */
  async warn(message, metadata = {}) {
    await this.log(LogLevels.WARN, message, metadata);
  }

  /**
   * Log info message
   * @param {string} message - Info message
   * @param {Object} metadata - Additional metadata
   */
  async info(message, metadata = {}) {
    await this.log(LogLevels.INFO, message, metadata);
  }

  /**
   * Log debug message
   * @param {string} message - Debug message
   * @param {Object} metadata - Additional metadata
   */
  async debug(message, metadata = {}) {
    await this.log(LogLevels.DEBUG, message, metadata);
  }

  /**
   * Log trace message
   * @param {string} message - Trace message
   * @param {Object} metadata - Additional metadata
   */
  async trace(message, metadata = {}) {
    await this.log(LogLevels.TRACE, message, metadata);
  }

  /**
   * Create a child logger with additional context
   * @param {Object} context - Additional context to include in all logs
   * @returns {Logger} Child logger instance
   */
  child(context = {}) {
    const childLogger = new Logger(this.options);
    childLogger.logLevel = this.logLevel;
    childLogger.logFiles = this.logFiles;
    childLogger.defaultContext = { ...this.defaultContext, ...context };
    
    // Override log method to include default context
    const originalLog = childLogger.log.bind(childLogger);
    childLogger.log = async (level, message, metadata = {}) => {
      const mergedMetadata = { ...childLogger.defaultContext, ...metadata };
      return originalLog(level, message, mergedMetadata);
    };

    return childLogger;
  }

  /**
   * Create performance timer
   * @param {string} label - Timer label
   * @returns {Object} Timer object with end method
   */
  timer(label) {
    const startTime = process.hrtime.bigint();
    const startTimestamp = new Date().toISOString();

    return {
      end: async (metadata = {}) => {
        const endTime = process.hrtime.bigint();
        const duration = Number(endTime - startTime) / 1000000; // Convert to milliseconds

        await this.info(`Timer: ${label}`, {
          duration: `${duration.toFixed(2)}ms`,
          startTime: startTimestamp,
          endTime: new Date().toISOString(),
          ...metadata
        });

        return duration;
      }
    };
  }

  /**
   * Log system information
   */
  async logSystemInfo() {
    const systemInfo = {
      nodeVersion: process.version,
      platform: process.platform,
      arch: process.arch,
      memory: process.memoryUsage(),
      uptime: process.uptime(),
      cwd: process.cwd(),
      env: {
        NODE_ENV: process.env.NODE_ENV,
        LOG_LEVEL: process.env.LOG_LEVEL
      }
    };

    await this.info('System Information', systemInfo);
  }

  /**
   * Flush all pending log writes
   */
  async flush() {
    // File writes are already awaited, but this method can be extended
    // for buffered logging implementations
    return Promise.resolve();
  }

  /**
   * Close logger and cleanup resources
   */
  async close() {
    await this.flush();
    // Additional cleanup if needed
  }
}

export default Logger;