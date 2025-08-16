# GitHub Actions Workflow Documentation

## Twitter Crypto Content Automation Workflow

This workflow automatically discovers trending cryptocurrency content on Twitter, translates it to Chinese, and publishes it as Hugo blog posts twice daily.

### Schedule

- **9:00 AM Beijing Time** (1:00 AM UTC)
- **9:00 PM Beijing Time** (1:00 PM UTC)

### Required GitHub Secrets

The following secrets must be configured in your repository settings:

#### Required Secrets

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `TWITTER_BEARER_TOKEN` | Twitter API v2 Bearer Token | ✅ Yes |

#### Optional Secrets

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `TWITTER_API_KEY` | Twitter API Key (for enhanced features) | ❌ No |
| `TWITTER_API_SECRET` | Twitter API Secret (for enhanced features) | ❌ No |
| `GOOGLE_TRANSLATE_API_KEY` | Google Translate API Key | ❌ No |
| `AZURE_TRANSLATOR_KEY` | Azure Translator Service Key | ❌ No |
| `SLACK_WEBHOOK_URL` | Slack webhook for notifications | ❌ No |
| `EMAIL_SMTP_HOST` | SMTP host for email notifications | ❌ No |
| `EMAIL_SMTP_PORT` | SMTP port for email notifications | ❌ No |
| `EMAIL_USER` | Email username for notifications | ❌ No |
| `EMAIL_PASS` | Email password for notifications | ❌ No |
| `EMAIL_TO` | Email recipient for notifications | ❌ No |

### Setup Instructions

1. **Configure Twitter API Access**
   - Go to [Twitter Developer Portal](https://developer.twitter.com/)
   - Create a new app or use existing app
   - Generate Bearer Token
   - Add `TWITTER_BEARER_TOKEN` to GitHub Secrets

2. **Configure GitHub Secrets**
   - Go to your repository → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Add the required secrets listed above

3. **Enable GitHub Actions**
   - Ensure GitHub Actions are enabled for your repository
   - The workflow will automatically run on the scheduled times
   - You can also trigger it manually from the Actions tab

### Workflow Steps

1. **Setup Environment**
   - Checkout repository
   - Setup Node.js 18
   - Install dependencies
   - Setup Hugo (latest extended version)

2. **Content Generation**
   - Search Twitter for trending crypto content
   - Process and rank tweets by engagement
   - Translate content to Chinese
   - Generate markdown articles using template

3. **Site Building**
   - Write articles to `content/posts/` directory
   - Build Hugo site with minification
   - Generate optimized HTML output

4. **Publishing**
   - Commit new content to repository
   - Push changes to trigger site deployment
   - Generate workflow summary

### Manual Execution

You can manually trigger the workflow:

1. Go to the Actions tab in your repository
2. Select "Twitter Crypto Content Automation"
3. Click "Run workflow"
4. Choose the branch and click "Run workflow"

### Monitoring

The workflow provides detailed logging and summary information:

- **Workflow Summary**: Shows execution status and statistics
- **Step Logs**: Detailed logs for each step
- **Error Handling**: Automatic retry logic for API calls and Git operations

### Troubleshooting

#### Common Issues

1. **Twitter API Rate Limits**
   - The workflow includes automatic retry logic
   - Rate limits reset every 15 minutes
   - Consider reducing search frequency if limits are consistently hit

2. **Hugo Build Failures**
   - Check Hugo configuration in `hugo.toml`
   - Ensure content files have valid front matter
   - Review build logs for specific errors

3. **Git Push Failures**
   - The workflow includes retry logic with exponential backoff
   - Ensure repository permissions are correctly configured
   - Check for conflicts with concurrent workflows

#### Debug Mode

To enable debug logging, add this secret:
- `LOG_LEVEL`: Set to `debug` for verbose logging

### Security Considerations

- All sensitive credentials are stored as GitHub Secrets
- The workflow uses minimal required permissions
- API keys are never logged or exposed in output
- Git operations use the built-in `GITHUB_TOKEN`

### Performance

- **Typical execution time**: 3-5 minutes
- **API calls**: ~10-20 Twitter API requests per run
- **Generated content**: Up to 3 articles per execution
- **Hugo build time**: 10-30 seconds depending on site size

### Customization

To modify the workflow behavior:

1. **Change Schedule**: Edit the `cron` expression in the workflow file
2. **Modify Keywords**: Update `searchKeywords` in `automation/config/default.json`
3. **Adjust Content Count**: Change `topTweetsCount` in the configuration
4. **Custom Templates**: Modify `md-template.md` in the repository root

### Support

For issues with the workflow:

1. Check the Actions tab for detailed logs
2. Review the automation code in the `automation/` directory
3. Ensure all required secrets are properly configured
4. Test the automation locally using the demo scripts