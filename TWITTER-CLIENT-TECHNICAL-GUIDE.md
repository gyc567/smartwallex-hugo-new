# Twitter API Client Technical Implementation Guide

## Overview
This guide provides comprehensive instructions for implementing, testing, and validating the Twitter API client for cryptocurrency content automation based on the official Twitter API v2 specification.

---

## 1. API Specification Reference

### Official Endpoint
```
GET https://api.twitter.com/2/tweets/search/recent
```

### Authentication
```
Authorization: Bearer {YOUR_BEARER_TOKEN}
```

### Required Parameters
| Parameter | Type | Description | Limits |
|-----------|------|-------------|---------|
| `query` | string | Search query with operators | 512 chars |
| `max_results` | integer | Results per request | 10-100 |
| `tweet.fields` | string | Comma-separated tweet fields | optional |
| `user.fields` | string | Comma-separated user fields | optional |
| `expansions` | string | Related object expansions | optional |

### Search Operators
- `OR` - Logical OR
- `-` - Negation
- `lang:en` - Language filter
- `is:retweet` - Retweet filter
- `from:user` - Author filter
- `since:YYYY-MM-DD` - Date filter

---

## 2. Implementation Checklist

### ✅ Core Functionality
- [x] **searchTweets()** - Search for crypto-related tweets
- [x] **getTweetDetails()** - Get individual tweet details
- [x] **getRateLimitStatus()** - Check API limits
- [x] **validateTweetQuality()** - Content filtering

### 🔧 Required Enhancements

#### 2.1 Pagination Support
```javascript
async searchTweetsWithPagination(keywords, maxResults = 100) {
  const allTweets = [];
  let nextToken = null;
  
  do {
    const params = {
      query: keywords.join(' OR '),
      max_results: Math.min(maxResults, 100),
      tweet.fields: 'id,text,author_id,created_at,public_metrics',
      user.fields: 'id,name,username,verified,public_metrics',
      expansions: 'author_id',
      ...(nextToken && { next_token: nextToken })
    };
    
    const response = await this.client.get('/tweets/search/recent', { params });
    allTweets.push(...this.processTweetData(response.data));
    nextToken = response.data.meta?.next_token;
    
    // Respect maxResults limit
    if (allTweets.length >= maxResults) break;
    
  } while (nextToken && allTweets.length < maxResults);
  
  return allTweets.slice(0, maxResults);
}
```

#### 2.2 Rate Limit Header Parsing
```javascript
updateRateLimitFromHeaders(headers) {
  this.rateLimits = {
    remaining: parseInt(headers['x-rate-limit-remaining']) || 0,
    limit: parseInt(headers['x-rate-limit-limit']) || 180,
    reset: new Date(parseInt(headers['x-rate-limit-reset']) * 1000)
  };
}
```

---

## 3. Configuration Requirements

### Environment Variables
```bash
TWITTER_BEARER_TOKEN=your_bearer_token_here
```

### Configuration File (config/twitter.json)
```json
{
  "twitter": {
    "baseUrl": "https://api.twitter.com/2",
    "searchEndpoint": "/tweets/search/recent",
    "maxResults": 100,
    "rateLimits": {
      "searchRequests": 180,
      "windowMinutes": 15
    },
    "searchKeywords": [
      "cryptocurrency OR crypto",
      "blockchain OR bitcoin OR BTC",
      "ethereum OR ETH OR DeFi",
      "NFT OR Web3 OR altcoin"
    ]
  },
  "content": {
    "minRetweetCount": 5,
    "minCharacterCount": 50
  }
}
```

---

## 4. Test Suite Implementation

### 4.1 Unit Tests (Jest)
```javascript
// __tests__/TwitterClient.test.js
import { TwitterClient } from '../src/clients/TwitterClient.js';

describe('TwitterClient', () => {
  let client;
  let mockClient;
  
  beforeEach(() => {
    process.env.TWITTER_BEARER_TOKEN = 'test-token';
    mockClient = {
      get: jest.fn()
    };
    client = new TwitterClient(null, true, mockClient);
  });

  describe('searchTweets', () => {
    test('should construct correct query parameters', async () => {
      mockClient.get.mockResolvedValue({
        data: {
          data: [],
          includes: { users: [] }
        }
      });

      await client.searchTweets(['bitcoin', 'ethereum'], 50);
      
      expect(mockClient.get).toHaveBeenCalledWith(
        '/tweets/search/recent',
        expect.objectContaining({
          params: expect.objectContaining({
            query: 'bitcoin OR ethereum',
            max_results: 50
          })
        })
      );
    });

    test('should handle rate limit errors', async () => {
      mockClient.get.mockRejectedValue({
        response: {
          status: 429,
          headers: { 'x-rate-limit-reset': Math.floor(Date.now() / 1000) + 60 }
        }
      });

      await expect(client.searchTweets(['crypto'])).rejects.toThrow('Rate limit');
    });
  });

  describe('getTweetDetails', () => {
    test('should retrieve tweet with author info', async () => {
      const mockTweet = {
        data: {
          id: '123456',
          text: 'Bitcoin hits $50k! 🚀 #crypto',
          author_id: '789',
          public_metrics: { retweet_count: 100 }
        },
        includes: {
          users: [{
            id: '789',
            username: 'crypto_user',
            name: 'Crypto Expert',
            verified: true
          }]
        }
      };

      mockClient.get.mockResolvedValue({ data: mockTweet });
      
      const result = await client.getTweetDetails('123456');
      
      expect(result.id).toBe('123456');
      expect(result.author.username).toBe('crypto_user');
    });
  });
});
```

