import streamlit as st
from langchain.tools import tool
from src.vectorstore import get_vectorstore, search_documents

@tool
def search_pdf_documents(query: str) -> str:
    """업로드된 PDF 문서 내에서 정보를 검색합니다. 
    사실 확인이나 전문적인 응답이 필요할 때 사용하세요.
    """
    # 세션 상태에 벡터스토어가 있으면 가져오고, 없으면 로드 시도
    vectorstore = st.session_state.get("vectorstore")
    if vectorstore is None:
        vectorstore = get_vectorstore()
        
    if vectorstore is not None:
        docs = search_documents(vectorstore, query, k=3)
        return "\n\n".join([doc.page_content for doc in docs])
    
    return "검색할 문서가 없습니다. 먼저 PDF 파일을 업로드해 주세요."
