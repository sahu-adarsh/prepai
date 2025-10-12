# AI-Powered Interview Preparation Tool - Architecture Guide

## Project Overview
A modular interview preparation platform that helps students and professionals practice for various interview types using AWS-powered AI agents.

## Architecture Components

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│  ┌──────────────────┐         ┌─────────────────────────────┐  │
│  │  Landing Page    │────────>│  Interview Session Page     │  │
│  │  (Select Type)   │         │  - Chat Interface           │  │
│  │                  │         │  - Live Transcript Display  │  │
│  └──────────────────┘         └─────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS/WebSocket
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AWS API Gateway                             │
│                   (REST + WebSocket APIs)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI on Lambda)                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Session Management Service                     │ │
│  │  - Create interview sessions                                │ │
│  │  - Store conversation history                               │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Amazon Bedrock Agent                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              AI Interview Agent (Core)                      │ │
│  │  - LLM: Claude 3.5 Sonnet                                   │ │
│  │  - Reasoning: Multi-turn conversation logic                 │ │
│  │  - Autonomous: Adapts questions based on responses          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Action Groups (Tools/APIs)                     │ │
│  │  1. Knowledge Base Lookup (RAG)                             │ │
│  │  2. Code Execution Tool                                     │ │
│  │  3. Resume/CV Analysis Tool                                 │ │
│  │  4. Performance Evaluator                                   │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌──────────────┐  ┌──────────────────┐  ┌─────────────────┐
│   Amazon S3  │  │ Bedrock Knowledge│  │  Lambda Tools   │
│              │  │      Base        │  │                 │
│ - Transcripts│  │                  │  │ - Code Runner   │
│ - Resumes    │  │ - Interview Q&A  │  │ - Evaluator     │
│ - Reports    │  │ - Company Data   │  │ - CV Analyzer   │
└──────────────┘  └──────────────────┘  └─────────────────┘
```

---

## Detailed Component Breakdown

### 1. Frontend (Next.js)

**Tech Stack:**
- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS
- WebSocket client for real-time updates
- AWS SDK (if needed for S3 direct uploads)

**Pages:**

#### a) Landing Page (`/`)
```typescript
Features:
- Interview type selection cards
- Categories:
  * Technical Interviews (Google SDE, Amazon SDE, etc.)
  * Solutions Architect (AWS, Azure, GCP)
  * CV Grilling / Behavioral
  * Coding Round Practice
- Start Interview button
```

#### b) Interview Session Page (`/interview/[sessionId]`)
```typescript
Layout:
┌─────────────────────────────────────────┐
│         Header (Timer, End Session)     │
├──────────────────┬──────────────────────┤
│                  │                      │
│   Transcript     │   Chat Interface     │
│   (Left Panel)   │   (Right Panel)      │
│                  │                      │
│   - Live text    │   - Message input    │
│   - Auto-scroll  │   - Send button      │
│   - Timestamps   │   - Voice input      │
│                  │   - File upload      │
│                  │     (for resume)     │
└──────────────────┴──────────────────────┘
│         Performance Hints (Bottom)       │
└─────────────────────────────────────────┘
```

**Key Features:**
- Real-time message streaming via WebSocket
- Live transcript display with auto-scroll
- File upload for CV (stored in S3)
- Export transcript functionality
- Session persistence

---

### 2. Backend (FastAPI)

**Deployment:** AWS Lambda with Function URLs or API Gateway

**Project Structure:**
```
backend/
├── app/
│   ├── main.py                 # FastAPI app entry
│   ├── routers/
│   │   ├── sessions.py         # Session management
│   │   ├── interviews.py       # Interview logic
│   │   └── websocket.py        # WebSocket handler
│   ├── services/
│   │   ├── bedrock_agent.py    # Bedrock Agent integration
│   │   ├── s3_service.py       # S3 operations
│   │   └── transcript.py       # Transcript management
│   ├── models/
│   │   ├── interview.py        # Pydantic models
│   │   └── session.py
│   └── config.py               # AWS configs
└── requirements.txt
```

**Core Endpoints:**

```python
# REST API Endpoints
POST   /api/sessions                    # Create new interview session
GET    /api/sessions/{session_id}       # Get session details
POST   /api/sessions/{session_id}/upload-cv  # Upload resume
POST   /api/interviews/message          # Send message to AI agent
GET    /api/interviews/{session_id}/transcript  # Get full transcript
POST   /api/interviews/{session_id}/end # End session & generate report

