#!/usr/bin/env node

/**
 * Setup Validation Script
 * Comprehensive validation of the entire system setup
 */

import fs from 'fs-extra';
import path from 'path';
import ConfigLoader from '../src/config/ConfigLoader.js';
import ConfigValidator from '../src/config/ConfigValidator.js';

class SetupValidator {
  constructor() {
    this.results = {
      files: { passed: false, issues: [] },
      configuration: { passed: false, issues: [] },
      environment: { passed: false, issues: [] },
      dependencies: { passed: false, issues: [] },
      github: { passed: false, issues: [] }
    };
  }

  /**
   * Run all validation checks
   */
  async validate() {
    console.log('🔍 Validating Twitter Crypto Content Automation Setup\n');

    await this.validateFiles();
    await this.validateConfiguration();
    await this.validateEnvironment();
    await this.validateDependencies();
    await this.validateGitHub();

    this.generateReport();
    return this.isValid();
  }

  /**
   * Validate required files exist
   */
  async validateFiles() {
    console.log('📁 Validating Files...');

    const requiredFiles = [
      'package.json',
      'src/index.js',
      'src/config/ConfigLoader.js',
      'src/config/ConfigValidator.js',
      'src/clients/TwitterClient.js',
      'src/generators/ArticleGenerator.js',
      'config/default.json',
      'config/production.json',
      '.env.example',
      '../.github/workflows/twitter-automation.yml',
      '../md-template.md'
    ];

    const requiredDirectories = [
      'src',
      'config',
      'tests',
      'docs',
      'scripts',
      '../content/posts'
    ];

    let allFilesExist = true;

    // Check files
    for (const file of requiredFiles) {
      const filePath = path.resolve(file);
      if (await fs.pathExists(filePath)) {
        console.log(`✅ ${file}`);
      } else {
        console.log(`❌ ${file} - Missing`);
        this.results.files.issues.push(`Missing file: ${file}`);
        allFilesExist = false;
      }
    }

    // Check directories
    for (const dir of requiredDirectories) {
      const dirPath = path.resolve(dir);
      if (await fs.pathExists(dirPath)) {
        console.log(`✅ ${dir}/`);
      } else {
        console.log(`❌ ${dir}/ - Missing directory`);
        this.results.files.issues.push(`Missing directory: ${dir}`);
        allFilesExist = false;
      }
    }

    this.results.files.passed = allFilesExist;
    console.log();
  }

  /**
   * Validate configuration files
   */
  async validateConfiguration() {
    console.log('⚙️  Validating Configuration...');

    try {
      // Test configuration loading
      const configLoader = new ConfigLoader();
      const config = await configLoader.load(false);

      // Validate configuration structure
      const validator = new ConfigValidator();
      const result = validator.validateConfig(config);

      if (result.valid) {
        console.log('✅ Configuration is valid');
        this.results.configuration.passed = true;
      } else {
        console.log('❌ Configuration validation failed');
        this.results.configuration.issues = result.errors;
        result.errors.forEach(error => console.log(`   • ${error}`));
      }

      // Check specific configuration values
      this.validateConfigurationValues(config);

    } catch (error) {
      console.log('❌ Configuration loading failed:', error.message);
      this.results.configuration.issues.push(`Configuration error: ${error.message}`);
    }

    console.log();
  }

  /**
   * Validate specific configuration values
   */
  validateConfigurationValues(config) {
    // Check Twitter configuration
    if (config.twitter) {
      if (!config.twitter.searchKeywords || config.twitter.searchKeywords.length === 0) {
        this.results.configuration.issues.push('No Twitter search keywords configured');
      }
      
      if (config.twitter.maxResults > 100) {
        console.log('⚠️  Twitter maxResults > 100 may hit rate limits');
      }
    }

    // Check Hugo configuration
    if (config.hugo) {
      if (!config.hugo.contentPath) {
        this.results.configuration.issues.push('Hugo content path not configured');
      }
      
      if (!config.hugo.buildCommand) {
        this.results.configuration.issues.push('Hugo build command not configured');
      }
    }

    // Check GitHub configuration
    if (config.github) {
      if (!config.github.repository) {
        this.results.configuration.issues.push('GitHub repository not configured');
      }
    }
  }

  /**
   * Validate environment variables
   */
  async validateEnvironment() {
    console.log('🔐 Validating Environment...');

    try {
      const validator = new ConfigValidator();
      const result = validator.validateEnvironment();

      if (result.valid) {
        console.log('✅ All required environment variables are set');
        this.results.environment.passed = true;
      } else {
        console.log('❌ Environment validation failed');
        this.results.environment.issues = result.errors;
        result.errors.forEach(error => console.log(`   • ${error}`));
      }

      // Show summary
      console.log(`📊 Environment Summary:`);
      console.log(`   Required: ${result.summary.requiredFound}/${result.summary.requiredTotal}`);
      console.log(`   Optional: ${result.summary.optionalFound}/${result.summary.optionalTotal}`);

      if (result.warnings.length > 0) {
        console.log('⚠️  Warnings:');
        result.warnings.forEach(warning => console.log(`   • ${warning}`));
      }

    } catch (error) {
      console.log('❌ Environment validation failed:', error.message);
      this.results.environment.issues.push(`Environment error: ${error.message}`);
    }

    console.log();
  }

