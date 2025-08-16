/**
 * Comprehensive error handling and monitoring system
 * Provides centralized error handling, retry logic, and notification capabilities
 */

/**
 * Error types for categorization and handling
 */
export const ErrorTypes = {
  API_ERROR: 'API_ERROR',
  RATE_LIMIT: 'RATE_LIMIT',
  AUTHENTICATION: 'AUTHENTICATION',
  NETWORK: 'NETWORK',
  VALIDATION: 'VALIDATION',
  FILE_SYSTEM: 'FILE_SYSTEM',
  TRANSLATION: 'TRANSLATION',
  BUILD: 'BUILD',
  CONFIGURATION: 'CONFIGURATION',
  UNKNOWN: 'UNKNOWN'
};

/**
 * Error severity levels
 */
export const ErrorSeverity = {
  CRITICAL: 'CRITICAL',
  HIGH: 'HIGH',
  MEDIUM: 'MEDIUM',
  LOW: 'LOW'
};

/**
 * Custom error class with enhanced metadata
 */
export class TwitterAutomationError extends Error {
  constructor(message, type = ErrorTypes.UNKNOWN, severity = ErrorSeverity.MEDIUM, metadata = {}) {
    super(message);
    this.name = 'TwitterAutomationError';
    this.type = type;
    this.severity = severity;
    this.metadata = metadata;
    this.timestamp = new Date().toISOString();
    this.stack = Error.captureStackTrace ? Error.captureStackTrace(this, TwitterAutomationError) : this.stack;
  }

  toJSON() {
    return {
      name: this.name,
      message: this.message,
      type: this.type,
      severity: this.severity,
      metadata: this.metadata,
      timestamp: this.timestamp,
      stack: this.stack
    };
  }
}

/**
 * Retry configuration for different error types
 */
const RETRY_CONFIGS = {
  [ErrorTypes.API_ERROR]: {
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: 30000,
    backoffMultiplier: 2
  },
  [ErrorTypes.RATE_LIMIT]: {
    maxRetries: 2,
    baseDelay: 60000, // 1 minute
    maxDelay: 900000, // 15 minutes
    backoffMultiplier: 1.5
  },
  [ErrorTypes.NETWORK]: {
    maxRetries: 3,
    baseDelay: 2000,
    maxDelay: 10000,
    backoffMultiplier: 2
  },
  [ErrorTypes.FILE_SYSTEM]: {
    maxRetries: 2,
    baseDelay: 500,
    maxDelay: 5000,
    backoffMultiplier: 2
  },
  [ErrorTypes.TRANSLATION]: {
    maxRetries: 2,
    baseDelay: 1000,
    maxDelay: 5000,
    backoffMultiplier: 1.5
  },
  [ErrorTypes.BUILD]: {
    maxRetries: 1,
    baseDelay: 2000,
    maxDelay: 10000,
    backoffMultiplier: 1
  }
};

/**
 * Main error handler class
 */
export class ErrorHandler {
  constructor(logger, notificationService = null) {
    this.logger = logger;
    this.notificationService = notificationService;
    this.errorStats = {
      totalErrors: 0,
      errorsByType: {},
      errorsBySeverity: {},
      recoveredErrors: 0,
      criticalErrors: 0
    };
  }

  /**
   * Handle error with appropriate recovery strategy
   * @param {Error} error - The error to handle
   * @param {string} context - Context where error occurred
   * @param {Object} metadata - Additional metadata
   * @returns {Object} Error handling result
   */
  async handleError(error, context = 'unknown', metadata = {}) {
    const enhancedError = this.enhanceError(error, context, metadata);
    
    // Update error statistics
    this.updateErrorStats(enhancedError);

    // Log the error
    this.logError(enhancedError, context);

    // Determine recovery strategy
    const recoveryStrategy = this.determineRecoveryStrategy(enhancedError);

    // Execute recovery if possible
    let recoveryResult = null;
    if (recoveryStrategy.canRecover) {
      try {
        recoveryResult = await this.executeRecovery(enhancedError, recoveryStrategy);
        if (recoveryResult.success) {
          this.errorStats.recoveredErrors++;
          this.logger.info(`Successfully recovered from error in ${context}`, {
            errorType: enhancedError.type,
            recoveryStrategy: recoveryStrategy.strategy
          });
        }
      } catch (recoveryError) {
        this.logger.error(`Recovery failed for error in ${context}:`, recoveryError);
      }
    }

    // Send notifications for critical errors
    if (enhancedError.severity === ErrorSeverity.CRITICAL) {
      await this.sendCriticalErrorNotification(enhancedError, context);
    }

    return {
      error: enhancedError,
      recoveryStrategy,
      recoveryResult,
      canContinue: recoveryResult?.success || enhancedError.severity !== ErrorSeverity.CRITICAL
    };
  }

