---
name: 밀리터리숏폼
description: 국뽕/방산 테마 세로 숏폼(1080×1920) 영상을 주제 1줄에서 완성 mp4까지 신규 제작한다. 주제 발굴·팩트체크 → 대본 → 풋티지 수집·검수 → TTS → 프리플라이트 → 합성 → 캡션까지 STEP 0~7 파이프라인을 오케스트레이션한다. "밀리터리 숏폼 만들어줘", "K9 숏폼", "방산 영상 제작", mil_NNN 런 작업 시 사용. 완성된 편의 2차 재가공은 밀리터리숏폼2차 스킬을 쓴다.
---

# 밀리터리 숏폼 자동화

작업 폴더: `01_자동화/밀리터리_숏폼/`
산출 폴더: `02_콘텐츠/밀리터리/NNN_YYYYMMDD_키워드/`

## 시작 전 반드시 읽을 것

1. `설계서_v1.7.md` — §0-2 절대 규칙, §2 파이프라인, §3 레이아웃, §4 소재 정책, §8 수용 기준
2. `대본_스타일가이드_v3.6.md` — 대본 작성 시 전 규칙 적용 (심리 엔진 6종, 문장 규칙, 흐름 규칙 9종, 과장 검수, 대립 서사). 개정 이력은 `대본_스타일가이드_개정이력.md`(작성 시 읽지 않음)

두 문서 모두 **최신 버전을 자동 선택**해서 읽는다:
```bash
ls 설계서_v*.md | sort -V | tail -1
ls 대본_스타일가이드_v*.md | sort -V | tail -1
```

## 절대 규칙

1. **파일 덮어쓰기 금지** — 수정 시 새 버전 생성(`_v1.1.py` → `_v1.2.py`), 구버전은 `_versions/`로 이동. 삭제 금지.
2. **좌표 하드코딩 금지** — 모든 화면 좌표는 `layout.json`에서만 읽는다.
3. **run_id 격리** — 모든 중간 산출물은 `_work/<run_id>/` 아래에만. run_id 규칙: `mil_NNN_YYYYMMDD` (NNN = `02_콘텐츠/밀리터리/` 연번, 3자리 0패딩).
4. **facts.json에 없는 수치·인용은 대본에 넣지 않는다.** 검증 실패 시 대본을 고치지 말고 팩트를 먼저 보강한다.
5. **소재는 설계서 §4-1 허용 소스만.** 뉴스 영상·타 유튜브 클립 다운로드 코드는 어떤 이유로도 작성 금지.
6. **API 키는 `.env`에만.** 코드에 키 문자열 금지.
7. **버전 자동 선택** — 스크립트 호출 시 버전 하드코딩 금지:
   ```bash
   SCRIPT=$(ls footage_collect_v*.py | sort -V | tail -1)
   ```
8. **프리플라이트 불통과 시 빌드 진입 금지** (exit 1).

## 세션 4분할 ★토큰 절감 핵심

비용은 세션 길이의 **제곱**에 비례한다(세션 26개 회귀 실측: 56턴 세션 턴당 86K vs 962턴 세션 턴당 360K = 4.2배). 4분할 시 -55% (`파이프라인_토큰최적화_검토_v3.0.md`).
파이프라인 상태는 전부 파일(facts/scenes/manifest/rejects/tts)에 있으므로 끊어도 잃는 게 없다.

| 세션 | 담당 STEP | 완료 조건 | 모델 |
|---|---|---|---|
| **S1 기획** | 0 팩트 · 0.5 소재 가용성 · 1 대본 | `scenes.json` | Opus 필수 |
| **S2 수집** | 2 풋티지 수집 (+AI컷 반입) | `manifest.json` | Opus/Sonnet |
| **S3 검수** | 3 눈검수 · 4 TTS | `tts/` | **Opus 필수** (비전 판별 — mil_037 사고 진원지) |
| **S4 출고** | 5 preflight · 6 빌드 · postflight · 7 캡션 | mp4 + caption | Opus |

**모델 확인 ★세션 첫 응답**
세션 단계가 정해지면(신규=S1, 이어서=handoff 결과) 현재 모델(시스템 프롬프트의 모델명)을 위 표 '모델' 열과 대조한다.
- **일치하면 아무 말도 하지 않는다.**
- 불일치면 첫 응답 맨 위에 한 줄: `⚠️ 모델: 현재 Sonnet — 이 세션(S3 검수)은 Opus 필수`
- **"필수" 세션이면 Walter 답을 받은 뒤 진행**한다. 그 외(Opus/Sonnet·Opus 권장)는 알리고 바로 진행.
- 세션 도중 모델이 바뀐 게 보이면 다시 대조한다.

