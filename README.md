# PrepAI - AI-Powered Interview Preparation Platform

An intelligent interview preparation tool powered by AWS Bedrock Agents with real-time voice communication capabilities.

## Project Status

**Phase 1: Foundation - ✅ COMPLETED** (October 13, 2025)
**Phase 2: AI Agent Core - ✅ COMPLETED & DEPLOYED** (October 16, 2025)

### Current Deployment
- **Bedrock Agent:** Active (Agent ID: `V43BCCYVLK`)
- **Knowledge Base:** Synced with 230+ questions
- **Backend Integration:** Tested and working
- **Status:** Ready for voice pipeline integration

### Quick Links

- 🚀 **[Quick Start Guide (Phase 2)](QUICKSTART_PHASE2.md)** - Get agent running in 30 minutes
- 📖 **[Phase 2 Setup Guide](PHASE2_SETUP_GUIDE.md)** - Detailed instructions
- 📋 **[Phase 2 Summary](PHASE2_SUMMARY.md)** - Complete implementation details
- 🏗️ **[Architecture Guide](ARCHITECTURE_GUIDE.md)** - Full system architecture

### Completed Features

#### Phase 1: Foundation
**Frontend (Next.js)**
- ✅ Landing page with 8 interview type selections
- ✅ Interview session page with voice interface
- ✅ Real-time voice communication UI with transcript display
- ✅ Timer and session management
- ✅ Responsive design with Tailwind CSS

**Backend (FastAPI)**
- ✅ Complete project structure (routers, services, models)
- ✅ Session management API endpoints
- ✅ WebSocket handler for real-time voice streaming
- ✅ faster-whisper integration for Speech-to-Text
- ✅ Coqui TTS integration for natural Text-to-Speech
- ✅ S3 service for persistent storage

#### Phase 2: AI Agent Core
**Bedrock Agent**
- ✅ Voice-optimized AI interviewer (Claude 3.5 Sonnet)
- ✅ 8 interview type support (Google, Amazon, Microsoft, AWS/Azure/GCP SA, Behavioral, Coding)
- ✅ Session state management with context tracking
- ✅ Adaptive difficulty and hint system
- ✅ Professional evaluation criteria

**Knowledge Base (RAG)**
- ✅ 230+ curated interview questions
  - 50+ Technical DSA problems with solutions
  - 100+ Behavioral STAR method questions
  - 80+ Cloud Solutions Architect scenarios
- ✅ Automatic question retrieval based on context
- ✅ S3 upload automation

**Testing & Documentation**
- ✅ Comprehensive test suite (4 automated tests)
- ✅ Step-by-step setup guides
- ✅ Quick start guide (30-minute deployment)

## Tech Stack

