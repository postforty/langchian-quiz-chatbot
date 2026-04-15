import os
from dotenv import load_dotenv
import streamlit as st

# .env 파일 로드
load_dotenv()

def validate_env():
    """필수 환경 변수 검증"""
    if not os.getenv("GOOGLE_API_KEY"):
        st.error("❌ GOOGLE_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
        st.stop()

# --- [모델 설정] ---
# 의도 분류 및 경량 작업용
ROUTER_MODEL = "gemini-2.5-flash-lite"
# 퀴즈 생성 및 주요 응답용
MAIN_MODEL = "gemini-2.5-flash"
# 임베딩 모델
EMBEDDING_MODEL = "models/gemini-embedding-001"

# --- [텍스트 처리 설정] ---
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

# --- [스토리지 설정] ---
FAISS_INDEX_PATH = "faiss_index_pdf_quiz"

# --- [UI/UX 설정] ---
PAGE_TITLE = "PDF AI 퀴즈 챗봇"
PAGE_ICON = "📖"
