from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from src.core.state import AgentState
from src.utils.guardrails_wrapper import input_guardrail_node, output_guardrail_node, guardrail_router
from src.agents.supervisor import supervisor_node
from src.agents.quiz_agent import quiz_agent_node
from src.agents.tutor_agent import tutor_agent_node
from src.utils.tools import search_pdf_documents

def tutor_router(state: AgentState):
    """Tutor 노드에서 도구 호출 여부에 따라 다음 경로를 결정합니다."""
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "output_guardrail"

def build_graph():
    """멀티 에이전트 시스템을 위한 LangGraph 워크플로우를 구성합니다."""
    workflow = StateGraph(AgentState)
    
    # 1. 노드 추가
    workflow.add_node("input_guardrail", input_guardrail_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("quiz", quiz_agent_node)
    workflow.add_node("tutor", tutor_agent_node)
    workflow.add_node("output_guardrail", output_guardrail_node)
    
    # 도구 실행 노드 (TutorAgent와 연동)
    tool_node = ToolNode([search_pdf_documents])
    workflow.add_node("tools", tool_node)
    
    # 2. 에지 연결
    # 진입점: 입력 가드레일 검사
    workflow.set_entry_point("input_guardrail")
    
    # L1-3 가드레일 결과에 따른 라우팅
    workflow.add_conditional_edges(
        "input_guardrail",
        guardrail_router,
        {
            "supervisor": "supervisor",
            "END": END
        }
    )
    
    # Supervisor의 의도 파악 결과에 따른 배분
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state.get("next_node", "tutor"),
        {
            "quiz": "quiz",
            "tutor": "tutor"
        }
    )
    
    # Quiz 결과 -> 출력 가드레일
    workflow.add_edge("quiz", "output_guardrail")
    
    # Tutor 결과 -> 도구 사용 시 tools로, 아닐 시 출력 가드레일로
    workflow.add_conditional_edges(
        "tutor",
        tutor_router,
        {
            "tools": "tools",
            "output_guardrail": "output_guardrail"
        }
    )
    
    # 도구 실행 후 다시 Tutor로 복귀하여 답변 생성
    workflow.add_edge("tools", "tutor")
    
    # 출력 가드레일 후 종료
    workflow.add_edge("output_guardrail", END)
    
    return workflow.compile()
