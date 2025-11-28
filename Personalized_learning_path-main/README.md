# PathForge

A modern, AI-assisted personalized learning path generator built with Flask (backend) and static HTML/CSS/JS (frontend).

## Features
- Auth (Sign Up/Sign In) with localStorage session and remember-me
- Onboarding: Career selection, optional known skills
- AI-generated learning paths (Flask endpoints)
- Modern UI theme (Inter/Poppins, blue/purple accents)

## Getting Started

### Prerequisites
- Python 3.11+

### Install
```
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r backend/requirements.txt
```

### Run (local)
```
python backend/app.py
```
App runs on http://localhost:5000

## Environment Variables
Copy `.env.example` to `.env` and set values:
- `SECRET_KEY` (required)
- `FLASK_ENV` (production/development)

## Deployment

### Render
- Uses `render.yaml` (already provided)
- Build Command: `pip install -r backend/requirements.txt`
- Start Command: `gunicorn -w 2 -b 0.0.0.0:10000 backend.app:app`

### Vercel
- For Python/Flask, prefer Render. If using Vercel, consider a serverless rewrite or proxy to a hosted Flask service.
- `vercel.json` includes SPA rewrites.

## Build & Performance Checklist
- Optimize images as WebP and add `loading="lazy"`
- Remove unused imports and assets before deploy

## Testing
- Validate forms (empty/invalid/weak password)
- Test onboarding flow and learning path generation
- Verify localStorage persistence and Remember Me

## Security
- Sanitize user inputs on the client
- Do not expose secrets; use environment variables
- Configure CORS if exposing APIs

## License
MIT

