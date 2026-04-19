from langchain.tools import tool
from src.utils.ingestion import get_vectorstore

@tool
def search_pdf_documents(query: str) -> str:
    """업로드된 PDF 문서 내에서 정보를 검색합니다. 
    사실 확인이나 전문적인 내용이 필요할 때 사용하세요.
    """
    vectorstore = get_vectorstore()
    
    if vectorstore is not None:
        docs = vectorstore.similarity_search(query, k=3)
        return "\n\n".join([doc.page_content for doc in docs])
    return "검색할 문서가 없습니다. 먼저 PDF를 업로드해 주세요."
