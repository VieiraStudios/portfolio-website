# Vieira Studios

The website for **Vieira Studios**, a studio that designs and builds mobile apps, web apps and AI-powered products.

**Live site:** [vieirastudios.vercel.app](https://vieirastudios.vercel.app)

## Features

- **Four pages:** Home, Work, About and Contact, plus a custom 404 page
- **Project showcase:** filter work by Mobile, Web and AI, with custom mockup visuals on each card
- **Contact form:** messages are saved to a Postgres database, with spam and abuse protection (CSRF tokens, a honeypot field and rate limiting)
- **Smooth motion:** inertia scrolling, section snapping on desktop, scroll-reveal animations, a scroll progress bar and magnetic buttons
- **Accessible:** respects the "reduce motion" setting, keyboard friendly, with a skip-to-content link
- **Secure by default:** a strict Content Security Policy and other security headers, and secrets kept in environment variables
- **Responsive:** designed for everything from small phones to large desktop screens

## Tech stack

| Area | Tools |
|---|---|
| Backend | Python 3.14, Flask, Jinja templates |
| Forms | Flask-WTF, WTForms |
| Database | Flask-SQLAlchemy, Neon Postgres in production, SQLite locally |
| Styling | Tailwind CSS v4 |
| Front end | Vanilla JavaScript, Lenis (smooth scrolling) |
| Fonts | Sora and Inter, from Google Fonts |
| Testing | pytest |
| Tooling | uv |
| Hosting | Vercel |

## Running locally

You need [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/VieiraStudios/portfolio-website.git
cd portfolio-website
uv sync
uv run flask --app app run --debug
```

Then open http://127.0.0.1:5000. Locally, messages go to a SQLite file in `instance/`. To use other settings, copy `.env.example` to `.env`.

**Styles:** after changing classes in the templates, rebuild the CSS:

```bash
uv run tailwindcss -i styles/input.css -o public/static/css/output.css --watch
```

**Tests:**

```bash
uv run pytest
```

**Viewing contact messages:**

```bash
uv run flask --app app messages
```

## Project structure

```
app.py               Flask app: routes, database model, security headers
forms.py             Contact form and validation
content.py           Site copy: services, process steps, projects
templates/           Jinja pages and reusable macros
styles/input.css     Tailwind source and custom animations
public/static/       Built CSS, JavaScript, favicon (served by Vercel's CDN)
tests/               pytest test suite
```

Most text on the site lives in `content.py`, so adding a project or service doesn't require editing any HTML.

## Deployment

Every push to `main` deploys automatically to Vercel. Production needs these environment variables:

- `SECRET_KEY`: a long random string
- `DATABASE_URL`: added automatically by Vercel's Neon integration

## License

© Vieira Studios. All rights reserved. The code is public for reference, but the brand, design and content may not be reused.
