# ========================
# Imports
# ========================

import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask import send_from_directory
from openai import OpenAI, OpenAIError
from pymongo import MongoClient

from apscheduler.schedulers.background import BackgroundScheduler
from reminder import send_daily_reminders


# ========================
# App & Environment Setup
# ========================
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM") or EMAIL_USERNAME
WELCOME_EMAIL_SUBJECT = "Welcome to Floxen Study Hours"
WELCOME_EMAIL_BODY = (
    "Hi there,\n\n"
    "Welcome to Floxen Study Hours! We are thrilled you signed up and hope this distraction-free study space helps you conquer your goals.\n"
    "If you ever need a reset, come back, drop in a YouTube link, and let the session begin.\n\n"
    "Focus on what matters,\n"
    "Floxen Study Hours Team"
)

# ========================
# External Clients
# ========================

# OpenAI client (AI chatbot)
openai_client = OpenAI(api_key=OPENAI_KEY)

 

# ========================
# MongoDB client (database)
# ========================

# Set override=True to ensure the .env file values take precedence
load_dotenv(override=True)

mongo_uri = os.environ.get("MONGODB_URI")



mongo_client = MongoClient(mongo_uri)
db = mongo_client["flask_db"]
users_collection = db["users"]
activity_collection = db["watch_activity"]


def send_notification_email(recipient: str, subject: str, body: str) -> bool:
    if not all([EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_HOST, EMAIL_PORT]):
        app.logger.warning("Email settings incomplete; skipping notification to %s", recipient)
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = recipient
    msg.set_content(body)

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as exc:
        app.logger.error("Failed to send notification to %s: %s", recipient, exc)
        return False

# ========================
# Routes
# ========================

@app.route("/")
def home():
    return redirect(url_for("register"))

@app.route("/robots.txt")
def robots_txt():
    return send_from_directory("static", "robots.txt")

@app.route("/mongo-test")
def mongo_test():
    users_collection.insert_one({"status": "connected"})
    return "MongoDB connected 🎉"

# ---------- BLOG ----------
@app.route("/blog")
def blog():
    return render_template("blogs/blog.html")

@app.route("/blog/how-floxen-works")
def blog_how_floxen_works():
    return render_template("blogs/how-floxen-works.html")

@app.route("/blog/stop-youtube-distraction")
def blog_stop_distraction():
    return render_template("blogs/stop-youtube-distraction.html")

@app.route("/blog/pomodoro-technique")
def blog_pomodoro():
    return render_template("blogs/pomodoro-technique.html")

# ---------- AUTH ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = users_collection.find_one({"email": email})

        if user and user["password"] == password:
            session["email"] = email
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials. Please try again.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Email and password cannot be empty.", "danger")
            return redirect(url_for("register"))

        if users_collection.find_one({"email": email}):
            flash("Email already registered!", "danger")
            return redirect(url_for("register"))

        if "@gmail.com" not in email:
            flash("Please enter a valid Gmail address.", "danger")
            return redirect(url_for("register"))

        new_user = {
            "email": email,
            "password": password,
            "notifications_enabled": True,
            "welcome_email_sent": False,
            "created_at": datetime.now(ZoneInfo("Asia/Kolkata"))
        }

        users_collection.insert_one(new_user)

        if send_notification_email(email, WELCOME_EMAIL_SUBJECT, WELCOME_EMAIL_BODY):
            users_collection.update_one(
                {"email": email},
                {"$set": {"welcome_email_sent": True}}
            )

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("floxenstudyhours.html")


@app.route("/dashboard")
def dashboard():
    if "email" not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["email"]}) or {}
    notifications_enabled = bool(user.get("notifications_enabled", False))
    return render_template(
        "dashboard.html",
        email=session["email"],
        notifications_enabled=notifications_enabled
    )


@app.route("/toggle-notifications", methods=["POST"])
def toggle_notifications():
    if "email" not in session:
        return jsonify({"ok": False, "message": "Please log in first."}), 401

    data = request.get_json(silent=True) or {}
    enabled = data.get("enabled")

    if not isinstance(enabled, bool):
        return jsonify({"ok": False, "message": "Missing or invalid value."}), 400

    email = session["email"]
    users_collection.update_one(
        {"email": email},
        {"$set": {"notifications_enabled": enabled}}
    )

    user = users_collection.find_one({"email": email}) or {}
    welcome_sent = user.get("welcome_email_sent", False)

    if enabled and not welcome_sent:
        if send_notification_email(email, WELCOME_EMAIL_SUBJECT, WELCOME_EMAIL_BODY):
            users_collection.update_one(
                {"email": email},
                {"$set": {"welcome_email_sent": True}}
            )

    return jsonify({"ok": True, "enabled": enabled})

