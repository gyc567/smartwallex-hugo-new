import { jest } from '@jest/globals';
import { beforeEach, describe, test, expect } from '@jest/globals';

// Mock fs module before importing
const mockFs = {
  writeFile: jest.fn(),
  access: jest.fn(),
  mkdir: jest.fn(),
  readdir: jest.fn()
};

jest.unstable_mockModule('fs/promises', () => ({
  default: mockFs
}));

// Import after mocking
const { default: FileWriter } = await import('../../src/utils/FileWriter.js');
const { default: path } = await import('path');

describe('FileWriter', () => {
  let fileWriter;
  const mockContentDir = 'test-content/posts';

  beforeEach(() => {
    fileWriter = new FileWriter(mockContentDir);
    jest.clearAllMocks();
  });

  describe('constructor', () => {
    test('should initialize with default content directory', () => {
      const defaultWriter = new FileWriter();
      expect(defaultWriter.contentDir).toBe('content/posts');
    });

    test('should initialize with custom content directory', () => {
      expect(fileWriter.contentDir).toBe(mockContentDir);
    });
  });

  describe('writeArticleFile', () => {
    const mockContent = '+++\ntitle = "Test"\ndate = "2025-08-14"\ndraft = false\n+++\n\nTest content';
    const mockFilename = 'test-article.md';

    test('should write article file successfully', async () => {
      mockFs.access.mockResolvedValue();
      mockFs.writeFile.mockResolvedValue();

      const result = await fileWriter.writeArticleFile(mockContent, mockFilename);

      expect(mockFs.writeFile).toHaveBeenCalledWith(
        path.join(mockContentDir, mockFilename),
        mockContent,
        'utf8'
      );
      expect(result).toBe(path.join(mockContentDir, mockFilename));
    });

    test('should create directory if it does not exist', async () => {
      mockFs.access.mockRejectedValue({ code: 'ENOENT' });
      mockFs.mkdir.mockResolvedValue();
      mockFs.writeFile.mockResolvedValue();

      await fileWriter.writeArticleFile(mockContent, mockFilename);

      expect(mockFs.mkdir).toHaveBeenCalledWith(mockContentDir, { recursive: true });
      expect(mockFs.writeFile).toHaveBeenCalled();
    });

    test('should throw error if write fails', async () => {
      mockFs.access.mockResolvedValue();
      mockFs.writeFile.mockRejectedValue(new Error('Write failed'));

      await expect(fileWriter.writeArticleFile(mockContent, mockFilename))
        .rejects.toThrow('Write failed');
    });
  });

  describe('generateFilename', () => {
    test('should generate filename with default parameters', () => {
      const title = 'Bitcoin价格分析报告';
      const date = new Date('2025-08-14T10:00:00Z');
      
      const filename = fileWriter.generateFilename(title, date);
      
      expect(filename).toMatch(/^crypto-twitter-.*-20250814-001\.md$/);
    });

    test('should generate filename with custom sequence', () => {
      const title = 'Ethereum市场动态';
      const date = new Date('2025-08-14T10:00:00Z');
      const sequence = 5;
      
      const filename = fileWriter.generateFilename(title, date, sequence);
      
      expect(filename).toMatch(/^crypto-twitter-.*-20250814-005\.md$/);
    });

    test('should handle title extraction correctly', () => {
      const title = 'DeFi协议：新兴趋势分析';
      const date = new Date('2025-08-14T10:00:00Z');
      
      const filename = fileWriter.generateFilename(title, date);
      
      expect(filename).toContain('20250814');
      expect(filename).toContain('001');
      expect(filename.endsWith('.md')).toBe(true);
    });

    test('should generate fallback filename on error', () => {
      // Pass invalid parameters to trigger error
      const filename = fileWriter.generateFilename(null);
      
      expect(filename).toMatch(/^crypto-twitter-article-\d+\.md$/);
    });
  });

  describe('extractTopicFromTitle', () => {
    test('should extract topic from Chinese title', () => {
      const title = 'Bitcoin价格分析：市场趋势报告';
      const topic = fileWriter.extractTopicFromTitle(title);
      
      expect(topic).toBe('bitcoin价格分析');
    });

    test('should extract topic from English title', () => {
      const title = 'Ethereum DeFi Protocol Analysis';
      const topic = fileWriter.extractTopicFromTitle(title);
      
      expect(topic).toBe('ethereum-defi-protocol');
    });

    test('should handle mixed language title', () => {
      const title = 'NFT Market 市场分析 Report';
      const topic = fileWriter.extractTopicFromTitle(title);
      
      expect(topic).toBe('nft-market-市场分析');
    });

    test('should limit topic length', () => {
      const longTitle = 'Very Long Title That Should Be Truncated Because It Exceeds Maximum Length';
      const topic = fileWriter.extractTopicFromTitle(longTitle);
      
      expect(topic.length).toBeLessThanOrEqual(30);
    });

    test('should return default topic for empty title', () => {
      const topic = fileWriter.extractTopicFromTitle('');
      expect(topic).toBe('analysis');
    });
  });

  describe('fileExists', () => {
    test('should return true if file exists', async () => {
      mockFs.access.mockResolvedValue();
      
      const exists = await fileWriter.fileExists('test.md');
      
      expect(exists).toBe(true);
      expect(mockFs.access).toHaveBeenCalledWith(path.join(mockContentDir, 'test.md'));
    });

    test('should return false if file does not exist', async () => {
      mockFs.access.mockRejectedValue({ code: 'ENOENT' });
      
      const exists = await fileWriter.fileExists('nonexistent.md');
      
      expect(exists).toBe(false);
    });
  });

  describe('getNextSequenceNumber', () => {
    test('should return 1 for first file of the day', async () => {
      mockFs.readdir.mockResolvedValue([]);
      
      const sequence = await fileWriter.getNextSequenceNumber('bitcoin', new Date('2025-08-14'));
      
      expect(sequence).toBe(1);
    });

    test('should return next sequence number', async () => {
      const mockFiles = [
        'crypto-twitter-bitcoin-20250814-001.md',
        'crypto-twitter-bitcoin-20250814-002.md',
        'crypto-twitter-ethereum-20250814-001.md'
      ];
      mockFs.readdir.mockResolvedValue(mockFiles);
      
      const sequence = await fileWriter.getNextSequenceNumber('bitcoin', new Date('2025-08-14'));
      
      expect(sequence).toBe(3);
    });

    test('should handle readdir error gracefully', async () => {
      mockFs.readdir.mockRejectedValue(new Error('Read error'));
      
      const sequence = await fileWriter.getNextSequenceNumber('bitcoin', new Date('2025-08-14'));
      
      expect(sequence).toBe(1);
    });
  });

  describe('generateUniqueFilename', () => {
    test('should generate unique filename', async () => {
      mockFs.readdir.mockResolvedValue([]);
      
      const filename = await fileWriter.generateUniqueFilename('Bitcoin分析', new Date('2025-08-14'));
      
      expect(filename).toMatch(/^crypto-twitter-.*-20250814-001\.md$/);
    });
  });

  describe('validateFileContent', () => {
    test('should validate correct TOML front matter', () => {
      const validContent = `+++
title = "Test Article"
date = "2025-08-14"
draft = false
+++

Article content here.`;
      
      const isValid = fileWriter.validateFileContent(validContent);
      expect(isValid).toBe(true);
    });

    test('should reject content without front matter', () => {
      const invalidContent = 'Just article content without front matter';
      
      const isValid = fileWriter.validateFileContent(invalidContent);
      expect(isValid).toBe(false);
    });

    test('should reject content with incomplete front matter', () => {
      const invalidContent = `+++
title = "Test Article"
+++

Article content here.`;
      
      const isValid = fileWriter.validateFileContent(invalidContent);
      expect(isValid).toBe(false);
    });

    test('should reject content without closing front matter', () => {
      const invalidContent = `+++
title = "Test Article"
date = "2025-08-14"
draft = false

Article content here.`;
      
      const isValid = fileWriter.validateFileContent(invalidContent);
      expect(isValid).toBe(false);
    });
  });

  describe('ensureDirectoryExists', () => {
    test('should not create directory if it exists', async () => {
      mockFs.access.mockResolvedValue();
      
      await fileWriter.ensureDirectoryExists('existing-dir');
      
      expect(mockFs.mkdir).not.toHaveBeenCalled();
    });

    test('should create directory if it does not exist', async () => {
      mockFs.access.mockRejectedValue({ code: 'ENOENT' });
      mockFs.mkdir.mockResolvedValue();
      
      await fileWriter.ensureDirectoryExists('new-dir');
      
      expect(mockFs.mkdir).toHaveBeenCalledWith('new-dir', { recursive: true });
    });

    test('should throw error for other access errors', async () => {
      mockFs.access.mockRejectedValue({ code: 'EPERM' });
      
      await expect(fileWriter.ensureDirectoryExists('restricted-dir'))
        .rejects.toThrow();
    });
  });
});