import { TwitterClient } from './clients/TwitterClient.js';
import ContentProcessor from './processors/ContentProcessor.js';
import TranslationService from './services/TranslationService.js';
import ArticleGenerator from './generators/ArticleGenerator.js';
import DuplicateChecker from './utils/DuplicateChecker.js';
import FileWriter from './utils/FileWriter.js';
import HugoBuilder from './builders/HugoBuilder.js';
import ConfigLoader from './config/ConfigLoader.js';
import Logger from './utils/Logger.js';
import ErrorHandler, { ErrorTypes, ErrorSeverity } from './utils/ErrorHandler.js';
import NotificationService from './services/NotificationService.js';
import fs from 'fs-extra';
import path from 'path';

/**
 * Main orchestration workflow for Twitter crypto content automation
 * Coordinates all components from Twitter search to site deployment
 */
class TwitterCryptoAutomation {
  constructor() {
    this.config = null;
    this.logger = new Logger({
      level: process.env.LOG_LEVEL || 'INFO',
      enableFile: true,
      logDir: 'logs'
    });
    this.errorHandler = null;
    this.notificationService = null;
    this.components = {};
    this.stats = {
      startTime: null,
      endTime: null,
      tweetsFound: 0,
      tweetsProcessed: 0,
      articlesGenerated: 0,
      duplicatesSkipped: 0,
      errors: [],
      recoveredErrors: 0
    };
  }

  /**
   * Initialize all components with configuration
   */
  async initialize() {
    const timer = this.logger.timer('initialization');
    
    try {
      await this.logger.info('Initializing Twitter Crypto Content Automation...');
      await this.logger.logSystemInfo();
      this.stats.startTime = new Date();

      // Load configuration
      this.config = await this.executeWithErrorHandling(
        () => ConfigLoader.load(),
        'configuration_loading',
        ErrorTypes.CONFIGURATION
      );
      await this.logger.info('Configuration loaded successfully');

      // Initialize notification service
      if (this.config.notifications) {
        this.notificationService = new NotificationService(this.config.notifications, this.logger);
        await this.logger.info('Notification service initialized');
      }

      // Initialize error handler
      this.errorHandler = new ErrorHandler(this.logger, this.notificationService);
      await this.logger.info('Error handler initialized');

      // Initialize components with error handling
      await this.initializeComponents();

      await this.logger.info('All components initialized successfully');
      await timer.end();
    } catch (error) {
      await timer.end({ success: false });
      await this.logger.error('Failed to initialize components:', error);
      
      if (this.errorHandler) {
        const errorResult = await this.errorHandler.handleError(error, 'initialization');
        if (!errorResult.canContinue) {
          throw errorResult.error;
        }
      }
      throw error;
    }
  }

  /**
   * Initialize all components with individual error handling
   */
  async initializeComponents() {
    const componentInitializers = [
      {
        name: 'twitterClient',
        factory: () => new TwitterClient(),
        errorType: ErrorTypes.API_ERROR
      },
      {
        name: 'contentProcessor',
        factory: () => new ContentProcessor(this.config.content),
        errorType: ErrorTypes.CONFIGURATION
      },
      {
        name: 'translationService',
        factory: () => new TranslationService(this.config.translation),
        errorType: ErrorTypes.TRANSLATION
      },
      {
        name: 'articleGenerator',
        factory: () => new ArticleGenerator(this.config.template?.path),
        errorType: ErrorTypes.FILE_SYSTEM
      },
      {
        name: 'duplicateChecker',
        factory: () => new DuplicateChecker(this.config.storage?.processedTweetsPath),
        errorType: ErrorTypes.FILE_SYSTEM
      },
      {
        name: 'fileWriter',
        factory: () => new FileWriter(this.config.hugo?.contentDir),
        errorType: ErrorTypes.FILE_SYSTEM
      },
      {
        name: 'hugoBuilder',
        factory: () => new HugoBuilder(this.config.hugo?.siteRoot, this.config.hugo?.outputDir),
        errorType: ErrorTypes.BUILD
      }
    ];

    for (const { name, factory, errorType } of componentInitializers) {
      try {
        this.components[name] = await this.executeWithErrorHandling(
          factory,
          `${name}_initialization`,
          errorType
        );
        await this.logger.debug(`${name} initialized successfully`);
      } catch (error) {
        await this.logger.error(`Failed to initialize ${name}:`, error);
        throw error;
      }
    }
  }

