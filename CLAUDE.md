# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a bilingual (Chinese/English) Hugo static website for SmartWallex, a cryptocurrency intelligence platform that aggregates smart money information, provides GitHub project analysis, market insights, and investment recommendations. The site features automated content generation from Twitter/GitHub sources and includes search, like buttons, SEO optimization, and ad integration.

## Common Development Commands

### Hugo Development
```bash
# Start development server
hugo server -D

# Build production site
hugo

# Build with cleanup and minification
hugo --cleanDestinationDir --minify
```

### Python Scripts (Content Automation)
```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Setup environment (copy and configure API keys)
cp scripts/.env.example scripts/.env.local
# Edit .env.local to add GITHUB_TOKEN and GLM_API_KEY

# Run AI-powered crypto project analyzer
python scripts/crypto-project-analyzer.py

# Run crypto swap daily analyzer (new feature)
python scripts/crypto_swap_analyzer.py

# Run comprehensive tests for crypto swap analyzer
python scripts/run_crypto_swap_tests.py          # Full test suite
python scripts/run_crypto_swap_tests.py syntax   # Syntax check only
python scripts/run_crypto_swap_tests.py unit     # Unit tests only

# Manage project history
python scripts/manage-history.py stats
python scripts/manage-history.py list
python scripts/manage-history.py search "keyword"

# Environment variables (can also be set in .env.local):
# GITHUB_TOKEN=your_github_token               # Optional, for higher API limits
# OPENAI_API_KEY=your_openai_api_key          # Required for AI analysis
# OPENAI_BASE_URL=https://api-inference.modelscope.cn/v1/  # API endpoint
# OPENAI_MODEL=Qwen/Qwen2.5-Coder-32B-Instruct           # Model name
# DAYS_BACK=7                                 # Search recent N days (default: 7)
# MAX_PROJECTS=3                              # Max projects per run (default: 3)
```

### Node.js Automation System
```bash
# Install dependencies
cd automation && npm install

# Run tests
npm test
npm run test:watch

# Development mode
npm run dev

# Run demos
npm run demo
npm run demo:full
npm run demo:mock

# Validate configuration
npm run validate
npm run validate:setup
```

## Architecture Overview

### Hugo Site Structure
- **Theme**: Uses PaperMod theme (`themes/PaperMod/`)
- **Content**: Markdown files in `content/posts/` with bilingual support
- **Configuration**: `hugo.toml` with SEO optimization, social links, and monetization
- **Custom Layouts**: Search functionality, like buttons, crypto sharing in `layouts/`
- **Static Assets**: CSS, JavaScript, and robots.txt in `static/`

### Automation Systems

#### 1. Python-based GitHub Analysis (`scripts/`)
- **Purpose**: AI-powered analysis of trending crypto projects on GitHub
- **AI Integration**: Uses OpenAI-compatible APIs (ModelScope, OpenAI, Azure OpenAI) for intelligent project filtering and content generation
- **Schedule**: Daily via GitHub Actions (UTC 16:00 / Beijing 00:00)
- **Output**: Generates 3 professional review articles daily with AI insights
- **Key Features**:
  - AI-based project quality assessment (0-1 scoring)
  - Intelligent filtering of low-value/empty projects
  - AI-generated project summaries and technical analysis
  - Smart GitHub metrics interpretation
- **Key Files**: 
  - `crypto-project-analyzer.py` - Main analyzer with AI integration
  - `manage-history.py` - Project history management
  - `config.py` - Configuration settings including AI parameters
  - `openai_client.py` - Unified OpenAI-compatible API client
  - `.env.example` - Environment configuration template

#### 2. Crypto Swap Daily Analysis (`scripts/`)
- **Purpose**: Generates professional perpetual contract trading signals for mainstream cryptocurrencies
- **AI Integration**: Uses expert prompt system for Market Cycle Phases (MCP) analysis
- **Schedule**: Daily at 05:00 Beijing time (UTC 21:00) via GitHub Actions crypto-swap-daily workflow
- **Output**: Comprehensive daily report covering BTC, ETH, BNB, SOL, BCH
- **Key Features**:
  - Expert-level perpetual contract signal generation
  - Risk management with 1:2+ risk-reward ratios
  - MCP-based market phase analysis
  - Technical indicators (RSI, MACD, Bollinger Bands)
  - Professional trading recommendations
