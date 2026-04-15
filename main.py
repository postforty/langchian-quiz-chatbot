import re
import streamlit as st
import tempfile
import os
from langchain_core.messages import HumanMessage, AIMessage

# --- [내부 모듈 임포트] ---
from src.config import PAGE_TITLE, PAGE_ICON, validate_env
from src.ingestion import load_and_split_pdf
from src.vectorstore import get_vectorstore, save_vectorstore
from src.graph import quiz_app

# 1. 환경 변수 검증 (API 키 등)
validate_env()

# 2. 페이지 설정
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON)
st.title(f"{PAGE_ICON} {PAGE_TITLE}")

# 3. 세션 상태 초기화 함수
def init_session_state():
    defaults = {
        "messages": [],
        "pdf_processed": False,
        "vectorstore": get_vectorstore(),
        "graph_state": {
            "messages": [],
            "intent": "",
            "current_quiz": None,
            "quiz_history": [],
            "wrong_answers": [],
            "total_correct": 0,
            "total_attempted": 0,
            "retrieved_docs": []
        }
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# 4. 사이드바 - 상태 및 학습 지원
with st.sidebar:
    st.header("📊 학습 현황")
    gs = st.session_state.graph_state
    if gs["total_attempted"] > 0:
        acc = (gs["total_correct"] / gs["total_attempted"]) * 100
        st.metric("정답률", f"{acc:.1f}%")
        st.write(f"✅ 정답: {gs['total_correct']} / ❌ 오답: {len(gs['wrong_answers'])}")
    else:
        st.info("퀴즈를 풀면 통계가 표시됩니다.")
        
    if st.button("학습 데이터 초기화"):
        st.session_state.graph_state["wrong_answers"] = []
        st.session_state.graph_state["total_correct"] = 0
        st.session_state.graph_state["total_attempted"] = 0
        st.rerun()

# 5. PDF 업로드 및 처리
if not st.session_state.pdf_processed:
    uploaded_file = st.file_uploader("학습할 PDF 파일을 업로드하세요", type="pdf")
    if uploaded_file and st.button("학습 시작"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        
        try:
            with st.spinner("문서 분석 중..."):
                docs, full_context = load_and_split_pdf(tmp_path)
                if docs:
                    vstore = save_vectorstore(docs)
                    st.session_state.vectorstore = vstore
                    st.session_state.pdf_processed = True
                    st.success("✅ 문서 분석 완료! 이제 대화를 시작할 수 있습니다.")
                    st.rerun()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

# 6. 채팅 인터페이스
# 기존 메시지 출력
for msg in st.session_state.messages:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.write(msg.content)

# 사용자 입력 처리
if prompt := st.chat_input("메시지를 입력하세요 (퀴즈 풀기, 질문하기, 학습 분석 등)"):
    if not st.session_state.pdf_processed:
        st.warning("먼저 PDF 문서를 업로드해 주세요.")
        st.stop()

    # 1) 사용자 메시지 추가
    user_msg = HumanMessage(content=prompt)
    st.session_state.messages.append(user_msg)
    with st.chat_message("user"):
        st.write(prompt)

    # 2) Graph 실행을 위한 상태 준비 (메시지 동기화)
    current_state = st.session_state.graph_state
    current_state["messages"] = st.session_state.messages

    # 3) StateGraph 실행 — router가 의도를 판단하여 적절한 노드로 라우팅
    with st.chat_message("assistant"):
        with st.spinner("생각 중..."):
            result = quiz_app.invoke(current_state)

            # 결과 상태 저장 및 UI 업데이트
            st.session_state.graph_state = result
            st.session_state.messages = result["messages"]

            # 마지막 AI 응답 출력
            last_ai_msg = [m for m in result["messages"] if isinstance(m, AIMessage)][-1]
            st.write(last_ai_msg.content)

            st.rerun()
