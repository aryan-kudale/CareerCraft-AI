"""
IBM watsonx.ai client wrapper for CareerCraft AI
Handles authentication, model calls, and graceful fallback
"""
import os
import logging
import json
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class WatsonxClient:
    """IBM watsonx.ai Granite model client with connection status tracking."""

    IAM_URL = "https://iam.cloud.ibm.com/identity/token"

    def __init__(self):
        # Ensure .env is loaded even if called before app.py loads dotenv
        from dotenv import load_dotenv
        from pathlib import Path
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)
        self.api_key = os.environ.get("IBM_API_KEY", "")
        self.project_id = os.environ.get("WATSONX_PROJECT_ID", "")
        self.base_url = os.environ.get("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        self._token = None
        self._token_expiry = None
        self.status = "unchecked"   # unchecked | ok | error | no_credentials
        self.status_message = "Not yet verified"
        self._verify_connection()

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------
    def _get_iam_token(self):
        """Fetch (or return cached) IAM bearer token."""
        if self._token and self._token_expiry and datetime.utcnow() < self._token_expiry:
            return self._token
        if not self.api_key or self.api_key == "your_ibm_api_key_here":
            raise ValueError("IBM_API_KEY not configured")
        resp = requests.post(
            self.IAM_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": self.api_key,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - 60)
        return self._token

    # ------------------------------------------------------------------
    # Connection check
    # ------------------------------------------------------------------
    def _verify_connection(self):
        """Probe the watsonx endpoint and set self.status accordingly."""
        if not self.api_key or self.api_key in ("", "your_ibm_api_key_here"):
            self.status = "no_credentials"
            self.status_message = "IBM credentials not configured – using demo mode"
            logger.warning(self.status_message)
            return
        if not self.project_id or self.project_id in ("", "your_watsonx_project_id_here"):
            self.status = "no_credentials"
            self.status_message = "WATSONX_PROJECT_ID not configured – using demo mode"
            logger.warning(self.status_message)
            return
        try:
            token = self._get_iam_token()
            # Light probe – list foundation models
            url = f"{self.base_url}/ml/v1/foundation_model_specs?version=2024-05-31"
            resp = requests.get(
                url,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                timeout=10,
            )
            if resp.status_code == 200:
                self.status = "ok"
                self.status_message = "IBM watsonx.ai connected successfully"
                logger.info(self.status_message)
            else:
                self.status = "error"
                self.status_message = f"watsonx returned HTTP {resp.status_code}"
                logger.error(self.status_message)
        except Exception as exc:
            self.status = "error"
            self.status_message = f"Connection error: {exc}"
            logger.error(self.status_message)

    def recheck(self):
        """Re-run connection verification – re-reads .env so hot credential edits work."""
        from dotenv import load_dotenv
        from pathlib import Path
        import os
        # Reload .env so credentials edited after startup are picked up
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)
        # Refresh credentials from environment
        self.api_key = os.environ.get("IBM_API_KEY", "")
        self.project_id = os.environ.get("WATSONX_PROJECT_ID", "")
        self.base_url = os.environ.get("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        self._token = None
        self._token_expiry = None
        self._verify_connection()
        return {"status": self.status, "message": self.status_message}

    # ------------------------------------------------------------------
    # Text generation
    # ------------------------------------------------------------------
    def generate(self, prompt: str, model_id: str = "ibm/granite-3-8b-instruct",
                 max_tokens: int = 600, temperature: float = 0.7) -> str:
        """Call watsonx text generation; fall back to demo response on any error."""
        if self.status not in ("ok",):
            return self._demo_response(prompt)
        try:
            token = self._get_iam_token()
            url = f"{self.base_url}/ml/v1/text/generation?version=2024-05-31"
            payload = {
                "model_id": model_id,
                "input": prompt,
                "parameters": {
                    "decoding_method": "greedy",
                    "max_new_tokens": max_tokens,
                    "temperature": temperature,
                    "repetition_penalty": 1.1,
                },
                "project_id": self.project_id,
            }
            resp = requests.post(
                url,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            result = resp.json()
            generated = result["results"][0]["generated_text"].strip()
            return generated if generated else "I couldn't generate a response. Please try again."
        except Exception as exc:
            logger.error("watsonx generate error: %s", exc)
            return self._demo_response(prompt)

    # ------------------------------------------------------------------
    # Demo / offline fallback
    # ------------------------------------------------------------------
    def _demo_response(self, prompt: str) -> str:
        """Return a helpful demo reply when IBM credentials are absent or broken."""
        p = prompt.lower()
        if any(w in p for w in ["resume", "cv"]):
            return ("**Resume Analysis (Demo Mode)**\n\n"
                    "Your resume looks structured. Key suggestions:\n"
                    "• Add measurable achievements (e.g., *increased sales by 20%*)\n"
                    "• Use action verbs: *Led, Built, Designed, Optimised*\n"
                    "• Keep to 1–2 pages; tailor each version to the job description\n"
                    "• Add a concise professional summary at the top\n\n"
                    "*Configure IBM credentials in `.env` to unlock full AI analysis.*")
        if any(w in p for w in ["skill", "learn", "gap"]):
            return ("**Skill Gap Analysis (Demo Mode)**\n\n"
                    "Based on current industry trends:\n"
                    "• **High demand:** Python, Cloud (AWS/Azure/GCP), GenAI/LLMs\n"
                    "• **Growing:** DevOps, Kubernetes, Data Engineering\n"
                    "• **Soft skills:** Communication, Leadership, Agile\n\n"
                    "Recommended learning path: Coursera → Kaggle → Build projects → Contribute to OSS\n\n"
                    "*Configure IBM credentials to get personalised analysis.*")
        if any(w in p for w in ["roadmap", "career", "path", "plan"]):
            return ("**Career Roadmap (Demo Mode)**\n\n"
                    "**Phase 1 – Foundation (0–6 months)**\n"
                    "  Master fundamentals; build 2 portfolio projects\n\n"
                    "**Phase 2 – Specialise (6–18 months)**\n"
                    "  Pick a domain; certify (AWS/GCP/Azure, etc.)\n\n"
                    "**Phase 3 – Lead (18–36 months)**\n"
                    "  Mentor others; open-source contributions; target senior roles\n\n"
                    "*Configure IBM credentials for a personalised roadmap.*")
        if any(w in p for w in ["interview", "question", "prep"]):
            return ("**Interview Prep (Demo Mode)**\n\n"
                    "Common patterns:\n"
                    "• **Behavioural:** Use STAR (Situation → Task → Action → Result)\n"
                    "• **Technical:** Think aloud; ask clarifying questions first\n"
                    "• **System Design:** Start with requirements, then scale\n\n"
                    "*Configure IBM credentials for tailored interview coaching.*")
        return ("**CareerCraft AI (Demo Mode)**\n\n"
                "Hello! I'm CareerCraft, your AI career assistant.\n\n"
                "I can help you with:\n"
                "• 📄 Resume analysis & optimisation\n"
                "• 🗺️ Career roadmap planning\n"
                "• 🔍 Skill gap identification\n"
                "• 💬 Interview preparation\n"
                "• 📊 Job market insights\n\n"
                "To enable full IBM Granite AI, add your credentials to `.env`.\n"
                "In the meantime, ask me anything – I'll give you solid guidance!")
