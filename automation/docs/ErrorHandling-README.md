# Error Handling and Monitoring System

This document describes the comprehensive error handling and monitoring system implemented for the Twitter Crypto Content Automation project.

## Overview

The error handling system provides:
- **Centralized error management** with classification and severity levels
- **Automatic retry logic** with exponential backoff
- **Error recovery mechanisms** for common failure scenarios
- **Comprehensive logging** with structured output and file rotation
- **Critical error notifications** via multiple channels (Slack, email, webhooks, GitHub issues)
- **Error statistics and reporting** for monitoring system health

## Components

### 1. ErrorHandler (`src/utils/ErrorHandler.js`)

The main error handling orchestrator that provides:

#### Error Classification
Automatically classifies errors into types:
- `API_ERROR` - HTTP API failures
- `RATE_LIMIT` - API rate limiting
- `AUTHENTICATION` - Auth failures (401, 403)
- `NETWORK` - Network connectivity issues
- `VALIDATION` - Data validation errors
- `FILE_SYSTEM` - File I/O operations
- `TRANSLATION` - Translation service failures
- `BUILD` - Hugo build failures
- `CONFIGURATION` - Config loading issues
- `UNKNOWN` - Unclassified errors

#### Severity Levels
- `CRITICAL` - System-stopping errors (auth, config)
- `HIGH` - Major functionality impact (API, build)
- `MEDIUM` - Recoverable issues (rate limits, network)
- `LOW` - Minor issues (validation, unknown)

#### Recovery Strategies
- **Rate Limit Recovery**: Wait for reset window
- **Network Recovery**: Exponential backoff retry
- **Translation Recovery**: Fallback to original content
- **File System Recovery**: Alternative paths/retry
- **API Recovery**: Retry with backoff

#### Usage Example
```javascript
import ErrorHandler, { ErrorTypes } from './src/utils/ErrorHandler.js';

const errorHandler = new ErrorHandler(logger, notificationService);

// Handle individual errors
const result = await errorHandler.handleError(error, 'context');

// Execute with retry
const data = await errorHandler.executeWithRetry(
  () => apiCall(),
  'api_operation',
  ErrorTypes.API_ERROR
);
```

### 2. Logger (`src/utils/Logger.js`)

Advanced logging system with:

#### Features
- **Multiple log levels**: ERROR, WARN, INFO, DEBUG, TRACE
- **Structured logging**: JSON or text format
- **File output**: Automatic rotation and cleanup
- **Console output**: Colored and formatted
- **Performance timing**: Built-in timer functionality
- **Child loggers**: Contextual logging with inheritance

#### Configuration
```javascript
const logger = new Logger({
  level: 'INFO',
  enableFile: true,
  enableConsole: true,
  logDir: 'logs',
  maxFileSize: 10485760, // 10MB
  maxFiles: 5,
  format: 'json',
  includeStackTrace: true
});
```

#### Usage Example
```javascript
// Basic logging
await logger.info('Operation completed', { duration: 1500 });
await logger.error('Operation failed', error);

// Performance timing
const timer = logger.timer('database_query');
// ... perform operation
await timer.end({ recordsProcessed: 100 });

// Child logger with context
const childLogger = logger.child({ component: 'twitter-client' });
await childLogger.debug('Searching tweets', { keywords: ['crypto'] });
```

### 3. NotificationService (`src/services/NotificationService.js`)

Multi-channel notification system for critical alerts:

#### Supported Channels
- **Slack**: Webhook integration with rich formatting
- **Email**: HTML and text notifications via API
- **Webhook**: Generic HTTP POST notifications
- **GitHub Issues**: Automatic issue creation

#### Configuration Example
```javascript
const notificationService = new NotificationService({
  enabled: true,
  channels: [
    {
      type: 'slack',
      webhookUrl: 'https://hooks.slack.com/services/...'
    },
    {
      type: 'email',
      recipients: ['admin@example.com'],
      apiUrl: 'https://api.sendgrid.com/v3/mail/send',
      apiKey: 'SG.xxx'
    },
    {
      type: 'github',
      owner: 'username',
      repo: 'repository',
      token: 'ghp_xxx'
    }
  ],
  retryAttempts: 3,
  retryDelay: 5000
});
```

#### Usage Example
```javascript
await notificationService.sendCriticalAlert({
  title: 'Twitter API Authentication Failed',
  message: 'Unable to authenticate with Twitter API',
  errorType: 'AUTHENTICATION',
  metadata: { endpoint: '/tweets/search/recent' }
});
```

## Integration with Main System

The error handling system is fully integrated into the `TwitterCryptoAutomation` class:

### Initialization
```javascript
class TwitterCryptoAutomation {
  constructor() {
    this.logger = new Logger(config.logging);
    this.errorHandler = new ErrorHandler(this.logger, this.notificationService);
  }
}
```

### Workflow Integration
All major operations use error handling:

```javascript
// Search tweets with error handling
const tweets = await this.executeWorkflowStep(
  () => this.searchCryptoTweets(),
  'search_crypto_tweets',
  ErrorTypes.API_ERROR
);

// Generate articles with individual error handling
for (const tweet of tweets) {
  try {
    const article = await this.executeWithErrorHandling(
      () => this.generateArticleFromTweet(tweet),
      `article_generation_${tweet.id}`,
      ErrorTypes.TRANSLATION
    );
  } catch (error) {
    // Error is logged and handled, workflow continues
  }
}
```

## Configuration

