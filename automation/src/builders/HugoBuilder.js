import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs/promises';
import path from 'path';

const execAsync = promisify(exec);

/**
 * HugoBuilder class for site generation and deployment
 * Handles Hugo build commands and site optimization
 */
class HugoBuilder {
  constructor(siteRoot = '.', outputDir = 'public') {
    this.siteRoot = siteRoot;
    this.outputDir = outputDir;
    this.hugoCommand = 'hugo';
  }

  /**
   * Build Hugo site with optimization
   * @param {Object} options - Build options
   * @param {boolean} options.minify - Enable minification (default: true)
   * @param {boolean} options.gc - Enable garbage collection (default: true)
   * @param {boolean} options.cleanDestinationDir - Clean destination directory (default: true)
   * @returns {Promise<Object>} - Build result with stats
   */
  async buildSite(options = {}) {
    const {
      minify = true,
      gc = true,
      cleanDestinationDir = true
    } = options;

    try {
      console.log('Starting Hugo site build...');
      
      // Validate Hugo installation
      await this.validateHugoInstallation();
      
      // Prepare build command
      let buildCommand = this.hugoCommand;
      
      if (minify) {
        buildCommand += ' --minify';
      }
      
      if (gc) {
        buildCommand += ' --gc';
      }
      
      if (cleanDestinationDir) {
        buildCommand += ' --cleanDestinationDir';
      }
      
      // Add verbose output for debugging
      buildCommand += ' --verbose';
      
      console.log(`Executing: ${buildCommand}`);
      
      // Execute build command
      const startTime = Date.now();
      const { stdout, stderr } = await execAsync(buildCommand, {
        cwd: this.siteRoot,
        maxBuffer: 1024 * 1024 * 10 // 10MB buffer
      });
      
      const buildTime = Date.now() - startTime;
      
      // Parse build output for statistics
      const stats = this.parseBuildOutput(stdout);
      
      console.log('Hugo build completed successfully');
      console.log(`Build time: ${buildTime}ms`);
      console.log(`Pages generated: ${stats.pages}`);
      
      // Validate build output
      await this.validateBuildOutput();
      
      return {
        success: true,
        buildTime,
        stats,
        stdout,
        stderr: stderr || null
      };
      
    } catch (error) {
      console.error(`Hugo build failed: ${error.message}`);
      throw new Error(`Hugo build failed: ${error.message}`);
    }
  }

  /**
   * Validate Hugo installation and version
   * @returns {Promise<string>} - Hugo version
   */
  async validateHugoInstallation() {
    try {
      const { stdout } = await execAsync(`${this.hugoCommand} version`);
      const version = stdout.trim();
      console.log(`Hugo version: ${version}`);
      return version;
    } catch (error) {
      throw new Error(`Hugo not found or not installed. Please install Hugo first. Error: ${error.message}`);
    }
  }

  /**
   * Parse Hugo build output for statistics
   * @param {string} output - Hugo build stdout
   * @returns {Object} - Parsed statistics
   */
  parseBuildOutput(output) {
    const stats = {
      pages: 0,
      staticFiles: 0,
      processed: 0,
      duration: 0
    };

    try {
      // Extract page count - handle different formats
      const pageMatch = output.match(/(?:(\d+) pages created|Pages:\s*(\d+))/i);
      if (pageMatch) {
        stats.pages = parseInt(pageMatch[1] || pageMatch[2], 10);
      }

      // Extract static files count - handle different formats
      const staticMatch = output.match(/(?:(\d+) static files copied|Static files:\s*(\d+))/i);
      if (staticMatch) {
        stats.staticFiles = parseInt(staticMatch[1] || staticMatch[2], 10);
      }

      // Extract processing time - handle different formats
      const durationMatch = output.match(/(?:Total in (\d+) ms|Total in (\d+) ms)/i);
      if (durationMatch) {
        stats.duration = parseInt(durationMatch[1] || durationMatch[2], 10);
      }

      // Extract processed files count
      const processedMatch = output.match(/(\d+) of \d+ drafts rendered/i);
      if (processedMatch) {
        stats.processed = parseInt(processedMatch[1], 10);
      }

    } catch (error) {
      console.warn(`Error parsing build output: ${error.message}`);
    }

    return stats;
  }

  /**
   * Validate build output directory and files
   * @returns {Promise<boolean>} - True if validation passes
   */
  async validateBuildOutput() {
    try {
      const outputPath = path.join(this.siteRoot, this.outputDir);
      
      // Check if output directory exists
      await fs.access(outputPath);
      
      // Check for index.html
      const indexPath = path.join(outputPath, 'index.html');
      await fs.access(indexPath);
      
      // Check output directory contents
      const files = await fs.readdir(outputPath);
      console.log(`Build output contains ${files.length} items`);
      
      // Validate that we have essential files/directories
      const essentialItems = ['index.html'];
      const optionalItems = ['posts', 'css', 'js', 'sitemap.xml', 'robots.txt'];
      
      for (const item of essentialItems) {
        if (!files.includes(item)) {
          throw new Error(`Missing essential file/directory: ${item}`);
        }
      }
      
      console.log('Build output validation passed');
      return true;
      
    } catch (error) {
      console.error(`Build output validation failed: ${error.message}`);
      throw error;
    }
  }

