from typing import Dict, Any, List
from src.core.state import AgentState
from src.guardrails import (
    education_guardrail,
    student_safety_middleware,
    counseling_escalation_middleware,
    answer_leakage_guardrail
)
from langchain_core.messages import AIMessage, BaseMessage

def input_guardrail_node(state: AgentState) -> Dict[str, Any]:
    """
    단일 노드에서 Layer 1, 2, 3 가드레일을 통합 실행합니다.
    """
    # [Layer 2] 개인정보 보호 (메시지 내용 수정 반영)
    # student_safety_middleware는 내부적으로 last_message.content를 수정하므로 
    # 원본 메시지를 복사하거나 수정된 내용을 새 메시지로 반환하는 처리가 필요함
    student_safety_middleware.before_agent(state, None)
    
    # [Layer 1] 교육 가드레일 (부정행위 및 딴짓 차단)
    edu_res = education_guardrail.before_agent(state, None)
    if edu_res and edu_res.get("jump_to") == "end":
        return {
            "messages": edu_res["messages"], 
            "next_node": "END"
        }
        
    # [Layer 3] 상담 이관
    escalation_res = counseling_escalation_middleware.before_agent(state, None)
    if escalation_res and escalation_res.get("jump_to") == "end":
        return {
            "messages": escalation_res["messages"], 
            "next_node": "END"
        }
        
    # 모든 검사를 통과한 경우
    return {"next_node": "supervisor"}

def output_guardrail_node(state: AgentState) -> Dict[str, Any]:
    """
    AI 답변이 생성된 후 Layer 4(정답 유출) 가드레일을 실행합니다.
    """
    # [Layer 4] 정답 유출 방지
    # answer_leakage_guardrail은 마지막 AI 메시지를 검사하고 내용을 직접 수정함
    answer_leakage_guardrail.after_agent(state, None)
    
    # 수정이 발생했을 수 있으므로 마지막 메시지를 포함하여 반환
    # (LangGraph add_messages에 의해 마지막 메시지가 업데이트되거나 유지됨)
    return {"messages": [state["messages"][-1]]}

def guardrail_router(state: AgentState) -> str:
    """
    가드레일 결과에 따라 다음 흐름을 결정합니다.
    """
    if state.get("next_node") == "END":
        return "END"
    return state.get("next_node", "supervisor")
