# Security Daily - AGENTS.md

## 1. 문서 목적

이 문서는 프로젝트에서 AI Coding Agent가 작업할 때 반드시 따라야 하는 공통 작업 규칙을 정의한다.

세부 구현 방식은 `PROJECT.md`, `ARCHITECTURE.md`, 현재 코드와 테스트를 기준으로 판단한다.

---

# 2. 작업 전 필수 확인

모든 작업 전에 다음 문서를 우선 확인한다.

```text
docs/PROJECT.md
docs/ARCHITECTURE.md
AGENTS.md
```

문서 역할:

```text
PROJECT.md
→ 무엇을 만들고 왜 만드는가

ARCHITECTURE.md
→ 시스템을 어떻게 구현하는가

AGENTS.md
→ AI가 어떤 방식으로 작업하는가
```

현재 작업 요청이 `PROJECT.md` 또는 `ARCHITECTURE.md`와 충돌하면 임의로 구현하지 말고 먼저 보고한다.

---

# 3. 기본 작업 원칙

- `PROJECT.md`와 `ARCHITECTURE.md`를 작업 전에 반드시 확인한다.
- 기본 개발 단위는 **Epic**으로 한다.
- 서로 연관되어 함께 구현하는 것이 효율적인 여러 Task를 하나의 Epic으로 묶는다.
- Epic 내부에서는 어떤 Task를 수행하는지 명확하게 구분한다.
- 사용자가 특정 Task만 요청한 경우에는 해당 Task만 수행한다.
- 요청 범위를 넘어선 기능 추가나 리팩터링을 하지 않는다.
- 기존 Architecture와 충돌하는 변경이 필요한 경우 임의로 변경하지 말고 먼저 보고한다.
- 새로운 Dependency를 추가하면 사용 목적과 이유를 보고한다.
- 테스트 없이 작업을 완료 처리하지 않는다.
- 주요 로직과 초보자가 이해하기 어려운 부분에는 한국어 주석을 작성한다.
- 현재 개발 환경은 Windows를 기준으로 한다.
- 향후 Docker 기반 환경으로 이전할 수 있는 구조를 유지한다.
- Git/GitHub 기반 버전 관리와 향후 CI/CD 적용 가능성을 항상 고려한다.
- 과도한 추상화보다 읽고 이해하기 쉬운 구현을 우선한다.

---

# 4. Epic과 Task

기본 작업 구조는 다음과 같다.

```text
Epic
├── Task 1
├── Task 2
├── Task 3
└── Task 4
```

Epic은 서로 연관되어 한 흐름으로 구현할 수 있는 작업들을 묶는다.

예:

```text
EPIC — Backend 초기 개발환경 구축

Task 1
Python 프로젝트 초기화

Task 2
FastAPI 설치 및 기본 실행

Task 3
환경변수 설정 구조 구성

Task 4
pytest 기본 환경 구성
```

Epic 작업을 수행하더라도 내부 Task별 작업 내용과 완료 여부를 구분할 수 있어야 한다.

단일 Task 수행은 다음 경우 사용한다.

- 사용자가 특정 Task만 명시적으로 요청한 경우
- 오류 수정
- 작은 기능 변경
- 독립적인 리팩터링
- 특정 테스트 추가

---

# 5. 완료 기준

Epic 또는 Task는 다음 조건을 만족해야 완료로 간주한다.

```text
[ ] 요구사항 구현
[ ] 요청 범위 밖 변경 없음
[ ] 필요한 테스트 작성 또는 기존 테스트 확인
[ ] 관련 테스트 통과
[ ] 불필요한 Dependency 추가 없음
[ ] Architecture 위반 없음
[ ] 필요한 한국어 주석 작성
```

Epic 단위 작업에서는 포함된 각 Task의 완료 여부도 확인한다.

---

# 6. 작업 완료 보고

작업 완료 후 다음 형식으로 보고한다.

```text
## 완료 내용

Epic:
- 완료한 Epic

Tasks:
- Task 1
- Task 2
- Task 3

변경 파일:
- 생성/수정한 주요 파일

## 테스트

실행 명령:
결과:

## Architecture 영향

- 없음

또는

- 변경 또는 검토가 필요한 내용

## 추가 Dependency

- 없음

또는

- Dependency와 추가 이유

## 다음 작업

- 다음으로 진행하기 적절한 작업
```

