from langgraph.graph import StateGraph, START, END
from src.models import QuizState
from src.nodes import (
    router, quiz_gen, grade, explain, 
    rag_search, coach_analyze
)

# --- [조건부 엣지 함수] ---

def route_by_intent(state: QuizState) -> str:
    """사용자의 의도에 따라 다음 노드를 결정합니다."""
    intent = state.get("intent", "qa")
    if intent == "quiz":
        return "quiz_gen"
    elif intent == "coach":
        return "coach_analyze"
    elif intent == "grade":
        return "grade"
    else:
        return "rag_search"

def route_after_grade(state: QuizState) -> str:
    """채점 결과에 따라 해설을 할지, 종료할지 결정합니다."""
    # 마지막 메시지가 정답 알림인 경우 (노드에서 직접 텍스트 비교는 모호하므로 상태 활용 추천)
    # 여기서는 단순화를 위해 오답 기록이 직전 노드에서 추가되었는지 확인하거나 
    # 정답 메시지 여부로 판단
    last_msg = state["messages"][-1].content
    if "정답입니다" in last_msg:
        return END
    return "explain"

# --- [그래프 조립] ---

def create_quiz_graph():
    # 1. 그래프 초기화 (상태 스키마 연결)
    workflow = StateGraph(QuizState)
    
    # 2. 노드 등록
    workflow.add_node("router", router)
    workflow.add_node("quiz_gen", quiz_gen)
    workflow.add_node("grade", grade)
    workflow.add_node("explain", explain)
    workflow.add_node("rag_search", rag_search)
    workflow.add_node("coach_analyze", coach_analyze)
    
    # 3. 엣지 연결
    workflow.add_edge(START, "router")
    
    # 조건부 라우팅
    workflow.add_conditional_edges(
        "router",
        route_by_intent,
        {
            "quiz_gen": "quiz_gen",
            "rag_search": "rag_search",
            "coach_analyze": "coach_analyze",
            "grade": "grade"
        }
    )
    
    # 퀴즈 플로우: 출제 후 일단 종료 (UI에서 답변을 받기 위함)
    # 실제 ReAct나 복잡한 loop 대신, Streamlit의 chat_input 루프와 맞추기 위해 
    # 퀴즈 출제 후 END로 가고, 사용자가 답변하면 다시 router가 작동하게 하거나
    # 특정 상태(current_quiz 존재 여부)를 router에서 먼저 체크하게 설계
    workflow.add_edge("quiz_gen", END)
    
    # 일반 QA 및 코칭은 응답 후 종료
    workflow.add_edge("rag_search", END)
    workflow.add_edge("coach_analyze", END)
    
    # 채점 및 해설 플로우
    # 사용자 답변이 들어왔을 때 router가 '채점'이 필요한 상황임을 인지하도록 
    # 아래 엣지는 router에서 분기되거나, 별도의 전처리 로직이 필요함.
    # 여기서는 router가 'answer check' 의도를 파악한다고 가정하거나 
    # 퀴즈 진행 중일 때 최우선으로 grade로 보내는 로직을 router에 추가할 수 있음.
    
    workflow.add_conditional_edges(
        "grade",
        route_after_grade,
        {
            "explain": "explain",
            "END": END
        }
    )
    workflow.add_edge("explain", END)
    
    return workflow.compile()

# 컴파일된 앱 인스턴스
quiz_app = create_quiz_graph()
