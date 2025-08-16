/**
 * Content processing and ranking system for Twitter cryptocurrency content
 * Handles tweet analysis, ranking by engagement, and content quality validation
 */
class ContentProcessor {
  constructor(config = {}) {
    this.config = {
      // Weighted scoring algorithm configuration
      weights: {
        retweets: 0.6,    // 60% weight for retweets
        likes: 0.25,      // 25% weight for likes
        replies: 0.15     // 15% weight for replies
      },
      // Content quality thresholds
      quality: {
        minLength: 20,           // Minimum tweet length
        maxLength: 2000,         // Maximum tweet length
        minEngagement: 5,        // Minimum total engagement
        spamKeywords: [          // Common spam indicators
          'follow me', 'dm me', 'check bio', 'link in bio',
          'free crypto', 'guaranteed profit', 'pump and dump',
          'get rich quick', 'easy money', 'investment opportunity'
        ]
      },
      ...config
    };
  }

  /**
   * Rank tweets by engagement using weighted scoring algorithm
   * @param {Array} tweets - Array of tweet objects
   * @returns {Array} Sorted array of tweets by engagement score
   */
  rankTweetsByEngagement(tweets) {
    if (!Array.isArray(tweets) || tweets.length === 0) {
      return [];
    }

    // Calculate engagement score for each tweet
    const tweetsWithScores = tweets.map(tweet => {
      const metrics = tweet.metrics || {};
      const retweetCount = metrics.retweetCount || 0;
      const likeCount = metrics.likeCount || 0;
      const replyCount = metrics.replyCount || 0;

      // Calculate weighted engagement score
      const engagementScore =
        (retweetCount * this.config.weights.retweets) +
        (likeCount * this.config.weights.likes) +
        (replyCount * this.config.weights.replies);

      return {
        ...tweet,
        engagementScore
      };
    });

    // Sort by engagement score in descending order
    return tweetsWithScores.sort((a, b) => b.engagementScore - a.engagementScore);
  }

  /**
   * Extract and parse tweet content and metadata
   * @param {Object} tweet - Raw tweet object from Twitter API
   * @returns {Object} Processed tweet data with extracted content
   */
  extractTweetContent(tweet) {
    if (!tweet || typeof tweet !== 'object') {
      throw new Error('Invalid tweet object provided');
    }

    const extractedContent = {
      id: tweet.id || '',
      text: tweet.text || '',
      author: {
        username: tweet.author?.username || '',
        displayName: tweet.author?.displayName || tweet.author?.name || '',
        verified: tweet.author?.verified || false,
        followerCount: tweet.author?.followerCount || tweet.author?.public_metrics?.followers_count || 0
      },
      metrics: {
        retweetCount: tweet.metrics?.retweetCount || tweet.public_metrics?.retweet_count || 0,
        likeCount: tweet.metrics?.likeCount || tweet.public_metrics?.like_count || 0,
        replyCount: tweet.metrics?.replyCount || tweet.public_metrics?.reply_count || 0,
        quoteCount: tweet.metrics?.quoteCount || tweet.public_metrics?.quote_count || 0
      },
      createdAt: tweet.createdAt || tweet.created_at || new Date().toISOString(),
      url: tweet.url || `https://twitter.com/${tweet.author?.username}/status/${tweet.id}`,
      media: tweet.media || tweet.attachments?.media_keys || [],
      hashtags: this.extractHashtags(tweet.text || ''),
      mentions: this.extractMentions(tweet.text || ''),
      urls: this.extractUrls(tweet.text || '')
    };

    return extractedContent;
  }

  /**
   * Validate content quality and filter out spam
   * @param {Object} tweet - Tweet object to validate
   * @returns {Object} Validation result with isValid flag and reasons
   */
  validateContentQuality(tweet) {
    const validation = {
      isValid: true,
      reasons: []
    };

    if (!tweet || !tweet.text) {
      validation.isValid = false;
      validation.reasons.push('Missing tweet text');
      return validation;
    }

    const text = tweet.text.toLowerCase();
    const textLength = tweet.text.length;
    const totalEngagement = (tweet.metrics?.retweetCount || 0) +
      (tweet.metrics?.likeCount || 0) +
      (tweet.metrics?.replyCount || 0);

    // Check minimum length
    if (textLength < this.config.quality.minLength) {
      validation.isValid = false;
      validation.reasons.push(`Tweet too short (${textLength} < ${this.config.quality.minLength})`);
    }

    // Check maximum length
    if (textLength > this.config.quality.maxLength) {
      validation.isValid = false;
      validation.reasons.push(`Tweet too long (${textLength} > ${this.config.quality.maxLength})`);
    }

    // Check minimum engagement
    if (totalEngagement < this.config.quality.minEngagement) {
      validation.isValid = false;
      validation.reasons.push(`Low engagement (${totalEngagement} < ${this.config.quality.minEngagement})`);
    }

    // Check for spam keywords
    const spamKeywords = this.config.quality.spamKeywords.filter(keyword =>
      text.includes(keyword.toLowerCase())
    );

    if (spamKeywords.length > 0) {
      validation.isValid = false;
      validation.reasons.push(`Contains spam keywords: ${spamKeywords.join(', ')}`);
    }

    // Check for excessive hashtags (potential spam)
    const hashtagCount = (tweet.text.match(/#\w+/g) || []).length;
    if (hashtagCount > 5) {
      validation.isValid = false;
      validation.reasons.push(`Too many hashtags (${hashtagCount} > 5)`);
    }

    // Check for excessive mentions (potential spam)
    const mentionCount = (tweet.text.match(/@\w+/g) || []).length;
    if (mentionCount > 3) {
      validation.isValid = false;
      validation.reasons.push(`Too many mentions (${mentionCount} > 3)`);
    }

    return validation;
  }

  /**
   * Extract hashtags from tweet text
   * @param {string} text - Tweet text
   * @returns {Array} Array of hashtags without # symbol
   */
  extractHashtags(text) {
    const hashtagRegex = /#(\w+)/g;
    const hashtags = [];
    let match;

    while ((match = hashtagRegex.exec(text)) !== null) {
      hashtags.push(match[1]);
    }

    return hashtags;
  }

  /**
   * Extract mentions from tweet text
   * @param {string} text - Tweet text
   * @returns {Array} Array of mentions without @ symbol
   */
  extractMentions(text) {
    const mentionRegex = /@(\w+)/g;
    const mentions = [];
    let match;

    while ((match = mentionRegex.exec(text)) !== null) {
      mentions.push(match[1]);
    }

    return mentions;
  }

  /**
   * Extract URLs from tweet text
   * @param {string} text - Tweet text
   * @returns {Array} Array of URLs found in the text
   */
  extractUrls(text) {
    const urlRegex = /https?:\/\/[^\s]+/g;
    return text.match(urlRegex) || [];
  }

  /**
   * Process and filter tweets for quality content
   * @param {Array} tweets - Array of raw tweet objects
   * @returns {Array} Array of processed and validated tweets
   */
  processAndFilterTweets(tweets) {
    if (!Array.isArray(tweets)) {
      return [];
    }

    const processedTweets = [];

    for (const tweet of tweets) {
      try {
        // Extract content
        const extractedTweet = this.extractTweetContent(tweet);

        // Validate quality
        const validation = this.validateContentQuality(extractedTweet);

        if (validation.isValid) {
          processedTweets.push(extractedTweet);
        }
      } catch (error) {
        console.warn(`Failed to process tweet ${tweet?.id || 'unknown'}:`, error.message);
      }
    }

    // Rank by engagement
    return this.rankTweetsByEngagement(processedTweets);
  }
}

export default ContentProcessor;