import boto3
from app.config import AWS_REGION, AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, BEDROCK_AGENT_ID, BEDROCK_AGENT_ALIAS_ID

class BedrockService:
    def __init__(self):
        self.bedrock_agent_client = boto3.client(
            'bedrock-agent-runtime',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        self.agent_id = BEDROCK_AGENT_ID
        self.agent_alias_id = BEDROCK_AGENT_ALIAS_ID

    def invoke_agent(self, session_id: str, input_text: str, enable_trace: bool = False):
        """
        Invoke Bedrock Agent with streaming response

        Returns:
            Generator yielding response chunks
        """
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

        except Exception as e:
            print(f"Error invoking Bedrock Agent: {e}")
            raise

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
