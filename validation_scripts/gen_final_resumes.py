import os
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

# Candidate A: Strong AI Engineer
make_resume(
    'resume_strong.pdf', 'Arjun Karpathy', 'arjun.strong@example.com', 'karpathy',
    'Senior AI Engineer with 6 years of experience building and deploying scalable Deep Learning and NLP systems. Ex-OpenAI, ex-Tesla.',
    {
        'Languages': 'Python, C++, CUDA',
        'ML/DL': 'PyTorch, TensorFlow, Keras, JAX',
        'NLP': 'HuggingFace, BERT, LLaMA, GPT-4, LangChain',
        'MLOps': 'Docker, Kubernetes, AWS, Triton',
    },
    [
        {
            'title': 'LLM Training Framework in PyTorch',
            'desc': 'Built a lightweight PyTorch-based training framework for LLMs using DeepSpeed ZeRO-3. Reduced memory footprint by 40%.',
            'stack': 'PyTorch, Python, CUDA, DeepSpeed'
        },
        {
            'title': 'Computer Vision Inference API',
            'desc': 'Deployed YOLOv8 models via FastAPI and TensorRT. Served 10,000 requests/sec on Kubernetes.',
            'stack': 'Python, FastAPI, TensorRT, Kubernetes, Docker'
        }
    ],
    'Ph.D. in Computer Science (AI), Stanford University, 2021. CGPA: 9.8/10.'
)

# Candidate B: Average AI Engineer
make_resume(
    'resume_avg.pdf', 'Octo Cat', 'octo.avg@example.com', 'octocat',
    'Software Engineer with an interest in Machine Learning. 2 years of experience building web applications and exploring basic ML models.',
    {
        'Languages': 'Python, Ruby, JavaScript',
        'ML/DL': 'Scikit-Learn, Pandas, basic PyTorch',
        'Web': 'Flask, Ruby on Rails, React',
        'Tools': 'Git, Docker',
    },
    [
        {
            'title': 'Titanic Survival Prediction',
            'desc': 'Standard Kaggle project predicting Titanic survival rates using Random Forest and Logistic Regression.',
            'stack': 'Python, Scikit-Learn, Pandas'
        },
        {
            'title': 'Flask Web Application',
            'desc': 'Built a simple web app for managing tasks with a PostgreSQL database.',
            'stack': 'Python, Flask, SQL'
        }
    ],
    'B.S. in Computer Science, State University, 2022. CGPA: 7.5/10.'
)

# Candidate C: Resume Padding
make_resume(
    'resume_pad.pdf', 'Rahul Fake', 'rahul.fake@example.com', 'rahulverma-web',
    'Expert AI Engineer with 10 years experience building LLMs, scalable ML infrastructure, and self-driving cars.',
    {
        'Languages': 'Python, C++, CUDA, Rust, Go',
        'ML/DL': 'AWS, Kubernetes, PyTorch, TensorFlow, MLOps, OpenAI API',
        'NLP': 'LLM Engineering, LangChain, RAG',
    },
    [
        {
            'title': 'Enterprise LLM Chatbot',
            'desc': 'Built a custom GPT-4 chatbot using LangChain and PyTorch. Deployed on AWS EKS.',
            'stack': 'Python, PyTorch, AWS, Kubernetes, LangChain'
        },
        {
            'title': 'Autonomous Driving Model',
            'desc': 'Trained a 50B parameter self-driving model from scratch using TensorFlow and CUDA.',
            'stack': 'TensorFlow, CUDA, C++'
        }
    ],
    'M.S. in AI, Fake University, 2018. CGPA: 9.9/10.'
)

print('Done.')