단일 Task 작업이라면 Epic 항목은 생략할 수 있다.

---

# 7. 실패 보고

작업 중 문제가 발생하면 숨기거나 임의로 우회하지 않는다.

다음 형식으로 보고한다.

```text
문제:

원인:

현재 확인한 내용:

가능한 해결책:

추천 해결책:
```

테스트 실패를 무시하고 완료 처리하지 않는다.

---

# 8. Git 원칙

논리적으로 구분되는 변경 단위를 유지한다.

Commit Message는 변경 내용을 명확하게 표현한다.

예:

```text
feat: add article domain model

test: add article validation tests

fix: prevent duplicate article urls
```

사용자의 명시적인 요청 없이 Git History를 파괴하는 작업을 수행하지 않는다.

금지 예:

```text
git reset --hard

git push --force
```

GitHub Actions 등 향후 CI/CD를 적용하기 어렵게 만드는 구조를 피한다.

---

# 9. 환경설정 원칙

환경에 따라 달라지는 값은 코드에 하드코딩하지 않는다.

예:

```text
Database URL
Ollama URL
Model Name
Port
Password
Timezone
```

환경변수를 사용한다.

실제 Secret은 Repository에 저장하지 않는다.

---

# 10. Windows → Docker 이전 원칙

현재 개발 환경은 Windows지만 향후 Docker 기반 Home Server로 이전할 예정이다.

따라서 다음과 같은 구현을 피한다.

- Windows 전용 절대경로 하드코딩
- 특정 PC Username에 종속된 경로
- Localhost 주소를 비즈니스 코드에 직접 삽입
- Process 내부에 영속 데이터를 저장하는 구조

환경에 따라 달라지는 값은 Configuration을 통해 관리한다.

---

# 11. 보안 원칙

다음 기본 보안 원칙을 유지한다.

- Secret 하드코딩 금지
- SQL 문자열 직접 조합 금지
- 사용자 입력 검증
- 외부 HTTP 요청 Timeout 설정
- 외부 데이터 무조건 신뢰 금지
- LLM 출력 무조건 신뢰 금지
- Error Message에 Secret 노출 금지

보안상 중대한 문제가 발견되면 임의로 무시하지 말고 보고한다.

---

# 12. 문서 관리

프로젝트 문서는 다음 역할로 분리한다.

```text
PROJECT.md
→ 프로젝트 목적과 요구사항

ARCHITECTURE.md
→ 구현 구조와 Architecture Decision

AGENTS.md
→ AI Coding Agent 작업 규칙

HISTORY-xxx.md
→ 개발 진행 기록
```

같은 내용을 여러 문서에 반복해서 기록하지 않는다.

---

# 13. History 관리

History는 Task마다 작성하지 않는다.

**2~3개의 Epic이 완료되었을 때 하나의 History 문서로 묶어 기록한다.**

예:

```text
docs/history/HISTORY-001.md
docs/history/HISTORY-002.md
```

History에는 필요한 핵심 내용만 기록한다.

```text
기간:

완료 Epic:
- EPIC 1
- EPIC 2
- EPIC 3

주요 구현 내용:

주요 변경 파일:

Architecture 변경:

주요 문제와 해결:

테스트 결과:

현재 상태:

다음 작업:
```

History 작성 자체가 개발보다 큰 작업이 되지 않도록 간결하게 유지한다.

---

# 14. 금지 사항

AI는 다음 행동을 하지 않는다.

- 요청 범위 밖 기능 추가
- Architecture 임의 변경
- 테스트 실패 무시
- 불필요한 대규모 리팩터링
- 사용자 동의 없는 Dependency 대량 추가
- Secret 코드 삽입
- 이해하기 어려운 과도한 추상화
- 사용하지 않는 코드 미리 생성
- 필요성이 확인되지 않은 기능 선행 구현
- 기존 동작을 확인하지 않고 코드 전체 재작성

---

# 15. 판단 우선순위

작업 중 판단이 필요한 경우 다음 순서를 따른다.

```text
1. 현재 사용자 요청
2. PROJECT.md
3. ARCHITECTURE.md
4. AGENTS.md
5. 기존 코드와 테스트
6. 일반적인 Best Practice
```

상위 기준과 하위 기준이 충돌하면 상위 기준을 우선한다.

단, 보안상 중대한 문제가 있거나 데이터 손실 위험이 있는 경우 작업을 중단하고 사용자에게 보고한다.