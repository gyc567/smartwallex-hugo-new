#!/usr/bin/env node

import fs from 'fs-extra';
import path from 'path';
import Logger from '../src/utils/Logger.js';

/**
 * Content Quality Monitoring Script
 * Monitors generated content for quality, performance, and compliance
 */

const logger = new Logger('ContentQualityMonitor');

class ContentQualityMonitor {
  constructor(contentDir = '../content/posts') {
    this.contentDir = path.resolve(process.cwd(), contentDir);
    this.publicDir = path.resolve(process.cwd(), '../public');
    this.qualityMetrics = {
      totalArticles: 0,
      passedQuality: 0,
      failedQuality: 0,
      averageLength: 0,
      averageReadingTime: 0,
      seoScore: 0,
      performanceScore: 0
    };
  }

  async runQualityCheck() {
    logger.info('Starting content quality monitoring...');
    
    try {
      await this.analyzeContentQuality();
      await this.checkSEOCompliance();
      await this.validatePerformance();
      await this.generateQualityReport();
      
      logger.info('✅ Content quality monitoring completed successfully!');
      return this.qualityMetrics;
    } catch (error) {
      logger.error('❌ Content quality monitoring failed:', error);
      return null;
    }
  }

  async analyzeContentQuality() {
    logger.info('Analyzing content quality...');
    
    if (!await fs.pathExists(this.contentDir)) {
      logger.warn('Content directory not found, skipping quality analysis');
      return;
    }
    
    const files = await fs.readdir(this.contentDir);
    const markdownFiles = files.filter(file => file.endsWith('.md'));
    
    this.qualityMetrics.totalArticles = markdownFiles.length;
    
    let totalLength = 0;
    let totalReadingTime = 0;
    let qualityPassed = 0;
    
    for (const file of markdownFiles) {
      const filePath = path.join(this.contentDir, file);
      const content = await fs.readFile(filePath, 'utf-8');
      
      const quality = this.assessArticleQuality(content, file);
      
      if (quality.passed) {
        qualityPassed++;
      }
      
      totalLength += quality.length;
      totalReadingTime += quality.readingTime;
      
      logger.info(`Quality check for ${file}: ${quality.passed ? 'PASS' : 'FAIL'} (Score: ${quality.score}/100)`);
    }
    
    this.qualityMetrics.passedQuality = qualityPassed;
    this.qualityMetrics.failedQuality = markdownFiles.length - qualityPassed;
    this.qualityMetrics.averageLength = Math.round(totalLength / markdownFiles.length);
    this.qualityMetrics.averageReadingTime = Math.round(totalReadingTime / markdownFiles.length);
    
    logger.info(`Quality analysis completed: ${qualityPassed}/${markdownFiles.length} articles passed`);
  }

  assessArticleQuality(content, filename) {
    const quality = {
      passed: false,
      score: 0,
      length: content.length,
      readingTime: Math.ceil(content.split(' ').length / 200), // 200 words per minute
      issues: []
    };
    
    let score = 0;
    
    // Check front matter (20 points)
    if (content.startsWith('+++')) {
      score += 10;
      const frontMatterEnd = content.indexOf('+++', 3);
      if (frontMatterEnd !== -1) {
        score += 10;
        const frontMatter = content.substring(3, frontMatterEnd);
        
        // Check required fields
        const requiredFields = ['title', 'date', 'description', 'tags', 'categories'];
        const missingFields = requiredFields.filter(field => !frontMatter.includes(`${field} =`));
        
        if (missingFields.length === 0) {
          score += 10;
        } else {
          quality.issues.push(`Missing front matter fields: ${missingFields.join(', ')}`);
        }
      } else {
        quality.issues.push('Incomplete front matter');
      }
    } else {
      quality.issues.push('Missing front matter');
    }
    
    // Check content length (15 points)
    if (content.length > 2000) {
      score += 15;
    } else if (content.length > 1000) {
      score += 10;
    } else if (content.length > 500) {
      score += 5;
    } else {
      quality.issues.push('Content too short');
    }
    
    // Check Chinese content (15 points)
    const chineseRegex = /[\u4e00-\u9fff]/g;
    const chineseMatches = content.match(chineseRegex);
    if (chineseMatches && chineseMatches.length > 100) {
      score += 15;
    } else if (chineseMatches && chineseMatches.length > 50) {
      score += 10;
    } else {
      quality.issues.push('Insufficient Chinese content');
    }
    
    // Check required sections (20 points)
    const requiredSections = ['## 原始推文信息', '## 关于作者'];
    const missingSections = requiredSections.filter(section => !content.includes(section));
    
    if (missingSections.length === 0) {
      score += 20;
    } else {
      score += Math.max(0, 20 - (missingSections.length * 10));
      quality.issues.push(`Missing sections: ${missingSections.join(', ')}`);
    }
    
    // Check author information (10 points)
    if (content.includes('ERIC') && content.includes('gyc567@gmail.com')) {
      score += 10;
    } else {
      quality.issues.push('Missing or incomplete author information');
    }
    
    // Check contact information (10 points)
    if (content.includes('smartwallex.com') && content.includes('telegram')) {
      score += 10;
    } else {
      quality.issues.push('Missing contact information');
    }
    
    // Check formatting (10 points)
    const hasHeaders = content.includes('##') || content.includes('###');
    const hasBullets = content.includes('- ') || content.includes('* ');
    const hasEmphasis = content.includes('**') || content.includes('*');
    
    if (hasHeaders && hasBullets && hasEmphasis) {
      score += 10;
    } else if (hasHeaders && (hasBullets || hasEmphasis)) {
      score += 7;
    } else if (hasHeaders) {
      score += 5;
    } else {
      quality.issues.push('Poor formatting - missing headers, bullets, or emphasis');
    }
    
    quality.score = score;
    quality.passed = score >= 70; // 70% threshold
    
    return quality;
  }

