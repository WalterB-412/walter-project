#!/usr/bin/env python3
"""
[롱폼 v1.7] 세로 소재 **완전 배제** (2026-10-12, Walter 지시 "롱폼은 가로 소재만 사용").
  v1.3~v1.6은 세로를 '강등'만 했다 — 가로 후보가 0건이면 정렬 맨 뒤에 있던 세로가 그대로
  뽑혔고(fresh·reuse·사진 폴백 세 경로 모두), preflight는 씬 수 10%까지 허용했다.
  → 이제 후보 단계에서 세로(ar<1.0)를 **아예 버린다.** 버린 결과 소재가 0건이면 조용히
    채우지 않고 기존 폴백 체인(no_match / ai_request / card)으로 넘어간다 — 다음 단계에서
    사람이 가로 소재를 찾거나 AI컷을 **가로로** 생성한다.
  · try_pick 첫 줄에서 is_portrait → False (세 경로 공통 차단점 하나)
  · pool.json(차순위 후보)에도 세로를 싣지 않는다 — swap_next로 되돌아 들어오는 경로 차단
  · ai_first / ai_request 후보 목록에서 세로 AI컷 제외(재사용 판단 목록에 보일 이유가 없다)
  · 4:3·1:1(ar 1.0 이상)은 그대로 허용 — 옛 기록영상이 다큐의 핵심 소재라서다.
    build의 fit 체인이 블러 여백으로 받는다.
  · 비율 미상(ar=0) 후보는 v1.3과 같이 통과시키고, 최종 판정은 preflight v2.0의
    [PORTRAIT-IN-LONG](파일 ffprobe 실측, 상한 0)이 한다.
  · 비상 우회: .env MIL_LONG_ALLOW_PORTRAIT=1 (v1.6 동작으로 복귀)
[롱폼 v1.4] Pexels 세로 강제 요청 제거 — v1.3 게이트를 무력화하던 포크 버그(2026-08-10).
  `pexels_search`가 숏폼에서 **`"orientation": "portrait"`를 그대로 물려받아** API에 세로만
  요청하고 있었다. v1.3의 세로 강등은 "가로 후보가 하나라도 있으면"이 전제인데, 후보 풀이
  애초에 100% 세로면 **강등할 대상이 없다** — 게이트가 조용히 무의미해진다.
  실측: millong_001의 세로 14씬 중 **10씬이 Pexels 스톡**이었다(AI컷은 4씬뿐. 스펙이 사고로
  지목한 s24·s49·s50·s53이 그 4개고, 진짜 다수는 이쪽이었다).
  → 롱폼은 `landscape`로 요청한다. 개념 b-roll이 롱폼 소재의 주력이라 이 한 줄이 v1.3보다
    실질 효과가 크다. (짧은 변 1080 필터는 그대로 — 가로 1920×1080이 그대로 통과한다.)

[롱폼 v1.3] 세로 소재 차단 게이트(2026-08-10 — 작업스펙_AI컷_비율정합_v1.0 작업 2·4-2).
  배경: `military_build v1.10`이 풀블리드를 폐지해 `fit_decision`이 **절대 None을 반환하지
  않는다**. 그래서 720×1280 세로컷이 1920×1080 캔버스에 들어가면 폭 547px = 화면의 28.5%만
  차지하고 나머지는 블러인데, 그게 **경고 한 줄 없이** 출고됐다(millong_001 s24·s49·s50·s53).
  블러 폴백은 버그가 아니라 안전망이다 — 없던 건 그 앞단의 차단 게이트다. 여기가 그 앞단이다.
  · `cand_ar()`: 후보의 실제 표시 비율(width/height → resolution "WxH" → _ai index의 ar 순).
  · **가로 후보가 하나라도 있으면 세로는 절대 선택하지 않는다** — fresh/reuse 정렬의 *첫*
    키가 is_portrait다(era·hint·impact보다 앞. 세로는 어떤 장점으로도 만회가 안 된다).
    비율을 모르는 후보(ar=0)는 세로로 취급하지 않는다 — 오래된 라이브러리 항목이
    부당하게 강등되면 회귀다.
  · AI 최후수단에서 **가로 AI컷이 하나도 없으면** 세로로 때우지 않고 `fallback:"ai_request"`로
    승격한다(작업 4-2) → preflight [AI-REQUEST]가 잡고 → 게이트 A로 Walter에게 가로 생성 요청.
    세로 후보는 `ai_library_candidates`에 orient 표시와 함께 실어 보낸다(사람이 상한 안에서
    쓰겠다고 판단하면 수동 배정 가능 — 자동으로는 절대 안 들어간다).
  · manifest 항목 `resolution`을 실제 값으로 채운다(라이브러리·AI 후보는 v1.2까지 "0x0"이었고,
    그래서 하류 도구가 비율을 볼 방법이 없었다).
  판정 근거 데이터는 `_ai/index.json`의 w·h·ar — `ai_ratio_backfill_v1.0.py`가 백필하고
  `ai_intake_v1.2`(롱폼)/`v1.3`(숏폼)이 반입 시 자동 기록한다.

[롱폼 v1.2] ai_first 씬이 card로 조용히 강등되던 버그 근본수정(2026-08-10, millong_001).
  · footage.ai_first=true → fallback:"ai_request"(+_library/_ai 재사용 후보 동봉)로 승격.
    preflight [AI-REQUEST]는 "ai_request"만 검사하므로, card 강등은 게이트를 무력화했다.
  · 숏폼 mil_037/mil_039와 동일한 사고 경로 — 롱폼 포크에도 그대로 있었다(dry-run으로 재현).

[롱폼 v1.1] 숏폼 footage_collect v3.3+v3.4 이식(2026-08-09).
  · v3.3: 함정 접두 호칭(roks/uss/hms…)을 GENERIC_TOKENS에 추가 — 함급이 다른 배들이
    호칭 하나로 단독 매칭되던 오배정 차단.
  · v3.4: 스톡 차단어에 운동·요리·수공예 추가 — press_briefing→케틀벨, engineer_design→
    대장간 오배정 차단. 롱폼은 개념 씬 비중이 숏폼보다 커서 이 차단이 더 중요하다.
  롱폼 고유 로직(graphic 씬 바이패스·롱테이크 need 계산·SOURCE_REUSE_CAP)은 v1.0 그대로.
"""

"""
footage_collect_v1.8.py — 밀리터리 숏폼 소재 수집기 (설계서_v1.5 §6-1)

v1.1: Commons 관련성 검사 완화(제목→설명 순, 미매칭은 후순위 강등만),
      사진 검색량 20→50, 판정식 개선(영상 풍부시 사진 부족해도 GREEN)
v1.2: 캐시 등록 슬러그를 파일 제목이 아닌 검색 구문 기준으로 수정 (캐시 재사용 버그 픽스)
v1.3: ①CC BY-SA 허용(Walter 승인 2026-07-04 — 크레딧 표기 의무 자동 기록)
      ②Openverse 사진 소스 추가(Flickr CC/PD 등, wikimedia 제공분은 중복이라 제외)
      ③prefer=photo 체인에 DVIDS 사진 추가(§4-3 설계 누락분) ④CC 저작자표기 disclaimers 추가
v1.4: 주제 일치 게이트(Walter 요청 — "K2 주제에 전투기 금지")
      ①scenes.json subject 필드: 씬 phrases가 주제 별칭 밖이면 수집 거부(offtopic_ok 예외)
      ②rejects.json: 눈검수(footage_review)에서 거부된 source_id 재수집 영구 제외
      ③manifest 항목에 key(s01_a)·verified:false 추가 — preflight가 verified 강제 예정
v1.5: 영상 비중 극대화 (Walter 요청 — "영상 위주 + 한 영상을 잘라 여러 씬 분배")
      ①런 레벨 클립 풀: 씬 간 같은 클립 그대로 반복 금지, 긴 영상은 다음 구간(start_s)으로 재사용
      ②start_s 자동 분배 — 같은 소스여도 씬마다 다른 구간이 잘려 들어감 (역동성)
      ③사진 폴백 전에 '기존 영상의 새 구간' 재사용을 먼저 시도 (video-first)
v3.0: 개념 b-roll (Walter 요청 2026-07-20 — "대본과 전혀 상관없는 영상이 맵핑된다").
      원인: 어휘 부재. weapon_aliases.json은 무기 슬러그만 갖고 있어서 '영국 군사전문지
      제인스가 기록했다' 같은 씬에 배정할 말이 없었다 → Claude가 가장 가까운 무기 슬러그를
      억지로 넣고 화면은 무관한 사막 클립이 됐다(mil_028 씬8 실측). 게다가 주제 일치
      게이트가 무기 밖 phrases를 거부해서, 잡지·신문을 넣으려는 시도 자체가 차단됐다.
      ①concepts.json 신설 + footage.concept 필드 — 잡지·엔지니어·공장·서명·표적 등 개념 어휘
      ②concept 씬은 주제 일치 게이트 자동 우회(offtopic_ok 불필요) + caption_note 자동
      ③무료스톡 소스 추가(Pexels·Pixabay) — concept 씬 전용. 개념 영상은 Commons에 사실상
        없어서 이게 없으면 3)번 요구가 해결 안 된다. 주제 무기 씬에는 절대 투입되지 않는다.
      ④스톡은 인물 클로즈업 자동 제외(모델릴리스 미보장) — STOCK_TITLE_BLOCK
v2.9: 눈검수 기록 → 배치 배선 (Walter 목적 — "눈으로 본 게 실제 배치까지 이어지는 것").
      배경: `_ai/index.json`의 best_s 62건이 **한 번도 읽히지 않았다**(2026-07-19 실측).
      누락이 아니라 덮어쓰기였다 — AI 클립은 start_s=3.0이 깔린 뒤 v2.8 소프트랭킹이 또 옮겼다.
      ①`_library/_eyes.json`(키 = **md5**, 경로·source_id 아님) 신설 — 오염의 본질이
        "레코드는 맞는데 파일이 침입자"라 경로는 못 믿는다. md5에 붙이면 같은 md5가
        소스 9개에 등록돼 있어도 한 번 보면 9개가 동시에 해결된다.
      ②`eyes.best_s`가 있으면 **소프트랭킹 완전 스킵**(눈 > 산술). 미세조정 허용 안 함 —
        기록과 결과가 어긋나면 눈검수 자체가 무의미해진다. 단 같은 클립 2회차 사용은
        잠금 없이 소프트랭킹(같은 장면 두 번 방지) + `eyes.skip` 구간 회피.
      ③`verdict:"bad"` 파일은 후보에서 제외(_contaminated.json 보완).
      ④manifest에 `eyes` 통계 — 반영 0건이면 경고. 배선이 또 끊기면 즉시 드러난다.
      ⑤`_eyes.json`이 없으면 md5 계산조차 안 함 = v2.8과 완전 동일 동작(회귀 없음).
v1.6: 소스 다양화 (Walter 피드백 — "같은 영상 반복 過多")
      ①소스당 사용 상한 3회 ②직전 세그먼트와 같은 소스는 대안 있으면 회피(인접 중복 방지)
      ③인트로 스킵 3초 — 기관·방송 클립 도입부의 안내판/타이틀/페이드 회피(여유 길이 있을 때만)
v1.7: 다양화 강화(Walter 2차 피드백) — ①소스당 상한 3→2회 ②한 씬 안에 같은 소스 2구간 금지
      (부족분은 사진 폴백으로 채워 화면 다양성 확보 — 영상 비율 75~85% 유지)
v1.8: ①씬-소재 의미 매칭 — scenes.json footage.hint(예: "firing|사격")가 후보 제목과
      매칭되면 해당 소스를 그 씬에 최우선 배정 (대본 내용 ≈ 화면 내용)
      ②로컬 스톡 tier — 유튜브_자동화/output/images/ (Walter 보유 438장, Wikimedia 수집분).
      _rename_log.json의 원본명으로 Commons 라이선스 역추적 → 확인된 것만 채택.
      사용 시 _library에 desc 파일명 그대로 보존 등록(재사용 네이밍 요구 충족)
v1.9: 영상 간 다양성 (Walter 3차 피드백 — "비슷한 주제마다 같은 클립 재등장, 지루함")
      근본원인: ①_library 캐시가 무조건 1순위(tier)라 새 다운로드를 안 함
                ②사용이력을 영상 간에 기억 안 함(pool은 한 영상 내부만)
      해결: ①전역 사용대장(index.json usage/runs) — 어느 클립을 어느 영상에 몇 번 썼는지 영구 기록
            ②tier 우선 → '전역 사용 적은 소스 우선' 랭킹으로 교체 (라이브러리 독점 해소)
            ③쿨다운 — 최근 N개 영상에 쓴 클립은 대안 있으면 후순위(소프트, 고갈 시 자동 완화)
            ④신선비율 경고 — 영상당 '한 번도 안 쓴 새 소스' 비율이 목표 미만이면 경고(하드 반려 X)
            ⑤--backfill — 기존 _work/*/manifest.json에서 과거 사용이력 시딩(1회)
      튜닝(.env): MIL_FOOTAGE_COOLDOWN(기본 2), MIL_FRESH_RATIO(기본 0.4)
      순수 국산무기(K2·KF-21 등 커버리지 빈약)는 풀 고갈 시 LRU 재사용으로 우아하게 degrade.
v2.0: 다운로드 재시도+Range 이어받기(connection reset 등 일시 오류 방어).
v2.1: 시대(era) 축 신설 (Walter 요청 — "역사 주제에 현대 영상이 딸려온다") ★
      근본원인: 소스가 전부 현대 실사 편향(DVIDS는 2004년 이후 대부분) + era 차원 부재.
      해결:
        ①scenes.json 최상위 "era" 또는 씬 footage.era (예: vietnam_war·korean_war·wwii·modern).
          기본 modern = 현행과 100% 동일(추가검색·페널티 없음).
        ②archive.org(Internet Archive) 영상 어댑터 — PD/CC 필터(licenseurl·collection·저작권상태
          교차확인, 불명은 자동 제외하되 dry-run에 '수동확인 후보'로 카운트). era 검색토큰 결합.
        ③NARA(미 국립기록원) 어댑터 — NARA_API_KEY(.env) 있을 때만 활성(없으면 조용히 [] = Phase 2).
        ③-2 e영상역사관/대한뉴스 어댑터 — 공공누리 제1유형(=KOGL Type 1, license_ok 통과).
            EHISTORY_API_KEY(.env, data.go.kr 발급) 있을 때만 활성. 링크가 재생페이지면
            자동다운 불가라 manual 카운트만 → 사람이 ehistory_intake_v1.0.py로 반입.
            (스키마 미확정 — 키 발급 후 EHISTORY_API_URL·필드매핑 1회 보정 필요.)
        ④era≠modern이면: 현대 DVIDS 제외 + era 소스(archive/nara) 최우선 랭킹 + 영상 최소높이 완화
          (아카이브 필름은 저해상도라 720 게이트로 걸러지던 문제 → era_styles.json _video_min_height).
        ⑤era 검색토큰·AI 연출 프롬프트 = era_styles.json 단일 소스(코드 아닌 데이터 확장).
      ⚠️ 라이선스 원칙 불변: 확인된 PD/CC만 자동 채택. 불명은 STEP 3 눈검수로. 나이≠PD.
v2.3: 병렬 세션 안전(Walter 요청 — "여러 주제를 다른 세션에서 동시 진행").
      근본원인: index.json(전역 사용대장·라이브러리 캐시)이 락 없이 read-modify-write되어
                두 세션이 동시에 footage_collect를 돌리면 한쪽 갱신이 유실될 수 있었음.
                또한 같은 소스 클립을 두 세션이 동시에 받으면 .part 임시파일이 뒤섞일 수 있었음.
      해결: ①fcntl.flock 기반 index.json 트랜잭션(library_index_txn) — build_ledger/
              record_usage/library_register/backfill_ledger 전부 이 락 아래에서 read+write
            ②download()/archive_range_download()에 dest별 락(.lock 파일) — 동시 요청은
              직렬화되고, 락 획득 후 dest가 이미 있으면 재다운로드 없이 즉시 반환(멱등)
      NNN 폴더 연번은 reserve_run_v1.0.py로 별도 원자적 채번(이 스크립트와 무관, SKILL.md 참고).
v2.2: 대용량 원본 range-seek 수집 (Walter 요청 — "대용량이라 스킵하지 말고 다운받아 잘라서 다른 곳에도 활용").
      근본원인: archive.org 원본이 소형 파생본(≤180MB) 없이 대용량(수백MB~GB) 파일 하나뿐이면
                v2.1까지는 통째로 스킵 → K2/K9 같은 소재 빈약 무기의 후보가 그대로 유실.
      해결: ①소형 파생본이 없을 때만 대용량 원본을 후보로 승격(archive_large=True)
            ②전체 다운로드 대신 ffmpeg `-ss <start_s> -i <url> -t <구간>`로 필요한 구간만
              원격에서 잘라온다(HTTP range seek, 실전송량≈구간 길이). 이 구간 파일이 최종 클립.
            ③구간 파일은 그 자체로 완결된 소스이므로 manifest start_s를 0으로 재설정,
              duration_s도 물리적 구간 길이로 보정(다운스트림 military_build/footage_review가
              존재하지 않는 구간을 seek하지 않도록).
            ④library_register에도 보정된 duration_s로 등록 → _library 캐시에 남아
              **다른 영상 제작 시에도 그대로 재사용**(Walter가 원한 "다른 곳에도 활용").
            ⑤같은 소스를 여러 씬이 서로 다른 start_s로 쓰면(v1.5 클립 풀) 매 씬마다 별도
              구간을 다시 range-fetch — 로컬 파일 공유 캐시(pool._local)는 이 케이스에서 끔
              (물리적으로 그 구간만 있어 다른 start_s를 못 커버하기 때문).
      튜닝(.env): MIL_ARCHIVE_RANGE_MARGIN(기본 2.5초 — 씬 길이 + 여유분).
v2.7: 라이브러리 오염 파일 배제 (Walter 승인 2026-07-17).
v2.8: 구간 선택을 소프트랭킹으로 재설계 (Walter 요청 2026-07-17).
      ①v2.4 피크윈도우를 impact:"high" 씬 → 전 씬으로 확장. 프로파일만 갈린다:
        high=impact(발사·화염 우선, v2.4 가중치 유지) / 그 외=presence(사각지대 회피).
        presence는 소스 선택·다양성 랭킹에 개입하지 않는다 — 같은 클립 안에서 구간만 옮긴다.
      ②MIL_IMPACT_MAX_SCAN(180초 상한) 폐기 → 2단 스캔(coarse 전체훑기+캐시 → 상위구간 fine).
        상한이 긴 원본 67/203개를 스캔에서 통째로 제외시켰고, 그게 1153초 KF-21의
        500초 빈하늘이 검수를 통과해 출고된 경로였다.
      ③정규화 절대 바닥 도입 — v2.4의 `max+1e-6`은 화염이 0인 클립의 노이즈까지
        1.0으로 증폭했다(실측: KF-21 fire max 0.0080 → 기여도 1.60).
      ④pool[src]["used"] 점유 구간 대장 — 같은 클립을 여러 씬이 쓸 때 구간 충돌 방지.
      ★ 하드블록(skip_ranges)은 폐기됐다. 재도입 금지 — 근거는 아래 v2.8 블록 주석 참조.
      index가 주장하는 source와 실물 내용이 다른 파일 48개를 후보에서 뺀다.
      실측: 영상 277개 중 43개(16%)가 index duration ≠ 실물. 동일 md5가 다른 source_id로
      등록된 그룹 20개, 저작자까지 다른 그룹 14개(캡션 저작자 표기가 틀릴 수 있는 건).
      v2.6의 매칭 수정이 "엉뚱한 소스를 고르는" 문제였다면, 이건 "고른 소스의 파일이 딴 내용"이다.
      목록: _library/_contaminated.json (library_map_v1.0.py audit --write-blocklist로 생성).
      파일 없으면 조용히 비활성 = v2.6과 동일 동작.

v2.6: 무기 제식명 오매칭 근본수정 2종 (Walter 승인 2026-07-17).
      기존 "엉뚱한 무기 배정" 사례의 근본 원인 — 둘 다 매칭 단계 버그다.

      ① relevant()가 순진한 substring이라 'k2'가 'k239'에 걸려 K2 흑표 씬에 K239 천무가 실렸다.
         실측: "K2 흑표 전차 기동" 라이브러리 매칭 17건 중 10건(59%)이 K239 천무·천무PL·K239T.
         → _token_hit(): 숫자 포함 토큰은 뒤에 숫자가 더 오면 불일치(K2≠K239, K2A1은 일치).
      ② core_tokens()가 숫자 든 토큰을 무조건 우선해서 맨숫자가 핵심 토큰이 됐다.
         "Leopard 2 tank" → 핵심 토큰이 '2' 하나 = "2가 들어간 아무거나"와 매칭(231개 중 96개).
         → 제식명(글자+숫자)만 우선. 맨숫자(2·2015)는 연도·수량이지 무기가 아니다.

      검증(실전 scenes.json phrase 50개 전량 대조): 결과가 달라진 조합 6개, 제외 144건이
      전부 '토큰 뒤 숫자'=다른 무기, 새로 늘어난 매칭 0건. K9·KF-21·K239·120mm 전부 무변경.

v2.5: AI 생성 컷 최후수단 자동화 (Walter 요청 — "_ai 폴더도 목록화해서 없을 때 최후에 검토").
      근본배경: _library/_ai/는 ai_intake_v1.0.py가 씬 1개 반입 시에만 등재해 지금까지
                자동 검색 대상이 아니었음(Walter가 직접 폴더에 드롭한 파일은 인덱스에도 없었음,
                49/76건 미등재 확인 2026-07-17) — 실사가 있어도 AI가 끼어들 위험을 피하려면
                순서가 중요해서 손대지 않았던 부분.
      해결: ①ai_library_find()가 `_library/_ai/index.json`을 keyword 매칭 — 단 실사(영상+사진
              Ken Burns 폴백까지) 전부 실패한 씬에서만 호출(최후수단, tier 최하위 고정)
            ②픽업되면 manifest disclaimers_needed에 "ai_disclosure" 자동 추가 +
              scenes.json 해당 씬 caption_note("AI 연출 화면") 자동 주입(수동 등재 불필요해짐)
            ③ledger(전역 사용대장)를 AI 클립에도 그대로 적용 — 같은 AI 컷 반복 사용도 다양성 랭킹 대상
      인덱스 갱신: 새 AI 영상을 계속 만들 때는 ai_library_sync_v1.0.py를 수시 재실행해
                  _library/_ai/의 미등재 파일을 자동 backfill(파일명 토큰화로 keywords 유추).

v3.2: ★매니페스트 보존 버그 근본수정 (mil_032 실전에서 발견 — Walter 지적 2026-07-23).
      증상: 씬 하나만 고치려고 --scenes를 다시 돌려도, run_scenes_mode가 매번
            manifest.json을 "items": [] 로 새로 시작해 scenes.json 전체를 처음부터
            재수집한다. 그 결과 이미 반입해둔 AI컷·수동확정 소재(scan_pick이
            manual_*이거나 source가 ai)가 조용히 스톡 검색 결과로 되돌아갔다
            (씬1·6 AI컷이 2번 연속 리셋됨 — STEP 3를 통과했던 것도 무의미해짐).
      수정: run_scenes_mode 시작 시 기존 manifest.json을 읽어 씬별로
            "보호 대상"(source=="ai" 또는 scan_pick이 "manual_"로 시작하는 항목이
            하나라도 있는 씬)을 추려낸다. 그 씬은 collect_for_scene을 아예 호출하지
            않고 기존 항목을 그대로 이어받는다 — 나머지 씬만 정상적으로 재수집된다.
      우회: --force-recollect "3,7,10" 처럼 씬 ID를 넘기면 보호를 무시하고
            강제로 재수집한다(의도적으로 다시 검색하고 싶을 때).

사용법:
  # STEP 0.5 소재 가용성 체크 (run_id 불필요, 다운로드 없음)
  python3 footage_collect_v2.2.py --query "K9 Thunder" --dry-run

  # STEP 2 씬별 수집 (scenes.json 기반)
  python3 footage_collect_v2.2.py --scenes _work/<run>/scenes.json --run-id <run> [--dry-run]

  # (1회) 과거 사용이력 백필 — index.json에 usage/runs 시딩
  python3 footage_collect_v1.9.py --backfill

종료 코드: 0=성공 / 1=검증 실패 / 2=격리 위반 / 3=외부 API 실패
소스 우선순위(v1.9): 전역 사용 적은 순 → (동률) hint매칭 → 쿨다운 밖 → 카드 씬
  ※ 라이브러리·Commons·DVIDS를 한 풀에 놓고 '덜 쓴 소스'가 이김 (tier 우선순위 폐지)
라이선스 화이트리스트(§4-2-2c): PD·CC0·KOGL Type 1·CC BY (CC BY-SA/NC/ND 제외)
"""
import argparse
import fcntl
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import urllib.parse
from contextlib import contextmanager
from pathlib import Path

