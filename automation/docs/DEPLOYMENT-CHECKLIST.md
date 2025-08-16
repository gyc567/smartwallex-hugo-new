# Deployment Checklist

Use this checklist to ensure your Twitter Crypto Content Automation is properly configured and ready for production deployment.

## Pre-Deployment Checklist

### ✅ 1. Prerequisites

- [ ] Node.js 18+ installed
- [ ] Git configured with your GitHub account
- [ ] Hugo static site generator installed
- [ ] Twitter Developer Account created
- [ ] GitHub repository set up with Hugo site structure

### ✅ 2. API Setup

#### Twitter API
- [ ] Twitter Developer Account approved
- [ ] Twitter App created with appropriate permissions
- [ ] Bearer Token generated and saved securely
- [ ] API Key and Secret generated (optional)
- [ ] Rate limits understood (300 requests per 15 minutes)

#### GitHub API
- [ ] Personal Access Token created
- [ ] Token has `repo` and `workflow` permissions
- [ ] Token tested and working

### ✅ 3. Repository Setup

- [ ] Repository contains Hugo site structure
- [ ] `content/posts/` directory exists
- [ ] `md-template.md` file exists and is properly formatted
- [ ] `automation/` directory contains all required files
- [ ] `.github/workflows/twitter-automation.yml` exists

### ✅ 4. Configuration Files

- [ ] `automation/config/default.json` configured
- [ ] `automation/config/production.json` configured
- [ ] Configuration values match your requirements
- [ ] File paths are correct for your repository structure

## Configuration Validation

### ✅ 5. GitHub Secrets

Run the secrets setup script to validate:

```bash
node .github/scripts/setup-secrets.js validate
```

#### Required Secrets
- [ ] `TWITTER_BEARER_TOKEN` - Twitter API Bearer Token
- [ ] `GITHUB_TOKEN` - GitHub Personal Access Token
- [ ] `GITHUB_REPOSITORY` - Repository name (format: username/repo)

#### Optional Secrets (for enhanced features)
- [ ] `TWITTER_API_KEY` - Twitter API Key
- [ ] `TWITTER_API_SECRET` - Twitter API Secret
- [ ] `GOOGLE_TRANSLATE_API_KEY` - Google Translate API Key
- [ ] `SLACK_WEBHOOK_URL` - Slack webhook for notifications
- [ ] `EMAIL_SMTP_HOST` - SMTP host for email notifications
- [ ] `EMAIL_USER` - Email username
- [ ] `EMAIL_PASS` - Email password/app password

### ✅ 6. Configuration Validation

Run the configuration validator:

```bash
cd automation
node -e "
import ConfigLoader from './src/config/ConfigLoader.js';
const config = new ConfigLoader();
await config.load();
console.log(config.getValidationReport());
"
```

Ensure all validation checks pass.

## Testing Phase

### ✅ 7. Local Testing

```bash
cd automation
npm install
npm test
```

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] No critical errors in test output

### ✅ 8. Deployment Testing

Run the comprehensive deployment test:

```bash
cd automation
node scripts/test-deployment.js
```

- [ ] Configuration tests pass
- [ ] Environment variable tests pass
- [ ] Dependency tests pass
- [ ] API connectivity tests pass
- [ ] File system tests pass
- [ ] Hugo build tests pass
- [ ] GitHub operation tests pass
- [ ] End-to-end tests pass

### ✅ 9. Manual Workflow Test

1. Go to your repository's Actions tab
2. Find "Twitter Crypto Content Automation" workflow
3. Click "Run workflow" to trigger manually
4. Monitor the execution logs

- [ ] Workflow starts successfully
- [ ] Twitter API calls succeed
- [ ] Content generation completes
- [ ] Articles are created in `content/posts/`
- [ ] Hugo build succeeds
- [ ] Changes are committed to repository

## Production Deployment

### ✅ 10. GitHub Actions Setup

- [ ] Workflow file is in `.github/workflows/twitter-automation.yml`
- [ ] Cron schedule is configured correctly (9 AM & 9 PM Beijing time)
- [ ] Workflow permissions are set correctly
- [ ] Actions are enabled in repository settings

### ✅ 11. Repository Settings

#### Actions Settings
- [ ] Go to Settings > Actions > General
- [ ] Ensure "Allow all actions and reusable workflows" is selected
- [ ] Set "Workflow permissions" to "Read and write permissions"
- [ ] Enable "Allow GitHub Actions to create and approve pull requests" if needed

#### Branch Protection (Optional but Recommended)
- [ ] Set up branch protection rules for main branch
- [ ] Allow automation to bypass protection if needed
- [ ] Require status checks if desired

### ✅ 12. Monitoring Setup

#### Notifications (Optional)
- [ ] Slack webhook configured for error notifications
- [ ] Email notifications configured
- [ ] Test notification delivery

#### Logging
- [ ] Log level set appropriately for production
- [ ] Log retention configured
- [ ] Error tracking enabled

## Post-Deployment Verification

### ✅ 13. First Run Verification

After the first automated run:

- [ ] Check Actions tab for successful execution
- [ ] Verify new articles were created in `content/posts/`
- [ ] Confirm articles are properly formatted
- [ ] Check that Hugo build succeeded
- [ ] Verify live site shows new content
- [ ] Review content quality and relevance

### ✅ 14. Ongoing Monitoring

Set up regular checks:

- [ ] Monitor GitHub Actions for failures
- [ ] Check API usage and rate limits
- [ ] Review generated content quality
- [ ] Monitor site performance
- [ ] Check for duplicate content issues

## Security Checklist

### ✅ 15. Security Best Practices

- [ ] All secrets are stored in GitHub Secrets (never in code)
- [ ] API keys have minimal required permissions
- [ ] Repository access is properly controlled
- [ ] Branch protection rules are in place
- [ ] Regular security updates are planned

### ✅ 16. API Security

- [ ] Twitter API keys are rotated regularly
- [ ] GitHub token has minimal required scopes
- [ ] API usage is monitored for anomalies
- [ ] Rate limiting is properly implemented

## Troubleshooting Preparation

### ✅ 17. Documentation

- [ ] Setup documentation is accessible to team
- [ ] Troubleshooting guide is available
- [ ] Configuration is documented
- [ ] Emergency contacts are defined

### ✅ 18. Backup Plans

- [ ] Manual content generation process documented
- [ ] API key backup/rotation process defined
- [ ] Site rollback procedure documented
- [ ] Emergency shutdown procedure defined

## Performance Optimization

### ✅ 19. Performance Settings

- [ ] API request limits are optimized
- [ ] Content processing is efficient
- [ ] Hugo build is optimized
- [ ] Caching is properly configured

### ✅ 20. Scalability

- [ ] System can handle increased API limits
- [ ] Content storage can scale
- [ ] Build times are acceptable
- [ ] Error handling is robust

## Final Verification

### ✅ 21. Complete System Test

Run a complete end-to-end test:

1. Trigger manual workflow
2. Monitor all stages
3. Verify output quality
4. Check site deployment
5. Confirm notifications work

- [ ] All stages complete successfully
- [ ] Content quality meets standards
- [ ] Site updates are live
- [ ] No errors in logs

### ✅ 22. Production Readiness

- [ ] All checklist items completed
- [ ] Team is trained on monitoring
- [ ] Documentation is complete
- [ ] Emergency procedures are in place
- [ ] Success metrics are defined

## Sign-off

**Deployment completed by:** ________________  
**Date:** ________________  
**Environment:** Production  
**Version:** ________________  

**Verification:**
- [ ] Technical lead approval
- [ ] Content quality approval
- [ ] Security review completed
- [ ] Monitoring configured
- [ ] Team notified

---

## Quick Commands Reference

```bash
# Validate secrets
node .github/scripts/setup-secrets.js validate

# Test configuration
cd automation && node -e "import ConfigLoader from './src/config/ConfigLoader.js'; const config = new ConfigLoader(); await config.load(); console.log(config.getValidationReport());"

# Run deployment tests
cd automation && node scripts/test-deployment.js

# Manual workflow trigger
gh workflow run twitter-automation.yml

# Check workflow status
gh run list --workflow=twitter-automation.yml

# View latest run logs
gh run view --log
```

Save this checklist and check off items as you complete them. Keep a record of your deployment for future reference and troubleshooting.