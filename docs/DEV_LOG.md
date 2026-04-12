# 🛠️ 개발 로그 및 트러블슈팅 (DEV_LOG)

이 문서는 LangChain Quiz Chatbot 개발 과정에서 발생하는 문제 해결 과정, 성능 최적화 실험(예: Chunking, 프롬프트 엔지니어링 등) 및 주요 아키텍처 결정 사항을 기록합니다.
포트폴리오 작성 시 **[문제 정의] - [해결 과정] - [결과]**를 증명하는 핵심 자료로 활용됩니다.

## 📝 기록 템플릿

새로운 이슈나 실험을 진행할 때 아래 포맷을 복사하여 최상단에 기록하세요.

```markdown
### [날짜] 제목 (예: PDF Chunking 사이즈 최적화 실험)
- **배경 및 문제 정의 (가설):** 
  (어떤 문제가 있었는지, 혹은 어떤 가설을 검증하고자 했는지 작성)
- **시도 및 해결책:**
  (구체적으로 어떤 코드를 바꾸거나 파라미터를 변경했는지 작성)
- **결과 및 채택 이유:**
  (실험 결과 어떻게 개선되었으며, 최종적으로 이 방식을 선택한 기술적 근거 작성)
```

---

## 🪵 로그 상세 내역

### 2026-04-12 | Streamlit 환경에서 Runtime instance already exists! 오류 해결
- **배경 및 문제 정의 (가설):** `uv run streamlit run main.py` 명령어로 앱을 직접 실행할 때 `RuntimeError: Runtime instance already exists!` 오류가 발생하여 실행이 중단됨. Streamlit CLI 도구(`streamlit run`)로 실행 중인데 `main.py` 파일 내부에서 `stcli.main()`을 또다시 호출하여 런타임 객체를 중복 생성하려 한 것이 원인임을 파악함.
- **시도 및 해결책:** `streamlit.runtime.exists()` 메서드를 가져와서 런타임 존재 여부를 먼저 확인하도록 로직을 수정함 (`if not runtime.exists():` 조건문 추가). 
- **결과 및 채택 이유:** Streamlit 명령어로 실행했을 때는 내부에서 다시 재실행을 방지하여 에러가 깔끔하게 해결됨. 추후 사용자가 단순히 `python main.py`(또는 `uv run python main.py`)명령어를 입력했을 때도 `streamlit` 커맨드로 전환해주는 편의성은 그대로 유지할 수 있음.

### 2026-04-12 | 최신 무료 LLM 모델(Gemini 2.5 Flash)로 일괄 마이그레이션
- **배경 및 문제 정의 (가설):** 기존 `gemini-2.0-flash` 모델이 Deprecated(감손) 상태임을 공식 문서(`gemini-ai-studio.md`)에서 확인. 비용 효율적이면서도 동일한 성능을 보장하는 무료 티어 모델로의 전환 필요성 대두.
- **시도 및 해결책:** 프로젝트 로직 전반(`main.py`의 `ChatGoogleGenerativeAI`, `create_agent`)과 프로젝트 가이드라인(`AGENTS.md`)을 최신 권장 무료 모델인 `gemini-2.5-flash`로 모두 업데이트함. 포트폴리오 가이드에도 명시.
- **결과 및 채택 이유:** 서비스 안정성 확보 및 API 지원 중단에 대비 완료. 비용 발생 없이 지속적인 테스트와 RAG 고도화 작업을 이어나갈 수 있는 기반을 다짐.
