"""Generate two distinct test resumes for end-to-end validation."""
from fpdf import FPDF

def make_resume(filename, name, email, github, summary, skills, projects, education):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, name, ln=1, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Email: {email}  |  GitHub: github.com/{github}", ln=1, align="C")
    pdf.ln(4)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Summary", ln=1)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 6, summary)
    pdf.ln(3)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Technical Skills", ln=1)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 6, skills)
    pdf.ln(3)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Projects", ln=1)
    pdf.set_font("Arial", "", 10)
    for proj in projects:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 7, proj["title"], ln=1)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 6, proj["desc"])
        pdf.cell(0, 6, f"Tech Stack: {proj['stack']}", ln=1)
        pdf.ln(2)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Education", ln=1)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 6, education)

    pdf.output(filename)
    print(f"Generated {filename}")


# ── Student A: Strong AI/ML Candidate ──────────────────────────────────────
make_resume(
    filename="resume_student_a.pdf",
    name="Priya Sharma",
    email="priya.sharma@example.com",
    github="priyasharma-ml",
    summary=(
        "Final-year B.Tech CSE student at IIT Delhi specializing in Artificial Intelligence "
        "and Machine Learning. CGPA: 9.2/10. Passionate about building production-grade ML "
        "systems with experience in NLP, computer vision, and MLOps. 2x hackathon winner."
    ),
    skills=(
        "Programming: Python, C++\n"
        "ML/DL: TensorFlow, PyTorch, Scikit-Learn, Keras, XGBoost, LightGBM\n"
        "NLP: HuggingFace Transformers, BERT, GPT, spaCy, NLTK, LangChain\n"
        "Data: Pandas, NumPy, Matplotlib, Seaborn, SQL, Apache Spark\n"
        "MLOps: Docker, Kubernetes, MLflow, FastAPI, AWS SageMaker\n"
        "Tools: Git, GitHub Actions, Jupyter, Linux"
    ),
    projects=[
        {
            "title": "Medical Image Segmentation using U-Net (PyTorch)",
            "desc": (
                "Built a semantic segmentation pipeline for MRI scans achieving 94% Dice score. "
                "Trained on 10,000 annotated images using transfer learning from ResNet-50. "
                "Deployed as a FastAPI microservice with Docker on AWS EC2."
            ),
            "stack": "PyTorch, FastAPI, Docker, AWS, ResNet-50, U-Net, OpenCV, NumPy"
        },
        {
            "title": "Real-Time Sentiment Analysis Pipeline (BERT + Kafka)",
            "desc": (
                "Designed a real-time NLP pipeline processing 50,000 tweets/second using "
                "Apache Kafka for streaming and fine-tuned BERT for sentiment classification. "
                "Achieved 91% accuracy on financial news datasets."
            ),
            "stack": "BERT, HuggingFace, Kafka, Python, Pandas, Scikit-Learn, SQL"
        },
        {
            "title": "Candidate Ranking System using Semantic Embeddings",
            "desc": (
                "Built an ATS-replacement system using sentence-transformers and pgvector "
                "for semantic similarity matching between job descriptions and resumes. "
                "Outperformed keyword-based matching by 40% in recruiter satisfaction surveys."
            ),
            "stack": "Python, FastAPI, SentenceTransformers, PostgreSQL, pgvector, Docker"
        },
    ],
    education="B.Tech Computer Science Engineering, IIT Delhi, 2024. CGPA: 9.2/10."
)


# ── Student B: Weaker Web/Frontend Candidate ───────────────────────────────
make_resume(
    filename="resume_student_b.pdf",
    name="Rahul Verma",
    email="rahul.verma@example.com",
    github="rahulverma-web",
    summary=(
        "Third-year B.Sc IT student at NMIMS Mumbai. Interested in web development. "
        "CGPA: 6.8/10. Some exposure to JavaScript and React. "
        "Looking for my first industry experience."
    ),
    skills=(
        "Programming: JavaScript, HTML, CSS\n"
        "Frameworks: React (basic), Bootstrap\n"
        "Tools: Git, VS Code\n"
        "Databases: MySQL (basic)\n"
        "Other: Python (beginner), Machine Learning (heard about it)"
    ),
    projects=[
        {
            "title": "Personal Portfolio Website",
            "desc": (
                "Built a personal portfolio website to showcase my projects and skills. "
                "Used HTML, CSS and a little JavaScript for animations."
            ),
            "stack": "HTML, CSS, JavaScript"
        },
        {
            "title": "To-Do List App (React)",
            "desc": (
                "Simple to-do list web application built with React for state management practice. "
                "Supports adding and deleting tasks."
            ),
            "stack": "React, JavaScript, CSS"
        },
    ],
    education="B.Sc Information Technology, NMIMS Mumbai, 2025 (ongoing). CGPA: 6.8/10."
)
