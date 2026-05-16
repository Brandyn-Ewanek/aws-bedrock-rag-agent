import json
import time
import uuid
import boto3
import csv

# Initialize Bedrock clients
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='ca-central-1')
bedrock_agent_client = boto3.client('bedrock-agent', region_name='ca-central-1') # Added to fetch model info
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

# The highly cost-effective Amazon Nova Pro Judge
JUDGE_MODEL_ID = 'us.amazon.nova-pro-v1:0'

# Configuration for multiple agents
AGENTS_CONFIG = [
    {
        "agent_name": "Test Agent",
        "file_name": "test_batch_test.json",
        "agent_id": "FGA2DS16VI",           # Your Test Agent ID
        "agent_alias_id": "Q7YK1FFTL9"      # Your Test Agent Alias ID
    },
    {
        "agent_name": "Learn Agent",
        "file_name": "test_batch_learn.json",
        "agent_id": "QAR0IDUDSX",           # Learn agent ID
        "agent_alias_id": "O4UMR0JC5L"      # Learn Alias ID
    }
]

def get_agent_model_id(agent_id, alias_id):
    """Fetches the underlying foundation model ID currently active on the Alias."""
    try:
        # 1. Look up the specific Version the Alias is currently routing to
        alias_resp = bedrock_agent_client.get_agent_alias(agentId=agent_id, agentAliasId=alias_id)
        version = alias_resp['agentAlias']['routingConfiguration'][0]['agentVersion']
        
        # 2. Look up the Foundation Model configured for that specific Version
        version_resp = bedrock_agent_client.get_agent_version(agentId=agent_id, agentVersion=version)
        return version_resp['agentVersion']['foundationModel']
    except Exception as e:
        print(f"⚠️ Warning: Could not fetch model ID for agent {agent_id}. Error: {e}")
        return "Unknown Model"

def extract_tokens_from_trace(trace_data):
    """Recursively searches the hidden Bedrock trace logs for true token usage."""
    input_tok = 0
    output_tok = 0
    
    if isinstance(trace_data, dict):
        if 'usage' in trace_data and 'inputTokens' in trace_data['usage']:
            input_tok += trace_data['usage'].get('inputTokens', 0)
            output_tok += trace_data['usage'].get('outputTokens', 0)
        else:
            for key, value in trace_data.items():
                i, o = extract_tokens_from_trace(value)
                input_tok += i
                output_tok += o
    elif isinstance(trace_data, list):
        for item in trace_data:
            i, o = extract_tokens_from_trace(item)
            input_tok += i
            output_tok += o
            
    return input_tok, output_tok

def calculate_cost(model_id, in_tokens, out_tokens):
    """Calculates cost dynamically based on the active model."""
    model_id = model_id.lower()
    
    # Pricing per 1 Million Tokens (Approximate AWS standard rates)
    if 'haiku' in model_id:
        in_rate, out_rate = 0.25, 1.25
    elif 'sonnet' in model_id:
        in_rate, out_rate = 3.00, 15.00
    elif 'nova-lite' in model_id:
        in_rate, out_rate = 0.06, 0.24
    elif 'nova-micro' in model_id:
        in_rate, out_rate = 0.035, 0.14
    else:
        # Fallback if model is unknown
        return 0.0

    return (in_tokens / 1_000_000 * in_rate) + (out_tokens / 1_000_000 * out_rate)

