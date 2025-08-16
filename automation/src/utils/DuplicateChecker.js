import crypto from 'crypto';
import { promises as fs } from 'fs';
import path from 'path';

/**
 * DuplicateChecker class for preventing duplicate content publication
 * Implements content fingerprinting and persistent storage for processed tweets
 */
class DuplicateChecker {
  constructor(dataFilePath = path.join(process.cwd(), 'data/processed-tweets.json')) {
    this.dataFilePath = dataFilePath;
    this.processedData = null;
    this.RETENTION_DAYS = 30;
  }

  /**
   * Load processed tweets data from persistent storage
   * @returns {Promise<Object>} Processed tweets data
   */
  async loadProcessedData() {
    try {
      const data = await fs.readFile(this.dataFilePath, 'utf8');
      this.processedData = JSON.parse(data);
      
      // Clean up old entries (older than 30 days)
      await this.cleanupOldEntries();
      
      return this.processedData;
    } catch (error) {
      if (error.code === 'ENOENT') {
        // File doesn't exist, create default structure
        this.processedData = {
          processedTweets: [],
          lastUpdated: null,
          version: "1.0.0"
        };
        await this.saveProcessedData();
        return this.processedData;
      }
      throw new Error(`Failed to load processed data: ${error.message}`);
    }
  }

  /**
   * Save processed tweets data to persistent storage
   * @returns {Promise<void>}
   */
  async saveProcessedData() {
    try {
      this.processedData.lastUpdated = new Date().toISOString();
      await fs.writeFile(this.dataFilePath, JSON.stringify(this.processedData, null, 2));
    } catch (error) {
      throw new Error(`Failed to save processed data: ${error.message}`);
    }
  }

  /**
   * Generate SHA-256 hash for content fingerprinting
   * @param {string} content - Tweet content to hash
   * @returns {string} SHA-256 hash of normalized content
   */
  generateContentHash(content) {
    if (!content || typeof content !== 'string') {
      throw new Error('Content must be a non-empty string');
    }

    // Normalize content: remove extra whitespace, convert to lowercase, remove URLs
    const normalizedContent = content
      .toLowerCase()
      .replace(/https?:\/\/[^\s]+/g, '') // Remove URLs
      .replace(/\s+/g, ' ') // Normalize whitespace
      .trim();

    return crypto.createHash('sha256').update(normalizedContent, 'utf8').digest('hex');
  }

  /**
   * Check if tweet is duplicate based on ID and content hash
   * @param {string} tweetId - Twitter tweet ID
   * @param {string} content - Tweet content
   * @param {string} tweetUrl - Tweet URL (optional)
   * @returns {Promise<Object>} Duplicate check result
   */
  async checkDuplicate(tweetId, content, tweetUrl = null) {
    if (!tweetId || !content) {
      throw new Error('Tweet ID and content are required');
    }

    // Ensure data is loaded
    if (!this.processedData) {
      await this.loadProcessedData();
    }

    const contentHash = this.generateContentHash(content);
    const processedTweets = this.processedData.processedTweets;

    // Check for exact tweet ID match
    const tweetIdMatch = processedTweets.find(tweet => tweet.tweetId === tweetId);
    if (tweetIdMatch) {
      return {
        isDuplicate: true,
        reason: 'tweet_id_exists',
        matchedEntry: tweetIdMatch,
        contentHash
      };
    }

    // Check for content hash match
    const contentHashMatch = processedTweets.find(tweet => tweet.contentHash === contentHash);
    if (contentHashMatch) {
      return {
        isDuplicate: true,
        reason: 'content_hash_match',
        matchedEntry: contentHashMatch,
        contentHash
      };
    }

    // Check for URL match if provided
    if (tweetUrl) {
      const urlMatch = processedTweets.find(tweet => tweet.tweetUrl === tweetUrl);
      if (urlMatch) {
        return {
          isDuplicate: true,
          reason: 'url_match',
          matchedEntry: urlMatch,
          contentHash
        };
      }
    }

    // Perform semantic similarity check (simplified version)
    const similarityMatch = await this.checkSemanticSimilarity(content, contentHash);
    if (similarityMatch) {
      return {
        isDuplicate: true,
        reason: 'semantic_similarity',
        matchedEntry: similarityMatch,
        contentHash
      };
    }

    return {
      isDuplicate: false,
      reason: 'unique_content',
      contentHash
    };
  }

  /**
   * Check for semantic similarity with existing content
   * @param {string} content - Tweet content to check
   * @param {string} contentHash - Content hash
   * @returns {Promise<Object|null>} Matching entry if similar content found
   */
  async checkSemanticSimilarity(content, contentHash) {
    const processedTweets = this.processedData.processedTweets;
    const SIMILARITY_THRESHOLD = 0.85;

    // Simple keyword-based similarity check
    const contentWords = this.extractKeywords(content);
    
    for (const processedTweet of processedTweets) {
      if (processedTweet.keywords) {
        const similarity = this.calculateSimilarity(contentWords, processedTweet.keywords);
        if (similarity > SIMILARITY_THRESHOLD) {
          return processedTweet;
        }
      }
    }

    return null;
  }