  /**
   * Clean build output directory
   * @returns {Promise<void>}
   */
  async cleanBuildOutput() {
    try {
      const outputPath = path.join(this.siteRoot, this.outputDir);
      
      // Check if directory exists
      try {
        await fs.access(outputPath);
        // Directory exists, remove it
        await fs.rm(outputPath, { recursive: true, force: true });
        console.log(`Cleaned build output directory: ${outputPath}`);
      } catch (error) {
        if (error.code !== 'ENOENT') {
          throw error;
        }
        // Directory doesn't exist, nothing to clean
        console.log('Build output directory does not exist, nothing to clean');
      }
    } catch (error) {
      console.error(`Error cleaning build output: ${error.message}`);
      throw error;
    }
  }

  /**
   * Build site for development (with drafts)
   * @returns {Promise<Object>} - Build result
   */
  async buildDevelopment() {
    try {
      console.log('Building site for development...');
      
      const buildCommand = `${this.hugoCommand} --buildDrafts --buildFuture --verbose`;
      
      const startTime = Date.now();
      const { stdout, stderr } = await execAsync(buildCommand, {
        cwd: this.siteRoot,
        maxBuffer: 1024 * 1024 * 10
      });
      
      const buildTime = Date.now() - startTime;
      const stats = this.parseBuildOutput(stdout);
      
      console.log('Development build completed');
      
      return {
        success: true,
        buildTime,
        stats,
        stdout,
        stderr: stderr || null
      };
      
    } catch (error) {
      console.error(`Development build failed: ${error.message}`);
      throw error;
    }
  }

  /**
   * Start Hugo development server
   * @param {Object} options - Server options
   * @param {number} options.port - Server port (default: 1313)
   * @param {boolean} options.drafts - Include drafts (default: true)
   * @returns {Promise<Object>} - Server process info
   */
  async startDevServer(options = {}) {
    const { port = 1313, drafts = true } = options;
    
    try {
      let serverCommand = `${this.hugoCommand} server --port ${port}`;
      
      if (drafts) {
        serverCommand += ' --buildDrafts --buildFuture';
      }
      
      console.log(`Starting Hugo development server on port ${port}...`);
      console.log(`Command: ${serverCommand}`);
      
      // Note: This would start a long-running process
      // In a real implementation, you might want to return a child process
      // that can be managed separately
      
      return {
        command: serverCommand,
        port,
        url: `http://localhost:${port}`
      };
      
    } catch (error) {
      console.error(`Failed to start development server: ${error.message}`);
      throw error;
    }
  }

  /**
   * Get site configuration information
   * @returns {Promise<Object>} - Site configuration
   */
  async getSiteConfig() {
    try {
      const configPath = path.join(this.siteRoot, 'hugo.toml');
      
      // Check if config file exists
      await fs.access(configPath);
      
      const configContent = await fs.readFile(configPath, 'utf8');
      
      // Basic TOML parsing for key information
      const config = {
        baseURL: this.extractConfigValue(configContent, 'baseURL'),
        title: this.extractConfigValue(configContent, 'title'),
        languageCode: this.extractConfigValue(configContent, 'languageCode')
      };
      
      return config;
      
    } catch (error) {
      console.warn(`Could not read site configuration: ${error.message}`);
      return {};
    }
  }

  /**
   * Extract configuration value from TOML content
   * @param {string} content - TOML content
   * @param {string} key - Configuration key
   * @returns {string|null} - Configuration value
   */
  extractConfigValue(content, key) {
    try {
      const regex = new RegExp(`${key}\\s*=\\s*['"]([^'"]+)['"]`, 'i');
      const match = content.match(regex);
      return match ? match[1] : null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Check if Hugo site is properly configured
   * @returns {Promise<boolean>} - True if site is properly configured
   */
  async validateSiteConfiguration() {
    try {
      // Check for essential files
      const essentialFiles = ['hugo.toml', 'content'];
      
      for (const file of essentialFiles) {
        const filePath = path.join(this.siteRoot, file);
        await fs.access(filePath);
      }
      
      // Check content directory structure
      const contentPath = path.join(this.siteRoot, 'content');
      const contentItems = await fs.readdir(contentPath);
      
      console.log(`Site validation passed. Content items: ${contentItems.length}`);
      return true;
      
    } catch (error) {
      console.error(`Site configuration validation failed: ${error.message}`);
      return false;
    }
  }
}

export default HugoBuilder;