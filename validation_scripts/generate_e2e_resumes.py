"""Generate two distinct AI/ML resumes for E2E ranking validation."""
from fpdf import FPDF


def make_resume(filename, name, email, github, summary, skills_sections, projects, education):
    pdf = FPDF()
    pdf.add_page()

    # Header
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, name, ln=1, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Email: {email}  |  GitHub: github.com/{github}", ln=1, align="C")
    pdf.ln(4)

    # Summary
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Professional Summary", ln=1)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 6, summary)
    pdf.ln(3)

    # Skills
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Technical Skills", ln=1)
    pdf.set_font("Arial", "", 10)
    for section_name, skills in skills_sections.items():
        pdf.set_font("Arial", "B", 10)
        pdf.cell(40, 6, f"{section_name}:", ln=0)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 6, skills)
    pdf.ln(2)

    # Projects
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Key Projects", ln=1)
    for proj in projects:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 7, proj["title"], ln=1)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 6, proj["desc"])
        pdf.set_font("Arial", "I", 9)
        pdf.cell(0, 6, f"Technologies: {proj['stack']}", ln=1)
        pdf.ln(2)

    # Education
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Education", ln=1)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 6, education)

    pdf.output(filename)
    print(f"Generated: {filename}")


# ── Student A: Priya Sharma ─ Strong AI/ML (IIT Delhi, CGPA 9.2) ──────────
make_resume(
    filename="resume_priya.pdf",
    name="Priya Sharma",
    email="priya.sharma.test@example.com",
    github="keras-team",
    summary=(
        "Final-year B.Tech CSE (AI specialization) at IIT Delhi. CGPA 9.2/10. "
        "2+ years hands-on with deep learning, NLP and MLOps. "
        "Built production ML systems serving 100k+ users. "
        "2x Hackathon winner (Smart India Hackathon 2023, ML India Cup 2024)."
    ),
    skills_sections={
        "Languages":   "Python, C++, SQL",
        "ML/DL":       "TensorFlow, PyTorch, Scikit-Learn, XGBoost, LightGBM, Keras",
        "NLP":         "HuggingFace Transformers, BERT, GPT-2, spaCy, LangChain",
        "Data":        "Pandas, NumPy, Matplotlib, Apache Spark, SQL",
        "MLOps":       "Docker, Kubernetes, MLflow, FastAPI, AWS SageMaker, GitHub Actions",
        "Tools":       "Git, Jupyter, Linux, Bash",
    },
    projects=[
        {
            "title": "Medical Image Segmentation — U-Net (PyTorch)",
            "desc": (
                "Semantic segmentation pipeline for MRI brain tumour scans. "
                "94% Dice score on BraTS2021 dataset (10,000 images). "
                "Transfer learning from ResNet-50. Deployed as FastAPI microservice "
                "on AWS EC2 via Docker. Serving 500 radiologists daily."
            ),
            "stack": "PyTorch, FastAPI, Docker, AWS EC2, ResNet-50, U-Net, OpenCV, NumPy, MLflow",
        },
        {
            "title": "Real-Time Sentiment Pipeline — BERT + Kafka",
            "desc": (
                "End-to-end NLP pipeline processing 50,000 tweets/second. "
                "Fine-tuned BERT for 3-class sentiment classification on financial news. "
                "91% accuracy, <50ms latency. Kafka streaming with Spark for aggregation."
            ),
            "stack": "BERT, HuggingFace Transformers, Kafka, PySpark, Python, Scikit-Learn",
        },
        {
            "title": "Resume Ranking System — Semantic Embeddings + pgvector",
            "desc": (
                "AI-powered ATS replacement using sentence-transformers and pgvector "
                "for semantic similarity matching. Outperformed keyword ATS by 40% in "
                "recruiter satisfaction. FastAPI backend, PostgreSQL with pgvector."
            ),
            "stack": "Python, FastAPI, SentenceTransformers, PostgreSQL, pgvector, Docker",
        },
    ],
    education=(
        "B.Tech Computer Science & Engineering (AI Specialization)\n"
        "Indian Institute of Technology Delhi | 2020-2024 | CGPA: 9.2/10\n"
        "Relevant coursework: Deep Learning, NLP, Computer Vision, Distributed Systems"
    ),
)


