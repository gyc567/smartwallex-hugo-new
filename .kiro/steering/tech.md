# Technology Stack

## Framework
- **Hugo**: Static site generator built with Go
- **Version**: Latest (check with `hugo version`)

## Configuration
- **Config File**: `hugo.toml` (TOML format)
- **Base URL**: Currently set to example.org (update for production)
- **Language**: English (en-us)

## Content Format
- **Markup**: Markdown files with TOML front matter
- **Archetypes**: Template files in `archetypes/` directory for new content
- **Front Matter**: Uses `+++` delimiters for TOML format

## Common Commands

### Development
```bash
# Start development server with live reload
hugo server

# Start server with drafts visible
hugo server -D

# Start server on specific port
hugo server -p 1314
```

### Build & Deploy
```bash
# Build site for production
hugo

# Build including draft content
hugo -D

# Clean build cache
hugo --gc
```

### Content Management
```bash
# Create new post
hugo new posts/my-post.md

# Create new page
hugo new about.md

# Create content using specific archetype
hugo new posts/my-post.md --kind post
```

## Dependencies
- Hugo binary (no additional runtime dependencies)
- Go (only needed if building Hugo from source)