try:
    import requests
except ImportError:
    print(json.dumps({"error": "requests 미설치 — pip install requests"}, ensure_ascii=False))
    sys.exit(3)

# v2.4 임팩트 스캔용(선택 의존성) — 없으면 프레임 점수만 조용히 비활성, 나머지 파이프라인 정상.
try:
    import cv2
    import numpy as _np
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False

# v1.6 (2026-09-08): ★요구 화면(shot) 매칭 — 숏폼 v3.5/v3.6 처방 B·C·D 이식.
#   이 수집기도 scene["text"]를 읽는 곳이 0군데였고 fresh_key에 관련성 축이 0개였다
#   (숏폼과 같은 구멍). 롱폼은 **씬당 클립 상한이 5**라 한 씬에 오배정이 더 많이 들어온다.
#   · footage.shot{subject,action,setting,exclude} → shot_score를 랭킹 최우선 키로
#     (is_portrait·era 다음, hint 앞). 다양성은 동점 내부에서만.
#   · library_find가 files[].seen(화면 서술)로도 파일을 찾는다 — 롱폼 _library는 숏폼
#     _library의 심볼릭 링크라 백필분(950파일·2,189문장)을 그대로 쓴다.
#   · 조건 충족 후보 0건이면 fallback:"no_match" → preflight [NO-MATCH]가 빌드를 막는다.
#   · 차순위 후보를 pool.json에 남겨 swap_next가 재검색 없이 교체한다.
#   ★ shot이 없는 씬은 v1.5와 100% 동일하게 동작한다(옵트인).
BASE = Path(__file__).resolve().parent
UA = {"User-Agent": "WalterShortformBot/0.1 (bongstyle412@gmail.com)"}
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
DVIDS_SEARCH = "https://api.dvidshub.net/search"
DVIDS_ASSET = "https://api.dvidshub.net/asset"
ARCHIVE_SEARCH = "https://archive.org/advancedsearch.php"   # v2.1 Internet Archive
ARCHIVE_META = "https://archive.org/metadata"               # /<identifier>
ARCHIVE_DL = "https://archive.org/download"                 # /<identifier>/<file>
NARA_API = "https://catalog.archives.gov/api/v1"            # v2.1 (NARA_API_KEY 필요, Phase 2)
# archive.org 큐레이션 PD/CC 컬렉션 — 여기 속하면 라이선스 공란이어도 PD로 신뢰(그 외는 licenseurl로 판정)
ARCHIVE_PD_COLLECTIONS = {"prelinger", "stock_footage", "35mmstockfootage",
                          "publicmoviesarchive", "FedFlix", "usnationalarchives"}
# 5초 클립엔 거대 원본 불필요 — 소형 파생본은 이 상한 이하만 채택(그 외는 range-seek 후보로)
ARCHIVE_MAX_MB = int(os.environ.get("MIL_ARCHIVE_MAX_MB", "250"))
# v2.2: 소형 파생본이 없어 대용량 원본을 range-seek할 때, 씬 필요 길이에 더할 여유(초)
ARCHIVE_RANGE_MARGIN = float(os.environ.get("MIL_ARCHIVE_RANGE_MARGIN", "2.5"))
TIMEOUT = 30

EXIT_OK, EXIT_VALIDATION, EXIT_ISOLATION, EXIT_API = 0, 1, 2, 3

SEC_PER_CHAR = 0.12          # 씬 길이 추정: len(text) × 0.12 (§6-1)
# 롱폼 v1.0: 숏폼과 분리된 튜닝 상수(.env로 override, 기본값은 숏폼과 동일해 하위호환).
LONG_MAX_CLIP_DUR = float(os.environ.get("MIL_LONG_MAX_CLIP_DUR", "7.5"))    # preflight MAX_SINGLE_CLIP_DUR와 동기
LONG_TARGET_SEG_DUR = float(os.environ.get("MIL_LONG_TARGET_SEG_DUR", "5.0"))  # v1.5: 목표 세그먼트 길이
SOURCE_REUSE_CAP = int(os.environ.get("MIL_SOURCE_REUSE_CAP", "3"))          # 숏폼 하드코딩 3 → env화(기본값 동일)
MIN_VIDEO_HEIGHT = 720       # §4-2-3
MIN_PHOTO_LONG_EDGE = 1280   # §4-2-3

# v1.9 다양성 튜닝 (.env로 override — load_env() 이후 런타임에 읽음)
def cooldown_n() -> int:
    return int(os.environ.get("MIL_FOOTAGE_COOLDOWN", "2"))   # 최근 N개 영상에 쓴 소스는 후순위

def fresh_ratio() -> float:
    return float(os.environ.get("MIL_FRESH_RATIO", "0.4"))    # 영상당 '한 번도 안 쓴 새 소스' 목표 비율


# ══════════════════════════════════════════════════════════════════════════
# v2.8 소프트랭킹 구간 선택 — v2.4 피크윈도우를 전 씬으로 확장
#
#   철학: 지금까지 start_s는 '아무도 화면을 안 본 채 산술로' 정해졌다(fresh=3.0 고정,
#         reuse=next_start 눈먼 전진). 대신 실제 프레임을 보고 그 클립 안에서
#         상대적으로 나은 구간으로 옮긴다.
#
#   ★ 하드블록(skip_ranges)은 폐기됐다 — 다시 넣지 말 것.
#     절대 임계값(edge<0.02 등)으로 구간을 영구 차단하면 오탐 1건의 대가가 비대칭이다:
#     하드블록은 오탐 시 소재가 영영 사라지고(곡예비행 영상 62% 오차단 실측),
#     소프트랭킹은 오탐해도 '조금 덜 좋은 구간'을 고를 뿐 소재는 남는다.
#     그래서 여기선 임계값을 쓰지 않는다. 클립 내부에서 정규화해 '창 순위'만 매긴다.
#     같은 신호가 임계값으로 쓰면 틀리고 비교자로 쓰면 맞는다 — 그게 이 재설계의 전부다.
#
#   ★ 실측 근거 (2026-07-17, KF-21 데모비행 1153s, 설계_구간인덱싱 지상검증 대상):
#       빈 하늘(496~752s): edge 0.0006~0.09 / blob 0.0001~0.20
#       좋은 구간        : edge 0.17~0.34   / blob 0.33~0.52   → 20~100배 차이
#     가중치 47개 조합 전수 시험에서 빈하늘이 상위 10위에 든 경우 0건(최악 39위/70).
#     즉 사각지대 회피는 가중치에 둔감하다 = 튜닝이 필요없다. 임계값 튜닝으로 실패했던
#     하드블록과 갈리는 지점이 정확히 여기다. 가중치를 만지고 싶어지면 과적합을 의심할 것.
#
#   ☞ 한계(알고 쓸 것): presence는 "뭔가 찍혀 있다"까지만 안다. 같은 클립에서
#     격납고 건물(464s, edge 0.34)이 KF-21 지상 클로즈업(352s, 설계문서가 '좋음'으로 지목)을
#     이긴다 — 의미 판별은 물리량 밖이다. 소프트랭킹의 일은 '금맥 채굴'이 아니라
#     '빈 화면에 착지하지 않기'다. 의미 선택은 큐레이션 레이어(설계_구간인덱싱 ①segments)
#     몫이고, 그걸 가중치로 흉내내려 들면 표본 몇 개짜리 과적합이 된다.
# ══════════════════════════════════════════════════════════════════════════

# 특징 순서 고정 — 가중치·바닥 튜플이 전부 이 순서를 따른다.
SCAN_FEATS = ("edge", "blob", "motion", "flash", "fire")

# 정규화 절대 바닥: 클립 내 최대값이 이보다 작으면 "그 특징은 사실상 없다"로 눌러 담는다.
#   v2.4는 `E / (E.max() + 1e-6)`이라 화염이 아예 없는 클립의 노이즈까지 1.0으로 증폭했다.
#   실측: KF-21(화염 0) fire max 0.0080 → 기여도 1.60(!) / K239(진짜 발사) 0.0431 → 1.60.
#   바닥 0.02를 깔면 KF-21은 0.64로 내려가고 K239는 1.60 그대로 — 진짜 화염만 살아남는다.
#   (다만 실측 2개 클립에선 이 보정이 최종 선택을 바꾸지는 않았다. 노이즈 증폭 자체가
#    틀린 계산이라 고친 것이지, 관측된 사고를 고친 게 아니다.)
SCAN_FLOORS = (0.03, 0.05, 0.02, 0.05, 0.02)

SCAN_PROFILES = {
    # 전 씬 기본. 목적은 자극이 아니라 '사각지대 회피' — 빈 하늘·암전·로고/타이틀 카드를 피한다.
    #   motion을 낮게 두는 이유: 정적인 좋은 컷(지상 클로즈업)을 벌주지 않기 위해서.
    "presence": (1.0, 1.0, 0.3, 0.0, 0.0),
    # impact:"high" 씬(HOOK·PROOF 등 편당 2~3개)만. v2.4 가중치를 그대로 두되
    #   presence를 바닥에 깔아 '빈 화면의 섬광·노이즈'가 이기지 않게 한다.
    "impact": (0.4, 0.4, 1.0, 1.3, 1.6),
}


def scan_enabled() -> bool:
    # 비상 탈출구: MIL_SCAN_DISABLE=1 이면 전 구간 스캔 없이 v2.7 산술 동작으로 되돌아간다.
    return _HAS_CV2 and os.environ.get("MIL_SCAN_DISABLE", "") != "1"


def _scan_budget():
    # coarse=파일 전체 훑기(캐시됨) / fine=상위 구간만 촘촘히 재스캔(매번, 싸다)
    return (int(os.environ.get("MIL_SCAN_COARSE", "72")),
            int(os.environ.get("MIL_SCAN_FINE", "28")))


def _impact_weights():
    # v2.4 .env 튜닝 키 호환 유지
    e, b, m, f, r = SCAN_PROFILES["impact"]
    return (e, b,
            float(os.environ.get("MIL_IMPACT_W_MOTION", m)),
            float(os.environ.get("MIL_IMPACT_W_FLASH", f)),
            float(os.environ.get("MIL_IMPACT_W_FIRE", r)))


def _probe_duration(path: str) -> float:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
            capture_output=True, text=True, timeout=30)
        return float(json.loads(out.stdout)["format"]["duration"])
    except Exception:
        return 0.0


def _frame_feats(bgr, prev_gray):
    """프레임 1장 → (edge, blob, motion, flash, fire). 160x90 축소본에서 계산."""
    small = cv2.resize(bgr, (160, 90))
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    g = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    gf = g.astype(_np.float32)
    edge = float(cv2.Canny(g, 60, 160).mean()) / 255.0          # 윤곽 밀도(피사체·질감)
    dev = _np.abs(gf - float(_np.median(gf)))
    blob = float((dev > 40).mean())                              # 배경에서 벗어난 픽셀 = 실루엣
    motion = 0.0 if prev_gray is None else float(_np.abs(gf - prev_gray).mean()) / 255.0
    flash = float((gf > 235).mean())                             # 순간 고휘도(총구화염·폭발)
    H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    fire = float(((H < 30) & (S > 110) & (V > 150)).mean())      # 주황 고채도
    return (edge, blob, motion, flash, fire), gf


def _scan_range(path: str, t0: float, t1: float, n: int, local_motion_s: float = 0.25):
    """[t0,t1)을 n개 지점에서 샘플. 반환 (times, F[n×5]).

    motion은 각 지점에서 local_motion_s 뒤 프레임과의 국소 차분으로 잰다.
    (v2.4는 샘플 간 차분이라, 성긴 스트라이드에선 '움직임'이 아니라 '장면 바뀜'을 쟀다.
     긴 파일을 성기게 훑는 v2.8에선 그 값이 의미를 잃으므로 국소 차분이 필수다.)
    """
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return [], None
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        if not (fps > 0) or fps > 240:
            fps = 30.0
        step = max((t1 - t0) / max(n, 1), 0.05)
        times, rows = [], []
        t = t0
        while t < t1:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
            ok, a = cap.read()
            if not ok:
                break
            fa, ga = _frame_feats(a, None)
            for _ in range(max(1, int(local_motion_s * fps))):   # grab은 디코드만, 변환 없음(쌈)
                cap.grab()
            ok2, b = cap.retrieve()
            if ok2:
                fb, _ = _frame_feats(b, ga)
                # 정지 특징은 두 프레임 중 큰 쪽(순간 섬광을 놓치지 않게), motion은 실측 차분
                f = tuple(fb[i] if i == 2 else max(fa[i], fb[i]) for i in range(5))
            else:
                f = fa
            times.append(round(t, 1))
            rows.append(f)
            t += step
        return times, (_np.array(rows, dtype=_np.float32) if rows else None)
    except Exception:
        return [], None
    finally:
        cap.release()


def _scan_cache_file(path: str, t0: float, t1: float, n: int):
    try:
        st = os.stat(path)
    except OSError:
        return None
    # 내용이 같으면 재사용 — 경로가 아니라 (크기, mtime)으로 키를 만든다.
    #   _library 오염 이력([[mil-library-index-contamination]])상 '같은 경로 = 같은 내용'을 못 믿는다.
    sig = f"{st.st_size}_{int(st.st_mtime)}_{t0:.1f}_{t1:.1f}_{n}_{Path(path).name}"
    return BASE / "_scan_cache" / f"{hashlib.md5(sig.encode()).hexdigest()[:16]}.json"


def _scan_cached(path: str, t0: float, t1: float, n: int):
    """_scan_range + 디스크 캐시. coarse(전체 훑기)·fine(정밀) 양쪽 다 캐시한다.

    대형 원본은 seek 자체가 비싸다(2.6GB/1153s 실측: coarse 72샘플 52초, fine 28샘플 22초).
    라이브러리 소재는 여러 씬·여러 런에서 반복 스캔되므로 캐시가 사실상 필수다.
    """
    cf = _scan_cache_file(path, t0, t1, n)
    if cf and cf.exists():
        try:
            d = json.loads(cf.read_text(encoding="utf-8"))
            return d["times"], _np.array(d["F"], dtype=_np.float32)
        except Exception:
            pass
    times, F = _scan_range(path, t0, t1, n)
    if F is not None and cf:
        try:
            cf.parent.mkdir(parents=True, exist_ok=True)
            cf.write_text(json.dumps({"times": times, "F": F.tolist()}), encoding="utf-8")
        except Exception:
            pass
    return times, F


def _window_score(times, F, weights, win, full, intro_skip, used):
    """창 시작 후보별 점수. 반환 [(score, start)] 내림차순.

    정규화는 '이 클립 안에서'만 한다 → 절대 임계값이 없다 = 아무것도 차단하지 않는다.
    used(이미 이 런에서 쓴 구간)만 제외하는데, 이건 품질 판단이 아니라 중복 방지다.
    """
    W = _np.array(weights, dtype=_np.float32)
    denom = _np.maximum(F.max(axis=0), _np.array(SCAN_FLOORS, dtype=_np.float32))
    score = (F / denom) @ W
    T = _np.array(times)
    out = []
    for s in times:
        if s < intro_skip or s + win > full:
            continue
        if any(s < ue and (s + win) > us for us, ue in used):   # 겹치는 구간은 후보에서 제외
            continue
        m = (T >= s) & (T < s + win)
        if not m.any():
            continue
        out.append((float(score[m].mean()), float(s)))
    out.sort(reverse=True)
    return out


def pick_window(path: str, win: float, full: float, profile: str = "presence",
                used=(), intro_skip: float = 1.0):
    """클립 안에서 win초짜리 '가장 나은' 구간 시작점을 고른다. 실패 시 None(=호출부 산술 유지).

    2단: coarse로 전체를 훑어 상위 구간을 찾고(캐시), 그 근방만 fine으로 촘촘히 재스캔한다.
    v2.4의 180초 상한을 이 2단 구조가 대체한다 — 상한은 긴 원본을 스캔에서 통째로
    제외시켰고(203개 중 67개), 파이프라인이 1153초짜리 KF-21의 500초 빈하늘에 착지해
    그대로 출고된 사고가 정확히 그 구멍이었다.
    """
    if not scan_enabled():
        return None
    if full <= 0 or win <= 0 or full < win + 0.2:
        return None
    weights = _impact_weights() if profile == "impact" else SCAN_PROFILES["presence"]
    n_coarse, n_fine = _scan_budget()
    fine_stride = max(win / 4.0, 0.4)

    if full <= n_fine * fine_stride:          # 짧은 클립은 1단으로 충분(대부분의 다운로드 클립)
        times, F = _scan_cached(path, 0.0, full, max(int(full / fine_stride), 3))
        if F is None or len(times) < 3:
            return None
        ranked = _window_score(times, F, weights, win, full, intro_skip, used)
        return None if not ranked else round(ranked[0][1], 1)

    times, F = _scan_cached(path, 0.0, full, n_coarse)
    if F is None or len(times) < 3:
        return None
    ranked = _window_score(times, F, weights, win, full, intro_skip, used)
    if not ranked:
        return None
    best = ranked[0][1]
    # 정밀 단계: coarse 스트라이드가 성겨서 놓친 창 안쪽 몇 초를 확정한다.
    lo, hi = max(0.0, best - win), min(full, best + 2.0 * win)
    ft, fF = _scan_cached(path, lo, hi, n_fine)
    if fF is None or len(ft) < 3:
        return round(best, 1)
    fine_ranked = _window_score(ft, fF, weights, win, full, intro_skip, used)
    return round((fine_ranked[0][1] if fine_ranked else best), 1)

# ① 제목 액션어휘(방법 3의 조준경): high 씬에서 hint 다음 타이브레이크로 '발사·기동·폭발' 제목 우선.
ACTION_LEXICON = re.compile(
    r"\b(launch(?:ing|es|ed)?|fir(?:e|es|ing)|live[\-\s]?fire|salvo|volley|"
    r"blast|explos|detonat|impact|strike|barrage|muzzle|recoil|"
    r"maneuver|manoeuvre|charg(?:e|ing)|assault|scramble|takeoff|afterburner)\b"
    r"|발사|사격|기동|폭발|화염|돌격|출격|불꽃|섬광",
    re.I,
)