# ── Student B: Priyansh Verma ─ Advanced AI/ML (IIT Bombay, CGPA 9.6) ─────
make_resume(
    filename="resume_priyansh.pdf",
    name="Priyansh Verma",
    email="priyansh.verma.test@example.com",
    github="huggingface",
    summary=(
        "Pre-final year B.Tech CSE + M.Tech AI (dual degree) at IIT Bombay. CGPA 9.6/10. "
        "Published ML researcher (NeurIPS 2023 workshop). "
        "Core contributor to open-source LLM tooling. "
        "3 years deep learning research under Prof. Sunita Sarawagi. "
        "Interned at Google DeepMind and Microsoft Research."
    ),
    skills_sections={
        "Languages":   "Python, C++, CUDA, Julia",
        "ML/DL":       "PyTorch, JAX, TensorFlow, Triton, ONNX, TensorRT, DeepSpeed",
        "LLM/NLP":     "HuggingFace Transformers, LLaMA, GPT-4, BERT, T5, LoRA, PEFT, LangChain, RAG",
        "Computer Vision": "OpenCV, YOLO, Detectron2, SAM, CLIP, Stable Diffusion",
        "MLOps":       "Kubernetes, Docker, Ray, vLLM, Triton Inference Server, MLflow, DVC, Weights & Biases",
        "Data":        "Pandas, NumPy, Polars, Apache Spark, Databricks, Snowflake",
        "Cloud":       "GCP (Vertex AI, TPUs), AWS (SageMaker, EC2), Azure ML",
    },
    projects=[
        {
            "title": "LLM Fine-Tuning Pipeline — LoRA + QLoRA (PyTorch + DeepSpeed)",
            "desc": (
                "Production-grade fine-tuning pipeline for 7B/13B LLaMA models on custom "
                "domain corpora. 4-bit QLoRA reduced GPU memory by 60%. "
                "DeepSpeed ZeRO-3 for distributed training across 8xA100 GPUs. "
                "MMLU benchmark: 72.3% (vs 67.1% base). Published at NeurIPS 2023 workshop."
            ),
            "stack": "PyTorch, DeepSpeed, LoRA, QLoRA, LLaMA, HuggingFace PEFT, Weights & Biases, CUDA",
        },
        {
            "title": "Multimodal RAG System — CLIP + LangChain + pgvector",
            "desc": (
                "Enterprise document Q&A system combining visual and textual retrieval. "
                "CLIP embeddings for images, sentence-transformers for text stored in pgvector. "
                "GPT-4 for answer synthesis. 95% retrieval accuracy on internal benchmarks. "
                "Deployed on GCP with autoscaling Kubernetes pods."
            ),
            "stack": "CLIP, LangChain, pgvector, GPT-4, SentenceTransformers, FastAPI, GCP, Kubernetes",
        },
        {
            "title": "Real-Time Object Detection — YOLO + TensorRT (Edge AI)",
            "desc": (
                "YOLO-v8 model optimized with TensorRT for deployment on NVIDIA Jetson Orin. "
                "78 FPS inference (vs 12 FPS baseline). "
                "Deployed across 200 smart cameras for warehouse automation at Reliance Retail."
            ),
            "stack": "YOLOv8, TensorRT, ONNX, Python, OpenCV, CUDA, NVIDIA Jetson, Docker",
        },
    ],
    education=(
        "B.Tech + M.Tech Dual Degree, CSE + Artificial Intelligence\n"
        "Indian Institute of Technology Bombay | 2020-2025 | CGPA: 9.6/10\n"
        "Publications: NeurIPS 2023 (workshop), ICLR 2024 (workshop)\n"
        "Internships: Google DeepMind (2023), Microsoft Research India (2022)"
    ),
)

print("\nBoth resumes generated successfully.")