**세션 운영**
- **세션 경계는 승인 게이트가 아니다.** 담당 STEP을 끝내면 handoff를 만들고 **그냥 세션을 끝낸다.** "미완 항목이 남으면 종료 금지"는 **이번 세션 담당 범위 안에서만** 적용한다.
- **눈검수 시트 이미지는 S3에서만 연다.** 다른 세션에서 열면 그 세션 내내 매 턴 재전송된다.
- 세션 인계(세션 종료 직전 + 새 세션 시작 직후):
  ```bash
  python3 "$(ls handoff_v*.py|sort -V|tail -1)" --run NNN
  ```
  진행 단계를 파일 존재로 판정하고 `_work/<run_id>/handoff.md` + stdout 출력(Read 턴 절약). **상태파일 전량을 읽지 말고 handoff가 가리키는 파일만 연다.**
- 다음 세션 진입: `/밀리터리숏폼 이어서 NNN` → 첫 동작은 위 handoff 실행.
- 분할하지 않는 예외: 한 세션 안에서 이미 대부분 끝났고 남은 게 스크립트 1~2개뿐일 때.

## 파이프라인 STEP 0~7

`[C]` = Claude가 대화 중 직접 수행 / `[S]` = 스크립트 실행

### STEP 0 — 리서치·팩트체크 [C]
웹검색 + `../유튜브_자동화/naver_search.py`로 주제 검증 → `_work/<run_id>/facts.json`
- 출처 3개 미만이면 주제 변경 제안
- 주제 발굴이 필요하면 `conflict_scout_v*.py` 사용:
  ```bash
  python3 "$(ls conflict_scout_v*.py|sort -V|tail -1)" --pool          # 주제 풀 조회
  python3 "$(ls conflict_scout_v*.py|sort -V|tail -1)" --init --topic "주제" --topic-en "English keyword"
  python3 "$(ls conflict_scout_v*.py|sort -V|tail -1)" --validate --run-id mil_NNN_YYYYMMDD
  ```

### STEP 0.5 — 소재 가용성 체크 [S] ★대본보다 먼저
```bash
python3 "$(ls footage_collect_v*.py|sort -V|tail -1)" --query "<영문 키워드>" --dry-run
```
**영상 후보 0건이면 대본 쓰기 전에 주제 반려.** "소재가 존재하는 주제만 대본이 된다."

### STEP 1 — 대본 작성 [C]
`대본_스타일가이드` 전 규칙 적용 → `_work/<run_id>/scenes.json`
- 총 길이 40~55초 (58초 초과 시 빌드 중단)
- 문장 ≤40자 · 씬 ≤70자 (HOOK 30 · CTA 80)
- 씬별 `footage.shot = {subject, action, setting, exclude}` 로 요구 화면을 구조로 지정 (어휘는 `shot_vocab.json` 단일 소스)
- 스타일가이드 §10 셀프 체크리스트 통과할 때까지 자체 검수
- ★**문장 단위 화면 지정** (수정이력_분석_v2.0 P1 — Walter 수정 소재 117건이 이 유형):
  ```bash
  python3 "$(ls sentence_shot_v*.py|sort -V|tail -1)" --run-id mil_NNN_YYYYMMDD --propose   # 문장별 need 제안
  # 틀린 need는 _work/<run>/sentence_shots.json에서 고친다(흔한 문장의 발사·비행 제안은 subject로 낮춰도 됨)
  python3 "$(ls sentence_shot_v*.py|sort -V|tail -1)" --run-id mil_NNN_YYYYMMDD --apply     # scenes[].sentences 기록
  python3 "$(ls sentence_shot_v*.py|sort -V|tail -1)" --run-id mil_NNN_YYYYMMDD --gaps      # 라이브러리 후보·AI 요청 묶음
  ```
  Walter 기대치: 말하는 사람 → **실존 인물 영상 우선**(본인 → 같은 기관 관계자, 다른 행사면 고지) → 없으면 AI 가상 인물 / 나라 주어 → 그 나라 국기 / 금액 → 그 통화 지폐 / "A에서 B까지" → 지도 / 만들다 → 공장 / 맞히다 → 맞는 순간.
  사람 need 문장에 `shot.exclude: interview`·visual_must "인물 아님"을 넣지 않는다(172·177 재발 패턴, --propose가 경고).
  `--gaps`가 만든 `ai_request_batch.md`(후보 0건 문장)는 **S1 끝에 Flow 프롬프트로 한 번에** Walter에게 전달한다(ai_prompt_check 통과본).
