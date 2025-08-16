# Troubleshooting Guide

This guide covers common issues and their solutions for the Twitter Crypto Content Automation system.

## Table of Contents

- [Configuration Issues](#configuration-issues)
- [API Problems](#api-problems)
- [GitHub Actions Failures](#github-actions-failures)
- [Content Generation Issues](#content-generation-issues)
- [Hugo Build Problems](#hugo-build-problems)
- [Performance Issues](#performance-issues)
- [Debugging Tools](#debugging-tools)

## Configuration Issues

### ❌ "Configuration validation failed"

**Symptoms**: Error during startup with validation messages

**Causes & Solutions**:

1. **Missing required environment variables**
   ```bash
   # Check which secrets are missing
   node .github/scripts/setup-secrets.js validate
   ```
   
2. **Invalid configuration format**
   ```bash
   # Validate JSON syntax
   node -e "console.log(JSON.parse(require('fs').readFileSync('automation/config/default.json')))"
   ```

3. **Incorrect GitHub repository format**
   - Must be in format: `username/repository`
   - Check `GITHUB_REPOSITORY` secret

### ❌ "Environment variable X is empty"

**Solution**: Update GitHub Secrets
1. Go to repository Settings > Secrets and variables > Actions
2. Edit the empty secret
3. Ensure no trailing spaces or newlines

### ❌ "Could not load config file"

**Causes**:
- Missing configuration file
- Invalid JSON syntax
- File permissions

**Solution**:
```bash
# Check file exists and is valid JSON
ls -la automation/config/
node -c automation/config/default.json
```

## API Problems

### ❌ Twitter API Authentication Failed

**Error**: `401 Unauthorized` or `403 Forbidden`

**Solutions**:

1. **Check Bearer Token**
   ```bash
   # Test token manually
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        "https://api.twitter.com/2/tweets/search/recent?query=crypto&max_results=10"
   ```

2. **Verify API Access Level**
   - Ensure you have Essential access or higher
   - Check if your app has search permissions

3. **Token Format Issues**
   - Bearer tokens should be ~100+ characters
   - No spaces or special characters
   - Check for copy-paste errors

### ❌ Rate Limit Exceeded

**Error**: `429 Too Many Requests`

**Solutions**:

1. **Reduce API calls**
   - Lower `maxResults` in configuration
   - Increase delay between requests
   - Reduce `topTweetsCount`

2. **Check rate limit status**
   ```javascript
   // Add to your script for debugging
   console.log('Rate limit headers:', response.headers);
   ```

3. **Implement exponential backoff** (already included)

### ❌ No Tweets Found

**Symptoms**: "No qualifying tweets found" in logs

**Solutions**:

1. **Adjust search criteria**
   ```json
   {
     "content": {
       "minRetweetCount": 5,  // Lower threshold
       "minCharacterCount": 30  // Lower threshold
     }
   }
   ```

2. **Update keywords**
   - Add trending crypto terms
   - Use broader search terms
   - Check keyword spelling

3. **Time-based issues**
   - Crypto content varies by time
   - Consider different execution times

## GitHub Actions Failures

### ❌ Workflow Permission Denied

**Error**: `Permission denied` or `403` during git operations

**Solutions**:

1. **Check GitHub Token Permissions**
   - Token needs `repo` scope
   - Regenerate token if needed

2. **Repository Settings**
   - Go to Settings > Actions > General
   - Ensure "Read and write permissions" is enabled

3. **Branch Protection**
   - Check if main branch has protection rules
   - Add bypass for automation if needed

### ❌ Hugo Build Failed

**Error**: Hugo command fails during workflow

**Solutions**:

1. **Check Hugo Version**
   ```yaml
   # In workflow file, specify version
   - name: Setup Hugo
     uses: peaceiris/actions-hugo@v2
     with:
       hugo-version: '0.119.0'
       extended: true
   ```

2. **Template Issues**
   - Validate `md-template.md` syntax
   - Check front matter format
   - Ensure all template variables are defined

3. **Content Path Issues**
   ```bash
   # Verify paths in configuration
   ls -la content/posts/
   ```

### ❌ Workflow Timeout

**Symptoms**: Workflow stops after 6 hours (GitHub limit)

**Solutions**:

1. **Optimize API calls**
   - Reduce `maxResults`
   - Implement better caching
   - Parallel processing where possible

2. **Split workflow**
   - Separate content generation and building
   - Use workflow artifacts for data passing

## Content Generation Issues

### ❌ Translation Failures

**Error**: Translation service errors or poor quality

**Solutions**:

1. **Fallback Translation**
   ```json
   {
     "translation": {
       "enableFallback": true,
       "fallbackService": "local"
     }
   }
   ```

2. **API Key Issues**
   - Verify Google Translate API key
   - Check API quotas and billing
   - Test API key manually

3. **Content Length**
   - Very long tweets may fail translation
   - Implement content truncation

### ❌ Duplicate Content Detection

**Error**: All content marked as duplicate

**Solutions**:

1. **Check duplicate storage**
   ```bash
   # Verify processed tweets file
   cat automation/data/processed-tweets.json
   ```

2. **Adjust similarity threshold**
   ```json
   {
     "duplicate": {
       "similarityThreshold": 0.7  // Lower = less strict
     }
   }
   ```

3. **Clear processed history**
   ```bash
   # Reset duplicate detection (use carefully)
   echo '{"processedTweets": []}' > automation/data/processed-tweets.json
   ```

### ❌ Article Generation Errors

**Symptoms**: Empty or malformed articles

**Solutions**:

1. **Template Validation**
   ```bash
   # Check template syntax
   cat md-template.md
   ```

2. **Data Validation**
   ```javascript
   // Add debugging to ArticleGenerator
   console.log('Tweet data:', JSON.stringify(tweetData, null, 2));
   ```

3. **Encoding Issues**
   - Ensure UTF-8 encoding
   - Check for special characters
   - Validate Chinese character handling

## Hugo Build Problems

### ❌ "Template not found"

**Solutions**:

1. **Check theme installation**
   ```bash
   ls -la themes/
   git submodule update --init --recursive
   ```

2. **Verify layout files**
   ```bash
   ls -la layouts/_default/
   ```

### ❌ Front Matter Errors

**Error**: TOML parsing errors

**Solutions**:

1. **Validate TOML syntax**
   ```bash
   # Test TOML parsing
   node -e "console.log(require('@iarna/toml').parse(frontMatter))"
   ```

2. **Escape special characters**
   ```javascript
   // In ArticleGenerator
   title: title.replace(/"/g, '\\"')
   ```

### ❌ Build Performance Issues

**Symptoms**: Very slow Hugo builds

**Solutions**:

1. **Enable caching**
   ```yaml
   # In GitHub Actions
   - uses: actions/cache@v3
     with:
       path: /tmp/hugo_cache
       key: ${{ runner.os }}-hugomod-${{ hashFiles('**/go.sum') }}
   ```

2. **Optimize configuration**
   ```toml
   # In hugo.toml
   [caches]
   [caches.getjson]
   maxAge = "10m"
   ```

## Performance Issues

### ❌ Slow Execution

**Solutions**:

1. **Profile execution time**
   ```javascript
   // Add timing logs
   console.time('Twitter API');
   // ... API call
   console.timeEnd('Twitter API');
   ```

2. **Optimize API calls**
   - Use batch requests where possible
   - Implement request caching
   - Reduce unnecessary data fetching

3. **Parallel processing**
   ```javascript
   // Process tweets in parallel
   const results = await Promise.all(
     tweets.map(tweet => processTweet(tweet))
   );
   ```

### ❌ Memory Issues

**Symptoms**: Out of memory errors in GitHub Actions

**Solutions**:

1. **Reduce memory usage**
   ```javascript
   // Process tweets one at a time instead of all at once
   for (const tweet of tweets) {
     await processTweet(tweet);
   }
   ```

2. **Increase GitHub Actions memory**
   ```yaml
   # Use larger runner if needed
   runs-on: ubuntu-latest-4-cores
   ```

## Debugging Tools

### Configuration Validator

```bash
# Run configuration validation
cd automation
node -e "
import ConfigLoader from './src/config/ConfigLoader.js';
const config = new ConfigLoader();
await config.load();
console.log(config.getValidationReport());
"
```

### API Testing

```bash
# Test Twitter API connection
curl -H "Authorization: Bearer $TWITTER_BEARER_TOKEN" \
     "https://api.twitter.com/2/tweets/search/recent?query=crypto&max_results=10"
```

### Local Testing

```bash
# Run automation locally
cd automation
npm run demo
```

### Log Analysis

```bash
# Check GitHub Actions logs
gh run list --repo your-username/your-repo
gh run view RUN_ID --log
```

### Secret Validation

```bash
# Validate GitHub Secrets
node .github/scripts/setup-secrets.js validate
```

## Getting Help

If you're still experiencing issues:

1. **Enable debug logging**
   ```json
   {
     "logging": {
       "level": "debug"
     }
   }
   ```

2. **Collect diagnostic information**
   - GitHub Actions logs
   - Configuration validation report
   - API response samples
   - Error stack traces

3. **Check common causes**
   - API key expiration
   - Rate limit changes
   - GitHub repository permissions
   - Hugo version compatibility

4. **Create detailed issue report**
   - Include error messages
   - Provide configuration (without secrets)
   - Share relevant logs
   - Describe expected vs actual behavior

## Prevention Tips

1. **Regular monitoring**
   - Set up notifications for failures
   - Monitor API usage regularly
   - Check content quality periodically

2. **Proactive maintenance**
   - Rotate API keys quarterly
   - Update dependencies monthly
   - Review and update keywords
   - Monitor Hugo version updates

3. **Testing strategy**
   - Test configuration changes locally
   - Use manual workflow triggers for testing
   - Validate content before production
   - Monitor first few automated runs after changes

---

**Remember**: Most issues are related to configuration, API keys, or permissions. Start with the basics and work your way up to more complex debugging.