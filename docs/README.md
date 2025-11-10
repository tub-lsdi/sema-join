# Project SEMA-JOIN Documentation

This directory contains the Docusaurus documentation site for Project SEMA-JOIN.

## Running the Documentation

### Development Mode

Start the documentation development server:

```bash
cd docs
npm start
```

The site will be available at http://localhost:3000

### Building for Production

Build the static documentation site:

```bash
cd docs
npm run build
```

The built site will be in the `build` directory.

### Serving Production Build

Test the production build locally:

```bash
cd docs
npm run serve
```

## Project Structure

- `/docs` - Documentation markdown files
- `/src` - Custom React components and pages
- `/static` - Static assets (images, files)
- `docusaurus.config.ts` - Docusaurus configuration
- `sidebars.ts` - Sidebar navigation structure

## Editing Documentation

Documentation files are in the `/docs` directory:

- `getting-started.md` - Introduction to SEMA-JOIN
- `environment-setup.md` - Environment configuration
- `installation.md` - Installation instructions
- `corpus-ingestion.md` - How to ingest corpus data
- `using-sema-join.md` - User guide for the application

To add a new page, create a markdown file in `/docs` and update `sidebars.ts` to include it in the navigation.

## Documentation Guidelines

- Write for end users, not developers
- Keep explanations clear and concise
- Avoid overly technical details
- Use professional, minimalistic language
- No code examples unless absolutely necessary
- No emojis or informal language
