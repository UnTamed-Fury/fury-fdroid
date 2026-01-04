# Fury's F-Droid Repository Website

This is the Nuxt-based website for Fury's F-Droid Repository, providing a modern interface for browsing and accessing the F-Droid repository.

## Features

- **Modern UI/UX**: Clean, responsive design with dark theme
- **App Browsing**: Browse all available apps in the repository
- **Search Functionality**: Search apps by name, author, or category
- **Repository Information**: Easy access to repository URL and fingerprint
- **Statistics**: View repository statistics and app counts
- **Responsive Design**: Works on all device sizes

## Project Structure

```
website/
├── assets/           # CSS, images, and other assets
├── components/       # Vue components
├── layouts/          # Layout templates
├── pages/            # Page components (auto-routed)
├── public/           # Static assets
├── nuxt.config.ts    # Nuxt configuration
└── package.json      # Project dependencies and scripts
```

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run generate` - Generate static site
- `npm run preview` - Preview production build

## Development

1. Install dependencies: `npm install`
2. Start development server: `npm run dev`
3. Visit `http://localhost:3000`

## Deployment

The website is designed to work with GitHub Pages. The generated static files can be deployed directly to GitHub Pages.

## Configuration

The site configuration is in `nuxt.config.ts`. You can customize:
- Site metadata
- CSS files
- Build settings
- Routing