def run_test_scenario(scenario_data, agent_id, agent_alias_id, agent_name, active_model_id):
    session_id = str(uuid.uuid4())
    transcript = []
    total_scenario_latency = 0
    total_input_tokens = 0
    total_output_tokens = 0
    
    print(f"\n--- Running: [{agent_name} | {active_model_id}] {scenario_data['scenario']} ---")
    
    # Loop through the user's inputs to build the conversation
    for user_input in scenario_data['user_messages']:
        transcript.append(f"User: {user_input}")
        
        start_time = time.time()
        
        # NOTE: enableTrace=True is required to get token counts from Agents
        response = bedrock_agent_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=user_input,
            enableTrace=True
        )
        
        agent_reply = ""
        for event in response.get('completion'):
            if 'chunk' in event:
                agent_reply += event['chunk']['bytes'].decode('utf-8')
            if 'trace' in event:
                i_tok, o_tok = extract_tokens_from_trace(event['trace'])
                total_input_tokens += i_tok
                total_output_tokens += o_tok
        
        turn_latency = time.time() - start_time
        total_scenario_latency += turn_latency
        
        transcript.append(f"Agent: {agent_reply}")
        # Add a slight delay to simulate human typing and allow cache to settle
        time.sleep(1) 

    # Compile the full transcript
    full_transcript = "\n".join(transcript)
    
    # Send transcript and criteria to the Judge LLM
    judge_prompt = f"""You are an Evaluation Judge for DataSimple.education.
    Read the following conversation transcript between a User and the {agent_name}.
    
    TRANSCRIPT:
    {full_transcript}
    
    EVALUATION CRITERIA:
    {scenario_data['evaluation_criteria']}
    
    Grade the agent on a scale of 1 to 5 for Accuracy, Persona, and Faithfulness to the criteria.
    Output your response STRICTLY as valid JSON with no markdown formatting.
    Format: {{"accuracy": 5, "persona": 5, "faithfulness": 5, "reasoning": "..."}}
    """
    
    # Amazon Nova Pro API Call Format
    judge_response = bedrock_runtime.invoke_model(
        modelId=JUDGE_MODEL_ID,
        body=json.dumps({
            "inferenceConfig": {
                "max_new_tokens": 500,
                "temperature": 0.1
            },
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": judge_prompt}]
                }
            ]
        }),
        contentType="application/json",
        accept="application/json"
    )
    
    # Parse Amazon Nova Pro output
    response_body = json.loads(judge_response['body'].read())
    judge_result = response_body['output']['message']['content'][0]['text']
    
    # Clean up markdown block if Nova accidentally adds it
    judge_result = judge_result.strip()
    if judge_result.startswith("```json"):
        judge_result = judge_result[7:]
    if judge_result.endswith("```"):
        judge_result = judge_result[:-3]
    judge_result = judge_result.strip()
    
    # Calculate costs dynamically
    scenario_cost = calculate_cost(active_model_id, total_input_tokens, total_output_tokens)
    
    print(f"Total Latency: {total_scenario_latency:.2f} seconds")
    print(f"Tokens Used: {total_input_tokens} In | {total_output_tokens} Out")
    print(f"Estimated Cost: ${scenario_cost:.6f}")
    print("Judge Evaluation:")
    print(judge_result)

    # Return the structured data to the main loop
    return {
        "Agent Name": agent_name,
        "Model Used": active_model_id,
        "Scenario": scenario_data['scenario'],
        "Latency": total_scenario_latency,
        "Input Tokens": total_input_tokens,
        "Output Tokens": total_output_tokens,
        "Cost": scenario_cost,
        "Judge": json.loads(judge_result)
    }

if __name__ == "__main__":
    all_results = []
    
    # Loop through each agent in the config
    for agent in AGENTS_CONFIG:
        print(f"\n=============================================")
        print(f"STARTING EVALUATIONS FOR: {agent['agent_name']}")
        print(f"=============================================")
        
        # 1. Fetch the exact model running on this agent's alias right now
        active_model = get_agent_model_id(agent['agent_id'], agent['agent_alias_id'])
        print(f"Detected Foundation Model: {active_model}")
        
        try:
            with open(agent['file_name'], 'r') as file:
                test_cases = json.load(file)
        except FileNotFoundError:
            print(f"⚠️ Could not find {agent['file_name']}. Skipping {agent['agent_name']}.")
            continue
            
        for test in test_cases:
            try:
                # Pass the specific agent IDs and the active model into the function
                result_data = run_test_scenario(
                    test, 
                    agent['agent_id'], 
                    agent['agent_alias_id'], 
                    agent['agent_name'],
                    active_model
                )
                
                # Flatten the data for the CSV
                flat_result = {
                    "Agent": result_data["Agent Name"],
                    "Model": result_data["Model Used"],
                    "Scenario": result_data["Scenario"],
                    "Total Latency (s)": round(result_data["Latency"], 2),
                    "Input Tokens": result_data["Input Tokens"],
                    "Output Tokens": result_data["Output Tokens"],
                    "Est. Cost ($)": f"{result_data['Cost']:.6f}",
                    "Accuracy": result_data["Judge"].get("accuracy", ""),
                    "Persona": result_data["Judge"].get("persona", ""),
                    "Faithfulness": result_data["Judge"].get("faithfulness", ""),
                    "Reasoning": result_data["Judge"].get("reasoning", "")
                }
                all_results.append(flat_result)
            except Exception as e:
                print(f"❌ Error processing scenario '{test['scenario']}': {str(e)}")
            
    # Export to CSV
    csv_filename = "multi_agent_evaluation_report.csv"
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["Agent", "Model", "Scenario", "Total Latency (s)", "Input Tokens", "Output Tokens", "Est. Cost ($)", "Accuracy", "Persona", "Faithfulness", "Reasoning"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(all_results)
        
    print(f"\n✅ All evaluations complete! Results saved to {csv_filename}")