  /**
   * Execute the complete workflow from Twitter search to site deployment
   */
  async executeWorkflow() {
    const workflowTimer = this.logger.timer('complete_workflow');
    
    try {
      await this.logger.info('Starting complete automation workflow...');

      // Step 1: Search for trending crypto tweets
      const tweets = await this.executeWorkflowStep(
        () => this.searchCryptoTweets(),
        'search_crypto_tweets',
        ErrorTypes.API_ERROR
      );
      this.stats.tweetsFound = tweets.length;

      if (tweets.length === 0) {
        await this.logger.warn('No tweets found matching criteria');
        return this.generateReport();
      }

      // Step 2: Process and rank tweets
      const processedTweets = await this.executeWorkflowStep(
        () => this.processAndRankTweets(tweets),
        'process_and_rank_tweets',
        ErrorTypes.VALIDATION
      );
      this.stats.tweetsProcessed = processedTweets.length;

      // Step 3: Select top 3 tweets
      const topTweets = processedTweets.slice(0, 3);
      await this.logger.info(`Selected top ${topTweets.length} tweets for article generation`);

      // Step 4: Generate articles for each tweet
      const articles = await this.generateArticlesFromTweets(topTweets);

      if (articles.length === 0) {
        await this.logger.warn('No articles were generated successfully');
        return this.generateReport();
      }

      // Step 5: Write articles to files
      const writtenFiles = await this.executeWorkflowStep(
        () => this.writeArticlesToFiles(articles),
        'write_articles_to_files',
        ErrorTypes.FILE_SYSTEM
      );

      // Step 6: Build Hugo site
      await this.executeWorkflowStep(
        () => this.buildHugoSite(),
        'build_hugo_site',
        ErrorTypes.BUILD
      );

      // Step 7: Cleanup and finalize
      await this.executeWorkflowStep(
        () => this.cleanup(),
        'cleanup',
        ErrorTypes.FILE_SYSTEM
      );

      this.stats.endTime = new Date();
      await this.logger.info(`Workflow completed successfully. Generated ${articles.length} articles.`);

      const report = this.generateReport();
      await workflowTimer.end({ success: true, articlesGenerated: articles.length });
      return report;

    } catch (error) {
      this.stats.endTime = new Date();
      await workflowTimer.end({ success: false });
      
      const errorResult = await this.errorHandler.handleError(error, 'workflow_execution');
      this.stats.errors.push({
        step: 'workflow_execution',
        error: error.message,
        type: errorResult.error.type,
        severity: errorResult.error.severity
      });
      
      throw errorResult.error;
    }
  }

  /**
   * Execute a workflow step with error handling
   * @param {Function} stepFunction - The step function to execute
   * @param {string} stepName - Name of the step for logging
   * @param {string} errorType - Expected error type
   * @returns {Promise} Step result
   */
  async executeWorkflowStep(stepFunction, stepName, errorType) {
    return await this.errorHandler.executeWithRetry(
      stepFunction,
      stepName,
      errorType,
      { workflowStep: stepName }
    );
  }

  /**
   * Execute operation with error handling
   * @param {Function} operation - Operation to execute
   * @param {string} context - Context for error handling
   * @param {string} errorType - Expected error type
   * @returns {Promise} Operation result
   */
  async executeWithErrorHandling(operation, context, errorType) {
    try {
      return await operation();
    } catch (error) {
      const errorResult = await this.errorHandler.handleError(error, context);
      if (errorResult.canContinue && errorResult.recoveryResult?.success) {
        this.stats.recoveredErrors++;
        // Retry the operation after recovery
        return await operation();
      }
      throw errorResult.error;
    }
  }