### Default Configuration (`config/default.json`)
```json
{
  "logging": {
    "level": "INFO",
    "enableFile": true,
    "enableConsole": true,
    "logDir": "logs",
    "maxFileSize": 10485760,
    "maxFiles": 5,
    "format": "json",
    "includeStackTrace": true
  },
  "notifications": {
    "enabled": false,
    "channels": [],
    "retryAttempts": 3,
    "retryDelay": 5000
  },
  "errorHandling": {
    "maxRetries": 3,
    "baseDelay": 1000,
    "maxDelay": 30000,
    "enableRecovery": true,
    "criticalErrorThreshold": 5
  }
}
```

### Environment Variables
- `LOG_LEVEL`: Override default log level (ERROR, WARN, INFO, DEBUG, TRACE)
- `TWITTER_BEARER_TOKEN`: Required for Twitter API access

## Error Recovery Scenarios

### 1. Twitter API Rate Limiting
```javascript
// Automatic handling in TwitterClient
if (error.response?.status === 429) {
  const resetTime = error.response.headers['x-rate-limit-reset'];
  await this.sleep(waitTime);
  return this.client.request(error.config); // Retry
}
```

### 2. Translation Service Failures
```javascript
// Fallback to original content
try {
  const translated = await translationService.translateText(text);
} catch (error) {
  const fallback = await this.generateFallbackContent(tweet);
  // Continue with original English content
}
```

### 3. File System Errors
```javascript
// Alternative file paths and retry logic
try {
  await fileWriter.writeArticleFile(content, filename);
} catch (error) {
  const alternativeFilename = await generateAlternativeFilename();
  await fileWriter.writeArticleFile(content, alternativeFilename);
}
```

### 4. Hugo Build Failures
```javascript
// Detailed error reporting and guidance
try {
  await hugoBuilder.buildSite();
} catch (error) {
  if (error.message.includes('Hugo not found')) {
    logger.error('Hugo is not installed. Please install Hugo to continue.');
  } else if (error.message.includes('config')) {
    logger.error('Hugo configuration error. Please check hugo.toml file.');
  }
  throw error; // Critical error, stop workflow
}
```

## Monitoring and Reporting

### Error Statistics
The system tracks comprehensive error statistics:

```javascript
const stats = errorHandler.getErrorStats();
// Returns:
{
  totalErrors: 15,
  errorsByType: { 'API_ERROR': 8, 'RATE_LIMIT': 4, 'NETWORK': 3 },
  errorsBySeverity: { 'HIGH': 8, 'MEDIUM': 4, 'LOW': 3 },
  recoveredErrors: 12,
  criticalErrors: 0,
  recoveryRate: '80.00%'
}
```

### Execution Reports
Each workflow execution generates a detailed report:

```javascript
{
  executionTime: 125000,
  executionTimeFormatted: "2m 5s",
  statistics: {
    tweetsFound: 50,
    tweetsProcessed: 45,
    articlesGenerated: 3,
    duplicatesSkipped: 2,
    errorsEncountered: 5,
    recoveredErrors: 4
  },
  errorStatistics: { /* detailed error stats */ },
  success: true,
  hasErrors: true,
  criticalErrors: 0
}
```

## Testing

### Unit Tests
Comprehensive test suites cover:
- Error classification accuracy
- Severity determination logic
- Recovery strategy selection
- Retry mechanisms with backoff
- Notification delivery
- Log formatting and rotation

### Integration Tests
End-to-end tests verify:
- Workflow error handling
- Component integration
- Recovery scenarios
- Statistics tracking
- Report generation

### Manual Testing
Run the test script to verify functionality:
```bash
node test-error-handling.js
```

## Best Practices

### 1. Error Context
Always provide meaningful context when handling errors:
```javascript
await errorHandler.handleError(error, 'twitter_search', {
  keywords: searchKeywords,
  maxResults: 50,
  attempt: 2
});
```

### 2. Graceful Degradation
Design workflows to continue with partial failures:
```javascript
// Process articles individually, don't fail entire batch
for (const tweet of tweets) {
  try {
    await processArticle(tweet);
  } catch (error) {
    logger.warn(`Failed to process tweet ${tweet.id}, continuing...`);
  }
}
```

### 3. Resource Cleanup
Always perform cleanup even when errors occur:
```javascript
try {
  await executeWorkflow();
} finally {
  await cleanup(); // Always runs
}
```

### 4. Monitoring Alerts
Configure notifications for critical errors only:
```javascript
if (error.severity === ErrorSeverity.CRITICAL) {
  await notificationService.sendCriticalAlert(alert);
}
```

## Troubleshooting

### Common Issues

1. **High Error Rates**
   - Check API quotas and rate limits
   - Verify network connectivity
   - Review configuration settings

2. **Failed Notifications**
   - Verify webhook URLs and API keys
   - Check notification service logs
   - Test configuration with `testConfiguration()`

3. **Log File Issues**
   - Ensure write permissions to log directory
   - Check disk space availability
   - Verify log rotation settings

4. **Recovery Failures**
   - Review retry configuration
   - Check error classification accuracy
   - Verify recovery strategy implementation

### Debug Mode
Enable debug logging for detailed troubleshooting:
```bash
LOG_LEVEL=DEBUG node src/index.js
```

This will output detailed information about:
- Error classification decisions
- Recovery strategy selection
- Retry attempts and backoff calculations
- Notification delivery attempts
- Performance timing data

## Future Enhancements

Potential improvements to consider:
- **Metrics Integration**: Export metrics to Prometheus/Grafana
- **Circuit Breaker**: Prevent cascading failures
- **Distributed Tracing**: Track errors across service boundaries
- **Machine Learning**: Predictive error detection
- **Dashboard**: Real-time error monitoring UI