- **Key Files**:
  - `crypto_swap_analyzer.py` - Main analyzer with expert AI prompts
  - `crypto_swap_config.py` - Configuration for 5 supported cryptocurrencies
  - `test_crypto_swap_analyzer.py` - Comprehensive test suite (100% coverage)
  - `run_crypto_swap_tests.py` - Test runner with multiple test modes

#### 3. Node.js Twitter Automation (`automation/`)
- **Purpose**: Discovers trending crypto content on Twitter, translates to Chinese
- **Architecture**: Modular ES6 modules with comprehensive testing
- **Key Components**:
  - `src/clients/TwitterClient.js` - Twitter API integration
  - `src/generators/ArticleGenerator.js` - Content generation
  - `src/builders/HugoBuilder.js` - Hugo integration
  - `src/processors/ContentProcessor.js` - Content processing

### Content Generation Workflow
1. **GitHub Analysis**: Searches trending crypto projects, generates professional reviews
2. **Crypto Swap Analysis**: Generates daily perpetual contract trading signals for BTC/ETH/BNB/SOL/BCH
3. **Twitter Monitoring**: Fetches trending tweets, translates content
4. **Content Processing**: Applies SEO optimization, formatting, and branding
5. **Hugo Integration**: Creates markdown files with proper frontmatter
6. **Automated Publishing**: Commits changes and builds site via GitHub Actions

### Configuration Management
- **Hugo**: `hugo.toml` for site settings, SEO, and theme configuration
- **Python**: `scripts/config.py` for analyzer settings and GitHub API parameters
- **Crypto Swap**: `scripts/crypto_swap_config.py` for trading signal configuration
- **Node.js**: Hierarchical config system in `automation/config/` (default/development/production)
- **GitHub Actions**: Workflow files in `.github/workflows/`

## Key Development Patterns

### Hugo Content Structure
All articles follow the template in `md-template.md` with:
- Bilingual frontmatter (title, description, tags in Chinese)
- SEO-optimized metadata with keywords and categories
- Standardized author information and contact details
- Professional review format with ratings and analysis

### Testing Strategy
- **Python**: Syntax checking with `scripts/check-syntax.py`
- **Node.js**: Jest test suite with unit, integration, and live tests
- **Integration**: End-to-end workflow testing and deployment validation
- **Content Quality**: Automated validation and monitoring scripts

### Deployment Process
1. **GitHub Actions**: Automated daily runs for both systems
2. **Content Generation**: Creates articles in `content/posts/`
3. **Hugo Build**: Generates static site in `public/`
4. **Git Commit**: Automatic commit with standardized messages
5. **Monitoring**: Action summaries and error logging

## Important Notes

### API Keys and Secrets
- GitHub token automatically provided by GitHub Actions
- Twitter API keys stored in GitHub Secrets for the automation system
- **OPENAI_API_KEY**: OpenAI-compatible API key for AI analysis (supports ModelScope, OpenAI, Azure OpenAI)
- **OPENAI_BASE_URL**: API endpoint URL (default: ModelScope)
- **OPENAI_MODEL**: Model name (default: Qwen/Qwen2.5-Coder-32B-Instruct)
- **Setup**: Copy `scripts/.env.example` to `scripts/.env.local` and configure your API keys
- No hardcoded credentials in the codebase

### Content Quality
- All generated content includes investment risk disclaimers
- Professional formatting with consistent author branding
- SEO optimization with proper meta tags and structured data
- Bilingual support with Chinese as primary language

### File Locations
- New articles: `content/posts/`
- Configuration: `hugo.toml`, `automation/config/`, `scripts/config.py`
- Tests: `automation/tests/`, various test scripts in `scripts/`
- Logs: `automation/logs/` (created at runtime)
- Data: `data/analyzed_projects.json` for project history