from pydantic import BaseModel, Field
from typing import Annotated, TypedDict, List, Optional
from langgraph.graph.message import add_messages

# --- [퀴즈 스키마] ---
class QuizSchema(BaseModel):
    """AI가 생성할 퀴즈의 구조화된 데이터 모델"""
    question: str = Field(description="퀴즈 문제 내용")
    options: List[str] = Field(description="4개의 객관식 선택지 (1~4번 포함)")
    answer: int = Field(description="정답 번호 (1~4)", ge=1, le=4)
    explanation: str = Field(description="문제에 대한 상세 해설")

# --- [LangGraph 상태 스키마] ---
class QuizState(TypedDict):
    """그래프 전체에서 공유되고 유지되는 상태(State) 정의"""
    # 대화 메시지 히스토리 (add_messages를 통해 순차적으로 누적됨)
    messages: Annotated[list, add_messages]
    
    # 라우터 판별 결과 (quiz, qa, coach)
    intent: str
    
    # 현재 활성화된 퀴즈 데이터
    current_quiz: Optional[dict]
    
    # 출제된 퀴즈 이력 (중복 방지용)
    quiz_history: List[dict]
    
    # 오답 기록
    wrong_answers: List[dict]
    
    # 학습 통계
    total_correct: int
    total_attempted: int
    
    # 노드 간 전달되는 검색된 문서 청크
    retrieved_docs: List[str]
