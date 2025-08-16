import axios from 'axios';

/**
 * Notification service for sending alerts about critical failures
 * Supports multiple notification channels (email, Slack, webhook)
 */
export class NotificationService {
  constructor(config = {}, logger = null) {
    this.config = {
      enabled: config.enabled !== false,
      channels: config.channels || [],
      retryAttempts: config.retryAttempts || 3,
      retryDelay: config.retryDelay || 5000,
      ...config
    };
    this.logger = logger;
  }

  /**
   * Send critical alert to all configured channels
   * @param {Object} alert - Alert information
   * @returns {Promise<Object>} Notification results
   */
  async sendCriticalAlert(alert) {
    if (!this.config.enabled) {
      this.log('info', 'Notifications disabled, skipping critical alert');
      return { success: true, message: 'Notifications disabled' };
    }

    if (this.config.channels.length === 0) {
      this.log('warn', 'No notification channels configured');
      return { success: false, message: 'No notification channels configured' };
    }

    const results = [];

    for (const channel of this.config.channels) {
      try {
        const result = await this.sendToChannel(channel, alert);
        results.push({ channel: channel.type, success: true, result });
        this.log('info', `Critical alert sent successfully to ${channel.type}`);
      } catch (error) {
        results.push({ channel: channel.type, success: false, error: error.message });
        this.log('error', `Failed to send critical alert to ${channel.type}:`, error);
      }
    }

    const successCount = results.filter(r => r.success).length;
    const totalCount = results.length;

    return {
      success: successCount > 0,
      message: `Sent to ${successCount}/${totalCount} channels`,
      results
    };
  }

  /**
   * Send notification to specific channel
   * @param {Object} channel - Channel configuration
   * @param {Object} alert - Alert information
   * @returns {Promise} Channel-specific result
   */
  async sendToChannel(channel, alert) {
    switch (channel.type) {
      case 'slack':
        return await this.sendSlackNotification(channel, alert);
      case 'webhook':
        return await this.sendWebhookNotification(channel, alert);
      case 'email':
        return await this.sendEmailNotification(channel, alert);
      case 'github':
        return await this.sendGitHubIssue(channel, alert);
      default:
        throw new Error(`Unsupported notification channel: ${channel.type}`);
    }
  }

  /**
   * Send Slack notification
   * @param {Object} channel - Slack channel configuration
   * @param {Object} alert - Alert information
   * @returns {Promise} Slack API response
   */
  async sendSlackNotification(channel, alert) {
    const payload = {
      text: `🚨 ${alert.title}`,
      attachments: [
        {
          color: 'danger',
          fields: [
            {
              title: 'Error Message',
              value: alert.message,
              short: false
            },
            {
              title: 'Error Type',
              value: alert.errorType || 'Unknown',
              short: true
            },
            {
              title: 'Timestamp',
              value: alert.timestamp || new Date().toISOString(),
              short: true
            }
          ]
        }
      ]
    };

    if (alert.metadata) {
      payload.attachments[0].fields.push({
        title: 'Additional Details',
        value: JSON.stringify(alert.metadata, null, 2),
        short: false
      });
    }

    return await this.executeWithRetry(async () => {
      const response = await axios.post(channel.webhookUrl, payload, {
        headers: { 'Content-Type': 'application/json' },
        timeout: 10000
      });
      return response.data;
    });
  }