  /**
   * Search for trending cryptocurrency tweets
   */
  async searchCryptoTweets() {
    const searchTimer = this.logger.timer('crypto_tweet_search');
    
    try {
      await this.logger.info('Searching for crypto tweets...');
      
      const keywords = this.config.twitter?.searchKeywords || [
        'cryptocurrency OR crypto',
        'blockchain OR bitcoin OR BTC',
        'ethereum OR ETH OR DeFi',
        'NFT OR Web3 OR altcoin'
      ];

      const maxResults = this.config.twitter?.maxResults || 50;
      
      const tweets = await this.components.twitterClient.searchTweets(keywords, maxResults);
      
      await this.logger.info(`Found ${tweets.length} tweets matching crypto keywords`);
      await searchTimer.end({ tweetsFound: tweets.length });
      return tweets;

    } catch (error) {
      await searchTimer.end({ success: false });
      await this.logger.error('Failed to search crypto tweets:', error);
      throw error;
    }
  }

  /**
   * Process and rank tweets by engagement
   */
  async processAndRankTweets(tweets) {
    const processingTimer = this.logger.timer('tweet_processing');
    
    try {
      await this.logger.info('Processing and ranking tweets...');
      
      const processedTweets = this.components.contentProcessor.processAndFilterTweets(tweets);
      
      await this.logger.info(`Processed ${processedTweets.length} valid tweets`);
      await processingTimer.end({ 
        inputTweets: tweets.length, 
        validTweets: processedTweets.length,
        filteredOut: tweets.length - processedTweets.length
      });
      return processedTweets;

    } catch (error) {
      await processingTimer.end({ success: false });
      await this.logger.error('Failed to process tweets:', error);
      throw error;
    }
  }

  /**
   * Generate articles from multiple tweets with individual error handling
   * @param {Array} tweets - Array of tweets to process
   * @returns {Array} Array of generated articles
   */
  async generateArticlesFromTweets(tweets) {
    const articles = [];
    const errors = [];

    for (const tweet of tweets) {
      try {
        const article = await this.executeWithErrorHandling(
          () => this.generateArticleFromTweet(tweet),
          `article_generation_${tweet.id}`,
          ErrorTypes.TRANSLATION
        );
        
        if (article) {
          articles.push(article);
          this.stats.articlesGenerated++;
        }
      } catch (error) {
        await this.logger.error(`Failed to generate article for tweet ${tweet.id}:`, error);
        errors.push({
          step: 'article_generation',
          tweetId: tweet.id,
          error: error.message,
          type: error.type || ErrorTypes.UNKNOWN
        });
        this.stats.errors.push(errors[errors.length - 1]);
      }
    }

    await this.logger.info(`Generated ${articles.length} articles from ${tweets.length} tweets`);
    
    if (errors.length > 0) {
      await this.logger.warn(`Encountered ${errors.length} errors during article generation`);
    }

    return articles;
  }

