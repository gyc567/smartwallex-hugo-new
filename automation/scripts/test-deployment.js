#!/usr/bin/env node

/**
 * Deployment Testing Script
 * Tests the complete deployment pipeline in a staging environment
 */

import fs from 'fs-extra';
import path from 'path';
import { execSync } from 'child_process';
import ConfigLoader from '../src/config/ConfigLoader.js';
import ConfigValidator from '../src/config/ConfigValidator.js';

class DeploymentTester {
  constructor() {
    this.testResults = {
      configuration: { passed: false, errors: [] },
      environment: { passed: false, errors: [] },
      dependencies: { passed: false, errors: [] },
      apiConnectivity: { passed: false, errors: [] },
      fileSystem: { passed: false, errors: [] },
      hugo: { passed: false, errors: [] },
      github: { passed: false, errors: [] },
      endToEnd: { passed: false, errors: [] }
    };
    
    this.tempDir = path.join(process.cwd(), 'test-deployment-temp');
  }

  /**
   * Run all deployment tests
   */
  async runAllTests() {
    console.log('🚀 Starting Deployment Testing...\n');

    try {
      await this.testConfiguration();
      await this.testEnvironment();
      await this.testDependencies();
      await this.testApiConnectivity();
      await this.testFileSystem();
      await this.testHugo();
      await this.testGitHub();
      await this.testEndToEnd();
    } catch (error) {
      console.error('❌ Critical error during testing:', error.message);
    } finally {
      await this.cleanup();
      this.generateReport();
    }
  }

  /**
   * Test configuration loading and validation
   */
  async testConfiguration() {
    console.log('📋 Testing Configuration...');
    
    try {
      const configLoader = new ConfigLoader();
      const config = await configLoader.load(false); // Don't validate yet
      
      const validator = new ConfigValidator();
      const configResult = validator.validateConfig(config);
      
      if (configResult.valid) {
        this.testResults.configuration.passed = true;
        console.log('✅ Configuration is valid');
      } else {
        this.testResults.configuration.errors = configResult.errors;
        console.log('❌ Configuration validation failed');
        configResult.errors.forEach(error => console.log(`   • ${error}`));
      }
    } catch (error) {
      this.testResults.configuration.errors.push(error.message);
      console.log('❌ Configuration loading failed:', error.message);
    }
    
    console.log();
  }

  /**
   * Test environment variables
   */
  async testEnvironment() {
    console.log('🔐 Testing Environment Variables...');
    
    try {
      const validator = new ConfigValidator();
      const envResult = validator.validateEnvironment();
      
      if (envResult.valid) {
        this.testResults.environment.passed = true;
        console.log('✅ All required environment variables are set');
      } else {
        this.testResults.environment.errors = envResult.errors;
        console.log('❌ Environment validation failed');
        envResult.errors.forEach(error => console.log(`   • ${error}`));
      }
      
      if (envResult.warnings.length > 0) {
        console.log('⚠️  Environment warnings:');
        envResult.warnings.forEach(warning => console.log(`   • ${warning}`));
      }
    } catch (error) {
      this.testResults.environment.errors.push(error.message);
      console.log('❌ Environment testing failed:', error.message);
    }
    
    console.log();
  }

  /**
   * Test Node.js dependencies
   */
  async testDependencies() {
    console.log('📦 Testing Dependencies...');
    
    try {
      // Check package.json exists
      const packagePath = path.join(process.cwd(), 'package.json');
      if (!await fs.pathExists(packagePath)) {
        throw new Error('package.json not found');
      }
      
      // Check node_modules
      const nodeModulesPath = path.join(process.cwd(), 'node_modules');
      if (!await fs.pathExists(nodeModulesPath)) {
        console.log('⚠️  node_modules not found, running npm install...');
        execSync('npm install', { stdio: 'inherit' });
      }
      
      // Test key imports
      const testImports = [
        '../src/config/ConfigLoader.js',
        '../src/clients/TwitterClient.js',
        '../src/generators/ArticleGenerator.js'
      ];
      
      for (const importPath of testImports) {
        try {
          await import(importPath);
        } catch (error) {
          throw new Error(`Failed to import ${importPath}: ${error.message}`);
        }
      }
      
      this.testResults.dependencies.passed = true;
      console.log('✅ All dependencies are available');
    } catch (error) {
      this.testResults.dependencies.errors.push(error.message);
      console.log('❌ Dependency test failed:', error.message);
    }
    
    console.log();
  }

  /**
   * Test API connectivity
   */
  async testApiConnectivity() {
    console.log('🌐 Testing API Connectivity...');
    
    try {
      // Test Twitter API
      if (process.env.TWITTER_BEARER_TOKEN) {
        const response = await fetch('https://api.twitter.com/2/tweets/search/recent?query=test&max_results=10', {
          headers: {
            'Authorization': `Bearer ${process.env.TWITTER_BEARER_TOKEN}`
          }
        });
        
        if (response.ok) {
          console.log('✅ Twitter API connection successful');
        } else {
          throw new Error(`Twitter API returned ${response.status}: ${response.statusText}`);
        }
      } else {
        console.log('⚠️  Twitter Bearer Token not set, skipping API test');
      }
      
      // Test GitHub API
      if (process.env.GITHUB_TOKEN) {
        const response = await fetch('https://api.github.com/user', {
          headers: {
            'Authorization': `token ${process.env.GITHUB_TOKEN}`,
            'User-Agent': 'Twitter-Crypto-Automation'
          }
        });
        
        if (response.ok) {
          console.log('✅ GitHub API connection successful');
        } else {
          throw new Error(`GitHub API returned ${response.status}: ${response.statusText}`);
        }
      } else {
        console.log('⚠️  GitHub Token not set, skipping API test');
      }
      
      this.testResults.apiConnectivity.passed = true;
    } catch (error) {
      this.testResults.apiConnectivity.errors.push(error.message);
      console.log('❌ API connectivity test failed:', error.message);
    }
    
    console.log();
  }

  /**
   * Test file system operations
   */
  async testFileSystem() {
    console.log('📁 Testing File System Operations...');
    
    try {
      // Create temp directory
      await fs.ensureDir(this.tempDir);
      
      // Test file creation
      const testFile = path.join(this.tempDir, 'test-article.md');
      const testContent = `+++
date = '2025-08-16T10:00:00Z'
title = 'Test Article'
description = 'Test description'
tags = ['test']
categories = ['测试']
+++

# Test Content

This is a test article.
`;
      
      await fs.writeFile(testFile, testContent);
      
      // Test file reading
      const readContent = await fs.readFile(testFile, 'utf8');
      if (readContent !== testContent) {
        throw new Error('File content mismatch');
      }
      
      // Test directory operations
      const testDir = path.join(this.tempDir, 'posts');
      await fs.ensureDir(testDir);
      
      // Test file moving
      const newPath = path.join(testDir, 'moved-article.md');
      await fs.move(testFile, newPath);
      
      if (!await fs.pathExists(newPath)) {
        throw new Error('File move operation failed');
      }
      
      this.testResults.fileSystem.passed = true;
      console.log('✅ File system operations successful');
    } catch (error) {
      this.testResults.fileSystem.errors.push(error.message);
      console.log('❌ File system test failed:', error.message);
    }
    
    console.log();
  }

  /**
   * Test Hugo installation and build
   */
  async testHugo() {
    console.log('🏗️  Testing Hugo...');
    
    try {
      // Check if Hugo is available
      try {
        const version = execSync('hugo version', { encoding: 'utf8' });
        console.log(`✅ Hugo found: ${version.trim()}`);
      } catch (error) {
        // Try to install Hugo for testing
        console.log('⚠️  Hugo not found, attempting to install...');
        
        if (process.platform === 'linux') {
          execSync('wget -O hugo.tar.gz https://github.com/gohugoio/hugo/releases/download/v0.119.0/hugo_extended_0.119.0_Linux-64bit.tar.gz', { stdio: 'inherit' });
          execSync('tar -xzf hugo.tar.gz', { stdio: 'inherit' });
          execSync('sudo mv hugo /usr/local/bin/', { stdio: 'inherit' });
          execSync('rm hugo.tar.gz', { stdio: 'inherit' });
        } else {
          throw new Error('Hugo installation not supported on this platform for testing');
        }
      }
      
      // Test Hugo build in temp directory
      const hugoTestDir = path.join(this.tempDir, 'hugo-test');
      await fs.ensureDir(hugoTestDir);
      
      // Create minimal Hugo site structure
      await fs.ensureDir(path.join(hugoTestDir, 'content', 'posts'));
      await fs.ensureDir(path.join(hugoTestDir, 'layouts', '_default'));
      
      // Create basic config
      await fs.writeFile(path.join(hugoTestDir, 'hugo.toml'), `
baseURL = 'https://example.org'
languageCode = 'en-us'
title = 'Test Site'
`);
      
      // Create basic layout
      await fs.writeFile(path.join(hugoTestDir, 'layouts', '_default', 'baseof.html'), `
<!DOCTYPE html>
<html>
<head>
  <title>{{ .Title }}</title>
</head>
<body>
  {{ block "main" . }}{{ end }}
</body>
</html>
`);
      
      await fs.writeFile(path.join(hugoTestDir, 'layouts', '_default', 'single.html'), `
{{ define "main" }}
<h1>{{ .Title }}</h1>
{{ .Content }}
{{ end }}
`);
      
      // Create test content
      await fs.writeFile(path.join(hugoTestDir, 'content', 'posts', 'test.md'), `+++
title = 'Test Post'
date = '2025-08-16T10:00:00Z'
+++

# Test Content
`);
      
      // Test Hugo build
      execSync('hugo --minify', { 
        cwd: hugoTestDir, 
        stdio: 'inherit' 
      });
      
      // Check if public directory was created
      const publicDir = path.join(hugoTestDir, 'public');
      if (!await fs.pathExists(publicDir)) {
        throw new Error('Hugo build did not create public directory');
      }
      
      this.testResults.hugo.passed = true;
      console.log('✅ Hugo build successful');
    } catch (error) {
      this.testResults.hugo.errors.push(error.message);
      console.log('❌ Hugo test failed:', error.message);
    }
    
    console.log();
  }