  /**
   * Send webhook notification
   * @param {Object} channel - Webhook channel configuration
   * @param {Object} alert - Alert information
   * @returns {Promise} Webhook response
   */
  async sendWebhookNotification(channel, alert) {
    const payload = {
      type: 'critical_alert',
      alert,
      timestamp: new Date().toISOString(),
      source: 'twitter-crypto-automation'
    };

    const headers = {
      'Content-Type': 'application/json',
      'User-Agent': 'TwitterCryptoAutomation/1.0'
    };

    // Add authentication if configured
    if (channel.auth) {
      if (channel.auth.type === 'bearer') {
        headers['Authorization'] = `Bearer ${channel.auth.token}`;
      } else if (channel.auth.type === 'basic') {
        const credentials = Buffer.from(`${channel.auth.username}:${channel.auth.password}`).toString('base64');
        headers['Authorization'] = `Basic ${credentials}`;
      } else if (channel.auth.type === 'header') {
        headers[channel.auth.headerName] = channel.auth.headerValue;
      }
    }

    return await this.executeWithRetry(async () => {
      const response = await axios.post(channel.url, payload, {
        headers,
        timeout: 15000
      });
      return response.data;
    });
  }

  /**
   * Send email notification (using webhook to email service)
   * @param {Object} channel - Email channel configuration
   * @param {Object} alert - Alert information
   * @returns {Promise} Email service response
   */
  async sendEmailNotification(channel, alert) {
    const emailPayload = {
      to: channel.recipients,
      subject: `🚨 Critical Alert: ${alert.title}`,
      html: this.generateEmailHTML(alert),
      text: this.generateEmailText(alert)
    };

    // Use configured email service (SendGrid, Mailgun, etc.)
    const headers = {
      'Content-Type': 'application/json'
    };

    if (channel.apiKey) {
      headers['Authorization'] = `Bearer ${channel.apiKey}`;
    }

    return await this.executeWithRetry(async () => {
      const response = await axios.post(channel.apiUrl, emailPayload, {
        headers,
        timeout: 15000
      });
      return response.data;
    });
  }

  /**
   * Create GitHub issue for critical errors
   * @param {Object} channel - GitHub channel configuration
   * @param {Object} alert - Alert information
   * @returns {Promise} GitHub API response
   */
  async sendGitHubIssue(channel, alert) {
    const issuePayload = {
      title: `🚨 Critical Error: ${alert.title}`,
      body: this.generateGitHubIssueBody(alert),
      labels: ['bug', 'critical', 'automation']
    };

    const headers = {
      'Accept': 'application/vnd.github.v3+json',
      'Authorization': `token ${channel.token}`,
      'User-Agent': 'TwitterCryptoAutomation/1.0'
    };

    const url = `https://api.github.com/repos/${channel.owner}/${channel.repo}/issues`;

    return await this.executeWithRetry(async () => {
      const response = await axios.post(url, issuePayload, {
        headers,
        timeout: 15000
      });
      return response.data;
    });
  }

  /**
   * Generate HTML email content
   * @param {Object} alert - Alert information
   * @returns {string} HTML content
   */
  generateEmailHTML(alert) {
    return `
      <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
          <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; padding: 15px; margin-bottom: 20px;">
            <h2 style="color: #721c24; margin: 0;">🚨 Critical Alert</h2>
          </div>
          
          <h3>${alert.title}</h3>
          
          <div style="background-color: #f8f9fa; border-left: 4px solid #dc3545; padding: 15px; margin: 15px 0;">
            <strong>Error Message:</strong><br>
            <code style="background-color: #e9ecef; padding: 2px 4px; border-radius: 3px;">${alert.message}</code>
          </div>
          
          <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
            <tr>
              <td style="border: 1px solid #dee2e6; padding: 8px; background-color: #f8f9fa;"><strong>Error Type:</strong></td>
              <td style="border: 1px solid #dee2e6; padding: 8px;">${alert.errorType || 'Unknown'}</td>
            </tr>
            <tr>
              <td style="border: 1px solid #dee2e6; padding: 8px; background-color: #f8f9fa;"><strong>Timestamp:</strong></td>
              <td style="border: 1px solid #dee2e6; padding: 8px;">${alert.timestamp || new Date().toISOString()}</td>
            </tr>
          </table>
          
          ${alert.metadata ? `
            <h4>Additional Details:</h4>
            <pre style="background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; border-radius: 4px; overflow-x: auto;">${JSON.stringify(alert.metadata, null, 2)}</pre>
          ` : ''}
          
          <hr style="margin: 20px 0;">
          <p style="color: #6c757d; font-size: 12px;">
            This alert was generated by the Twitter Crypto Content Automation system.
          </p>
        </body>
      </html>
    `;
  }