# WebSocket
WS     /ws/interview/{session_id}       # Real-time chat connection
```

---

### 3. AWS Bedrock Agent (Core AI Component)

**This is the heart of your hackathon project and meets all requirements.**

#### Agent Configuration

**Base LLM:**
- Claude 3.5 Sonnet (via Bedrock)

**Agent Instructions:**
```
You are an expert technical interviewer conducting a {interview_type} interview.

Your responsibilities:
1. Ask relevant questions based on the interview type
2. Analyze candidate responses for technical accuracy
3. Provide hints when the candidate struggles
4. Adapt difficulty based on candidate performance
5. Evaluate coding solutions if provided
6. Give constructive feedback

Interview Type Context: {interview_context}
Candidate Resume: {resume_summary}

Be professional, encouraging, and thorough.
```

#### Action Groups (Tools)

**1. Knowledge Base Lookup Tool**
- **Purpose:** Retrieve company-specific interview questions, best practices
- **Integration:** Bedrock Knowledge Base (RAG)
- **Data Sources:** S3 bucket with interview questions, company culture docs

**2. Code Execution Tool**
- **Purpose:** Run and validate code submitted by candidates
- **Integration:** Lambda function
- **Technology:** AWS Lambda with containerized Python/JavaScript runtimes

**3. Resume/CV Analysis Tool**
- **Purpose:** Extract skills and experience from uploaded CV
- **Integration:** Lambda + Amazon Textract
- **Output:** Structured JSON with skills, experience, education

**4. Performance Evaluator Tool**
- **Purpose:** Score candidate responses and generate feedback
- **Integration:** Lambda function with custom logic
- **Criteria:** Technical accuracy, communication, problem-solving approach

---

### 4. AWS Services Deep Dive

#### a) Amazon Bedrock Agent (REQUIRED - Core Component)

**Setup Steps:**
1. Create Agent in Bedrock console
2. Select foundation model (Nova Pro or Claude 3.5 Sonnet)
3. Define agent instructions with interview prompt
4. Add action groups (Lambda functions for tools)
5. Create Knowledge Base for RAG
6. Enable session state management

**Agent Primitives to Use:**
- **InvokeAgent:** Main API to send messages and get responses
- **SessionState:** Maintain conversation context
- **ActionGroupInvocation:** Execute tools/functions
- **KnowledgeBaseLookup:** RAG for interview questions

#### b) Amazon Bedrock Knowledge Base

**Purpose:** Store and retrieve interview questions, tips, company info

**Setup:**
1. Create S3 bucket with interview content:
   ```
   s3://prepai-knowledge-base/
   ├── google-sde/
   │   ├── technical-questions.md
   │   ├── coding-patterns.md
   │   └── company-culture.md
   ├── aws-sa/
   │   ├── architecture-scenarios.md
   │   └── service-questions.md
   └── general/
       ├── behavioral-questions.md
       └── resume-tips.md
   ```

2. Create Knowledge Base in Bedrock console
3. Point to S3 bucket
4. Choose embedding model (Amazon Titan Embeddings)
5. Sync data

#### c) AWS Lambda Functions

**Function 1: FastAPI Backend Handler**
```python
# Handles all API requests
# Runtime: Python 3.12
# Memory: 1024 MB
# Timeout: 30s
```

**Function 2: Code Executor**
```python
# Runs candidate code in sandbox
# Runtime: Python 3.12 with container
# Memory: 2048 MB
# Timeout: 60s
# Layers: numpy, pandas (if needed)
```

**Function 3: CV Analyzer**
```python
# Analyzes uploaded resumes
# Runtime: Python 3.12
# Integrations: Textract, Bedrock
# Memory: 512 MB
```

**Function 4: Performance Evaluator**
```python
# Scores responses and generates feedback
# Runtime: Python 3.12
# Memory: 512 MB
```

#### d) Amazon S3 Buckets

**Bucket 1: `prepai-user-data`**
- User uploaded CVs
- Session transcripts
- Performance reports

**Bucket 2: `prepai-knowledge-base`**
- Interview questions
- Company information
- Best practices guides

**Bucket 3: `prepai-frontend` (optional)**
- Static Next.js build (if using S3 + CloudFront)

#### e) Amazon API Gateway

**REST API:**
- Endpoints for session management
- Lambda proxy integration
- CORS enabled

**WebSocket API:**
- Real-time chat connection
- Routes: $connect, $disconnect, message
- Lambda integration for message handling

---

## Implementation Roadmap

### Phase 1: Foundation (Day 1-2)

**Frontend:**
- [ ] Setup Next.js project
- [ ] Create landing page with interview type cards
- [ ] Create interview session page with basic layout
- [ ] Implement chat interface UI

**Backend:**
- [ ] Setup FastAPI project structure
- [ ] Create session management endpoints
- [ ] Setup AWS SDK and credentials

**AWS:**
- [ ] Create S3 buckets
- [ ] Setup IAM roles and policies
- [ ] Deploy Lambda function for FastAPI

### Phase 2: AI Agent Core (Day 2-3)

**Bedrock Agent:**
- [ ] Create Bedrock Agent with Nova/Claude
- [ ] Write detailed agent instructions
- [ ] Test basic conversational flow
- [ ] Implement session state management

**Knowledge Base:**
- [ ] Prepare interview question documents
- [ ] Create Bedrock Knowledge Base
- [ ] Connect Knowledge Base to Agent
- [ ] Test RAG retrieval

### Phase 3: Tools & Action Groups (Day 3-4)

**Lambda Tools:**
- [ ] Implement Code Executor Lambda
- [ ] Implement CV Analyzer Lambda
- [ ] Implement Performance Evaluator Lambda
- [ ] Create Action Groups in Bedrock Agent
- [ ] Connect Lambda functions to Agent

**Integration:**
- [ ] Connect FastAPI to Bedrock Agent
- [ ] Implement message flow: User → API → Agent → Response
- [ ] Handle tool invocations

### Phase 4: Real-time Features (Day 4-5)

**WebSocket:**
- [ ] Setup API Gateway WebSocket API
- [ ] Implement WebSocket handler in FastAPI
- [ ] Connect frontend to WebSocket
- [ ] Implement live transcript updates

**Frontend Polish:**
- [ ] Real-time transcript display
- [ ] Message streaming
- [ ] File upload for CV
- [ ] Session persistence

### Phase 5: Testing & Deployment (Day 5-6)

**Testing:**
- [ ] End-to-end interview flow
- [ ] Test all interview types
- [ ] Code execution validation
- [ ] Performance evaluation accuracy

**Deployment:**
- [ ] Deploy FastAPI to Lambda
- [ ] Deploy Next.js (Vercel/AWS Amplify/S3+CloudFront)
- [ ] Configure API Gateway
- [ ] Setup environment variables
- [ ] Domain setup (optional)

### Phase 6: Demo Preparation (Day 6-7)

- [ ] Prepare demo script
- [ ] Create sample interview scenarios
- [ ] Record demo video
- [ ] Prepare presentation slides
- [ ] Document architecture for judges

---

## Meeting Hackathon Requirements

### ✅ Requirement 1: LLM from Bedrock/SageMaker
- **Using:** Amazon Bedrock with Nova Pro/Lite OR Claude 3.5 Sonnet
- **How:** Core LLM powering the interview agent

### ✅ Requirement 2: AWS Services
- **Amazon Bedrock Agent:** Main AI agent with primitives (InvokeAgent, ActionGroups, KnowledgeBase)
- **Amazon Bedrock:** Foundation models
- **AWS Lambda:** FastAPI backend + tool functions
- **Amazon S3:** Storage for CVs, transcripts, knowledge base
- **Amazon API Gateway:** REST + WebSocket APIs

### ✅ Requirement 3: AI Agent Qualification

**a) Reasoning LLMs for decision-making:**
- Agent uses Claude/Nova to analyze candidate responses
- Adapts question difficulty based on performance
- Decides when to provide hints or move to next question

**b) Autonomous capabilities:**
- Conducts full interviews without human intervention
- Automatically evaluates responses
- Generates performance reports
- Can operate with or without human feedback

**c) Integration with external tools:**
- **APIs:** FastAPI backend, external code execution
- **Databases:** S3 for data storage
- **External tools:**
  - Code execution environment (Lambda)
  - Knowledge Base for RAG
  - CV analysis tool
  - Performance evaluator

---

## Code Examples

### 1. Bedrock Agent Integration (FastAPI)

```python
# backend/app/services/bedrock_agent.py

