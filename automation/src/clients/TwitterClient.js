import axios from 'axios';
import ConfigLoader from '../config/ConfigLoader.js';

/**
 * Twitter API client for searching and retrieving cryptocurrency content
 * Handles authentication, rate limiting, and error handling
 */
export class TwitterClient {
  constructor(mockConfig = null, disableInterceptors = false, mockClient = null) {
    this.bearerToken = process.env.TWITTER_BEARER_TOKEN;
    this.config = null;
    this.initialized = false;
    this.mockConfig = mockConfig; // For testing purposes
    this.disableInterceptors = disableInterceptors; // For testing purposes
    this.mockClient = mockClient; // For testing purposes

    if (!this.bearerToken) {
      throw new Error('Twitter Bearer Token is required. Set TWITTER_BEARER_TOKEN environment variable.');
    }
  }

  /**
   * Initialize the client with configuration
   * @private
   */
  async initialize() {
    if (this.initialized) return;

    this.config = this.mockConfig || await ConfigLoader.load();
    this.baseUrl = this.config.twitter.baseUrl;

    this.rateLimitTracker = {
      requests: 0,
      windowStart: Date.now(),
      windowDuration: this.config.twitter.rateLimits.windowMinutes * 60 * 1000
    };

    // Configure axios instance with default headers (or use mock for testing)
    this.client = this.mockClient || axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Authorization': `Bearer ${this.bearerToken}`,
        'Content-Type': 'application/json'
      },
      timeout: 30000 // 30 second timeout
    });

    // Add response interceptor for rate limit handling (skip in tests)
    if (!this.disableInterceptors) {
      this.client.interceptors.response.use(
        response => response,
        async error => {
          return await this.handleApiError(error);
        }
      );
    }

    this.initialized = true;
  }

  /**
   * Search for tweets using cryptocurrency keywords
   * @param {string[]} keywords - Array of search keywords
   * @param {number} count - Maximum number of tweets to retrieve
   * @returns {Promise<Object[]>} Array of tweet objects
   */
  async searchTweets(keywords = null, count = null) {
    try {
      await this.initialize();
      await this.checkRateLimit();

      const searchKeywords = keywords || this.config.twitter.searchKeywords;
      const maxResults = Math.min(count || this.config.twitter.maxResults, 100);

      // Combine keywords with OR operator
      const query = searchKeywords.join(' OR ');

      const params = {
        query: `(${query}) -is:retweet lang:en`,
        max_results: maxResults,
        'tweet.fields': 'id,text,author_id,created_at,public_metrics,context_annotations,lang,possibly_sensitive',
        'user.fields': 'id,name,username,verified,public_metrics,description',
        'expansions': 'author_id',
        'sort_order': 'relevancy'
      };

      console.log(`Searching Twitter for crypto content with query: ${params.query}`);

      const response = await this.client.get(this.config.twitter.searchEndpoint, { params });

      this.updateRateLimitTracker();

      if (!response.data || !response.data.data) {
        console.warn('No tweets found in search results');
        return [];
      }

      // Process and enrich tweet data
      const tweets = this.processTweetData(response.data);

      console.log(`Found ${tweets.length} tweets matching crypto keywords`);
      return tweets;

    } catch (error) {
      console.error('Error searching tweets:', error.message);
      throw new Error(`Twitter search failed: ${error.message}`);
    }
  }

  /**
   * Get detailed information for a specific tweet
   * @param {string} tweetId - The ID of the tweet to retrieve
   * @returns {Promise<Object>} Detailed tweet object
   */
  async getTweetDetails(tweetId) {
    try {
      await this.initialize();
      await this.checkRateLimit();

      const params = {
        'tweet.fields': 'id,text,author_id,created_at,public_metrics,context_annotations,lang,possibly_sensitive,referenced_tweets',
        'user.fields': 'id,name,username,verified,public_metrics,description,profile_image_url',
        'expansions': 'author_id,referenced_tweets.id'
      };

      console.log(`Retrieving details for tweet ID: ${tweetId}`);

      const response = await this.client.get(`/tweets/${tweetId}`, { params });

      this.updateRateLimitTracker();

      if (!response.data || !response.data.data) {
        throw new Error(`Tweet with ID ${tweetId} not found`);
      }

      // Process single tweet data - wrap in array for processTweetData
      const wrappedData = {
        data: [response.data.data],
        includes: response.data.includes
      };
      const tweetData = this.processTweetData(wrappedData);

      console.log(`Retrieved details for tweet by @${tweetData[0].author.username}`);
      return tweetData[0];

    } catch (error) {
      console.error(`Error retrieving tweet ${tweetId}:`, error.message);
      throw new Error(`Failed to get tweet details: ${error.message}`);
    }
  }

  /**
   * Get current rate limit status
   * @returns {Object} Rate limit information
   */
  getRateLimitStatus() {
    const now = Date.now();
    const windowElapsed = now - this.rateLimitTracker.windowStart;
    const windowRemaining = Math.max(0, this.rateLimitTracker.windowDuration - windowElapsed);

    // Reset window if expired
    if (windowElapsed >= this.rateLimitTracker.windowDuration) {
      this.rateLimitTracker.requests = 0;
      this.rateLimitTracker.windowStart = now;
    }

    return {
      requestsUsed: this.rateLimitTracker.requests,
      requestsRemaining: Math.max(0, this.config.twitter.rateLimits.searchRequests - this.rateLimitTracker.requests),
      windowRemainingMs: windowRemaining,
      resetTime: new Date(this.rateLimitTracker.windowStart + this.rateLimitTracker.windowDuration)
    };
  }

  /**
   * Check if we're within rate limits before making a request
   * @private
   */
  async checkRateLimit() {
    const status = this.getRateLimitStatus();

    if (status.requestsRemaining <= 0) {
      const waitTime = Math.ceil(status.windowRemainingMs / 1000);
      console.warn(`Rate limit reached. Waiting ${waitTime} seconds until reset...`);

      if (waitTime > 0) {
        await this.sleep(status.windowRemainingMs);
        // Reset tracker after waiting
        this.rateLimitTracker.requests = 0;
        this.rateLimitTracker.windowStart = Date.now();
      }
    }
  }

  /**
   * Update rate limit tracker after successful request
   * @private
   */
  updateRateLimitTracker() {
    this.rateLimitTracker.requests++;
  }

  /**
   * Process raw Twitter API response data into structured format
   * @param {Object} apiResponse - Raw API response
   * @returns {Object[]} Processed tweet objects
   * @private
   */
  processTweetData(apiResponse) {
    const tweets = apiResponse.data;
    const users = apiResponse.includes?.users || [];

    // Create user lookup map
    const userMap = users.reduce((map, user) => {
      map[user.id] = user;
      return map;
    }, {});

    return tweets.map(tweet => {
      const author = userMap[tweet.author_id] || {};

      return {
        id: tweet.id,
        text: tweet.text,
        author: {
          id: author.id || tweet.author_id,
          username: author.username || 'unknown',
          displayName: author.name || 'Unknown User',
          verified: author.verified || false,
          followerCount: author.public_metrics?.followers_count || 0,
          description: author.description || '',
          profileImageUrl: author.profile_image_url || ''
        },
        metrics: {
          retweetCount: tweet.public_metrics?.retweet_count || 0,
          likeCount: tweet.public_metrics?.like_count || 0,
          replyCount: tweet.public_metrics?.reply_count || 0,
          quoteCount: tweet.public_metrics?.quote_count || 0
        },
        createdAt: tweet.created_at,
        url: `https://twitter.com/${author.username || 'i'}/status/${tweet.id}`,
        lang: tweet.lang,
        possiblySensitive: tweet.possibly_sensitive || false,
        contextAnnotations: tweet.context_annotations || []
      };
    });
  }

  /**
   * Handle API errors with appropriate retry logic
   * @param {Error} error - Axios error object
   * @private
   */
  async handleApiError(error) {
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data;

      switch (status) {
        case 429: // Rate limit exceeded
          const resetTime = error.response.headers['x-rate-limit-reset'];
          const rateLimitError = new Error('Twitter API rate limit exceeded');
          rateLimitError.response = error.response;
          rateLimitError.resetTime = resetTime;

          if (resetTime) {
            const waitTime = (parseInt(resetTime) * 1000) - Date.now();
            if (waitTime > 0 && waitTime < 900000) { // Max 15 minutes
              console.warn(`Rate limit exceeded. Waiting ${Math.ceil(waitTime / 1000)} seconds...`);
              await this.sleep(waitTime);
              // Retry the original request
              return this.client.request(error.config);
            }
          }
          throw rateLimitError;

        case 401: // Unauthorized
          const authError = new Error('Twitter API authentication failed. Check your bearer token.');
          authError.response = error.response;
          throw authError;

        case 403: // Forbidden
          const forbiddenError = new Error('Twitter API access forbidden. Check your API permissions.');
          forbiddenError.response = error.response;
          throw forbiddenError;

        case 404: // Not found
          const notFoundError = new Error('Twitter API endpoint not found.');
          notFoundError.response = error.response;
          throw notFoundError;

        case 500:
        case 502:
        case 503:
        case 504: // Server errors
          console.warn(`Twitter API server error (${status}). Retrying in 5 seconds...`);
          await this.sleep(5000);
          return this.client.request(error.config);

        default:
          console.error(`Twitter API error ${status}:`, data);
          const apiError = new Error(`Twitter API error: ${status} ${data?.message || 'Unknown error'}`);
          apiError.response = error.response;
          throw apiError;
      }
    } else if (error.code === 'ECONNABORTED') {
      const timeoutError = new Error('Twitter API request timeout. Please try again.');
      timeoutError.code = error.code;
      throw timeoutError;
    } else if (error.code === 'ENOTFOUND' || error.code === 'ECONNREFUSED') {
      const networkError = new Error('Unable to connect to Twitter API. Check your internet connection.');
      networkError.code = error.code;
      throw networkError;
    }

    throw error;
  }

  /**
   * Sleep for specified milliseconds
   * @param {number} ms - Milliseconds to sleep
   * @private
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Validate tweet content quality
   * @param {Object} tweet - Tweet object to validate
   * @returns {boolean} True if tweet meets quality criteria
   */
  validateTweetQuality(tweet) {
    const minRetweetCount = this.config.content.minRetweetCount;
    const minCharacterCount = this.config.content.minCharacterCount;

    // Check minimum engagement
    if (tweet.metrics.retweetCount < minRetweetCount) {
      return false;
    }

    // Check minimum content length
    if (tweet.text.length < minCharacterCount) {
      return false;
    }

    // Skip potentially sensitive content
    if (tweet.possiblySensitive) {
      return false;
    }

    // Skip tweets that are mostly links or mentions
    const textWithoutUrls = tweet.text.replace(/https?:\/\/\S+/g, '').replace(/@\w+/g, '');
    if (textWithoutUrls.trim().length < minCharacterCount * 0.7) {
      return false;
    }

    return true;
  }
}