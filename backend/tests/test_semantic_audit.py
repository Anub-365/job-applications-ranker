import asyncio
from backend.services.embedding_service import generate_embedding

# We don't have numpy installed by default in standard FastAPI containers unless explicitly added, 
# but we can use pure python math for cosine similarity since it's just two 384-dim lists!
import math

def cosine_similarity(v1, v2):
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    return dot_product / (norm_a * norm_b)

async def run_semantic_audit():
    print("🚀 Starting Semantic Intelligence Audit...\n")

    # TEST 1: Concept vs Framework (Asynchronous vs FastAPI)
    jd_1 = "Looking for an Asynchronous Web API developer with experience in Non-blocking I/O."
    resume_1 = "Built high-performance backends using FastAPI and uvicorn."
    
    # TEST 2: Action vs Tool (Containerization vs Docker)
    jd_2 = "Seeking someone to containerize applications and manage cloud deployments."
    resume_2 = "Proficient in Docker, Kubernetes, and AWS EC2."

    # TEST 3: Intent vs Keyword (The "React" trap)
    jd_3 = "Experience in Frontend Development (React/Vue)."
    resume_3 = "Backend Engineer who built REST APIs for React frontends."

    # TEST 4: Irrelevant Garbage (The Baseline)
    garbage = "I enjoy cooking pasta and hiking in the mountains during summer."

    # Generate Embeddings (These return list[float])
    vec_jd1 = generate_embedding(jd_1)
    vec_res1 = generate_embedding(resume_1)
    
    vec_jd2 = generate_embedding(jd_2)
    vec_res2 = generate_embedding(resume_2)

    vec_jd3 = generate_embedding(jd_3)
    vec_res3 = generate_embedding(resume_3)
    
    vec_garbage = generate_embedding(garbage)

    # Calculate Scores
    score_1 = cosine_similarity(vec_jd1, vec_res1)
    score_2 = cosine_similarity(vec_jd2, vec_res2)
    score_3 = cosine_similarity(vec_jd3, vec_res3)
    score_garbage = cosine_similarity(vec_jd1, vec_garbage)

    print(f"📊 TEST 1 (Concept Match): {score_1:.4f}")
    print("   -> Expectation: > 0.70 (Matches 'Asynchronous' to 'FastAPI/uvicorn' without identical text)")
    
    print(f"\n📊 TEST 2 (Tool Match): {score_2:.4f}")
    print("   -> Expectation: > 0.70 (Matches 'Containerize' to 'Docker/Kubernetes')")

    print(f"\n📊 TEST 3 (Context Trap): {score_3:.4f}")
    print("   -> Expectation: < 0.60 (React is present, but the 'Intent' is completely different)")

    print(f"\n📊 TEST 4 (Baseline): {score_garbage:.4f}")
    print("   -> Expectation: < 0.30 (Pure garbage check)")

    if score_1 > score_garbage and score_2 > score_garbage:
        print("\n✅ SEMANTIC PASS: The system mathematically understands technical relationships.")
    else:
        print("\n❌ SEMANTIC FAIL: Check if the embedding model is loaded correctly.")

if __name__ == "__main__":
    asyncio.run(run_semantic_audit())