  async checkSEOCompliance() {
    logger.info('Checking SEO compliance...');
    
    if (!await fs.pathExists(this.publicDir)) {
      logger.warn('Public directory not found, skipping SEO check');
      return;
    }
    
    let seoScore = 0;
    let totalChecks = 0;
    
    // Check index page
    const indexPath = path.join(this.publicDir, 'index.html');
    if (await fs.pathExists(indexPath)) {
      const indexContent = await fs.readFile(indexPath, 'utf-8');
      
      // Title tag
      if (indexContent.includes('<title>') && indexContent.includes('SmartWallex')) {
        seoScore += 10;
      }
      totalChecks += 10;
      
      // Meta description
      if (indexContent.includes('meta name=\"description\"')) {
        seoScore += 10;
      }
      totalChecks += 10;
      
      // Meta keywords
      if (indexContent.includes('meta name=\"keywords\"')) {
        seoScore += 5;
      }
      totalChecks += 5;
      
      // Open Graph tags
      if (indexContent.includes('meta property=\"og:')) {
        seoScore += 10;
      }
      totalChecks += 10;
      
      // Canonical URL
      if (indexContent.includes('rel=\"canonical\"')) {
        seoScore += 5;
      }
      totalChecks += 5;
    }
    
    // Check sitemap
    const sitemapPath = path.join(this.publicDir, 'sitemap.xml');
    if (await fs.pathExists(sitemapPath)) {
      seoScore += 10;
    }
    totalChecks += 10;
    
    // Check RSS feed
    const rssPath = path.join(this.publicDir, 'index.xml');
    if (await fs.pathExists(rssPath)) {
      seoScore += 5;
    }
    totalChecks += 5;
    
    // Check robots.txt
    const robotsPath = path.join(this.publicDir, 'robots.txt');
    if (await fs.pathExists(robotsPath)) {
      seoScore += 5;
    }
    totalChecks += 5;
    
    this.qualityMetrics.seoScore = Math.round((seoScore / totalChecks) * 100);
    logger.info(`SEO compliance score: ${this.qualityMetrics.seoScore}%`);
  }

  async validatePerformance() {
    logger.info('Validating site performance...');
    
    if (!await fs.pathExists(this.publicDir)) {
      logger.warn('Public directory not found, skipping performance check');
      return;
    }
    
    let performanceScore = 100;
    const issues = [];
    
    // Check file sizes
    const indexPath = path.join(this.publicDir, 'index.html');
    if (await fs.pathExists(indexPath)) {
      const stats = await fs.stat(indexPath);
      if (stats.size > 500 * 1024) { // 500KB
        performanceScore -= 20;
        issues.push(`Large index page: ${Math.round(stats.size / 1024)}KB`);
      } else if (stats.size > 200 * 1024) { // 200KB
        performanceScore -= 10;
        issues.push(`Moderately large index page: ${Math.round(stats.size / 1024)}KB`);
      }
    }
    
    // Check CSS file size
    const cssPath = path.join(this.publicDir, 'css', 'style.css');
    if (await fs.pathExists(cssPath)) {
      const stats = await fs.stat(cssPath);
      if (stats.size > 100 * 1024) { // 100KB
        performanceScore -= 15;
        issues.push(`Large CSS file: ${Math.round(stats.size / 1024)}KB`);
      } else if (stats.size > 50 * 1024) { // 50KB
        performanceScore -= 5;
        issues.push(`Moderately large CSS file: ${Math.round(stats.size / 1024)}KB`);
      }
    }
    
    // Check total site size
    const allFiles = await this.getAllFiles(this.publicDir);
    let totalSize = 0;
    
    for (const file of allFiles) {
      const stats = await fs.stat(file);
      totalSize += stats.size;
    }
    
    const totalSizeMB = totalSize / (1024 * 1024);
    if (totalSizeMB > 50) { // 50MB
      performanceScore -= 25;
      issues.push(`Very large site: ${totalSizeMB.toFixed(1)}MB`);
    } else if (totalSizeMB > 20) { // 20MB
      performanceScore -= 15;
      issues.push(`Large site: ${totalSizeMB.toFixed(1)}MB`);
    } else if (totalSizeMB > 10) { // 10MB
      performanceScore -= 5;
      issues.push(`Moderately large site: ${totalSizeMB.toFixed(1)}MB`);
    }
    
    // Check number of files
    if (allFiles.length > 1000) {
      performanceScore -= 10;
      issues.push(`Many files: ${allFiles.length}`);
    } else if (allFiles.length > 500) {
      performanceScore -= 5;
      issues.push(`Moderate number of files: ${allFiles.length}`);
    }
    
    this.qualityMetrics.performanceScore = Math.max(0, performanceScore);
    
    if (issues.length > 0) {
      logger.warn(`Performance issues found: ${issues.join(', ')}`);
    }
    
    logger.info(`Performance score: ${this.qualityMetrics.performanceScore}%`);
  }

