# DataSimple.education Serverless GenAI Agent & Data Pipeline
This repository contains the architecture, data preparation, and metadata strategy for the DataSimple.education RAG (Retrieval-Augmented Generation) Chatbot. Built on AWS, this system integrates a static educational knowledge base with a dynamic web-search agent and a persistent user feedback loop.

## Architecture Overview

![DataSimple AI Architecture Diagram](Phase%202/docs/Architecture-DataSimple-Chatbot.jpg)

**[Click here to read the full Architecture Report of Phase 2 (PDF)](https://shr.pn/SaIv)**

**[Click here to read Testing and Optimization of Phase 2 (PDF)](https://shr.pn/PpvB)**

![Phase 2 Experiments](Phase%202/docs/Phase-2-Experiments.png)

This project utilizes a decoupled, serverless AWS architecture to manage cost, latency, and data freshness. 

* **The RAG Pipeline (Persistent Knowledge):** Scrubbed curriculum files (`.md`) and their corresponding metadata sidecars are stored in **Amazon S3**. **AWS Bedrock Knowledge Base** chunks and embeds these documents using **Amazon Titan Text Embeddings v2**, storing the resulting vectors in a Serverless **Pinecone Vector Database** for semantic retrieval.
* **The Agentic Web Search (Ephemeral Context):** When user queries fall outside the static curriculum, **Bedrock AgentCore** dynamically routes requests to Live Web Search APIs (Serper/Tavily via MCP). This data is injected into the LLM's working memory to synthesize a real-time answer and is instantly discarded to optimize costs and reduce data staleness.
* **The Feedback Loop (Persistent Storage):** User ratings and interactions are routed through a dedicated **AWS Lambda (Feedback processing)** function, which cleans and writes the payload to an **Amazon DynamoDB** (`feedbacks` table) for continuous model evaluation and curriculum improvement.


## Key Learnings & Insights from Phase 2: Multi-Agent LLMOps
Phase 2 focused on optimizing the underlying LLM architecture to build a sustainable, high-velocity ecosystem capable of delivering real-time tutoring at scale. Over the course of nine rigorous experiments, the engineering team benchmarked proprietary and open-source models across strict grading and RAG workflows.

### The Final Architecture: A Hybrid-Model Ecosystem
The evaluation proved that a "one-size-fits-all" model approach is highly inefficient. The finalized architecture implements a decoupled, specialized hybrid stack:
* **Routing Agent (Amazon Nova Lite):** Deployed for ultra-low-latency intent classification and raw pass-through routing, eliminating API gateway bottlenecks.
* **Learn Agent / RAG Tutor (Claude 3 Haiku):** Replaces Claude 3.5 Sonnet for database retrieval. It natively supports AWS Bedrock Tool Use and maintains high conversational fluency while dropping costs to just $0.0026 per query.
* **Test Agent / Grader (Meta Llama 3 8B):** Deployed as a high-context, open-source grader. It securely tracks test state and calculates scores while driving grading inference costs to near zero ($0.0000 API cost; ~$0.0042 on-demand compute).

### Business Impact & ROI
By strategically assigning models based on workflow complexity, the new architecture delivers phenomenal operational improvements:
* **60% Latency Reduction:** Average system response times have been slashed from 15–19 seconds down to 6–7 seconds, ensuring a fluid, frictionless user experience.
* **90%+ Cost Reduction:** Operational costs have been driven down from pennies-per-query ($0.05 - $0.11) to fractions of a penny.
* **Strategic Trade-off:** The system absorbs a fractional penalty (~0.10 to 0.40 out of 5.00) in strict formatting adherence. The agents now act as fast, supportive tutors rather than draconian examiners—an overwhelmingly positive trade-off for a free, self-paced learning environment.


## The Content Catalog
This repository manages the metadata for nearly 100 Guided Projects and Data Tips from the DataSimple curriculum, ensuring the AI can precisely filter and recommend content across:

* **Data Analysis & Visualization:** Pandas, Seaborn, Plotly, Sweetviz.
* **Machine Learning:** Sklearn (Regression, Classification, Clustering), Ensemble Methods (XGBoost, LightGBM), and Explainability (SHAP, Yellowbrick).
* **Deep Learning:** TensorFlow (Sequential & Functional APIs), Recurrent Neural Networks (RNN/LSTM), and Computer Vision (CNNs).
* **Natural Language Processing (NLP):** TensorFlow Text Generation, Hugging Face Transformers, and NLP Pipelines.

**[Try the Live Chatbot Here: DataSimple.education](https://shr.pn/fFpw)**

## User Interface

![DataSimple Chatbot Interface](Phase%201/docs/Ai-Teacher-Brandyn.jpg)


## How to Use This Repository (Metadata Pipeline)
AWS Bedrock Knowledge Bases require a "sidecar" `.metadata.json` file for every single document to allow Pinecone to perform metadata filtering (e.g., filtering out Level 6 projects when a beginner asks a question). Instead of managing hundreds of individual JSON files manually, this pipeline manages a single `master_metadata.json` file and automates the extraction.

### Step 1: Update the Master JSON
When a new guided project or data tip is published, add a new block to `master_metadata.json` using the standardized tagging system:

* `contentType:` "guided_project" or "data_tip"
* `difficultyLevel:` 1 through 10
* `topic:` "Data Analysis", "Data Visualization", "Machine Learning", "Deep Learning", or "Deep Learning NLP"
* `libraries:` e.g., ["Pandas", "Seaborn"], ["TensorFlow", "Hugging Face"]
* `hasCode:` "true" or "false"
* `hasVideo:` "true" or "false" (Allows the LLM to know if a video exists)
* `videoUrl:` "https://youtube.com/..." (Allows the LLM to provide the student with a direct link)

### Step 2: Generate the Sidecar Files
Run the Python automation script to unpack the master JSON into the individual files Bedrock expects.

```bash
python generate_bedrock_sidecars.py