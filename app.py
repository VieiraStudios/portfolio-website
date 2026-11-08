import json
import os
import secrets
import smtplib
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for

from content import CATEGORIES, PROCESS, PROJECT_TYPES, PROJECTS, SERVICES, SOCIAL_LINKS, TOOLKIT
from forms import ContactForm

app = Flask(__name__)

# SECRET_KEY signs session cookies and CSRF tokens. In production it must be
# set as an environment variable (see .env.example). Locally, a random key is
# generated each time the server starts.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # reject request bodies over 64 KB
app.config["MESSAGES_FILE"] = Path(app.instance_path) / "messages.jsonl"

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

        message = {
            "received_at": datetime.now(timezone.utc).isoformat(),
            "name": form.name.data.strip(),
            "email": form.email.data.strip(),
            "project_type": dict(PROJECT_TYPES)[form.project_type.data],
            "message": form.message.data.strip(),
        }
        _save_message(message)
        _email_message(message)

        # Post/Redirect/Get: redirecting stops the browser from re-sending
        # the form if the visitor refreshes the page.
        return redirect(url_for("contact", sent=1))

    return render_template("contact.html", form=form, sent=request.args.get("sent") == "1")


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


def _rate_limited(ip: str) -> bool:
    now = time.monotonic()
    attempts = _contact_attempts[ip]
    while attempts and now - attempts[0] > CONTACT_WINDOW_SECONDS:
        attempts.popleft()
    if len(attempts) >= CONTACT_LIMIT:
        return True
    attempts.append(now)
    return False


def _save_message(message: dict) -> None:
    """Append the message to a local file (one JSON object per line)."""
    path = Path(app.config["MESSAGES_FILE"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(message) + "\n")


def _email_message(message: dict) -> None:
    """Email the message to you, if email settings are configured in .env."""
    server = os.environ.get("MAIL_SERVER")
    recipient = os.environ.get("MAIL_TO")
    if not server or not recipient:
        return

    email = EmailMessage()
    email["Subject"] = f"New enquiry: {message['project_type']}"
    email["From"] = os.environ.get("MAIL_FROM", os.environ.get("MAIL_USERNAME", recipient))
    email["To"] = recipient
    email["Reply-To"] = message["email"]
    email.set_content(
        f"Name: {message['name']}\n"
        f"Email: {message['email']}\n"
        f"Project type: {message['project_type']}\n\n"
        f"{message['message']}\n"
    )

    try:
        with smtplib.SMTP(server, int(os.environ.get("MAIL_PORT", 587)), timeout=10) as smtp:
            smtp.starttls()
            username = os.environ.get("MAIL_USERNAME")
            if username:
                smtp.login(username, os.environ.get("MAIL_PASSWORD", ""))
            smtp.send_message(email)
    except (OSError, smtplib.SMTPException) as exc:
        # The message is already saved to the file, so don't fail the request.
        app.logger.error("Could not email contact message: %s", exc)


if __name__ == "__main__":
    app.run(debug=True)
