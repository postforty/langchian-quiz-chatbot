# Commit Convention: LangChain Quiz Chatbot

이 문서는 프로젝트의 일관된 커밋 메시지 작성을 위한 규칙을 정의합니다. 모든 커밋은 아래의 컨벤션을 준수해야 합니다.

## 1. 메시지 구조

커밋 메시지는 다음과 같은 구조로 작성합니다:

```text
<type>(<scope>): <subject>

<body>

<footer>
```

- **Type**: 필수 항목. 커밋의 성격을 설명합니다.
- **Scope**: 선택 항목. 변경이 발생한 위치(예: `ui`, `rag`, `deps` 등)를 나타냅니다.
- **Subject**: 필수 항목. 변경 사항에 대한 간결한 요약 (현재형, 명령문 사용).
- **Body**: 선택 항목. 변경 동기 및 상세 내용을 작성합니다.
- **Footer**: 선택 항목. 이슈 트래킹 코드나 Breaking Changes를 기입합니다.

## 2. Type 가이드 (간소화)

1인 개발 환경에 최적화하여 필수적인 타입으로 압축하였습니다.

| Type | 설명 |
| :--- | :--- |
| **feat** | 새로운 기능 추가 |
| **fix** | 버그 수정 |
| **docs** | 문서 수정 (README, 가이드 등) |
| **refactor** | 기능 변경 없는 코드 구조 개선 (포맷팅, 성능 개선 포함) |
| **chore** | 기타 변경 사항 (의존성 관리, 빌드 설정, 파일 삭제/이동 등) |

## 3. 권장 지침 (Best Practices)

- 제목(Subject)은 **50자 이내**로 작성하며, 마침표를 찍지 않습니다.
- 제목의 첫 글자는 대문자로 시작하지 않고, **명령어 형태**로 작성합니다. (예: `add feature` O, `Added feature` X)
- 본문(Body)은 한 줄당 **72자 이내**로 작성하며, '무엇을', '왜' 변경했는지를 상세히 설명합니다.
- 커밋 메시지는 **한국어** 작성을 권장하며, 변경 사항을 명확하고 가이드에 따라 작성합니다.

## 4. 예시

```text
feat(ui): add quiz generator sidebar option

- PDF 분석 후 퀴즈 생성을 위한 사이드바 UI 추가
- 생성 개수 설정 슬라이더 구현
```

```text
fix(rag): resolve document retrieval overlap issue

- FAISS 검색 결과에서 중복된 문서가 반환되는 로직 수정
```