### Frontend
- **Framework:** Next.js 14+ (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Real-time:** WebSocket for voice streaming

### Backend
- **Framework:** FastAPI
- **Language:** Python 3.12
- **Voice Processing:**
  - **STT:** faster-whisper (local, cost-effective)
  - **TTS:** Piper TTS (local neural voice)
- **AI:** AWS Bedrock Agent with Claude 3.5 Sonnet

### AWS Services
- **Amazon Bedrock Agent** - Core AI interview agent
- **AWS Lambda** - Serverless compute (future deployment)
- **Amazon S3** - Session data, recordings, transcripts
- **API Gateway** - WebSocket & REST APIs (future deployment)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Frontend (Next.js + React)                  │
│  Landing Page → Voice Interview Page (Mic + Transcripts)    │
└────────────────────────┬────────────────────────────────────┘
                         │ WebSocket (Binary Audio + JSON)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           Backend (FastAPI - Voice Processing)              │
│  Audio → faster-whisper → Bedrock Agent → Piper TTS        │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┴────────────────┐
          ▼                               ▼
┌──────────────────┐           ┌──────────────────┐
│ Amazon Bedrock   │           │    Amazon S3     │
│     Agent        │           │  (Sessions,      │
│ (Claude LLM)     │           │   Transcripts)   │
└──────────────────┘           └──────────────────┘
```

## Setup Instructions

### Prerequisites

- Node.js 18+ and npm
- Python 3.12+
- AWS Account with Bedrock access
- AWS CLI configured

### 1. Clone the Repository

```bash
cd prepai
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your AWS credentials

# Setup AWS resources (S3 buckets)
python setup_aws.py

# Download Piper TTS model
mkdir -p models/piper
# Download from: https://github.com/rhasspy/piper/releases
# Place en_US-lessac-medium.onnx and .json files in models/piper/
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Configure environment
# .env.local is already created with default values
```

### 4. AWS Bedrock Agent Setup

1. Go to AWS Console → Amazon Bedrock → Agents
2. Create a new agent:
   - Name: PrepAI Interview Agent
   - Model: Claude 3.5 Sonnet
   - Instructions: (Use instructions from ARCHITECTURE_GUIDE.md)
3. Create an alias (e.g., "prod")
4. Copy Agent ID and Alias ID to backend/.env:
   ```
   BEDROCK_AGENT_ID=your_agent_id
   BEDROCK_AGENT_ALIAS_ID=your_alias_id
   ```

### 5. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
prepai/
├── frontend/                    # Next.js frontend
│   ├── app/
│   │   ├── page.tsx            # Landing page
│   │   ├── interview/
│   │   │   └── new/
│   │   │       └── page.tsx    # Interview session page
│   │   └── api/                # API routes (proxy)
│   ├── components/
│   │   └── VoiceInterview.tsx  # Voice interface component
│   └── .env.local
│
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── main.py             # FastAPI app
│   │   ├── config.py           # Configuration
│   │   ├── routers/            # API endpoints
│   │   │   ├── sessions.py     # Session management
│   │   │   ├── interviews.py   # Interview endpoints
│   │   │   └── websocket.py    # Voice WebSocket
│   │   ├── services/           # Business logic
│   │   │   ├── s3_service.py   # S3 operations
│   │   │   └── bedrock_service.py  # Bedrock Agent
│   │   └── models/             # Pydantic models
│   │       └── session.py
│   ├── setup_aws.py            # AWS setup script
│   ├── requirements.txt
│   └── .env
│
├── ARCHITECTURE_GUIDE.md       # Detailed architecture
└── README.md                   # This file
```

## S3 Structure

```
prepai-user-data
    folders = [
        'sessions/',
        'recordings/',
        'cvs/',
        'transcripts/',
        'reports/'
    ]
prepai-knowledge-base

```

## How It Works

### Voice Interview Flow

1. **User selects interview type** on landing page
2. **Session created** via REST API, stored in S3
3. **WebSocket connection** established for real-time voice
4. **User speaks** → Microphone captures audio
5. **Silence detected** → Audio sent to backend
6. **faster-whisper transcribes** → Text displayed progressively
7. **Bedrock Agent processes** → Streaming LLM response
8. **Piper TTS generates audio** → Sentence-by-sentence
9. **Audio plays** → User hears AI interviewer
10. **Transcript saved** to S3 after each exchange

### Latency Optimization

- **Streaming at every layer** - Audio, LLM, TTS all stream
- **Sentence-by-sentence TTS** - Audio plays before full response
- **Progressive transcription** - See text while speaking
- **Local models** - No API call latency for STT/TTS

## Environment Variables

### Backend (.env)
```env
AWS_ACCESS_KEY=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
S3_BUCKET_USER_DATA=prepai-user-data
S3_BUCKET_KNOWLEDGE_BASE=prepai-knowledge-base
BEDROCK_AGENT_ID=your_agent_id
BEDROCK_AGENT_ALIAS_ID=your_alias_id
WHISPER_MODEL=small
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Next Steps

### Phase 2: AI Agent Core ✅ COMPLETED
- ✅ Created and configured Bedrock Agent with voice-optimized instructions
- ✅ Setup Knowledge Base with 230+ interview questions (RAG)
- ✅ Tested conversational flow and question adaptation
- ✅ Implemented session state management

### Phase 3: Tools & Action Groups ✅ COMPLETED
- ✅ Code Executor Lambda (run and validate candidate code)
- ✅ CV Analyzer Lambda (extract resume information)
- ✅ Performance Evaluator Lambda (generate comprehensive reports)
- ✅ OpenAPI 3.0 schemas for Action Groups
- ✅ SAM deployment template and scripts
- ✅ Ready for deployment to AWS

### Phase 4: Enhanced Features
- [ ] Upload CV functionality
- [ ] Performance report generation
- [ ] Interview recording playback
- [ ] Multiple interview type personas

### Phase 5: Deployment
- [ ] Deploy backend to AWS Lambda (container)
- [ ] Setup API Gateway (WebSocket + REST)
- [ ] Deploy frontend to Vercel/Amplify
- [ ] Production environment configuration

## API Endpoints

### REST API

- `POST /api/sessions` - Create new interview session
- `GET /api/sessions/{session_id}` - Get session details
- `GET /api/interviews/{session_id}/transcript` - Get transcript
- `POST /api/interviews/{session_id}/end` - End session
- `GET /health` - Health check

### WebSocket

- `WS /ws/interview/{session_id}` - Real-time voice communication
  - Receives: Binary audio chunks, JSON control signals
  - Sends: Binary audio responses, JSON events (transcripts, LLM chunks)

## Cost Estimation

For 100 interviews/month (30 min average):
- **Bedrock Agent:** ~$50-100 (token usage)
- **Lambda:** ~$30-50 (voice processing)
- **S3:** ~$10 (storage)
- **API Gateway:** ~$10 (WebSocket)
- **faster-whisper:** $0 (self-hosted)
- **Piper TTS:** $0 (self-hosted)

**Total: ~$100-170/month** (85% cheaper than cloud STT/TTS)

## Contributing

This is a hackathon project. Contributions welcome!

## License

MIT License

## Built With

- [Next.js](https://nextjs.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [AWS Bedrock](https://aws.amazon.com/bedrock/)
- [faster-whisper](https://github.com/guillaumekln/faster-whisper)
- [Piper TTS](https://github.com/rhasspy/piper)

---

Built for AWS Bedrock Agent Hackathon 🚀
