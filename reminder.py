# ========================
# reminder.py
# Daily motivational email sender
# Run this file daily using a scheduler (APScheduler or cron)
# ========================

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo

load_dotenv(override=True)

# ── Config ──────────────────────────────────────
EMAIL_HOST     = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT     = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM     = os.getenv("EMAIL_FROM") or EMAIL_USERNAME
SITE_URL       = "https://floxenstudyhours.com"

# ── MongoDB ──────────────────────────────────────
mongo_client  = MongoClient(os.environ.get("MONGODB_URI"))
db            = mongo_client["flask_db"]
users_col     = db["users"]

# ── Motivational messages (rotates daily) ────────
MESSAGES = [
    ("Your goals don't take a day off 🎯",
     "Even 25 minutes of focused study today puts you ahead of where you were yesterday. Open a lecture, set your timer, and start."),

    ("Every expert was once a beginner 📚",
     "The students who crack JEE, NEET, and board exams aren't smarter — they're more consistent. Today's session is one more brick in that wall."),

    ("Small steps, big results 🚀",
     "You don't need a perfect 4-hour session. A single focused 30-minute session today beats zero. Come back and watch one lecture."),

    ("Your future self is counting on today 🌟",
     "The effort you put in right now — when it's hard, when you don't feel like it — is exactly what separates you from the rest. Let's go."),

    ("Distraction-free = deeper learning 🧠",
     "Studies show focused, uninterrupted study sessions improve retention by up to 40%. Your Floxen session is waiting — no distractions, just you and your lecture."),

    ("One lecture. One session. One step forward. ⏱",
     "You don't have to study everything today. Just open one video, set your timer, and give it your full attention. That's enough."),

    ("Consistency is your superpower 💪",
     "The habit of showing up daily — even for short sessions — compounds into extraordinary results over weeks and months. Today is part of that chain."),
]

# ── HTML Email Template ───────────────────────────
def build_html_email(name: str, subject_line: str, message_body: str) -> str:
    greeting = f"Hi {name.split('@')[0].capitalize()}," if "@" in name else f"Hi {name},"
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{subject_line}</title>
</head>
<body style="margin:0;padding:0;background:#f0f4ff;font-family:'Segoe UI',Arial,sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4ff;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="max-width:600px;width:100%;background:#ffffff;
                      border-radius:16px;overflow:hidden;
                      box-shadow:0 4px 24px rgba(10,36,99,0.10);">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#0A2463,#1E5FA8);
                       padding:32px 40px;text-align:center;">
              <div style="font-size:28px;margin-bottom:8px;">⏱</div>
              <div style="font-family:Georgia,serif;font-size:22px;
                          font-weight:700;color:#ffffff;letter-spacing:0.5px;">
                Floxen Study Hours
              </div>
              <div style="font-size:12px;color:rgba(255,255,255,0.6);
                          margin-top:4px;letter-spacing:0.08em;text-transform:uppercase;">
                Your distraction-free study companion
              </div>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px 40px 32px;">

              <p style="font-size:15px;color:#3D4F63;margin:0 0 8px;">{greeting}</p>

              <h2 style="font-family:Georgia,serif;font-size:22px;
                         color:#0A2463;margin:0 0 20px;line-height:1.3;">
                {subject_line}
              </h2>

              <p style="font-size:15px;color:#4A5568;line-height:1.75;margin:0 0 28px;">
                {message_body}
              </p>

              <!-- CTA Button -->
              <table cellpadding="0" cellspacing="0" style="margin:0 auto 28px;">
                <tr>
                  <td align="center"
                      style="background:#3A86FF;border-radius:50px;padding:0;">
                    <a href="{SITE_URL}"
                       style="display:inline-block;padding:14px 32px;
                              font-size:15px;font-weight:600;
                              color:#ffffff;text-decoration:none;
                              letter-spacing:0.3px;">
                      Start Studying Now →
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Divider -->
              <hr style="border:none;border-top:1px solid #E8F0FE;margin:0 0 24px;"/>

              <!-- Tip box -->
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="background:#EEF4FF;border-radius:10px;
                             border-left:4px solid #3A86FF;padding:16px 18px;">
                    <p style="margin:0;font-size:13px;color:#0A2463;line-height:1.6;">
                      💡 <strong>Quick tip:</strong> Paste your YouTube lecture URL into
                      Floxen, set a 25–45 minute timer, and study with zero sidebar
                      distractions. Your activity gets logged automatically.
                    </p>
                  </td>
                </tr>
              </table>

            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#F7F9FF;padding:20px 40px;
                       border-top:1px solid #E8F0FE;text-align:center;">
              <p style="font-size:12px;color:#9BA8BB;margin:0 0 8px;">
                You are receiving this because you enabled study reminders on
                <a href="{SITE_URL}" style="color:#3A86FF;text-decoration:none;">
                  floxenstudyhours.com</a>
              </p>
              <p style="font-size:12px;color:#9BA8BB;margin:0;">
                To turn off reminders, go to
                <a href="{SITE_URL}/dashboard"
                   style="color:#3A86FF;text-decoration:none;">
                  your dashboard → menu → notifications off</a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>

</body>
</html>
"""

# ── Send one email ────────────────────────────────
def send_reminder(recipient: str, subject: str, html_body: str) -> bool:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Floxen Study Hours <{EMAIL_FROM}>"
    msg["To"]      = recipient
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"  ✅ Sent to {recipient}")
        return True
    except Exception as e:
        print(f"  ❌ Failed for {recipient}: {e}")
        return False

# ── Main runner ───────────────────────────────────
def send_daily_reminders():
    now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))

    # Pick message based on day of year so it rotates
    msg_index   = now_ist.timetuple().tm_yday % len(MESSAGES)
    subject_line, message_body = MESSAGES[msg_index]

    # Fetch all users with notifications enabled
    users = list(users_col.find(
        {"notifications_enabled": True},
        {"email": 1, "_id": 0}
    ))

    print(f"\n📬 Floxen Daily Reminder — {now_ist.strftime('%d %b %Y, %I:%M %p IST')}")
    print(f"📋 Sending to {len(users)} user(s)")
    print(f"📝 Today's message: \"{subject_line}\"\n")

    sent = 0
    for user in users:
        email = user.get("email", "")
        if not email:
            continue
        html = build_html_email(email, subject_line, message_body)
        if send_reminder(email, f"Floxen: {subject_line}", html):
            sent += 1

    print(f"\n✅ Done — {sent}/{len(users)} emails sent successfully.")

# ── Entry point ───────────────────────────────────
if __name__ == "__main__":
    send_daily_reminders()