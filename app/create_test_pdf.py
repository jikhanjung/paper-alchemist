#!/usr/bin/env python3
"""
테스트용 PDF 파일 생성 스크립트
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import os

def create_test_pdf(filename="test_paper.pdf"):
    """과학 논문 형태의 테스트 PDF 생성"""
    
    doc = SimpleDocTemplate(filename, pagesize=A4,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=18)
    
    # 스타일 정의
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1,  # 중앙 정렬
        textColor=colors.black
    )
    
    author_style = ParagraphStyle(
        'Author',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20,
        alignment=1,  # 중앙 정렬
        textColor=colors.black
    )
    
    abstract_style = ParagraphStyle(
        'Abstract',
        parent=styles['Normal'],
        fontSize=10,
        leftIndent=36,
        rightIndent=36,
        spaceAfter=20,
        textColor=colors.black
    )
    
    # 문서 내용 구성
    story = []
    
    # 제목
    title = Paragraph("Deep Learning Approaches for Automated Document Processing: A Comprehensive Survey", title_style)
    story.append(title)
    story.append(Spacer(1, 12))
    
    # 저자
    authors = Paragraph("John Smith¹, Jane Doe², Michael Johnson¹", author_style)
    story.append(authors)
    
    affiliations = Paragraph("¹Department of Computer Science, Stanford University<br/>²MIT Computer Science and Artificial Intelligence Laboratory", author_style)
    story.append(affiliations)
    story.append(Spacer(1, 24))
    
    # Abstract
    abstract_title = Paragraph("<b>Abstract</b>", styles['Heading2'])
    story.append(abstract_title)
    
    abstract_text = """
    This paper presents a comprehensive survey of deep learning approaches for automated document processing. 
    We analyze various neural network architectures including Convolutional Neural Networks (CNNs), 
    Recurrent Neural Networks (RNNs), and Transformer models for tasks such as Optical Character Recognition (OCR), 
    document layout analysis, and information extraction. Our study covers over 150 recent publications and 
    provides a systematic evaluation of different methodologies. We introduce a novel benchmark dataset 
    containing 50,000 documents across multiple domains and languages. Experimental results demonstrate 
    that transformer-based models achieve state-of-the-art performance with an average accuracy of 94.7% 
    on document understanding tasks. We also discuss current challenges and future research directions 
    in the field of automated document processing.
    """
    
    abstract_para = Paragraph(abstract_text, abstract_style)
    story.append(abstract_para)
    story.append(Spacer(1, 24))
    
    # Keywords
    keywords = Paragraph("<b>Keywords:</b> Deep Learning, Document Processing, OCR, Natural Language Processing, Computer Vision", styles['Normal'])
    story.append(keywords)
    story.append(Spacer(1, 24))
    
    # 1. Introduction
    intro_title = Paragraph("1. Introduction", styles['Heading2'])
    story.append(intro_title)
    
    intro_text = """
    Document processing has become increasingly important in the digital age, with millions of documents 
    being generated and processed daily across various industries. Traditional rule-based approaches 
    have limitations in handling the diversity and complexity of real-world documents. Recent advances 
    in deep learning have opened new possibilities for automated document understanding and processing.
    
    The field of automated document processing encompasses several key tasks: (1) Optical Character 
    Recognition (OCR) for converting scanned documents to text, (2) Document layout analysis for 
    understanding document structure, (3) Information extraction for identifying and extracting 
    specific data points, and (4) Document classification for categorizing documents based on content.
    
    This survey aims to provide a comprehensive overview of deep learning techniques applied to these 
    tasks, analyzing their strengths, limitations, and potential for future development.
    """
    
    intro_para = Paragraph(intro_text, styles['Normal'])
    story.append(intro_para)
    story.append(Spacer(1, 18))
    
    # 2. Related Work
    related_title = Paragraph("2. Related Work", styles['Heading2'])
    story.append(related_title)
    
    related_text = """
    Early work in document processing relied heavily on handcrafted features and traditional machine 
    learning algorithms. Lecun et al. (1998) pioneered the use of convolutional neural networks for 
    document analysis, demonstrating their effectiveness in recognizing handwritten digits and characters.
    
    The introduction of attention mechanisms by Bahdanau et al. (2014) revolutionized sequence-to-sequence 
    learning, which proved beneficial for OCR tasks involving sequential text recognition. Vaswani et al. 
    (2017) further advanced the field with the Transformer architecture, enabling more effective modeling 
    of long-range dependencies in text.
    
    Recent work has focused on end-to-end learning approaches that jointly optimize multiple document 
    processing tasks. Notable contributions include LayoutLM (Xu et al., 2020) for document understanding 
    and BERT-based models for information extraction tasks.
    """
    
    related_para = Paragraph(related_text, styles['Normal'])
    story.append(related_para)
    story.append(Spacer(1, 18))
    
    # 3. Methodology
    method_title = Paragraph("3. Methodology", styles['Heading2'])
    story.append(method_title)
    
    method_text = """
    Our survey methodology consists of three main phases: (1) Literature collection and screening, 
    (2) Systematic analysis and categorization, and (3) Experimental evaluation.
    
    We collected papers from major conferences and journals including ICCV, CVPR, ICML, NeurIPS, 
    and ACL, focusing on publications from 2018 to 2023. Our search strategy included keywords 
    such as "document processing", "OCR", "document understanding", and "information extraction".
    
    For experimental evaluation, we implemented and tested representative models on our benchmark 
    dataset, measuring performance across multiple metrics including accuracy, precision, recall, 
    and processing speed.
    """
    
    method_para = Paragraph(method_text, styles['Normal'])
    story.append(method_para)
    story.append(Spacer(1, 18))
    
    # 표 추가
    table_title = Paragraph("Table 1: Performance Comparison of Different Approaches", styles['Heading3'])
    story.append(table_title)
    
    table_data = [
        ['Method', 'Accuracy (%)', 'Speed (ms)', 'Memory (MB)'],
        ['CNN-based OCR', '87.3', '45', '256'],
        ['RNN-based OCR', '89.1', '67', '512'],
        ['Transformer OCR', '94.7', '23', '1024'],
        ['Hybrid Approach', '92.4', '34', '768']
    ]
    
    table = Table(table_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 18))
    
    # 4. Results
    results_title = Paragraph("4. Results and Discussion", styles['Heading2'])
    story.append(results_title)
    
    results_text = """
    Our experimental results demonstrate that transformer-based approaches consistently outperform 
    traditional CNN and RNN architectures across all evaluated metrics. The superior performance 
    can be attributed to the attention mechanism's ability to capture long-range dependencies 
    and contextual information effectively.
    
    Notably, our hybrid approach combining convolutional features with transformer attention 
    achieves competitive results while maintaining reasonable computational efficiency. This 
    suggests that combining different architectural paradigms can lead to practical solutions 
    for real-world applications.
    
    Error analysis reveals that current approaches still struggle with heavily distorted text, 
    complex layouts, and multilingual documents. These challenges represent important directions 
    for future research.
    """
    
    results_para = Paragraph(results_text, styles['Normal'])
    story.append(results_para)
    story.append(Spacer(1, 18))
    
    # 5. Conclusion
    conclusion_title = Paragraph("5. Conclusion", styles['Heading2'])
    story.append(conclusion_title)
    
    conclusion_text = """
    This survey provides a comprehensive overview of deep learning approaches for automated document 
    processing. We have systematically analyzed over 150 publications and demonstrated the superiority 
    of transformer-based models through extensive experiments.
    
    Key contributions of this work include: (1) A systematic categorization of existing approaches, 
    (2) Introduction of a comprehensive benchmark dataset, (3) Experimental validation of different 
    methodologies, and (4) Identification of future research directions.
    
    Future work should focus on improving robustness to document variations, developing more 
    efficient architectures for real-time processing, and exploring few-shot learning approaches 
    for domain adaptation.
    """
    
    conclusion_para = Paragraph(conclusion_text, styles['Normal'])
    story.append(conclusion_para)
    story.append(Spacer(1, 18))
    
    # References
    ref_title = Paragraph("References", styles['Heading2'])
    story.append(ref_title)
    
    references = [
        "Bahdanau, D., Cho, K., & Bengio, Y. (2014). Neural machine translation by jointly learning to align and translate. arXiv preprint arXiv:1409.0473.",
        "LeCun, Y., Bottou, L., Bengio, Y., & Haffner, P. (1998). Gradient-based learning applied to document recognition. Proceedings of the IEEE, 86(11), 2278-2324.",
        "Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., ... & Polosukhin, I. (2017). Attention is all you need. Advances in neural information processing systems, 30.",
        "Xu, Y., Li, M., Cui, L., Huang, S., Wei, F., & Zhou, M. (2020). LayoutLM: Pre-training of text and layout for document image understanding. In Proceedings of the 26th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining (pp. 1192-1200)."
    ]
    
    for ref in references:
        ref_para = Paragraph(ref, styles['Normal'])
        story.append(ref_para)
        story.append(Spacer(1, 6))
    
    # PDF 생성
    doc.build(story)
    print(f"테스트 PDF 생성 완료: {filename}")

if __name__ == "__main__":
    create_test_pdf()