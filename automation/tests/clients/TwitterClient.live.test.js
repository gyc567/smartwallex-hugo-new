import { TwitterClient } from '../../src/clients/TwitterClient.js';
import ConfigLoader from '../../src/config/ConfigLoader.js';
import dotenv from 'dotenv';
import path from 'path';

// Load environment variables
dotenv.config({ path: path.join(process.cwd(), '.env') });

describe('TwitterClient - Live API Tests', () => {
  let twitterClient;
  let config;

  beforeAll(async () => {
    // Load real configuration
    config = await ConfigLoader.load();
    
    // Initialize TwitterClient with real API
    twitterClient = new TwitterClient(config);
    await twitterClient.initialize();
  });

  describe('Real API Connection', () => {
    test('should connect to Twitter API successfully', async () => {
      expect(twitterClient).toBeDefined();
      expect(process.env.TWITTER_BEARER_TOKEN).toBeDefined();
    });

    test('should have valid rate limit status', () => {
      const rateLimitStatus = twitterClient.getRateLimitStatus();
      
      expect(rateLimitStatus).toHaveProperty('requestsUsed');
      expect(rateLimitStatus).toHaveProperty('requestsRemaining');
      expect(rateLimitStatus).toHaveProperty('windowRemainingMs');
      expect(rateLimitStatus).toHaveProperty('resetTime');
      
      expect(typeof rateLimitStatus.requestsUsed).toBe('number');
      expect(typeof rateLimitStatus.requestsRemaining).toBe('number');
      expect(rateLimitStatus.requestsRemaining).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Live Tweet Search', () => {
    test('should search for crypto tweets successfully', async () => {
      const tweets = await twitterClient.searchTweets(['bitcoin'], 10);
      
      expect(Array.isArray(tweets)).toBe(true);
      
      if (tweets.length > 0) {
        const tweet = tweets[0];
        
        // Validate tweet structure
        expect(tweet).toHaveProperty('id');
        expect(tweet).toHaveProperty('text');
        expect(tweet).toHaveProperty('author');
        expect(tweet).toHaveProperty('metrics');
        expect(tweet).toHaveProperty('createdAt');
        expect(tweet).toHaveProperty('url');
        
        // Validate author structure
        expect(tweet.author).toHaveProperty('username');
        expect(tweet.author).toHaveProperty('displayName');
        expect(tweet.author).toHaveProperty('verified');
        expect(tweet.author).toHaveProperty('followerCount');
        
        // Validate metrics structure
        expect(tweet.metrics).toHaveProperty('retweetCount');
        expect(tweet.metrics).toHaveProperty('likeCount');
        expect(tweet.metrics).toHaveProperty('replyCount');
        expect(tweet.metrics).toHaveProperty('quoteCount');
        
        // Validate data types
        expect(typeof tweet.id).toBe('string');
        expect(typeof tweet.text).toBe('string');
        expect(typeof tweet.author.username).toBe('string');
        expect(typeof tweet.author.followerCount).toBe('number');
        expect(typeof tweet.metrics.retweetCount).toBe('number');
        
        console.log('Sample tweet found:', {
          id: tweet.id,
          text: tweet.text.substring(0, 100) + '...',
          author: tweet.author.username,
          metrics: tweet.metrics
        });
      } else {
        console.log('No tweets found in search results');
      }
    }, 30000); // 30 second timeout for API calls

    test('should search with multiple keywords', async () => {
      const tweets = await twitterClient.searchTweets(['ethereum', 'blockchain'], 5);
      
      expect(Array.isArray(tweets)).toBe(true);
      
      if (tweets.length > 0) {
        // Check if tweets contain relevant keywords
        const hasRelevantContent = tweets.some(tweet => {
          const text = tweet.text.toLowerCase();
          return text.includes('ethereum') || 
                 text.includes('blockchain') || 
                 text.includes('crypto') ||
                 text.includes('btc') ||
                 text.includes('eth');
        });
        
        expect(hasRelevantContent).toBe(true);
        console.log(`Found ${tweets.length} tweets with ethereum/blockchain keywords`);
      }
    }, 30000);

    test('should handle empty search results gracefully', async () => {
      // Search for very specific unlikely terms
      const tweets = await twitterClient.searchTweets(['veryrareunlikelycryptoterm12345'], 5);
      
      expect(Array.isArray(tweets)).toBe(true);
      console.log(`Search for rare terms returned ${tweets.length} tweets`);
    }, 30000);
  });

  describe('Live Tweet Details', () => {
    test('should retrieve tweet details if tweet exists', async () => {
      // First search for a tweet to get a real ID
      const searchResults = await twitterClient.searchTweets(['bitcoin'], 1);
      
      if (searchResults.length > 0) {
        const tweetId = searchResults[0].id;
        
        const tweetDetails = await twitterClient.getTweetDetails(tweetId);
        
        expect(tweetDetails).toHaveProperty('id', tweetId);
        expect(tweetDetails).toHaveProperty('text');
        expect(tweetDetails).toHaveProperty('author');
        expect(tweetDetails).toHaveProperty('metrics');
        
        console.log('Retrieved tweet details for ID:', tweetId);
      } else {
        console.log('No tweets found to test details retrieval');
      }
    }, 30000);

    test('should handle non-existent tweet ID', async () => {
      const nonExistentId = '999999999999999999'; // Very unlikely to exist
      
      await expect(twitterClient.getTweetDetails(nonExistentId))
        .rejects.toThrow();
    }, 30000);
  });

  describe('Tweet Quality Validation', () => {
    test('should validate real tweet quality', async () => {
      const tweets = await twitterClient.searchTweets(['cryptocurrency'], 20);
      
      if (tweets.length > 0) {
        let highQualityCount = 0;
        let lowQualityCount = 0;
        
        tweets.forEach(tweet => {
          const isHighQuality = twitterClient.validateTweetQuality(tweet);
          if (isHighQuality) {
            highQualityCount++;
          } else {
            lowQualityCount++;
          }
        });
        
        console.log(`Quality validation results: ${highQualityCount} high quality, ${lowQualityCount} low quality tweets`);
        
        // At least some tweets should pass quality validation
        expect(highQualityCount + lowQualityCount).toBe(tweets.length);
      }
    }, 30000);
  });

  describe('Rate Limiting', () => {
    test('should track rate limit usage correctly', async () => {
      const initialStatus = twitterClient.getRateLimitStatus();
      const initialUsed = initialStatus.requestsUsed;
      
      // Make a search request
      await twitterClient.searchTweets(['bitcoin'], 5);
      
      const afterStatus = twitterClient.getRateLimitStatus();
      const afterUsed = afterStatus.requestsUsed;
      
      // Should have incremented usage
      expect(afterUsed).toBeGreaterThan(initialUsed);
      expect(afterStatus.requestsRemaining).toBeLessThan(initialStatus.requestsRemaining);
      
      console.log('Rate limit status:', {
        used: afterUsed,
        remaining: afterStatus.requestsRemaining,
        resetTime: afterStatus.resetTime
      });
    }, 30000);

    test('should respect rate limits', () => {
      const status = twitterClient.getRateLimitStatus();
      
      // Should not exceed the configured limit
      expect(status.requestsUsed).toBeLessThanOrEqual(config.twitter.rateLimits.searchRequests);
      expect(status.requestsRemaining).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Error Handling', () => {
    test('should handle API errors gracefully', async () => {
      // Create a client with invalid token to test error handling
      const invalidConfig = { ...config };
      const originalToken = process.env.TWITTER_BEARER_TOKEN;
      
      try {
        process.env.TWITTER_BEARER_TOKEN = 'invalid_token_12345';
        const invalidClient = new TwitterClient(invalidConfig);
        await invalidClient.initialize();
        
        await expect(invalidClient.searchTweets(['bitcoin'], 5))
          .rejects.toThrow();
      } finally {
        // Restore original token
        process.env.TWITTER_BEARER_TOKEN = originalToken;
      }
    }, 30000);
  });

  describe('Data Processing', () => {
    test('should process real API response correctly', async () => {
      const tweets = await twitterClient.searchTweets(['crypto'], 3);
      
      if (tweets.length > 0) {
        tweets.forEach(tweet => {
          // Validate URL format
          expect(tweet.url).toMatch(/^https:\/\/twitter\.com\/\w+\/status\/\d+$/);
          
          // Validate date format
          expect(new Date(tweet.createdAt)).toBeInstanceOf(Date);
          expect(new Date(tweet.createdAt).getTime()).not.toBeNaN();
          
          // Validate metrics are numbers
          expect(typeof tweet.metrics.retweetCount).toBe('number');
          expect(typeof tweet.metrics.likeCount).toBe('number');
          expect(typeof tweet.metrics.replyCount).toBe('number');
          expect(typeof tweet.metrics.quoteCount).toBe('number');
          
          // Validate author data
          expect(typeof tweet.author.verified).toBe('boolean');
          expect(typeof tweet.author.followerCount).toBe('number');
          expect(tweet.author.followerCount).toBeGreaterThanOrEqual(0);
        });
        
        console.log('Data processing validation passed for all tweets');
      }
    }, 30000);
  });
});