import boto3
import json
from typing import Dict, List, Any

class BedrockAgentService:
    def __init__(self):
        self.client = boto3.client('bedrock-agent-runtime')
        self.agent_id = "YOUR_AGENT_ID"
        self.agent_alias_id = "YOUR_ALIAS_ID"

    async def send_message(
        self,
        session_id: str,
        message: str,
        interview_type: str,
        resume_summary: str = None
    ) -> Dict[str, Any]:
        """Send message to Bedrock Agent and get response"""

        # Prepare session state with context
        session_state = {
            "sessionAttributes": {
                "interview_type": interview_type,
                "resume_summary": resume_summary or "Not provided"
            }
        }

        try:
            response = self.client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=message,
                sessionState=session_state
            )

            # Parse streaming response
            agent_response = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        agent_response += chunk['bytes'].decode('utf-8')

            return {
                "response": agent_response,
                "session_id": session_id
            }

        except Exception as e:
            print(f"Error invoking agent: {e}")
            raise

    async def end_session(self, session_id: str) -> Dict[str, Any]:
        """End interview session and get summary"""

        summary_prompt = "Please provide a summary of the candidate's performance and areas for improvement."

        response = await self.send_message(
            session_id=session_id,
            message=summary_prompt,
            interview_type="summary"
        )

        return response
