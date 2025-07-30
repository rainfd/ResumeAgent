#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fpdf import FPDF
import os

class UTF8_PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_page()
        # 尝试使用系统字体支持中文
        try:
            # 在Linux系统中查找中文字体
            chinese_fonts = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/TTF/DejaVuSans.ttf',
                '/System/Library/Fonts/Arial.ttf',  # macOS
                'C:\\Windows\\Fonts\\arial.ttf'     # Windows
            ]
            
            font_found = False
            for font_path in chinese_fonts:
                if os.path.exists(font_path):
                    self.add_font('DejaVu', '', font_path, uni=True)
                    self.set_font('DejaVu', size=12)
                    font_found = True
                    break
            
            if not font_found:
                # 回退到内置字体
                self.set_font('Arial', size=12)
                
        except Exception:
            # 如果添加字体失败，使用默认字体
            self.set_font('Arial', size=12)

def create_test_resume_pdf():
    pdf = UTF8_PDF()
    
    # 标题
    pdf.set_font_size(16)
    pdf.cell(0, 10, 'Zhao Liu - AI Engineer Resume', ln=True, align='C')
    pdf.ln(5)
    
    # 基本信息
    pdf.set_font_size(14)
    pdf.cell(0, 8, 'Personal Information', ln=True)
    pdf.set_font_size(10)
    pdf.cell(0, 6, 'Name: Zhao Liu', ln=True)
    pdf.cell(0, 6, 'Age: 27, Male', ln=True)
    pdf.cell(0, 6, 'Phone: 136****6666', ln=True)
    pdf.cell(0, 6, 'Email: zhaoliu@example.com', ln=True)
    pdf.cell(0, 6, 'Education: 2017.09~2021.06 Beijing University Computer Science Master', ln=True)
    pdf.cell(0, 6, 'Experience: 4 years AI/ML development', ln=True)
    pdf.cell(0, 6, 'Expected Salary: 25-40K', ln=True)
    pdf.ln(5)
    
    # 专业技能
    pdf.set_font_size(14)
    pdf.cell(0, 8, 'Technical Skills', ln=True)
    pdf.set_font_size(10)
    pdf.cell(0, 6, 'Programming: Python, Java, C++, JavaScript', ln=True)
    pdf.cell(0, 6, 'AI/ML: TensorFlow, PyTorch, Scikit-learn, Keras', ln=True)
    pdf.cell(0, 6, 'Deep Learning: CNN, RNN, LSTM, Transformer, BERT', ln=True)
    pdf.cell(0, 6, 'NLP: Natural Language Processing, Text Analysis, ChatBot', ln=True)
    pdf.cell(0, 6, 'Computer Vision: OpenCV, Image Recognition, Object Detection', ln=True)
    pdf.cell(0, 6, 'Big Data: Spark, Hadoop, Kafka, ElasticSearch', ln=True)
    pdf.cell(0, 6, 'Cloud: AWS, Google Cloud, Docker, Kubernetes', ln=True)
    pdf.cell(0, 6, 'Database: MySQL, MongoDB, Redis, Vector Database', ln=True)
    pdf.ln(5)
    
    # 工作经历
    pdf.set_font_size(14)
    pdf.cell(0, 8, 'Work Experience', ln=True)
    
    pdf.set_font_size(12)
    pdf.cell(0, 6, 'AI Technology Company | Senior AI Engineer | 2022.03 - Present', ln=True)
    pdf.set_font_size(10)
    pdf.cell(0, 5, 'Responsibilities:', ln=True)
    pdf.cell(0, 5, '- Lead development of large language model applications', ln=True)
    pdf.cell(0, 5, '- Design and implement RAG systems and knowledge graphs', ln=True)
    pdf.cell(0, 5, '- Optimize model inference performance and deployment', ln=True)
    pdf.cell(0, 5, 'Key Achievements:', ln=True)
    pdf.cell(0, 5, '- LLM Application Platform: Built enterprise LLM platform with 95% accuracy', ln=True)
    pdf.cell(0, 5, '- Intelligent Q&A System: Implemented RAG-based system serving 10K+ users', ln=True)
    pdf.cell(0, 5, '- Model Optimization: Reduced inference latency by 60% through quantization', ln=True)
    pdf.ln(3)
    
    pdf.set_font_size(12)
    pdf.cell(0, 6, 'Internet Company B | Machine Learning Engineer | 2021.07 - 2022.02', ln=True)
    pdf.set_font_size(10)
    pdf.cell(0, 5, 'Main Work:', ln=True)
    pdf.cell(0, 5, '- Developed recommendation algorithms and user profiling systems', ln=True)
    pdf.cell(0, 5, '- Built real-time feature engineering pipelines', ln=True)
    pdf.cell(0, 5, '- Participated in A/B testing and model evaluation', ln=True)
    pdf.cell(0, 5, 'Projects:', ln=True)
    pdf.cell(0, 5, '- Recommendation System: Improved CTR by 25% using deep learning', ln=True)
    pdf.cell(0, 5, '- Fraud Detection: Built ML model achieving 92% precision', ln=True)
    pdf.ln(3)
    
    # 项目经历
    pdf.set_font_size(14)
    pdf.cell(0, 8, 'Project Experience', ln=True)
    
    pdf.set_font_size(12)
    pdf.cell(0, 6, 'Enterprise ChatBot System | 2023.06 - 2023.09', ln=True)
    pdf.set_font_size(10)
    pdf.cell(0, 5, 'Tech Stack: Python + FastAPI + LangChain + ChromaDB + OpenAI API', ln=True)
    pdf.cell(0, 5, 'Description:', ln=True)
    pdf.cell(0, 5, '- Built intelligent customer service bot with multi-modal capabilities', ln=True)
    pdf.cell(0, 5, '- Implemented RAG system for accurate knowledge retrieval', ln=True)
    pdf.cell(0, 5, '- Integrated voice recognition and text-to-speech features', ln=True)
    pdf.cell(0, 5, '- Achieved 90% customer satisfaction rate in pilot deployment', ln=True)
    pdf.ln(3)
    
    pdf.set_font_size(12)
    pdf.cell(0, 6, 'Multi-modal Content Understanding | 2023.01 - 2023.04', ln=True)
    pdf.set_font_size(10)
    pdf.cell(0, 5, 'Tech Stack: PyTorch + CLIP + Transformer + Docker', ln=True)
    pdf.cell(0, 5, 'Description:', ln=True)
    pdf.cell(0, 5, '- Developed system for understanding images, text, and video content', ln=True)
    pdf.cell(0, 5, '- Fine-tuned pre-trained models for domain-specific tasks', ln=True)
    pdf.cell(0, 5, '- Built scalable inference pipeline handling 1M+ requests daily', ln=True)
    pdf.ln(3)
    
    # 教育经历
    pdf.set_font_size(14)
    pdf.cell(0, 8, 'Education', ln=True)
    
    pdf.set_font_size(12)
    pdf.cell(0, 6, 'Beijing University | Computer Science | Master | 2019.09 - 2021.06', ln=True)
    pdf.set_font_size(10)
    pdf.cell(0, 5, 'Major Courses: Machine Learning, Deep Learning, NLP, Computer Vision', ln=True)
    pdf.cell(0, 5, 'Thesis: Research on Large Language Model Fine-tuning Methods', ln=True)
    pdf.cell(0, 5, 'Awards: First-class Scholarship (2020), Outstanding Graduate (2021)', ln=True)
    pdf.ln(3)
    
    pdf.set_font_size(12)
    pdf.cell(0, 6, 'Technology Institute | Software Engineering | Bachelor | 2017.09 - 2019.06', ln=True)
    pdf.set_font_size(10)
    pdf.cell(0, 5, 'Major Courses: Data Structures, Algorithms, Database Systems', ln=True)
    pdf.cell(0, 5, 'Awards: Second-class Scholarship (2018)', ln=True)
    pdf.ln(5)
    
    # 技术认证
    pdf.set_font_size(14)
    pdf.cell(0, 8, 'Certifications', ln=True)
    pdf.set_font_size(10)
    pdf.cell(0, 6, '- AWS Certified Machine Learning - Specialty (2023)', ln=True)
    pdf.cell(0, 6, '- Google Cloud Professional ML Engineer (2022)', ln=True)
    pdf.cell(0, 6, '- NVIDIA Deep Learning Institute Certificate (2022)', ln=True)
    pdf.ln(5)
    
    # 自我评价
    pdf.set_font_size(14)
    pdf.cell(0, 8, 'Self Assessment', ln=True)
    pdf.set_font_size(10)
    pdf.cell(0, 5, '- Strong foundation in AI/ML with 4+ years hands-on experience', ln=True)
    pdf.cell(0, 5, '- Expertise in large language models and multi-modal AI systems', ln=True)
    pdf.cell(0, 5, '- Proven track record in building production-ready AI applications', ln=True)
    pdf.cell(0, 5, '- Strong problem-solving skills and ability to work in fast-paced environments', ln=True)
    pdf.cell(0, 5, '- Excellent communication skills and team collaboration experience', ln=True)
    pdf.cell(0, 5, '- Passionate about AI technology trends and continuous learning', ln=True)
    
    # 保存PDF
    output_path = '/home/rainfd/projects/ResumeAgent/data/resumes/test_resume_ai_engineer.pdf'
    pdf.output(output_path)
    print(f"PDF resume created successfully: {output_path}")

if __name__ == "__main__":
    create_test_resume_pdf()