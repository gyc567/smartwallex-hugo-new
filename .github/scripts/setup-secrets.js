#!/usr/bin/env node

/**
 * GitHub Secrets Setup Script
 * Helps users set up required GitHub Secrets for the Twitter automation
 */

import { execSync } from 'child_process';
import fs from 'fs-extra';
import path from 'path';

class GitHubSecretsSetup {
  constructor() {
    this.requiredSecrets = [
      {
        name: 'TWITTER_BEARER_TOKEN',
        description: 'Twitter API Bearer Token for authentication',
        required: true,
        example: 'AAAAAAAAAAAAAAAAAAAAAMLheAAAAAAA0%2BuSeid%2BULvsea4JtiGRiSDSJSI%3DEUifiRBkKG5E2XzMDjRfl76ZC9Ub0wnz4XsNiRVBChTYbJcE3F'
      },
      {
        name: 'GITHUB_TOKEN',
        description: 'GitHub Personal Access Token with repo permissions',
        required: true,
        example: 'ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
      },
      {
        name: 'GITHUB_REPOSITORY',
        description: 'GitHub repository in format username/repository',
        required: true,
        example: 'your-username/your-crypto-blog'
      },
      {
        name: 'TWITTER_API_KEY',
        description: 'Twitter API Key (optional, for enhanced features)',
        required: false,
        example: 'xxxxxxxxxxxxxxxxxxxxxxxxx'
      },
      {
        name: 'TWITTER_API_SECRET',
        description: 'Twitter API Secret (optional, for enhanced features)',
        required: false,
        example: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
      },
      {
        name: 'GOOGLE_TRANSLATE_API_KEY',
        description: 'Google Translate API Key (optional, for better translations)',
        required: false,
        example: 'AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
      },
      {
        name: 'SLACK_WEBHOOK_URL',
        description: 'Slack Webhook URL for notifications (optional)',
        required: false,
        example: 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'
      },
      {
        name: 'EMAIL_SMTP_HOST',
        description: 'SMTP host for email notifications (optional)',
        required: false,
        example: 'smtp.gmail.com'
      },
      {
        name: 'EMAIL_USER',
        description: 'Email username for notifications (optional)',
        required: false,
        example: 'your-email@gmail.com'
      },
      {
        name: 'EMAIL_PASS',
        description: 'Email password or app password (optional)',
        required: false,
        example: 'your-app-password'
      }
    ];
  }

