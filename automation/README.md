# Twitter Crypto Content Automation

Automated system that discovers trending cryptocurrency content on Twitter, translates it into Chinese, and publishes it as Hugo blog posts via GitHub Actions.

## 🚀 Quick Start

1. **Setup**: Follow the [Setup Guide](docs/SETUP.md)
2. **Configure**: Set up GitHub Secrets and configuration files
3. **Deploy**: Use the [Deployment Checklist](docs/DEPLOYMENT-CHECKLIST.md)
4. **Monitor**: Check GitHub Actions for automated runs

## 📚 Documentation

- **[Setup Guide](docs/SETUP.md)** - Complete setup instructions
- **[Deployment Checklist](docs/DEPLOYMENT-CHECKLIST.md)** - Pre-deployment verification
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Error Handling](docs/ErrorHandling-README.md)** - Error handling documentation
- **[Main Workflow](docs/MainWorkflow-README.md)** - Workflow documentation

## Project Structure

```
automation/
├── src/                    # Source code
│   ├── clients/           # API clients (Twitter, etc.)
│   ├── processors/        # Content processing logic
│   ├── services/          # Translation and other services
│   ├── generators/        # Article generation
│   ├── utils/            # Utility classes
│   ├── builders/         # Hugo building logic
│   ├── config/           # Configuration management
│   └── index.js          # Main entry point
├── config/               # Configuration files
│   ├── default.json      # Default configuration
│   ├── development.json  # Development overrides
│   └── production.json   # Production overrides
├── data/                 # Data storage
│   └── processed-tweets.json  # Processed tweet tracking
├── tests/                # Test files
├── logs/                 # Log files (created at runtime)
└── package.json          # Node.js dependencies
```

## 🔧 Setup & Configuration

### Prerequisites
- Node.js 18+
- Twitter Developer Account
- GitHub repository with Hugo site

### Quick Setup
```bash
# 1. Install dependencies
cd automation
npm install

# 2. Set up GitHub Secrets (interactive)
node .github/scripts/setup-secrets.js interactive

# 3. Validate configuration
node scripts/test-deployment.js

# 4. Test manually
npm run demo
```

### Configuration Files
- `config/default.json` - Base settings
- `config/production.json` - Production overrides
- `.env.example` - Environment variable template

See [Setup Guide](docs/SETUP.md) for detailed instructions.

## Configuration

The system uses a hierarchical configuration system:
- `config/default.json` - Base configuration
- `config/development.json` - Development overrides
- `config/production.json` - Production overrides
- `.env` - Environment variables (API keys, secrets)

## Testing

Run tests with:
```bash
npm test
```

Run tests in watch mode:
```bash
npm run test:watch
```

## 🛠️ Development

### Local Development
```bash
# Development mode with auto-reload
npm run dev

# Run specific examples
npm run example:twitter
npm run example:article
npm run example:workflow
```

### Testing & Validation
```bash
# Run all tests
npm test

# Test deployment readiness
node scripts/test-deployment.js

# Validate GitHub Secrets
node .github/scripts/setup-secrets.js validate

# Check configuration
node -e "import ConfigLoader from './src/config/ConfigLoader.js'; const config = new ConfigLoader(); await config.load(); console.log(config.getValidationReport());"
```

## 🚀 Deployment

### Automated Deployment (GitHub Actions)
The system runs automatically twice daily:
- **9:00 AM Beijing Time** (01:00 UTC)
- **9:00 PM Beijing Time** (13:00 UTC)

### Manual Deployment
```bash
# Trigger workflow manually
gh workflow run twitter-automation.yml

# Check workflow status
gh run list --workflow=twitter-automation.yml
```

### Deployment Checklist
Use the [Deployment Checklist](docs/DEPLOYMENT-CHECKLIST.md) to ensure everything is configured correctly.

## 📊 Monitoring

### GitHub Actions
- Monitor workflow runs in the Actions tab
- Check logs for errors or warnings
- Review generated content quality

### Configuration Validation
```bash
# Check system health
node scripts/test-deployment.js

# Validate secrets
node .github/scripts/setup-secrets.js validate
```

## 🔒 Security

- All API keys stored in GitHub Secrets
- Regular token rotation recommended
- Rate limiting and error handling built-in
- Content validation and spam filtering

## 🆘 Troubleshooting

If you encounter issues:

1. Check the [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
2. Validate your configuration
3. Review GitHub Actions logs
4. Test API connectivity

Common issues:
- **API Authentication**: Check Twitter Bearer Token
- **Rate Limits**: Monitor API usage
- **Configuration**: Validate JSON syntax
- **Permissions**: Check GitHub token scopes