  /**
   * Generate article from a single tweet
   */
  async generateArticleFromTweet(tweet) {
    const articleTimer = this.logger.timer(`article_generation_${tweet.id}`);
    
    try {
      await this.logger.info(`Generating article for tweet ${tweet.id} by @${tweet.author.username}`);

      // Check for duplicates
      const duplicateCheck = await this.executeWithErrorHandling(
        () => this.components.duplicateChecker.checkDuplicate(tweet.id, tweet.text, tweet.url),
        `duplicate_check_${tweet.id}`,
        ErrorTypes.FILE_SYSTEM
      );

      if (duplicateCheck.isDuplicate) {
        await this.logger.info(`Skipping duplicate tweet ${tweet.id}: ${duplicateCheck.reason}`);
        this.stats.duplicatesSkipped++;
        await articleTimer.end({ skipped: true, reason: 'duplicate' });
        return null;
      }

      // Translate tweet content with fallback handling
      let translatedContent;
      let enhancedContent;
      
      try {
        translatedContent = await this.executeWithErrorHandling(
          () => this.components.translationService.translateText(tweet.text),
          `translation_${tweet.id}`,
          ErrorTypes.TRANSLATION
        );
        
        enhancedContent = await this.executeWithErrorHandling(
          () => this.components.translationService.enhanceContent(tweet, translatedContent),
          `content_enhancement_${tweet.id}`,
          ErrorTypes.TRANSLATION
        );
      } catch (translationError) {
        await this.logger.warn(`Translation failed for tweet ${tweet.id}, using fallback approach`);
        const fallbackResult = await this.generateFallbackContent(tweet);
        translatedContent = fallbackResult.translatedContent;
        enhancedContent = fallbackResult.enhancedContent;
      }

      // Generate article
      const article = await this.executeWithErrorHandling(
        () => this.components.articleGenerator.generateArticle(tweet, translatedContent, enhancedContent),
        `article_creation_${tweet.id}`,
        ErrorTypes.FILE_SYSTEM
      );

      // Update processed list
      await this.executeWithErrorHandling(
        () => this.components.duplicateChecker.updateProcessedList(
          tweet.id,
          duplicateCheck.contentHash,
          article.filename,
          {
            tweetUrl: tweet.url,
            author: tweet.author.username,
            content: tweet.text,
            processedAt: new Date().toISOString()
          }
        ),
        `update_processed_list_${tweet.id}`,
        ErrorTypes.FILE_SYSTEM
      );

      await this.logger.info(`Article generated successfully: ${article.filename}`);
      await articleTimer.end({ success: true, filename: article.filename });
      return article;

    } catch (error) {
      await articleTimer.end({ success: false });
      await this.logger.error(`Failed to generate article for tweet ${tweet.id}:`, error);
      throw error;
    }
  }

  /**
   * Generate fallback content when translation fails
   * @param {Object} tweet - Tweet object
   * @returns {Object} Fallback content
   */
  async generateFallbackContent(tweet) {
    try {
      await this.logger.info(`Generating fallback content for tweet ${tweet.id}`);
      
      // Use original English content with basic enhancement
      const basicEnhancement = `${tweet.text}

## Market Context

This tweet from @${tweet.author.username} has gained significant attention in the crypto community with ${tweet.metrics.retweetCount} retweets and ${tweet.metrics.likeCount} likes.

## Key Points

The content reflects current market sentiment and community discussions around cryptocurrency trends.

*Note: This content is presented in its original language due to translation service limitations.*`;

      return {
        translatedContent: tweet.text, // Use original text as "translation"
        enhancedContent: basicEnhancement
      };
    } catch (error) {
      await this.logger.error('Fallback content generation failed:', error);
      throw error;
    }
  }

  /**
   * Write generated articles to files
   */
  async writeArticlesToFiles(articles) {
    const writeTimer = this.logger.timer('file_writing');
    
    try {
      await this.logger.info(`Writing ${articles.length} articles to files...`);
      
      const writtenFiles = [];
      const errors = [];
      
      for (const article of articles) {
        try {
          // Validate content before writing
          const isValid = await this.executeWithErrorHandling(
            () => this.components.fileWriter.validateFileContent(article.fullContent),
            `content_validation_${article.filename}`,
            ErrorTypes.VALIDATION
          );

          if (!isValid) {
            await this.logger.warn(`Invalid content for article ${article.filename}, skipping...`);
            continue;
          }

          // Generate unique filename to avoid conflicts
          const uniqueFilename = await this.executeWithErrorHandling(
            () => this.components.fileWriter.generateUniqueFilename(article.frontMatter.title),
            `filename_generation_${article.filename}`,
            ErrorTypes.FILE_SYSTEM
          );

          // Write article to file
          const filePath = await this.executeWithErrorHandling(
            () => this.components.fileWriter.writeArticleFile(article.fullContent, uniqueFilename),
            `file_write_${uniqueFilename}`,
            ErrorTypes.FILE_SYSTEM
          );

          writtenFiles.push({
            filename: uniqueFilename,
            path: filePath,
            title: article.frontMatter.title
          });

          await this.logger.info(`Article written: ${uniqueFilename}`);

        } catch (error) {
          await this.logger.error(`Failed to write article ${article.filename}:`, error);
          const errorInfo = {
            step: 'file_writing',
            filename: article.filename,
            error: error.message,
            type: error.type || ErrorTypes.FILE_SYSTEM
          };
          errors.push(errorInfo);
          this.stats.errors.push(errorInfo);
        }
      }

      await this.logger.info(`Successfully wrote ${writtenFiles.length} articles`);
      
      if (errors.length > 0) {
        await this.logger.warn(`Encountered ${errors.length} errors during file writing`);
      }

      await writeTimer.end({ 
        articlesWritten: writtenFiles.length, 
        errors: errors.length,
        totalArticles: articles.length
      });
      
      return writtenFiles;

    } catch (error) {
      await writeTimer.end({ success: false });
      await this.logger.error('Failed to write articles to files:', error);
      throw error;
    }
  }

