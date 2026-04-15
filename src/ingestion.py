import os
import streamlit as st
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.config import CHUNK_SIZE, CHUNK_OVERLAP

def load_and_split_pdf(pdf_path: str):
    """
    PDF 파일을 로드하고 지정된 크기로 분할합니다.
    """
    try:
        # 파일 존재 및 크기 확인
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {pdf_path}")
            
        file_size = os.path.getsize(pdf_path) / (1024 * 1024) # MB 단위
        if file_size > 50:
            raise ValueError(f"파일 크기({file_size:.1f}MB)가 너무 큽니다. 50MB 이하의 파일만 지원합니다.")
            
        # 1. PDF 로드
        loader = PyMuPDFLoader(pdf_path)
        docs = loader.load()
        
        if not docs:
            raise ValueError("PDF에서 텍스트를 추출할 수 없습니다. 문서가 비어있거나 스캔된 이미지일 수 있습니다.")

        # 2. 텍스트 분할
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, 
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", "!", "?", " ", ""]
        )
        split_docs = text_splitter.split_documents(docs)
        
        # 퀴즈 생성용 전체 컨텍스트 (메모리 효율을 위해 나중에 RAG로 대체할 예정이나 현재 호환성 유지)
        full_context = "\n".join([doc.page_content for doc in docs])
        
        return split_docs, full_context

    except Exception as e:
        st.error(f"❌ PDF 처리 중 오류 발생: {str(e)}")
        return None, None
