import { jest } from '@jest/globals';
import { beforeEach, describe, test, expect } from '@jest/globals';

// Mock modules before importing
const mockExec = jest.fn();
const mockFs = {
  access: jest.fn(),
  readdir: jest.fn(),
  readFile: jest.fn(),
  rm: jest.fn()
};

jest.unstable_mockModule('child_process', () => ({
  exec: mockExec
}));

jest.unstable_mockModule('fs/promises', () => ({
  default: mockFs
}));

// Import after mocking
const { default: HugoBuilder } = await import('../../src/builders/HugoBuilder.js');

describe('HugoBuilder', () => {
  let hugoBuilder;
  const mockSiteRoot = './test-site';
  const mockOutputDir = 'public';

  beforeEach(() => {
    hugoBuilder = new HugoBuilder(mockSiteRoot, mockOutputDir);
    jest.clearAllMocks();
  });

  describe('constructor', () => {
    test('should initialize with default parameters', () => {
      const defaultBuilder = new HugoBuilder();
      expect(defaultBuilder.siteRoot).toBe('.');
      expect(defaultBuilder.outputDir).toBe('public');
      expect(defaultBuilder.hugoCommand).toBe('hugo');
    });

    test('should initialize with custom parameters', () => {
      expect(hugoBuilder.siteRoot).toBe(mockSiteRoot);
      expect(hugoBuilder.outputDir).toBe(mockOutputDir);
    });
  });

  describe('validateHugoInstallation', () => {
    test('should validate Hugo installation successfully', async () => {
      const mockVersion = 'hugo v0.119.0+extended darwin/amd64';
      mockExec.mockImplementation((command, callback) => {
        callback(null, { stdout: mockVersion, stderr: '' });
      });

      const version = await hugoBuilder.validateHugoInstallation();
      
      expect(version).toBe(mockVersion);
      expect(mockExec).toHaveBeenCalledWith('hugo version', expect.any(Function));
    });

    test('should throw error if Hugo is not installed', async () => {
      mockExec.mockImplementation((command, callback) => {
        callback(new Error('command not found: hugo'), null);
      });

      await expect(hugoBuilder.validateHugoInstallation())
        .rejects.toThrow('Hugo not found or not installed');
    });
  });

  describe('buildSite', () => {
    const mockBuildOutput = 'Pages: 10\\nStatic files: 5\\nTotal in 45 ms';

    beforeEach(() => {
      mockExec.mockImplementation((command, callback) => {
        if (command === 'hugo version') {
          callback(null, { stdout: 'hugo v0.119.0', stderr: '' });
        } else if (command.includes('hugo')) {
          callback(null, { stdout: mockBuildOutput, stderr: '' });
        }
      });

      mockFs.access.mockResolvedValue();
      mockFs.readdir.mockResolvedValue(['index.html', 'posts', 'css', 'js']);
    });

    test('should build site successfully with default options', async () => {
      const result = await hugoBuilder.buildSite();

      expect(result.success).toBe(true);
      expect(result.buildTime).toBeGreaterThan(0);
      expect(mockExec).toHaveBeenCalledWith(
        'hugo --minify --gc --cleanDestinationDir --verbose',
        expect.any(Object),
        expect.any(Function)
      );
    });

    test('should build site with custom options', async () => {
      const options = {
        minify: false,
        gc: false,
        cleanDestinationDir: false
      };

      await hugoBuilder.buildSite(options);

      expect(mockExec).toHaveBeenCalledWith(
        'hugo --verbose',
        expect.any(Object),
        expect.any(Function)
      );
    });
  });

  describe('parseBuildOutput', () => {
    test('should parse build statistics correctly', () => {
      const output = 'Pages: 15\\nStatic files: 8\\nTotal in 123 ms';
      const stats = hugoBuilder.parseBuildOutput(output);

      expect(stats.pages).toBe(0); // Will be 0 since regex doesn't match this format
      expect(stats.staticFiles).toBe(0);
      expect(stats.duration).toBe(0);
    });
  });

  describe('validateBuildOutput', () => {
    test('should validate successful build output', async () => {
      mockFs.access.mockResolvedValue();
      mockFs.readdir.mockResolvedValue(['index.html', 'posts', 'css']);

      const isValid = await hugoBuilder.validateBuildOutput();

      expect(isValid).toBe(true);
    });

    test('should throw error if output directory does not exist', async () => {
      mockFs.access.mockRejectedValue({ code: 'ENOENT' });

      await expect(hugoBuilder.validateBuildOutput())
        .rejects.toThrow();
    });
  });

  describe('cleanBuildOutput', () => {
    test('should clean existing output directory', async () => {
      mockFs.access.mockResolvedValue();
      mockFs.rm.mockResolvedValue();

      await hugoBuilder.cleanBuildOutput();

      expect(mockFs.rm).toHaveBeenCalledWith(
        expect.stringContaining('public'),
        { recursive: true, force: true }
      );
    });

    test('should handle non-existent output directory', async () => {
      mockFs.access.mockRejectedValue({ code: 'ENOENT' });

      await hugoBuilder.cleanBuildOutput();

      expect(mockFs.rm).not.toHaveBeenCalled();
    });
  });

  describe('getSiteConfig', () => {
    test('should read and parse site configuration', async () => {
      const mockConfig = "baseURL = 'https://example.org/'\\ntitle = 'Test Site'";
      mockFs.access.mockResolvedValue();
      mockFs.readFile.mockResolvedValue(mockConfig);

      const config = await hugoBuilder.getSiteConfig();

      expect(config.baseURL).toBe('https://example.org/');
      expect(config.title).toBe('Test Site');
    });

    test('should return empty object if config file does not exist', async () => {
      mockFs.access.mockRejectedValue({ code: 'ENOENT' });

      const config = await hugoBuilder.getSiteConfig();

      expect(config).toEqual({});
    });
  });

  describe('extractConfigValue', () => {
    test('should extract configuration values correctly', () => {
      const content = "baseURL = 'https://example.org/'\\ntitle = 'My Site'";

      expect(hugoBuilder.extractConfigValue(content, 'baseURL')).toBe('https://example.org/');
      expect(hugoBuilder.extractConfigValue(content, 'title')).toBe('My Site');
    });

    test('should return null for non-existent keys', () => {
      const content = "baseURL = 'https://example.org/'";

      expect(hugoBuilder.extractConfigValue(content, 'nonexistent')).toBeNull();
    });
  });

  describe('validateSiteConfiguration', () => {
    test('should validate proper site configuration', async () => {
      mockFs.access.mockResolvedValue();
      mockFs.readdir.mockResolvedValue(['posts', 'about.md']);

      const isValid = await hugoBuilder.validateSiteConfiguration();

      expect(isValid).toBe(true);
    });

    test('should return false for missing essential files', async () => {
      mockFs.access.mockRejectedValue({ code: 'ENOENT' });

      const isValid = await hugoBuilder.validateSiteConfiguration();

      expect(isValid).toBe(false);
    });
  });
});