```

### 2. FastAPI Endpoints

```python
# backend/app/routers/interviews.py

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.services.bedrock_agent import BedrockAgentService
from app.services.s3_service import S3Service
import uuid

router = APIRouter()
bedrock_service = BedrockAgentService()
s3_service = S3Service()

class CreateSessionRequest(BaseModel):
    interview_type: str
    candidate_name: str

class MessageRequest(BaseModel):
    session_id: str
    message: str

@router.post("/sessions")
async def create_session(request: CreateSessionRequest):
    """Create a new interview session"""

    session_id = str(uuid.uuid4())

    # Initialize session in S3 or DynamoDB
    session_data = {
        "session_id": session_id,
        "interview_type": request.interview_type,
        "candidate_name": request.candidate_name,
        "created_at": datetime.utcnow().isoformat(),
        "transcript": []
    }

    await s3_service.save_session(session_id, session_data)

    return {
        "session_id": session_id,
        "message": "Session created successfully"
    }

@router.post("/sessions/{session_id}/upload-cv")
async def upload_cv(session_id: str, file: UploadFile = File(...)):
    """Upload candidate CV"""

    # Save CV to S3
    cv_url = await s3_service.upload_file(
        file=file,
        bucket="prepai-user-data",
        key=f"cvs/{session_id}/{file.filename}"
    )

    # Analyze CV using Lambda tool
    cv_analysis = await analyze_cv(cv_url)

    # Update session with CV summary
    await s3_service.update_session(session_id, {
        "cv_url": cv_url,
        "cv_summary": cv_analysis
    })

    return {
        "message": "CV uploaded successfully",
        "cv_analysis": cv_analysis
    }

@router.post("/interviews/message")
async def send_message(request: MessageRequest):
    """Send message to AI agent"""

    # Get session data
    session = await s3_service.get_session(request.session_id)

    # Send to Bedrock Agent
    response = await bedrock_service.send_message(
        session_id=request.session_id,
        message=request.message,
        interview_type=session['interview_type'],
        resume_summary=session.get('cv_summary')
    )

    # Update transcript
    transcript_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "role": "user",
        "message": request.message
    }
    session['transcript'].append(transcript_entry)

    transcript_entry_agent = {
        "timestamp": datetime.utcnow().isoformat(),
        "role": "agent",
        "message": response['response']
    }
    session['transcript'].append(transcript_entry_agent)

    await s3_service.save_session(request.session_id, session)

    return {
        "response": response['response'],
        "session_id": request.session_id
    }

