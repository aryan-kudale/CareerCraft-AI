# CareerCraft AI

**AI-powered career guidance platform** — built with Python Flask and IBM watsonx.ai Granite models.

## Features

| Feature | Description |
|---|---|
| 🤖 AI Career Chat | Real-time career advice via IBM Granite |
| 📄 Resume Analyser | Upload PDF/DOCX for AI-powered scoring |
| 🗺️ Career Roadmap | Personalised step-by-step roadmap |
| ⚡ Skill Gap Analysis | Know exactly what to learn next |
| 📊 Dashboard | Visual career progress tracking |
| 👤 Profile Manager | Manage your professional details |
| 🌙 Dark Mode | Full dark/light theme switching |
| 📱 Responsive | Works on desktop, tablet, and mobile |

---

## Quick Start (Windows)

### 1. Double-click `run.bat`

That's it! The script will:
- Detect your Python version
- Create a virtual environment
- Install all dependencies in the correct order
- Verify imports
- Start the application

Then open **http://localhost:5000** in your browser.

---

## Manual Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip wheel setuptools

# Install dependencies
pip install -r requirements.txt

# Copy .env template
copy .env.example .env

# Start the app
python app.py
```

---

## IBM watsonx.ai Configuration

The app works in **Demo Mode** without IBM credentials. To enable full AI:

1. Get an IBM Cloud account: https://cloud.ibm.com
2. Create a watsonx.ai project: https://dataplatform.cloud.ibm.com
3. Generate an API key: IBM Cloud → Manage → Access → API keys
4. Edit `.env`:

```env
IBM_API_KEY=your_actual_api_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

5. Restart the app — the green dot in the navbar confirms the connection.

---

## Status Indicator

The navbar shows your IBM connection status:

| Indicator | Meaning |
|---|---|
| 🟢 **IBM Granite Live** | Full AI connected and working |
| 🟡 **Demo Mode** | No IBM credentials — smart fallback responses |
| 🔴 **Connection Error** | Credentials set but connection failed |

---

## Project Structure

```
CareerCraft_AI/
├── app.py                  ← Flask application entry point
├── requirements.txt        ← Pinned Python dependencies
├── run.bat                 ← Windows one-click launcher
├── .env.example            ← Environment variables template
├── .env                    ← Your actual credentials (not committed)
├── README.md
│
├── utils/
│   ├── watsonx_client.py   ← IBM watsonx.ai wrapper
│   └── resume_parser.py    ← PDF/DOCX text extraction
│
├── templates/
│   ├── base.html           ← Shared layout (navbar, footer)
│   ├── index.html          ← Landing page
│   ├── dashboard.html      ← Career dashboard
│   ├── chat.html           ← AI chat interface
│   ├── resume.html         ← Resume analyser
│   ├── roadmap.html        ← Career roadmap generator
│   ├── skills.html         ← Skill gap analysis
│   ├── profile.html        ← Profile management
│   └── error.html          ← Error pages
│
└── static/
    ├── css/main.css        ← Custom styles + dark mode
    └── js/main.js          ← Theme, animations, status polling
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET  | `/api/status` | Check IBM watsonx.ai connectivity |
| POST | `/api/chat` | Send message to AI |
| POST | `/api/analyze-resume` | Upload and analyse resume |
| POST | `/api/generate-roadmap` | Generate career roadmap |
| POST | `/api/skill-gap` | Skill gap analysis |
| POST | `/api/clear-chat` | Clear chat history |

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| Flask | 3.0.3 | Web framework |
| Werkzeug | 3.0.3 | WSGI utilities |
| ibm-watsonx-ai | 1.1.2 | IBM Granite AI |
| python-dotenv | 1.0.1 | Environment config |
| PyPDF2 | 3.0.1 | PDF parsing |
| docx2txt | 0.8 | DOCX parsing |
| numpy | 1.26.4 | Numerical ops |
| requests | 2.32.3 | HTTP client |

---

## Troubleshooting

**Port already in use?**
```bash
# Use a different port
set PORT=5001
python app.py
```

**Package install fails?**
```bash
# Install problematic packages individually
pip install Flask==3.0.3
pip install ibm-watsonx-ai==1.1.2
```

**IBM connection error?**
- Verify your API key in `.env`
- Check your project ID on https://dataplatform.cloud.ibm.com
- Ensure your IBM Cloud account has watsonx.ai access
- Click "Re-check Connection" on the Dashboard

---

## Technology Stack

- **Backend**: Python 3.11, Flask 3.0
- **AI**: IBM watsonx.ai, Granite 13B Chat v2
- **Frontend**: Bootstrap 5.3, Animate.css, Marked.js
- **Resume parsing**: PyPDF2, docx2txt
- **Styling**: CSS custom properties, dark mode

---

*Made with IBM watsonx.ai Granite*
