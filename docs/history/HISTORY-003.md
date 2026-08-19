# HISTORY-003

## 기간

- 2026-08-20

## 완료 Epic

- EPIC-010 — Next.js Security Daily Dashboard
- EPIC-011 — Windows Task Scheduler 기반 Daily 자동 실행
- EPIC-012 — 프로젝트 마감 및 GitHub/CI 구성

## 주요 구현 내용

- Next.js 원페이지 Dashboard에 Morning Security Briefing, 날짜별 지난 뉴스와 단답형 Quiz UI를 구현했다.
- Server Component에서 뉴스·Quiz를 조회하고 Quiz 제출만 Client Component와 Server Action으로 분리했다.
- Dark Neutral 기반 반응형 UI와 Section별 Loading, Empty, Error 상태를 구현했다.
- PowerShell Daily Runner와 Task 등록 Script를 추가하고 매일 08:30 KST에 실행되는 `SecurityDaily-DailyPipeline` Task를 등록했다.
- 날짜별 실행 로그와 30일 보존 정책을 구성하고 Pipeline 종료 코드를 Scheduler에 그대로 전달하도록 했다.
- Root README와 외부 서비스 비의존 Backend/Frontend GitHub Actions CI를 추가했다.
- Public Repository Commit 전 ignore 규칙과 Secret을 점검하고 재현 가능한 설치·운영 절차를 문서화했다.

## 주요 변경 파일

- `frontend/src/app/`
- `frontend/src/components/`
- `frontend/src/lib/`
- `frontend/.env.example`
- `scripts/run_daily_pipeline.ps1`
- `scripts/register_daily_task.ps1`
- `.github/workflows/ci.yml`
- `README.md`
- `.gitignore`, `frontend/.gitignore`
- `docs/ARCHITECTURE.md`

## Architecture 변경

- Next.js Dashboard의 Server/Client Component 책임과 FastAPI 연결 방식을 실제 구현했다.
- Windows Task Scheduler가 FastAPI와 분리된 Daily Runner를 실행하도록 구성했다.
- Quiz는 선정 기사별 최대 1문제를 독립 생성하고 전체 최대 3개·중복 Validation을 적용하도록 안정화했다.
- Quiz Ollama 요청에 출력 token 상한을 적용했다.

## 주요 문제와 해결

- Frontend 실제 환경파일이 없어 Server Component의 Backend URL이 비어 있던 문제를 `frontend/.env.local` 구성으로 해결했다. 실제 환경파일은 Git에서 제외했다.
- PowerShell 5.1이 Python stderr Logging을 오류로 처리하던 문제를 실제 프로세스 종료 코드로 판단하도록 수정했다.
- 실제 다중 기사 Quiz 요청이 9천 token 이상 출력하며 Timeout 되던 문제를 확인했다. 기사 원문은 입력되지 않았으며, 기사별 독립 생성과 출력 제한으로 10.566초에 완료하도록 안정화했다.
- PowerShell `Tee-Object`의 로그 인코딩 혼합을 UTF-8 명시적 append 방식으로 해결했다.

## 테스트 결과

- 실제 `2026-08-18` 뉴스 3건, AI 분석, Quiz 3문제와 정답 제출 흐름을 확인했다.
- 실제 `2026-08-19` Quiz 2건 생성·저장과 동일 날짜 재실행 Skip을 확인했다.
- 최종 Backend 전체 테스트: `100 passed, 5 skipped`
- CI 대상 Backend 테스트: `87 passed, 18 deselected`
- Frontend ESLint, TypeScript와 Next.js Production Build 통과
- Alembic Schema drift 없음, uv lock과 Python compile 검증 통과
- Scheduler: `Ready`, `LastTaskResult=0`

## 현재 상태

- 수집부터 Quiz까지 Daily Pipeline과 뉴스·Quiz REST API, 반응형 Dashboard가 완성되어 있다.
- Windows Task Scheduler가 매일 08:30 KST에 Pipeline을 실행하도록 등록되어 있다.
- 설치·환경설정·운영·테스트 방법과 GitHub Actions CI가 준비되어 있다.

## 다음 작업

- 실제 운영 중 Local LLM 처리시간과 Daily 로그 관찰
- 필요 시 Home Server와 Docker Compose 환경으로 이전
