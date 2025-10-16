import boto3
import time
import json
from typing import Dict, Any, Optional, List, Generator
from botocore.config import Config
from botocore.exceptions import ClientError
from app.config import AWS_REGION, AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, BEDROCK_AGENT_ID, BEDROCK_AGENT_ALIAS_ID

class BedrockService:
    def __init__(self):
        # Configure boto3 with connection reuse and faster settings
        config = Config(
            region_name=AWS_REGION,
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            },
            connect_timeout=5,  # Faster initial connection
            read_timeout=60,
            max_pool_connections=50,  # Connection pooling
            tcp_keepalive=True  # Keep connections alive
        )

        self.bedrock_agent_client = boto3.client(
            'bedrock-agent-runtime',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            config=config
        )
        self.agent_id = BEDROCK_AGENT_ID
        self.agent_alias_id = BEDROCK_AGENT_ALIAS_ID

        # Session state cache (in production, use Redis or DynamoDB)
        self.session_states: Dict[str, Dict[str, Any]] = {}

    def initialize_session(
        self,
        session_id: str,
        interview_type: str,
        candidate_name: str,
        resume_summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initialize session state for a new interview session

        Args:
            session_id: Unique session identifier
            interview_type: Type of interview (e.g., "Google SDE", "AWS SA")
            candidate_name: Name of the candidate
            resume_summary: Optional summary of candidate's resume

        Returns:
            Session state dictionary
        """
        session_state = {
            "sessionId": session_id,
            "interviewType": interview_type,
            "candidateName": candidate_name,
            "resumeSummary": resume_summary or "Not provided",
            "conversationHistory": [],
            "startTime": time.time(),
            "turnCount": 0
        }

        self.session_states[session_id] = session_state
        return session_state

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session state for a given session ID

        Args:
            session_id: Unique session identifier

        Returns:
            Session state dictionary or None if not found
        """
        return self.session_states.get(session_id)

    def update_session_state(
        self,
        session_id: str,
        user_input: str,
        agent_response: str
    ) -> None:
        """
        Update session state with latest conversation turn

        Args:
            session_id: Unique session identifier
            user_input: User's input text
            agent_response: Agent's response text
        """
        if session_id in self.session_states:
            self.session_states[session_id]["conversationHistory"].append({
                "role": "user",
                "content": user_input,
                "timestamp": time.time()
            })
            self.session_states[session_id]["conversationHistory"].append({
                "role": "assistant",
                "content": agent_response,
                "timestamp": time.time()
            })
            self.session_states[session_id]["turnCount"] += 1

    def invoke_agent(
        self,
        session_id: str,
        input_text: str,
        enable_trace: bool = False,
        max_retries: int = 2,
        session_state: Optional[Dict[str, Any]] = None
    ):
        """
        Invoke Bedrock Agent with streaming response and retry logic

        Args:
            session_id: Unique session identifier
            input_text: User input text
            enable_trace: Enable agent trace for debugging
            max_retries: Maximum number of retry attempts
            session_state: Optional session state attributes to pass to agent

        Returns:
            Generator yielding response chunks
        """
        retry_count = 0
        base_delay = 0.5  # Start with 500ms delay

        # Build session state for Bedrock Agent
        session_attributes = {}
        if session_state:
            # Pass interview context to agent
            session_attributes = {
                "interview_type": session_state.get("interviewType", ""),
                "candidate_name": session_state.get("candidateName", ""),
                "resume_summary": session_state.get("resumeSummary", ""),
                "turn_count": str(session_state.get("turnCount", 0))
            }

        while retry_count <= max_retries:
            try:
                # Prepare invocation parameters
                invoke_params = {
                    "agentId": self.agent_id,
                    "agentAliasId": self.agent_alias_id,
                    "sessionId": session_id,
                    "inputText": input_text,
                    "enableTrace": enable_trace
                }

                # Add session state if provided
                if session_attributes:
                    invoke_params["sessionState"] = {
                        "sessionAttributes": session_attributes
                    }

                response = self.bedrock_agent_client.invoke_agent(**invoke_params)

                # Return the streaming event stream
                event_stream = response.get('completion', [])
                return event_stream

            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')

                if error_code == 'ThrottlingException' and retry_count < max_retries:
                    # Exponential backoff
                    delay = base_delay * (2 ** retry_count)
                    print(f"Throttling detected. Retrying in {delay}s... (attempt {retry_count + 1}/{max_retries})")
                    time.sleep(delay)
                    retry_count += 1
                else:
                    print(f"Error invoking Bedrock Agent: {e}")
                    raise

            except Exception as e:
                print(f"Error invoking Bedrock Agent: {e}")
                raise

        # If all retries exhausted
        raise Exception("Max retries exceeded for Bedrock Agent invocation")

    def extract_text_from_stream(self, event_stream):
        """
        Extract text chunks from Bedrock Agent event stream

        Yields:
            Text chunks from the agent response
        """
        for event in event_stream:
            if 'chunk' in event:
                chunk_data = event['chunk']
                if 'bytes' in chunk_data:
                    text_chunk = chunk_data['bytes'].decode('utf-8')
                    yield text_chunk