  /**
   * Check if GitHub CLI is installed
   * @returns {boolean} True if gh CLI is available
   */
  isGitHubCliAvailable() {
    try {
      execSync('gh --version', { stdio: 'ignore' });
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Check if user is authenticated with GitHub CLI
   * @returns {boolean} True if authenticated
   */
  isGitHubAuthenticated() {
    try {
      execSync('gh auth status', { stdio: 'ignore' });
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get current repository info
   * @returns {Object|null} Repository info or null if not in a git repo
   */
  getCurrentRepository() {
    try {
      const remoteUrl = execSync('git remote get-url origin', { encoding: 'utf8' }).trim();
      const match = remoteUrl.match(/github\.com[:/]([^/]+)\/([^/.]+)/);
      if (match) {
        return {
          owner: match[1],
          repo: match[2],
          fullName: `${match[1]}/${match[2]}`
        };
      }
    } catch (error) {
      // Not in a git repository or no origin remote
    }
    return null;
  }

  /**
   * List existing secrets in the repository
   * @param {string} repo - Repository in format owner/repo
   * @returns {Array} List of existing secret names
   */
  listExistingSecrets(repo) {
    try {
      const output = execSync(`gh secret list --repo ${repo}`, { encoding: 'utf8' });
      return output.split('\n')
        .filter(line => line.trim())
        .map(line => line.split('\t')[0]);
    } catch (error) {
      console.warn('Could not list existing secrets:', error.message);
      return [];
    }
  }

  /**
   * Set a GitHub secret
   * @param {string} repo - Repository in format owner/repo
   * @param {string} name - Secret name
   * @param {string} value - Secret value
   * @returns {boolean} True if successful
   */
  setSecret(repo, name, value) {
    try {
      execSync(`gh secret set ${name} --repo ${repo} --body "${value}"`, { stdio: 'ignore' });
      return true;
    } catch (error) {
      console.error(`Failed to set secret ${name}:`, error.message);
      return false;
    }
  }

  /**
   * Generate setup instructions
   * @returns {string} Formatted setup instructions
   */
  generateInstructions() {
    const repo = this.getCurrentRepository();
    let instructions = `
🔐 GitHub Secrets Setup Instructions
=====================================

This automation requires several GitHub Secrets to be configured in your repository.

`;

    if (!this.isGitHubCliAvailable()) {
      instructions += `
❌ GitHub CLI Not Found
The GitHub CLI (gh) is not installed. You have two options:

Option 1: Install GitHub CLI (Recommended)
- Visit: https://cli.github.com/
- Follow installation instructions for your platform
- Run: gh auth login
- Then run this script again

Option 2: Manual Setup via GitHub Web Interface
- Go to your repository on GitHub.com
- Navigate to Settings > Secrets and variables > Actions
- Click "New repository secret" for each required secret below

`;
    } else if (!this.isGitHubAuthenticated()) {
      instructions += `
❌ GitHub CLI Not Authenticated
Please authenticate with GitHub CLI:
- Run: gh auth login
- Follow the prompts to authenticate
- Then run this script again

`;
    } else {
      instructions += `
✅ GitHub CLI is ready!
`;
      if (repo) {
        instructions += `📁 Current repository: ${repo.fullName}\n`;
      }
    }

    instructions += `
📋 Required Secrets:
`;

    this.requiredSecrets.forEach(secret => {
      const status = secret.required ? '🔴 REQUIRED' : '🟡 OPTIONAL';
      instructions += `
${status} ${secret.name}
Description: ${secret.description}
Example: ${secret.example}
`;
    });

    if (this.isGitHubCliAvailable() && this.isGitHubAuthenticated() && repo) {
      const existingSecrets = this.listExistingSecrets(repo.fullName);
      
      instructions += `
📊 Current Status:
`;
      
      this.requiredSecrets.forEach(secret => {
        const exists = existingSecrets.includes(secret.name);
        const status = exists ? '✅' : (secret.required ? '❌' : '⚪');
        instructions += `${status} ${secret.name} ${exists ? '(configured)' : '(not set)'}\n`;
      });

      instructions += `
🚀 Quick Setup Commands:
To set secrets using GitHub CLI, run these commands:

`;

      this.requiredSecrets.forEach(secret => {
        instructions += `# ${secret.description}
gh secret set ${secret.name} --repo ${repo.fullName}

`;
      });
    }

    instructions += `
📚 Additional Resources:
- Twitter API Setup: https://developer.twitter.com/en/docs/twitter-api/getting-started/getting-access-to-the-twitter-api
- GitHub Personal Access Tokens: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
- Google Translate API: https://cloud.google.com/translate/docs/setup

⚠️  Security Notes:
- Never commit secrets to your repository
- Use environment-specific secrets for different deployments
- Regularly rotate your API keys and tokens
- Monitor secret usage in GitHub Actions logs

`;

    return instructions;
  }

  /**
   * Interactive setup process
   */
  async interactiveSetup() {
    console.log('🔐 GitHub Secrets Interactive Setup\n');

    if (!this.isGitHubCliAvailable()) {
      console.log('❌ GitHub CLI is required for interactive setup.');
      console.log('Please install it from: https://cli.github.com/');
      return;
    }

    if (!this.isGitHubAuthenticated()) {
      console.log('❌ Please authenticate with GitHub CLI first:');
      console.log('Run: gh auth login');
      return;
    }

    const repo = this.getCurrentRepository();
    if (!repo) {
      console.log('❌ Not in a GitHub repository. Please run this from your repository root.');
      return;
    }

    console.log(`📁 Repository: ${repo.fullName}`);
    
    const existingSecrets = this.listExistingSecrets(repo.fullName);
    console.log(`📊 Found ${existingSecrets.length} existing secrets\n`);

    // Check required secrets
    const missingRequired = this.requiredSecrets
      .filter(s => s.required && !existingSecrets.includes(s.name));

    if (missingRequired.length === 0) {
      console.log('✅ All required secrets are configured!');
    } else {
      console.log(`❌ Missing ${missingRequired.length} required secrets:`);
      missingRequired.forEach(secret => {
        console.log(`   • ${secret.name}: ${secret.description}`);
      });
    }

    console.log('\n📋 Setup Instructions:');
    console.log(this.generateInstructions());
  }

  /**
   * Validate secrets configuration
   * @param {string} repo - Repository name
   * @returns {Object} Validation result
   */
  validateSecrets(repo) {
    const existingSecrets = this.listExistingSecrets(repo);
    const missing = [];
    const optional = [];

    this.requiredSecrets.forEach(secret => {
      if (!existingSecrets.includes(secret.name)) {
        if (secret.required) {
          missing.push(secret.name);
        } else {
          optional.push(secret.name);
        }
      }
    });

    return {
      valid: missing.length === 0,
      existing: existingSecrets.filter(name => 
        this.requiredSecrets.some(s => s.name === name)
      ),
      missing,
      optional,
      total: this.requiredSecrets.length,
      configured: existingSecrets.length
    };
  }
}

// CLI interface
if (import.meta.url === `file://${process.argv[1]}`) {
  const setup = new GitHubSecretsSetup();
  
  const command = process.argv[2];
  
  switch (command) {
    case 'interactive':
    case 'setup':
      await setup.interactiveSetup();
      break;
    
    case 'validate':
      const repo = setup.getCurrentRepository();
      if (repo) {
        const result = setup.validateSecrets(repo.fullName);
        console.log('🔐 Secrets Validation Result:');
        console.log(`✅ Valid: ${result.valid}`);
        console.log(`📊 Configured: ${result.configured}/${result.total}`);
        if (result.missing.length > 0) {
          console.log(`❌ Missing required: ${result.missing.join(', ')}`);
        }
        if (result.optional.length > 0) {
          console.log(`⚪ Missing optional: ${result.optional.join(', ')}`);
        }
      } else {
        console.log('❌ Not in a GitHub repository');
      }
      break;
    
    default:
      console.log(setup.generateInstructions());
  }
}

export default GitHubSecretsSetup;