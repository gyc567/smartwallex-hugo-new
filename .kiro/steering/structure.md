# Project Structure

## Directory Organization

```
├── archetypes/          # Content templates
│   └── default.md       # Default archetype for new content
├── assets/              # Asset processing (SCSS, JS, images)
├── content/             # Site content (Markdown files)
├── data/                # Data files (JSON, YAML, TOML)
├── i18n/                # Translation files for internationalization
├── layouts/             # HTML templates and partials
├── static/              # Static files (copied as-is to output)
├── themes/              # Hugo themes
└── hugo.toml            # Site configuration
```

## Key Conventions

### Content Organization
- **Posts**: Place in `content/posts/` directory
- **Pages**: Place directly in `content/` or organized by section
- **Sections**: Subdirectories in `content/` create site sections
- **File Naming**: Use kebab-case for filenames (e.g., `my-blog-post.md`)

### Front Matter Standards
- Use TOML format with `+++` delimiters
- Required fields: `title`, `date`
- Set `draft = true` for unpublished content
- Use `date` in ISO format: `2024-01-15T10:30:00Z`

### Asset Management
- **Static Assets**: Place in `static/` for direct copying
- **Processed Assets**: Place in `assets/` for Hugo Pipes processing
- **Images**: Organize by content type or date

### Layout Hierarchy
- **Base Templates**: `layouts/_default/`
- **Section Templates**: `layouts/[section]/`
- **Partials**: `layouts/partials/`
- **Shortcodes**: `layouts/shortcodes/`

## Build Output
- Generated site outputs to `public/` directory (git-ignored)
- Cache files in `resources/` directory (git-ignored)