  /**
   * Generate plain text email content
   * @param {Object} alert - Alert information
   * @returns {string} Plain text content
   */
  generateEmailText(alert) {
    let text = `🚨 CRITICAL ALERT\n\n`;
    text += `Title: ${alert.title}\n`;
    text += `Error Message: ${alert.message}\n`;
    text += `Error Type: ${alert.errorType || 'Unknown'}\n`;
    text += `Timestamp: ${alert.timestamp || new Date().toISOString()}\n`;
    
    if (alert.metadata) {
      text += `\nAdditional Details:\n${JSON.stringify(alert.metadata, null, 2)}\n`;
    }
    
    text += `\n---\nThis alert was generated by the Twitter Crypto Content Automation system.`;
    
    return text;
  }

  /**
   * Generate GitHub issue body
   * @param {Object} alert - Alert information
   * @returns {string} Issue body markdown
   */
  generateGitHubIssueBody(alert) {
    let body = `## Critical Error Report\n\n`;
    body += `**Error Message:** ${alert.message}\n\n`;
    body += `**Error Type:** ${alert.errorType || 'Unknown'}\n\n`;
    body += `**Timestamp:** ${alert.timestamp || new Date().toISOString()}\n\n`;
    
    if (alert.metadata) {
      body += `## Additional Details\n\n`;
      body += `\`\`\`json\n${JSON.stringify(alert.metadata, null, 2)}\n\`\`\`\n\n`;
    }
    
    body += `## Environment\n\n`;
    body += `- Node.js: ${process.version}\n`;
    body += `- Platform: ${process.platform}\n`;
    body += `- Architecture: ${process.arch}\n\n`;
    
    body += `---\n`;
    body += `*This issue was automatically created by the Twitter Crypto Content Automation system.*`;
    
    return body;
  }

  /**
   * Execute operation with retry logic
   * @param {Function} operation - Async operation to execute
   * @returns {Promise} Operation result
   */
  async executeWithRetry(operation) {
    let lastError = null;

    for (let attempt = 1; attempt <= this.config.retryAttempts; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error;
        
        if (attempt < this.config.retryAttempts) {
          this.log('warn', `Notification attempt ${attempt} failed, retrying in ${this.config.retryDelay}ms:`, error.message);
          await this.sleep(this.config.retryDelay);
        }
      }
    }

    throw lastError;
  }

  /**
   * Sleep for specified milliseconds
   * @param {number} ms - Milliseconds to sleep
   * @returns {Promise} Promise that resolves after delay
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Log message using configured logger or console
   * @param {string} level - Log level
   * @param {string} message - Log message
   * @param {*} data - Additional data
   */
  log(level, message, data = null) {
    if (this.logger) {
      this.logger[level](message, data);
    } else {
      const timestamp = new Date().toISOString();
      const logMessage = `[${timestamp}] [${level.toUpperCase()}] NotificationService: ${message}`;
      
      if (data) {
        console[level](logMessage, data);
      } else {
        console[level](logMessage);
      }
    }
  }

  /**
   * Test notification configuration
   * @returns {Promise<Object>} Test results
   */
  async testConfiguration() {
    const testAlert = {
      title: 'Test Notification',
      message: 'This is a test notification to verify configuration',
      errorType: 'TEST',
      timestamp: new Date().toISOString(),
      metadata: {
        test: true,
        configuredChannels: this.config.channels.length
      }
    };

    try {
      const result = await this.sendCriticalAlert(testAlert);
      return {
        success: true,
        message: 'Test notification sent successfully',
        result
      };
    } catch (error) {
      return {
        success: false,
        message: 'Test notification failed',
        error: error.message
      };
    }
  }
}

export default NotificationService;