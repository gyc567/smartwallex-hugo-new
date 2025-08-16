import fs from 'fs/promises';
import path from 'path';

/**
 * FileWriter class for markdown file creation and management
 * Handles saving articles to Hugo content directory with proper naming conventions
 */
class FileWriter {
  constructor(contentDir = 'content/posts') {
    this.contentDir = contentDir;
  }

  /**
   * Write article file to /content/posts directory
   * @param {string} content - The markdown content to write
   * @param {string} filename - The filename to use
   * @returns {Promise<string>} - The full path of the written file
   */
  async writeArticleFile(content, filename) {
    try {
      // Ensure the content directory exists
      await this.ensureDirectoryExists(this.contentDir);
      
      // Create full file path
      const filePath = path.join(this.contentDir, filename);
      
      // Write the file
      await fs.writeFile(filePath, content, 'utf8');
      
      console.log(`Article written successfully: ${filePath}`);
      return filePath;
    } catch (error) {
      console.error(`Error writing article file: ${error.message}`);
      throw error;
    }
  }

  /**
   * Generate descriptive filename with naming convention
   * Format: crypto-twitter-{topic}-{YYYYMMDD}-{sequence}.md
   * @param {string} title - The article title
   * @param {Date} date - The publication date
   * @param {number} sequence - Sequence number for the day (default: 1)
   * @returns {string} - Generated filename
   */
  generateFilename(title, date = new Date(), sequence = 1) {
    try {
      // Extract topic from title (first few meaningful words)
      const topic = this.extractTopicFromTitle(title);
      
      // Format date as YYYYMMDD
      const dateStr = date.toISOString().slice(0, 10).replace(/-/g, '');
      
      // Format sequence with leading zeros
      const sequenceStr = sequence.toString().padStart(3, '0');
      
      // Create filename
      const filename = `crypto-twitter-${topic}-${dateStr}-${sequenceStr}.md`;
      
      return filename;
    } catch (error) {
      console.error(`Error generating filename: ${error.message}`);
      // Fallback filename
      const timestamp = Date.now();
      return `crypto-twitter-article-${timestamp}.md`;
    }
  }

  /**
   * Extract topic from title for filename
   * @param {string} title - The article title
   * @returns {string} - Extracted topic in kebab-case
   */
  extractTopicFromTitle(title) {
    if (!title || typeof title !== 'string') {
      return 'analysis';
    }
    
    // Remove common Chinese characters and extract meaningful words
    const cleanTitle = title
      .replace(/[：:：，,。！!？?]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
    
    // Extract first few meaningful words (up to 3)
    const words = cleanTitle.split(' ').slice(0, 3);
    
    // Convert to kebab-case and limit length
    let topic = words
      .join('-')
      .toLowerCase()
      .replace(/[^a-z0-9\u4e00-\u9fff-]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');
    
    // Limit topic length and ensure it's not empty
    if (topic.length > 30) {
      topic = topic.substring(0, 30).replace(/-[^-]*$/, '');
    }
    
    return topic || 'analysis';
  }

  /**
   * Ensure directory exists, create if it doesn't
   * @param {string} dirPath - Directory path to ensure
   */
  async ensureDirectoryExists(dirPath) {
    try {
      await fs.access(dirPath);
    } catch (error) {
      if (error.code === 'ENOENT') {
        await fs.mkdir(dirPath, { recursive: true });
        console.log(`Created directory: ${dirPath}`);
      } else {
        throw error;
      }
    }
  }

  /**
   * Check if file already exists
   * @param {string} filename - Filename to check
   * @returns {Promise<boolean>} - True if file exists
   */
  async fileExists(filename) {
    try {
      const filePath = path.join(this.contentDir, filename);
      await fs.access(filePath);
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get next available sequence number for a given date and topic
   * @param {string} baseTopic - Base topic for the filename
   * @param {Date} date - Date for the filename
   * @returns {Promise<number>} - Next available sequence number
   */
  async getNextSequenceNumber(baseTopic, date = new Date()) {
    try {
      const dateStr = date.toISOString().slice(0, 10).replace(/-/g, '');
      const pattern = `crypto-twitter-${baseTopic}-${dateStr}-`;
      
      // Read directory contents
      const files = await fs.readdir(this.contentDir);
      
      // Find files matching the pattern
      const matchingFiles = files.filter(file => file.startsWith(pattern));
      
      if (matchingFiles.length === 0) {
        return 1;
      }
      
      // Extract sequence numbers and find the highest
      const sequences = matchingFiles
        .map(file => {
          const match = file.match(/-(\d{3})\.md$/);
          return match ? parseInt(match[1], 10) : 0;
        })
        .filter(seq => seq > 0);
      
      return sequences.length > 0 ? Math.max(...sequences) + 1 : 1;
    } catch (error) {
      console.error(`Error getting next sequence number: ${error.message}`);
      return 1;
    }
  }

  /**
   * Generate unique filename by checking for existing files
   * @param {string} title - Article title
   * @param {Date} date - Publication date
   * @returns {Promise<string>} - Unique filename
   */
  async generateUniqueFilename(title, date = new Date()) {
    // Ensure directory exists before checking for files
    await this.ensureDirectoryExists(this.contentDir);
    
    const topic = this.extractTopicFromTitle(title);
    const sequence = await this.getNextSequenceNumber(topic, date);
    return this.generateFilename(title, date, sequence);
  }

  /**
   * Validate file content for Hugo compatibility
   * @param {string} content - Markdown content to validate
   * @returns {boolean} - True if content is valid
   */
  validateFileContent(content) {
    try {
      // Check for required front matter
      if (!content.startsWith('+++')) {
        console.warn('Content missing TOML front matter');
        return false;
      }
      
      // Check for closing front matter
      const frontMatterEnd = content.indexOf('+++', 3);
      if (frontMatterEnd === -1) {
        console.warn('Content missing closing front matter delimiter');
        return false;
      }
      
      // Extract front matter
      const frontMatter = content.substring(3, frontMatterEnd);
      
      // Check for required fields
      const requiredFields = ['title', 'date', 'draft'];
      for (const field of requiredFields) {
        if (!frontMatter.includes(`${field} =`)) {
          console.warn(`Content missing required field: ${field}`);
          return false;
        }
      }
      
      return true;
    } catch (error) {
      console.error(`Error validating content: ${error.message}`);
      return false;
    }
  }
}

export default FileWriter;