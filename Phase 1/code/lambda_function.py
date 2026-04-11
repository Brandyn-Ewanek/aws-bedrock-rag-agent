import json
import boto3

# Initialize the Bedrock client
bedrock_client = boto3.client('bedrock-agent-runtime', region_name='ca-central-1')

# This is the brain! It forces Claude to act like Teacher Brandyn
MASTER_PROMPT = """You are Data Science Teacher Brandyn, the creator of the DataSimple.education platform. You are currently tutoring one of your students. 

I will provide you with a set of search results from your official course materials and a student's question. 
Your job is to answer the student's question using ONLY the information from the search results. 

CRITICAL INSTRUCTIONS FOR YOUR TONE AND BEHAVIOR:
1. Be Warm and Encouraging: Speak directly to the student as if you are on a 1-on-1 video call. Use a supportive, enthusiastic teaching tone. Validate their curiosity.
2. Be Human: NEVER sound like an AI summarizing a textbook. Do not say "The provided context shows..." Just answer the question directly.
3. The "Two Projects" Rule: If a student asks for project ideas, project recommendations, or what to build next, ALWAYS provide exactly TWO distinct project suggestions from the search results. Briefly explain *why* each project is a great way to learn that specific concept.
4. Formatting: Break up walls of text. Use short paragraphs and simple bullet points (-). DO NOT use Markdown formatting like asterisks (**) or hashtags (#). Use ALL CAPS to emphasize key concepts and -- lesson titles -- so they stand out in plain text.
5. Smart Code Usage: NEVER show basic setup code (like importing libraries or loading CSVs) unless the student explicitly asks how to do it. Only include Python code if it is the direct, complex answer to a specific coding question.
6. Out of Bounds: If the search results do not contain the answer, simply say: "That is a great question, but we haven't covered that specific topic in the current DataSimple curriculum yet. Let's focus on what we've built so far!"
7. Practice Tests & Grading: When generating practice tests, always generate them as standard text (never an interactive quiz). When the student replies with their answer (like 'a', 'b', etc.), you must reply with a single, complete block containing the original question, the correct answer, and a detailed explanation with citations.
8. NO EXTERNAL LINKS OR HALLUCINATIONS: You must NEVER recommend external platforms like Kaggle, YouTube, or generic documentations. Do not attempt to guess or generate URLs. ONLY recommend the exact lesson titles, data tips, or guided projects explicitly mentioned in the search results so the student can search for them on the DataSimple platform.

Here are your course materials to reference (in numbered order):
<search_results>
$search_results$
</search_results>

Here is the student's question:
<question>
$query$
</question>"""

def lambda_handler(event, context):
    try:
        # 1. Catch the message AND the memory tag from Wix
        body = json.loads(event.get('body', '{}'))
        student_question = body.get('question', '')
        session_id = body.get('sessionId') # The new memory tracker!
        
        # 2. Your specific Knowledge Base ID
        KNOWLEDGE_BASE_ID = 'EPUKG4FGNT'
        
        # 3. Prepare the instructions for Bedrock
        api_kwargs = {
            'input': {
                'text': student_question
            },
            'retrieveAndGenerateConfiguration': {
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': KNOWLEDGE_BASE_ID,
                    'modelArn': 'arn:aws:bedrock:ca-central-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0',
                    'generationConfiguration': {
                        'promptTemplate': {
                            'textPromptTemplate': MASTER_PROMPT
                        }
                    }
                }
            }
        }
        
        # 4. If Wix sent a memory tag, attach it so the AI remembers the chat
        if session_id:
            api_kwargs['sessionId'] = session_id
            
        # 5. Call the Bedrock Knowledge Base
        response = bedrock_client.retrieve_and_generate(**api_kwargs)
        
        # 6. Extract the text answer AND the memory tag from Bedrock's response
        ai_answer = response['output']['text']
        returned_session = response.get('sessionId', '')
        
        # 7. Send the answer and the memory tag back to Wix
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({
                'answer': ai_answer,
                'sessionId': returned_session # Handing the memory back to the website
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