  /**
   * Test GitHub operations
   */
  async testGitHub() {
    console.log('🐙 Testing GitHub Operations...');
    
    try {
      // Check git configuration
      try {
        const gitUser = execSync('git config user.name', { encoding: 'utf8' }).trim();
        const gitEmail = execSync('git config user.email', { encoding: 'utf8' }).trim();
        console.log(`✅ Git configured: ${gitUser} <${gitEmail}>`);
      } catch (error) {
        throw new Error('Git not configured properly');
      }
      
      // Check if we're in a git repository
      try {
        execSync('git status', { stdio: 'ignore' });
        console.log('✅ In a git repository');
      } catch (error) {
        throw new Error('Not in a git repository');
      }
      
      // Test GitHub CLI if available
      try {
        execSync('gh --version', { stdio: 'ignore' });
        execSync('gh auth status', { stdio: 'ignore' });
        console.log('✅ GitHub CLI authenticated');
      } catch (error) {
        console.log('⚠️  GitHub CLI not available or not authenticated');
      }
      
      this.testResults.github.passed = true;
    } catch (error) {
      this.testResults.github.errors.push(error.message);
      console.log('❌ GitHub test failed:', error.message);
    }
    
    console.log();
  }

  /**
   * Test end-to-end workflow (simplified)
   */
  async testEndToEnd() {
    console.log('🔄 Testing End-to-End Workflow...');
    
    try {
      // Only run if all previous tests passed
      const criticalTests = ['configuration', 'environment', 'dependencies'];
      const criticalPassed = criticalTests.every(test => this.testResults[test].passed);
      
      if (!criticalPassed) {
        throw new Error('Critical tests failed, skipping end-to-end test');
      }
      
      // Import and test main components
      const { default: ConfigLoader } = await import('../src/config/ConfigLoader.js');
      const { default: TwitterClient } = await import('../src/clients/TwitterClient.js');
      
      // Load configuration
      const configLoader = new ConfigLoader();
      const config = await configLoader.load();
      
      // Test Twitter client initialization
      const twitterClient = new TwitterClient(config.twitter);
      
      // Test a simple search (if API key available)
      if (process.env.TWITTER_BEARER_TOKEN) {
        console.log('🔍 Testing Twitter search...');
        const tweets = await twitterClient.searchTweets(['test'], 5);
        console.log(`✅ Found ${tweets.length} tweets`);
      }
      
      this.testResults.endToEnd.passed = true;
      console.log('✅ End-to-end test successful');
    } catch (error) {
      this.testResults.endToEnd.errors.push(error.message);
      console.log('❌ End-to-end test failed:', error.message);
    }
    
    console.log();
  }

  /**
   * Clean up temporary files
   */
  async cleanup() {
    try {
      if (await fs.pathExists(this.tempDir)) {
        await fs.remove(this.tempDir);
        console.log('🧹 Cleaned up temporary files');
      }
    } catch (error) {
      console.warn('⚠️  Could not clean up temporary files:', error.message);
    }
  }

  /**
   * Generate and display test report
   */
  generateReport() {
    console.log('\n' + '='.repeat(60));
    console.log('📊 DEPLOYMENT TEST REPORT');
    console.log('='.repeat(60));
    
    let totalTests = 0;
    let passedTests = 0;
    
    for (const [testName, result] of Object.entries(this.testResults)) {
      totalTests++;
      const status = result.passed ? '✅ PASS' : '❌ FAIL';
      console.log(`${status} ${testName.toUpperCase()}`);
      
      if (result.passed) {
        passedTests++;
      } else if (result.errors.length > 0) {
        result.errors.forEach(error => {
          console.log(`     • ${error}`);
        });
      }
    }
    
    console.log('='.repeat(60));
    console.log(`📈 SUMMARY: ${passedTests}/${totalTests} tests passed`);
    
    if (passedTests === totalTests) {
      console.log('🎉 All tests passed! Deployment is ready.');
    } else {
      console.log('⚠️  Some tests failed. Please address the issues before deployment.');
    }
    
    console.log('='.repeat(60));
    
    // Return overall status
    return passedTests === totalTests;
  }
}

// CLI interface
if (import.meta.url === `file://${process.argv[1]}`) {
  const tester = new DeploymentTester();
  const success = await tester.runAllTests();
  process.exit(success ? 0 : 1);
}

export default DeploymentTester;