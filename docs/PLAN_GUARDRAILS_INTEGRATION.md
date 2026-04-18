# 구현 계획서: 교육용 다층 가드레일 시스템 도입

이 문서는 `01_guardrails.ipynb`에서 검증된 4단계 가드레일 기능을 `langchian-quiz-chatbot` 프로젝트에 통합하기 위한 상세 계획을 담고 있습니다.

## 1. 개요 (Overview)
- **목적**: 불필요한 대화 차단, 개인정보 보호, 유해 콘텐츠 필터링, 정답 유출 방지를 통해 안전하고 교육적인 AI 튜터 시스템 구축
- **핵심 목표**: `AGENTS.md` 지침에 따라 로직을 모듈화하고, 기존 Streamlit 앱에 안정적으로 통합

## 2. 아키텍처 설계 (Architecture Design)

### 2.1 파일 구조 변경
```
project_root/
├── src/
│   ├── guardrails.py       # (신규) 4단계 가드레일 미들웨어 로직
│   └── agent.py            # (추가 예정) 에이전트 생성 및 설정 로직
└── main.py                 # 기존 Streamlit UI 유지 및 신규 모듈 호출
```

### 2.2 가드레일 프로세스 워크플로우
1.  **Input Phase (Before Agent)**:
    -   `education_guardrail`: 부정행위/딴짓/유해어 필터링
    -   `privacy_guardrail`: PII(전화번호, 이메일) 마스킹
    -   `escalation_guardrail`: 위기 상황 감지 시 상담사 이관
2.  **Execution Phase**:
    -   LLM이 사용자 의도를 분석하고 답변 생성 또는 도구(PDF 검색) 사용
3.  **Output Phase (After Agent)**:
    -   `leakage_guardrail`: 답변 내 정답 유출 여부 검사 및 최종 교정

## 3. 구현 태스크 리스트 (Implementation Task List)

- [x] **Task 1: 가드레일 모듈 신설 (`src/guardrails.py`)**
    - [x] `01_guardrails.ipynb`의 코드를 기반으로 미들웨어 함수 4종 구현
    - [x] 금지 키워드 및 정규표현식(PII) 정의
    - [x] `safety_model` (Gemini 2.5 Flash Lite) 설정
- [x] **Task 2: 메인 앱 에이전트 초기화 수정**
    - [x] `main.py`에 `src.guardrails` 모듈 임포트
    - [x] `initialize_agent` 함수에 4단계 미들웨어 리스트 등록
- [x] **Task 3: Streamlit UI 메시지 핸들링 최적화**
    - [x] 가드레일에 의해 차단되거나 수정된 답변이 세션 상태에 올바르게 저장되는지 확인
    - [x] 상담사 이관 상황 발생 시 특수 알림 메시지 디자인/노출
- [x] **Task 4: 테스트 및 실험 기록**
    - [x] 각 레이어별 작동 테스트 (부정행위 시도, 개인정보 입력 등)
    - [x] `docs/DEV_LOG.md`에 테스트 결과 및 가설 검증 결과 기록

## 4. 향후 확장성
-   커스텀 키워드 추가 기능 (운영 대시보드 연동 고려)
-   다국어 지원 가드레일 확장

---
> [!IMPORTANT]
> 모든 코드는 `Python uv` 환경에서 실행 가능해야 하며, `gemini-2.5-flash-lite` 또는 `gemini-3.1-flash-lite-preview` 모델을 사용하여 비용 효율성을 극대화합니다.
