from typing import Annotated, List, Optional, Dict, Any, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    LangGraph에서 에이전트 간 공유되는 상태 정의
    """
    # 채팅 메시지 히스토리 (메시지가 추가될 때마다 리스트가 업데이트됨)
    messages: Annotated[List[BaseMessage], add_messages]
    
    # 애플리케이션 모드 세션 데이터
    mode: str  # "퀴즈 풀기" 또는 "질문하기"
    
    # PDF 관련 데이터
    pdf_context: str # 퀴즈 생성을 위한 PDF 전체 텍스트
    pdf_processed: bool # PDF 분석 완료 여부
    
    # 퀴즈 관련 상태
    current_question: Optional[Dict[str, Any]] # 현재 진행 중인 퀴즈 (question, options, answer, explanation)
    wrong_answers: List[Dict[str, Any]] # 틀린 문제 기록 (정적 데이터로 관리)
    
    # 에이전트 제어용 필드
    next_node: Optional[str] # 다음에 실행할 노드 (Supervisor가 결정)
    guardrail_response: Optional[str] # 가드레일에 의해 생성된 즉시 응답용
