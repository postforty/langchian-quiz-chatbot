import os
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from src.config import EMBEDDING_MODEL, FAISS_INDEX_PATH

@st.cache_resource
def get_embeddings():
    """임베딩 객체를 캐싱하여 재사용합니다."""
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        transport='rest'
    )

def get_vectorstore():
    """기존 FAISS 인덱스를 로드하거나 None을 반환합니다."""
    if os.path.exists(FAISS_INDEX_PATH):
        try:
            # allow_dangerous_deserialization=True는 로컬에서 생성된 신뢰할 수 있는 
            # 인덱스 파일 로드 시에만 사용해야 합니다.
            return FAISS.load_local(
                FAISS_INDEX_PATH, 
                get_embeddings(), 
                allow_dangerous_deserialization=True
            )
        except Exception as e:
            st.warning(f"벡터 저장소 로드 실패: {e}")
            return None
    return None

def save_vectorstore(documents):
    """문서 리스트를 벡터화하여 로컬에 저장합니다."""
    try:
        vectorstore = FAISS.from_documents(documents, get_embeddings())
        vectorstore.save_local(FAISS_INDEX_PATH)
        return vectorstore
    except Exception as e:
        st.error(f"벡터 저장소 저장 중 오류 발생: {e}")
        return None

def search_documents(vectorstore, query: str, k: int = 3):
    """유사도 검색을 수행합니다."""
    if vectorstore:
        try:
            return vectorstore.similarity_search(query, k=k)
        except Exception as e:
            st.error(f"검색 중 오류 발생: {e}")
            return []
    return []