@router.get("/interviews/{session_id}/transcript")
async def get_transcript(session_id: str):
    """Get full interview transcript"""

    session = await s3_service.get_session(session_id)
    return {
        "transcript": session['transcript']
    }

@router.post("/interviews/{session_id}/end")
async def end_interview(session_id: str):
    """End interview and generate report"""

    # Get performance summary from agent
    summary = await bedrock_service.end_session(session_id)

    # Save final report to S3
    report_url = await s3_service.save_report(session_id, summary)

    return {
        "message": "Interview ended",
        "summary": summary,
        "report_url": report_url
    }
```

### 3. Lambda Function: Code Executor

```python
# lambda_functions/code_executor/handler.py

import json
import subprocess
import sys
import tempfile
import os

def lambda_handler(event, context):
    """
    Executes candidate's code in a secure environment
    """

    code = event.get('code', '')
    language = event.get('language', 'python')
    test_cases = event.get('test_cases', [])

    results = []

    try:
        if language == 'python':
            results = execute_python(code, test_cases)
        elif language == 'javascript':
            results = execute_javascript(code, test_cases)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Unsupported language'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps({
                'results': results,
                'success': all(r['passed'] for r in results)
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def execute_python(code: str, test_cases: list) -> list:
    """Execute Python code with test cases"""

    results = []

    for test_case in test_cases:
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                f.write(f"\n\n# Test case\n")
                f.write(f"print({test_case['function_call']})")
                temp_file = f.name

            # Execute with timeout
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=5
            )

            output = result.stdout.strip()
            expected = str(test_case['expected'])

            results.append({
                'input': test_case['input'],
                'expected': expected,
                'actual': output,
                'passed': output == expected,
                'error': result.stderr if result.stderr else None
            })

            # Clean up
            os.unlink(temp_file)

        except subprocess.TimeoutExpired:
            results.append({
                'input': test_case['input'],
                'expected': test_case['expected'],
                'actual': None,
                'passed': False,
                'error': 'Execution timeout'
            })
        except Exception as e:
            results.append({
                'input': test_case['input'],
                'expected': test_case['expected'],
                'actual': None,
                'passed': False,
                'error': str(e)
            })

    return results
```

### 4. Next.js Interview Page

```typescript
// app/interview/[sessionId]/page.tsx

'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';

interface Message {
  role: 'user' | 'agent';
  message: string;
  timestamp: string;
}

