"""文件加载工具：读取txt/docx/pdf/csv格式文件"""
import pandas as pd
from docx import Document
import PyPDF2


def load_file(file):
    file_type = file.name.split(".")[-1].lower()
    try:
        if file_type == "txt":
            return file.read().decode("utf-8")
        elif file_type == "docx":
            doc = Document(file)
            return "\n".join([para.text for para in doc.paragraphs])
        elif file_type == "pdf":
            pdf_reader = PyPDF2.PdfReader(file)
            return "\n".join([page.extract_text() for page in pdf_reader.pages])
        elif file_type == "csv":
            df = pd.read_csv(file)
            return df.to_string(index=False)
        else:
            return ""
    except Exception as e:
        print(f"读取文件失败：{str(e)}")
        return ""