- ★**귀 검사**: `python3 "$(ls script_ear_lint_v*.py|sort -V|tail -1)" --run-id mil_NNN_YYYYMMDD` — 약어·축약 조사(엔·땐)·고정 오독어(날쌔게 등)·숫자+부대 단위·조사 없는 쉼표 조각. 나온 건 문장이나 tts_text로 고친다

### STEP 2 — 풋티지 수집 [S]
```bash
python3 "$(ls footage_collect_v*.py|sort -V|tail -1)" --scenes _work/<run_id>/scenes.json --run-id mil_NNN_YYYYMMDD
```
→ `_work/<run_id>/footage/` + `manifest.json` + `pool.json`(차순위 후보)

AI 컷 반입:
```bash
python3 "$(ls ai_intake_v*.py|sort -V|tail -1)" --run-id mil_NNN_YYYYMMDD --scene N --slot a --file <경로> --desc "<slug>" --keywords 한글 ... english ...
```
- `--slot a|b|c|d`: 그 슬롯만 교체(v1.5~). 다른 슬롯은 남는다
- 반입 결과의 경고를 읽는다: 앞 0.5초 장면 전환(참조 이미지 잔존 → start_s 자동 이동), 클립 안 하드컷 시각, 360p. ✦·Veo 워터마크가 있으면 manifest 항목에 `"delogo": [[x,y,w,h]]`(출력 1080×1920 좌표) — 빌드가 그 클립 구간에만 지운다. 거울 반전 컷(160)은 자동 검출이 안 되니 S3에서 8fps 확인
**AI 컷 반입 = 소재등록 동시** — `ai_intake`가 라이브러리 등록(index·md5 중복차단·비율)까지 한다. `/ai소재등록`을 따로 부르지 않는다. 대신 반입 인자를 등록 품질로 채운다:
- `--desc`: 소문자-하이픈 영문 2~7토큰, 내가 쓴 프롬프트 기준 화면 묘사 (런 번호·씬 번호 넣지 않기 — 재사용 소재다)
- `--keywords`: **필수**, 한국어+영어 혼합 6개 이상. 비우면 라이브러리에서 영원히 못 찾는다
- `--note`: `"AI 연출 화면"`만 (화면에 자막으로 구워진다)
- 반입 배치가 끝나면 **밀리터리 라이브러리만** scan 1회(썰은 안 본다):
  ```bash
  python3 "$(ls ai_library_sync_v*.py|sort -V|tail -1)" scan
  ```
  미등록·no_keywords 0건이면 끝. 남은 게 있으면 그 건만 `/ai소재등록` 2~4단계로 처리. 워터마크·타국 마킹 눈확인은 S3 눈검수에서 한다(여기서 컨택트시트 열지 않음).

### STEP 3 — 풋티지 검수 [C+S]
```bash
python3 "$(ls footage_review_v*.py|sort -V|tail -1)" --run-id mil_NNN_YYYYMMDD --sheet
```
- 승인/반려: `--approve N` / `--reject N --reason "사유"`
- 피사체 중앙 지정: `--focus N:0.5`
- **재수집 대신 차순위 교체**를 우선한다(재검색은 verified 리셋·타 씬 오염 위험):
  ```bash
  python3 "$(ls swap_next_v*.py|sort -V|tail -1)" --run-id mil_NNN_YYYYMMDD --list          # 교체 후보 확인
  python3 "$(ls swap_next_v*.py|sort -V|tail -1)" --run-id mil_NNN_YYYYMMDD --key <씬키> --rank N --reason "사유"
  ```
- 문장 need 검사: `sentence_shot --check`. 불일치 문장은 교체하거나, 눈으로 보고 맞으면 `--shows "s02_a:flag"`로 기록
- 금지(bad) 소재는 `--approve`가 거부한다(v2.4). 금지를 풀려면 Walter 확인 후 `--unban`. `--bad`는 슬롯을 남기므로 바로 swap 가능
- 한 명령에 같은 옵션을 여러 번 줘도 된다(v2.4부터 모두 기록)

