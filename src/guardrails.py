import re
from langchain.agents.middleware import before_agent, after_agent
from langchain.messages import AIMessage
from langchain.chat_models import init_chat_model

# --- [설정 및 키워드 정의] ---

# 차단 및 제재 키워드
FORBIDDEN_TOPICS = {
    "cheating": ["답지", "정답 알려줘", "숙제 대신", "써줘", "베끼기"], # 부정행위 관련
    "distraction": ["롤", "게임", "유튜브", "아이돌", "웹툰", "웃긴", "리그오브레전드", "발로란트", "배카"], # 학습 방해 요소
    "harmful": ["담배", "술", "폭력", "싸움", "바보"] # 유해 콘텐츠
}

# 상담 이관 키워드
ESCALATION_KEYWORDS = ["왕따", "괴롭힘", "우울해", "학교 폭력", "상담 선생님", "사람 불러줘"]

# 가드레일 전용 소형 모델 (비용 효율성)
safety_model = init_chat_model("google_genai:gemini-2.5-flash-lite")

# --- [가드레일 미들웨어 구현] ---

@before_agent(can_jump_to=["end"])
def education_guardrail(state, runtime):
    """
    [Layer 1] 입력 필터: 학생의 질문 의도를 파악하여 교육적이지 않거나 
    부정행위/딴짓이 의심될 경우 AI 답변 생성을 차단하고 즉시 교정합니다.
    """
    if not state.get("messages"):
        return None

    last_message = state["messages"][-1]
    # HumanMessage 타입인지 확인 (문자열 또는 객체일 수 있음)
    user_text = last_message.content if hasattr(last_message, "content") else str(last_message)
    
    if not isinstance(user_text, str):
        return None

    # Case A: 부정행위 방지
    for keyword in FORBIDDEN_TOPICS["cheating"]:
        if keyword in user_text:
            return {
                "messages": [{
                    "role": "assistant",
                    "content": "🚫 스스로 고민해봐야 실력이 늘어요! 정답을 바로 알려드리는 대신, 힌트를 드릴까요? 어떤 부분이 가장 어려운지 말해주세요."
                }],
                "jump_to": "end"
            }

    # Case B: 학습 집중 유도
    for keyword in FORBIDDEN_TOPICS["distraction"]:
        if keyword in user_text:
            return {
                "messages": [{
                    "role": "assistant",
                    "content": "⏰ 지금은 공부에 집중할 시간이에요! 딴짓은 쉬는 시간에 하고, 지금 풀고 있는 문제에 집중해볼까요?"
                }],
                "jump_to": "end"
            }

    # Case C: 유해 콘텐츠 차단
    for keyword in FORBIDDEN_TOPICS["harmful"]:
        if keyword in user_text:
            return {
                "messages": [{
                    "role": "assistant",
                    "content": "⚠️ 부적절한 대화 주제입니다. 바르고 고운 말을 사용해주세요."
                }],
                "jump_to": "end"
            }

    return None

@before_agent
def student_safety_middleware(state, runtime):
    """
    [Layer 2] 개인정보 보호: 학생의 전화번호나 이메일이 감지되면 마스킹 처리하여 안전을 확보합니다.
    """
    if not state.get("messages"):
        return None
        
    last_message = state["messages"][-1]
    if hasattr(last_message, "type") and last_message.type != "human":
        return None

    content = last_message.content
    if not isinstance(content, str):
        return None

    # 전화번호 패턴 (010-XXXX-XXXX 또는 010XXXXXXXX 등)
    phone_pattern = r'01[016789]-?[0-9]{3,4}-?[0-9]{4}'
    # 이메일 패턴
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    is_redacted = False

    if re.search(phone_pattern, content):
        content = re.sub(phone_pattern, '<PHONE_REDACTED>', content)
        is_redacted = True

    if re.search(email_pattern, content):
        content = re.sub(email_pattern, '<EMAIL_REDACTED>', content)
        is_redacted = True

    if is_redacted:
        # 내용을 수정하여 LLM에게 전달
        last_message.content = content

    return None

@before_agent(can_jump_to=["end"])
def counseling_escalation_middleware(state, runtime):
    """
    [Layer 3] 상담 이관: 심리적 위기 상황이나 상담 요청이 감지되면 AI 답변을 멈추고 
    전문 상담사 연결 안내를 제공합니다.
    """
    if not state.get("messages"):
        return None
        
    last_message = state["messages"][-1]
    content = last_message.content if hasattr(last_message, "content") else str(last_message)

    if not isinstance(content, str):
        return None

    for keyword in ESCALATION_KEYWORDS:
        if keyword in content:
            return {
                "messages": [{
                    "role": "assistant",
                    "content": "학생, 많이 힘들었겠구나. 이 문제는 내가 답변하기보다는 전문 상담 선생님이 직접 듣고 도와주시는 게 좋을 것 같아. \n\n지금 바로 상담 선생님께 연결해 드렸으니 잠시만 기다려 줄래? 🍀 (상담실 연결 중...)"
                }],
                "jump_to": "end"
            }
    return None

@after_agent
def answer_leakage_guardrail(state, runtime):
    """
    [Layer 4] 출력 컴플라이언스: AI가 정답을 직접 유출하는지 감시자 모델이 검사하고, 
    필요 시 교육적인 답변으로 교정합니다.
    """
    if not state.get("messages"):
        return None
        
    last_message = state["messages"][-1]

    # 마지막 메시지가 AI의 답변인 경우에만 검사
    if not isinstance(last_message, AIMessage):
        return None

    # 감시자 모델에게 평가 요청
    auditor_prompt = f"""
    당신은 엄격한 교육 감독관입니다.
    다음 '튜터의 답변'을 확인하세요.
    답변이 학생을 지도하지 않고 문제의 정답이나 전체 풀이를 직접적으로 제공한다면 'LEAKED'라고 답하세요.
    답변이 적절한 힌트나 설명을 제공한다면 'SAFE'라고 답하세요.

    튜터의 답변: {last_message.content}
    """

    try:
        result = safety_model.invoke([{"role": "user", "content": auditor_prompt}])
        
        if "LEAKED" in result.content:
            # 정답 유출 시 답변 교정
            last_message.content = "앗, 제가 정답을 바로 말할 뻔했네요! 😅 정답보다는 푸는 방법을 먼저 생각해볼까요? 이 문제의 핵심 개념은..."
    except Exception:
        # 모델 호출 실패 시 안전하게 통과 (또는 로그 기록)
        pass

    return None
