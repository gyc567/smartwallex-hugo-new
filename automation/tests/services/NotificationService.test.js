import NotificationService from '../../src/services/NotificationService.js';
import axios from 'axios';

// Mock axios
jest.mock('axios');

describe('NotificationService', () => {
  let notificationService;
  let mockLogger;

  beforeEach(() => {
    mockLogger = {
      info: jest.fn(),
      warn: jest.fn(),
      error: jest.fn(),
      debug: jest.fn()
    };

    axios.post.mockClear();
  });

  describe('Initialization', () => {
    test('should initialize with default configuration', () => {
      const service = new NotificationService();
      
      expect(service.config.enabled).toBe(true);
      expect(service.config.channels).toEqual([]);
      expect(service.config.retryAttempts).toBe(3);
    });

    test('should initialize with custom configuration', () => {
      const config = {
        enabled: false,
        channels: [{ type: 'slack' }],
        retryAttempts: 5
      };
      
      const service = new NotificationService(config);
      
      expect(service.config.enabled).toBe(false);
      expect(service.config.channels).toHaveLength(1);
      expect(service.config.retryAttempts).toBe(5);
    });
  });

  describe('Critical Alert Sending', () => {
    test('should skip sending when notifications are disabled', async () => {
      const service = new NotificationService({ enabled: false }, mockLogger);
      
      const result = await service.sendCriticalAlert({
        title: 'Test Alert',
        message: 'Test message'
      });

      expect(result.success).toBe(true);
      expect(result.message).toBe('Notifications disabled');
    });

    test('should return error when no channels configured', async () => {
      const service = new NotificationService({ channels: [] }, mockLogger);
      
      const result = await service.sendCriticalAlert({
        title: 'Test Alert',
        message: 'Test message'
      });

      expect(result.success).toBe(false);
      expect(result.message).toBe('No notification channels configured');
    });

    test('should send to all configured channels', async () => {
      const channels = [
        { type: 'slack', webhookUrl: 'https://hooks.slack.com/test' },
        { type: 'webhook', url: 'https://example.com/webhook' }
      ];
      
      const service = new NotificationService({ channels }, mockLogger);
      
      axios.post.mockResolvedValue({ data: { ok: true } });

      const alert = {
        title: 'Test Alert',
        message: 'Test message',
        errorType: 'TEST_ERROR'
      };

      const result = await service.sendCriticalAlert(alert);

      expect(result.success).toBe(true);
      expect(result.results).toHaveLength(2);
      expect(axios.post).toHaveBeenCalledTimes(2);
    });

    test('should handle partial failures', async () => {
      const channels = [
        { type: 'slack', webhookUrl: 'https://hooks.slack.com/test' },
        { type: 'webhook', url: 'https://example.com/webhook' }
      ];
      
      const service = new NotificationService({ channels }, mockLogger);
      
      axios.post
        .mockResolvedValueOnce({ data: { ok: true } })
        .mockRejectedValueOnce(new Error('Webhook failed'));

      const alert = {
        title: 'Test Alert',
        message: 'Test message'
      };

      const result = await service.sendCriticalAlert(alert);

      expect(result.success).toBe(true); // At least one succeeded
      expect(result.message).toBe('Sent to 1/2 channels');
      expect(result.results[0].success).toBe(true);
      expect(result.results[1].success).toBe(false);
    });
  });

  describe('Slack Notifications', () => {
    test('should send Slack notification with correct payload', async () => {
      const channel = { 
        type: 'slack', 
        webhookUrl: 'https://hooks.slack.com/test' 
      };
      
      const service = new NotificationService({ channels: [channel] });
      
      axios.post.mockResolvedValue({ data: { ok: true } });

      const alert = {
        title: 'Critical Error',
        message: 'Something went wrong',
        errorType: 'API_ERROR',
        timestamp: '2023-01-01T00:00:00.000Z',
        metadata: { context: 'test' }
      };

      await service.sendCriticalAlert(alert);

      expect(axios.post).toHaveBeenCalledWith(
        'https://hooks.slack.com/test',
        expect.objectContaining({
          text: '🚨 Critical Error',
          attachments: expect.arrayContaining([
            expect.objectContaining({
              color: 'danger',
              fields: expect.arrayContaining([
                expect.objectContaining({
                  title: 'Error Message',
                  value: 'Something went wrong'
                }),
                expect.objectContaining({
                  title: 'Error Type',
                  value: 'API_ERROR'
                })
              ])
            })
          ])
        }),
        expect.objectContaining({
          headers: { 'Content-Type': 'application/json' }
        })
      );
    });
  });

  describe('Webhook Notifications', () => {
    test('should send webhook notification with authentication', async () => {
      const channel = { 
        type: 'webhook', 
        url: 'https://example.com/webhook',
        auth: {
          type: 'bearer',
          token: 'test-token'
        }
      };
      
      const service = new NotificationService({ channels: [channel] });
      
      axios.post.mockResolvedValue({ data: { received: true } });

      const alert = {
        title: 'Test Alert',
        message: 'Test message'
      };

      await service.sendCriticalAlert(alert);

      expect(axios.post).toHaveBeenCalledWith(
        'https://example.com/webhook',
        expect.objectContaining({
          type: 'critical_alert',
          alert,
          source: 'twitter-crypto-automation'
        }),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token'
          })
        })
      );
    });

    test('should handle basic authentication', async () => {
      const channel = { 
        type: 'webhook', 
        url: 'https://example.com/webhook',
        auth: {
          type: 'basic',
          username: 'user',
          password: 'pass'
        }
      };
      
      const service = new NotificationService({ channels: [channel] });
      
      axios.post.mockResolvedValue({ data: { received: true } });

      await service.sendCriticalAlert({ title: 'Test', message: 'Test' });

      const expectedAuth = Buffer.from('user:pass').toString('base64');
      expect(axios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(Object),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': `Basic ${expectedAuth}`
          })
        })
      );
    });

    test('should handle custom header authentication', async () => {
      const channel = { 
        type: 'webhook', 
        url: 'https://example.com/webhook',
        auth: {
          type: 'header',
          headerName: 'X-API-Key',
          headerValue: 'secret-key'
        }
      };
      
      const service = new NotificationService({ channels: [channel] });
      
      axios.post.mockResolvedValue({ data: { received: true } });

      await service.sendCriticalAlert({ title: 'Test', message: 'Test' });

      expect(axios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(Object),
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-API-Key': 'secret-key'
          })
        })
      );
    });
  });

  describe('Email Notifications', () => {
    test('should send email notification', async () => {
      const channel = { 
        type: 'email',
        recipients: ['admin@example.com'],
        apiUrl: 'https://api.sendgrid.com/v3/mail/send',
        apiKey: 'test-api-key'
      };
      
      const service = new NotificationService({ channels: [channel] });
      
      axios.post.mockResolvedValue({ data: { message: 'sent' } });

      const alert = {
        title: 'Critical Error',
        message: 'System failure',
        errorType: 'SYSTEM_ERROR'
      };

      await service.sendCriticalAlert(alert);

      expect(axios.post).toHaveBeenCalledWith(
        'https://api.sendgrid.com/v3/mail/send',
        expect.objectContaining({
          to: ['admin@example.com'],
          subject: '🚨 Critical Alert: Critical Error',
          html: expect.stringContaining('System failure'),
          text: expect.stringContaining('System failure')
        }),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-api-key'
          })
        })
      );
    });
  });

  describe('GitHub Issue Creation', () => {
    test('should create GitHub issue', async () => {
      const channel = { 
        type: 'github',
        owner: 'testuser',
        repo: 'testrepo',
        token: 'github-token'
      };
      
      const service = new NotificationService({ channels: [channel] });
      
      axios.post.mockResolvedValue({ 
        data: { 
          id: 123, 
          number: 456, 
          html_url: 'https://github.com/testuser/testrepo/issues/456' 
        } 
      });

      const alert = {
        title: 'Critical System Error',
        message: 'Database connection failed',
        errorType: 'DATABASE_ERROR',
        metadata: { connection: 'primary' }
      };

      await service.sendCriticalAlert(alert);

      expect(axios.post).toHaveBeenCalledWith(
        'https://api.github.com/repos/testuser/testrepo/issues',
        expect.objectContaining({
          title: '🚨 Critical Error: Critical System Error',
          body: expect.stringContaining('Database connection failed'),
          labels: ['bug', 'critical', 'automation']
        }),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'token github-token'
          })
        })
      );
    });
  });

  describe('Content Generation', () => {
    test('should generate HTML email content', () => {
      const service = new NotificationService();
      
      const alert = {
        title: 'Test Alert',
        message: 'Test error message',
        errorType: 'TEST_ERROR',
        timestamp: '2023-01-01T00:00:00.000Z',
        metadata: { context: 'test' }
      };

      const html = service.generateEmailHTML(alert);

      expect(html).toContain('🚨 Critical Alert');
      expect(html).toContain('Test Alert');
      expect(html).toContain('Test error message');
      expect(html).toContain('TEST_ERROR');
      expect(html).toContain('2023-01-01T00:00:00.000Z');
      expect(html).toContain('"context": "test"');
    });

    test('should generate plain text email content', () => {
      const service = new NotificationService();
      
      const alert = {
        title: 'Test Alert',
        message: 'Test error message',
        errorType: 'TEST_ERROR'
      };

      const text = service.generateEmailText(alert);

      expect(text).toContain('🚨 CRITICAL ALERT');
      expect(text).toContain('Title: Test Alert');
      expect(text).toContain('Error Message: Test error message');
      expect(text).toContain('Error Type: TEST_ERROR');
    });

    test('should generate GitHub issue body', () => {
      const service = new NotificationService();
      
      const alert = {
        title: 'Critical Error',
        message: 'System failure',
        errorType: 'SYSTEM_ERROR',
        metadata: { component: 'database' }
      };

      const body = service.generateGitHubIssueBody(alert);

      expect(body).toContain('## Critical Error Report');
      expect(body).toContain('**Error Message:** System failure');
      expect(body).toContain('**Error Type:** SYSTEM_ERROR');
      expect(body).toContain('```json');
      expect(body).toContain('"component": "database"');
      expect(body).toContain('## Environment');
      expect(body).toContain(`- Node.js: ${process.version}`);
    });
  });

  describe('Retry Logic', () => {
    test('should retry failed operations', async () => {
      const service = new NotificationService({ 
        retryAttempts: 2,
        retryDelay: 10 // Short delay for testing
      });

      let attempts = 0;
      const operation = jest.fn().mockImplementation(() => {
        attempts++;
        if (attempts < 3) {
          throw new Error('Temporary failure');
        }
        return 'success';
      });

      const result = await service.executeWithRetry(operation);

      expect(result).toBe('success');
      expect(operation).toHaveBeenCalledTimes(3);
    });

    test('should fail after max retries', async () => {
      const service = new NotificationService({ 
        retryAttempts: 2,
        retryDelay: 10
      });

      const operation = jest.fn().mockRejectedValue(new Error('Persistent failure'));

      await expect(service.executeWithRetry(operation)).rejects.toThrow('Persistent failure');
      expect(operation).toHaveBeenCalledTimes(3); // 1 initial + 2 retries
    });
  });

  describe('Configuration Testing', () => {
    test('should test notification configuration successfully', async () => {
      const channels = [
        { type: 'slack', webhookUrl: 'https://hooks.slack.com/test' }
      ];
      
      const service = new NotificationService({ channels });
      
      axios.post.mockResolvedValue({ data: { ok: true } });

      const result = await service.testConfiguration();

      expect(result.success).toBe(true);
      expect(result.message).toBe('Test notification sent successfully');
      expect(axios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          text: '🚨 Test Notification'
        }),
        expect.any(Object)
      );
    });

    test('should handle test configuration failure', async () => {
      const channels = [
        { type: 'slack', webhookUrl: 'https://hooks.slack.com/test' }
      ];
      
      const service = new NotificationService({ channels });
      
      axios.post.mockRejectedValue(new Error('Network error'));

      const result = await service.testConfiguration();

      expect(result.success).toBe(false);
      expect(result.message).toBe('Test notification failed');
      expect(result.error).toBe('Network error');
    });
  });

  describe('Logging', () => {
    test('should use provided logger', () => {
      const service = new NotificationService({}, mockLogger);
      
      service.log('info', 'Test message', { data: 'test' });

      expect(mockLogger.info).toHaveBeenCalledWith('Test message', { data: 'test' });
    });

    test('should fallback to console when no logger provided', () => {
      const consoleSpy = jest.spyOn(console, 'info').mockImplementation();
      const service = new NotificationService();
      
      service.log('info', 'Test message');

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('NotificationService: Test message')
      );

      consoleSpy.mockRestore();
    });
  });

  describe('Unsupported Channel Types', () => {
    test('should handle unsupported channel types', async () => {
      const channels = [
        { type: 'unsupported', url: 'https://example.com' }
      ];
      
      const service = new NotificationService({ channels });

      const result = await service.sendCriticalAlert({
        title: 'Test',
        message: 'Test'
      });

      expect(result.success).toBe(false);
      expect(result.results[0].success).toBe(false);
      expect(result.results[0].error).toContain('Unsupported notification channel');
    });
  });
});