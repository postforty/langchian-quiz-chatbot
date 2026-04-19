from typing import Dict, Any, Literal
from src.core.state import AgentState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# 라우팅 및 의도 파악용 모델 (비용 효율적인 Flash-Lite 권장)
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

SYSTEM_PROMPT = """당신은 교육 서비스의 Supervisor입니다. 사용자의 대화 내용을 분석하여 적절한 에이전트를 선택하세요.

1. 'quiz': 사용자가 퀴즈를 풀고 싶어하거나, 퀴즈 정답(번호 등)을 제출하거나, 다음 문제를 요청하는 경우.
2. 'tutor': 사용자가 문서 내용에 대해 질문하거나, 설명을 요청하거나, 지식적인 답변을 원하는 경우.

사용자가 선택한 현재 모드: {mode}

응답은 반드시 'quiz' 또는 'tutor' 한 단어로만 하세요."""

def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """
    Supervisor 노드: 사용자 의도 및 현재 설정된 모드를 바탕으로 작업을 할당합니다.
    """
    last_message = state["messages"][-1]
    
    # 의도 파악 호출
    prompt = SYSTEM_PROMPT.format(mode=state.get("mode", "알 수 없음"))
    response = model.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=last_message.content)
    ])
    
    intent = response.content.strip().lower()
    
    # 안정성을 위해 fallback 처리
    if "quiz" in intent:
        next_node = "quiz"
    elif "tutor" in intent:
        next_node = "tutor"
    else:
        # 알 수 없는 경우 UI 모드를 따라감
        next_node = "quiz" if state.get("mode") == "퀴즈 풀기" else "tutor"
        
    return {"next_node": next_node}
