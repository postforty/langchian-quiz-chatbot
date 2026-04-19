import streamlit as st
import tempfile
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 내부 모듈 임포트
from src.utils.ingestion import load_and_parse_pdf, get_vectorstore
from src.workflow.graph_builder import build_graph
from langchain_core.messages import HumanMessage, AIMessage

# --- [초기 설정] ---

# 그래프 컴파일 (세션 내 1회 실행)
if "graph" not in st.session_state:
    st.session_state.graph = build_graph()

# 세션 상태 초기화 (UI 및 상태 유지용)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_context" not in st.session_state:
    st.session_state.pdf_context = ""
if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "wrong_answers" not in st.session_state:
    st.session_state.wrong_answers = []
if "mode" not in st.session_state:
    st.session_state.mode = "퀴즈 풀기"

# --- [비즈니스 로직 연동] ---

def process_chat(user_input: str):
    """LangGraph를 통해 사용자 입력을 처리하고 상태를 동기화합니다."""
    
    # 1. 입력 메시지 구성
    new_message = HumanMessage(content=user_input)
    
    # 2. 그래프 실행을 위한 초기 상태 구성
    # LangGraph의 Annotated[List, add_messages]를 고려하여 현재 메시지만 넘기거나 전체를 넘길 수 있음
    # 여기서는 상태 유지를 위해 전체 히스토리를 전달하되, 새 메시지를 추가함
    inputs = {
        "messages": st.session_state.messages + [new_message],
        "mode": st.session_state.mode,
        "pdf_context": st.session_state.pdf_context,
        "current_question": st.session_state.current_question,
        "wrong_answers": st.session_state.wrong_answers,
        "pdf_processed": st.session_state.pdf_processed
    }
    
    # 3. 그래프 실행
    with st.spinner("생각 중..."):
        result = st.session_state.graph.invoke(inputs)
    
    # 4. 결과 반영 (Session State 동기화)
    st.session_state.messages = result["messages"]
    st.session_state.current_question = result.get("current_question")
    st.session_state.wrong_answers = result.get("wrong_answers", [])
    
    return result["messages"][-1].content

# --- Streamlit UI 시작 ---
st.set_page_config(page_title="PDF AI 멀티 에이전트 챗봇", page_icon="🤖")
st.title("🤖 PDF AI 멀티 에이전트 챗봇")

# 사이드바 설정 영역
with st.sidebar:
    st.header("⚙️ 설정")
    st.session_state.mode = st.radio(
        "학습 모드 선택",
        ["퀴즈 풀기", "질문하기"],
        help="Supervisor가 의도를 파악할 때 참고합니다."
    )
    
    if st.session_state.wrong_answers:
        st.write("---")
        st.write(f"❌ 틀린 문제: {len(st.session_state.wrong_answers)}개")
        if st.button("오답 노트 초기화"):
            st.session_state.wrong_answers = []
            st.rerun()

uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")

# PDF 처리 로직
if uploaded_file and not st.session_state.pdf_processed:
    if st.button("학습 시작"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name
        
        with st.spinner("문서를 분석 중... (멀티 에이전트 가동 준비)"):
            vectorstore, full_text = load_and_parse_pdf(tmp_path)
            st.session_state.pdf_context = full_text
            st.session_state.pdf_processed = True
            
            # 초기 환영 메시지 또는 첫 문제 생성
            initial_prompt = "안녕! 퀴즈를 시작해줘." if st.session_state.mode == "퀴즈 풀기" else "문서 분석이 완료되었습니다. 무엇이든 물어보세요!"
            process_chat(initial_prompt)
            
        os.unlink(tmp_path)
        st.rerun()

# 문장 분석 완료 상태 표시
if st.session_state.pdf_processed:
    st.success("✅ 문서 분석 및 에이전트 배치 완료!")

# 대화 내용 출력 (LangGraph 메시지 객체 처리)
for msg in st.session_state.messages:
    # HumanMessage, AIMessage, ToolMessage 등을 구분하여 출력
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.write(msg.content)
    elif isinstance(msg, AIMessage):
        if msg.content: # 내용이 있는 경우에만 출력 (ToolCall만 있는 경우는 제외)
            with st.chat_message("assistant"):
                # 가드레일 특수 메시지 시각화
                if "(상담실 연결 중...)" in msg.content:
                    st.warning(msg.content)
                elif msg.content.startswith("🚫") or msg.content.startswith("⚠️"):
                    st.error(msg.content)
                elif msg.content.startswith("⏰"):
                    st.info(msg.content)
                else:
                    st.write(msg.content)

# 사용자 입력 처리
if prompt := st.chat_input("메세지를 입력하세요"):
    if not st.session_state.pdf_processed:
        st.warning("먼저 PDF 파일을 업로드하고 '학습 시작'을 눌러주세요.")
        st.stop()

    # 채팅 프로세스 실행
    process_chat(prompt)
    st.rerun()

if __name__ == "__main__":
    import sys
    from streamlit.web import cli as stcli
    import streamlit.runtime as runtime
    
    if not runtime.exists():
        sys.argv = ["streamlit", "run", "main.py"]
        sys.exit(stcli.main())