@app.route("/timer-theme")
def timer_theme():
    if "email" not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for("login"))

    return render_template("Timer Theme.html", email=session["email"])

@app.route("/your-activity")
def your_activity():
    if "email" not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for("login"))

    return render_template("your-activity.html", email=session["email"])

@app.route("/activity/log", methods=["POST"])
def log_activity():
    if "email" not in session:
        return jsonify({"ok": False, "message": "Please log in first."}), 401

    data = request.get_json(silent=True) or {}
    link = (data.get("link") or "").strip()
    video_id = (data.get("video_id") or "").strip()

    if not link:
        return jsonify({"ok": False, "message": "Link is required."}), 400

    now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))

    activity_collection.insert_one({
        "email": session["email"],
        "link": link,
        "video_id": video_id,
        "watched_at": now_ist,
        "watched_date": now_ist.strftime("%Y-%m-%d")
    })

    return jsonify({"ok": True})

@app.route("/activity-data")
def activity_data():
    if "email" not in session:
        return jsonify({"ok": False, "message": "Please log in first."}), 401

    email = session["email"]
    entries = activity_collection.find(
        {"email": email},
        {"_id": 0, "link": 1, "video_id": 1, "watched_at": 1, "watched_date": 1}
    ).sort("watched_at", -1)

    grouped = {}
    for item in entries:
        date_key = item.get("watched_date", "Unknown Date")
        grouped.setdefault(date_key, [])
        watched_at = item.get("watched_at")
        time_str = watched_at.strftime("%I:%M %p") if watched_at else ""
        grouped[date_key].append({
            "link": item.get("link", ""),
            "video_id": item.get("video_id", ""),
            "time": time_str
        })

    result = [{"date": date, "items": grouped[date]} for date in sorted(grouped.keys(), reverse=True)]
    return jsonify({"ok": True, "activity": result})


@app.route("/logout")
def logout():
    session.pop("email", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


# ---------- CHATBOT ----------
@app.route("/chat", methods=["POST"])
def chat():
    if "email" not in session:
        return jsonify({"reply": "Please log in to use the assistant."})

    data = request.json
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Ask a study-related question."})

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Floxen, a calm and distraction-free study assistant. "
                        "Only answer academic doubts, concepts, or study-related questions. "
                        "If the question is unrelated, gently guide the student back to studying. "
                        "Respond in plain text only. Do not use Markdown symbols like **, *, #, or bullets. "
                        "Use short paragraphs or numbered lines with clear line breaks."
                    )
                },
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=200
        )

        reply = response.choices[0].message.content
        return jsonify({"reply": reply})


    except OpenAIError as e:

        # OpenAI-specific issues (quota, auth, network, etc.)

        app.logger.error(f"OpenAI API error: {e}")

        return jsonify({

            "reply": "The study assistant is temporarily unavailable. Please try again shortly."

        }), 503


    except ValueError as e:

        # Input / data-related issues

        app.logger.error(f"Invalid input: {e}")

        return jsonify({

            "reply": "Invalid request. Please rephrase your question."

        }), 400


    except RuntimeError as e:

        # Known runtime problems

        app.logger.error(f"Runtime error: {e}")

        return jsonify({

            "reply": "A server issue occurred. Please try again."

        }), 500

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/sitemap.xml")
def sitemap():
    return send_from_directory('static', 'sitemap.xml')

@app.route('/googlead60dc2cca06b5e4.html')
def google_verify():
    return app.send_static_file('googlead60dc2cca06b5e4.html')


# ========================
# Run Server
# ========================
if __name__ == "__main__":
    # ========================
    # Daily Reminder Scheduler
    # Runs every day at 8:00 PM IST
    # ========================
    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
    scheduler.add_job(
        send_daily_reminders,
        trigger="cron",
        hour=14,  # 8 PM IST
        minute=15,
        id="daily_reminder",
        replace_existing=True
    )
    scheduler.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
