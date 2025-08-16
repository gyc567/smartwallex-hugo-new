import fs from 'fs-extra';
import path from 'path';
import { fileURLToPath } from 'url';
import ConfigValidator from './ConfigValidator.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Configuration loader that merges default, environment-specific, and environment variable configs
 */
class ConfigLoader {
  constructor() {
    this.config = null;
    this.configDir = path.join(__dirname, '../../config');
    this.validator = new ConfigValidator();
  }

  /**
   * Load configuration based on NODE_ENV
   * @param {boolean} validate - Whether to validate configuration (default: true)
   * @returns {Object} Merged configuration object
   */
  async load(validate = true) {
    if (this.config) {
      return this.config;
    }

    const env = process.env.NODE_ENV || 'development';
    
    // Load default configuration
    const defaultConfig = await this.loadConfigFile('default.json');
    
    // Load environment-specific configuration
    const envConfig = await this.loadConfigFile(`${env}.json`);
    
    // Merge configurations (env overrides default)
    this.config = this.mergeConfigs(defaultConfig, envConfig);
    
    // Override with environment variables
    this.applyEnvironmentVariables();
    
    // Validate configuration if requested
    if (validate) {
      const validationResult = this.validateConfiguration();
      if (!validationResult.valid) {
        throw new Error(`Configuration validation failed:\n${validationResult.report}`);
      }
    }
    
    return this.config;
  }

  /**
   * Load a configuration file
   * @param {string} filename - Configuration file name
   * @returns {Object} Configuration object
   */
  async loadConfigFile(filename) {
    const filePath = path.join(this.configDir, filename);
    
    try {
      if (await fs.pathExists(filePath)) {
        const content = await fs.readJson(filePath);
        return content;
      }
    } catch (error) {
      console.warn(`Warning: Could not load config file ${filename}:`, error.message);
    }
    
    return {};
  }

  /**
   * Deep merge configuration objects
   * @param {Object} target - Target configuration
   * @param {Object} source - Source configuration to merge
   * @returns {Object} Merged configuration
   */
  mergeConfigs(target, source) {
    const result = { ...target };
    
    for (const key in source) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        result[key] = this.mergeConfigs(result[key] || {}, source[key]);
      } else {
        result[key] = source[key];
      }
    }
    
    return result;
  }

  /**
   * Apply environment variable overrides
   */
  applyEnvironmentVariables() {
    // Twitter configuration
    if (process.env.TWITTER_BEARER_TOKEN) {
      this.config.twitter.bearerToken = process.env.TWITTER_BEARER_TOKEN;
    }
    if (process.env.TWITTER_API_KEY) {
      this.config.twitter.apiKey = process.env.TWITTER_API_KEY;
    }
    if (process.env.TWITTER_API_SECRET) {
      this.config.twitter.apiSecret = process.env.TWITTER_API_SECRET;
    }

    // GitHub configuration
    if (process.env.GITHUB_TOKEN) {
      this.config.github.token = process.env.GITHUB_TOKEN;
    }
    if (process.env.GITHUB_REPOSITORY) {
      this.config.github.repository = process.env.GITHUB_REPOSITORY;
    }

    // Translation services
    if (process.env.GOOGLE_TRANSLATE_API_KEY) {
      this.config.translation = this.config.translation || {};
      this.config.translation.googleApiKey = process.env.GOOGLE_TRANSLATE_API_KEY;
    }
    if (process.env.AZURE_TRANSLATOR_KEY) {
      this.config.translation = this.config.translation || {};
      this.config.translation.azureKey = process.env.AZURE_TRANSLATOR_KEY;
    }

    // Notification settings
    if (process.env.SLACK_WEBHOOK_URL) {
      this.config.notifications = this.config.notifications || {};
      this.config.notifications.slackWebhook = process.env.SLACK_WEBHOOK_URL;
    }
  }

  /**
   * Validate current configuration
   * @returns {Object} Validation result with report
   */
  validateConfiguration() {
    const envResult = this.validator.validateEnvironment();
    const configResult = this.validator.validateConfig(this.config);
    const report = this.validator.generateReport(envResult, configResult);
    
    return {
      valid: envResult.valid && configResult.valid,
      environment: envResult,
      configuration: configResult,
      report
    };
  }

  /**
   * Get validation report without throwing errors
   * @returns {string} Formatted validation report
   */
  getValidationReport() {
    try {
      const result = this.validateConfiguration();
      return result.report;
    } catch (error) {
      return `❌ Configuration validation error: ${error.message}`;
    }
  }

  /**
   * Check if configuration is ready for production
   * @returns {boolean} True if ready for production
   */
  isProductionReady() {
    try {
      const result = this.validateConfiguration();
      return result.valid && result.environment.missing.length === 0;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get a configuration value by dot notation path
   * @param {string} path - Dot notation path (e.g., 'twitter.maxResults')
   * @param {*} defaultValue - Default value if path not found
   * @returns {*} Configuration value
   */
  get(path, defaultValue = null) {
    if (!this.config) {
      throw new Error('Configuration not loaded. Call load() first.');
    }

    const keys = path.split('.');
    let value = this.config;

    for (const key of keys) {
      if (value && typeof value === 'object' && key in value) {
        value = value[key];
      } else {
        return defaultValue;
      }
    }

    return value;
  }
}

// Export singleton instance
export default new ConfigLoader();