### 4.2 Integration Tests
```javascript
// __tests__/twitter.integration.test.js
describe('Twitter API Integration', () => {
  test('should search for crypto tweets successfully', async () => {
    const client = new TwitterClient();
    const tweets = await client.searchTweets(['bitcoin'], 10);
    
    expect(Array.isArray(tweets)).toBe(true);
    expect(tweets.length).toBeGreaterThan(0);
    expect(tweets[0]).toHaveProperty('id');
    expect(tweets[0]).toHaveProperty('text');
    expect(tweets[0]).toHaveProperty('author.username');
  });
});
```

---

## 5. Mock Data for Testing

### 5.1 Mock Response Structure
```javascript
const mockTweetResponse = {
  data: [
    {
      id: "123456789",
      text: "Bitcoin just hit $50,000! 🚀 #crypto",
      author_id: "111222333",
      created_at: "2024-01-15T12:00:00.000Z",
      public_metrics: {
        retweet_count: 150,
        reply_count: 25,
        like_count: 500,
        quote_count: 10
      },
      lang: "en"
    }
  ],
  includes: {
    users: [
      {
        id: "111222333",
        name: "Crypto Analyst",
        username: "crypto_analyst",
        verified: true,
        public_metrics: {
          followers_count: 50000
        }
      }
    ]
  },
  meta: {
    newest_id: "123456789",
    oldest_id: "123456789",
    result_count: 1,
    next_token: "b26v89c19zqg8o3..."
  }
};
```

---

## 6. Error Handling Matrix

| Error Code | Description | Client Response |
|------------|-------------|-----------------|
| 400 | Bad Request | Log query details, skip |
| 401 | Unauthorized | Throw auth error |
| 403 | Forbidden | Check API permissions |
| 429 | Rate Limited | Implement backoff |
| 500+ | Server Error | Retry with delay |

---

## 7. Performance Benchmarks

### Target Metrics
- **API Response Time**: < 2 seconds per request
- **Rate Limit Efficiency**: > 95% utilization
- **Memory Usage**: < 50MB for 100 tweets
- **Processing Speed**: 100 tweets/second

---

## 8. Deployment Checklist

### Pre-deployment
- [ ] Validate bearer token
- [ ] Test rate limit handling
- [ ] Verify search query syntax
- [ ] Test error scenarios
- [ ] Validate response processing

### Post-deployment
- [ ] Monitor API usage
- [ ] Check error rates
- [ ] Validate data quality
- [ ] Test rate limit recovery

---

## 9. Monitoring Setup

### Key Metrics to Track
- API requests per hour
- Rate limit utilization
- Error response codes
- Tweet processing time
- Data quality scores

### Alerting Thresholds
- Rate limit < 10% remaining
- Error rate > 5%
- Response time > 5 seconds
- Zero tweets returned > 3 consecutive calls

---

## 10. Quick Start Guide

### Installation
```bash
npm install axios
```

### Basic Usage
```javascript
import { TwitterClient } from './src/clients/TwitterClient.js';

const client = new TwitterClient();
const tweets = await client.searchTweets(['bitcoin', 'ethereum'], 50);
console.log(`Found ${tweets.length} tweets`);
```

### Testing
```bash
npm test
npm run test:integration
```

---

## 11. Validation Script

Create `validate-twitter-client.js`:
```javascript
import { TwitterClient } from './src/clients/TwitterClient.js';

async function validateClient() {
  const client = new TwitterClient();
  
  try {
    // Test basic search
    const tweets = await client.searchTweets(['bitcoin'], 5);
    console.log('✅ Search API working');
    
    // Test tweet details
    if (tweets.length > 0) {
      const details = await client.getTweetDetails(tweets[0].id);
      console.log('✅ Tweet details API working');
    }
    
    // Check rate limits
    const limits = client.getRateLimitStatus();
    console.log('✅ Rate limit tracking working');
    
  } catch (error) {
    console.error('❌ Validation failed:', error.message);
  }
}

validateClient();
```

---

## Summary
This implementation guide ensures your TwitterClient.js is fully compliant with Twitter API v2 specifications and provides comprehensive testing coverage for reliable cryptocurrency content automation.