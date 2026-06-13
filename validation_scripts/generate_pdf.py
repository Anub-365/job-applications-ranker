from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.cell(200, 10, txt="John Doe - Full Stack & AI Intern", ln=1, align='C')
pdf.cell(200, 10, txt="Email: johndoe123@example.com", ln=1, align='C')
pdf.cell(200, 10, txt="GitHub: @johndoe", ln=1, align='C')
pdf.cell(200, 10, txt="", ln=1)

pdf.cell(200, 10, txt="Skills: Python, Machine Learning, Data Analytics, React, Node.js", ln=1)
pdf.cell(200, 10, txt="Experience: Built a sentiment analysis tool using PyTorch.", ln=1)

pdf.output("sample_resume.pdf")
print("Generated sample_resume.pdf")