### STEP 4 — TTS [S]
```bash
python3 "$(ls tts_run_mil_v*.py|sort -V|tail -1)" _work/<run_id>/scenes.json
```
엔진 체인: Google Chirp3-HD → Edge TTS → gTTS
v3.4부터 한 문장을 통째로 합성한다(쉼표 조각 합성 폐지 — TTS 지적 24건의 원인). 쉼표는 자막에만 남는다. 쉼표를 빼면 앞뒤가 붙어 다른 말로 들릴 곳("같은 해 제트")은 tts_text에 조사를 붙인다. 명·척·문·시간은 고유어로 읽는다("세 명").
→ `_work/<run_id>/tts/*.mp3` + `timing.json`

### STEP 5 — 프리플라이트 [S] ★게이트
```bash
python3 "$(ls preflight_mil_v*.py|sort -V|tail -1)" --run-id mil_NNN_YYYYMMDD
```
**불통과(exit 1) 시 절대 빌드로 넘어가지 않는다.** 지적 사항을 고치고 재실행.
게이트 우회 플래그(`--skip-why`, `--skip-rewrite` 등)는 **Walter 승인 시에만** 사용.
v3.7 신규 차단: [SENT-SHOT] 문장 need↔클립 · [BANNED] 금지 소재 · [PHOTO-LONG] 사진 3초 초과 · [SAMESRC-MANY] 짧은 소재 3회 이상 · [TTS-STALE] 대본≠음성 · [TTS-PEAK] 클리핑. [EAR]은 경고.

### STEP 6 — 영상 합성 [S]
```bash
python3 "$(ls military_build_v*.py|sort -V|tail -1)" --run-id mil_NNN_YYYYMMDD
```
4레이어: L1 풋티지 → L2 스크림 → L3 제목 밴드 → L4 자막
v1.19: `--out`을 비우면 산출 폴더(`02_콘텐츠/밀리터리/NNN_*`)를 자동으로 찾는다(폴더 경로만, mp4 경로 금지). seg_dur가 없는 씬은 **문장 경계에서 클립을 바꾼다**(50:50은 문장이 1개일 때만). manifest `delogo`는 재빌드해도 유지된다.

### STEP 7 — 산출·캡션 [C+S]
```bash
python3 "$(ls postflight_v*.py|sort -V|tail -1)" --run-id mil_NNN_YYYYMMDD --video "<완성 mp4>"
```
★**문장별 대조 시트 자가검수** (P7): 시트를 열어 문장마다 ①need 화면이 보이나 ②주어=화면 주체 ③국적·영역 ④앞 칸 반복 ⑤✦·로고·타국 마킹 을 본다. "Walter라면 걸 문장"은 고치고 재빌드. 결과 기록:
`--verdict "3-1:ok,7-2:fix:국기 아님"` — fix가 남아 있으면(exit 1) 출고하지 않는다.
캡션(`caption.txt`·`youtube_caption.txt`)은 Claude가 작성. mp4는 STEP 6 빌드가 산출 폴더에 직접 쓴다.
★**댓글 10개** (2026-10-07~): `youtube_caption.txt` 맨 아래에 `【댓글】 ※ 설명란에 붙이지 말 것 — 업로드 후 댓글용` 블록을 붙인다(184 형식). 유형 라벨은 붙이지 않고 댓글만 빈 줄로 나눈다.
- 구성: **응원 3 · 부정 2 · 의문 3 · 헛소리 2** (유형 순서대로)
  - 응원: 이 편 주제에 맞춘 한마디. "유익한 영상 감사합니다" 같은 범용 칭찬 금지
  - 부정: 회의·비꼼은 의견으로만. 실존 기업·인물에 대한 근거 없는 사실 단정(“발표만 하고 엎었다” 등) 금지
  - 의문: 영상이 답하지 않은 실제로 궁금할 만한 것. 질문 안에 틀린 사실을 전제로 깔지 않는다
  - 헛소리: 영상 속 단어에서 튀어나온 엉뚱한 농담(184 "콜라 캔 던지는 줄")