  /**
   * Extract keywords from content for similarity comparison
   * @param {string} content - Content to extract keywords from
   * @returns {Array<string>} Array of keywords
   */
  extractKeywords(content) {
    // Remove common words and extract meaningful terms
    const commonWords = new Set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should']);
    
    return content
      .toLowerCase()
      .replace(/[^\w\s]/g, '') // Remove punctuation
      .split(/\s+/)
      .filter(word => word.length > 2 && !commonWords.has(word))
      .slice(0, 20); // Limit to top 20 keywords
  }

  /**
   * Calculate similarity between two keyword arrays
   * @param {Array<string>} keywords1 - First set of keywords
   * @param {Array<string>} keywords2 - Second set of keywords
   * @returns {number} Similarity score (0-1)
   */
  calculateSimilarity(keywords1, keywords2) {
    if (!keywords1.length || !keywords2.length) return 0;

    const set1 = new Set(keywords1);
    const set2 = new Set(keywords2);
    const intersection = new Set([...set1].filter(x => set2.has(x)));
    const union = new Set([...set1, ...set2]);

    return intersection.size / union.size; // Jaccard similarity
  }

  /**
   * Update processed list with new tweet information
   * @param {string} tweetId - Twitter tweet ID
   * @param {string} contentHash - Content hash
   * @param {string} filename - Generated filename
   * @param {Object} additionalData - Additional tweet data
   * @returns {Promise<void>}
   */
  async updateProcessedList(tweetId, contentHash, filename, additionalData = {}) {
    if (!tweetId || !contentHash || !filename) {
      throw new Error('Tweet ID, content hash, and filename are required');
    }

    // Ensure data is loaded
    if (!this.processedData) {
      await this.loadProcessedData();
    }

    const processedEntry = {
      tweetId,
      contentHash,
      processedDate: new Date().toISOString(),
      filename,
      ...additionalData
    };

    // Add keywords for similarity checking
    if (additionalData.content) {
      processedEntry.keywords = this.extractKeywords(additionalData.content);
    }

    this.processedData.processedTweets.push(processedEntry);
    await this.saveProcessedData();
  }

  /**
   * Clean up entries older than retention period
   * @returns {Promise<void>}
   */
  async cleanupOldEntries() {
    if (!this.processedData || !this.processedData.processedTweets) {
      return;
    }

    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - this.RETENTION_DAYS);

    const initialCount = this.processedData.processedTweets.length;
    this.processedData.processedTweets = this.processedData.processedTweets.filter(tweet => {
      const processedDate = new Date(tweet.processedDate);
      return processedDate > cutoffDate;
    });

    const removedCount = initialCount - this.processedData.processedTweets.length;
    if (removedCount > 0) {
      console.log(`Cleaned up ${removedCount} old processed tweet entries`);
      await this.saveProcessedData();
    }
  }

  /**
   * Get statistics about processed tweets
   * @returns {Promise<Object>} Statistics object
   */
  async getStatistics() {
    if (!this.processedData) {
      await this.loadProcessedData();
    }

    const now = new Date();
    const last24Hours = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    const last7Days = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

    const recentTweets24h = this.processedData.processedTweets.filter(tweet => 
      new Date(tweet.processedDate) > last24Hours
    );

    const recentTweets7d = this.processedData.processedTweets.filter(tweet => 
      new Date(tweet.processedDate) > last7Days
    );

    return {
      totalProcessed: this.processedData.processedTweets.length,
      processedLast24Hours: recentTweets24h.length,
      processedLast7Days: recentTweets7d.length,
      lastUpdated: this.processedData.lastUpdated,
      oldestEntry: this.processedData.processedTweets.length > 0 
        ? this.processedData.processedTweets[0].processedDate 
        : null
    };
  }

  /**
   * Check if a tweet is a retweet and prioritize original content
   * @param {Object} tweetData - Tweet data object
   * @returns {boolean} True if tweet is original content
   */
  isOriginalContent(tweetData) {
    // Check if tweet starts with "RT @" indicating a retweet
    if (tweetData.text && tweetData.text.startsWith('RT @')) {
      return false;
    }

    // Check if tweet has retweeted_status field (Twitter API v1.1)
    if (tweetData.retweeted_status) {
      return false;
    }

    // Check if tweet has referenced_tweets with type "retweeted" (Twitter API v2)
    if (tweetData.referenced_tweets) {
      const hasRetweet = tweetData.referenced_tweets.some(ref => ref.type === 'retweeted');
      if (hasRetweet) {
        return false;
      }
    }

    return true;
  }
}

export default DuplicateChecker;