def _action_match(title: str) -> bool:
    return bool(title and ACTION_LEXICON.search(title))

# ---------- 공통 유틸 ----------

def load_env():
    """BASE/.env 를 파싱해 os.environ 에 주입 (기존 값 우선)."""
    env_path = BASE / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


def allow_bysa() -> bool:
    return os.environ.get("MIL_ALLOW_BYSA", "1").strip() != "0"


def license_ok(short_name: str) -> bool:
    """라이선스 화이트리스트 (§4-2-2c, v1.3에서 BY-SA 허용). 거부 조건을 먼저 검사한다."""
    s = (short_name or "").strip()
    if not s:
        return False
    if s.startswith("CC BY-NC"):
        return False
    if "-NC" in s or "-ND" in s or " NC" in s or " ND" in s:
        return False
    if s.startswith("CC BY-SA"):
        return allow_bysa()
    allow_prefixes = ("Public domain", "CC0", "KOGL Type 1", "CC BY")
    return any(s.startswith(p) for p in allow_prefixes)


def license_from_url(url: str):
    """licenseurl(archive.org 등) → license_ok가 아는 short name. 판정 불가 시 None."""
    u = (url or "").lower()
    if not u:
        return None
    if "publicdomain/mark" in u or "publicdomain/1.0" in u or "/publicdomain" in u:
        return "Public domain"
    if "publicdomain/zero" in u or "/zero/1.0" in u:
        return "CC0"
    if "licenses/by-nc" in u or "licenses/by-nd" in u:
        return None  # NC/ND 거부
    if "licenses/by-sa" in u:
        return "CC BY-SA"
    if "licenses/by" in u:
        return "CC BY"
    return None


# ---------- v2.1 시대(era) 설정 (era_styles.json 단일 소스) ----------

_ERA_CFG = None


def era_config():
    global _ERA_CFG
    if _ERA_CFG is None:
        p = BASE / "era_styles.json"
        try:
            _ERA_CFG = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            _ERA_CFG = {}
    return _ERA_CFG


def era_search_terms(era: str):
    """해당 era의 아카이브 검색 보조 토큰(연도·전쟁명). modern/미등록이면 []."""
    if not era or era == "modern":
        return []
    return era_config().get(era, {}).get("search", []) or []


def era_video_min_h() -> int:
    """아카이브 필름은 저해상도 → era 영상 최소높이 완화(기본 360)."""
    return int(era_config().get("_video_min_height", 360))


# ── v3.1 시대 제목 게이트 (mil_029 춘천대첩에서 발견된 3종 오배정의 근본대응) ──
#   증상: era=korean_war 런에 'Duck and Cover'(1951 핵 민방위 만화), 'Signal 30'(교통사고
#   교육영화), 'The Big Lift'(극영화 타이틀카드), 'Japan Maritime Self-Defense US-2'(현대
#   일본 비행정)가 배정됐다. archive.org·Commons 검색이 컬렉션·연도 토큰만으로 넓게 걸리는데
#   제목을 아무도 검증하지 않았기 때문이다. 눈검수가 최종 게이트지만, 후보 단계에서 걸러야
#   재수집 반복이 줄고 풀이 오염되지 않는다.
#   규칙: era 씬의 후보 제목에는 그 시대의 식별 토큰(korea/korean/1950~1953…)이 최소 1개
#   있어야 한다. 'war'처럼 어느 전쟁에나 붙는 일반어는 단독 근거로 쓰지 않는다(베를린 공수
#   영화가 'war'로 통과하던 사례).
_ERA_GENERIC_WORDS = {"war", "army", "navy", "military", "force", "forces", "combat"}

# 현대 제식명이 제목에 있으면 시대 씬에서 배제한다. era_title_ok는 '식별 토큰이 하나라도
# 있으면 통과'라서, Commons의 "K-weapon source K-21 IFV — Republic of Korea MND" 같은
# 현대 홍보 컴필레이션이 제목 속 'Korea' 하나로 1950년 대본을 통과했다(mil_029 s11 실측).
# 지명은 시대를 가리키지 못하므로, 시대를 부정하는 증거를 우선한다.
_MODERN_DESIGNATION_RE = re.compile(
    r"\b(?:k-?\d{1,3}[a-z]?\d?|kf-?\d{2}|fa-?50|f-?\d{2}|kaai|kai\b|"
    r"현무|천궁|천무|현궁|레드백|redback|k-?weapon)\b", re.I)


def modern_designation_in(title: str) -> bool:
    """제목에 현대 무기 제식명이 있는가(시대 씬 배제용)."""
    return bool(_MODERN_DESIGNATION_RE.search(title or ""))


def era_title_tokens(era: str):
    """era 제목 게이트용 식별 토큰. era_styles.json의 title_require가 있으면 그것을 쓰고,
    없으면 search 토큰에서 일반어를 뺀 나머지를 자동 유도한다(신규 시대도 설정 없이 동작)."""
    st = era_config().get(era, {}) or {}
    req = st.get("title_require")
    if req:
        return [str(t).lower() for t in req]
    toks = set()
    for s in st.get("search", []) or []:
        for w in re.findall(r"[A-Za-z]{3,}|\d{4}", str(s)):
            wl = w.lower()
            if wl in _ERA_GENERIC_WORDS:
                continue
            toks.add(wl)
    return sorted(toks)


def era_title_ok(title: str, era: str) -> bool:
    """era 씬 후보의 제목이 그 시대를 실제로 가리키는가. modern·미등록 시대는 항상 통과."""
    if not era or era == "modern":
        return True
    toks = era_title_tokens(era)
    if not toks:
        return True
    t = (title or "").lower()
    return any(tok in t for tok in toks)


def era_filter_cands(cands, era: str, drop_modern_sources: bool = False):
    """era 씬 후보 목록에서 시대 불일치를 제거.

    drop_modern_sources=True면 DVIDS 출신(source_id 'video:'/'image:')도 함께 뺀다.
    v3.0까지 library_find()가 is_era 분기 **밖**에서 호출돼(§collect 1880행), 라이브러리에
    캐시된 DVIDS 현대 영상(M777 사격훈련·우크라이나 레오파르트2·Northern Strike)이 시대
    필터를 통째로 우회해 1950년 대본에 배정됐다. 신규 DVIDS 조회만 막고 캐시는 안 막았던 것.
    """
    if not era or era == "modern":
        return cands
    out = []
    for c in cands or []:
        sid = str(c.get("source_id") or "")
        if drop_modern_sources and (sid.startswith("video:") or sid.startswith("image:")):
            continue
        title = c.get("title") or ""
        if modern_designation_in(title):   # 현대 제식명 = 시대를 부정하는 증거
            continue
        if not era_title_ok(title, era):
            continue
        out.append(c)
    return out


def core_tokens(phrase: str):
    """관련성 후검증용 핵심 토큰 (§4-2-1b): 무기 제식명 우선, 없으면 3자 이상 토큰.

    v2.6: 숫자 우선권을 '제식명'(글자+숫자)으로 좁혔다. v2.5는 숫자가 든 토큰이면 무조건
    우선해서 맨숫자도 핵심 토큰이 됐고, 그 결과 "Leopard 2 tank"의 핵심 토큰이 **"2" 하나**가
    되어 정작 판별력 있는 'Leopard'·'tank'가 버려졌다 — 즉 "2가 들어간 아무거나"와 매칭됐다
    (실측 2026-07-17: 라이브러리 231개 중 96개 매칭). "ADEX 2015 K2"도 연도 '2015'가 핵심
    토큰이 되어 2015년 자료 전부를 물어왔다.
    제식명(K2·KF-21·120mm·현무-5·M1A2)은 글자를 동반한다. 맨숫자는 연도·수량이지 무기가 아니다.
    """
    toks = re.findall(r"[\w가-힣-]+", phrase)
    designation = [t for t in toks
                   if re.search(r"\d", t) and re.search(r"[a-zA-Z가-힣]", t)]
    if designation:
        return designation
    return [t for t in toks if len(t) >= 3] or toks


# v1.9: 지명·관사 등 너무 흔한 토큰 — '단독 매칭 근거' 금지
#  (예: "armored vehicle live fire Korea"가 'Korea'만으로 KF-21 항공기·삼성궁 사당과 매칭되던 오탑재)
# 롱폼 v1.1 (숏폼 v3.3 이식): 각국 함정명 접두 호칭도 같은 종류의 함정이다 — mil_045 실측:
#   alias "ROKS Daejeon"의 'ROKS' 토큰이 라이브러리의 모든 한국 해군함(ROKS Yulgok Yi·
#   ROKS Jeongjo·ROKS Chungmugong Yi Sun-sin 등 전혀 다른 함급)과 단독 매칭돼 축구 경기
#   영상까지 '대구급 호위함'으로 끌려왔다. 'rok'은 이미 막혀 있었지만 'roks'는 다른
#   문자열이라 안 걸렸다 — 같은 버그의 재발.
GENERIC_TOKENS = {
    "korea", "korean", "rok", "republic", "south",
    "the", "and", "for", "with", "from",
    "roks", "rokn", "uss", "hms", "hmcs", "hmnzs", "hmas", "cns", "brp", "arc",
}


def _token_hit(t: str, text_l: str) -> bool:
    """v2.6: 숫자 포함 토큰(= 무기 제식명)은 뒤에 숫자가 더 붙으면 다른 무기다.
    순진한 substring 매칭이던 v2.5는 'k2'가 'k239' 안에 들어있다는 이유로 K2 흑표 검색에
    K239 천무를 물어왔다 — 실측 2026-07-17: "K2 흑표 전차 기동" 매칭 17건 중 10건(59%)이 K239.
    (K2 vs K21/K239, K9 vs K90 …). 뒤에 숫자가 아닌 것(K239T·K2A1 등 파생형)은 같은 무기로 본다."""
    if re.search(r"\d", t):
        return re.search(re.escape(t) + r"(?!\d)", text_l) is not None
    return t in text_l


def relevant(phrase: str, text: str, strict: bool = False) -> bool:
    """strict=True(_library 캐시 매칭): 지명 토큰 단독 매칭 차단 — garbage 대량 억제.
    strict=False(기본): v1.8대로 넓게 매칭. commons는 이미 따옴표 정확검색이라 strict 불필요.
    v2.6: 숫자 토큰 경계 검사 추가(_token_hit) — 호출부 6곳 전부에 적용된다."""
    text_l = (text or "").lower()
    core = [t.lower() for t in core_tokens(phrase)]
    if strict:
        meaningful = [t for t in core if t not in GENERIC_TOKENS]
        core = meaningful or core          # 전부 일반 토큰이면 기존 동작 유지(빈 결과 방지)
    return any(_token_hit(t, text_l) for t in core)


# ── v4.2 요구 화면(shot) ─────────────────────────────────────────────────
_SHOT_VOCAB = None


def shot_vocab() -> dict:
    """shot_vocab.json 단일 소스. 신규 어휘는 JSON에 한 줄 추가 — 코드 수정 불필요."""
    global _SHOT_VOCAB
    if _SHOT_VOCAB is None:
        p = BASE / "shot_vocab.json"
        _SHOT_VOCAB = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return _SHOT_VOCAB


def shot_min() -> int:
    """이 점수 미만은 '약한 후보'. subject만 맞아도 2점이라 기본 2 = 주체는 맞아야 한다."""
    return int(os.environ.get("MIL_SHOT_MIN", "2"))


def scene_shot(footage: dict):
    """footage.shot을 정규화해 반환. 없으면 None(= v4.1과 완전히 동일하게 동작)."""
    sh = (footage or {}).get("shot")
    if not isinstance(sh, dict):
        return None
    out = {k: (str(sh.get(k)).strip().lower() if sh.get(k) else None)
           for k in ("subject", "action", "setting")}
    ex = sh.get("exclude") or []
    out["exclude"] = [str(x).strip().lower() for x in ex if str(x).strip()]
    return out if (out["subject"] or out["action"] or out["setting"] or out["exclude"]) else None


def _vocab_tokens(key: str, group: str = None):
    """어휘 키 → 매칭 토큰들. group 미지정이면 action→setting→exclude_extra 순으로 찾는다.
    사전에 없는 키는 그 문자열 자체를 토큰으로 쓴다(자유어 허용)."""
    v = shot_vocab()
    groups = [group] if group else ["action", "setting", "exclude_extra"]
    for g in groups:
        d = (v.get(g) or {}).get(key)
        if d:
            return [t.lower() for t in (d.get("ko") or []) + (d.get("en") or [])]
    return [key.lower()] if key else []


def _subject_tokens(subject: str, aliases: dict):
    """subject 슬러그 → 별칭들의 핵심 토큰(일반 토큰 제외). 슬러그가 아니면 그대로 토큰화."""
    phrases = aliases.get(subject) or [subject]
    toks = {t.lower() for p in phrases for t in core_tokens(p)}
    return (toks - GENERIC_TOKENS) or toks


# evidence는 '없다'를 자주 쓴다 — "관중·천막 없는 구간", "국기·부대마크 없음", "no flags".
#   순진한 substring 매칭은 이 부정 서술을 긍정 히트로 읽어 **정답 소재를 exclude로 죽인다**
#   (실측 2026-09-08: "K2 흑표 차체 흙먼지 기동 … (관중·천막 없는 구간)"이 static_display에
#    걸려 -1점으로 최하위 추락). 토큰 주변 윈도우에 부정어가 있으면 히트로 치지 않는다.
_NEG_AFTER = re.compile(r"^.{0,10}?(없|아니|제외|미노출|안\s)")
_NEG_BEFORE = re.compile(r"(없|아니|제외|no|not|without|free of|absent)\s*\S{0,10}$")


def _ctx_hit(tok: str, hay: str) -> bool:
    """부정 문맥을 배제한 어휘 매칭. tok이 나오는 모든 위치를 보고 하나라도 긍정이면 True."""
    i = hay.find(tok)
    while i != -1:
        after = hay[i + len(tok): i + len(tok) + 14]
        before = hay[max(0, i - 14): i]
        if not (_NEG_AFTER.match(after) or _NEG_BEFORE.search(before)):
            return True
        i = hay.find(tok, i + 1)
    return False


def _subject_hit(hay: str, shot: dict, aliases: dict) -> bool:
    if not shot.get("subject"):
        return True
    return any(_token_hit(t, hay) for t in _subject_tokens(shot["subject"], aliases))


def _shot_signals(hay: str, shot: dict, aliases: dict) -> int:
    """제목/서술 문자열 하나에 대한 신호 점수(subject 2 · action 2 · setting 1)."""
    sc = 0
    if shot.get("subject"):
        if _subject_hit(hay, shot, aliases):
            sc += 2
    if shot.get("action") and any(_ctx_hit(t, hay) for t in _vocab_tokens(shot["action"], "action")):
        sc += 2
    if shot.get("setting") and any(_ctx_hit(t, hay) for t in _vocab_tokens(shot["setting"], "setting")):
        sc += 1
    return sc


def shot_axes(c: dict, shot: dict, aliases: dict) -> dict:
    """어느 축이 맞았나 — 점수만으로는 '주체만 맞고 행위는 전혀 다름'을 구분할 수 없다.
    검수 시트와 shot_low 판정이 읽는다."""
    hay = ((c.get("title") or "") + " " + " ".join(c.get("seen") or [])).lower()
    out = {}
    if shot.get("subject"):
        out["subject"] = _subject_hit(hay, shot, aliases)
    if shot.get("action"):
        out["action"] = any(_ctx_hit(t, hay) for t in _vocab_tokens(shot["action"], "action"))
    if shot.get("setting"):
        out["setting"] = any(_ctx_hit(t, hay) for t in _vocab_tokens(shot["setting"], "setting"))
    return out


def shot_score(c: dict, shot: dict, aliases: dict) -> int:
    """후보가 '요구 화면'에 얼마나 맞는가. exclude 히트는 큰 음수(하드 제거 대상).

    제목만으로 계산한 점수보다 (제목+서술) 점수가 높으면 +1 — 그 신호는 사람이 픽셀을 보고
    쓴 evidence에서 나온 것이라 제목 문자열보다 신뢰도가 높다.
    """
    title_l = (c.get("title") or "").lower()
    seen_l = " ".join(c.get("seen") or []).lower()
    hay = (title_l + " " + seen_l).strip()

    base = _shot_signals(hay, shot, aliases)
    if seen_l and base > _shot_signals(title_l, shot, aliases):
        base += 1

    # ── 주체 게이트 ──
    #   action·setting만 맞고 subject가 틀린 후보는 "발사 장면이긴 한데 다른 무기"다.
    #   실측(2026-09-08 회귀): hyunmoo 씬에 세종대왕함, naval_mine 씬에 USS Chief가
    #   action+setting만으로 임계를 넘겨 통과했다. 주체 오배정이 가장 치명적이므로
    #   점수를 임계 아래로 끌어내린다(만점 조합 4점 - 3 = 1 < 임계 2).
    #   완전 배제가 아니라 최하위다 — 강한 후보가 없으면 relaxed 모드가 열고 shot_low를 남긴다.
    if not _subject_hit(hay, shot, aliases):
        base -= 3

    # exclude는 별도 차원이다. 하드 제거 대상이므로 다른 감점과 섞이지 않게 크게 뺀다.
    for ex in shot.get("exclude") or []:
        if any(_ctx_hit(t, hay) for t in _vocab_tokens(ex)):
            base -= 100
    return base


def slugify(phrase: str) -> str:
    s = re.sub(r"[^\w가-힣]+", "-", phrase.lower()).strip("-")
    return s or "misc"


