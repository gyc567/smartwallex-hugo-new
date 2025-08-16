/**
 * Configuration Validator
 * Validates configuration files and environment variables
 */

class ConfigValidator {
  constructor() {
    this.requiredEnvVars = [
      'TWITTER_BEARER_TOKEN',
      'GITHUB_TOKEN',
      'GITHUB_REPOSITORY'
    ];

    this.optionalEnvVars = [
      'TWITTER_API_KEY',
      'TWITTER_API_SECRET',
      'GOOGLE_TRANSLATE_API_KEY',
      'AZURE_TRANSLATOR_KEY',
      'SLACK_WEBHOOK_URL',
      'EMAIL_SMTP_HOST',
      'EMAIL_USER',
      'EMAIL_PASS',
      'EMAIL_TO'
    ];

    this.configSchema = {
      twitter: {
        required: ['apiVersion', 'baseUrl', 'searchEndpoint', 'maxResults', 'searchKeywords'],
        types: {
          apiVersion: 'string',
          baseUrl: 'string',
          searchEndpoint: 'string',
          maxResults: 'number',
          searchKeywords: 'array'
        }
      },
      content: {
        required: ['topTweetsCount', 'minRetweetCount', 'targetLanguage'],
        types: {
          topTweetsCount: 'number',
          minRetweetCount: 'number',
          minCharacterCount: 'number',
          targetLanguage: 'string',
          enhanceContent: 'boolean'
        }
      },
      hugo: {
        required: ['contentPath', 'buildCommand'],
        types: {
          contentPath: 'string',
          templatePath: 'string',
          buildCommand: 'string',
          outputDir: 'string',
          baseUrl: 'string'
        }
      },
      github: {
        required: ['repository', 'branch', 'contentPath'],
        types: {
          repository: 'string',
          branch: 'string',
          contentPath: 'string',
          commitMessage: 'string'
        }
      }
    };
  }

  /**
   * Validate environment variables
   * @returns {Object} Validation result
   */
  validateEnvironment() {
    const errors = [];
    const warnings = [];
    const missing = [];

    // Check required environment variables
    for (const envVar of this.requiredEnvVars) {
      if (!process.env[envVar]) {
        missing.push(envVar);
        errors.push(`Missing required environment variable: ${envVar}`);
      } else if (process.env[envVar].trim() === '') {
        errors.push(`Environment variable ${envVar} is empty`);
      }
    }

    // Check optional environment variables
    for (const envVar of this.optionalEnvVars) {
      if (!process.env[envVar]) {
        warnings.push(`Optional environment variable not set: ${envVar}`);
      }
    }

    // Validate specific formats
    if (process.env.GITHUB_REPOSITORY && !this.isValidGitHubRepo(process.env.GITHUB_REPOSITORY)) {
      errors.push('GITHUB_REPOSITORY must be in format "username/repository"');
    }

    if (process.env.TWITTER_BEARER_TOKEN && !this.isValidBearerToken(process.env.TWITTER_BEARER_TOKEN)) {
      errors.push('TWITTER_BEARER_TOKEN appears to be invalid format');
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings,
      missing,
      summary: {
        requiredFound: this.requiredEnvVars.length - missing.length,
        requiredTotal: this.requiredEnvVars.length,
        optionalFound: this.optionalEnvVars.filter(v => process.env[v]).length,
        optionalTotal: this.optionalEnvVars.length
      }
    };
  }

