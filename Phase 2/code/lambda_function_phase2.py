import json
import boto3
import uuid

# Initialize the Bedrock client
bedrock_client = boto3.client('bedrock-agent-runtime', region_name='ca-central-1')

# --- CONFIGURATION ---
AGENT_ID = 'OFK8VD1LYC'
AGENT_ALIAS_ID = 'XIG87UXLM3' 

def lambda_handler(event, context):
    try:
        # Catch the message and the memory tag from Wix
        body = json.loads(event.get('body', '{}'))
        student_question = body.get('question', '')
        session_id = body.get('sessionId') 
        
        # Agents REQUIRE a sessionId. If it's a new chat, generate a secure random ID.
        if not session_id:
            session_id = str(uuid.uuid4())

        # Call the Supervisor Agent
        response = bedrock_client.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=student_question
        )

        # Bedrock Agents return a streaming response. We must stitch the byte chunks together.
        ai_answer = ""
        for stream_event in response.get('completion'):
            if 'chunk' in stream_event:
                chunk = stream_event['chunk']
                ai_answer += chunk['bytes'].decode('utf-8')

        # Send the compiled answer and the memory tag back to Wix
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({
                'answer': ai_answer,
                'sessionId': session_id 
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }