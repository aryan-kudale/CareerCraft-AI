"""
CareerCraft AI – Main Flask Application
IBM watsonx.ai powered career guidance platform
"""
import os
import sys
import json
import logging
import traceback
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: load .env before anything else
# ---------------------------------------------------------------------------
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"[OK] Loaded .env from {env_path}")
else:
    load_dotenv()
    print("[WARN] .env file not found – using environment variables")

# ---------------------------------------------------------------------------
# Flask and extensions
# ---------------------------------------------------------------------------
from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for, flash
)
from werkzeug.utils import secure_filename

# ---------------------------------------------------------------------------
# Local utilities
# ---------------------------------------------------------------------------
from utils.watsonx_client import WatsonxClient
from utils.resume_parser import extract_text, score_resume, extract_skills

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("careercraft")

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "careercraft-dev-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024   # 5 MB upload limit
app.config["UPLOAD_EXTENSIONS"] = {".pdf", ".docx", ".doc", ".txt"}

# ---------------------------------------------------------------------------
# watsonx client (singleton)
# ---------------------------------------------------------------------------
wx = WatsonxClient()
logger.info("watsonx status: %s – %s", wx.status, wx.status_message)

# ---------------------------------------------------------------------------
# Demo user profile (in-memory; replace with DB for production)
# ---------------------------------------------------------------------------
DEFAULT_PROFILE = {
    "name": "Alex Johnson",
    "title": "Software Engineer",
    "email": "alex@example.com",
    "location": "San Francisco, CA",
    "experience": "3 years",
    "target_role": "Senior Full-Stack Engineer",
    "skills": ["Python", "JavaScript", "React", "Docker", "SQL"],
    "bio": "Passionate software engineer focused on building scalable web applications.",
    "github": "https://github.com/alexj",
    "linkedin": "https://linkedin.com/in/alexj",
    "resume_score": 72,
    "career_stage": "Mid-level",
}


def get_profile():
    return session.get("profile", DEFAULT_PROFILE.copy())


def save_profile(data: dict):
    session["profile"] = data
    session.modified = True


# ---------------------------------------------------------------------------
# Context processors
# ---------------------------------------------------------------------------
@app.context_processor
def inject_globals():
    return {
        "watsonx_status": wx.status,
        "watsonx_message": wx.status_message,
        "current_year": datetime.utcnow().year,
        "profile": get_profile(),
    }


# ===========================================================================
# ROUTES – Pages
# ===========================================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    profile = get_profile()
    stats = {
        "resume_score": profile.get("resume_score", 0),
        "skills_count": len(profile.get("skills", [])),
        "career_stage": profile.get("career_stage", "Early"),
        "target_role": profile.get("target_role", "Not set"),
    }
    return render_template("dashboard.html", stats=stats)


@app.route("/chat")
def chat():
    if "chat_history" not in session:
        session["chat_history"] = []
    return render_template("chat.html", history=session.get("chat_history", []))


@app.route("/resume")
def resume():
    return render_template("resume.html")


@app.route("/roadmap")
def roadmap():
    profile = get_profile()
    return render_template("roadmap.html", profile=profile)


@app.route("/skills")
def skills():
    profile = get_profile()
    return render_template("skills.html", profile=profile)


@app.route("/profile", methods=["GET", "POST"])
def profile_page():
    if request.method == "POST":
        profile = get_profile()
        profile.update({
            "name": request.form.get("name", profile["name"]),
            "title": request.form.get("title", profile["title"]),
            "email": request.form.get("email", profile["email"]),
            "location": request.form.get("location", profile["location"]),
            "experience": request.form.get("experience", profile["experience"]),
            "target_role": request.form.get("target_role", profile["target_role"]),
            "bio": request.form.get("bio", profile["bio"]),
            "github": request.form.get("github", profile["github"]),
            "linkedin": request.form.get("linkedin", profile["linkedin"]),
        })
        skills_raw = request.form.get("skills", "")
        if skills_raw:
            profile["skills"] = [s.strip() for s in skills_raw.split(",") if s.strip()]
        save_profile(profile)
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile_page"))
    return render_template("profile.html", profile=get_profile())


# ===========================================================================
# ROUTES – API
# ===========================================================================

