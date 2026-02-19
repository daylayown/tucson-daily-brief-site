# Tucson Daily Brief Site

Static blog for GitHub Pages — minimal, text-first, Daring Fireball style. No JavaScript, no frameworks, no build tools.

## Project Structure

```
├── style.css           # Desert/Southwest themed CSS (sand, terracotta, sage)
├── generate_post.py    # Markdown → HTML generator + index rebuilder
├── index.html          # Auto-generated index page (newest-first)
├── posts/              # Individual post HTML files (named YYYY-MM-DD.html)
├── .nojekyll           # Tells GitHub Pages to skip Jekyll
└── CLAUDE.md
```

## How It Works

`generate_post.py` takes a briefing markdown file as input and:
1. Extracts the date from the filename (e.g., `tucson-brief-2026-02-18.md` → `2026-02-18`)
2. Converts the markdown to HTML (handles bold, emoji section headers, source citations, separators)
3. Writes an HTML post to `posts/YYYY-MM-DD.html`
4. Rebuilds `index.html` by scanning all posts in `posts/` and listing them newest-first
5. Is idempotent — running it twice with the same input overwrites cleanly, no duplicates

Usage:
```
python generate_post.py ~/.openclaw/workspace/briefings/tucson-brief-2026-02-18.md
```

## Input Format

Briefing files come from the Tucson Daily Brief podcast project at `~/.openclaw/workspace/briefings/`. They have:
- Title line: "Tucson Daily Brief — February 18, 2026"
- Emoji section headers (🏛️ Government, 🚨 Public Safety, etc.)
- Bold story headlines with descriptions
- Source citations prefixed with 📰 or 📄
- ─── separators between sections
- Weather section
- Trailing metadata lines (stripped during conversion)

## Design

- Desert palette: sand bg `#f5f0e6`, terracotta links `#c75b39`, sage dates `#7a8b6f`, brown text `#3d3029`
- Single-column, max-width 600px, centered
- System font stack, line-height 1.7
- Mobile-friendly via viewport meta + fluid layout
- Footer links to Apple Podcasts and YouTube

## Deployment

Push to GitHub and enable GitHub Pages from the main branch root. `.nojekyll` ensures static serving.
