---
description: raw 자료를 wiki에 정제 박제 (LLM Wiki Operations: Ingest)
---

raw 자료를 LLM Wiki 패턴으로 정제하여 wiki에 박제한다.

# 위키 루트
/Users/kakao/Documents/2. 개인/Walter Project/03_위키/Walter_위키/Walter의 상상은 현실이 된다/

# 입력
$ARGUMENTS  (raw 파일 경로 또는 raw 자료 내용)
- 상대 경로 입력 시 위키 루트 기준으로 해석
- 절대 경로도 허용

# 절차
1. **읽기**: raw 자료 + 위키 루트/CLAUDE.md + 위키 루트/raw-wiki-규칙.md
2. **진입 판정** (규칙 §A): 통과 / 참조 / 모호 / 반려
3. **영역 분류** (규칙 §B, 통과·참조 시): 5분기 결정 트리
4. **압축** (규칙 §C): 10~20% 압축률, ≤200줄, 직접 인용 ≤3줄, cross-link ≥3개
5. **frontmatter** 의무: `area`, `created`, `sources`, `tags`
6. **노트 생성**: 위키 루트/{해당 영역 폴더}에 저장
7. **index 갱신**: 위키 루트/index.md 해당 영역에 1줄 추가
8. **log append**: 위키 루트/log.md에 `## [YYYY-MM-DD] ingest | {제목}`

# 모호 처리
[모호] 시 규칙 §D 따름:
- 후보 자료 1~3문장 발췌 + 분기 옵션 2개를 사용자에게 제시
- 사용자 선택 → 규칙 "모호 사례 로그"에 append

# 제약
- raw/ 절대 수정 X
- frontmatter 누락 금지
- 인용 없는 주장 금지
- 결정 트리 임의 분기 추가 금지

# 출력
- 처리 결과 (통과/참조/모호/반려)
- 생성된 노트 경로
- 갱신된 index 항목
- log 엔트리
