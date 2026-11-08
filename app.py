import os
import secrets
import smtplib
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

import click
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from werkzeug.middleware.proxy_fix import ProxyFix

from content import CATEGORIES, PROCESS, PROJECT_TYPES, PROJECTS, SERVICES, SOCIAL_LINKS, TOOLKIT
from forms import ContactForm

ON_VERCEL = bool(os.environ.get("VERCEL"))

# Static files (CSS, JS, images) live in public/static. Locally Flask serves
# them; on Vercel the public/ folder is served straight from its global CDN.
app = Flask(__name__, static_folder="public/static", static_url_path="/static")

if ON_VERCEL:
    # Vercel sits in front of the app as a proxy; trust its X-Forwarded-For
    # header so request.remote_addr is the visitor's real IP address.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# SECRET_KEY signs session cookies and CSRF tokens. In production it must be
# set as an environment variable (see .env.example). Locally, a random key is
# generated each time the server starts.
secret_key = os.environ.get("SECRET_KEY")
if ON_VERCEL and not secret_key:
    raise RuntimeError("Set the SECRET_KEY environment variable in your Vercel project settings.")
app.config["SECRET_KEY"] = secret_key or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # reject request bodies over 64 KB


def database_url() -> str:
    """Postgres (Neon) in production; a local SQLite file for development."""
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if not url and ON_VERCEL:
        raise RuntimeError("Connect a Neon database in your Vercel project (Storage tab), then redeploy.")
    if not url:
        Path(app.instance_path).mkdir(parents=True, exist_ok=True)
        return "sqlite:///" + str(Path(app.instance_path) / "messages.db")
    # SQLAlchemy needs to be told to use the psycopg (v3) driver.
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


app.config["SQLALCHEMY_DATABASE_URI"] = database_url()
# Check connections are alive before use; serverless databases close idle ones.
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True, "pool_recycle": 300}
if app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql"):
    # Neon's pooled connection (PgBouncer) shares connections between requests,
    # so don't let psycopg cache prepared statements on them.
    app.config["SQLALCHEMY_ENGINE_OPTIONS"]["connect_args"] = {"prepare_threshold": None}


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(app, model_class=Base)


class Message(db.Model):
    """A contact-form submission. SQLAlchemy writes all values as query
    parameters, never by gluing strings into SQL, which prevents SQL injection."""

    id: Mapped[int] = mapped_column(primary_key=True)
    received_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    name: Mapped[str] = mapped_column(db.String(100))
    email: Mapped[str] = mapped_column(db.String(254))
    project_type: Mapped[str] = mapped_column(db.String(50))
    body: Mapped[str] = mapped_column(db.Text)


with app.app_context():
    db.create_all()  # creates the table the first time; does nothing after that

# Simple rate limit for the contact form: max submissions per IP per window.
CONTACT_LIMIT = 5
CONTACT_WINDOW_SECONDS = 60 * 60
_contact_attempts: dict[str, deque] = defaultdict(deque)


@app.context_processor
def inject_globals():
    """Values available in every template."""
    return {
        "current_year": datetime.now().year,
        "social_links": SOCIAL_LINKS,
    }


@app.after_request
def set_security_headers(response):
    """Tell browsers to apply extra protections to every page."""
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if ON_VERCEL:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


@app.route("/")
def index():
    return render_template(
        "index.html",
        services=SERVICES,
        process=PROCESS,
        projects=PROJECTS[:3],
    )


@app.route("/work")
def work():
    return render_template("work.html", projects=PROJECTS, categories=CATEGORIES)


@app.route("/about")
def about():
    return render_template("about.html", services=SERVICES, toolkit=TOOLKIT)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()

    if form.validate_on_submit():
        # Honeypot filled in: almost certainly a bot. Pretend it worked.
        if form.website.data:
            return redirect(url_for("contact", sent=1))

        if _rate_limited(request.remote_addr or "unknown"):
            flash("You've sent several messages already. Please try again later.", "error")
            return redirect(url_for("contact"))

        message = Message(
            name=form.name.data.strip(),
            email=form.email.data.strip(),
            project_type=dict(PROJECT_TYPES)[form.project_type.data],
            body=form.message.data.strip(),
        )
        db.session.add(message)
        db.session.commit()
        _email_message(message)

        # Post/Redirect/Get: redirecting stops the browser from re-sending
        # the form if the visitor refreshes the page.
        return redirect(url_for("contact", sent=1))

    return render_template("contact.html", form=form, sent=request.args.get("sent") == "1")


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@app.cli.command("messages")
@click.option("--limit", default=20, help="How many recent messages to show.")
def list_messages(limit):
    """Show recent contact-form messages: uv run flask --app app messages"""
    rows = db.session.execute(db.select(Message).order_by(Message.received_at.desc()).limit(limit)).scalars()
    for m in rows:
        click.echo(f"\n[{m.received_at:%Y-%m-%d %H:%M}] {m.name} <{m.email}> · {m.project_type}\n{m.body}")


def _rate_limited(ip: str) -> bool:
    now = time.monotonic()
    attempts = _contact_attempts[ip]
    while attempts and now - attempts[0] > CONTACT_WINDOW_SECONDS:
        attempts.popleft()
    if len(attempts) >= CONTACT_LIMIT:
        return True
    attempts.append(now)
    return False


def _email_message(message: Message) -> None:
    """Email the message to you, if email settings are configured (optional)."""
    server = os.environ.get("MAIL_SERVER")
    recipient = os.environ.get("MAIL_TO")
    if not server or not recipient:
        return

    email = EmailMessage()
    email["Subject"] = f"New enquiry: {message.project_type}"
    email["From"] = os.environ.get("MAIL_FROM", os.environ.get("MAIL_USERNAME", recipient))
    email["To"] = recipient
    email["Reply-To"] = message.email
    email.set_content(
        f"Name: {message.name}\n"
        f"Email: {message.email}\n"
        f"Project type: {message.project_type}\n\n"
        f"{message.body}\n"
    )

    try:
        with smtplib.SMTP(server, int(os.environ.get("MAIL_PORT", 587)), timeout=10) as smtp:
            smtp.starttls()
            username = os.environ.get("MAIL_USERNAME")
            if username:
                smtp.login(username, os.environ.get("MAIL_PASSWORD", ""))
            smtp.send_message(email)
    except (OSError, smtplib.SMTPException) as exc:
        # The message is already saved in the database, so don't fail the request.
        app.logger.error("Could not email contact message: %s", exc)


if __name__ == "__main__":
    app.run(debug=True)
