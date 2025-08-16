import ContentProcessor from '../../src/processors/ContentProcessor.js';

describe('ContentProcessor', () => {
  let processor;

  beforeEach(() => {
    processor = new ContentProcessor();
  });

  describe('constructor', () => {
    test('should initialize with default configuration', () => {
      expect(processor.config.weights.retweets).toBe(0.6);
      expect(processor.config.weights.likes).toBe(0.25);
      expect(processor.config.weights.replies).toBe(0.15);
      expect(processor.config.quality.minLength).toBe(20);
    });

    test('should accept custom configuration', () => {
      const customConfig = {
        weights: { retweets: 0.5, likes: 0.3, replies: 0.2 },
        quality: { minLength: 30 }
      };
      const customProcessor = new ContentProcessor(customConfig);
      
      expect(customProcessor.config.weights.retweets).toBe(0.5);
      expect(customProcessor.config.weights.likes).toBe(0.3);
      expect(customProcessor.config.quality.minLength).toBe(30);
    });
  });

  describe('rankTweetsByEngagement', () => {
    test('should return empty array for empty input', () => {
      expect(processor.rankTweetsByEngagement([])).toEqual([]);
      expect(processor.rankTweetsByEngagement(null)).toEqual([]);
      expect(processor.rankTweetsByEngagement(undefined)).toEqual([]);
    });

    test('should rank tweets by engagement score correctly', () => {
      const tweets = [
        {
          id: '1',
          metrics: { retweetCount: 100, likeCount: 500, replyCount: 50 }
        },
        {
          id: '2',
          metrics: { retweetCount: 200, likeCount: 300, replyCount: 30 }
        },
        {
          id: '3',
          metrics: { retweetCount: 150, likeCount: 400, replyCount: 40 }
        }
      ];

      const ranked = processor.rankTweetsByEngagement(tweets);
      
      // Tweet 2 should be first (200*0.6 + 300*0.25 + 30*0.15 = 199.5)
      // Tweet 3 should be second (150*0.6 + 400*0.25 + 40*0.15 = 196)
      // Tweet 1 should be third (100*0.6 + 500*0.25 + 50*0.15 = 192.5)
      expect(ranked[0].id).toBe('2');
      expect(ranked[1].id).toBe('3');
      expect(ranked[2].id).toBe('1');
      expect(ranked[0].engagementScore).toBeCloseTo(199.5);
    });

    test('should handle missing metrics gracefully', () => {
      const tweets = [
        { id: '1', metrics: { retweetCount: 100 } },
        { id: '2' },
        { id: '3', metrics: { likeCount: 200 } }
      ];

      const ranked = processor.rankTweetsByEngagement(tweets);
      expect(ranked).toHaveLength(3);
      expect(ranked[0].engagementScore).toBeGreaterThan(0);
    });
  });

  describe('extractTweetContent', () => {
    test('should extract basic tweet content correctly', () => {
      const rawTweet = {
        id: '123456789',
        text: 'Bitcoin is reaching new heights! #BTC #crypto @elonmusk https://example.com',
        author: {
          username: 'cryptouser',
          displayName: 'Crypto User',
          verified: true,
          followerCount: 10000
        },
        metrics: {
          retweetCount: 150,
          likeCount: 500,
          replyCount: 25,
          quoteCount: 10
        },
        createdAt: '2025-08-14T09:00:00Z'
      };

      const extracted = processor.extractTweetContent(rawTweet);

      expect(extracted.id).toBe('123456789');
      expect(extracted.text).toBe('Bitcoin is reaching new heights! #BTC #crypto @elonmusk https://example.com');
      expect(extracted.author.username).toBe('cryptouser');
      expect(extracted.author.verified).toBe(true);
      expect(extracted.metrics.retweetCount).toBe(150);
      expect(extracted.hashtags).toEqual(['BTC', 'crypto']);
      expect(extracted.mentions).toEqual(['elonmusk']);
      expect(extracted.urls).toEqual(['https://example.com']);
    });

    test('should handle Twitter API v2 format', () => {
      const rawTweet = {
        id: '123456789',
        text: 'Ethereum update #ETH',
        author: {
          username: 'ethdev',
          name: 'Ethereum Developer'
        },
        public_metrics: {
          retweet_count: 75,
          like_count: 200,
          reply_count: 15,
          quote_count: 5
        },
        created_at: '2025-08-14T10:00:00Z'
      };

      const extracted = processor.extractTweetContent(rawTweet);

      expect(extracted.author.displayName).toBe('Ethereum Developer');
      expect(extracted.metrics.retweetCount).toBe(75);
      expect(extracted.metrics.likeCount).toBe(200);
      expect(extracted.createdAt).toBe('2025-08-14T10:00:00Z');
    });

    test('should throw error for invalid input', () => {
      expect(() => processor.extractTweetContent(null)).toThrow('Invalid tweet object provided');
      expect(() => processor.extractTweetContent('invalid')).toThrow('Invalid tweet object provided');
    });

    test('should handle missing fields gracefully', () => {
      const rawTweet = { id: '123' };
      const extracted = processor.extractTweetContent(rawTweet);

      expect(extracted.id).toBe('123');
      expect(extracted.text).toBe('');
      expect(extracted.author.username).toBe('');
      expect(extracted.metrics.retweetCount).toBe(0);
      expect(extracted.hashtags).toEqual([]);
    });
  });

  describe('validateContentQuality', () => {
    test('should validate good quality content', () => {
      const goodTweet = {
        text: 'Bitcoin price analysis shows strong bullish momentum with institutional adoption increasing.',
        metrics: { retweetCount: 50, likeCount: 200, replyCount: 25 }
      };

      const validation = processor.validateContentQuality(goodTweet);
      expect(validation.isValid).toBe(true);
      expect(validation.reasons).toEqual([]);
    });

    test('should reject tweets that are too short', () => {
      const shortTweet = {
        text: 'BTC up!',
        metrics: { retweetCount: 10, likeCount: 50, replyCount: 5 }
      };

      const validation = processor.validateContentQuality(shortTweet);
      expect(validation.isValid).toBe(false);
      expect(validation.reasons).toContain('Tweet too short (7 < 20)');
    });

    test('should reject tweets with low engagement', () => {
      const lowEngagementTweet = {
        text: 'This is a tweet about cryptocurrency that meets length requirements but has no engagement.',
        metrics: { retweetCount: 0, likeCount: 1, replyCount: 0 }
      };

      const validation = processor.validateContentQuality(lowEngagementTweet);
      expect(validation.isValid).toBe(false);
      expect(validation.reasons).toContain('Low engagement (1 < 5)');
    });

    test('should reject tweets with spam keywords', () => {
      const spamTweet = {
        text: 'Get free crypto now! Follow me for guaranteed profit and easy money opportunities!',
        metrics: { retweetCount: 10, likeCount: 50, replyCount: 5 }
      };

      const validation = processor.validateContentQuality(spamTweet);
      expect(validation.isValid).toBe(false);
      expect(validation.reasons.some(reason => reason.includes('spam keywords'))).toBe(true);
    });

    test('should reject tweets with too many hashtags', () => {
      const hashtagSpamTweet = {
        text: 'Bitcoin #BTC #crypto #blockchain #trading #investment #money #profit analysis today.',
        metrics: { retweetCount: 10, likeCount: 50, replyCount: 5 }
      };

      const validation = processor.validateContentQuality(hashtagSpamTweet);
      expect(validation.isValid).toBe(false);
      expect(validation.reasons.some(reason => reason.includes('Too many hashtags'))).toBe(true);
    });

    test('should reject tweets with too many mentions', () => {
      const mentionSpamTweet = {
        text: 'Hey @user1 @user2 @user3 @user4 check out this crypto opportunity!',
        metrics: { retweetCount: 10, likeCount: 50, replyCount: 5 }
      };

      const validation = processor.validateContentQuality(mentionSpamTweet);
      expect(validation.isValid).toBe(false);
      expect(validation.reasons.some(reason => reason.includes('Too many mentions'))).toBe(true);
    });

    test('should handle missing tweet text', () => {
      const invalidTweet = {
        metrics: { retweetCount: 10, likeCount: 50, replyCount: 5 }
      };

      const validation = processor.validateContentQuality(invalidTweet);
      expect(validation.isValid).toBe(false);
      expect(validation.reasons).toContain('Missing tweet text');
    });
  });

  describe('extractHashtags', () => {
    test('should extract hashtags correctly', () => {
      const text = 'Bitcoin and Ethereum are trending! #BTC #ETH #crypto #blockchain';
      const hashtags = processor.extractHashtags(text);
      expect(hashtags).toEqual(['BTC', 'ETH', 'crypto', 'blockchain']);
    });

    test('should return empty array for text without hashtags', () => {
      const text = 'This tweet has no hashtags';
      const hashtags = processor.extractHashtags(text);
      expect(hashtags).toEqual([]);
    });
  });

  describe('extractMentions', () => {
    test('should extract mentions correctly', () => {
      const text = 'Great analysis by @cryptoexpert and @blockchaindev about the market';
      const mentions = processor.extractMentions(text);
      expect(mentions).toEqual(['cryptoexpert', 'blockchaindev']);
    });

    test('should return empty array for text without mentions', () => {
      const text = 'This tweet has no mentions';
      const mentions = processor.extractMentions(text);
      expect(mentions).toEqual([]);
    });
  });

  describe('extractUrls', () => {
    test('should extract URLs correctly', () => {
      const text = 'Check out https://example.com and http://test.org for more info';
      const urls = processor.extractUrls(text);
      expect(urls).toEqual(['https://example.com', 'http://test.org']);
    });

    test('should return empty array for text without URLs', () => {
      const text = 'This tweet has no URLs';
      const urls = processor.extractUrls(text);
      expect(urls).toEqual([]);
    });
  });

  describe('processAndFilterTweets', () => {
    test('should process and filter tweets correctly', () => {
      const rawTweets = [
        {
          id: '1',
          text: 'Bitcoin analysis shows strong momentum with institutional adoption increasing significantly.',
          author: { username: 'analyst1', displayName: 'Crypto Analyst' },
          metrics: { retweetCount: 100, likeCount: 300, replyCount: 50 }
        },
        {
          id: '2',
          text: 'BTC up!', // Too short
          author: { username: 'user2', displayName: 'User 2' },
          metrics: { retweetCount: 5, likeCount: 10, replyCount: 2 }
        },
        {
          id: '3',
          text: 'Ethereum smart contracts are revolutionizing decentralized finance applications.',
          author: { username: 'ethdev', displayName: 'ETH Developer' },
          metrics: { retweetCount: 200, likeCount: 500, replyCount: 75 }
        }
      ];

      const processed = processor.processAndFilterTweets(rawTweets);
      
      // Should filter out the short tweet and rank by engagement
      expect(processed).toHaveLength(2);
      expect(processed[0].id).toBe('3'); // Higher engagement
      expect(processed[1].id).toBe('1');
    });

    test('should handle invalid input gracefully', () => {
      expect(processor.processAndFilterTweets(null)).toEqual([]);
      expect(processor.processAndFilterTweets(undefined)).toEqual([]);
      expect(processor.processAndFilterTweets('invalid')).toEqual([]);
    });

    test('should handle processing errors gracefully', () => {
      const rawTweets = [
        {
          id: '1',
          text: 'Valid tweet with good content and engagement metrics for testing.',
          author: { username: 'user1', displayName: 'User 1' },
          metrics: { retweetCount: 50, likeCount: 150, replyCount: 25 }
        },
        null, // Invalid tweet that will cause processing error
        {
          id: '3',
          text: 'Another valid tweet with sufficient length and engagement for processing.',
          author: { username: 'user3', displayName: 'User 3' },
          metrics: { retweetCount: 75, likeCount: 200, replyCount: 30 }
        }
      ];

      const processed = processor.processAndFilterTweets(rawTweets);
      expect(processed).toHaveLength(2); // Should skip the invalid tweet
      expect(processed[0].id).toBe('3'); // Higher engagement
      expect(processed[1].id).toBe('1');
    });
  });
});