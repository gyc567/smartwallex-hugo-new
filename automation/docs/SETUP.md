# Twitter Crypto Content Automation - Setup Guide

This guide will walk you through setting up the Twitter Crypto Content Automation system from scratch.

## Prerequisites

Before you begin, ensure you have:

- A GitHub repository for your Hugo blog
- Node.js 18+ installed
- Git configured with your GitHub account
- A Twitter Developer Account (for API access)

## Step 1: Twitter API Setup

### 1.1 Create Twitter Developer Account

1. Visit [Twitter Developer Portal](https://developer.twitter.com/)
2. Sign up for a developer account
3. Create a new project/app
4. Generate your API keys:
   - **Bearer Token** (required)
   - API Key (optional, for enhanced features)
   - API Secret (optional, for enhanced features)

### 1.2 API Permissions

Ensure your Twitter app has the following permissions:
- Read access to tweets
- Access to search endpoints

## Step 2: GitHub Setup

### 2.1 Repository Preparation

1. Fork or clone this repository
2. Ensure your repository has a Hugo site structure:
   ```
   your-repo/
   ├── content/posts/     # Where articles will be generated
   ├── hugo.toml         # Hugo configuration
   ├── md-template.md    # Article template
   └── automation/       # Automation scripts
   ```

### 2.2 GitHub Personal Access Token

1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate a new token with these permissions:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
3. Save the token securely

## Step 3: Configure GitHub Secrets

### Option A: Automated Setup (Recommended)

1. Install GitHub CLI: https://cli.github.com/
2. Authenticate: `gh auth login`
3. Run the setup script:
   ```bash
   cd .github/scripts
   node setup-secrets.js interactive
   ```

### Option B: Manual Setup

1. Go to your repository on GitHub
2. Navigate to Settings > Secrets and variables > Actions
3. Add the following secrets:

#### Required Secrets

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `TWITTER_BEARER_TOKEN` | Twitter API Bearer Token | `AAAAAAAAAAAAAAAAAAAAAMLheAAAAAAA...` |
| `GITHUB_TOKEN` | GitHub Personal Access Token | `ghp_xxxxxxxxxxxxxxxxxxxx` |
| `GITHUB_REPOSITORY` | Repository in format owner/repo | `your-username/your-blog` |

#### Optional Secrets (for enhanced features)

| Secret Name | Description |
|-------------|-------------|
| `TWITTER_API_KEY` | Twitter API Key |
| `TWITTER_API_SECRET` | Twitter API Secret |
| `GOOGLE_TRANSLATE_API_KEY` | Google Translate API Key |
| `SLACK_WEBHOOK_URL` | Slack webhook for notifications |
| `EMAIL_SMTP_HOST` | SMTP host for email notifications |
| `EMAIL_USER` | Email username |
| `EMAIL_PASS` | Email password/app password |

## Step 4: Configuration

### 4.1 Environment-Specific Configuration

The system uses configuration files in `automation/config/`:

- `default.json` - Base configuration
- `development.json` - Development overrides
- `production.json` - Production overrides

### 4.2 Customize Configuration

Edit the configuration files to match your needs:

```json
{
  "twitter": {
    "searchKeywords": [
      "cryptocurrency OR crypto",
      "blockchain OR bitcoin OR BTC",
      "ethereum OR ETH OR DeFi"
    ],
    "maxResults": 100
  },
  "content": {
    "topTweetsCount": 3,
    "minRetweetCount": 10,
    "targetLanguage": "zh-CN"
  },
  "hugo": {
    "contentPath": "../content/posts",
    "baseUrl": "https://your-site.com"
  }
}
```

### 4.3 Template Customization

Customize the article template in `md-template.md`:

```markdown
+++
date = '{{date}}'
title = '{{title}}'
description = '{{description}}'
tags = [{{tags}}]
categories = ['推文分析']
+++

{{content}}
```

## Step 5: Testing

### 5.1 Local Testing

1. Install dependencies:
   ```bash
   cd automation
   npm install
   ```

2. Set up local environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Run tests:
   ```bash
   npm test
   ```

4. Test the workflow:
   ```bash
   npm run demo
   ```

### 5.2 Validate Configuration

Run the configuration validator:

```bash
node -e "
import ConfigLoader from './src/config/ConfigLoader.js';
const config = new ConfigLoader();
await config.load();
console.log(config.getValidationReport());
"
```

## Step 6: Deployment

### 6.1 Enable GitHub Actions

1. Go to your repository's Actions tab
2. Enable Actions if not already enabled
3. The workflow file `.github/workflows/twitter-automation.yml` should be automatically detected

### 6.2 Manual Trigger (Testing)

1. Go to Actions tab in your repository
2. Select "Twitter Crypto Content Automation"
3. Click "Run workflow" to test manually

### 6.3 Scheduled Execution

The automation runs automatically:
- **9:00 AM Beijing Time** (01:00 UTC)
- **9:00 PM Beijing Time** (13:00 UTC)

## Step 7: Monitoring

### 7.1 GitHub Actions Logs

Monitor execution in the Actions tab:
- Check for successful runs
- Review error logs if failures occur
- Monitor API usage and rate limits

### 7.2 Generated Content

Check the generated content:
- Articles appear in `content/posts/`
- Hugo builds the site automatically
- New posts are visible on your live site

### 7.3 Notifications (Optional)

If configured, you'll receive notifications via:
- Slack (if webhook configured)
- Email (if SMTP configured)

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues and solutions.

## Security Best Practices

1. **Never commit secrets** to your repository
2. **Rotate API keys** regularly (every 3-6 months)
3. **Monitor API usage** to detect anomalies
4. **Use least-privilege** access tokens
5. **Enable branch protection** on main branch
6. **Review generated content** periodically for quality

## Support

If you encounter issues:

1. Check the [troubleshooting guide](./TROUBLESHOOTING.md)
2. Review GitHub Actions logs
3. Validate your configuration
4. Check API quotas and limits
5. Open an issue with detailed error information

## Next Steps

After successful setup:

1. Monitor the first few automated runs
2. Adjust configuration based on content quality
3. Customize the article template for your brand
4. Set up additional notification channels
5. Consider adding more cryptocurrency keywords
6. Optimize Hugo build performance

---

**Note**: This automation respects Twitter's API rate limits and terms of service. Ensure your usage complies with Twitter's developer policies.