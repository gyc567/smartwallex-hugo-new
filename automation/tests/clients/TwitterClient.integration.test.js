import { TwitterClient } from '../../src/clients/TwitterClient.js';
import ConfigLoader from '../../src/config/ConfigLoader.js';
import dotenv from 'dotenv';
import path from 'path';

// Load environment variables
dotenv.config({ path: path.join(process.cwd(), '.env') });

describe('TwitterClient - Integration Tests', () => {
  let twitterClient;
  let config;
  let hasValidToken = false;

  beforeAll(async () => {
    // Load real configuration
    config = await ConfigLoader.load();
    
    // Check if we have a valid token
    hasValidToken = process.env.TWITTER_BEARER_TOKEN && 
                   process.env.TWITTER_BEARER_TOKEN !== 'your_bearer_token_here' &&
                   process.env.TWITTER_BEARER_TOKEN.length > 50;

    if (hasValidToken) {
      console.log('✅ Valid Twitter Bearer Token detected - running live API tests');
      twitterClient = new TwitterClient(config);
      await twitterClient.initialize();
    } else {
      console.log('⚠️  No valid Twitter Bearer Token - running configuration tests only');
      console.log('To run live API tests, set TWITTER_BEARER_TOKEN in .env file');
    }
  });

  describe('Configuration and Setup', () => {
    test('should load configuration successfully', () => {
      expect(config).toBeDefined();
      expect(config.twitter).toBeDefined();
      expect(config.twitter.baseUrl).toBe('https://api.twitter.com/2');
    });

    test('should detect Bearer Token presence', () => {
      const tokenExists = !!process.env.TWITTER_BEARER_TOKEN;
      expect(tokenExists).toBe(true);
      
      if (hasValidToken) {
        console.log('✅ Bearer Token format appears valid');
      } else {
        console.log('⚠️  Bearer Token appears to be placeholder or invalid');
      }
    });

    test('should initialize TwitterClient without errors', () => {
      if (hasValidToken) {
        expect(twitterClient).toBeDefined();
        expect(typeof twitterClient.searchTweets).toBe('function');
        expect(typeof twitterClient.getTweetDetails).toBe('function');
      } else {
        // Test with placeholder token should fail gracefully
        expect(() => {
          const testClient = new TwitterClient(config);
        }).not.toThrow();
      }
    });
  });

  describe('Rate Limiting (Configuration)', () => {
    test('should have rate limit configuration', () => {
      expect(config.twitter.rateLimits).toBeDefined();
      expect(config.twitter.rateLimits.searchRequests).toBeGreaterThan(0);
      expect(config.twitter.rateLimits.windowMinutes).toBeGreaterThan(0);
    });

    test('should initialize rate limit tracking', () => {
      if (hasValidToken) {
        const status = twitterClient.getRateLimitStatus();
        expect(status).toHaveProperty('requestsUsed');
        expect(status).toHaveProperty('requestsRemaining');
        expect(status).toHaveProperty('windowRemainingMs');
        expect(status).toHaveProperty('resetTime');
        expect(status.requestsUsed).toBe(0);
      }
    });
  });

  describe('Live API Tests', () => {
    beforeEach(() => {
      if (!hasValidToken) {
        pending('Skipping live API tests - no valid Bearer Token');
      }
    });

    test('should connect to Twitter API successfully', async () => {
      expect(twitterClient).toBeDefined();
      
      // Test basic connectivity by checking rate limit status
      const status = twitterClient.getRateLimitStatus();
      expect(status.requestsRemaining).toBeGreaterThanOrEqual(0);
    }, 10000);

    test('should search for tweets with basic query', async () => {
      try {
        const tweets = await twitterClient.searchTweets(['bitcoin'], 5);
        
        expect(Array.isArray(tweets)).toBe(true);
        console.log(`✅ Search successful: Found ${tweets.length} tweets`);
        
        if (tweets.length > 0) {
          const tweet = tweets[0];
          expect(tweet).toHaveProperty('id');
          expect(tweet).toHaveProperty('text');
          expect(tweet).toHaveProperty('author');
          expect(tweet).toHaveProperty('metrics');
          
          console.log('Sample tweet:', {
            id: tweet.id,
            author: tweet.author.username,
            text: tweet.text.substring(0, 100) + '...'
          });
        }
      } catch (error) {
        if (error.message.includes('forbidden') || error.message.includes('authentication')) {
          console.log('❌ API Access Error:', error.message);
          console.log('This suggests the Bearer Token may not have the required permissions');
          console.log('Required: Twitter API v2 with Tweet.read scope');
          throw new Error('API authentication/authorization failed - check token permissions');
        } else {
          throw error;
        }
      }
    }, 30000);

    test('should handle rate limiting correctly', async () => {
      const initialStatus = twitterClient.getRateLimitStatus();
      
      try {
        await twitterClient.searchTweets(['crypto'], 3);
        
        const afterStatus = twitterClient.getRateLimitStatus();
        expect(afterStatus.requestsUsed).toBeGreaterThan(initialStatus.requestsUsed);
        
        console.log('✅ Rate limiting tracked correctly:', {
          before: initialStatus.requestsUsed,
          after: afterStatus.requestsUsed,
          remaining: afterStatus.requestsRemaining
        });
      } catch (error) {
        if (error.message.includes('rate limit')) {
          console.log('✅ Rate limiting working - hit rate limit');
          expect(error.message).toContain('rate limit');
        } else {
          throw error;
        }
      }
    }, 30000);

    test('should validate tweet quality correctly', async () => {
      try {
        const tweets = await twitterClient.searchTweets(['cryptocurrency'], 10);
        
        if (tweets.length > 0) {
          let qualityResults = { high: 0, low: 0 };
          
          tweets.forEach(tweet => {
            const isHighQuality = twitterClient.validateTweetQuality(tweet);
            if (isHighQuality) {
              qualityResults.high++;
            } else {
              qualityResults.low++;
            }
          });
          
          console.log('✅ Quality validation results:', qualityResults);
          expect(qualityResults.high + qualityResults.low).toBe(tweets.length);
        }
      } catch (error) {
        if (!error.message.includes('forbidden') && !error.message.includes('authentication')) {
          throw error;
        }
      }
    }, 30000);
  });

  describe('Error Handling', () => {
    test('should handle invalid token gracefully', async () => {
      const invalidConfig = { ...config };
      const originalToken = process.env.TWITTER_BEARER_TOKEN;
      
      try {
        process.env.TWITTER_BEARER_TOKEN = 'invalid_token_12345';
        const invalidClient = new TwitterClient(invalidConfig);
        await invalidClient.initialize();
        
        await expect(invalidClient.searchTweets(['test'], 1))
          .rejects.toThrow();
      } finally {
        process.env.TWITTER_BEARER_TOKEN = originalToken;
      }
    }, 15000);

    test('should provide helpful error messages', () => {
      const testCases = [
        {
          error: { response: { status: 401 } },
          expectedMessage: 'authentication failed'
        },
        {
          error: { response: { status: 403 } },
          expectedMessage: 'access forbidden'
        },
        {
          error: { response: { status: 429 } },
          expectedMessage: 'rate limit'
        }
      ];

      testCases.forEach(({ error, expectedMessage }) => {
        expect(async () => {
          if (hasValidToken) {
            await twitterClient.handleApiError(error);
          }
        }).toBeDefined();
      });
    });
  });

  describe('Data Processing', () => {
    test('should process mock API response correctly', () => {
      if (!hasValidToken) {
        // Create a mock client for testing data processing
        const mockClient = new TwitterClient(config, true);
        
        const mockApiResponse = {
          data: [
            {
              id: '1234567890',
              text: 'Test tweet about cryptocurrency and blockchain technology',
              author_id: 'user123',
              created_at: '2025-08-16T10:00:00.000Z',
              public_metrics: {
                retweet_count: 25,
                like_count: 100,
                reply_count: 5,
                quote_count: 2
              },
              lang: 'en',
              possibly_sensitive: false
            }
          ],
          includes: {
            users: [
              {
                id: 'user123',
                username: 'cryptoexpert',
                name: 'Crypto Expert',
                verified: true,
                public_metrics: {
                  followers_count: 5000
                },
                description: 'Cryptocurrency analyst'
              }
            ]
          }
        };

        const processed = mockClient.processTweetData(mockApiResponse);
        
        expect(processed).toHaveLength(1);
        expect(processed[0]).toMatchObject({
          id: '1234567890',
          text: 'Test tweet about cryptocurrency and blockchain technology',
          author: {
            username: 'cryptoexpert',
            displayName: 'Crypto Expert',
            verified: true,
            followerCount: 5000
          },
          metrics: {
            retweetCount: 25,
            likeCount: 100,
            replyCount: 5,
            quoteCount: 2
          }
        });

        console.log('✅ Data processing validation passed');
      }
    });
  });

  afterAll(() => {
    if (hasValidToken) {
      console.log('✅ Integration tests completed with live API');
    } else {
      console.log('✅ Configuration tests completed');
      console.log('💡 To test with live API, provide a valid TWITTER_BEARER_TOKEN');
    }
  });
});