  async getAllFiles(dir) {
    const files = [];
    
    try {
      const items = await fs.readdir(dir);
      
      for (const item of items) {
        const fullPath = path.join(dir, item);
        const stats = await fs.stat(fullPath);
        
        if (stats.isDirectory()) {
          const subFiles = await this.getAllFiles(fullPath);
          files.push(...subFiles);
        } else {
          files.push(fullPath);
        }
      }
    } catch (error) {
      // Ignore errors for inaccessible directories
    }
    
    return files;
  }

  async generateQualityReport() {
    logger.info('Generating quality report...');
    
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalArticles: this.qualityMetrics.totalArticles,
        qualityPassRate: this.qualityMetrics.totalArticles > 0 
          ? Math.round((this.qualityMetrics.passedQuality / this.qualityMetrics.totalArticles) * 100)
          : 0,
        averageLength: this.qualityMetrics.averageLength,
        averageReadingTime: this.qualityMetrics.averageReadingTime,
        seoScore: this.qualityMetrics.seoScore,
        performanceScore: this.qualityMetrics.performanceScore
      },
      recommendations: this.generateRecommendations()
    };
    
    // Save report to file
    const reportsDir = path.join(process.cwd(), 'reports');
    await fs.ensureDir(reportsDir);
    
    const reportPath = path.join(reportsDir, `quality-report-${new Date().toISOString().split('T')[0]}.json`);
    await fs.writeJson(reportPath, report, { spaces: 2 });
    
    logger.info(`Quality report saved to: ${reportPath}`);
    
    // Log summary
    logger.info('=== QUALITY REPORT SUMMARY ===');
    logger.info(`Total Articles: ${report.summary.totalArticles}`);
    logger.info(`Quality Pass Rate: ${report.summary.qualityPassRate}%`);
    logger.info(`Average Length: ${report.summary.averageLength} characters`);
    logger.info(`Average Reading Time: ${report.summary.averageReadingTime} minutes`);
    logger.info(`SEO Score: ${report.summary.seoScore}%`);
    logger.info(`Performance Score: ${report.summary.performanceScore}%`);
    
    if (report.recommendations.length > 0) {
      logger.info('=== RECOMMENDATIONS ===');
      report.recommendations.forEach((rec, index) => {
        logger.info(`${index + 1}. ${rec}`);
      });
    }
    
    return report;
  }

  generateRecommendations() {
    const recommendations = [];
    
    // Quality recommendations
    const qualityPassRate = this.qualityMetrics.totalArticles > 0 
      ? (this.qualityMetrics.passedQuality / this.qualityMetrics.totalArticles) * 100
      : 0;
    
    if (qualityPassRate < 80) {
      recommendations.push('Improve content quality - less than 80% of articles meet quality standards');
    }
    
    if (this.qualityMetrics.averageLength < 1500) {
      recommendations.push('Consider increasing article length for better depth and SEO');
    }
    
    if (this.qualityMetrics.averageReadingTime < 3) {
      recommendations.push('Articles may be too short - aim for 3-5 minute reading time');
    }
    
    // SEO recommendations
    if (this.qualityMetrics.seoScore < 80) {
      recommendations.push('Improve SEO compliance - add missing meta tags, descriptions, and structured data');
    }
    
    // Performance recommendations
    if (this.qualityMetrics.performanceScore < 80) {
      recommendations.push('Optimize site performance - reduce file sizes and optimize images');
    }
    
    // General recommendations
    if (this.qualityMetrics.totalArticles < 10) {
      recommendations.push('Increase content volume - aim for regular publishing schedule');
    }
    
    return recommendations;
  }
}

// Run monitoring if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const monitor = new ContentQualityMonitor();
  const result = await monitor.runQualityCheck();
  process.exit(result ? 0 : 1);
}

export default ContentQualityMonitor;