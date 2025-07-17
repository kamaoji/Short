# app.py (Link Locker Version)

import os
import secrets
from flask import Flask, render_template, request, redirect, jsonify, abort
from flask_sqlalchemy import SQLAlchemy

# --- App & Database Configuration ---
app = Flask(__name__)
db_url = os.environ.get("DATABASE_URL", "sqlite:///db.sqlite")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# --- NEW Database Model ---
# We now store three URLs for each link
class LockedLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    destination_url = db.Column(db.String(), nullable=False)
    youtube_url = db.Column(db.String(), nullable=False)
    telegram_url = db.Column(db.String(), nullable=False)
    short_code = db.Column(db.String(8), unique=True, nullable=False)

# --- App Routes ---

@app.route("/", methods=["GET"])
def index():
    """Render the creator's dashboard."""
    return render_template("index.html")

@app.route("/create", methods=["POST"])
def create_locked_link():
    """API endpoint to create a new locked link."""
    data = request.get_json()
    destination_url = data.get("destination_url")
    youtube_url = data.get("youtube_url")
    telegram_url = data.get("telegram_url")

    if not all([destination_url, youtube_url, telegram_url]):
        return jsonify({"error": "All three URLs are required."}), 400

    while True:
        short_code = secrets.token_urlsafe(6)
        if not LockedLink.query.filter_by(short_code=short_code).first():
            break
            
    new_link = LockedLink(
        destination_url=destination_url,
        youtube_url=youtube_url,
        telegram_url=telegram_url,
        short_code=short_code
    )
    db.session.add(new_link)
    db.session.commit()

    locked_url = request.host_url + short_code
    return jsonify({"locked_url": locked_url})

@app.route("/<short_code>")
def unlock_page(short_code):
    """Serves the unlock page to visitors."""
    link = LockedLink.query.filter_by(short_code=short_code).first()
    if not link:
        abort(404) # Not Found
        
    return render_template(
        "unlock.html",
        destination_url=link.destination_url,
        youtube_url=link.youtube_url,
        telegram_url=link.telegram_url
    )

# Create the new database table if it doesn't exist
with app.app_context():
    db.create_all()