@app.route("/api/status")
def api_status():
    """Return watsonx connection status; re-checks on each call."""
    result = wx.recheck()
    return jsonify(result)


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Send a message to the AI and return a response."""
    try:
        data = request.get_json(force=True)
        user_message = (data.get("message") or "").strip()
        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        profile = get_profile()
        system_ctx = (
            f"You are CareerCraft AI, a professional career counselor powered by IBM Granite. "
            f"User profile: name={profile['name']}, title={profile['title']}, "
            f"experience={profile['experience']}, target_role={profile['target_role']}, "
            f"skills={', '.join(profile['skills'])}. "
            f"Give concise, actionable career advice. Use markdown formatting."
        )
        full_prompt = f"{system_ctx}\n\nUser: {user_message}\n\nAssistant:"

        response_text = wx.generate(full_prompt, max_tokens=500)

        # Persist to session history (keep last 20)
        history = session.get("chat_history", [])
        history.append({"role": "user", "content": user_message,
                        "time": datetime.utcnow().strftime("%H:%M")})
        history.append({"role": "assistant", "content": response_text,
                        "time": datetime.utcnow().strftime("%H:%M")})
        session["chat_history"] = history[-40:]
        session.modified = True

        return jsonify({"response": response_text, "status": wx.status})
    except Exception as exc:
        logger.error("api_chat error: %s", traceback.format_exc())
        return jsonify({"error": str(exc)}), 500


@app.route("/api/analyze-resume", methods=["POST"])
def api_analyze_resume():
    """Analyze an uploaded resume file."""
    try:
        if "resume" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        f = request.files["resume"]
        if not f.filename:
            return jsonify({"error": "Empty filename"}), 400
        ext = Path(secure_filename(f.filename)).suffix.lower()
        if ext not in app.config["UPLOAD_EXTENSIONS"]:
            return jsonify({"error": f"Unsupported file type: {ext}"}), 400

        raw = f.read()
        text = extract_text(raw, f.filename)
        if not text.strip():
            return jsonify({"error": "Could not extract text from the file"}), 422

        scores = score_resume(text)
        profile = get_profile()

        prompt = (
            f"Analyze this resume and provide detailed feedback.\n\n"
            f"Resume text (first 2000 chars):\n{text[:2000]}\n\n"
            f"Detected skills: {', '.join(scores['skills_found'])}\n"
            f"Word count: {scores['word_count']}\n"
            f"Target role: {profile.get('target_role', 'Not specified')}\n\n"
            f"Provide: 1) Overall assessment 2) Strengths 3) Areas for improvement "
            f"4) Specific suggestions 5) ATS optimisation tips. Use markdown."
        )
        ai_feedback = wx.generate(prompt, max_tokens=700)

        # Update profile score
        p = get_profile()
        p["resume_score"] = scores["score"]
        if scores["skills_found"]:
            existing = set(s.lower() for s in p.get("skills", []))
            for sk in scores["skills_found"]:
                if sk.lower() not in existing:
                    p["skills"].append(sk)
        save_profile(p)

        return jsonify({
            "score": scores["score"],
            "skills": scores["skills_found"],
            "word_count": scores["word_count"],
            "has_email": scores["has_email"],
            "has_phone": scores["has_phone"],
            "has_linkedin": scores["has_linkedin"],
            "ai_feedback": ai_feedback,
        })
    except Exception as exc:
        logger.error("api_analyze_resume error: %s", traceback.format_exc())
        return jsonify({"error": str(exc)}), 500


@app.route("/api/generate-roadmap", methods=["POST"])
def api_generate_roadmap():
    """Generate a personalised career roadmap."""
    try:
        data = request.get_json(force=True)
        profile = get_profile()
        current_role = data.get("current_role", profile.get("title", "Professional"))
        target_role = data.get("target_role", profile.get("target_role", "Senior Engineer"))
        timeline = data.get("timeline", "12 months")
        skills = data.get("skills", profile.get("skills", []))

        prompt = (
            f"Create a detailed career roadmap for transitioning from '{current_role}' "
            f"to '{target_role}' in {timeline}.\n"
            f"Current skills: {', '.join(skills)}\n\n"
            f"Structure your roadmap as:\n"
            f"**Phase 1 (0-3 months):** Foundation & Assessment\n"
            f"**Phase 2 (3-6 months):** Skill Building\n"
            f"**Phase 3 (6-9 months):** Practical Application\n"
            f"**Phase 4 (9-12 months):** Job Search & Interview Prep\n\n"
            f"For each phase list: goals, specific learning resources, milestones. Use markdown."
        )
        roadmap_text = wx.generate(prompt, max_tokens=800)
        return jsonify({"roadmap": roadmap_text, "status": wx.status})
    except Exception as exc:
        logger.error("api_generate_roadmap error: %s", traceback.format_exc())
        return jsonify({"error": str(exc)}), 500


@app.route("/api/skill-gap", methods=["POST"])
def api_skill_gap():
    """Analyse skill gaps for a target role."""
    try:
        data = request.get_json(force=True)
        profile = get_profile()
        target_role = data.get("target_role", profile.get("target_role", "Senior Engineer"))
        current_skills = data.get("skills", profile.get("skills", []))

        prompt = (
            f"Perform a skill gap analysis for someone targeting the role: '{target_role}'.\n"
            f"Current skills: {', '.join(current_skills)}\n\n"
            f"Provide:\n"
            f"1. **Required Skills** – top skills needed for this role\n"
            f"2. **Your Strengths** – skills you already have that are relevant\n"
            f"3. **Skill Gaps** – critical missing skills\n"
            f"4. **Learning Resources** – specific courses/certifications for each gap\n"
            f"5. **Priority Order** – which gaps to close first\n\n"
            f"Be specific and actionable. Use markdown formatting."
        )
        analysis = wx.generate(prompt, max_tokens=700)
        return jsonify({"analysis": analysis, "status": wx.status})
    except Exception as exc:
        logger.error("api_skill_gap error: %s", traceback.format_exc())
        return jsonify({"error": str(exc)}), 500


@app.route("/api/clear-chat", methods=["POST"])
def api_clear_chat():
    session.pop("chat_history", None)
    return jsonify({"ok": True})


# ===========================================================================
# Error handlers
# ===========================================================================

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404,
                           message="Page not found"), 404


@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large (max 5 MB)"}), 413


@app.errorhandler(500)
def server_error(e):
    logger.error("500 error: %s", e)
    return render_template("error.html", code=500,
                           message="Internal server error – check logs"), 500


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

    print("\n" + "=" * 60)
    print("  CareerCraft AI – IBM watsonx.ai Powered")
    print("=" * 60)
    print(f"  URL     : http://localhost:{port}")
    print(f"  Debug   : {debug}")
    print(f"  watsonx : {wx.status.upper()} – {wx.status_message}")
    print("=" * 60 + "\n")

    app.run(host="0.0.0.0", port=port, debug=debug)
