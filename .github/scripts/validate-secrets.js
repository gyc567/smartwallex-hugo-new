#!/usr/bin/env node

/**
 * GitHub Secrets Validation Script
 * 
 * This script helps validate that all required GitHub Secrets are properly configured
 * for the Twitter Crypto Content Automation workflow.
 * 
 * Usage: node .github/scripts/validate-secrets.js
 */

const requiredSecrets = [
  {
    name: 'TWITTER_BEARER_TOKEN',
    description: 'Twitter API v2 Bearer Token',
    required: true,
    validation: (value) => value && value.startsWith('AAAA') && value.length > 100
  }
];

const optionalSecrets = [
  {
    name: 'TWITTER_API_KEY',
    description: 'Twitter API Key',
    required: false,
    validation: (value) => !value || value.length > 20
  },
  {
    name: 'TWITTER_API_SECRET',
    description: 'Twitter API Secret',
    required: false,
    validation: (value) => !value || value.length > 40
  },
  {
    name: 'GOOGLE_TRANSLATE_API_KEY',
    description: 'Google Translate API Key',
    required: false,
    validation: (value) => !value || value.length > 30
  },
  {
    name: 'AZURE_TRANSLATOR_KEY',
    description: 'Azure Translator Service Key',
    required: false,
    validation: (value) => !value || value.length > 30
  },
  {
    name: 'SLACK_WEBHOOK_URL',
    description: 'Slack webhook URL for notifications',
    required: false,
    validation: (value) => !value || value.startsWith('https://hooks.slack.com/')
  }
];

function validateSecrets() {
  console.log('🔍 Validating GitHub Secrets Configuration...\n');
  
  let allValid = true;
  let warnings = [];

  // Check required secrets
  console.log('📋 Required Secrets:');
  for (const secret of requiredSecrets) {
    const value = process.env[secret.name];
    const isPresent = !!value;
    const isValid = isPresent && secret.validation(value);
    
    if (isPresent && isValid) {
      console.log(`  ✅ ${secret.name}: Configured and valid`);
    } else if (isPresent && !isValid) {
      console.log(`  ❌ ${secret.name}: Configured but invalid format`);
      allValid = false;
    } else {
      console.log(`  ❌ ${secret.name}: Missing (required)`);
      allValid = false;
    }
  }

  // Check optional secrets
  console.log('\n📋 Optional Secrets:');
  for (const secret of optionalSecrets) {
    const value = process.env[secret.name];
    const isPresent = !!value;
    
    if (isPresent) {
      const isValid = secret.validation(value);
      if (isValid) {
        console.log(`  ✅ ${secret.name}: Configured and valid`);
      } else {
        console.log(`  ⚠️  ${secret.name}: Configured but invalid format`);
        warnings.push(`${secret.name} appears to have an invalid format`);
      }
    } else {
      console.log(`  ⚪ ${secret.name}: Not configured (optional)`);
    }
  }

  // Summary
  console.log('\n📊 Validation Summary:');
  if (allValid) {
    console.log('  ✅ All required secrets are properly configured');
  } else {
    console.log('  ❌ Some required secrets are missing or invalid');
  }

  if (warnings.length > 0) {
    console.log('  ⚠️  Warnings:');
    warnings.forEach(warning => console.log(`    - ${warning}`));
  }

  // Instructions
  console.log('\n📖 Setup Instructions:');
  console.log('  1. Go to your repository → Settings → Secrets and variables → Actions');
  console.log('  2. Click "New repository secret"');
  console.log('  3. Add the missing secrets listed above');
  console.log('  4. For Twitter Bearer Token: https://developer.twitter.com/en/portal/dashboard');
  console.log('  5. Re-run this script to validate: node .github/scripts/validate-secrets.js');

  return allValid;
}

// Run validation if this script is executed directly
if (require.main === module) {
  const isValid = validateSecrets();
  process.exit(isValid ? 0 : 1);
}

module.exports = { validateSecrets, requiredSecrets, optionalSecrets };