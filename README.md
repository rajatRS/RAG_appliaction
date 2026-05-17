# 🚀 AI Hackathon RAG Boilerplate

A hackathon-ready boilerplate for building an enterprise-grade Retrieval-Augmented Generation (RAG) system. This project features a clean separation of concerns with a **Python/FastAPI Backend** and a lightning-fast **React/Vite Frontend**. 

It is designed to give you a massive structural and aesthetic advantage in any AI hackathon.

## 🌟 Key Features

### Premium UI & Frontend (React + Vite)
- **Glassmorphism Dark Mode:** A stunning, custom-built UI using vanilla CSS that looks incredibly premium right out of the box.
- **Dynamic Search Controls:** A sleek animated toggle switch allowing you to switch Vector Stores dynamically, configure `top_k` results (0-20), and choose between Dense, Sparse, or Hybrid search.
- **Progress Tracking:** Live step-by-step loaders with elapsed second counters built directly into the UI.
- **Dynamic Model Selection:** Dropdown to switch seamlessly between `gpt-3.5-turbo`, `gpt-4o`, `gpt-4-turbo`, and `gpt-4o-mini`.

### Advanced RAG Backend (FastAPI + Raw Pinecone SDK)
- **Multi-Query Expansion:** When a user asks a question, the backend uses an LLM to rewrite the query into 3 variations. It runs 3 parallel vector searches and unions the results to drastically improve recall.
- **LLM-as-a-Judge Reranking:** All retrieved chunks are passed through a `gpt-4o-mini` evaluation prompt. Each chunk is scored from 0-10 on relevance, and only the highest-scoring chunks are sent for final generation.
- **Multithreaded Ingestion:** Bulk parsing and chunking of massive local folders is accelerated using Python's `ThreadPoolExecutor`.
- **The "Responses API":** The entire generation and reranking pipeline has been decoupled from LangChain's bloated wrappers and uses a pure Python `openai` SDK client implementation for maximum control.
- **True Pinecone Hybrid Search:** We utilize the raw `pinecone` Python SDK to generate and bulk-upsert Dense and Sparse vectors natively, bypassing LangChain entirely for extreme speed and efficiency.
- **RAG Evaluator Dashboard:** A powerful new tab that runs automated evaluations (MRR, nDCG, LLM-as-a-judge accuracy) against a Ground Truth dataset (`tests.jsonl`). It features beautiful, responsive Recharts bar charts showing performance statistics by category.

## ⚙️ Setup Instructions

### 1. Configure the Environment
Copy the example environment file and add your OpenAI API Key.
```bash
cp .env.example .env
```

### 2. Install Dependencies (Backend & Frontend)
This command will use `uv` to install Python dependencies, and it will automatically use our isolated local Node.js binary to install your React dependencies.
```bash
make install
```

## 🚀 Running the Application

Because this is a modern, separated stack, you must run the backend and the frontend concurrently in two different terminal tabs.

### Terminal 1: Start the Backend
```bash
make dev-backend
```
- **FastAPI Server:** Runs on `http://localhost:8000`
- **Swagger API Docs:** Available at [http://localhost:8000/docs](http://localhost:8000/docs)

### Terminal 2: Start the Frontend
```bash
make dev-frontend
```
- **React UI:** Available at [http://localhost:5173](http://localhost:5173)

## 🌲 Migrating from ChromaDB to Pinecone

By default, the application runs fully locally using ChromaDB. This is perfect for offline development or standard dense retrieval. 

If you want to unlock **True Hybrid Search (Dense + Sparse)** and serverless scale, you can seamlessly migrate to Pinecone.

### Migration Steps:
1. **Create an Index:** Log in to your Pinecone dashboard and create an index.
2. **Critical Metric Setting:** You **MUST** select the **`dotproduct`** metric. If you select Cosine or Euclidean, Pinecone will reject the sparse vectors, and the hybrid bulk upsert will crash!
3. **Update `.env`:** Add your `PINECONE_API_KEY`, your `PINECONE_INDEX_NAME`, and set `VECTOR_STORE_TYPE=pinecone`.
4. **Restart Backend:** Stop your backend server (Ctrl+C) and run `make dev-backend` to ensure the environment variables are loaded.
5. **Toggle in UI:** In the React interface, flip the "Pinecone Vector Store" toggle to ON. You will immediately see the "Dense Only", "Sparse Only", and "Hybrid" buttons appear, giving you full control over the Pinecone SDK querying logic!

## 📁 Architecture Overview
- `src/api/`: FastAPI routes and core business logic.
- `src/rag/`: Advanced orchestration (Raw Pinecone Integrations, LLM Reranking, Multi-Query Expansion, ThreadPool chunking, Evaluation engine).
- `frontend/`: The React + Vite application.
- `Makefile`: One-click commands for local development.

---

## 📊 Automated RAG Evaluation

The boilerplate features a highly optimized, multithreaded evaluation pipeline to empirically grade your system.

### How it works:
1. **Tests Upload:** Switch to the **RAG Evaluator** tab in the sidebar and upload a `tests.jsonl` file.
2. **Ground Truth Structure:** Your JSONL file should contain one test case per line in this format:
   ```json
   {"question": "Who is the HR Business Partner at Insurellm?", "keywords": ["Amanda Foster", "HR Business Partner"], "reference_answer": "Amanda Foster is the HR Business Partner.", "category": "HR"}
   ```
3. **Retrieval Grading (MRR & nDCG):** The backend executes your advanced Multi-Query retrieval pipeline. It calculates the **Mean Reciprocal Rank (MRR)** and **Normalized Discounted Cumulative Gain (nDCG)** based on whether the expected keywords are present in the retrieved chunks.
4. **Answer Grading (LLM-as-a-judge):** The backend generates the final answer and spins up a separate parallel LLM execution environment using the Responses API (`gpt-4o-mini`) to grade the generated answer against the `reference_answer` across three dimensions: **Accuracy**, **Completeness**, and **Relevance** (scaled 1-5).
5. **Interactive Dashboard:** All results are instantly visualized using interactive `recharts` Bar Charts, separating performance by Category.

### High Concurrency:
The evaluation pipeline runs inside a high-speed `ThreadPoolExecutor` (configured in `src/rag/evaluation.py`). Instead of grading questions one-by-one, it fires parallel vector queries and LLM requests, completing massive test suites in seconds. You can tune the concurrency by updating `max_workers` inside the `run_full_evaluation` function!