  /**
   * Validate configuration object
   * @param {Object} config - Configuration object to validate
   * @returns {Object} Validation result
   */
  validateConfig(config) {
    const errors = [];
    const warnings = [];

    if (!config || typeof config !== 'object') {
      return {
        valid: false,
        errors: ['Configuration must be a valid object'],
        warnings: []
      };
    }

    // Validate each section
    for (const [section, schema] of Object.entries(this.configSchema)) {
      if (!config[section]) {
        errors.push(`Missing configuration section: ${section}`);
        continue;
      }

      // Check required fields
      for (const field of schema.required) {
        if (config[section][field] === undefined || config[section][field] === null) {
          errors.push(`Missing required field: ${section}.${field}`);
        }
      }

      // Check field types
      for (const [field, expectedType] of Object.entries(schema.types)) {
        if (config[section][field] !== undefined) {
          const actualType = this.getType(config[section][field]);
          if (actualType !== expectedType) {
            errors.push(`Invalid type for ${section}.${field}: expected ${expectedType}, got ${actualType}`);
          }
        }
      }
    }

    // Validate specific business rules
    this.validateBusinessRules(config, errors, warnings);

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Validate business-specific rules
   * @param {Object} config - Configuration object
   * @param {Array} errors - Errors array to populate
   * @param {Array} warnings - Warnings array to populate
   */
  validateBusinessRules(config, errors, warnings) {
    // Twitter configuration validation
    if (config.twitter) {
      if (config.twitter.maxResults > 100) {
        warnings.push('Twitter maxResults > 100 may hit rate limits quickly');
      }
      
      if (config.twitter.searchKeywords && config.twitter.searchKeywords.length === 0) {
        errors.push('At least one search keyword is required');
      }
    }

    // Content configuration validation
    if (config.content) {
      if (config.content.topTweetsCount > 10) {
        warnings.push('Processing more than 10 tweets may be slow');
      }
      
      if (config.content.minRetweetCount < 1) {
        warnings.push('Very low minRetweetCount may include low-quality content');
      }
    }

    // Hugo configuration validation
    if (config.hugo) {
      if (config.hugo.contentPath && !config.hugo.contentPath.includes('content')) {
        warnings.push('Hugo contentPath should typically include "content" directory');
      }
    }

    // GitHub configuration validation
    if (config.github) {
      if (config.github.repository && !this.isValidGitHubRepo(config.github.repository)) {
        errors.push('GitHub repository must be in format "username/repository"');
      }
    }
  }

  /**
   * Get the type of a value
   * @param {*} value - Value to check
   * @returns {string} Type name
   */
  getType(value) {
    if (Array.isArray(value)) return 'array';
    if (value === null) return 'null';
    return typeof value;
  }

  /**
   * Validate GitHub repository format
   * @param {string} repo - Repository string
   * @returns {boolean} Is valid
   */
  isValidGitHubRepo(repo) {
    return /^[a-zA-Z0-9._-]+\/[a-zA-Z0-9._-]+$/.test(repo);
  }

  /**
   * Validate Twitter Bearer Token format
   * @param {string} token - Bearer token
   * @returns {boolean} Is valid format
   */
  isValidBearerToken(token) {
    // Basic validation - should be a long alphanumeric string
    return /^[A-Za-z0-9%_-]{100,}$/.test(token);
  }

  /**
   * Generate validation report
   * @param {Object} envResult - Environment validation result
   * @param {Object} configResult - Config validation result
   * @returns {string} Formatted report
   */
  generateReport(envResult, configResult) {
    let report = '=== Configuration Validation Report ===\n\n';

    // Environment Variables Section
    report += '📋 Environment Variables:\n';
    report += `✅ Required: ${envResult.summary.requiredFound}/${envResult.summary.requiredTotal}\n`;
    report += `⚠️  Optional: ${envResult.summary.optionalFound}/${envResult.summary.optionalTotal}\n\n`;

    if (envResult.errors.length > 0) {
      report += '❌ Environment Errors:\n';
      envResult.errors.forEach(error => {
        report += `   • ${error}\n`;
      });
      report += '\n';
    }

    if (envResult.warnings.length > 0) {
      report += '⚠️  Environment Warnings:\n';
      envResult.warnings.forEach(warning => {
        report += `   • ${warning}\n`;
      });
      report += '\n';
    }

    // Configuration Section
    report += '⚙️  Configuration:\n';
    report += `Status: ${configResult.valid ? '✅ Valid' : '❌ Invalid'}\n\n`;

    if (configResult.errors.length > 0) {
      report += '❌ Configuration Errors:\n';
      configResult.errors.forEach(error => {
        report += `   • ${error}\n`;
      });
      report += '\n';
    }

    if (configResult.warnings.length > 0) {
      report += '⚠️  Configuration Warnings:\n';
      configResult.warnings.forEach(warning => {
        report += `   • ${warning}\n`;
      });
      report += '\n';
    }

    // Overall Status
    const overallValid = envResult.valid && configResult.valid;
    report += `🎯 Overall Status: ${overallValid ? '✅ Ready for deployment' : '❌ Issues need to be resolved'}\n`;

    return report;
  }
}

export default ConfigValidator;