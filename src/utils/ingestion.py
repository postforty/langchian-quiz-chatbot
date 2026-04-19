import os
import streamlit as st
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 환경 변수 로드 (이미 main.py에서 수행하지만 개별 모듈 테스트를 위해 추가 가능)
# from dotenv import load_dotenv
# load_dotenv()

# --- [설정 정보] ---
DB_PATH = "faiss_index_pdf_quiz"
EMBEDDING_MODEL = "models/gemini-embedding-001"

def get_embeddings():
    """Gemini 임베딩 모델 초기화"""
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        transport='rest' # Streamlit 환경 호환성
    )

def get_vectorstore():
    """로컬에 저장된 FAISS 인덱스를 로드합니다."""
    if os.path.exists(DB_PATH):
        return FAISS.load_local(
            DB_PATH, 
            get_embeddings(), 
            allow_dangerous_deserialization=True
        )
    return None

def load_and_parse_pdf(pdf_path: str):
    """
    PDF를 로드하고 텍스트를 분할하여 벡터스토어에 저장합니다.
    
    Returns:
        tuple: (vectorstore, full_text)
    """
    # 1. PDF 로드
    loader = PyMuPDFLoader(pdf_path)
    docs = loader.load()

    # 2. 텍스트 분할 (Chunking 전략)
    # TODO: AGENTS.md에 따라 나중에 이 부분의 전략 변경(실험)이 가능하도록 관리 필요
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=100
    )
    split_docs = text_splitter.split_documents(docs)

    # 3. 벡터스토어 생성 및 로컬 저장
    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    vectorstore.save_local(DB_PATH)
    
    # 4. 전체 컨텍스트 추출 (퀴즈 생성용)
    full_text = "\n".join([doc.page_content for doc in docs])
    
    return vectorstore, full_text

def clear_vectorstore_cache():
    """벡터스토어 관련 캐시를 초기화합니다 (필요한 경우)."""
    # Streamlit의 st.cache_resource를 사용하는 경우 외부에서 호출할 수 있도록 정의
    pass
