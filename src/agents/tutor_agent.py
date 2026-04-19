from typing import Dict, Any
from src.core.state import AgentState
from src.utils.tools import search_pdf_documents
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

# 모델 초기화 (AGENTS.md 준수)
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

SYSTEM_PROMPT = """당신은 업로드된 PDF 문서를 바탕으로 학습을 돕는 교육 전문가 'Study Tutor'입니다.
1. 사용자의 질문에 대해 'search_pdf_documents' 도구를 사용하여 정확한 정보를 찾으세요.
2. 답변은 반드시 검색된 문서의 내용에만 기반하여 한국어로 작성하세요.
3. 문서에 관련 내용이 없다면 억지로 꾸며내지 말고 솔직하게 모른다고 답변하세요.
4. 학생에게 친절하고 상세하게 설명해 주어야 합니다.
"""

def tutor_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    학습 튜터 노드: PDF 기반 RAG 질의응답을 담당합니다.
    """
    # 도구 바인딩
    model_with_tools = model.bind_tools([search_pdf_documents])
    
    # 메시지 구성 (시스템 프롬프트 포함)
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    
    # 모델 호출
    response = model_with_tools.invoke(messages)
    
    # 만약 도구 호출이 발생했다면 (tool_calls), 
    # LangGraph의 전형적인 구조인 'Action/Observation' 루프를 타야 함.
    # 여기서는 간단하게 invoke 결과(AIMessage)를 반환하고, 
    # 흐름 제어는 graph_builder에서 관리하도록 설계함.
    
    return {"messages": [response]}