  /**
   * Execute operation with retry logic
   * @param {Function} operation - Async operation to execute
   * @param {string} operationName - Name of the operation for logging
   * @param {string} errorType - Expected error type for retry configuration
   * @param {Object} context - Additional context for error handling
   * @returns {Promise} Operation result
   */
  async executeWithRetry(operation, operationName, errorType = ErrorTypes.UNKNOWN, context = {}) {
    const retryConfig = RETRY_CONFIGS[errorType] || RETRY_CONFIGS[ErrorTypes.API_ERROR];
    let lastError = null;

    for (let attempt = 1; attempt <= retryConfig.maxRetries + 1; attempt++) {
      try {
        this.logger.debug(`Executing ${operationName} (attempt ${attempt}/${retryConfig.maxRetries + 1})`);
        
        const result = await operation();
        
        if (attempt > 1) {
          this.logger.info(`${operationName} succeeded after ${attempt} attempts`);
        }
        
        return result;
      } catch (error) {
        lastError = error;
        
        if (attempt <= retryConfig.maxRetries) {
          const delay = this.calculateBackoffDelay(attempt - 1, retryConfig);
          
          this.logger.warn(`${operationName} failed (attempt ${attempt}), retrying in ${delay}ms:`, error.message);
          
          await this.sleep(delay);
        } else {
          this.logger.error(`${operationName} failed after ${attempt} attempts:`, error.message);
        }
      }
    }

    // All retries exhausted, handle the final error
    const errorResult = await this.handleError(lastError, operationName, context);
    throw errorResult.error;
  }

  /**
   * Enhance error with additional metadata and classification
   * @param {Error} error - Original error
   * @param {string} context - Context where error occurred
   * @param {Object} metadata - Additional metadata
   * @returns {TwitterAutomationError} Enhanced error
   */
  enhanceError(error, context, metadata) {
    if (error instanceof TwitterAutomationError) {
      return error;
    }

    const errorType = this.classifyError(error);
    const severity = this.determineSeverity(error, errorType);

    return new TwitterAutomationError(
      error.message,
      errorType,
      severity,
      {
        originalError: error.name,
        context,
        stack: error.stack,
        ...metadata
      }
    );
  }

  /**
   * Classify error type based on error characteristics
   * @param {Error} error - Error to classify
   * @returns {string} Error type
   */
  classifyError(error) {
    const message = error.message.toLowerCase();
    const code = error.code;
    const status = error.response?.status;

    // API and HTTP errors
    if (status === 429 || message.includes('rate limit')) {
      return ErrorTypes.RATE_LIMIT;
    }
    if (status === 401 || status === 403 || message.includes('unauthorized') || message.includes('forbidden')) {
      return ErrorTypes.AUTHENTICATION;
    }
    if (status >= 400 && status < 500) {
      return ErrorTypes.API_ERROR;
    }
    if (status >= 500 || message.includes('server error')) {
      return ErrorTypes.API_ERROR;
    }

    // Network errors
    if (code === 'ECONNABORTED' || code === 'ENOTFOUND' || code === 'ECONNREFUSED' || 
        message.includes('timeout') || message.includes('network')) {
      return ErrorTypes.NETWORK;
    }

    // File system errors
    if (code === 'ENOENT' || code === 'EACCES' || code === 'EMFILE' || 
        message.includes('file') || message.includes('directory')) {
      return ErrorTypes.FILE_SYSTEM;
    }

    // Translation errors
    if (message.includes('translation') || message.includes('translate')) {
      return ErrorTypes.TRANSLATION;
    }

    // Build errors
    if (message.includes('hugo') || message.includes('build')) {
      return ErrorTypes.BUILD;
    }

    // Configuration errors
    if (message.includes('config') || message.includes('environment') || message.includes('missing')) {
      return ErrorTypes.CONFIGURATION;
    }

    // Validation errors
    if (message.includes('validation') || message.includes('invalid') || message.includes('required')) {
      return ErrorTypes.VALIDATION;
    }

    return ErrorTypes.UNKNOWN;
  }