def api_get(url, params, headers=None):
    try:
        r = requests.get(url, params=params, headers=headers or UA, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise RuntimeError(f"API 호출 실패 {url}: {e}")


# Commons 제목 블록리스트 — 한국전쟁 검색 시 딸려오는 중국 항미원조(반미) 기념관/유물 사진 차단
# v2.4: "SAM"(M-SAM·KM-SAM 등) 검색이 토론토 Sam Smith Park 조류 사진과 동음이의 오탐(mil_002 재작업 중 발견) — 학명 태그 새사진 대량 차단
COMMONS_TITLE_BLOCK = ("resist u.s. aggression", "resist us aggression",
                       "aid korea", "chinese people's volunteer", "抗美援朝",
                       "sam smith park", "sam smith toronto")


# ---------- Wikimedia Commons (§4-2-2) ----------

def commons_search(phrase: str, kind: str, limit: int = None, min_h: int = None):
    """kind: 'video' | 'photo'. 따옴표 정확매칭 + filetype 필터. 반환: 후보 리스트.
    min_h: 영상 최소 높이(기본 720, era 저해상도 아카이브 대응으로 완화 가능).

    관련성 검사(v1.1): Commons는 따옴표 검색 자체가 정확매칭이므로 제목/설명 미매칭이어도
    폐기하지 않고 후순위로만 강등한다 (DVIDS와 다름 — DVIDS는 느슨한 매칭이라 폐기)."""
    if limit is None:
        limit = 40 if kind == "video" else 50   # v1.9: 영상 20→40 (다양성 위해 후보 풀 확대)
    ftype = "video" if kind == "video" else "bitmap"
    gsr = f'"{phrase}" filetype:{ftype}'
    data = api_get(COMMONS_API, {
        "action": "query", "format": "json",
        "generator": "search", "gsrsearch": gsr,
        "gsrnamespace": 6, "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata",
    })
    items = []
    for page in data.get("query", {}).get("pages", {}).values():
        ii = (page.get("imageinfo") or [{}])[0]
        em = ii.get("extmetadata", {}) or {}
        lic = (em.get("LicenseShortName", {}) or {}).get("value", "")
        artist = re.sub(r"<[^>]+>", "", (em.get("Artist", {}) or {}).get("value", "")).strip()
        title = page.get("title", "")
        w, h = ii.get("width") or 0, ii.get("height") or 0
        item = {
            "source": "commons", "kind": kind, "title": title,
            "url": ii.get("url"), "page_url": ii.get("descriptionurl"),
            "width": w, "height": h,
            "duration_s": round(float(ii.get("duration") or 0), 1),
            "license": lic, "credit": artist,
            "source_id": f"commons:{title}",
        }
        # 필터: 라이선스 → 크기 (관련성은 폐기 대신 순위 강등)
        if not license_ok(lic):
            continue
        # 제목 블록리스트 — Commons '한국전쟁' 사진풀은 중국 항미원조기념관(반미 선전) 업로드가 다수.
        #   국뽕 밀리터리엔 부적절 → 제목 기반 원천 차단.
        if any(b in title.lower() for b in COMMONS_TITLE_BLOCK):
            continue
        # 대용량 영상 배제 — Commons 원본은 1GB+도 흔함(5초 클립에 과함, 빌드 부담)
        if kind == "video":
            sz = int(ii.get("size") or 0)
            if sz > ARCHIVE_MAX_MB * 1048576:
                continue
        if kind == "video" and h < (min_h if min_h is not None else MIN_VIDEO_HEIGHT):
            continue
        if kind == "photo" and max(w, h) < MIN_PHOTO_LONG_EDGE:
            continue
        desc = re.sub(r"<[^>]+>", "", (em.get("ImageDescription", {}) or {}).get("value", ""))
        item["relevant"] = relevant(phrase, title) or relevant(phrase, desc)
        items.append(item)
    # 정렬: 관련성 매칭 우선 → 영상은 길이 긴 순(구간 잘라쓰기 유리), 사진은 해상도 순
    items.sort(key=lambda x: (x["relevant"],
                              x["duration_s"] if kind == "video" else max(x["width"], x["height"])),
               reverse=True)
    return items


# ---------- Openverse (v1.3 — Flickr CC/PD 등 통합검색) ----------

OPENVERSE_API = "https://api.openverse.org/v1/images/"
_OV_LICENSE_MAP = {"pdm": "Public domain", "cc0": "CC0", "by": "CC BY", "by-sa": "CC BY-SA"}


def openverse_search(phrase: str, limit: int = 20):
    """상업+수정 가능 라이선스만 요청. wikimedia 제공분은 Commons 직접 검색과 중복이라 제외."""
    data = api_get(OPENVERSE_API, {
        "q": phrase, "license_type": "commercial,modification", "page_size": limit})
    items = []
    for r in data.get("results", []):
        if r.get("source") == "wikimedia":
            continue
        lic_code = (r.get("license") or "").lower()
        lic = _OV_LICENSE_MAP.get(lic_code)
        if lic is None:
            continue
        if lic == "CC BY-SA" and not allow_bysa():
            continue
        w, h = r.get("width") or 0, r.get("height") or 0
        if max(w, h) < MIN_PHOTO_LONG_EDGE:
            continue
        title = r.get("title") or ""
        items.append({
            "source": "openverse", "kind": "photo", "title": title,
            "url": r.get("url"), "page_url": r.get("foreign_landing_url"),
            "width": w, "height": h, "duration_s": 0,
            "license": f'{lic} {r.get("license_version") or ""}'.strip(),
            "credit": r.get("creator") or "", "source_id": f'openverse:{r.get("id")}',
            "relevant": relevant(phrase, title),
        })
    items.sort(key=lambda x: (x["relevant"], max(x["width"], x["height"])), reverse=True)
    return items


# ---------- 무료스톡 (v3.0 — 개념 b-roll 전용) ----------
#
# ⚠️ 사용 범위 제한: concept 씬(concepts.json의 stock_ok=true)에서만 호출된다.
#    주제 무기 씬에 스톡이 섞이면 "K9 영상인 줄 알았는데 스톡 전차"가 되므로 라우팅으로 차단.
# 라이선스(2026-07-20 확인): Pexels License / Pixabay Content License 모두 상업이용 무료·
#    출처표시 불필요. 단 ①상표·로고가 찍힌 클립은 상품화 금지 ②식별 가능한 인물은 모델릴리스
#    미보장 → 인물 클로즈업은 아래 블록리스트로 자동 제외하고, 캡션에 소재 출처를 남긴다.
STOCK_TITLE_BLOCK = ("portrait", "model posing", "woman smiling", "man smiling",
                     "selfie", "influencer", "yoga", "dancing", "kissing",
                     "family", "couple", "child", "kids", "baby", "wedding",
                     # v3.0 실측(2026-07-20): archive_document가 "a business woman examining
                     # the documents"(사무실 스톡)를 물어왔다. 밀리터리 톤에서 사무실 라이프
                     # 스타일 컷은 전차 오배정만큼 몰입을 깬다.
                     "business woman", "businesswoman", "business man", "businessman",
                     "office worker", "coworkers", "team meeting", "startup",
                     # 롱폼 v1.1 (숏폼 v3.4 이식) 실측(2026-08-04, mil_051): press_briefing의
                     # 검색어 "press briefing podium"이 Pixabay 태그 "kettlebell clean and
                     # press"에 'press' 하나로 매칭돼 **케틀벨 운동 영상**이 방사청 발표 씬에
                     # 배정됐다. 같은 런에서 engineer_design은 "a blacksmith drawing a
                     # blueprint"(대장간)를 물어왔다. 운동·요리·수공예는 스톡에서 '일반 명사
                     # 한 개'로 쉽게 걸리는 3대 함정.
                     "kettlebell", "dumbbell", "barbell", "gym", "workout", "fitness",
                     "exercise", "training session", "blacksmith", "forge", "anvil",
                     "cooking", "kitchen", "chef", "recipe", "grill", "barbecue")

PEXELS_VIDEO_API = "https://api.pexels.com/videos/search"
PEXELS_PHOTO_API = "https://api.pexels.com/v1/search"
PIXABAY_VIDEO_API = "https://pixabay.com/api/videos/"
PIXABAY_PHOTO_API = "https://pixabay.com/api/"


def stock_enabled() -> bool:
    return os.environ.get("MIL_ALLOW_STOCK", "1").strip() != "0"


# 스톡 검색어에 흔히 섞이는 무의미 토큰 — 이것만 맞은 건 '맞은 게 아니다'.
# 실측(2026-07-20): "control room operators screens"가 Pixabay 태그 "cat, couch, pet,
# living room, cozy"와 'room' 하나로 매칭돼 **고양이 영상**이 지휘통제소 씬에 배정됐다.
STOCK_GENERIC_TOKENS = {
    "room", "close", "view", "screen", "screens", "person", "people",
    "modern", "indoor", "indoors", "outdoor", "old", "new", "high",
    "day", "night", "shot", "footage", "video", "background",
}


def _stock_relevant(phrase: str, title: str) -> bool:
    """스톡 전용 관련성 — 일반 토큰 단독 매칭을 근거로 인정하지 않는다.
    Pexels·Pixabay는 정확매칭이 없으면 느슨하게 관련된 걸 상위에 올리므로,
    '판별력 있는 토큰이 하나라도 맞았는가'를 따로 본다."""
    title_l = (title or "").lower()
    core = [t.lower() for t in core_tokens(phrase)]
    meaningful = [t for t in core if t not in STOCK_GENERIC_TOKENS]
    if not meaningful:                    # 검색어가 전부 일반어면 기존 판정으로
        return relevant(phrase, title)
    return any(_token_hit(t, title_l) for t in meaningful)


def _slug_title(page_url: str) -> str:
    """Pexels 페이지 URL 슬러그 → 사람이 읽는 제목.
    https://www.pexels.com/video/woman-browsing-a-magazine-6793083/ → 'woman browsing a magazine'
    alt가 비었을 때 내용을 알 수 있는 유일한 단서이고, 인물 차단의 근거이기도 하다."""
    if not page_url:
        return ""
    slug = [p for p in str(page_url).rstrip("/").split("/") if p]
    if not slug:
        return ""
    parts = slug[-1].split("-")
    if parts and parts[-1].isdigit():   # 끝의 asset id 제거
        parts = parts[:-1]
    return " ".join(parts)


def _stock_title_blocked(title: str) -> bool:
    t = (title or "").lower()
    return any(b in t for b in STOCK_TITLE_BLOCK)


def pexels_search(phrase: str, kind: str = "video", limit: int = 15):
    """Pexels 개념 b-roll. 키 없으면 조용히 [] (현행 무영향)."""
    key = os.environ.get("PEXELS_API_KEY", "").strip()
    if not key or not stock_enabled():
        return []
    api = PEXELS_VIDEO_API if kind == "video" else PEXELS_PHOTO_API
    try:
        # v1.4: 롱폼 캔버스는 1920×1080이다. v1.3까지 숏폼에서 물려받은 "portrait"를 그대로
        #   보내 **세로만** 받아왔고(millong_001 세로 14씬 중 10씬이 이 경로), 후보가 전부
        #   세로면 v1.3의 "가로 후보가 있으면 세로 금지" 규칙은 발동할 수가 없다.
        data = api_get(api, {"query": phrase, "per_page": limit, "orientation": "landscape"},
                       headers={"Authorization": key})
    except RuntimeError:
        # 스톡은 보조 소스 — 실패해도 파이프라인을 세우지 않는다
        return []
    items = []
    if kind == "video":
        for r in data.get("videos", []):
            # ★ alt는 자주 비어 있다. 그때 phrase를 제목으로 쓰면 ①검수시트에 검색어만 뜨고
            #   ②"woman browsing a magazine" 같은 인물 클립이 블록리스트를 그냥 통과한다
            #   (실측: 첫 테스트에서 인물 클립이 통과됨). URL 슬러그가 실제 내용을 담고 있다.
            title = r.get("alt") or _slug_title(r.get("url")) or phrase
            if _stock_title_blocked(title):
                continue
            files = [f for f in (r.get("video_files") or [])
                     if (f.get("height") or 0) >= MIN_VIDEO_HEIGHT]
            if not files:
                continue
            # ★ 출력이 1080×1920이라 짧은 변이 1080 미만이면 확대되어 뭉갠다.
            #   height만 보면 720×1280 세로 클립이 통과해 폭이 1.5배 확대된다(실측 버그).
            #   짧은 변 기준으로 걸러야 세로·가로 둘 다 무손실.
            hd = [f for f in files
                  if min(f.get("width") or 0, f.get("height") or 0) >= 1080]
            f = (min(hd, key=lambda x: (x.get("width") or 0) * (x.get("height") or 0)) if hd
                 else max(files, key=lambda x: (x.get("width") or 0) * (x.get("height") or 0)))
            if not _stock_relevant(phrase, title):
                # 판별력 있는 공통 토큰 0개 = 검색어와 무관한 채움 결과. 카드로 떨어지는 게 낫다
                # (엉뚱한 화면보다 [CONCEPT-EMPTY] 경고가 정직하다).
                continue
            items.append({
                "source": "pexels", "kind": "video", "title": title,
                "url": f.get("link"), "page_url": r.get("url"),
                "width": f.get("width") or 0, "height": f.get("height") or 0,
                "duration_s": float(r.get("duration") or 0),
                "license": "Pexels License", "credit": (r.get("user") or {}).get("name", ""),
                "source_id": f'pexels:{r.get("id")}', "stock": True,
                "relevant": relevant(phrase, title),
            })
    else:
        for r in data.get("photos", []):
            title = r.get("alt") or phrase
            if _stock_title_blocked(title):
                continue
            if max(r.get("width") or 0, r.get("height") or 0) < MIN_PHOTO_LONG_EDGE:
                continue
            items.append({
                "source": "pexels", "kind": "photo", "title": title,
                "url": (r.get("src") or {}).get("large2x") or (r.get("src") or {}).get("original"),
                "page_url": r.get("url"),
                "width": r.get("width") or 0, "height": r.get("height") or 0, "duration_s": 0,
                "license": "Pexels License", "credit": r.get("photographer", ""),
                "source_id": f'pexels:{r.get("id")}', "stock": True,
                "relevant": relevant(phrase, title),
            })
    items.sort(key=lambda x: (x["relevant"], x.get("duration_s", 0)), reverse=True)
    return items


def pixabay_search(phrase: str, kind: str = "video", limit: int = 15):
    """Pixabay 개념 b-roll. 키 없으면 조용히 [] (현행 무영향)."""
    key = os.environ.get("PIXABAY_API_KEY", "").strip()
    if not key or not stock_enabled():
        return []
    api = PIXABAY_VIDEO_API if kind == "video" else PIXABAY_PHOTO_API
    params = {"key": key, "q": phrase, "per_page": limit, "safesearch": "true"}
    if kind == "photo":
        params["image_type"] = "photo"
    try:
        data = api_get(api, params)
    except RuntimeError:
        return []
    items = []
    for r in data.get("hits", []):
        title = r.get("tags") or phrase
        if _stock_title_blocked(title):
            continue
        if kind == "video":
            vs = r.get("videos") or {}
            cand = vs.get("medium") or vs.get("large") or vs.get("small") or {}
            if (cand.get("height") or 0) < MIN_VIDEO_HEIGHT:
                continue
            if not _stock_relevant(phrase, title):
                continue
            items.append({
                "source": "pixabay", "kind": "video", "title": title,
                "url": cand.get("url"), "page_url": r.get("pageURL"),
                "width": cand.get("width") or 0, "height": cand.get("height") or 0,
                "duration_s": float(r.get("duration") or 0),
                "license": "Pixabay Content License", "credit": r.get("user", ""),
                "source_id": f'pixabay:{r.get("id")}', "stock": True,
                "relevant": relevant(phrase, title),
            })
        else:
            if max(r.get("imageWidth") or 0, r.get("imageHeight") or 0) < MIN_PHOTO_LONG_EDGE:
                continue
            items.append({
                "source": "pixabay", "kind": "photo", "title": title,
                "url": r.get("largeImageURL"), "page_url": r.get("pageURL"),
                "width": r.get("imageWidth") or 0, "height": r.get("imageHeight") or 0,
                "duration_s": 0,
                "license": "Pixabay Content License", "credit": r.get("user", ""),
                "source_id": f'pixabay:{r.get("id")}', "stock": True,
                "relevant": relevant(phrase, title),
            })
    items.sort(key=lambda x: (x["relevant"], x.get("duration_s", 0)), reverse=True)
    return items


# ---------- 로컬 스톡 (v1.8 — 유튜브_자동화 이미지 438장) ----------

LOCAL_STOCK = BASE.parent / "유튜브_자동화" / "output" / "images"


def _stock_license(folder: Path, filename: str):
    """rename_log의 원본(Wikimedia)명으로 Commons 라이선스 역추적. 실패 시 None(=채택 불가)."""
    log = folder / "_rename_log.json"
    if not log.exists():
        return None, None
    try:
        entries = json.loads(log.read_text(encoding="utf-8"))
        old_name = next(e["old"] for e in entries if e.get("new") == filename)
    except (StopIteration, Exception):
        return None, None
    # 원본명은 잘려있을 수 있음 → 번호 제거·언더스코어→공백 후 구문 검색
    stem = re.sub(r"^\d+_", "", Path(old_name).stem).replace("_", " ").strip()
    if len(stem) < 8:
        return None, None
    try:
        data = api_get(COMMONS_API, {
            "action": "query", "format": "json", "generator": "search",
            "gsrsearch": f'"{stem}"', "gsrnamespace": 6, "gsrlimit": 1,
            "prop": "imageinfo", "iiprop": "url|extmetadata"})
        page = next(iter(data.get("query", {}).get("pages", {}).values()))
        em = (page.get("imageinfo") or [{}])[0].get("extmetadata", {}) or {}
        lic = (em.get("LicenseShortName", {}) or {}).get("value", "")
        artist = re.sub(r"<[^>]+>", "", (em.get("Artist", {}) or {}).get("value", "")).strip()
        return (lic if license_ok(lic) else None), artist
    except Exception:
        return None, None


def local_stock_search(phrase: str, hint: str = None, limit: int = 3):
    """파일명 키워드 매칭 → 라이선스 역추적 성공분만 반환 (최대 limit개 — API 절약)."""
    if not LOCAL_STOCK.exists():
        return []
    terms = [t.lower() for t in core_tokens(phrase)]
    hint_re = re.compile(hint, re.I) if hint else None
    matches = []
    for f in LOCAL_STOCK.glob("*/*.jpg"):
        name = f.stem.lower()
        if not any(t in name for t in terms):
            continue
        matches.append((0 if (hint_re and hint_re.search(name)) else 1, f))
    matches.sort()
    items = []
    for _, f in matches:
        if len(items) >= limit:
            break
        lic, artist = _stock_license(f.parent, f.name)
        if not lic:
            continue
        try:
            from PIL import Image
            w, h = Image.open(f).size
        except Exception:
            w = h = 0
        if max(w, h) < MIN_PHOTO_LONG_EDGE:
            continue
        items.append({"source": "local_stock", "kind": "photo", "title": f.name,
                      "url": None, "page_url": "", "width": w, "height": h,
                      "duration_s": 0, "license": lic, "credit": artist,
                      "source_id": f"local:{f.parent.name}/{f.name}",
                      "abs": str(f), "relevant": True})
    return items


# ---------- DVIDS (§4-2-1, §5-1) ----------

def dvids_key():
    return os.environ.get("DVIDS_API_KEY", "").strip()


def dvids_search(phrase: str, country: str, media: str, limit: int = 40):
    """media: 'video' | 'image'. 따옴표 정확매칭 + country 별도 파라미터."""
    key = dvids_key()
    if not key:
        return []
    params = {"q": f'"{phrase}"', "type": media, "max_results": limit, "api_key": key}
    if country:
        params["country"] = country
    data = api_get(DVIDS_SEARCH, params)
    items = []
    for r in data.get("results", []):
        meta_text = " ".join(str(r.get(k, "")) for k in ("title", "keywords", "short_description"))
        if not relevant(phrase, meta_text):   # §4-2-1b 관련성 후검증 — DVIDS는 미통과 시 폐기
            continue
        items.append({
            "source": "dvids", "kind": "video" if media == "video" else "photo",
            "title": r.get("title", ""),
            "source_id": r.get("id", ""),
            "page_url": f"https://www.dvidshub.net/{media}/{str(r.get('id','')).split(':')[-1]}",
            "duration_s": round(float(r.get("duration") or 0), 1),
            "width": 0, "height": 1080 if r.get("hd") else 720,
            "license": "public_domain", "credit": r.get("credit", ""),
            "country": r.get("country", ""),
        })
    return items


def dvids_download_url(asset_id: str):
    """Asset API files[] 중 height≥720에서 파일크기 최소 항목 선택 (§5-1)."""
    key = dvids_key()
    data = api_get(DVIDS_ASSET, {"id": asset_id, "api_key": key})
    res = data.get("results", {}) or {}
    files = [f for f in (res.get("files") or []) if (f.get("height") or 0) >= MIN_VIDEO_HEIGHT]
    if not files:
        return None, res
    best = min(files, key=lambda f: f.get("size") or 1 << 60)
    return best.get("src"), res


# ---------- Internet Archive (v2.1 — 고전/시대 영상) ----------

_ARCHIVE_VIDEO_FMT = ("512kb mpeg4", "h.264", "mpeg4", "hd mp4", "mp4", "ia mp4")


_ARCHIVE_META_CACHE = {}   # identifier → metadata json (run 내 중복 메타호출 제거 = 속도)


def _archive_pick_file(identifier: str, min_h: int):
    """metadata API로 재생 가능한 mp4 계열 파생본 선택 + PD/CC 라이선스 확정.
    반환: (download_url, license_short, width, height, duration_s, large) 또는 (None,...,False).
    large=True면 소형 파생본이 없어 대용량 원본을 골랐다는 뜻 — 호출부는 전체 다운로드 대신
    archive_range_download()로 필요한 구간만 range-seek해야 한다(v2.2)."""
    data = _ARCHIVE_META_CACHE.get(identifier)
    if data is None:
        try:
            data = api_get(f"{ARCHIVE_META}/{identifier}", {})
        except RuntimeError:
            _ARCHIVE_META_CACHE[identifier] = {}
            return None, None, 0, 0, 0, False
        _ARCHIVE_META_CACHE[identifier] = data
    if not data:
        return None, None, 0, 0, 0, False
    meta = data.get("metadata", {}) or {}
    collections = meta.get("collection") or []
    if isinstance(collections, str):
        collections = [collections]
    # 라이선스 판정: licenseurl → 없으면 PD 컬렉션 소속 → 없으면 저작권상태 필드
    lic = license_from_url(meta.get("licenseurl", ""))
    if lic is None and (set(c.lower() for c in collections) & {c.lower() for c in ARCHIVE_PD_COLLECTIONS}):
        lic = "Public domain"
    if lic is None:
        status = str(meta.get("possible-copyright-status", "")).lower()
        if "not_in_copyright" in status or "no known copyright" in status:
            lic = "Public domain"
    if lic is None or not license_ok(lic):
        return None, None, 0, 0, 0, False   # 라이선스 불명/부적합 = 거부(원칙 유지)

    files = data.get("files", []) or []
    dur = 0.0
    for f in files:                       # 원본에서 길이 확보
        if f.get("length"):
            try:
                parts = str(f["length"]).split(":")
                dur = max(dur, sum(float(x) * 60 ** i for i, x in enumerate(reversed(parts))))
            except ValueError:
                pass
    # ★속도: 5초 클립+세로크롭+필름그레인엔 저용량 파생본이 최적. 최소높이(240)↑ +
    #   **크기 상한 이하**에서 가장 작은 파일(archive '512Kb MPEG4' 등)을 우선 채택.
    # v2.2: 소형 파생본이 하나도 없는 항목은(예전엔 스킵) 대용량 원본 중 최소 크기를
    #   large=True 후보로 승격 — 전체 다운로드 대신 range-seek로 구간만 떼어온다.
    FLOOR_H = min(240, min_h)
    MAX_BYTES = int(os.environ.get("MIL_ARCHIVE_MAX_MB", "180")) * 1024 * 1024
    best = None         # 소형 파생본 중 최소 (size, name, w, h)
    best_large = None   # 대용량 원본 중 최소 (size, name, w, h) — 소형본 없을 때만 사용
    for f in files:
        fmt = str(f.get("format", "")).lower()
        name = f.get("name", "")
        if not name.lower().endswith((".mp4", ".m4v")):
            continue
        if not any(k in fmt for k in _ARCHIVE_VIDEO_FMT) and "mp4" not in fmt:
            continue
        h = int(float(f.get("height") or 0))
        w = int(float(f.get("width") or 0))
        size = int(float(f.get("size") or 0))
        if h and h < FLOOR_H:            # 240p 미만만 배제(그 외 저용량 우선)
            continue
        key = size if size > 0 else (1 << 50)   # 크기 미상은 최후순위
        if size and size > MAX_BYTES:    # 소형 파생본 상한 초과 → range-seek 후보 풀로
            if best_large is None or key < best_large[0]:
                best_large = (key, name, w, h)
            continue
        if best is None or key < best[0]:
            best = (key, name, w, h)
    if best:
        _, name, w, h = best
        url = f"{ARCHIVE_DL}/{identifier}/{urllib.parse.quote(name)}"
        return url, lic, w, h, round(dur, 1), False
    if best_large:
        _, name, w, h = best_large
        url = f"{ARCHIVE_DL}/{identifier}/{urllib.parse.quote(name)}"
        return url, lic, w, h, round(dur, 1), True
    return None, None, 0, 0, 0, False


def archive_search(phrase: str, era: str, limit: int = 6, min_h: int = None):
    """Internet Archive 영상 검색(era 토큰 결합). 라이선스 확정된 PD/CC만 반환.
    부수효과 없음(다운로드 X) — url은 collect 단계에서 download()가 받는다."""
    min_h = min_h if min_h is not None else era_video_min_h()
    qparts = [f'"{phrase}"', "mediatype:movies"]
    terms = era_search_terms(era)
    if terms:
        qparts.append("(" + " OR ".join(f'"{t}"' for t in terms) + ")")
    params = {"q": " AND ".join(qparts),
              "fl[]": ["identifier", "title", "year", "downloads"],
              "rows": limit, "sort[]": "downloads desc", "output": "json"}
    try:
        data = api_get(ARCHIVE_SEARCH, params)
    except RuntimeError:
        return [], 0
    docs = (data.get("response", {}) or {}).get("docs", []) or []
    items, manual = [], 0
    for d in docs:
        ident = d.get("identifier")
        if not ident:
            continue
        url, lic, w, h, dur, large = _archive_pick_file(ident, min_h)
        if not url:
            manual += 1        # 검색엔 잡혔으나 라이선스 미확정 → dry-run 카운트만
            continue
        title = d.get("title") if isinstance(d.get("title"), str) else ident
        items.append({
            "source": "archive", "kind": "video", "title": title,
            "url": url, "page_url": f"https://archive.org/details/{ident}",
            "width": w, "height": h, "duration_s": dur,
            "license": lic, "credit": "Internet Archive", "source_id": f"archive:{ident}",
            "era_source": True, "relevant": True, "archive_large": large,
        })
    return items, manual


# ---------- NARA 미 국립기록원 (v2.1 — NARA_API_KEY 있을 때만, Phase 2) ----------

def nara_key():
    return os.environ.get("NARA_API_KEY", "").strip()


def nara_search(phrase: str, era: str, limit: int = 10, min_h: int = None):
    """NARA Catalog API 무빙이미지 검색. 키 없으면 조용히 [] (Phase 2 활성화 지점).
    연방정부 제작물이라 PD 확정. 온라인 재생용 mp4 오브젝트만 채택."""
    key = nara_key()
    if not key:
        return []
    min_h = min_h if min_h is not None else era_video_min_h()
    terms = era_search_terms(era)
    q = phrase + (" " + " ".join(terms[:2]) if terms else "")
    try:
        data = api_get(NARA_API, {"q": q, "recordType": "item", "objectType": "moving image",
                                  "limit": limit},
                       headers={**UA, "x-api-key": key})
    except RuntimeError:
        return []
    items = []
    for hit in (data.get("body", {}) or {}).get("hits", {}).get("hits", []) or []:
        rec = hit.get("_source", {}) or {}
        md = rec.get("record", {}) or {}
        objs = rec.get("digitalObjects", []) or md.get("digitalObjects", []) or []
        naid = md.get("naId") or hit.get("_id")
        mp4 = next((o.get("objectUrl") for o in objs
                    if str(o.get("objectUrl", "")).lower().endswith(".mp4")), None)
        if not mp4:
            continue
        items.append({
            "source": "nara", "kind": "video",
            "title": md.get("title") or f"NARA {naid}",
            "url": mp4, "page_url": f"https://catalog.archives.gov/id/{naid}",
            "width": 0, "height": 0, "duration_s": 0,
            "license": "Public domain", "credit": "U.S. National Archives (NARA)",
            "source_id": f"nara:{naid}", "era_source": True, "relevant": True,
        })
    return items


# ---------- e영상역사관/대한뉴스 (v2.1 — 공공누리 제1유형, 한국 역사영상 discovery) ----------
# data.go.kr "한국정책방송원_e영상역사관 정보 조회 서비스"(dataset 15137073, REST/JSON).
# 대한뉴스·국가기록영상은 공공누리 제1유형(출처표시/상업이용/변형 허용) = license_ok "KOGL Type 1".
# ★실측 스키마(2026-07-12, 키로 확정):
#   엔드포인트: http://apis.data.go.kr/1371037/ktvHistory/{dhNewsList|videoList|photoList}
#   필수 파라미터: serviceKey, startDate, endDate (YYYYMMDD) ← 없으면 전건 0건
#   ★검색 파라미터: title(제목검색) 또는 keyword(태그검색) — searchWord는 무시됨(2026-07-13 실측).
#   응답: response.body.items.item[] / 필드 title·url(재생페이지)·imgUrl·playTime(초)·contents·pk
#   ⚠️ url이 재생페이지(브라우저 세션 필요)라 **직접 다운로드 불가** → 이 어댑터는 discovery 전용.
#      실제 취득은 사람이 페이지에서 받아 ehistory_intake_v1.0.py로 반입(공공누리 1유형).
# 키(EHISTORY_API_KEY) 없으면 완전 휴면([],0). data.go.kr Decoding 키 사용(%인코딩 없는 원본).

EHISTORY_BASE = os.environ.get("EHISTORY_API_URL", "http://apis.data.go.kr/1371037/ktvHistory")
EHISTORY_OPS = ["dhNewsList", "videoList"]   # 대한뉴스 + 영상역사관 국가기록영상


def ehistory_key():
    return os.environ.get("EHISTORY_API_KEY", "").strip()


def ehistory_search(phrase: str, era: str = None, limit: int = 10,
                    start: str = "19530101", end: str = None):
    """대한뉴스/국가기록영상 discovery(검색). 키 없으면 ([],0).
    반환: (candidates, count). candidates는 **재생페이지 메타**(직접 다운로드 불가) —
    Claude가 씬에 맞는 후보를 골라 Walter에게 페이지 URL 안내 → ehistory_intake로 수동 반입."""
    key = ehistory_key()
    if not key:
        return [], 0
    if end is None:
        end = time.strftime("%Y%m%d")
    out = []
    for op in EHISTORY_OPS:
        try:
            data = api_get(f"{EHISTORY_BASE}/{op}",
                           {"serviceKey": key, "type": "json", "numOfRows": limit, "pageNo": 1,
                            "title": phrase, "startDate": start, "endDate": end})
        except RuntimeError:
            continue
        body = ((data.get("response") or {}).get("body")) or {}
        raw = body.get("items") or {}
        item = raw.get("item") if isinstance(raw, dict) else raw
        if isinstance(item, dict):
            item = [item]
        for r in (item or []):
            if not isinstance(r, dict):
                continue
            pt = str(r.get("playTime") or "").strip()
            dur = float(pt) if pt.replace(".", "", 1).isdigit() else 0.0
            title = str(r.get("title") or "e영상역사관")[:120]
            out.append({
                "source": "ehistory", "kind": "video", "title": title,
                "url": None,                       # 직접 다운로드 불가(재생페이지)
                "page_url": r.get("url", ""), "thumb": r.get("imgUrl", ""),
                "width": 0, "height": 0, "duration_s": round(dur, 1),
                "license": "KOGL Type 1", "credit": "e영상역사관(한국정책방송원)",
                "source_id": f"ehistory:{r.get('pk') or slugify(title)}",
                "desc": str(r.get("contents") or "")[:140],
                "op": op, "menu": r.get("menuName1", ""),
                "era_source": True, "relevant": True, "manual_intake": True,
            })
    return out, len(out)


# ---------- _library 캐시 (§4-4) ----------
# v2.3: index.json은 여러 세션(병렬 실행)이 공유하는 전역 상태 — 아래 두 헬퍼 없이
#       library_index()/library_save()를 직접 read-modify-write 하면 동시 갱신 유실 위험.

_LIB_INDEX_LOCK = BASE / "_library" / ".index.lock"


@contextmanager
def _flock(path: Path, exclusive: bool = True):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a+") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        try:
            yield
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def library_index():
    p = BASE / "_library" / "index.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"entries": []}


def library_save(idx):
    p = BASE / "_library" / "index.json"
    p.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")


def library_index_locked_read():
    """읽기 전용 조회(락은 짧게 공유모드로만 잡음)."""
    with _flock(_LIB_INDEX_LOCK, exclusive=False):
        return library_index()


@contextmanager
def library_index_txn():
    """index.json read-modify-write 원자화. with 블록 안에서 idx를 수정하면 종료 시 자동 저장.
    락을 쥔 채로 최신 상태를 다시 읽으므로, 락 획득 전에 읽어둔 값은 쓰지 말 것(stale 방지)."""
    with _flock(_LIB_INDEX_LOCK, exclusive=True):
        idx = library_index()
        yield idx
        library_save(idx)


_CONTAMINATED = None


def contaminated_paths() -> set:
    """v2.7: index가 주장하는 source와 실물 내용이 다른 파일 목록.

    실측 2026-07-17 — 라이브러리 영상 277개 중 43개(16%)가 index duration ≠ 실물 duration.
    동일 md5가 서로 다른 source_id로 등록된 그룹 20개, 저작자(credit)까지 다르게 기록된 그룹 14개.
    실례: md5 f08cf78ea6(632MB, 실제 내용은 'KADEX2024 지상전페스티벌' 방산엑스포 정적 전시)가
    '(ADEX 2015) 포각 조정하는 K-2'·'(ADEX 2015) 인사하는 K-2'·'혹한기 훈련 11사단' 등
    **소스 9개에 동시 등록** — 1개만 진짜고 8개는 남의 내용이다.
    고유소스 136개 중 131개는 index duration과 일치하는 파일을 갖고 있어 **메타데이터가 옳고
    파일이 침입자**임이 확인됐다. 이 목록을 후보에서 빼지 않으면 K-2 씬에 엑스포 워크스루가 실린다.

    목록 생성/갱신: python3 library_map_v1.0.py audit --write-blocklist
    파일이 없으면 조용히 비활성(= v2.6과 동일 동작, 회귀 없음)."""
    global _CONTAMINATED
    if _CONTAMINATED is None:
        p = BASE / "_library" / "_contaminated.json"
        try:
            _CONTAMINATED = set(json.loads(p.read_text(encoding="utf-8"))["paths"])
        except Exception:
            _CONTAMINATED = set()
    return _CONTAMINATED


# ---------- v2.9 눈검수 기록 계층 (Walter 목적: 눈으로 본 것이 배치까지 이어질 것) ----------
#   문제(2026-07-19 실측): `_ai/index.json`의 best_s 62개가 **한 번도 읽히지 않았다.**
#   footage_collect의 best_s는 pick_window() 안의 지역변수일 뿐 이 필드와 무관하다.
#   게다가 단순 누락이 아니라 덮어쓰기였다 — AI 클립(10초)은 try_pick에서 start_s=3.0이
#   깔린 뒤 v2.8 소프트랭킹이 산술 점수로 또 옮겼다. 사람이 "0.5초가 제일 좋다"고 적어둬도
#   화면을 안 본 알고리즘이 이겼다.
#
#   ★ 기록은 경로도 source_id도 아닌 **md5(파일 내용)** 에 붙인다.
#     이번 오염의 본질이 "레코드는 맞는데 파일이 침입자"라서, 경로·source_id는 못 믿는
#     대상 그 자체다. md5에 붙이면 (a)파일이 슬러그를 옮겨다녀도 기록이 따라가고
#     (b)같은 md5가 소스 9개에 등록된 경우 **한 번 보면 9개가 동시에 해결된다.**
#
#   ★ index.json에 넣지 않는 이유: index는 audit·dedup이 앞으로 다시 쓰는 파일이다.
#     라이브러리에서 제일 비싼 데이터(사람 눈)를 제일 자주 고쳐 쓰는 파일에 두지 않는다.
_EYES = None
_MD5CACHE = None
_MD5CACHE_DIRTY = False


def eyes_records() -> dict:
    """{md5: {"at","verdict","best_s","skip","note","seen_as":[...]}}.
    파일이 없으면 조용히 비활성(= v2.8과 동일 동작, 회귀 없음)."""
    global _EYES
    if _EYES is None:
        p = BASE / "_library" / "_eyes.json"
        try:
            _EYES = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(_EYES, dict):
                _EYES = {}
        except Exception:
            _EYES = {}
    return _EYES


def file_md5(path) -> str:
    """전체 md5. 라이브러리에 GB급 원본이 있어 (size, mtime) 캐시로 재계산을 막는다.
    캐시 미스나 실패는 빈 문자열 — 호출부는 '기록 없음'과 같게 처리한다."""
    global _MD5CACHE, _MD5CACHE_DIRTY
    if _MD5CACHE is None:
        cp = BASE / "_library" / "_md5cache.json"
        try:
            _MD5CACHE = json.loads(cp.read_text(encoding="utf-8"))
        except Exception:
            _MD5CACHE = {}
    try:
        p = Path(path)
        st = p.stat()
        key = str(p)
        hit = _MD5CACHE.get(key)
        if hit and hit.get("size") == st.st_size and abs(hit.get("mtime", 0) - st.st_mtime) < 1:
            return hit["md5"]
        h = hashlib.md5()
        with open(p, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        digest = h.hexdigest()
        _MD5CACHE[key] = {"size": st.st_size, "mtime": st.st_mtime, "md5": digest}
        _MD5CACHE_DIRTY = True
        return digest
    except Exception:
        return ""


def md5cache_flush():
    """런 종료 시 1회. 실패해도 수집 결과에 영향 없으므로 조용히 넘어간다."""
    global _MD5CACHE_DIRTY
    if not _MD5CACHE_DIRTY or _MD5CACHE is None:
        return
    try:
        (BASE / "_library" / "_md5cache.json").write_text(
            json.dumps(_MD5CACHE, ensure_ascii=False, indent=1), encoding="utf-8")
        _MD5CACHE_DIRTY = False
    except Exception:
        pass


def eyes_for(abs_path, ai_fallback: dict = None) -> dict:
    """이 파일에 대한 눈검수 기록. 조회 순서:
      ① `_eyes.json`[md5]        — 정본(실사·AI 공통)
      ② `_ai/index.json`의 best_s — 기존 62건을 버리지 않기 위한 하위호환
    반환: {"best_s": float|None, "skip": [[a,b]...], "verdict": str, "src": "eyes"|"ai_index"}
    기록이 없으면 빈 dict."""
    rec = eyes_records().get(file_md5(abs_path)) if eyes_records() else None
    if rec:
        return {"best_s": rec.get("best_s"), "skip": rec.get("skip") or [],
                "verdict": rec.get("verdict", ""), "src": "eyes"}
    if ai_fallback and ai_fallback.get("best_s") is not None:
        return {"best_s": ai_fallback["best_s"], "skip": [],
                "verdict": "", "src": "ai_index"}
    return {}


def library_find(phrase: str, kind: str, seen_match: bool = False):
    """캐시에서 phrase 관련 파일 검색 (source_id 중복 방지 겸용).

    v1.6: 매칭 단위가 둘이다(숏폼 v4.2와 동일).
      ① 엔트리 단위(기존) — slug + keywords. seen_match=False면 이것만(v1.5와 동일).
      ② 파일 단위(신규) — files[].seen. 과거 편에서 사람이 화면을 보고 쓴 서술이라
         제목·슬러그엔 없는 어휘로 파일을 찾는다. shot이 있는 씬에서만 켠다.
    ★ 롱폼 _library는 숏폼 _library의 심볼릭 링크다 — 숏폼에서 백필한 seen을 그대로 쓴다.
    """
    hits = []
    blocked = contaminated_paths()
    for e in library_index_locked_read()["entries"]:
        hay = e["slug"] + " " + " ".join(e.get("keywords", []))
        entry_hit = relevant(phrase, hay, strict=True)
        for f in e.get("files", []):
            if f["path"] in blocked:             # v2.7: 남의 내용이 이 소스로 등록된 파일
                continue
            if f["type"] != kind or not (BASE / f["path"]).exists():
                continue
            seen_txt = " ".join(f.get("seen") or [])
            if not entry_hit:
                if not (seen_match and seen_txt
                        and relevant(phrase, seen_txt, strict=True)):
                    continue
            abs_p = str(BASE / f["path"])
            hit = {**f, "source": "library", "kind": kind,
                   "title": f.get("title") or Path(f["path"]).name,
                   "seen": list(f.get("seen") or []),
                   "abs": abs_p}
            ey = eyes_for(abs_p)               # v2.9: 눈검수 기록 동행
            if ey.get("verdict") == "bad":     # 눈으로 '못 쓴다'고 판정된 파일
                continue
            if ey:
                hit["eyes"] = ey
            hits.append(hit)
    return hits


def cand_ar(c: dict) -> float:
    """v1.3: 후보의 **화면에 보이는** 가로세로비(w/h). 모르면 0.0.

    출처 우선순위: ①width/height(검색 API 후보) ②resolution "WxH"(라이브러리 캐시 항목)
    ③ar(_ai/index.json 백필분). 0.0(=미상)은 세로로 취급하지 않는다 — 모르는 걸 세로로
    간주하면 비율 정보가 없는 구 라이브러리 항목이 통째로 강등되는 회귀가 난다.
    """
    try:
        w, h = int(c.get("width") or 0), int(c.get("height") or 0)
        if w > 0 and h > 0:
            return round(w / h, 3)
    except (TypeError, ValueError):
        pass
    m = re.match(r"\s*(\d+)\s*x\s*(\d+)\s*$", str(c.get("resolution") or ""))
    if m and int(m.group(2)) > 0:
        return round(int(m.group(1)) / int(m.group(2)), 3)
    try:
        return round(float(c.get("ar") or 0), 3)
    except (TypeError, ValueError):
        return 0.0


def is_portrait(c: dict) -> bool:
    """세로 소재 여부. 미상(0.0)은 False — 확실한 세로만 막는다."""
    ar = cand_ar(c)
    return 0 < ar < 1.0


# v1.7: 롱폼은 세로 소재를 후보 단계에서 버린다(강등이 아니라 배제). 비상 우회만 env로 연다.
ALLOW_PORTRAIT = os.environ.get("MIL_LONG_ALLOW_PORTRAIT", "0") == "1"
_portrait_dropped = {"n": 0}


def portrait_blocked(c: dict) -> bool:
    """v1.7: 이 후보를 세로라서 버려야 하나. 버리면 집계만 남긴다(수집 끝에 한 줄 보고)."""
    if ALLOW_PORTRAIT or not is_portrait(c):
        return False
    _portrait_dropped["n"] += 1
    return True


def ai_library_find(phrase: str):
    """v2.5 최후수단: _library/_ai/index.json에서 AI 생성 컷 검색.
    실사(영상+사진 Ken Burns 폴백) 전부 실패한 씬에서만 호출자가 사용한다 — 항상 최하위.
    ★ index.json은 ai_library_sync_v1.0.py가 NFC로 정규화해 저장한다(macOS는 한글 파일명을
    NFD로 반환 — 정규화 안 맞추면 "천궁" 같은 조합형 검색어가 조용히 매칭 실패한다)."""
    idx_p = BASE / "_library" / "_ai" / "index.json"
    if not idx_p.exists():
        return []
    entries = json.loads(idx_p.read_text(encoding="utf-8"))
    phrase_nfc = unicodedata.normalize("NFC", phrase)
    hits = []
    for e in entries:
        fname = unicodedata.normalize("NFC", e["file"])
        p = BASE / "_library" / "_ai" / fname
        if not p.exists():
            continue
        desc = unicodedata.normalize("NFC", e.get("desc", ""))
        kws = [unicodedata.normalize("NFC", k) for k in (e.get("keywords") or core_tokens(desc))]
        hay = desc + " " + " ".join(kws)
        if not relevant(phrase_nfc, hay, strict=True):
            continue
        ey = eyes_for(str(p), ai_fallback=e)   # v2.9: _eyes.json → _ai best_s 순
        if ey.get("verdict") == "bad":
            continue
        hits.append({
            "source": "ai", "kind": e.get("type", "video"),
            "duration_s": e.get("duration_s", 0),
            # v1.3: 비율 동행 — 롱폼 세로 차단의 판단 근거. 백필 안 된 옛 항목은 0으로 남고
            #   cand_ar()가 '미상'으로 취급한다(강등 안 함).
            "width": e.get("w") or 0, "height": e.get("h") or 0, "ar": e.get("ar") or 0,
            **({"eyes": ey} if ey else {}),
            "abs": str(p), "title": f"[AI] {desc}",
            "source_id": f"ai:{desc}",
            "license": "AI-generated (자체 생성 — 저작권 클린)",
            "credit": "AI 연출",
        })
    return hits


def library_register(phrase: str, kind: str, src_file: Path, meta: dict):
    slug = slugify(phrase)
    sub = "videos" if kind == "video" else "photos"
    dest_dir = BASE / "_library" / slug / sub
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src_file.name
    if not dest.exists():
        shutil.copy2(src_file, dest)
    with library_index_txn() as idx:
        entry = next((e for e in idx["entries"] if e["slug"] == slug), None)
        if entry is None:
            entry = {"slug": slug, "keywords": core_tokens(phrase), "files": []}
            idx["entries"].append(entry)
        rel = str(dest.relative_to(BASE))
        if not any(f["path"] == rel for f in entry["files"]):
            entry["files"].append({
                "path": rel, "type": kind, "title": meta.get("title", ""),
                "duration_s": meta.get("duration_s", 0),
                "resolution": f'{meta.get("width",0)}x{meta.get("height",0)}',
                "source": meta.get("source", ""), "source_id": meta.get("source_id", ""),
                "license": meta.get("license", ""), "credit": meta.get("credit", ""),
            })


# ---------- v1.9 전역 사용대장 (영상 간 다양성) ----------
# index.json 최상위에 두 필드를 둔다:
#   "runs":  [run_id...]                    영상 처리 순서(중복 없이, 오래된→최신)
#   "usage": {source_id: {"count": n, "runs": [run_id...]}}   소스별 누적 사용
# → '전역 사용 적은 소스 우선' 랭킹 + '최근 N영상 쿨다운'의 근거 데이터.

def build_ledger(run_id: str):
    """현재 run 기준 소스별 사용현황: {source_id: {"uses": int, "recent": bool}}.
    recent = 현재 run 제외, 최근 COOLDOWN_N개 영상에서 쓰인 적 있음."""
    idx = library_index_locked_read()
    usage = idx.get("usage", {})
    runs = [r for r in idx.get("runs", []) if r != run_id]
    recent_set = set(runs[-cooldown_n():]) if cooldown_n() > 0 else set()
    ledger = {}
    for sid, u in usage.items():
        used_runs = [r for r in u.get("runs", []) if r != run_id]  # 자기 영상 재수집 시 자기이력 무시
        ledger[sid] = {
            "uses": len(used_runs),
            "recent": any(r in recent_set for r in used_runs),
        }
    return ledger


def record_usage(run_id: str, source_ids):
    """run 완료 시 사용대장 갱신. run_id 재수집에도 안전(멱등) — 먼저 이 run의 흔적을 지우고 다시 기록.
    v2.3: 락 아래서 최신 idx를 다시 읽어 갱신 — 다른 세션의 동시 record_usage와 유실 없이 병행."""
    with library_index_txn() as idx:
        usage = idx.setdefault("usage", {})
        runs = idx.setdefault("runs", [])
        # 1) 이 run의 기존 흔적 제거 (재수집 대비)
        for sid in list(usage.keys()):
            u = usage[sid]
            u["runs"] = [r for r in u.get("runs", []) if r != run_id]
            u["count"] = len(u["runs"])
            if not u["runs"]:
                del usage[sid]
        if run_id in runs:
            runs.remove(run_id)
        # 2) 이번 사용 기록
        for sid in dict.fromkeys(source_ids):        # 순서 보존 + 중복 제거
            if not sid:
                continue
            u = usage.setdefault(sid, {"count": 0, "runs": []})
            if run_id not in u["runs"]:
                u["runs"].append(run_id)
            u["count"] = len(u["runs"])
        runs.append(run_id)                          # 최신을 맨 뒤로


def backfill_ledger():
    """기존 _work/*/manifest.json을 run 번호순으로 훑어 usage/runs를 재구성(1회)."""
    # 정규 run만 (mil_NNN_YYYYMMDD 또는 롱폼 millong_NNN_YYYYMMDD) — 테스트/실험 run은 사용대장 오염 방지 위해 제외
    run_re = re.compile(r"^(mil|millong)_\d{3}_\d{8}$")
    manifests = sorted(
        (p for p in (BASE / "_work").glob("*/manifest.json") if run_re.match(p.parent.name)),
        key=lambda p: p.parent.name)   # run_id 문자열순 = 연번순
    with library_index_txn() as idx:
        idx["usage"] = {}
        idx["runs"] = []
        seeded = 0
        for mp in manifests:
            try:
                m = json.loads(mp.read_text(encoding="utf-8"))
            except Exception:
                continue
            rid = m.get("run_id") or mp.parent.name
            sids = [i.get("source_id") for i in m.get("items", [])
                    if i.get("source_id") and not i.get("fallback")]
            if not sids:
                continue
            usage, runs = idx["usage"], idx["runs"]
            for sid in dict.fromkeys(sids):
                u = usage.setdefault(sid, {"count": 0, "runs": []})
                if rid not in u["runs"]:
                    u["runs"].append(rid)
                u["count"] = len(u["runs"])
            if rid not in runs:
                runs.append(rid)
            seeded += 1
        total_sids = len(idx["usage"])
        reused = sum(1 for u in idx["usage"].values() if u["count"] >= 2)
        result = {"backfilled_runs": seeded, "runs": idx["runs"],
                  "unique_sources": total_sids, "sources_used_2plus": reused}
    print(json.dumps(result, ensure_ascii=False, indent=2))


# ---------- 다운로드 ----------

def _dest_lock_path(dest: Path) -> Path:
    return dest.parent / (dest.name + ".lock")


def download(url: str, dest: Path, retries: int = 4):
    """v2.3: dest별 락 — 두 세션이 같은 클립(같은 dest)을 동시에 요청해도 직렬화되고,
    락 획득 후 이미 받아둔 파일이 있으면 재다운로드 없이 즉시 반환(멱등)."""
    with _flock(_dest_lock_path(dest), exclusive=True):
        if dest.exists():
            return dest
        return _download_impl(url, dest, retries)


def _download_impl(url: str, dest: Path, retries: int = 4):
    """v2.0: connection reset(54) 등 일시 오류에 재시도 + Range 이어받기.
    .part 임시파일에 받고 완료 시 rename — 부분파일 오염/재다운로드 낭비 방지."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    last_err = None
    for attempt in range(1, retries + 1):
        have = part.stat().st_size if part.exists() else 0
        headers = dict(UA)
        mode = "wb"
        if have > 0:
            headers["Range"] = f"bytes={have}-"
            mode = "ab"
        try:
            with requests.get(url, headers=headers, timeout=120, stream=True) as r:
                # 서버가 Range 무시(200)하면 처음부터 다시
                if have > 0 and r.status_code == 200:
                    have, mode = 0, "wb"
                elif have > 0 and r.status_code == 416:
                    break  # 이미 다 받음
                r.raise_for_status()
                with open(part, mode) as fh:
                    for chunk in r.iter_content(1 << 16):
                        fh.write(chunk)
            part.replace(dest)
            return dest
        except requests.exceptions.HTTPError as e:
            # 5xx(archive.org CDN 노드 일시 오류 등)만 재시도, 4xx는 즉시 포기
            code = getattr(e.response, "status_code", 0)
            if not (500 <= code < 600):
                raise
            last_err = e
            print(f"  [download 재시도 {attempt}/{retries}] {dest.name} — HTTP {code}", flush=True)
            if attempt < retries:
                time.sleep(2 * attempt)
        except (requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                ConnectionResetError) as e:
            last_err = e
            got = part.stat().st_size if part.exists() else 0
            print(f"  [download 재시도 {attempt}/{retries}] {dest.name} "
                  f"({got:,}B 확보) — {type(e).__name__}", flush=True)
            if attempt < retries:
                time.sleep(2 * attempt)
    # 재시도 소진: 부분파일이 남아 있으면 정리하고 예외 전파
    if part.exists() and part.stat().st_size == 0:
        part.unlink()
    raise last_err if last_err else RuntimeError(f"다운로드 실패: {url}")


def archive_range_download(url: str, start_s: float, need_s: float, dest: Path) -> Path:
    """v2.3: dest별 락으로 감싼 래퍼 — 동시 요청 직렬화 + 이미 받은 구간은 재사용(멱등)."""
    with _flock(_dest_lock_path(dest), exclusive=True):
        if dest.exists():
            return dest
        return _archive_range_download_impl(url, start_s, need_s, dest)


def _archive_range_download_impl(url: str, start_s: float, need_s: float, dest: Path) -> Path:
    """v2.2: 소형 파생본이 없는 대용량 archive.org 원본에서, 전체를 받지 않고
    필요한 구간만 ffmpeg로 원격 range-seek 추출한다(-ss를 -i 앞에 둬 입력단 seek
    → ffmpeg http 프로토콜이 필요한 바이트 range만 요청, 실전송량≈구간 길이).
    키프레임 정합이 불확실해 -c copy 대신 재인코딩(정확한 구간 절단 보장)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    dur = round(max(0.5, need_s) + ARCHIVE_RANGE_MARGIN, 2)
    cmd = ["ffmpeg", "-y", "-ss", f"{max(0.0, start_s):.2f}", "-i", url,
           "-t", f"{dur:.2f}",
           "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-an", str(dest)]
    res = subprocess.run(cmd, capture_output=True, timeout=180)
    if res.returncode != 0 or not dest.exists() or dest.stat().st_size == 0:
        if dest.exists():
            dest.unlink()
        raise RuntimeError(f"range-seek 실패: {dest.name}\n{res.stderr.decode()[-400:]}")
    return dest


def to_mp4(src: Path) -> Path:
    """Commons webm/ogv → mp4 변환 (§4-2-2d). 원본은 그대로 두고 mp4 경로 반환."""
    if src.suffix.lower() in (".mp4", ".jpg", ".jpeg", ".png"):
        return src
    out = src.with_suffix(".mp4")
    if out.exists():
        return out
    cmd = ["ffmpeg", "-y", "-i", str(src), "-c:v", "libx264", "-crf", "18",
           "-pix_fmt", "yuv420p", "-an", str(out)]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError(f"ffmpeg 변환 실패: {src.name}\n{res.stderr.decode()[-400:]}")
    return out


# ---------- STEP 0.5: --query 모드 ----------

def run_query_mode(phrase: str, era: str = "modern"):
    is_era = era != "modern"
    vmin = era_video_min_h() if is_era else None
    report = {"query": phrase, "era": era, "checked": True, "sources": {}}
    av, av_manual, nv, eh, eh_manual = [], 0, [], [], 0
    try:
        cv = commons_search(phrase, "video", min_h=vmin)
        cp = commons_search(phrase, "photo")
        ov = openverse_search(phrase)
        if is_era:   # era 씬: 시대 아카이브 조회, 현대 DVIDS 생략
            av, av_manual = archive_search(phrase, era)
            nv = nara_search(phrase, era)
            eh, eh_manual = ehistory_search(phrase, era)
            dv = dv_any = []
        else:
            dv = dvids_search(phrase, "South Korea", "video")
            dv_any = dv or dvids_search(phrase, None, "video")
    except RuntimeError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(EXIT_API)

    def brief(items, n=5):
        out = []
        for i in items[:n]:
            row = {"title": i["title"][:70], "res": f'{i["width"]}x{i["height"]}',
                   "dur_s": i["duration_s"], "license": i["license"]}
            if "archive_large" in i:   # v2.2: dry-run에서 range-seek 대상 여부 노출
                row["archive_large"] = i["archive_large"]
            out.append(row)
        return out

    lib_v = library_find(phrase, "video")
    lib_p = library_find(phrase, "photo")
    report["sources"] = {
        "library":       {"video": len(lib_v), "photo": len(lib_p)},
        "commons_video": {"count": len(cv), "top": brief(cv)},
        "commons_photo": {"count": len(cp), "top": brief(cp)},
        "openverse_photo": {"count": len(ov), "top": brief(ov)},
        "dvids_video":   {"count": len(dv_any), "country_filtered": len(dv), "top": brief(dv_any)},
    }
    if is_era:
        report["sources"]["archive_video"] = {
            "count": len(av), "manual_review_후보": av_manual, "top": brief(av)}
        report["sources"]["nara_video"] = {"count": len(nv), "top": brief(nv),
                                           "활성": bool(nara_key())}
        # ehistory는 재생페이지만 제공(수동 intake) → 자동 verdict 총계에는 미포함, 후보만 표시
        report["sources"]["ehistory_대한뉴스"] = {
            "활성": bool(ehistory_key()), "discovery_후보": len(eh),
            "안내": "직접다운 불가 — page_url에서 받아 ehistory_intake로 반입(공공누리1)",
            "top": [{"title": i["title"][:50], "dur_s": i["duration_s"],
                     "page_url": i["page_url"], "menu": i.get("menu", "")} for i in eh[:5]]}
    total_video = len(cv) + len(dv_any) + len(lib_v) + len(av) + len(nv)
    total_photo = len(cp) + len(ov) + len(lib_p)
    if total_video >= 2 and total_video + total_photo >= 5:
        verdict = "GREEN"     # 영상 중심 구성 가능 (사진 부족은 영상 스틸로 대체 가능)
    elif total_photo >= 5 or total_video + total_photo >= 4:
        verdict = "YELLOW"    # 사진 KenBurns 중심 구성
    else:
        verdict = "RED"       # 주제 반려 권고 (§2 STEP 0.5)
    report["totals"] = {"video": total_video, "photo": total_photo}
    report["verdict"] = verdict
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(EXIT_OK)


# ---------- 대한뉴스 discovery 모드 (--ehistory) ----------

def run_ehistory_mode(phrase: str, start: str, end: str, limit: int = 20):
    """대한뉴스/e영상역사관 후보를 검색해 목록 출력. 실제 취득은 ehistory_intake로 수동 반입."""
    if not ehistory_key():
        print(json.dumps({"error": "EHISTORY_API_KEY 없음 — .env에 data.go.kr 발급키 추가 필요"},
                         ensure_ascii=False)); sys.exit(EXIT_VALIDATION)
    cands, n = ehistory_search(phrase, limit=limit, start=start,
                               end=end or time.strftime("%Y%m%d"))
    out = {"query": phrase, "기간": f"{start}~{end or 'today'}", "count": n,
           "license": "KOGL Type 1(공공누리 1유형) — 출처표시 의무",
           "취득": "page_url에서 영상 받아 → ehistory_intake_v1.0.py --file <mp4> --source-url <page_url> --type-ok",
           "후보": [{"title": c["title"], "dur_s": c["duration_s"], "menu": c.get("menu", ""),
                    "desc": c["desc"], "page_url": c["page_url"], "thumb": c["thumb"]}
                   for c in cands]}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(EXIT_OK)


# ---------- STEP 2: --scenes 모드 ----------

_CONCEPTS_CACHE = None


def concepts() -> dict:
    """concepts.json — 개념 b-roll 사전 (v3.0). 없으면 빈 dict(현행 무영향)."""
    global _CONCEPTS_CACHE
    if _CONCEPTS_CACHE is None:
        p = BASE / "concepts.json"
        if p.exists():
            _CONCEPTS_CACHE = {k: v for k, v in
                               json.loads(p.read_text(encoding="utf-8")).items()
                               if not k.startswith("_")}
        else:
            _CONCEPTS_CACHE = {}
    return _CONCEPTS_CACHE


def scene_concept(footage: dict):
    """씬이 개념 b-roll 씬이면 그 정의를 반환, 아니면 None."""
    slug = (footage or {}).get("concept")
    if not slug:
        return None
    return concepts().get(slug)


def resolve_phrases(footage: dict, aliases: dict):
    """footage.concept(v3.0) / weapon 슬러그 / phrases 직접 지정 → 검색 구문 배열 (§4-2-2b).

    우선순위: concept > weapon > phrases.
    concept이 weapon을 이기는 이유 — 개념 씬은 '무기를 보여주는 씬'이 아니다.
    둘 다 적힌 씬은 대본이 애매하다는 신호이므로 개념 쪽을 따른다(화면=문장 원칙).
    """
    con = scene_concept(footage)
    if con:
        return list(con.get("terms") or [])
    if footage.get("weapon") and footage["weapon"] in aliases:
        return aliases[footage["weapon"]]
    phrases = footage.get("phrases") or []
    out = []
    for p in phrases:
        out.extend(aliases.get(p, [p]))   # phrases 안에 슬러그가 섞여 있어도 해석
    return out


def load_rejects(work_dir: Path):
    """눈검수에서 거부된 source_id 집합 (_work/<run>/rejects.json)."""
    p = work_dir / "rejects.json"
    if p.exists():
        return {r["source_id"] for r in json.loads(p.read_text(encoding="utf-8"))}
    return set()


def collect_for_scene(scene, aliases, footage_dir, dry_run, rejects=frozenset(), pool=None,
                      ledger=None, doc_era="modern", pool_out=None):
    """폴백 체인(§4-3)+클립 풀(v1.5)로 씬 소재 확보. 반환: manifest item 리스트.

    pool(런 전체 공유): {source_id: {"duration": s, "next_start": s}}
    - 미사용 클립(fresh) 우선 → 부족하면 사용된 긴 영상의 '다음 구간' 재사용(reuse)
    - 같은 구간 반복은 금지 — 재사용 시 start_s가 항상 전진한다
    ledger(v1.9, 영상 간): {source_id: {"uses": int, "recent": bool}}
    - 후보 랭킹을 '전역 사용 적은 소스 우선 + 쿨다운 밖 우선'으로 (라이브러리 tier 독점 해소)
    """
    if pool is None:
        pool = {}
    if ledger is None:
        ledger = {}
    sid = scene["id"]
    text = scene.get("text", "")
    # ── v1.6 요구 화면(shot) — 숏폼 v3.5와 동일한 옵트인. 없으면 v1.5와 100% 같게 동작한다.
    #   롱폼은 씬당 클립 상한이 5라(숏폼 2) 한 씬에 오배정이 더 많이 들어올 수 있다.
    shot = scene_shot(scene.get("footage") or {})

    # 롱폼 v1.0: footage.type="graphic" 씬은 외부 API를 전혀 안 본다.
    #   graphic_card_capture_v1.0.mjs가 STEP 2 이전에 이미 렌더해 둔 PNG를
    #   _work/<run>/graphics/index.json에서 찾아 그대로 등재한다(Claude 자체 제작 화면이라
    #   출처 검증·눈검수 대상이 아님 — license=internal, verified=true 즉시 확정).
    fo0 = scene.get("footage") or {}
    if fo0.get("type") == "graphic":
        run_dir = Path(footage_dir).parent
        gi_path = run_dir / "graphics" / "index.json"
        if not gi_path.exists():
            return [{"scene_id": sid, "fallback": "graphic_missing",
                     "reason": "graphics/index.json 없음 — docu_graphic_v*.mjs(또는 graphic_card_capture) 먼저 실행"}]
        gi = json.loads(gi_path.read_text(encoding="utf-8"))
        hit = next((g for g in gi if g.get("scene_id") == sid), None)
        # 롱폼 v1.7: docu_graphic 렌더러는 애니메이션 mp4(video)와 정지 png를 함께 낸다 — mp4 우선
        gpath = next((hit.get(k) for k in ("video", "png")
                      if hit and hit.get(k) and Path(hit[k]).exists()), None) if hit else None
        if not gpath:
            return [{"scene_id": sid, "fallback": "graphic_missing",
                     "reason": f"graphics/index.json에 씬{sid} 항목/파일 없음"}]
        return [{
            "scene_id": sid, "key": f"s{sid:02d}_a", "verified": True,
            "tier": "graphic", "type": "graphic",
            "source": "generated", "source_id": f"graphic:{run_dir.name}:{sid}",
            "source_url": "", "license": "internal", "credit": "Claude 제작",
            "duration_s": 0, "start_s": 0.0, "resolution": "1920x1080",
            "fallback_used": None, "title": hit.get("title", ""),
            "path": gpath, "graphic_kind": hit.get("kind", ""),
        }]

    prefer = (scene.get("footage") or {}).get("prefer", "video")
    country = (scene.get("footage") or {}).get("country")

    # 롱폼 v1.2(2026-08-10): ai_first 씬이 card로 조용히 강등되던 버그 근본수정.
    #   ai_first는 "실사 무료소재로 채울 수 없음이 확정된 씬"이라는 선언이다(국적·기술수준
    #   특정 등). 그런데 v1.0/v1.1은 phrases가 비어 있다는 이유로 card 폴백을 반환했고,
    #   preflight의 [AI-REQUEST] 차단(fallback=="ai_request"만 검사)을 그대로 통과해
    #   "주제가 0프레임"인 영상이 출고될 뻔했다(숏폼 mil_037·mil_039와 동일 사고 경로).
    #   → ai_request로 올려 보내 게이트 A(사람 승인 후 ai_intake 반입)를 강제한다.
    #   재사용 판단을 돕기 위해 _library/_ai 후보를 함께 실어 보낸다(자동 채택은 안 한다 —
    #   AI컷 배정은 사람이 눈으로 보고 정하는 것이 이 파이프라인의 규칙).
    if (scene.get("footage") or {}).get("ai_first"):
        vmust = list((scene.get("footage") or {}).get("visual_must") or [])
        cands, seen = [], set()
        for term in vmust + list((scene.get("footage") or {}).get("phrases") or []):
            for c in ai_library_find(term):
                if c["source_id"] in seen:
                    continue
                if not ALLOW_PORTRAIT and is_portrait(c):   # 롱폼 v1.7: 세로 AI컷은 후보로도 안 보인다
                    continue
                seen.add(c["source_id"])
                cands.append({"source_id": c["source_id"], "title": c["title"],
                              "duration_s": c.get("duration_s", 0), "abs": c["abs"],
                              # v1.3: 재사용 판단은 사람이 한다 — 비율을 보여줘야 판단이 된다.
                              #   세로는 롱폼에서 폭 28.5% 블러 액자다(권장 안 함).
                              "ar": cand_ar(c),
                              "orient": "portrait" if is_portrait(c) else "landscape"})
        cands.sort(key=lambda c: c["orient"] == "portrait")   # 가로 후보를 위로
        return [{"scene_id": sid, "fallback": "ai_request", "fallback_used": True,
                 "reason": "footage.ai_first=true — 실사 무료소재로 채울 수 없는 씬(게이트 A)",
                 "visual_must": vmust, "text": text[:120],
                 "ai_library_candidates": cands[:8]}]

    phrases = resolve_phrases(scene.get("footage") or {}, aliases)
    if not phrases:
        return [{"scene_id": sid, "fallback": "card", "reason": "phrases 없음"}]

    # v2.1 시대: 씬 footage.era 우선, 없으면 문서 era. modern이면 현행과 동일.
    era = (scene.get("footage") or {}).get("era") or doc_era or "modern"
    is_era = era != "modern"
    vmin = era_video_min_h() if is_era else None
    # v2.4 임팩트: footage.impact:"high" 씬만 화려함 우선(제목 액션어휘) + 프레임 피크윈도우. 그 외 씬은 무변경.
    is_high = str((scene.get("footage") or {}).get("impact", "")).lower() == "high"

    est = round(len(text) * SEC_PER_CHAR, 1)
    # 롱폼 v1.0: 숏폼의 "4초 넘으면 무조건 2클립"(시각 변화 규칙) 대신, 실제 씬 길이를
    # 롱테이크 상한(LONG_MAX_CLIP_DUR)으로 나눠 필요한 최소 클립 수만 요구한다 —
    # 8~9분 영상은 씬이 9~19s대라 그대로 두면 전 씬이 need=2가 되어 롱테이크가 불가능해진다.
    # v1.5 (2026-08-18, Walter 지시): ceil(est / 12.0) 단독으로는 컷이 너무 오래 머문다.
    #   millong_001 실측 — 10.1초 씬이 클립 1개(10.1초 체류), 평균 8.22s, 최대 13.5s.
    #   한 클립이 2~3문장을 덮으면 앞문장에 맞춘 화면이 뒷문장에서 반드시 어긋난다.
    #   → 목표치(TARGET_SEG_DUR 5.0s) 반올림과 하드상한(LONG_MAX_CLIP_DUR 7.5s) 올림 중
    #     큰 쪽을 쓴다. 목표만 쓰면 7.4초 씬이 1개로 남고, 상한만 쓰면 13초 씬이 2개(6.5s)로
    #     남아 둘 다 반쪽이다.
    if prefer == "video":
        need = max(1,
                   math.ceil(est / LONG_MAX_CLIP_DUR),     # 어떤 세그먼트도 상한을 못 넘게
                   round(est / LONG_TARGET_SEG_DUR))       # 평균을 목표치에 붙게
    else:
        need = 1
    seg_dur = est / need + 1.0            # 세그먼트당 필요 소스 길이(+여유 1s)

    # ── 후보 수집 (티어 순서 유지, 씬 내 중복 소스 제거) ──
    cands, seen_here = [], set()

    def add_cands(items, tier):
        for c in items:
            if c["source_id"] in rejects or c["source_id"] in seen_here:
                continue
            seen_here.add(c["source_id"])
            cands.append({**c, "tier": tier})

    # v3.0 개념 b-roll: 무기 소스(DVIDS·무기 라이브러리)를 통째로 건너뛰고 개념 소스만 쓴다.
    #   여기서 라우팅을 갈라야 "잡지 씬에 전차 클립"이 구조적으로 불가능해진다.
    con = scene_concept(scene.get("footage") or {})
    if con:
        stock_ok = con.get("stock_ok", True)
        for phrase in phrases:
            if prefer == "video":
                add_cands(commons_search(phrase, "video", min_h=vmin), "commons_video")
                if stock_ok:
                    add_cands(pexels_search(phrase, "video"), "stock_video")
                    add_cands(pixabay_search(phrase, "video"), "stock_video")
            else:
                add_cands(commons_search(phrase, "photo"), "commons_photo")
                add_cands(openverse_search(phrase), "openverse_photo")
                if stock_ok:
                    add_cands(pexels_search(phrase, "photo"), "stock_photo")
                    add_cands(pixabay_search(phrase, "photo"), "stock_photo")

    for phrase in (phrases if not con else []):
        if prefer == "video":
            # v3.1: 라이브러리 캐시도 era 필터를 통과해야 한다. v3.0까지 이 호출이 is_era
            #   분기 밖이라 캐시된 DVIDS 현대 영상이 1950년 대본에 그대로 들어왔다.
            add_cands(era_filter_cands(library_find(phrase, "video", seen_match=bool(shot)),
                                       era, drop_modern_sources=True), "library")
            if is_era:   # v2.1 시대 소스 최우선 투입, 현대 DVIDS 제외
                add_cands(era_filter_cands(archive_search(phrase, era)[0], era),
                          "archive_video")
                add_cands(nara_search(phrase, era), "nara_video")
                # 대한뉴스(ehistory)는 재생페이지만 제공 → 자동 다운로드 불가.
                # 자동 pool 미포함. STEP 2에서 `--ehistory <검색어>` discovery로 후보를 뽑아
                # ehistory_intake_v1.0.py로 수동 반입(공공누리 1유형).
            add_cands(era_filter_cands(commons_search(phrase, "video", min_h=vmin), era),
                      "commons_video")
            if not is_era:
                add_cands(dvids_search(phrase, country, "video"), "dvids_video")
        else:
            add_cands(era_filter_cands(library_find(phrase, "photo", seen_match=bool(shot)),
                                       era, drop_modern_sources=True), "library")
            add_cands(era_filter_cands(commons_search(phrase, "photo"), era), "commons_photo")
            add_cands(local_stock_search(phrase, (scene.get("footage") or {}).get("hint")),
                      "local_stock")
            if not is_era:   # DVIDS 사진도 현대라 era 씬에선 제외
                add_cands(dvids_search(phrase, country, "image"), "dvids_photo")
            add_cands(openverse_search(phrase), "openverse_photo")

    # ── v1.6 shot 스코어링 (숏폼 v4.2와 동일 정책) ──
    #   exclude는 하드 제거, 임계는 소프트(강한 후보가 need에 모자라면 풀을 다시 연다).
    shot_stat = None
    if shot:
        for c in cands:
            c["_shot"] = shot_score(c, shot, aliases)
            c["_shot_axes"] = shot_axes(c, shot, aliases)
        n_all = len(cands)
        hard = [c for c in cands if c.get("_shot", 0) > -50]     # exclude 히트만 하드 제거
        strong = [c for c in hard if c["_shot"] >= shot_min()]
        relaxed = len(strong) < need
        cands = hard if relaxed else strong
        shot_stat = {"scanned": n_all, "excluded": n_all - len(hard),
                     "strong": len(strong), "kept": len(cands), "relaxed": relaxed}
        if relaxed and hard:
            print(f"  [SHOT-LOW] 씬{sid}: shot 조건을 충분히 만족하는 후보가 "
                  f"{len(strong)}건뿐(need {need}) — 약한 후보까지 열어 배정한다. "
                  f"S3 눈검수에서 이 씬을 먼저 볼 것.", flush=True)

    picked = []

    def try_pick(c, mode):
        """fresh=미사용 클립 / reuse=사용된 클립의 다음 구간. 성공 시 True.

        v2.8: 여기서 정한 start_s는 '잠정값'이다. 다운로드 후 소프트랭킹(pick_window)이
        같은 클립 안에서 더 나은 구간으로 옮긴다. 산술값은 스캔이 실패·비활성일 때의
        폴백으로 그대로 남는다(회귀 없음).
        """
        sid_ = c["source_id"]
        if portrait_blocked(c):                            # 롱폼 v1.7: 세로 배제(세 경로 공통 차단점)
            return False
        if any(x["source_id"] == sid_ for x in picked):    # v1.7: 씬 내 동일 소스 금지
            return False
        dur = c.get("duration_s") or 0
        if c["kind"] == "video":
            state = pool.get(sid_)
            if mode == "fresh":
                if state is not None:
                    return False
                if dur and dur < seg_dur:
                    return False
                # v1.6-③ 인트로 스킵: 길이 여유가 있으면 3초부터 (도입 안내판·타이틀 회피)
                base = 3.0 if (dur and dur >= seg_dur + 4.0) else 0.0
                # v2.9: 눈으로 본 기록이 있으면 산술값을 이긴다(첫 사용 한정).
                #   ★ 클립 끝을 넘지 않게 클램프 — best_s가 유효해도 표시길이가 넘칠 수 있다.
                eyes_lock = False
                eb = (c.get("eyes") or {}).get("best_s")
                if eb is not None:
                    b = float(eb)
                    if dur and b + seg_dur > dur:
                        b = max(0.0, dur - seg_dur)
                    base, eyes_lock = round(b, 1), True
                pool[sid_] = {"duration": dur, "next_start": base + seg_dur + 0.5, "uses": 1,
                              "used": [(base, base + seg_dur)]}   # v2.8: 런 내 점유 구간 대장
                picked.append({**c, "_phrase": c.get("_phrase"), "start_s": base,
                               "_eyes_lock": eyes_lock})
                return True
            # reuse: 남은 구간이 충분할 때만, start 전진
            if state is None:
                return False
            if state.get("uses", 1) >= SOURCE_REUSE_CAP:          # v1.7b: 상한(기본 3회, 롱폼 .env로 상향) — 소스 풀 소진 시 영상 80% 유지가 우선(인접금지+구간상이로 다양화 방어)
                return False
            start = state["next_start"]
            if dur and dur - start < seg_dur:
                return False
            state["next_start"] = start + seg_dur + 0.5
            state["uses"] = state.get("uses", 1) + 1
            state.setdefault("used", []).append((start, start + seg_dur))
            picked.append({**c, "start_s": round(start, 1)})
            return True
        # 사진: 런에서 1회만
        if sid_ in pool:
            return False
        pool[sid_] = {"duration": 0, "next_start": 0}
        picked.append({**c, "start_s": 0.0})
        return True

    hint = (scene.get("footage") or {}).get("hint")   # v1.8: 의미 매칭
    hint_re = re.compile(hint, re.I) if hint else None
    last_src = pool.get("_last")                       # v1.6: 직전 세그먼트 소스는 후순위

    def g_uses(c):                                     # v1.9: 전역(영상 간) 사용 횟수
        return ledger.get(c["source_id"], {}).get("uses", 0)

    def g_recent(c):                                   # v1.9: 최근 N영상 쿨다운 여부
        return ledger.get(c["source_id"], {}).get("recent", False)

    # v1.9 fresh 랭킹: hint매칭 → 쿨다운밖 → 전역 사용적음 → 직전소스회피
    #   (tier 우선순위 폐지 — 라이브러리/Commons/DVIDS를 한 풀에서 '덜 쓴 것'이 이김)
    def fresh_key(c):
        return (
            # v1.3 세로 강등 — **첫 키**. 가로 후보가 하나라도 있으면 세로는 절대 안 뽑힌다.
            #   era·hint·impact보다 앞에 두는 이유: 세로는 화면의 28.5%만 쓰는 블러 액자라
            #   내용이 아무리 맞아도 만회가 안 된다(millong_001 실측). 비율 미상은 강등 없음.
            is_portrait(c),
            (not c.get("era_source")) if is_era else False,   # v2.1: era 씬은 시대 소스가 최우선
            -c.get("_shot", 0),   # v1.6: 요구 화면 적합도가 다양성보다 앞선다(shot 없으면 전부 0 = 무영향)
            (not hint_re.search(c.get("title") or "")) if hint_re else False,
            (not _action_match(c.get("title") or "")) if is_high else False,  # v2.4: high 씬만 '발사·기동' 제목 우선(쿨다운보다 앞 → 화려함이 이김, g_uses가 최종 다양성 유지)
            g_recent(c),
            g_uses(c),
            c["source_id"] == last_src,
        )

    # v1.9: fresh(미사용) 우선 → reuse. hint는 fresh_key의 첫 타이브레이크로만 반영한다.
    #   (초기 위상 게이트는 hint 불일치 '한국어 제목' topical 클립까지 뒤로 밀어 풀을 좁혔음 →
    #    영상 내 unique 소스가 오히려 감소. 오프토픽 차단은 strict library 매칭이 이미 담당.)
    #   fresh는 '아직 이 영상에서 안 쓴 소스'를 최대한 넓게 펴는 게 최우선 = 영상 내 다양성.
    # v1.6: 차순위 후보를 남긴다 — 없으면 오배정 교체가 항상 '재수집'이 된다(처방 D).
    if pool_out is not None:
        _keep = ("source_id", "source", "kind", "title", "license", "credit",
                 "duration_s", "width", "height", "url", "page_url", "abs", "tier", "ar")
        pool_out[sid] = [
            {**{k: c.get(k) for k in _keep if c.get(k) is not None},
             "shot_score": c.get("_shot"), "shot_axes": c.get("_shot_axes")}
            for c in sorted([c for c in cands if ALLOW_PORTRAIT or not is_portrait(c)],
                            key=fresh_key)[:int(os.environ.get("MIL_POOL_KEEP", "10"))]
        ]   # 롱폼 v1.7: 차순위 풀에도 세로를 싣지 않는다(swap_next 역류 차단)

    for mode in ("fresh", "reuse"):
        if mode == "fresh":
            ordered = sorted(cands, key=fresh_key)
        else:
            # reuse: 런 내 적게 쓴 것 → 전역 적게 쓴 것 순 (LRU식 우아한 degrade)
            # v1.3: 여기서도 세로는 맨 뒤 — fresh에서 막아도 reuse 경로로 새어 들어왔다
            ordered = sorted(cands, key=lambda c: (
                is_portrait(c),
                -c.get("_shot", 0),   # v1.6: 재사용 구간을 고를 때도 적합도가 먼저
                pool.get(c["source_id"], {}).get("uses", 0), g_uses(c)))
        for c in ordered:
            if len(picked) >= need:
                break
            try_pick(c, mode)
        if len(picked) >= need:
            break
    if picked:
        pool["_last"] = picked[-1]["source_id"]

    # 영상 부족 → ①이미 쓴 영상 새 구간(위 reuse에서 처리됨) ②주제 사진 Ken Burns 폴백
    # v1.9: '부분 충원'(picked<need)도 카드로 떨구지 말고 주제 사진으로 남은 슬롯을 채운다
    #   (SKILL §4-3 폴백순서: 영상→주제 사진→카드. 오프토픽 영상보다 주제 사진이 낫다)
    fallback_used = False
    if prefer == "video" and len(picked) < need:
        for phrase in phrases:
            if len(picked) >= need:
                break
            if con:   # v3.0: 개념 씬은 무기 라이브러리를 섞지 않는다(사진 폴백도 개념 소스만)
                pool_cands = (commons_search(phrase, "photo") + openverse_search(phrase))
                if con.get("stock_ok", True):
                    pool_cands += pexels_search(phrase, "photo") + pixabay_search(phrase, "photo")
            else:
                pool_cands = (library_find(phrase, "photo")
                              + commons_search(phrase, "photo")
                              + openverse_search(phrase))
            # v1.9: 덜 쓴 사진 우선 / v1.3: 세로 사진은 맨 뒤(가로 사진이 있으면 안 뽑힘)
            pool_cands.sort(key=lambda c: (is_portrait(c), g_recent(c), g_uses(c)))
            for c in pool_cands:
                if len(picked) >= need:
                    break
                if c["source_id"] in rejects:
                    continue
                if try_pick({**c, "tier": "photo_kenburns_fallback"}, "fresh"):
                    fallback_used = True

    # v2.5 AI 최후수단: 실사(영상+사진 폴백) 전부 실패했을 때만 _library/_ai 검색.
    #   전역 사용대장(g_uses)으로 덜 쓴 AI 컷 우선 — 같은 컷 반복 사용도 다양성 랭킹 대상.
    if not picked and not con:   # v3.0: 개념 씬은 AI 무기 컷으로 때우지 않는다(주제 오염원)
        ai_cands, seen_ai = [], set()
        for phrase in phrases:
            for c in ai_library_find(phrase):
                if c["source_id"] in rejects or c["source_id"] in seen_ai:
                    continue
                seen_ai.add(c["source_id"])
                ai_cands.append(c)
        # ── v1.3: 가로만 자동 채택. 세로 AI컷은 여기서 절대 안 들어간다 ──
        #   _ai 라이브러리는 90%가 720×1280 세로다(2026-08-10 실측: 등재 186건 중 173건).
        #   숏폼용으로 만든 그 컷들이 v1.2까지 롱폼에 그대로 들어와 28% 블러 액자가 됐다.
        land = [c for c in ai_cands if not is_portrait(c)]
        for c in sorted(land, key=g_uses):
            if len(picked) >= need:
                break
            try_pick({**c, "tier": "ai_generated"}, "fresh")
        if not picked and ai_cands:
            # 세로밖에 없다 → 때우지 말고 게이트 A로 올린다(작업 4-2).
            #   세로 후보는 목록에 실어 보낸다 — 상한(preflight 10%) 안에서 쓰겠다는 판단은
            #   사람이 하고, 그때는 ai_intake로 수동 배정한다.
            return [{"scene_id": sid, "fallback": "ai_request", "fallback_used": True,
                     "reason": "실사 0건 + 가로 AI컷 0건 — 세로 AI컷만 있어 자동 배정 거부"
                               "(롱폼 1920×1080에서 폭 28.5% 블러 액자가 된다). "
                               "Flow에서 **가로 1080p 이상**으로 생성해 ai_intake로 반입할 것",
                     "visual_must": list((scene.get("footage") or {}).get("visual_must") or []),
                     "text": text[:120],
                     # 롱폼 v1.7: 세로 후보는 더 이상 싣지 않는다(수동 배정 경로도 닫음)
                     "ai_library_candidates": []}]

    if not picked:
        if shot:
            # v1.6: 조용히 라이브러리 잡동사니로 채우지 않는다 — preflight [NO-MATCH]가 막는다.
            return [{"scene_id": sid, "fallback": "no_match", "fallback_used": True,
                     "reason": f"shot 조건 충족 후보 0건 "
                               f"(subject={shot.get('subject')} action={shot.get('action')} "
                               f"setting={shot.get('setting')} exclude={shot.get('exclude')}) — "
                               f"검토 {(shot_stat or {}).get('scanned', 0)}건, "
                               f"exclude 탈락 {(shot_stat or {}).get('excluded', 0)}건",
                     "shot": shot, "shot_stat": shot_stat, "text": text}]
        return [{"scene_id": sid, "fallback": "card", "fallback_used": True,
                 "reason": f"소재 0건 (est {est}s, phrases {phrases[:3]})"}]

    items = []
    for n, c in enumerate(picked):
        letter = chr(ord("a") + n)
        item = {
            "scene_id": sid, "key": f"s{sid:02d}_{letter}", "verified": False,
            "tier": c["tier"], "type": c["kind"],
            "source": c["source"], "source_id": c["source_id"],
            "source_url": c.get("page_url", ""), "license": c["license"],
            "credit": c.get("credit", ""), "duration_s": c.get("duration_s", 0),
            "start_s": c.get("start_s", 0.0),
            # v1.3: 라이브러리·AI 후보는 width/height 키가 없어 v1.2까지 전부 "0x0"으로
            #   기록됐다 — 하류 도구(preflight·postflight)가 비율을 볼 방법이 아예 없었다.
            #   후보가 이미 갖고 있는 resolution 문자열을 살리고, 그마저 없을 때만 0x0.
            "resolution": (f'{c["width"]}x{c["height"]}'
                           if c.get("width") and c.get("height")
                           else (c.get("resolution") or "0x0")),
            "ar": cand_ar(c),
            "fallback_used": fallback_used, "title": c["title"],
        }
        if shot:
            item["shot_score"] = c.get("_shot", 0)
            axes = c.get("_shot_axes") or {}
            item["shot_axes"] = axes
            miss = [k for k, ok in axes.items() if not ok]
            if c.get("_shot", 0) < shot_min() or ("action" in miss):
                item["shot_low"] = {"score": c.get("_shot", 0), "min": shot_min(),
                                    "miss": miss, "shot": shot, "stat": shot_stat}
        if c.get("_eyes_lock"):
            # v2.9 감사 표식: 이 구간은 사람이 화면을 보고 지정한 값이다.
            #   소프트랭킹이 건드리지 않으며, postflight·눈검수에서 근거를 되짚을 수 있다.
            item["scan_pick"] = "eyes"
            item["eyes_src"] = (c.get("eyes") or {}).get("src", "eyes")
        if (c.get("eyes") or {}).get("skip"):
            item["eyes_skip"] = c["eyes"]["skip"]
        if not dry_run:
            if c["source"] in ("library", "ai"):
                item["path"] = c["abs"]
            elif c["source"] == "local_stock":
                dest = footage_dir / Path(c["abs"]).name     # desc 파일명 보존
                footage_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(c["abs"], dest)
                item["path"] = str(dest)
                library_register(c.get("_phrase") or c["title"][:40], "photo", dest, c)
            else:
                ext = Path(urllib.parse.urlparse(c.get("url") or "").path).suffix or \
                      (".mp4" if c["kind"] == "video" else ".jpg")
                # v2.4: 파일명에 source_id 해시 포함 — 같은 슬롯(sNN_letter)에 재수집으로
                #   다른 소스가 배정돼도 download()의 "dest 존재 시 스킵"이 이전 소스의
                #   잔존 파일을 엉뚱하게 재사용하지 않도록 함(mil_002 재작업 중 발견된 사고).
                src_tag = hashlib.md5(c["source_id"].encode("utf-8")).hexdigest()[:8]
                dest = footage_dir / f"s{sid:02d}_{letter}_{src_tag}{ext}"
                archive_large = c["source"] == "archive" and c.get("archive_large")
                # 같은 소스의 다른 구간 재사용이면 이미 받은 파일을 공유
                # v2.2: archive_large는 range-seek 구간 파일이라 다른 start_s를 못 커버 →
                #   공유 캐시 대상에서 제외(씬마다 그 구간을 새로 range-fetch).
                cached = None if archive_large else pool.get(c["source_id"], {}).get("_local")
                if cached and Path(cached).exists():
                    item["path"] = cached
                    items.append(item)
                    continue
                try:
                    if archive_large:
                        # 대용량 원본: 전체 다운로드 대신 필요한 구간만 range-seek로 추출
                        archive_range_download(c["url"], c.get("start_s", 0.0), est, dest)
                        usable = dest
                    elif c["source"] in ("commons", "openverse", "archive", "nara", "ehistory",
                                         "pexels", "pixabay"):
                        # v3.1: pexels·pixabay가 이 목록에 없어서 else(dvids) 분기로 떨어졌고,
                        #   스톡 id로 DVIDS Asset API를 때려 400을 받았다 — concept b-roll이
                        #   도입 이래 한 번도 성공하지 못한 원인(mil_029에서 발각).
                        download(c["url"], dest)
                        usable = to_mp4(dest) if c["kind"] == "video" else dest
                    else:  # dvids
                        dl, _ = dvids_download_url(c["source_id"])
                        if not dl:
                            item.update({"fallback": "skip", "reason": "다운로드 URL 없음"})
                            items.append(item)
                            continue
                        dest = footage_dir / f"s{sid:02d}_{letter}_{src_tag}.mp4"
                        download(dl, dest)
                        usable = to_mp4(dest) if c["kind"] == "video" else dest
                except Exception as e:
                    # v2.1: 개별 소스 다운로드/변환 실패(archive 500 등)는 전체 중단이 아니라
                    #       해당 후보만 스킵 → 씬은 나머지 클립으로, 0건이면 STEP3/AI로 충당.
                    item.update({"fallback": "skip",
                                 "reason": f"다운로드/변환 실패: {type(e).__name__} {str(e)[:80]}"})
                    print(f"  [수집 스킵] 씬{sid} {c['source']} {c['title'][:40]} — "
                          f"{type(e).__name__}", flush=True)
                    items.append(item)
                    continue
                item["path"] = str(usable)
                reg_meta = c
                if archive_large:
                    # 물리 파일은 원본 전체가 아니라 range-seek 구간 그 자체 —
                    # 다운스트림(military_build·footage_review·library 재사용)이 존재하지
                    # 않는 지점을 seek하지 않도록 start_s=0·duration_s=실제 구간 길이로 보정.
                    clip_dur = round(max(0.5, est) + ARCHIVE_RANGE_MARGIN, 1)
                    item["start_s"] = 0.0
                    item["duration_s"] = clip_dur
                    reg_meta = {**c, "duration_s": clip_dur}
                else:
                    pool.setdefault(c["source_id"], {"duration": c.get("duration_s", 0),
                                                     "next_start": 0})["_local"] = str(usable)
                library_register(c.get("_phrase") or c["title"][:40], c["kind"], usable, reg_meta)
        items.append(item)

    # ── v2.8 소프트랭킹 구간 선택: 전 씬(비디오 전부), 다운로드된 실제 파일을 보고 start_s 이동 ──
    #   v2.4는 impact:"high" 씬에서만 돌았다. 그래서 나머지 씬은 여전히 화면을 안 본 채
    #   3.0 고정·눈먼 next_start 점프로 착지했고, 그게 실측된 실패의 출처다
    #   (세그먼트 30%가 start_s=3.0, 59%가 원본 앞 10% 안, 그리고 KF-21 500초 빈하늘 출고).
    #   프로파일만 씬에 따라 갈린다:
    #     high 씬  → impact  (발사·화염 우선. 편당 2~3개 — Walter 결정, 전편 적용은 리듬을 죽인다)
    #     그 외 씬 → presence(자극이 아니라 사각지대 회피. 다양성·주제선택엔 개입하지 않는다)
    #   같은 클립 안에서 구간만 옮기므로 소스 선택·다양성 랭킹은 건드리지 않는다.
    if not dry_run and scan_enabled():
        profile = "impact" if is_high else "presence"
        disp = max(1.0, est / max(need, 1))          # 실제 표시 길이(빌드가 재생하는 초)
        for item in items:
            if item.get("type") != "video" or item.get("fallback"):
                continue
            # v2.9 ★ 눈 > 산술. 사람이 화면을 보고 지정한 구간은 여기서 절대 안 옮긴다.
            #   ±N초 미세조정을 허용하지 않는 이유는 정확도가 아니라 추적 가능성이다 —
            #   "12.4초라고 적었는데 왜 14.1초가 나갔나"를 매번 역추적하게 되면
            #   눈검수 기록의 값이 사라진다. 같은 클립 2회차 사용은 _eyes_lock이 없으므로
            #   아래 소프트랭킹이 정상 작동한다(같은 장면 두 번 방지).
            if item.get("scan_pick") == "eyes":
                continue
            p = item.get("path")
            if not p or not os.path.exists(p):
                continue
            full = item.get("duration_s") or _probe_duration(p)
            cur = item.get("start_s", 0.0)
            src = item.get("source_id")
            # 이 런에서 이미 점유한 구간은 후보에서 뺀다(자기 자신의 잠정 구간은 제외).
            #   품질 판단이 아니라 중복 방지 — 하드블록과 혼동 금지.
            used = [(a, b) for a, b in pool.get(src, {}).get("used", [])
                    if abs(a - cur) > 0.05]
            # v2.9: 눈으로 '여기는 쓰지 말라'고 적어둔 구간(로고·제원슬라이드·빈 하늘)을
            #   후보에서 뺀다. 2회차 사용이 1회차가 피한 쓰레기 구간에 착지하는 걸 막는다.
            used += [(float(a), float(b)) for a, b in (item.get("eyes_skip") or [])]
            best = pick_window(p, disp, full, profile=profile, used=used, intro_skip=1.0)
            if best is None or abs(best - cur) < 0.3:
                continue
            item["start_s"] = best
            item["scan_pick"] = profile              # 감사 표식(눈검수·postflight에서 확인)
            if profile == "impact":
                item["impact_peak"] = True           # v2.4 표식 유지(하위호환)
            st = pool.get(src)
            if st is not None:                       # 점유 대장을 확정값으로 갱신
                st["used"] = [(a, b) for a, b in st.get("used", []) if abs(a - cur) > 0.05]
                st["used"].append((best, best + seg_dur))
                st["next_start"] = max(st.get("next_start", 0), best + seg_dur + 0.5)
    return items


def _protected_scene_items(run_id: str, force_recollect: set):
    """v3.2: 기존 manifest.json에서 '보호 대상' 씬의 항목을 그대로 돌려준다.
    보호 대상 = source=="ai" 이거나 scan_pick이 "manual_"로 시작하는 항목이
    하나라도 있는 씬(id). force_recollect에 들어있는 씬 id는 보호를 무시한다.
    기존 manifest.json이 없으면 빈 dict(현행 무영향)."""
    path = BASE / "_work" / run_id / "manifest.json"
    if not path.exists():
        return {}
    try:
        old = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    by_scene = {}
    for it in old.get("items", []):
        by_scene.setdefault(it.get("scene_id"), []).append(it)
    protected = {}
    for sid, items in by_scene.items():
        if sid in force_recollect:
            continue
        if any(it.get("source") == "ai" or
               (it.get("scan_pick") or "").startswith("manual_") for it in items):
            protected[sid] = items
    return protected


def run_scenes_mode(scenes_path: Path, run_id: str, dry_run: bool, force_recollect: set = frozenset()):
    if not scenes_path.exists():
        print(json.dumps({"error": f"scenes.json 없음: {scenes_path}"}, ensure_ascii=False))
        sys.exit(EXIT_VALIDATION)
    scenes_doc = json.loads(scenes_path.read_text(encoding="utf-8"))
    if scenes_doc.get("run_id") != run_id:
        print(json.dumps({"error": "run_id 불일치 — 격리 위반",
                          "인자": run_id, "scenes.json": scenes_doc.get("run_id")},
                         ensure_ascii=False))
        sys.exit(EXIT_ISOLATION)

    aliases = {k: v for k, v in
               json.loads((BASE / "weapon_aliases.json").read_text(encoding="utf-8")).items()
               if not k.startswith("_")}
    footage_dir = BASE / "_work" / run_id / "footage"
    doc_era = scenes_doc.get("era", "modern")   # v2.1 문서 레벨 시대(씬 footage.era로 개별 override)
    manifest = {"run_id": run_id, "era": doc_era, "items": [], "disclaimers_needed": []}

    # v3.2: AI컷·수동확정 씬은 재수집에서 제외하고 기존 항목을 그대로 보존한다.
    protected = {} if dry_run else _protected_scene_items(run_id, force_recollect)
    if protected:
        print(json.dumps({"보존됨": sorted(protected.keys()),
                          "안내": "이 씬들은 source=ai 또는 scan_pick=manual_* 항목이 있어 "
                                  "재수집하지 않고 기존 manifest 항목을 그대로 이어받았다. "
                                  "강제로 다시 검색하려면 --force-recollect \"1,3\""},
                         ensure_ascii=False))

    # ── v3.0 concept 슬러그 검증 (subject 유무와 무관하게 항상) ──
    #   오타 슬러그를 조용히 통과시키면 concept이 무시되고 phrases 0건 → 카드 폴백으로 새어나간다.
    bad_concepts = [f"씬{s['id']}: '{(s.get('footage') or {})['concept']}'"
                    for s in scenes_doc.get("scenes", [])
                    if (s.get("footage") or {}).get("concept") and not scene_concept(s.get("footage"))]
    if bad_concepts:
        print(json.dumps({"error": "미등록 concept 슬러그", "violations": bad_concepts,
                          "해결": "concepts.json에 추가하거나 기존 슬러그로 교체",
                          "등록됨": sorted(concepts().keys())}, ensure_ascii=False, indent=2))
        sys.exit(EXIT_VALIDATION)

    # ── v1.4 주제 일치 게이트: subject 별칭 집합 밖의 씬 phrases는 수집 거부 ──
    subject = scenes_doc.get("subject") or []
    if subject:
        allowed = set()
        for slug in subject:
            allowed.add(slug.lower())
            for a in aliases.get(slug, []):
                allowed.add(a.lower())
        # 핵심 토큰 집합 (예: k2 → {"k2", "k-2", "흑표", ...}) — 구문 정확일치가 아니라
        # 구문 안에 주제 무기의 핵심 토큰이 포함되면 통과 ("K2 Tank Joins the Fight" 허용)
        allowed_tokens = set()
        for a in allowed:
            allowed_tokens.update(t.lower() for t in core_tokens(a))
        violations = []
        for scene in scenes_doc.get("scenes", []):
            fo = scene.get("footage") or {}
            if fo.get("offtopic_ok"):
                continue
            if scene_concept(fo):   # v3.0: 개념 b-roll은 애초에 무기가 아니다 → 게이트 우회
                continue
            for ph in resolve_phrases(fo, aliases):
                ph_tokens = {t.lower() for t in core_tokens(ph)}
                if ph.lower() not in allowed and not (ph_tokens & allowed_tokens):
                    violations.append(f"씬{scene['id']}: '{ph}' — subject {subject} 핵심 토큰과 불일치")
        if violations:
            print(json.dumps({"error": "주제 일치 게이트 위반 — K2 주제에 전투기 금지 규칙",
                              "violations": violations,
                              "해결": "phrases를 subject 무기로 바꾸거나, 의도된 b-roll이면 footage.offtopic_ok=true+사유"},
                             ensure_ascii=False, indent=2))
            sys.exit(EXIT_VALIDATION)

    rejects = load_rejects(BASE / "_work" / run_id)
    pool = {}   # v1.5 런 레벨 클립 풀 — 씬 간 구간 분배·중복 관리
    ledger = build_ledger(run_id)   # v1.9 영상 간 사용대장 (다양성 랭킹 근거)

    cand_pool = {}          # v1.6: 씬별 차순위 후보 — swap_next가 재검색 없이 읽는다
    try:
        for scene in scenes_doc.get("scenes", []):
            if scene["id"] in protected:
                manifest["items"].extend(protected[scene["id"]])
                continue
            manifest["items"].extend(
                collect_for_scene(scene, aliases, footage_dir, dry_run, rejects, pool, ledger,
                                  doc_era, pool_out=cand_pool))
    except RuntimeError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(EXIT_API)

    if any(i.get("source") == "dvids" for i in manifest["items"]):
        manifest["disclaimers_needed"].append("dvids_nonendorsement")
    if any("KOGL" in (i.get("license") or "") for i in manifest["items"]):
        manifest["disclaimers_needed"].append("kogl_type1")
    if any((i.get("license") or "").startswith("CC BY") for i in manifest["items"]):
        manifest["disclaimers_needed"].append("cc_attribution")   # caption에 저작자·라이선스 표기 필수
    if any(i.get("source") == "archive" for i in manifest["items"]):
        manifest["disclaimers_needed"].append("archive_org")      # caption 소재출처: Internet Archive
    if any(i.get("source") == "nara" for i in manifest["items"]):
        manifest["disclaimers_needed"].append("nara")             # caption 소재출처: U.S. National Archives

    # v3.0 개념 b-roll 고지: 스톡 소재는 캡션에 소재 출처를 남긴다(출처표시 의무는 없으나
    #   "이 장면은 실제 현장이 아니라 자료화면"임을 시청자에게 알리는 게 이 채널의 원칙).
    if any(i.get("source") in ("pexels", "pixabay") for i in manifest["items"]):
        manifest["disclaimers_needed"].append("stock_footage")

    # v3.0 개념 씬 caption_note 자동 부착 — 화면에 "자료화면 · 군사 전문지·보도"가 뜬다.
    con_notes = {}
    for scene in scenes_doc.get("scenes", []):
        c = scene_concept(scene.get("footage") or {})
        if c and not scene.get("caption_note"):
            con_notes[scene["id"]] = f'자료화면 · {c.get("ko", "")}'.strip(" ·")
    if con_notes:
        for scene in scenes_doc.get("scenes", []):
            if scene["id"] in con_notes:
                scene["caption_note"] = con_notes[scene["id"]]
        if not dry_run:
            scenes_path.write_text(json.dumps(scenes_doc, ensure_ascii=False, indent=2),
                                   encoding="utf-8")

    # v2.5 AI 최후수단으로 픽업된 씬: ai_intake_v1.0.py가 수동으로 하던 고지를 자동화.
    ai_scene_ids = {i["scene_id"] for i in manifest["items"] if i.get("source") == "ai"}
    if ai_scene_ids:
        if "ai_disclosure" not in manifest["disclaimers_needed"]:
            manifest["disclaimers_needed"].append("ai_disclosure")
        scenes_changed = False
        for scene in scenes_doc.get("scenes", []):
            if scene["id"] in ai_scene_ids and not scene.get("caption_note"):
                scene["caption_note"] = "AI 연출 화면"
                scenes_changed = True
        if scenes_changed and not dry_run:
            scenes_path.write_text(json.dumps(scenes_doc, ensure_ascii=False, indent=2),
                                    encoding="utf-8")

    # v1.9 신선비율 진단 — '이번 영상에서 처음 쓰는 소스' 비율 (하드 반려 아님, 경고만)
    real = [i for i in manifest["items"] if i.get("source_id") and not i.get("fallback")]
    fresh_srcs = {i["source_id"] for i in real if ledger.get(i["source_id"], {}).get("uses", 0) == 0}
    ratio = (len(fresh_srcs) / len({i["source_id"] for i in real})) if real else 0.0
    manifest["diversity"] = {
        "fresh_source_ratio": round(ratio, 2), "target": fresh_ratio(),
        "fresh_sources": len(fresh_srcs),
        "unique_sources": len({i["source_id"] for i in real}),
        "reused_from_past": sorted(
            {i["source_id"] for i in real if ledger.get(i["source_id"], {}).get("uses", 0) > 0}),
    }
    if ratio < fresh_ratio():
        manifest["diversity"]["warning"] = (
            f"[FRESH-LOW] 새 소스 비율 {ratio:.0%} < 목표 {fresh_ratio():.0%} — "
            f"소재 풀이 얕은 주제일 수 있음. STEP 3 눈검수에서 반복 컷 우선 reject 권장.")

    # v2.9: 이번 런에서 '눈으로 본 기록'이 실제로 배치에 반영된 건수.
    #   0이면 눈검수 기록이 아직 없거나 배선이 끊긴 것 — Walter가 바로 알아챌 수 있게 노출한다.
    eyed = [i for i in real if i.get("scan_pick") == "eyes"]
    vids = [i for i in real if i.get("type") == "video"]
    manifest["eyes"] = {
        "applied": len(eyed), "video_items": len(vids),
        "records_loaded": len(eyes_records()),
        "by_src": {s: sum(1 for i in eyed if i.get("eyes_src") == s)
                   for s in sorted({i.get("eyes_src", "eyes") for i in eyed})},
    }
    if vids and not eyed and eyes_records():
        manifest["eyes"]["warning"] = (
            "[EYES-UNUSED] 눈검수 기록은 있는데 이번 런에 반영된 항목이 0건 — "
            "md5 불일치(파일 교체) 또는 매칭 실패 의심.")
    # v1.6 [SHOT] 집계 — 요구 화면 매칭 성적표. preflight·눈검수가 읽는다.
    scored = [i for i in manifest["items"] if "shot_score" in i]
    no_match = [i for i in manifest["items"] if i.get("fallback") == "no_match"]
    low = [i for i in scored if i.get("shot_low")]
    if scored or no_match:
        manifest["shot_report"] = {
            "scored_items": len(scored),
            "avg_score": round(sum(i["shot_score"] for i in scored) / len(scored), 2) if scored else 0,
            "low_items": [{"key": i["key"], "scene_id": i["scene_id"],
                           "score": i["shot_score"], "title": i.get("title", "")[:70]} for i in low],
            "no_match_scenes": [{"scene_id": i["scene_id"], "reason": i.get("reason", "")}
                                for i in no_match],
            "min_score": shot_min(),
        }

    md5cache_flush()

    if not dry_run and cand_pool:
        (BASE / "_work" / run_id / "pool.json").write_text(
            json.dumps({"run_id": run_id, "scenes": cand_pool}, ensure_ascii=False, indent=2),
            encoding="utf-8")

    if not dry_run:
        footage_dir.mkdir(parents=True, exist_ok=True)
        out = BASE / "_work" / run_id / "manifest.json"
        out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        # v1.9 사용대장 기록 (재수집 시 이 run의 과거 흔적을 지우고 갱신 — 멱등)
        record_usage(run_id, [i["source_id"] for i in real])
    print(json.dumps(manifest, ensure_ascii=False, indent=2))

    for i in no_match:                      # v1.6: preflight가 차단한다 — 먼저 눈에 띄게
        print(f"[NO-MATCH] 씬{i['scene_id']}: {i.get('reason','')}", file=sys.stderr)
    for i in low:                           # v1.6: 배정은 됐지만 약한 후보
        print(f"[SHOT-LOW] {i['key']} (점수 {i['shot_score']}/{shot_min()}): "
              f"{i.get('title','')[:60]}", file=sys.stderr)

    if _portrait_dropped["n"]:              # 롱폼 v1.7: 세로 배제 집계(후보 단위, 중복 포함)
        print(f"[PORTRAIT-DROP] 세로 후보 {_portrait_dropped['n']}건을 배제했다(롱폼은 가로만). "
              f"소재가 비는 씬은 위 NO-MATCH/AI-REQUEST로 따로 보고된다", file=sys.stderr)

    card_only = [i["scene_id"] for i in manifest["items"] if i.get("fallback") == "card"]
    sys.exit(EXIT_VALIDATION if card_only and not dry_run else EXIT_OK)


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser(description="밀리터리 숏폼 소재 수집기")
    ap.add_argument("--query", help="STEP 0.5 가용성 체크용 검색 구문")
    ap.add_argument("--era", default="modern",
                    help="시대(query 모드용): modern|wwii|korean_war|vietnam_war|cold_war (era_styles.json)")
    ap.add_argument("--ehistory", help="대한뉴스/e영상역사관 discovery 검색어(수동 intake용 후보 목록)")
    ap.add_argument("--start", default="19530101", help="ehistory 검색 시작일 YYYYMMDD")
    ap.add_argument("--end", default=None, help="ehistory 검색 종료일 YYYYMMDD(기본 오늘)")
    ap.add_argument("--scenes", help="scenes.json 경로 (STEP 2) — era는 scenes.json에서 읽음")
    ap.add_argument("--run-id", help="run_id (scenes 모드 필수)")
    ap.add_argument("--dry-run", action="store_true", help="다운로드 없이 계획만 출력")
    ap.add_argument("--backfill", action="store_true",
                    help="(1회) 기존 _work/*/manifest.json에서 사용대장 시딩")
    ap.add_argument("--force-recollect", default="",
                    help="v3.2: 콤마구분 씬 id — AI컷·수동확정 보호를 무시하고 강제 재수집 (예: \"3,7\")")
    args = ap.parse_args()

    load_env()

    if args.backfill:
        backfill_ledger()
        sys.exit(EXIT_OK)
    if args.ehistory:
        run_ehistory_mode(args.ehistory, args.start, args.end)
    elif args.query:
        run_query_mode(args.query, args.era)
    elif args.scenes:
        if not args.run_id:
            print(json.dumps({"error": "--scenes 모드는 --run-id 필수"}, ensure_ascii=False))
            sys.exit(EXIT_VALIDATION)
        force_ids = {int(x) for x in args.force_recollect.split(",") if x.strip().isdigit()}
        run_scenes_mode(Path(args.scenes), args.run_id, args.dry_run, force_ids)
    else:
        ap.print_help()
        sys.exit(EXIT_VALIDATION)


if __name__ == "__main__":
    main()
