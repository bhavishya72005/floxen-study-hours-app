# ========================
# Imports
# ========================
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError



# ========================
# App & Environment Setup
# ========================
load_dotenv()

app = Flask(__name__)
app.secret_key = "your_secret_key"  # move to .env in future

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# ========================
# External Clients
# ========================

# OpenAI client (AI chatbot)
openai_client = OpenAI(api_key=OPENAI_KEY)

# MongoDB client (database)
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["flask_db"]
users_collection = db["users"]


# ========================
# Routes
# ========================

@app.route("/")
def home():
    return redirect(url_for("register"))


# ---------- AUTH ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = users_collection.find_one({"username": username})

        if user and user["password"] == password:
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials. Please try again.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Username and password cannot be empty.", "danger")
            return redirect(url_for("register"))

        if users_collection.find_one({"username": username}):
            flash("Username already taken.", "danger")
            return redirect(url_for("register"))

        users_collection.insert_one({
            "username": username,
            "password": password
        })

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("floxenstudyhours.html")


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for("login"))

    return render_template("dashboard.html", username=session["username"])


@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


# ---------- CHATBOT ----------
@app.route("/chat", methods=["POST"])
def chat():
    if "username" not in session:
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
                        "If the question is unrelated, gently guide the student back to studying."
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

# ========================
# Run Server
# ========================
if __name__ == "__main__":
    app.run(debug=True)