  /**
   * Build Hugo site
   */
  async buildHugoSite() {
    const buildTimer = this.logger.timer('hugo_build');
    
    try {
      await this.logger.info('Building Hugo site...');
      
      // Validate site configuration
      const isValidSite = await this.executeWithErrorHandling(
        () => this.components.hugoBuilder.validateSiteConfiguration(),
        'hugo_site_validation',
        ErrorTypes.BUILD
      );

      if (!isValidSite) {
        throw new Error('Hugo site configuration validation failed');
      }

      // Build site with optimization
      const buildResult = await this.executeWithErrorHandling(
        () => this.components.hugoBuilder.buildSite({
          minify: true,
          gc: true,
          cleanDestinationDir: true
        }),
        'hugo_site_build',
        ErrorTypes.BUILD
      );

      if (buildResult.success) {
        await this.logger.info(`Hugo build completed successfully in ${buildResult.buildTime}ms`);
        await this.logger.info(`Pages generated: ${buildResult.stats?.pages || 'unknown'}`);
        await buildTimer.end({ 
          success: true, 
          buildTime: buildResult.buildTime,
          pages: buildResult.stats?.pages
        });
      } else {
        throw new Error(`Hugo build failed: ${buildResult.error || 'Unknown error'}`);
      }

      return buildResult;

    } catch (error) {
      await buildTimer.end({ success: false });
      await this.logger.error('Hugo site build failed:', error);
      
      // Log specific error guidance
      if (error.message.includes('Hugo not found')) {
        await this.logger.error('Hugo is not installed. Please install Hugo to continue.');
      } else if (error.message.includes('config')) {
        await this.logger.error('Hugo configuration error. Please check hugo.toml file.');
      } else if (error.message.includes('template')) {
        await this.logger.error('Hugo template error. Please check your theme and layout files.');
      }
      
      throw error;
    }
  }

  /**
   * Handle rate limiting with exponential backoff
   */
  async handleRateLimit() {
    try {
      const rateLimitStatus = this.components.twitterClient.getRateLimitStatus();
      const waitTime = Math.max(rateLimitStatus.windowRemainingMs, 60000); // At least 1 minute
      
      await this.logger.info(`Rate limit reached. Waiting ${Math.ceil(waitTime / 1000)} seconds...`);
      
      await new Promise(resolve => setTimeout(resolve, waitTime));
      
      await this.logger.info('Rate limit wait completed, resuming operations');
    } catch (error) {
      await this.logger.error('Error handling rate limit:', error);
      // Default wait time if we can't get rate limit status
      await new Promise(resolve => setTimeout(resolve, 60000));
    }
  }

  /**
   * Cleanup resources and temporary files
   */
  async cleanup() {
    const cleanupTimer = this.logger.timer('cleanup');
    
    try {
      await this.logger.info('Performing cleanup...');
      
      // Clean up any temporary files
      await this.executeWithErrorHandling(
        () => this.components.duplicateChecker.cleanupOldEntries(),
        'cleanup_old_entries',
        ErrorTypes.FILE_SYSTEM
      );

      // Rotate logs if needed
      if (this.logger.rotateLogs) {
        await this.executeWithErrorHandling(
          () => this.logger.rotateLogs(),
          'log_rotation',
          ErrorTypes.FILE_SYSTEM
        );
      }

      // Close logger resources
      if (this.logger.close) {
        await this.logger.close();
      }
      
      await this.logger.info('Cleanup completed');
      await cleanupTimer.end({ success: true });
    } catch (error) {
      await cleanupTimer.end({ success: false });
      await this.logger.warn('Cleanup encountered errors:', error);
    }
  }

