import ArticleGenerator from '../src/generators/ArticleGenerator.js';

/**
 * Demo script showing ArticleGenerator functionality
 * This demonstrates how the ArticleGenerator converts tweet data into Hugo-compatible markdown articles
 */

async function demonstrateArticleGeneration() {
  console.log('🚀 ArticleGenerator Demo\n');

  // Sample tweet data (simulating data from TwitterClient)
  const sampleTweetData = {
    id: '1234567890123456789',
    text: 'Bitcoin just broke through $50,000! This is a major milestone for cryptocurrency adoption. The institutional interest is driving this bull run. #Bitcoin #BTC #crypto #bullish',
    author: {
      username: 'cryptoexpert',
      displayName: 'Crypto Expert',
      verified: true,
      followerCount: 125000
    },
    metrics: {
      retweetCount: 2500,
      likeCount: 8750,
      replyCount: 450,
      quoteCount: 320
    },
    createdAt: '2025-08-14T14:30:00Z',
    url: 'https://twitter.com/cryptoexpert/status/1234567890123456789'
  };

  // Sample translated content (simulating output from TranslationService)
  const translatedContent = '比特币刚刚突破了50,000美元！这是加密货币采用的一个重要里程碑。机构投资者的兴趣正在推动这轮牛市。';

  // Sample enhanced content (simulating output from TranslationService.enhanceContent)
  const enhancedContent = `比特币价格突破50,000美元大关，标志着加密货币市场进入新的发展阶段。这一历史性突破不仅反映了市场对比特币的强烈信心，更体现了机构投资者对数字资产的认可度不断提升。

## 市场分析

当前的价格突破主要受以下因素驱动：

1. **机构采用加速**：越来越多的传统金融机构开始将比特币纳入其投资组合
2. **监管环境改善**：全球多个国家对加密货币的监管政策趋于明朗
3. **技术发展成熟**：比特币网络的安全性和稳定性得到进一步验证
4. **通胀对冲需求**：在全球通胀压力下，比特币作为数字黄金的价值凸显

## 投资观点

从技术分析角度来看，比特币突破50,000美元阻力位后，下一个目标价位可能在55,000-60,000美元区间。然而，投资者仍需注意市场波动风险，建议采用分批建仓的策略。

**风险提示**：加密货币投资存在高风险，价格波动剧烈，投资者应根据自身风险承受能力谨慎投资，切勿盲目跟风。`;

  try {
    // Initialize ArticleGenerator with the actual template
    const generator = new ArticleGenerator('../md-template.md');
    
    console.log('📝 Generating article from tweet data...\n');
    
    // Generate the complete article
    const article = await generator.generateArticle(sampleTweetData, translatedContent, enhancedContent);
    
    console.log('✅ Article generated successfully!\n');
    console.log('📊 Article Details:');
    console.log(`   Title: ${article.frontMatter.title}`);
    console.log(`   Filename: ${article.filename}`);
    console.log(`   Tags: ${article.frontMatter.tags.join(', ')}`);
    console.log(`   Categories: ${article.frontMatter.categories.join(', ')}`);
    console.log(`   Content Length: ${article.content.length} characters\n`);
    
    console.log('📄 Generated Front Matter:');
    console.log('---');
    const frontMatterLines = article.fullContent.split('\n+++\n')[0] + '\n+++';
    console.log(frontMatterLines);
    console.log('---\n');
    
    console.log('📝 Content Preview (first 500 characters):');
    console.log('---');
    const contentPreview = article.content.substring(0, 500) + '...';
    console.log(contentPreview);
    console.log('---\n');
    
    console.log('🎯 Key Features Demonstrated:');
    console.log('   ✓ Chinese title generation with author and keywords');
    console.log('   ✓ Cryptocurrency tags in Chinese');
    console.log('   ✓ Hugo-compatible TOML front matter');
    console.log('   ✓ Enhanced content with market analysis');
    console.log('   ✓ Original tweet information preservation');
    console.log('   ✓ Author information and contact details');
    console.log('   ✓ SEO-optimized filename generation');
    
    return article;
    
  } catch (error) {
    console.error('❌ Error generating article:', error.message);
    throw error;
  }
}

// Run the demo if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  demonstrateArticleGeneration()
    .then(() => {
      console.log('\n🎉 Demo completed successfully!');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\n💥 Demo failed:', error.message);
      process.exit(1);
    });
}

export default demonstrateArticleGeneration;