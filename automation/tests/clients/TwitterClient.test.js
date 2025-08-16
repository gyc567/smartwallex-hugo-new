import { jest } from '@jest/globals';
import { TwitterClient } from '../../src/clients/TwitterClient.js';

describe('TwitterClient', () => {
  let mockConfig;
  let mockAxiosInstance;

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();
    
    // Mock axios instance
    mockAxiosInstance = {
      get: jest.fn(),
      interceptors: {
        response: {
          use: jest.fn()
        }
      }
    };
    
    // Mock configuration
    mockConfig = {
      twitter: {
        baseUrl: 'https://api.twitter.com/2',
        searchEndpoint: '/tweets/search/recent',
        maxResults: 100,
        searchKeywords: [
          'cryptocurrency OR crypto',
          'blockchain OR bitcoin OR BTC'
        ],
        rateLimits: {
          searchRequests: 300,
          windowMinutes: 15
        }
      },
      content: {
        minRetweetCount: 10,
        minCharacterCount: 50
      }
    };

    // Set environment variable
    process.env.TWITTER_BEARER_TOKEN = 'test-bearer-token';
  });

  afterEach(() => {
    delete process.env.TWITTER_BEARER_TOKEN;
  });

  describe('Constructor', () => {
    test('should initialize with valid bearer token', () => {
      expect(() => new TwitterClient(mockConfig)).not.toThrow();
    });

    test('should throw error without bearer token', () => {
      delete process.env.TWITTER_BEARER_TOKEN;
      expect(() => new TwitterClient(mockConfig)).toThrow('Twitter Bearer Token is required');
    });
  });

  describe('searchTweets', () => {
    let twitterClient;

    beforeEach(() => {
      twitterClient = new TwitterClient(mockConfig, true, mockAxiosInstance); // Pass mock client
    });

    test('should search tweets with default parameters', async () => {
      const mockResponse = {
        data: {
          data: [
            {
              id: '1234567890',
              text: 'Bitcoin is reaching new heights! #crypto #blockchain',
              author_id: 'user123',
              created_at: '2025-08-14T09:00:00.000Z',
              public_metrics: {
                retweet_count: 50,
                like_count: 200,
                reply_count: 10,
                quote_count: 5
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
                  followers_count: 10000
                },
                description: 'Cryptocurrency analyst'
              }
            ]
          }
        }
      };

      mockAxiosInstance.get.mockResolvedValue(mockResponse);

      const result = await twitterClient.searchTweets();

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/tweets/search/recent', {
        params: {
          query: '(cryptocurrency OR crypto OR blockchain OR bitcoin OR BTC) -is:retweet lang:en',
          max_results: 100,
          'tweet.fields': 'id,text,author_id,created_at,public_metrics,context_annotations,lang,possibly_sensitive',
          'user.fields': 'id,name,username,verified,public_metrics,description',
          'expansions': 'author_id',
          'sort_order': 'relevancy'
        }
      });

      expect(result).toHaveLength(1);
      expect(result[0]).toMatchObject({
        id: '1234567890',
        text: 'Bitcoin is reaching new heights! #crypto #blockchain',
        author: {
          username: 'cryptoexpert',
          displayName: 'Crypto Expert',
          verified: true,
          followerCount: 10000
        },
        metrics: {
          retweetCount: 50,
          likeCount: 200,
          replyCount: 10,
          quoteCount: 5
        },
        url: 'https://twitter.com/cryptoexpert/status/1234567890'
      });
    });

    test('should search tweets with custom parameters', async () => {
      const mockResponse = {
        data: {
          data: [],
          includes: { users: [] }
        }
      };

      mockAxiosInstance.get.mockResolvedValue(mockResponse);

      const customKeywords = ['ethereum', 'DeFi'];
      const customCount = 50;

      await twitterClient.searchTweets(customKeywords, customCount);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/tweets/search/recent', {
        params: expect.objectContaining({
          query: '(ethereum OR DeFi) -is:retweet lang:en',
          max_results: 50
        })
      });
    });

    test('should handle empty search results', async () => {
      const mockResponse = {
        data: {
          data: null
        }
      };

      mockAxiosInstance.get.mockResolvedValue(mockResponse);

      const result = await twitterClient.searchTweets();

      expect(result).toEqual([]);
    });

    test('should handle API errors', async () => {
      const error = new Error('API Error');
      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(twitterClient.searchTweets()).rejects.toThrow('Twitter search failed: API Error');
    });
  });

  describe('getTweetDetails', () => {
    let twitterClient;

    beforeEach(() => {
      twitterClient = new TwitterClient(mockConfig, true, mockAxiosInstance); // Pass mock client
    });

    test('should retrieve tweet details successfully', async () => {
      const mockResponse = {
        data: {
          data: {
            id: '1234567890',
            text: 'Detailed tweet content about crypto',
            author_id: 'user123',
            created_at: '2025-08-14T09:00:00.000Z',
            public_metrics: {
              retweet_count: 100,
              like_count: 500,
              reply_count: 25,
              quote_count: 10
            },
            lang: 'en'
          },
          includes: {
            users: [
              {
                id: 'user123',
                username: 'cryptoanalyst',
                name: 'Crypto Analyst',
                verified: false,
                public_metrics: {
                  followers_count: 5000
                }
              }
            ]
          }
        }
      };

      mockAxiosInstance.get.mockResolvedValue(mockResponse);

      const result = await twitterClient.getTweetDetails('1234567890');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/tweets/1234567890', {
        params: {
          'tweet.fields': 'id,text,author_id,created_at,public_metrics,context_annotations,lang,possibly_sensitive,referenced_tweets',
          'user.fields': 'id,name,username,verified,public_metrics,description,profile_image_url',
          'expansions': 'author_id,referenced_tweets.id'
        }
      });

      expect(result).toMatchObject({
        id: '1234567890',
        text: 'Detailed tweet content about crypto',
        author: {
          username: 'cryptoanalyst',
          displayName: 'Crypto Analyst',
          verified: false,
          followerCount: 5000
        },
        metrics: {
          retweetCount: 100,
          likeCount: 500,
          replyCount: 25,
          quoteCount: 10
        }
      });
    });

    test('should handle tweet not found', async () => {
      const mockResponse = {
        data: {
          data: null
        }
      };

      mockAxiosInstance.get.mockResolvedValue(mockResponse);

      await expect(twitterClient.getTweetDetails('nonexistent')).rejects.toThrow('Tweet with ID nonexistent not found');
    });
  });

  describe('Rate Limiting', () => {
    let twitterClient;

    beforeEach(async () => {
      twitterClient = new TwitterClient(mockConfig, true, mockAxiosInstance); // Pass mock client
      // Initialize the client to set up rate limiting
      await twitterClient.initialize();
    });

    test('should track rate limit status correctly', () => {
      const status = twitterClient.getRateLimitStatus();

      expect(status).toMatchObject({
        requestsUsed: 0,
        requestsRemaining: 300,
        windowRemainingMs: expect.any(Number),
        resetTime: expect.any(Date)
      });
    });

    test('should update rate limit after request', async () => {
      const mockResponse = {
        data: {
          data: [],
          includes: { users: [] }
        }
      };

      mockAxiosInstance.get.mockResolvedValue(mockResponse);

      await twitterClient.searchTweets();

      const status = twitterClient.getRateLimitStatus();
      expect(status.requestsUsed).toBe(1);
      expect(status.requestsRemaining).toBe(299);
    });
  });

  describe('Tweet Quality Validation', () => {
    let twitterClient;

    beforeEach(async () => {
      twitterClient = new TwitterClient(mockConfig, true, mockAxiosInstance); // Pass mock client
      await twitterClient.initialize();
    });

    test('should validate high-quality tweet', () => {
      const tweet = {
        text: 'This is a comprehensive analysis of Bitcoin market trends and future predictions for cryptocurrency adoption.',
        metrics: {
          retweetCount: 50,
          likeCount: 200
        },
        possiblySensitive: false
      };

      expect(twitterClient.validateTweetQuality(tweet)).toBe(true);
    });

    test('should reject tweet with low retweet count', () => {
      const tweet = {
        text: 'Short crypto tweet with good content but low engagement.',
        metrics: {
          retweetCount: 5,
          likeCount: 20
        },
        possiblySensitive: false
      };

      expect(twitterClient.validateTweetQuality(tweet)).toBe(false);
    });

    test('should reject tweet with insufficient content', () => {
      const tweet = {
        text: 'Short tweet',
        metrics: {
          retweetCount: 50,
          likeCount: 200
        },
        possiblySensitive: false
      };

      expect(twitterClient.validateTweetQuality(tweet)).toBe(false);
    });

    test('should reject potentially sensitive content', () => {
      const tweet = {
        text: 'This is a comprehensive analysis of Bitcoin market trends and future predictions for cryptocurrency adoption.',
        metrics: {
          retweetCount: 50,
          likeCount: 200
        },
        possiblySensitive: true
      };

      expect(twitterClient.validateTweetQuality(tweet)).toBe(false);
    });

    test('should reject tweets that are mostly links and mentions', () => {
      const tweet = {
        text: '@user1 @user2 check this out https://example.com/link https://another-link.com',
        metrics: {
          retweetCount: 50,
          likeCount: 200
        },
        possiblySensitive: false
      };

      expect(twitterClient.validateTweetQuality(tweet)).toBe(false);
    });
  });

  describe('Data Processing', () => {
    let twitterClient;

    beforeEach(async () => {
      twitterClient = new TwitterClient(mockConfig, true, mockAxiosInstance); // Pass mock client
      await twitterClient.initialize();
    });

    test('should process tweet data correctly', () => {
      const apiResponse = {
        data: [
          {
            id: '1234567890',
            text: 'Test tweet content',
            author_id: 'user123',
            created_at: '2025-08-14T09:00:00.000Z',
            public_metrics: {
              retweet_count: 10,
              like_count: 50,
              reply_count: 5,
              quote_count: 2
            },
            lang: 'en',
            possibly_sensitive: false,
            context_annotations: []
          }
        ],
        includes: {
          users: [
            {
              id: 'user123',
              username: 'testuser',
              name: 'Test User',
              verified: true,
              public_metrics: {
                followers_count: 1000
              },
              description: 'Test user description',
              profile_image_url: 'https://example.com/avatar.jpg'
            }
          ]
        }
      };

      const result = twitterClient.processTweetData(apiResponse);

      expect(result).toHaveLength(1);
      expect(result[0]).toMatchObject({
        id: '1234567890',
        text: 'Test tweet content',
        author: {
          id: 'user123',
          username: 'testuser',
          displayName: 'Test User',
          verified: true,
          followerCount: 1000,
          description: 'Test user description',
          profileImageUrl: 'https://example.com/avatar.jpg'
        },
        metrics: {
          retweetCount: 10,
          likeCount: 50,
          replyCount: 5,
          quoteCount: 2
        },
        createdAt: '2025-08-14T09:00:00.000Z',
        url: 'https://twitter.com/testuser/status/1234567890',
        lang: 'en',
        possiblySensitive: false,
        contextAnnotations: expect.any(Array)
      });
    });

    test('should handle missing user data gracefully', () => {
      const apiResponse = {
        data: [
          {
            id: '1234567890',
            text: 'Test tweet content',
            author_id: 'user123',
            created_at: '2025-08-14T09:00:00.000Z',
            public_metrics: {
              retweet_count: 10,
              like_count: 50
            },
            lang: 'en'
          }
        ],
        includes: {
          users: []
        }
      };

      const result = twitterClient.processTweetData(apiResponse);

      expect(result[0].author).toMatchObject({
        id: 'user123',
        username: 'unknown',
        displayName: 'Unknown User',
        verified: false,
        followerCount: 0
      });
    });
  });

  describe('Error Handling', () => {
    let twitterClient;

    beforeEach(async () => {
      twitterClient = new TwitterClient(mockConfig, true, mockAxiosInstance); // Pass mock client
      await twitterClient.initialize();
    });

    test('should handle 401 unauthorized error', async () => {
      const error = {
        response: {
          status: 401,
          data: { error: 'Unauthorized' }
        }
      };

      await expect(twitterClient.handleApiError(error)).rejects.toThrow('Twitter API authentication failed');
    });

    test('should handle 403 forbidden error', async () => {
      const error = {
        response: {
          status: 403,
          data: { error: 'Forbidden' }
        }
      };

      await expect(twitterClient.handleApiError(error)).rejects.toThrow('Twitter API access forbidden');
    });

    test('should handle timeout errors', async () => {
      const error = {
        code: 'ECONNABORTED'
      };

      await expect(twitterClient.handleApiError(error)).rejects.toThrow('Twitter API request timeout');
    });

    test('should handle connection errors', async () => {
      const error = {
        code: 'ENOTFOUND'
      };

      await expect(twitterClient.handleApiError(error)).rejects.toThrow('Unable to connect to Twitter API');
    });
  });
});