  /**
   * Validate dependencies
   */
  async validateDependencies() {
    console.log('📦 Validating Dependencies...');

    try {
      // Check package.json
      const packagePath = path.resolve('package.json');
      if (!await fs.pathExists(packagePath)) {
        throw new Error('package.json not found');
      }

      const packageJson = await fs.readJson(packagePath);
      
      // Check node_modules
      const nodeModulesPath = path.resolve('node_modules');
      if (!await fs.pathExists(nodeModulesPath)) {
        console.log('❌ node_modules not found - run npm install');
        this.results.dependencies.issues.push('Dependencies not installed');
        return;
      }

      // Check key dependencies
      const keyDependencies = ['axios', 'fs-extra', 'dotenv'];
      for (const dep of keyDependencies) {
        const depPath = path.resolve('node_modules', dep);
        if (await fs.pathExists(depPath)) {
          console.log(`✅ ${dep}`);
        } else {
          console.log(`❌ ${dep} - Not installed`);
          this.results.dependencies.issues.push(`Missing dependency: ${dep}`);
        }
      }

      // Test imports
      try {
        await import('../src/config/ConfigLoader.js');
        await import('../src/clients/TwitterClient.js');
        console.log('✅ Module imports successful');
        this.results.dependencies.passed = this.results.dependencies.issues.length === 0;
      } catch (error) {
        console.log('❌ Module import failed:', error.message);
        this.results.dependencies.issues.push(`Import error: ${error.message}`);
      }

    } catch (error) {
      console.log('❌ Dependency validation failed:', error.message);
      this.results.dependencies.issues.push(`Dependency error: ${error.message}`);
    }

    console.log();
  }

  /**
   * Validate GitHub setup
   */
  async validateGitHub() {
    console.log('🐙 Validating GitHub Setup...');

    try {
      // Check workflow file
      const workflowPath = path.resolve('../.github/workflows/twitter-automation.yml');
      if (await fs.pathExists(workflowPath)) {
        console.log('✅ GitHub Actions workflow file exists');
      } else {
        console.log('❌ GitHub Actions workflow file missing');
        this.results.github.issues.push('Workflow file missing');
      }

      // Check if in git repository
      const gitPath = path.resolve('../.git');
      if (await fs.pathExists(gitPath)) {
        console.log('✅ In a git repository');
      } else {
        console.log('❌ Not in a git repository');
        this.results.github.issues.push('Not in a git repository');
      }

      // Check template file
      const templatePath = path.resolve('../md-template.md');
      if (await fs.pathExists(templatePath)) {
        console.log('✅ Article template exists');
      } else {
        console.log('❌ Article template missing');
        this.results.github.issues.push('Article template missing');
      }

      // Check content directory
      const contentPath = path.resolve('../content/posts');
      if (await fs.pathExists(contentPath)) {
        console.log('✅ Content posts directory exists');
      } else {
        console.log('❌ Content posts directory missing');
        this.results.github.issues.push('Content directory missing');
      }

      this.results.github.passed = this.results.github.issues.length === 0;

    } catch (error) {
      console.log('❌ GitHub validation failed:', error.message);
      this.results.github.issues.push(`GitHub error: ${error.message}`);
    }

    console.log();
  }

  /**
   * Check if overall setup is valid
   */
  isValid() {
    return Object.values(this.results).every(result => result.passed);
  }

  /**
   * Generate validation report
   */
  generateReport() {
    console.log('='.repeat(60));
    console.log('📊 SETUP VALIDATION REPORT');
    console.log('='.repeat(60));

    let totalChecks = 0;
    let passedChecks = 0;

    for (const [category, result] of Object.entries(this.results)) {
      totalChecks++;
      const status = result.passed ? '✅ PASS' : '❌ FAIL';
      console.log(`${status} ${category.toUpperCase()}`);

      if (result.passed) {
        passedChecks++;
      } else if (result.issues.length > 0) {
        result.issues.forEach(issue => {
          console.log(`     • ${issue}`);
        });
      }
    }

    console.log('='.repeat(60));
    console.log(`📈 SUMMARY: ${passedChecks}/${totalChecks} categories passed`);

    if (this.isValid()) {
      console.log('🎉 Setup validation successful! System is ready for deployment.');
      console.log('\n📋 Next Steps:');
      console.log('1. Run deployment test: npm run test:deployment');
      console.log('2. Test manually: npm run demo');
      console.log('3. Follow deployment checklist: docs/DEPLOYMENT-CHECKLIST.md');
    } else {
      console.log('⚠️  Setup validation failed. Please address the issues above.');
      console.log('\n🔧 Recommended Actions:');
      
      if (!this.results.files.passed) {
        console.log('• Ensure all required files and directories exist');
      }
      if (!this.results.configuration.passed) {
        console.log('• Fix configuration errors in config files');
      }
      if (!this.results.environment.passed) {
        console.log('• Set up required environment variables/GitHub Secrets');
      }
      if (!this.results.dependencies.passed) {
        console.log('• Run npm install to install dependencies');
      }
      if (!this.results.github.passed) {
        console.log('• Set up GitHub repository structure and workflow');
      }
    }

    console.log('='.repeat(60));
  }
}

// CLI interface
if (import.meta.url === `file://${process.argv[1]}`) {
  const validator = new SetupValidator();
  const isValid = await validator.validate();
  process.exit(isValid ? 0 : 1);
}

export default SetupValidator;