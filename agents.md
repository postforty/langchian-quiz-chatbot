# Agents Guidelines: LangChain Quiz Chatbot

이 문서는 새로운 대화 세션이 시작될 때 AI 어시스턴트가 프로젝트의 컨텍스트를 빠르게 파악하고 일관된 개발을 이어가기 위해 반드시 확인해야 할 사항을 정의합니다.

## 1. 프로젝트 핵심 정보 (Core Context)
- **목적**: PDF 문서를 분석하여 퀴즈 생성 및 RAG 기반 질의응답을 제공하는 Streamlit 웹 애플리케이션.
- **주요 파일**: `src/quiz_chatbot.py` (메인 로직 및 UI 공유)
- **핵심 기술 스택**:
  - **LLM/Framework**: LangChain, LangGraph, Google Gemini (`gemini-1.5-flash` 권장)
  - **Storage**: FAISS (로컬 인덱스: `faiss_index_pdf_quiz`)
  - **UI**: Streamlit
  - **Dependency**: `uv` (Package Manager)

## 2. 세션 시작 시 핵심 체크리스트 (Project Specifics)
1. **분석 엔진 상태**: `src/quiz_chatbot.py` 내의 `ChatGoogleGenerativeAI` 모델 설정(`model="gemini-..."`)이 유효한 버전인지 확인하세요.
2. **로직 구조**: 
   - 퀴즈 생성: `question_generator()`
   - 대화 에이전트: `initialize_agent()` 및 `search_pdf_documents` 도구
   - 상태 유지: `st.session_state`를 통한 메시지/벡터스토어 관리 흐름

## 3. 개발 원칙 (Development Principles)
- **UI/UX**: Streamlit의 `st.chat_message`와 `st.sidebar`를 활용한 직관적인 디자인을 유지하세요.
- **RAG 무결성**: 답변 생성 시 반드시 검색된 문서(`search_pdf_documents`)에 기반해야 하며, 정보가 없을 경우 솔직하게 답변하도록 가이드하세요.
- **모듈화**: 현재 `quiz_chatbot.py`에 집중된 로직을 기능별(예: `ingestion.py`, `quiz_gen.py`, `agent.py`)로 분리하는 리팩토링을 고려하세요.
- **커밋 컨벤션**: 모든 변경 사항은 `COMMIT_CONVENTION.md`에 정의된 규칙을 준수하여 기록하세요.

## 4. 참고 사항 (Notes)
- 프로젝트 루트의 `analysis_results.md` 아티팩트에 상세 분석 내용이 기록되어 있습니다.
- **포트폴리오 가이드**: `PORTFOLIO_CHECKLIST.md`에 정의된 지침 및 체크리스트를 준수하여 개발을 진행하세요.
- 새로운 기능을 추가하기 전 항상 `src/quiz_chatbot.py`의 현재 상태를 `view_file`로 먼저 확인하세요.
