import math
import json
from typing import List, Dict, Tuple
from pydantic import BaseModel, Field
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.rag.retrieval import retrieve_documents
from src.rag.generation import generate_answer
from src.rag.llm_client import call_responses_api
from src.config import settings

class TestQuestion(BaseModel):
    question: str
    keywords: List[str]
    reference_answer: str
    category: str = "General"

class RetrievalEval(BaseModel):
    """Evaluation metrics for retrieval performance."""
    mrr: float
    ndcg: float
    keywords_found: int
    total_keywords: int
    keyword_coverage: float

class AnswerEval(BaseModel):
    """LLM-as-a-judge evaluation of answer quality."""
    feedback: str = Field(description="Concise feedback on the answer quality")
    accuracy: float = Field(description="1 to 5 scale")
    completeness: float = Field(description="1 to 5 scale")
    relevance: float = Field(description="1 to 5 scale")

class EvaluationResult(BaseModel):
    test_number: int
    category: str
    question: str
    retrieval: RetrievalEval
    answer_eval: AnswerEval

def calculate_mrr(keyword: str, retrieved_docs: list) -> float:
    keyword_lower = keyword.lower()
    for rank, doc in enumerate(retrieved_docs, start=1):
        if keyword_lower in doc.page_content.lower():
            return 1.0 / rank
    return 0.0

def calculate_dcg(relevances: list[int], k: int) -> float:
    dcg = 0.0
    for i in range(min(k, len(relevances))):
        dcg += relevances[i] / math.log2(i + 2)
    return dcg

def calculate_ndcg(keyword: str, retrieved_docs: list, k: int) -> float:
    keyword_lower = keyword.lower()
    relevances = [1 if keyword_lower in doc.page_content.lower() else 0 for doc in retrieved_docs[:k]]
    dcg = calculate_dcg(relevances, k)
    ideal_relevances = sorted(relevances, reverse=True)
    idcg = calculate_dcg(ideal_relevances, k)
    return dcg / idcg if idcg > 0 else 0.0

def evaluate_retrieval(test: TestQuestion, retrieved_docs: list, k: int) -> RetrievalEval:
    mrr_scores = [calculate_mrr(keyword, retrieved_docs) for keyword in test.keywords]
    avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0

    ndcg_scores = [calculate_ndcg(keyword, retrieved_docs, k) for keyword in test.keywords]
    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0

    keywords_found = sum(1 for score in mrr_scores if score > 0)
    total_keywords = len(test.keywords)
    keyword_coverage = (keywords_found / total_keywords * 100) if total_keywords > 0 else 0.0

    return RetrievalEval(
        mrr=avg_mrr,
        ndcg=avg_ndcg,
        keywords_found=keywords_found,
        total_keywords=total_keywords,
        keyword_coverage=keyword_coverage,
    )

def evaluate_answer(test: TestQuestion, generated_answer: str, model_name: str) -> AnswerEval:
    prompt = f"""You are an expert evaluator assessing the quality of answers. Evaluate the generated answer by comparing it to the reference answer. Only give 5/5 scores for perfect answers.

Question:
{test.question}

Generated Answer:
{generated_answer}

Reference Answer:
{test.reference_answer}

Please evaluate the generated answer on three dimensions:
1. Accuracy: How factually correct is it compared to the reference answer? Only give 5/5 scores for perfect answers.
2. Completeness: How thoroughly does it address all aspects of the question, covering all the information from the reference answer?
3. Relevance: How well does it directly answer the specific question asked, giving no additional information?

Provide your evaluation EXACTLY in the following JSON format:
{{
    "feedback": "your detailed feedback",
    "accuracy": <float 1-5>,
    "completeness": <float 1-5>,
    "relevance": <float 1-5>
}}
"""
    # Use the fastest cheap model for evaluation by default, or the passed model
    raw_response = call_responses_api(prompt, model_name="gpt-4o-mini")
    
    # Simple JSON extraction in case it's wrapped in markdown blocks
    try:
        import re
        match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if match:
            json_str = match.group()
            data = json.loads(json_str)
            return AnswerEval(
                feedback=data.get("feedback", ""),
                accuracy=float(data.get("accuracy", 1.0)),
                completeness=float(data.get("completeness", 1.0)),
                relevance=float(data.get("relevance", 1.0))
            )
        else:
            raise ValueError("No JSON found")
    except Exception as e:
        return AnswerEval(feedback=f"Failed to parse evaluation: {e}", accuracy=1.0, completeness=1.0, relevance=1.0)

def evaluate_single_test(test: TestQuestion, index: int, k: int, vector_store: str, model_name: str) -> EvaluationResult:
    print(f"\n[Test {index+1}] Starting evaluation for question: '{test.question[:60]}...'")
    
    # 1. Retrieve
    print(f"  [Test {index+1}] Step 1/4: Retrieving top {k} documents from {vector_store}...")
    search_type = "hybrid" if vector_store == "pinecone" else "dense"
    retrieved_docs = retrieve_documents(test.question, k=k, search_type=search_type, vector_store_type=vector_store)
    
    # 2. Evaluate Retrieval
    print(f"  [Test {index+1}] Step 2/4: Calculating MRR & nDCG retrieval metrics...")
    retrieval_result = evaluate_retrieval(test, retrieved_docs, k)
    
    # 3. Generate Answer
    print(f"  [Test {index+1}] Step 3/4: Generating answer using {model_name}...")
    generated_answer = generate_answer(test.question, retrieved_docs, model_name=model_name)
    
    # 4. Evaluate Answer
    print(f"  [Test {index+1}] Step 4/4: Evaluating answer quality (LLM-as-a-judge)...")
    answer_result = evaluate_answer(test, generated_answer, model_name=model_name)
    
    print(f"[Test {index+1}] ✓ Evaluation Complete!")
    
    return EvaluationResult(
        test_number=index,
        category=test.category,
        question=test.question,
        retrieval=retrieval_result,
        answer_eval=answer_result
    )

def run_full_evaluation(tests: List[TestQuestion], k: int = 5, vector_store: str = "chroma", model_name: str = "gpt-3.5-turbo") -> List[EvaluationResult]:
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(evaluate_single_test, test, i, k, vector_store, model_name): i 
            for i, test in enumerate(tests)
        }
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                print(f"Error evaluating test: {e}")
                
    # Sort results back to original order
    results.sort(key=lambda x: x.test_number)
    return results
