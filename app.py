# app.py

import os
import secrets
from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy

# --- App & Database Configuration ---

app = Flask(__name__)

# Get the database URL from Render's environment variables
# If it's not set, use a local SQLite database for testing
db_url = os.environ.get("DATABASE_URL", "sqlite:///db.sqlite")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# --- Database Model ---

class Link(db.Model):
    """Database table for storing links."""
    id = db.Column(db.Integer, primary_key=True)
    long_url = db.Column(db.String(), nullable=False)
    short_code = db.Column(db.String(6), unique=True, nullable=False)

# --- App Routes ---

@app.route("/", methods=["GET"])
def index():
    """Render the main page (our dashboard)."""
    return render_template("index.html")

@app.route("/shorten", methods=["POST"])
def shorten_link():
    """API endpoint to create a short link."""
    data = request.get_json()
    long_url = data.get("url")

    if not long_url:
        return jsonify({"error": "URL is required."}), 400

    # Generate a unique short code
    while True:
        short_code = secrets.token_urlsafe(4) # Generate a 6-character code
        if not Link.query.filter_by(short_code=short_code).first():
            break
            
    new_link = Link(long_url=long_url, short_code=short_code)
    db.session.add(new_link)
    db.session.commit()

    short_url = request.host_url + short_code
    return jsonify({"short_url": short_url})

@app.route("/<short_code>")
def redirect_to_url(short_code):
    """Redirects the short link to the original long URL."""
    link = Link.query.filter_by(short_code=short_code).first_or_404()
    return redirect(link.long_url)

# This is needed to create the database table on Render's free tier
with app.app_context():
    db.create_all()