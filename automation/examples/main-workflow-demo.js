import { TwitterCryptoAutomation } from '../src/index.js';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

/**
 * Demo script for the main Twitter Crypto Content Automation workflow
 * This demonstrates the complete end-to-end process
 */
async function runWorkflowDemo() {
  console.log('🚀 Twitter Crypto Content Automation Demo');
  console.log('==========================================\n');

  const automation = new TwitterCryptoAutomation();

  try {
    // Step 1: Initialize the automation system
    console.log('📋 Step 1: Initializing automation system...');
    await automation.initialize();
    console.log('✅ Initialization completed successfully\n');

    // Step 2: Execute the complete workflow
    console.log('🔄 Step 2: Executing complete workflow...');
    console.log('This will:');
    console.log('  - Search for trending crypto tweets');
    console.log('  - Process and rank by engagement');
    console.log('  - Translate to Chinese');
    console.log('  - Generate comprehensive articles');
    console.log('  - Check for duplicates');
    console.log('  - Write articles to files');
    console.log('  - Build Hugo site');
    console.log('  - Perform cleanup\n');

    const report = await automation.executeWorkflow();

    // Step 3: Display results
    console.log('📊 Step 3: Workflow Results');
    console.log('============================');
    console.log(`Execution Time: ${Math.round(report.executionTime / 1000)}s`);
    console.log(`Start Time: ${report.startTime.toISOString()}`);
    console.log(`End Time: ${report.endTime.toISOString()}`);
    console.log('\n📈 Statistics:');
    console.log(`  Tweets Found: ${report.statistics.tweetsFound}`);
    console.log(`  Tweets Processed: ${report.statistics.tweetsProcessed}`);
    console.log(`  Articles Generated: ${report.statistics.articlesGenerated}`);
    console.log(`  Duplicates Skipped: ${report.statistics.duplicatesSkipped}`);
    console.log(`  Errors Encountered: ${report.statistics.errorsEncountered}`);

    if (report.errors.length > 0) {
      console.log('\n⚠️  Errors:');
      report.errors.forEach((error, index) => {
        console.log(`  ${index + 1}. [${error.step}] ${error.error}`);
        if (error.tweetId) {
          console.log(`     Tweet ID: ${error.tweetId}`);
        }
      });
    }

    if (report.success) {
      console.log('\n🎉 Workflow completed successfully!');
      console.log('Generated articles have been saved to content/posts/');
      console.log('Hugo site has been built to public/');
    } else {
      console.log('\n⚠️  Workflow completed with issues.');
      console.log('Check the errors above for details.');
    }

  } catch (error) {
    console.error('\n❌ Demo failed with error:', error.message);
    console.error('Stack trace:', error.stack);
    
    // Provide troubleshooting tips
    console.log('\n🔧 Troubleshooting Tips:');
    
    if (error.message.includes('TWITTER_BEARER_TOKEN')) {
      console.log('  - Set your Twitter Bearer Token in environment variables');
      console.log('  - Copy .env.example to .env and fill in your API keys');
    }
    
    if (error.message.includes('Hugo not found')) {
      console.log('  - Install Hugo: https://gohugo.io/installation/');
      console.log('  - Make sure Hugo is in your PATH');
    }
    
    if (error.message.includes('rate limit')) {
      console.log('  - Twitter API rate limit reached');
      console.log('  - Wait for the rate limit window to reset');
      console.log('  - Consider reducing the number of search results');
    }
    
    if (error.message.includes('config')) {
      console.log('  - Check your configuration files in config/');
      console.log('  - Ensure all required fields are present');
    }
  }
}

/**
 * Demo with mock data for testing without API calls
 */
async function runMockDemo() {
  console.log('🧪 Mock Demo Mode (No API Calls)');
  console.log('==================================\n');

  // This would demonstrate the workflow with mock data
  // Useful for testing the integration without hitting real APIs
  
  console.log('Mock demo would show:');
  console.log('  ✅ Component initialization');
  console.log('  ✅ Mock tweet processing');
  console.log('  ✅ Translation simulation');
  console.log('  ✅ Article generation');
  console.log('  ✅ File writing simulation');
  console.log('  ✅ Build process simulation');
  console.log('\nThis mode is useful for:');
  console.log('  - Testing the workflow logic');
  console.log('  - Debugging without API limits');
  console.log('  - Development and CI/CD');
}

/**
 * Interactive demo that lets users choose options
 */
async function runInteractiveDemo() {
  console.log('🎮 Interactive Demo Mode');
  console.log('========================\n');
  
  console.log('Available demo options:');
  console.log('1. Full workflow with real APIs');
  console.log('2. Mock workflow (no API calls)');
  console.log('3. Component testing');
  console.log('4. Configuration validation');
  
  // In a real interactive demo, you would use readline or inquirer
  // to get user input and run different demo scenarios
  
  const demoType = process.env.DEMO_TYPE || '1';
  
  switch (demoType) {
    case '1':
      await runWorkflowDemo();
      break;
    case '2':
      await runMockDemo();
      break;
    case '3':
      await runComponentTestingDemo();
      break;
    case '4':
      await runConfigValidationDemo();
      break;
    default:
      console.log('Invalid demo type. Running full workflow...');
      await runWorkflowDemo();
  }
}