- AI 티 빼기: 길이 들쭉날쭉(한 줄~두 줄), 반말·존댓말·음슴체 섞기, ㅋㅋ·띄어쓰기 느슨하게 허용. 이모지·해시태그·느낌표 연발·"~네요!" 반복·영상 요약 금지. 10개가 같은 어미로 끝나지 않게
> `handoff_v*.py`는 출고 스크립트가 **아니다** — 세션 인계용(§세션 4분할).
최종 산출 폴더 구성: `short_NNN_<키워드>_YYYYMMDD_HHMMSS.mp4`, `caption.txt`, `youtube_caption.txt`, `facts.json`, `perf.json`
★**디스크 정리** (2026-10-07~): 출고 마지막에 `python3 "$(ls disk_dedup_v*.py|sort -V|tail -1)" --apply` 1회. 같은 소재 사본을 APFS 클론으로 합친다(내용·경로 그대로, 재가공 영향 없음). 다른 세션이 파이프라인 실행 중이면 스스로 중단 — 그냥 넘어간다. 출력 끝 '여유 공간'이 30GB 미만이면 Walter에게 알린다.

## 수정 요청 처리 ("수정사항 있어")

1. **먼저 기록**: `_수정요청_로그/<run_id>_<요청일>.md` — 항목별 표(번호·시점·축·씬키·대본 문장·기존 소재·Walter 요구·유형)
2. 지적 시점 프레임으로 **그 씬의 모든 슬롯**을 확인해 a/b를 확정한다(167 #2는 b였음)
3. 교체 후보는 **주체·동작·영역(지상/함정/공중)·국적** 4가지를 대본과 대조한다 — 동작만 맞추면 159-3처럼 함정 발사 컷이 지상 SAM 문장에 들어간다
4. 교체·금지한 소재가 **같은 편 다른 슬롯**에도 있는지 찾는다(160·184)
5. 대본을 고쳤으면 TTS 재합성 + highlight·script_draft 동기화 → preflight([TTS-STALE]이 잡는다)
6. 재빌드 후: postflight 시트 · caption_note/caption_notes · 캡션 크레딧(manifest credit과 대조) · 구 mp4·구 캡션은 **삭제**(`_이전버전/` 만들지 않음, 2026-10-07~). 산출 폴더엔 최신 mp4 1개만
7. 로그에 "처리 결과" 기입. 개선 효과는 `python3 "$(ls fix_stats_v*.py|sort -V|tail -1)" --split <적용 시작 편>`의 편당 건수로만 판단한다(재가공 `_rN` 로그는 v1.1부터 제외, `--rework`로 따로)

## 기존 편 재가공 (2차 제작)

완성된 편을 제2채널용으로 재가공하는 작업은 **`밀리터리숏폼2차` 스킬**을 사용한다. 소재 하드링크 승계·bind_class 규칙·rework_gate가 거기 정리돼 있다.

## 품질 목표

- 첫 3초 유지율 80%↑ / 완주율 70%↑ → 총 길이 **40~55초**
- 첫 텍스트 0.0초(제목 밴드 고정), 첫 발화 0.3초 내, 무음 인트로 금지
- 시각 변화 최대 4초 간격 (풋티지 교체 or 줌펀치)
- 오디오 최종 -14 LUFS, BGM 베드 -28 LUFS
- 첫 프레임 = 썸네일 성립

## 화면 안전영역 (1080×1920)

```
y=0~220     UI 위험지대      — 텍스트 금지
y=220~560   제목 밴드 (고정)
y=560~1300  풋티지 스테이지
y=1300~1560 자막 밴드 (최대 860px 센터)
y=1560~1920 UI 위험지대      — 텍스트 금지
x 우측 170px (y900~1560) 버튼 스택 — 침범 금지
```

## 실행 전 확인

- 유료/쿼터 API(DVIDS, Google TTS) 사용 단계는 ⚠️ 표기하고 드라이런을 먼저 제안한다.
- `.env` 필요 키: `DVIDS_API_KEY`, `MIL_TTS_VOICE`, `MIL_TTS_ENGINE`, `MIL_TTS_RATE`, `EHISTORY_API_KEY`, `NARA_API_KEY`, `PEXELS_API_KEY`, `PIXABAY_API_KEY`, `FLICKR_API_KEY`
- 의존성: `ffmpeg`, `python-dotenv`, `google-cloud-texttospeech`, `puppeteer`(headline capture)