  /**
   * Generate execution report
   */
  generateReport() {
    const duration = this.stats.endTime 
      ? this.stats.endTime.getTime() - this.stats.startTime.getTime()
      : Date.now() - this.stats.startTime.getTime();

    const errorStats = this.errorHandler ? this.errorHandler.getErrorStats() : {};

    const report = {
      executionTime: duration,
      executionTimeFormatted: this.formatDuration(duration),
      startTime: this.stats.startTime,
      endTime: this.stats.endTime,
      statistics: {
        tweetsFound: this.stats.tweetsFound,
        tweetsProcessed: this.stats.tweetsProcessed,
        articlesGenerated: this.stats.articlesGenerated,
        duplicatesSkipped: this.stats.duplicatesSkipped,
        errorsEncountered: this.stats.errors.length,
        recoveredErrors: this.stats.recoveredErrors
      },
      errorStatistics: errorStats,
      errors: this.stats.errors,
      success: this.stats.articlesGenerated > 0,
      hasErrors: this.stats.errors.length > 0,
      criticalErrors: this.stats.errors.filter(e => e.severity === ErrorSeverity.CRITICAL).length
    };

    // Log summary
    this.logger.info('=== EXECUTION REPORT ===');
    this.logger.info(`Duration: ${report.executionTimeFormatted}`);
    this.logger.info(`Articles Generated: ${report.statistics.articlesGenerated}`);
    this.logger.info(`Errors Encountered: ${report.statistics.errorsEncountered}`);
    this.logger.info(`Errors Recovered: ${report.statistics.recoveredErrors}`);
    this.logger.info(`Success: ${report.success ? 'YES' : 'NO'}`);
    
    if (report.hasErrors) {
      this.logger.warn('Errors occurred during execution:', report.errors);
    }

    this.logger.debug('Full Execution Report:', JSON.stringify(report, null, 2));
    return report;
  }

  /**
   * Format duration in human-readable format
   * @param {number} ms - Duration in milliseconds
   * @returns {string} Formatted duration
   */
  formatDuration(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  }
}



/**
 * Main execution function
 */
async function main() {
  const automation = new TwitterCryptoAutomation();
  
  try {
    await automation.initialize();
    const report = await automation.executeWorkflow();
    
    if (report.success && !report.hasErrors) {
      console.log('✅ Twitter Crypto Content Automation completed successfully!');
      console.log(`📊 Generated ${report.statistics.articlesGenerated} articles in ${report.executionTimeFormatted}`);
      process.exit(0);
    } else if (report.success && report.hasErrors) {
      console.log('⚠️ Twitter Crypto Content Automation completed with some errors.');
      console.log(`📊 Generated ${report.statistics.articlesGenerated} articles with ${report.statistics.errorsEncountered} errors`);
      console.log(`🔄 Recovered from ${report.statistics.recoveredErrors} errors`);
      process.exit(report.criticalErrors > 0 ? 1 : 0);
    } else {
      console.log('❌ Twitter Crypto Content Automation failed to generate any articles.');
      console.log(`📊 Encountered ${report.statistics.errorsEncountered} errors`);
      process.exit(1);
    }
  } catch (error) {
    console.error('❌ Twitter Crypto Content Automation failed:', error.message);
    
    // Log additional error details if available
    if (error.type) {
      console.error(`Error Type: ${error.type}`);
    }
    if (error.severity) {
      console.error(`Severity: ${error.severity}`);
    }
    
    process.exit(1);
  }
}

// Execute if this file is run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export { TwitterCryptoAutomation };