/**
 * Demo individual components
 */
async function runComponentTestingDemo() {
  console.log('🔧 Component Testing Demo');
  console.log('=========================\n');

  const automation = new TwitterCryptoAutomation();
  
  try {
    await automation.initialize();
    
    console.log('Testing individual components:');
    
    // Test Twitter Client
    console.log('\n📱 Testing Twitter Client...');
    try {
      const rateLimitStatus = automation.components.twitterClient.getRateLimitStatus();
      console.log('  ✅ Rate limit status:', rateLimitStatus);
    } catch (error) {
      console.log('  ❌ Twitter Client error:', error.message);
    }
    
    // Test Content Processor
    console.log('\n⚙️  Testing Content Processor...');
    const mockTweets = [
      {
        id: '123',
        text: 'Bitcoin is going to the moon! #BTC',
        metrics: { retweetCount: 100, likeCount: 500, replyCount: 25 }
      }
    ];
    const processed = automation.components.contentProcessor.processAndFilterTweets(mockTweets);
    console.log(`  ✅ Processed ${processed.length} tweets`);
    
    // Test Translation Service
    console.log('\n🌐 Testing Translation Service...');
    try {
      const translated = await automation.components.translationService.translateText('Hello Bitcoin!');
      console.log('  ✅ Translation result:', translated);
    } catch (error) {
      console.log('  ❌ Translation error:', error.message);
    }
    
    // Test Duplicate Checker
    console.log('\n🔍 Testing Duplicate Checker...');
    try {
      const duplicateCheck = await automation.components.duplicateChecker.checkDuplicate(
        'test123',
        'Test content'
      );
      console.log('  ✅ Duplicate check result:', duplicateCheck.isDuplicate ? 'Duplicate' : 'Unique');
    } catch (error) {
      console.log('  ❌ Duplicate checker error:', error.message);
    }
    
    // Test Hugo Builder
    console.log('\n🏗️  Testing Hugo Builder...');
    try {
      const isValid = await automation.components.hugoBuilder.validateSiteConfiguration();
      console.log('  ✅ Site configuration valid:', isValid);
    } catch (error) {
      console.log('  ❌ Hugo Builder error:', error.message);
    }
    
    console.log('\n✅ Component testing completed');
    
  } catch (error) {
    console.error('❌ Component testing failed:', error.message);
  }
}

/**
 * Demo configuration validation
 */
async function runConfigValidationDemo() {
  console.log('⚙️  Configuration Validation Demo');
  console.log('==================================\n');

  try {
    const automation = new TwitterCryptoAutomation();
    await automation.initialize();
    
    console.log('✅ Configuration loaded successfully');
    console.log('Configuration summary:');
    console.log(`  Twitter API configured: ${!!automation.config.twitter?.bearerToken}`);
    console.log(`  Search keywords: ${automation.config.twitter?.searchKeywords?.length || 0}`);
    console.log(`  Max results: ${automation.config.twitter?.maxResults || 'default'}`);
    console.log(`  Content directory: ${automation.config.hugo?.contentDir || 'default'}`);
    console.log(`  Template path: ${automation.config.template?.path || 'default'}`);
    
    // Validate required environment variables
    console.log('\nEnvironment variables:');
    console.log(`  TWITTER_BEARER_TOKEN: ${process.env.TWITTER_BEARER_TOKEN ? '✅ Set' : '❌ Missing'}`);
    console.log(`  NODE_ENV: ${process.env.NODE_ENV || 'development'}`);
    console.log(`  LOG_LEVEL: ${process.env.LOG_LEVEL || 'info'}`);
    
  } catch (error) {
    console.error('❌ Configuration validation failed:', error.message);
    
    console.log('\n🔧 Configuration troubleshooting:');
    console.log('  1. Check config files in config/ directory');
    console.log('  2. Ensure environment variables are set');
    console.log('  3. Verify file permissions');
    console.log('  4. Check JSON syntax in config files');
  }
}

// Main execution
async function main() {
  const args = process.argv.slice(2);
  const demoMode = args[0] || 'interactive';
  
  console.log(`Starting demo in ${demoMode} mode...\n`);
  
  switch (demoMode) {
    case 'full':
      await runWorkflowDemo();
      break;
    case 'mock':
      await runMockDemo();
      break;
    case 'components':
      await runComponentTestingDemo();
      break;
    case 'config':
      await runConfigValidationDemo();
      break;
    case 'interactive':
    default:
      await runInteractiveDemo();
      break;
  }
}

// Run the demo if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(error => {
    console.error('Demo execution failed:', error);
    process.exit(1);
  });
}

export {
  runWorkflowDemo,
  runMockDemo,
  runInteractiveDemo,
  runComponentTestingDemo,
  runConfigValidationDemo
};