import DuplicateChecker from '../src/utils/DuplicateChecker.js';

/**
 * Demo script showing how to use the DuplicateChecker class
 */
async function demonstrateDuplicateChecker() {
  console.log('🔍 DuplicateChecker Demo\n');

  // Create a new DuplicateChecker instance
  const checker = new DuplicateChecker();

  try {
    // Example tweet data
    const tweet1 = {
      id: '1234567890',
      text: 'Bitcoin is reaching new all-time highs! The cryptocurrency market is booming. #crypto #bitcoin',
      url: 'https://twitter.com/user/status/1234567890'
    };

    const tweet2 = {
      id: '1234567891',
      text: 'Ethereum smart contracts are revolutionizing DeFi protocols across the blockchain ecosystem.',
      url: 'https://twitter.com/user/status/1234567891'
    };

    const tweet3 = {
      id: '1234567892',
      text: 'Bitcoin is reaching new all-time highs! The cryptocurrency market is booming. #crypto #bitcoin', // Duplicate content
      url: 'https://twitter.com/user/status/1234567892'
    };

    console.log('1. Testing content hash generation:');
    const hash1 = checker.generateContentHash(tweet1.text);
    const hash2 = checker.generateContentHash(tweet2.text);
    const hash3 = checker.generateContentHash(tweet3.text);
    
    console.log(`Tweet 1 hash: ${hash1.substring(0, 16)}...`);
    console.log(`Tweet 2 hash: ${hash2.substring(0, 16)}...`);
    console.log(`Tweet 3 hash: ${hash3.substring(0, 16)}...`);
    console.log(`Tweet 1 and 3 have same hash: ${hash1 === hash3}\n`);

    console.log('2. Testing duplicate detection:');
    
    // Check first tweet (should be unique)
    let result = await checker.checkDuplicate(tweet1.id, tweet1.text, tweet1.url);
    console.log(`Tweet 1 duplicate check: ${result.isDuplicate ? 'DUPLICATE' : 'UNIQUE'} (${result.reason})`);

    // Add first tweet to processed list
    if (!result.isDuplicate) {
      await checker.updateProcessedList(
        tweet1.id, 
        result.contentHash, 
        'bitcoin-ath-analysis-20250814.md',
        { content: tweet1.text, tweetUrl: tweet1.url }
      );
      console.log('✅ Tweet 1 added to processed list');
    }

    // Check second tweet (should be unique)
    result = await checker.checkDuplicate(tweet2.id, tweet2.text, tweet2.url);
    console.log(`Tweet 2 duplicate check: ${result.isDuplicate ? 'DUPLICATE' : 'UNIQUE'} (${result.reason})`);

    // Add second tweet to processed list
    if (!result.isDuplicate) {
      await checker.updateProcessedList(
        tweet2.id, 
        result.contentHash, 
        'ethereum-defi-revolution-20250814.md',
        { content: tweet2.text, tweetUrl: tweet2.url }
      );
      console.log('✅ Tweet 2 added to processed list');
    }

    // Check third tweet (should be duplicate)
    result = await checker.checkDuplicate(tweet3.id, tweet3.text, tweet3.url);
    console.log(`Tweet 3 duplicate check: ${result.isDuplicate ? 'DUPLICATE' : 'UNIQUE'} (${result.reason})`);
    
    if (result.isDuplicate) {
      console.log(`🚫 Tweet 3 rejected - matches: ${result.matchedEntry.filename}`);
    }

    console.log('\n3. Testing original content detection:');
    const originalTweet = { text: 'This is original Bitcoin analysis' };
    const retweet = { text: 'RT @user: This is original Bitcoin analysis' };
    const quoteTweet = { 
      text: 'Great analysis!', 
      referenced_tweets: [{ type: 'quoted', id: '123' }] 
    };

    console.log(`Original tweet: ${checker.isOriginalContent(originalTweet) ? 'ORIGINAL' : 'RETWEET'}`);
    console.log(`Retweet: ${checker.isOriginalContent(retweet) ? 'ORIGINAL' : 'RETWEET'}`);
    console.log(`Quote tweet: ${checker.isOriginalContent(quoteTweet) ? 'ORIGINAL' : 'RETWEET'}`);

    console.log('\n4. Getting statistics:');
    const stats = await checker.getStatistics();
    console.log(`Total processed: ${stats.totalProcessed}`);
    console.log(`Processed last 24h: ${stats.processedLast24Hours}`);
    console.log(`Last updated: ${stats.lastUpdated}`);

    console.log('\n5. Testing keyword extraction and similarity:');
    const keywords1 = checker.extractKeywords(tweet1.text);
    const keywords2 = checker.extractKeywords(tweet2.text);
    const similarity = checker.calculateSimilarity(keywords1, keywords2);
    
    console.log(`Tweet 1 keywords: [${keywords1.slice(0, 5).join(', ')}...]`);
    console.log(`Tweet 2 keywords: [${keywords2.slice(0, 5).join(', ')}...]`);
    console.log(`Similarity score: ${(similarity * 100).toFixed(1)}%`);

    console.log('\n✅ Demo completed successfully!');

  } catch (error) {
    console.error('❌ Demo failed:', error.message);
  }
}

// Run the demo
demonstrateDuplicateChecker();