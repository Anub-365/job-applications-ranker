from fpdf import FPDF

def clean(s):
    return (s.replace('\u2014', '--').replace('\u2013', '-')
             .replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
             .replace('&', 'and'))

def make_resume(filename, name, email, github, summary, skills_sections, projects, education):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, clean(name), ln=1, align='C')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, clean(f'Email: {email}  |  GitHub: github.com/{github}'), ln=1, align='C')
    pdf.ln(4)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Professional Summary', ln=1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, clean(summary))
    pdf.ln(3)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Technical Skills', ln=1)
    for section, skills in skills_sections.items():
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(40, 6, clean(section) + ':', ln=0)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 6, clean(skills))
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Key Projects', ln=1)
    for proj in projects:
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 7, clean(proj['title']), ln=1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 6, clean(proj['desc']))
        pdf.set_font('Arial', 'I', 9)
        pdf.cell(0, 6, 'Technologies: ' + clean(proj['stack']), ln=1)
        pdf.ln(2)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Education', ln=1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, clean(education))
    pdf.output(filename)
    print(f'Generated: {filename}')

make_resume(
    'resume_priya.pdf', 'Priya Sharma', 'priya.sharma.e2e@example.com', 'keras-team',
    'Final-year B.Tech CSE (AI) at IIT Delhi. CGPA 9.2/10. 2+ years in deep learning, NLP, MLOps. Built production ML systems. 2x Hackathon winner.',
    {
        'Languages':   'Python, C++, SQL',
        'ML/DL':       'TensorFlow, PyTorch, Scikit-Learn, XGBoost, Keras',
        'NLP':         'HuggingFace Transformers, BERT, GPT-2, spaCy, LangChain',
        'MLOps':       'Docker, Kubernetes, MLflow, FastAPI, AWS SageMaker',
        'Tools':       'Git, Jupyter, Linux, Bash',
    },
    [
        {
            'title': 'Medical Image Segmentation -- U-Net (PyTorch)',
            'desc': 'Semantic segmentation for MRI brain tumour scans. 94% Dice score on BraTS2021 (10,000 images). Transfer learning from ResNet-50. Deployed as FastAPI microservice on AWS EC2. Serving 500 radiologists daily.',
            'stack': 'PyTorch, FastAPI, Docker, AWS, ResNet-50, U-Net, OpenCV, NumPy, MLflow',
        },
        {
            'title': 'Real-Time Sentiment Pipeline -- BERT + Kafka',
            'desc': 'NLP pipeline processing 50,000 tweets/second. Fine-tuned BERT for 3-class sentiment on financial news. 91% accuracy. Kafka streaming with Spark for aggregation.',
            'stack': 'BERT, HuggingFace Transformers, Kafka, PySpark, Python, Scikit-Learn',
        },
        {
            'title': 'Resume Ranking System -- Semantic Embeddings + pgvector',
            'desc': 'AI-powered ATS using sentence-transformers and pgvector for semantic similarity matching. Outperformed keyword ATS by 40%. FastAPI backend, PostgreSQL with pgvector.',
            'stack': 'Python, FastAPI, SentenceTransformers, PostgreSQL, pgvector, Docker',
        },
    ],
    'B.Tech CSE (AI Specialization), IIT Delhi, 2020-2024. CGPA: 9.2/10.'
)

make_resume(
    'resume_priyansh.pdf', 'Priyansh Verma', 'priyansh.verma.e2e@example.com', 'huggingface',
    'B.Tech + M.Tech Dual Degree CSE + AI at IIT Bombay. CGPA 9.6/10. Published ML researcher (NeurIPS 2023 workshop). Contributor to open-source LLM tooling. Interned at Google DeepMind and Microsoft Research.',
    {
        'Languages':   'Python, C++, CUDA, Julia',
        'ML/DL':       'PyTorch, JAX, TensorFlow, TensorRT, DeepSpeed, ONNX',
        'LLM/NLP':     'HuggingFace Transformers, LLaMA, BERT, T5, LoRA, PEFT, LangChain, RAG',
        'Computer Vision': 'OpenCV, YOLOv8, Detectron2, CLIP, Stable Diffusion',
        'MLOps':       'Kubernetes, Docker, Ray, vLLM, MLflow, DVC, Weights and Biases, GCP Vertex AI',
    },
    [
        {
            'title': 'LLM Fine-Tuning Pipeline -- LoRA + QLoRA (PyTorch + DeepSpeed)',
            'desc': 'Production fine-tuning for 7B/13B LLaMA models. 4-bit QLoRA reduced GPU memory by 60%. DeepSpeed ZeRO-3 across 8xA100 GPUs. MMLU benchmark 72.3% vs 67.1% base. Published at NeurIPS 2023 workshop.',
            'stack': 'PyTorch, DeepSpeed, LoRA, QLoRA, LLaMA, HuggingFace PEFT, Weights and Biases, CUDA',
        },
        {
            'title': 'Multimodal RAG System -- CLIP + LangChain + pgvector',
            'desc': 'Enterprise document QA combining visual and textual retrieval. CLIP embeddings + sentence-transformers stored in pgvector. GPT-4 for answer synthesis. 95% retrieval accuracy. Deployed on GCP with Kubernetes.',
            'stack': 'CLIP, LangChain, pgvector, GPT-4, SentenceTransformers, FastAPI, GCP, Kubernetes',
        },
        {
            'title': 'Real-Time Object Detection -- YOLOv8 + TensorRT (Edge AI)',
            'desc': 'YOLOv8 optimized with TensorRT for NVIDIA Jetson Orin. 78 FPS vs 12 FPS baseline. Deployed across 200 smart cameras for warehouse automation at Reliance Retail.',
            'stack': 'YOLOv8, TensorRT, ONNX, Python, OpenCV, CUDA, NVIDIA Jetson, Docker',
        },
    ],
    'B.Tech + M.Tech Dual Degree, CSE + AI, IIT Bombay, 2020-2025. CGPA: 9.6/10. Publications: NeurIPS 2023, ICLR 2024 (workshops).'
)

print('Done.')