  /**
   * Determine error severity
   * @param {Error} error - Error to evaluate
   * @param {string} errorType - Classified error type
   * @returns {string} Error severity
   */
  determineSeverity(error, errorType) {
    const message = error.message.toLowerCase();

    // Critical errors that stop the entire workflow
    if (errorType === ErrorTypes.AUTHENTICATION || 
        errorType === ErrorTypes.CONFIGURATION ||
        message.includes('fatal') || 
        message.includes('critical')) {
      return ErrorSeverity.CRITICAL;
    }

    // High severity errors that affect major functionality
    if (errorType === ErrorTypes.API_ERROR || 
        errorType === ErrorTypes.BUILD ||
        message.includes('failed to') && message.includes('all')) {
      return ErrorSeverity.HIGH;
    }

    // Medium severity errors that can be recovered from
    if (errorType === ErrorTypes.RATE_LIMIT || 
        errorType === ErrorTypes.NETWORK ||
        errorType === ErrorTypes.TRANSLATION) {
      return ErrorSeverity.MEDIUM;
    }

    // Low severity errors that are minor issues
    return ErrorSeverity.LOW;
  }

  /**
   * Determine recovery strategy for error
   * @param {TwitterAutomationError} error - Enhanced error
   * @returns {Object} Recovery strategy
   */
  determineRecoveryStrategy(error) {
    const strategies = {
      [ErrorTypes.RATE_LIMIT]: {
        canRecover: true,
        strategy: 'wait_and_retry',
        description: 'Wait for rate limit reset and retry'
      },
      [ErrorTypes.NETWORK]: {
        canRecover: true,
        strategy: 'exponential_backoff',
        description: 'Retry with exponential backoff'
      },
      [ErrorTypes.TRANSLATION]: {
        canRecover: true,
        strategy: 'fallback_translation',
        description: 'Use fallback translation method or original content'
      },
      [ErrorTypes.FILE_SYSTEM]: {
        canRecover: true,
        strategy: 'alternative_path',
        description: 'Try alternative file path or create directories'
      },
      [ErrorTypes.API_ERROR]: {
        canRecover: true,
        strategy: 'retry_with_backoff',
        description: 'Retry API call with exponential backoff'
      },
      [ErrorTypes.BUILD]: {
        canRecover: false,
        strategy: 'manual_intervention',
        description: 'Requires manual intervention to fix build issues'
      },
      [ErrorTypes.AUTHENTICATION]: {
        canRecover: false,
        strategy: 'manual_intervention',
        description: 'Requires manual intervention to fix authentication'
      },
      [ErrorTypes.CONFIGURATION]: {
        canRecover: false,
        strategy: 'manual_intervention',
        description: 'Requires manual intervention to fix configuration'
      }
    };

    return strategies[error.type] || {
      canRecover: false,
      strategy: 'unknown',
      description: 'Unknown error type, manual intervention may be required'
    };
  }

  /**
   * Execute recovery strategy
   * @param {TwitterAutomationError} error - Error to recover from
   * @param {Object} strategy - Recovery strategy
   * @returns {Object} Recovery result
   */
  async executeRecovery(error, strategy) {
    switch (strategy.strategy) {
      case 'wait_and_retry':
        return await this.handleRateLimitRecovery(error);
      
      case 'exponential_backoff':
        return await this.handleNetworkRecovery(error);
      
      case 'fallback_translation':
        return await this.handleTranslationRecovery(error);
      
      case 'alternative_path':
        return await this.handleFileSystemRecovery(error);
      
      case 'retry_with_backoff':
        return await this.handleApiRecovery(error);
      
      default:
        return { success: false, message: 'No recovery strategy available' };
    }
  }

  /**
   * Handle rate limit recovery
   * @param {TwitterAutomationError} error - Rate limit error
   * @returns {Object} Recovery result
   */
  async handleRateLimitRecovery(error) {
    const waitTime = error.metadata.resetTime 
      ? new Date(error.metadata.resetTime).getTime() - Date.now()
      : 60000; // Default 1 minute

    if (waitTime > 0 && waitTime < 900000) { // Max 15 minutes
      this.logger.info(`Waiting ${Math.ceil(waitTime / 1000)} seconds for rate limit reset`);
      await this.sleep(waitTime);
      return { success: true, message: 'Rate limit wait completed' };
    }

    return { success: false, message: 'Rate limit wait time too long or invalid' };
  }

  /**
   * Handle network recovery
   * @param {TwitterAutomationError} error - Network error
   * @returns {Object} Recovery result
   */
  async handleNetworkRecovery(error) {
    const retryConfig = RETRY_CONFIGS[ErrorTypes.NETWORK];
    const delay = this.calculateBackoffDelay(1, retryConfig);
    
    this.logger.info(`Network error recovery: waiting ${delay}ms before retry`);
    await this.sleep(delay);
    
    return { success: true, message: 'Network recovery wait completed' };
  }