export default function InterviewPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket(`wss://your-api.execute-api.region.amazonaws.com/ws/interview/${sessionId}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages(prev => [...prev, {
        role: 'agent',
        message: data.message,
        timestamp: new Date().toISOString()
      }]);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [sessionId]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      role: 'user',
      message: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Send via REST API (WebSocket will receive response)
      await fetch('/api/interviews/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: input
        })
      });
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen">
      {/* Left Panel: Transcript */}
      <div className="w-1/2 border-r border-gray-300 p-4 overflow-y-auto bg-gray-50">
        <h2 className="text-xl font-bold mb-4">Interview Transcript</h2>
        <div className="space-y-4">
          {messages.map((msg, idx) => (
            <div key={idx} className="p-3 rounded bg-white shadow-sm">
              <div className="flex justify-between text-sm text-gray-500 mb-1">
                <span className="font-semibold">
                  {msg.role === 'user' ? 'You' : 'Interviewer'}
                </span>
                <span>{new Date(msg.timestamp).toLocaleTimeString()}</span>
              </div>
              <p className="text-gray-800">{msg.message}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Right Panel: Chat Interface */}
      <div className="w-1/2 flex flex-col">
        <div className="flex-1 p-4 overflow-y-auto">
          <div className="space-y-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] p-3 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-800'
                  }`}
                >
                  <p>{msg.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-300 p-4">
          <div className="flex space-x-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Type your response..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400"
            >
              {loading ? 'Sending...' : 'Send'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## Deployment Instructions

### 1. Deploy FastAPI to Lambda

```bash
# Install dependencies
pip install -r requirements.txt -t ./package

# Create deployment package
cd package
zip -r ../deployment.zip .
cd ..
zip -g deployment.zip app/**/*.py

# Upload to Lambda
aws lambda create-function \
  --function-name prepai-backend \
  --runtime python3.12 \
  --handler app.main.handler \
  --zip-file fileb://deployment.zip \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role \
  --timeout 30 \
  --memory-size 1024
```

### 2. Deploy Next.js

**Option A: Vercel (Easiest)**
```bash
npm run build
vercel deploy --prod
```

**Option B: AWS Amplify**
```bash
# Connect GitHub repo in AWS Amplify Console
# Amplify will auto-deploy on git push
```

**Option C: S3 + CloudFront**
```bash
npm run build
npm run export
aws s3 sync out/ s3://prepai-frontend/
aws cloudfront create-invalidation --distribution-id ID --paths "/*"
```

### 3. Configure API Gateway

```bash
# Create REST API
aws apigatewayv2 create-api \
  --name prepai-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:region:account-id:function:prepai-backend

# Create WebSocket API
aws apigatewayv2 create-api \
  --name prepai-ws \
  --protocol-type WEBSOCKET \
  --route-selection-expression '$request.body.action'
```

---

## Environment Variables

### Backend (.env)
```bash
AWS_REGION=us-east-1
BEDROCK_AGENT_ID=your-agent-id
BEDROCK_AGENT_ALIAS_ID=your-alias-id
S3_BUCKET_USER_DATA=prepai-user-data
S3_BUCKET_KNOWLEDGE_BASE=prepai-knowledge-base
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=https://your-api.execute-api.region.amazonaws.com
NEXT_PUBLIC_WS_URL=wss://your-ws.execute-api.region.amazonaws.com
```

---

## Cost Estimation (AWS)

**Assuming 100 interview sessions/month:**

- **Bedrock Agent:** ~$50-100 (based on token usage)
- **Lambda:** ~$10 (mostly free tier)
- **S3:** ~$5 (storage + requests)
- **API Gateway:** ~$5
- **Bedrock Knowledge Base:** ~$10

**Total: ~$80-130/month**

---

## Demo Script for Judges

1. **Introduction (30 sec)**
   - "PrepAI: AI-powered interview preparation platform"
   - "Built entirely on AWS with Bedrock Agents"

2. **Show Landing Page (30 sec)**
   - Multiple interview types
   - Select "Google India, SDE Technical Interview"

3. **Upload Resume (30 sec)**
   - Upload sample CV
   - Show AI analyzing resume

4. **Conduct Interview (2-3 min)**
   - Show live chat with AI interviewer
   - Demonstrate transcript updating in real-time
   - Submit a coding problem
   - Show code execution results

5. **End Session (30 sec)**
   - Show performance summary
   - Highlight areas for improvement

6. **Architecture Overview (1 min)**
   - Show diagram
   - Highlight AWS services used
   - Explain Bedrock Agent primitives
   - Demonstrate autonomous decision-making

---

## Key Selling Points for Hackathon

1. **Fully leverages AWS Bedrock Agent primitives** (InvokeAgent, ActionGroups, KnowledgeBase)
2. **Demonstrates true autonomous AI** - adapts questions, evaluates responses, provides feedback without human intervention
3. **Practical real-world application** - solves genuine problem for students and professionals
4. **Modular & scalable architecture** - easy to extend with new interview types
5. **Multiple AWS integrations** - Bedrock, Lambda, S3, API Gateway, Knowledge Base
6. **Real-time capabilities** - WebSocket for live updates
7. **Tool usage** - Code execution, CV analysis, RAG, performance evaluation

---

## Next Steps

1. Clone/create repositories
2. Start with Phase 1 (Foundation)
3. Focus on Bedrock Agent setup (Phase 2) - this is your core value
4. Add tools incrementally (Phase 3)
5. Polish UI and test end-to-end (Phase 4-5)
6. Prepare compelling demo (Phase 6)

Good luck with your hackathon! 🚀
