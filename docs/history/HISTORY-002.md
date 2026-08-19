# HISTORY-002

## 기간

- 2026-08-20

## 완료 Epic

- EPIC-005 — Ollama 연동 및 News Selector Agent
- EPIC-006 — Summary + Security Analyst Agent
- EPIC-007 — Quiz Agent
- EPIC-008 — Quiz 풀이/채점 및 REST API
- EPIC-009 — 뉴스 조회 REST API

## 주요 구현 내용

- Ollama 기반 `LLMProvider` 추상화와 HTTP 오류, Timeout, 응답 검증 구조를 구현했다.
- Local LLM은 Selector `phi4-mini`, Summary `gemma3:4b`, Analyst `qwen3.5:9b`, Quiz `llama3.2:3b`로 구성하고 모델명과 Ollama 접속 정보는 환경변수로 관리했다.
- Selector가 전날 수집 기사 중 학습 가치가 높은 기사를 최대 3개 선정하고 `daily_selections`에 저장하도록 구현했다.
- 선정 기사에 대해 Summary와 Security Analyst 결과를 생성하고 기사별 상태와 결과를 `ai_analyses`에 저장하도록 구현했다.
- 분석 결과를 기반으로 단답형 Quiz를 최대 3개 생성하고 `quizzes`에 저장하도록 구현했다.
- Daily Pipeline을 `COLLECT → SELECT → SUMMARY → ANALYZE → QUIZ` 순서로 완성하고, 완료된 단계와 결과를 재사용하는 재실행 정책을 적용했다.
- LLM을 사용하지 않는 단답형 채점, `quiz_attempts` 저장, Quiz 조회·답안 제출 REST API를 구현했다.
- 선정 뉴스와 AI 분석을 결합한 Morning Briefing, 날짜별 뉴스, 데이터 존재 날짜 REST API를 구현했다.

## 주요 변경 파일

- `backend/src/security_daily/agents/`
- `backend/src/security_daily/infrastructure/llm/`
- `backend/src/security_daily/application/`
- `backend/src/security_daily/domain/`
- `backend/src/security_daily/infrastructure/database/`
- `backend/src/security_daily/api/`
- `backend/src/security_daily/jobs/daily.py`
- `backend/alembic/versions/0003_add_daily_selections.py`
- `backend/alembic/versions/0004_add_ai_analyses.py`
- `backend/alembic/versions/0005_add_quizzes.py`
- `backend/alembic/versions/0006_add_quiz_attempts.py`
- `backend/tests/`
- `.env.example`
- `docs/ARCHITECTURE.md`

## Architecture 변경

- Agent와 Ollama 구현체를 `LLMProvider` 경계로 분리하고 Structured Output을 Backend Schema로 검증하도록 했다.
- `daily_selections`, `ai_analyses`, `quizzes`, `quiz_attempts` 저장 구조를 실제 구현했다.
- Pipeline 상태 관리 범위를 `COLLECT`, `SELECT`, `SUMMARY`, `ANALYZE`, `QUIZ`로 확장했다.
- Morning Briefing과 오늘의 Quiz는 `Asia/Seoul` 기준 현재 날짜의 전날 데이터를 조회하도록 확정했다.
- 선정되지 않은 수집 기사는 사용자 뉴스 API에 노출하지 않고, 분석 미완료 기사는 분석 필드를 `null`로 반환하도록 했다.

## 주요 문제와 해결

- Ollama가 Quiz의 상세 Pydantic JSON Schema를 grammar로 변환하지 못해 HTTP 400이 발생했다. Ollama에는 호환 가능한 경량 Transport Schema를 전달하고, 응답 수신 후 엄격한 Backend Schema로 다시 검증하도록 분리해 해결했다.
- LLM 출력은 존재하는 기사 ID, 개수 제한, 중복, 필수 필드와 값 범위를 저장 전에 검증하고, 잘못된 출력은 DB에 저장하지 않도록 했다.
- 단계 실패 후 전체 Pipeline을 반복하지 않도록 성공 결과와 단계 상태를 확인해 필요한 단계부터 재실행하는 구조를 적용했다.
- Quiz 채점은 의미를 임의 추론하지 않고 공백 및 영문 대소문자만 정규화하여 대표 정답과 허용 정답을 비교하도록 했다.

## 테스트 결과

- Selector, Summary, Analyst, Quiz Agent는 Fake/Stub Provider 기반 Unit Test와 실제 Ollama Smoke Test를 분리했다.
- 실제 `2026-08-18` 분석 결과로 Quiz 3개 생성, Structured Output 검증과 PostgreSQL 저장을 확인했다.
- PostgreSQL Repository와 FK, UNIQUE, JSONB, Pipeline 상태, Quiz 풀이 기록 및 뉴스 관계 조회를 Integration Test로 검증했다.
- Quiz 및 뉴스 REST API의 응답 Schema, 정답 비노출, 날짜 정책, 빈 데이터와 입력 오류 처리를 검증했다.
- 최종 Backend 전체 테스트: `99 passed, 5 skipped` — 외부 사이트/Ollama Smoke Test는 기본 실행에서 제외된다.
- 최종 PostgreSQL Integration Test: `13 passed`
- Alembic: `0006_add_quiz_attempts (head)` 적용 및 `alembic check`에서 Schema 차이 없음을 확인했다.

## 현재 상태

- 전날 기사 수집부터 선정, 요약, 보안 분석, Quiz 생성까지 Daily Pipeline이 연결되어 있다.
- Local LLM 4개 역할의 실행 및 결과 검증·저장 구조가 준비되어 있다.
- Frontend가 사용할 뉴스 조회, Quiz 조회와 답안 제출 API가 구현되어 있다.
- Quiz 풀이 기록은 PostgreSQL에 저장되며 채점에는 LLM을 사용하지 않는다.

## 다음 작업

- Frontend에서 Morning Briefing, 날짜별 뉴스와 Quiz API 연결
- Windows Task Scheduler 등록 또는 향후 Docker 기반 실행 환경 구성
