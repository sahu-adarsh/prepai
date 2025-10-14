import boto3
import time
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

    def invoke_agent(self, session_id: str, input_text: str, enable_trace: bool = False, max_retries: int = 2):
        """
        Invoke Bedrock Agent with streaming response and retry logic

        Args:
            session_id: Unique session identifier
            input_text: User input text
            enable_trace: Enable agent trace for debugging
            max_retries: Maximum number of retry attempts

        Returns:
            Generator yielding response chunks
        """
        retry_count = 0
        base_delay = 0.5  # Start with 500ms delay

        while retry_count <= max_retries:
            try:
                response = self.bedrock_agent_client.invoke_agent(
                    agentId=self.agent_id,
                    agentAliasId=self.agent_alias_id,
                    sessionId=session_id,
                    inputText=input_text,
                    enableTrace=enable_trace
                )

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