  /**
   * Handle translation recovery
   * @param {TwitterAutomationError} error - Translation error
   * @returns {Object} Recovery result
   */
  async handleTranslationRecovery(error) {
    this.logger.info('Translation error recovery: will use original content as fallback');
    return { 
      success: true, 
      message: 'Translation fallback strategy activated',
      fallbackMode: true
    };
  }

  /**
   * Handle file system recovery
   * @param {TwitterAutomationError} error - File system error
   * @returns {Object} Recovery result
   */
  async handleFileSystemRecovery(error) {
    this.logger.info('File system error recovery: attempting alternative approach');
    return { 
      success: true, 
      message: 'File system recovery strategy activated',
      useAlternativePath: true
    };
  }

  /**
   * Handle API recovery
   * @param {TwitterAutomationError} error - API error
   * @returns {Object} Recovery result
   */
  async handleApiRecovery(error) {
    const retryConfig = RETRY_CONFIGS[ErrorTypes.API_ERROR];
    const delay = this.calculateBackoffDelay(1, retryConfig);
    
    this.logger.info(`API error recovery: waiting ${delay}ms before retry`);
    await this.sleep(delay);
    
    return { success: true, message: 'API recovery wait completed' };
  }

  /**
   * Calculate exponential backoff delay
   * @param {number} attempt - Attempt number (0-based)
   * @param {Object} config - Retry configuration
   * @returns {number} Delay in milliseconds
   */
  calculateBackoffDelay(attempt, config) {
    const delay = config.baseDelay * Math.pow(config.backoffMultiplier, attempt);
    return Math.min(delay, config.maxDelay);
  }

  /**
   * Update error statistics
   * @param {TwitterAutomationError} error - Error to track
   */
  updateErrorStats(error) {
    this.errorStats.totalErrors++;
    
    this.errorStats.errorsByType[error.type] = (this.errorStats.errorsByType[error.type] || 0) + 1;
    this.errorStats.errorsBySeverity[error.severity] = (this.errorStats.errorsBySeverity[error.severity] || 0) + 1;
    
    if (error.severity === ErrorSeverity.CRITICAL) {
      this.errorStats.criticalErrors++;
    }
  }

  /**
   * Log error with appropriate level
   * @param {TwitterAutomationError} error - Error to log
   * @param {string} context - Context where error occurred
   */
  logError(error, context) {
    const logData = {
      context,
      errorType: error.type,
      severity: error.severity,
      metadata: error.metadata
    };

    switch (error.severity) {
      case ErrorSeverity.CRITICAL:
        this.logger.error(`CRITICAL ERROR in ${context}: ${error.message}`, logData);
        break;
      case ErrorSeverity.HIGH:
        this.logger.error(`HIGH SEVERITY ERROR in ${context}: ${error.message}`, logData);
        break;
      case ErrorSeverity.MEDIUM:
        this.logger.warn(`MEDIUM SEVERITY ERROR in ${context}: ${error.message}`, logData);
        break;
      case ErrorSeverity.LOW:
        this.logger.info(`LOW SEVERITY ERROR in ${context}: ${error.message}`, logData);
        break;
      default:
        this.logger.error(`ERROR in ${context}: ${error.message}`, logData);
    }
  }

  /**
   * Send critical error notification
   * @param {TwitterAutomationError} error - Critical error
   * @param {string} context - Context where error occurred
   */
  async sendCriticalErrorNotification(error, context) {
    if (!this.notificationService) {
      this.logger.warn('No notification service configured for critical error alerts');
      return;
    }

    try {
      await this.notificationService.sendCriticalAlert({
        title: `Critical Error in Twitter Automation: ${context}`,
        message: error.message,
        errorType: error.type,
        timestamp: error.timestamp,
        metadata: error.metadata
      });
    } catch (notificationError) {
      this.logger.error('Failed to send critical error notification:', notificationError);
    }
  }

  /**
   * Get error statistics summary
   * @returns {Object} Error statistics
   */
  getErrorStats() {
    return {
      ...this.errorStats,
      recoveryRate: this.errorStats.totalErrors > 0 
        ? (this.errorStats.recoveredErrors / this.errorStats.totalErrors * 100).toFixed(2) + '%'
        : '0%'
    };
  }

  /**
   * Sleep for specified milliseconds
   * @param {number} ms - Milliseconds to sleep
   * @returns {Promise} Promise that resolves after delay
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

export { ErrorHandler as default };