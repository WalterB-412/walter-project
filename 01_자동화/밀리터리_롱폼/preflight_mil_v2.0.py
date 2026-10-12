#!/usr/bin/env python3
"""
[롱폼 v2.0] 2026-10-12 — 다큐 전환 게이트 (Walter 지시: 국뽕→다큐 · 가로 소재만 · 정보 그래픽 ≤20% ·
  좌하단 소제목 · 다큐9분식 자막 · 팩트체크·전문성 강화). military_build v1.5와 짝이다.
  ① [PORTRAIT-IN-LONG] 상한 10% → **0건**. 세로 영상·사진 모두 1건이라도 있으면 exit 1
     (footage_collect v1.7이 후보 단계에서 이미 버리므로 여기 걸리면 수동 배정·AI 반입 경로다).
     --skip-portrait는 그대로 비상 우회(경고로 낮춤).
  ② [GFX-RATIO] 전체화면 정보 그래픽 비중 = 그래픽 세그먼트 초 ÷ 총 길이. layout.graphics 값을 읽는다.
     max_ratio(20%) 초과 exit 1 · min_ratio_warn(5%) 미만 경고 · 목표 10~15%.
     [GFX-STREAK] 그래픽만 있는 씬 연속 max_consecutive_scenes(2) 초과 경고 ·
     [GFX-CHAPTER] 한 챕터 안 그래픽 비중 chapter_max_ratio(35%) 초과 경고 ·
     [GFX-COLDOPEN] 인사(GREETING) 전 콜드오픈에 그래픽 경고(첫 화면은 실사).
  ③ [GFX-SOURCE] 그래픽 씬은 화면에 찍힐 출처(footage.graphic.source)와 fact_ids 필수 — exit 1.
     그래픽은 숫자를 '크게' 보여주는 화면이라 틀리면 영상 전체 신뢰가 무너진다.
  ④ [FACT-*] facts.json v2 스키마(출처 등급제). scenes가 참조하는 팩트만 검사한다.
     · 출처가 C등급(위키·블로그·커뮤니티)뿐이면 exit 1 [FACT-TIER]
     · 수치 팩트인데 독립 출처 2개 미만 → 경고 [FACT-XCHECK]
     · confidence=estimated|disputed인데 씬 문장에 헤징 표현이 없으면 exit 1 [HEDGE]
     · 구 스키마(sources 없음)는 경고 [FACT-LEGACY] — 진행 중인 런을 깨지 않기 위함
  ⑤ [HYPE] 국뽕·선정 표현 차단(exit 1, --skip-hype) + 애국 CTA 상투구 경고([HYPE-CTA]).
  ⑥ [BALANCE] 한계·반론 씬(counterpoint:true) 0개면 경고 — 다큐는 반대편 근거를 다룬다.
  ⑦ [QUOTE] 인용 자막 씬: speaker(≤label_max_chars) + fact_ids 필수, 한국어·원문 각 2줄 이하.
  ⑧ 소제목(lower third): chapter_mode=lower_third면 chapters/*.png 대신 line1/line2 픽셀 폭을
     검사([LT-WIDTH]). 총 길이·자막 시뮬은 military_build.scene_lead()로 소제목 무나레이션 구간을 포함한다.
  ⑨ [LOCATION] scene.location 30자 초과 경고.
[롱폼 v1.9] 2026-10-06 — [BANNED] 금지 소재 차단 (숏폼 preflight v3.7 41번 이식, 수정이력_분석_v2.x P4).
  _eyes.json verdict=bad 소재(또는 manifest banned=True)가 배정돼 있으면 exit 1. 롱폼 _library는
  숏폼 _library 심볼릭 링크라 숏폼에서 금지한 소재가 롱폼에 그대로 배정될 수 있고, footage_review
  v1.1 이하의 --approve는 bad를 ok로 덮어 verified 게이트로는 못 막았다(숏폼 160→184 재출고 경로).
  우회 플래그 없음 — 금지를 풀려면 Walter 확인 후 footage_review --unban.
[롱폼 v1.6] 2026-08-18 — 컷 리듬 게이트 + 채널 인사 게이트 (Walter 지시).
  millong_001 완성본 실측이 이 개정의 근거다: 실사 세그먼트 **평균 8.22s · 최대 13.5s ·
  60씬 중 27씬이 8초 초과**. Walter 지적은 두 가지였는데("화면이 오래 나온다",
  "소재와 대본이 안 맞는다") **뿌리가 하나**다 — 클립 하나가 2~3문장을 덮으면
  앞문장에 맞춘 화면이 뒷문장에서 반드시 어긋난다. 프레임 대조 실측 예:
    · 씬22 "한국은 라인이 돌아가고 있었다" → 화면은 **폐허 공장**(뒷문장엔 맞고 앞문장엔 정반대)
    · 씬28 수출국 8개국 나열 → 빨강·파랑 **잉크 추상**
    · 씬33·42 → NATO 홍보물의 **영어 타이틀 카드**가 그대로 노출
  ① [SEG-LONG] 세그먼트 체류시간 — v1.5는 `len(items)==1`일 때만 봐서 20초 씬에 클립 2개면
     10초짜리 두 개가 그냥 통과했다. v1.6은 **항목 수와 무관하게 실제 세그먼트 길이**를 본다.
     상한 12.0s → **7.5s(exit 1)**, 목표 5.0s, 평균 6.0s 초과 시 경고.
     그래픽 카드 단독 씬은 '읽는 화면'이라 하드 차단하지 않고 [SEG-GRAPHIC] 경고만 낸다.
  ② 씬당 클립 상한 2 → 5 (military_build v1.3·footage_collect v1.5와 동기).
     클립 부족 게이트의 `need = dur / min(len(items), 2)`도 같이 고쳤다 — 안 고치면
     3클립 씬의 필요 길이를 1.5배로 잘못 계산해 멀쩡한 소재를 반려한다.
  ③ [NO-GREETING] 채널 인사 — beat "GREETING" 신설. 모든 롱폼은 콜드오픈 직후에
     "안녕하세요. 대한의 밀리터리 입니다."로 시작하는 인사 씬을 둔다(위치 고정).

[롱폼 v1.4] 2026-08-10 — [PORTRAIT-IN-LONG] 세로 소재 게이트 신설
  (작업스펙_AI컷_비율정합_v1.0 작업 4-1, Walter 요청 "세로 영상은 최소 비율로만").
  왜: `military_build v1.10`이 풀블리드를 폐지해 `fit_decision`이 **절대 None을 반환하지
  않는다** — 어떤 비율이 들어와도 조용히 블러 여백으로 나간다. 720×1280 세로컷은
  1920×1080 캔버스에서 폭 547px = **화면의 28.5%**다. millong_001의 s24·s49·s50·s53이
  그렇게 출고됐고, 어떤 게이트도 한마디 하지 않았다. 블러 폴백은 안전망이라 폐지하지 않는다
  (대안인 "세로 원본 16:9 상하 크롭"은 720×405 → 1920폭 = 2.67배 업스케일로 더 나쁘다).
  대신 **최후수단으로 묶어둔다**:
    · 목표 0건 / 허용 상한 = 씬 수의 10%(내림, 60씬이면 6씬)
    · 세로 씬끼리 **최소 3씬 간격** — 연달아 나오면 액자 화면이 이어져 티가 난다
    · 1건 이상이면 **warning**(씬 번호·파일명·해상도 출력), 상한 초과 또는 간격 위반은 **exit 1**
  판정은 manifest 값이 아니라 **파일을 직접 ffprobe한 실측값**이다(회전 메타 ±90° 반영).
  manifest resolution은 v1.2까지 라이브러리·AI 항목이 전부 "0x0"이라 신뢰할 수 없고,
  파생본 교체(크롭·tpad·delogo)로 실제 파일만 바뀌는 경로도 있다.
  사진(Ken Burns)은 상한 계산에서 제외하고 별도 정보성 경고만 낸다 — 실사 영상이 0건인
  주제에서 세로 사진 폴백은 정답인 경우가 많다(무료 영상 공백 주제 다수). 비상 우회: --skip-portrait

[롱폼 v1.3] 2026-08-09 — 챕터 서사 역할(arc) 게이트 신설.
  chapter_title.arc = 기/승/전/결. **시간배분·분량 하한은 두지 않는다**(고정 템플릿은
  유튜브 비진정성 콘텐츠 정책 리스크) — 역할 라벨만 붙여 "중반 늘어짐"을 막는다.
  경고: [NO-ARC](arc 전무) · [NO-TURN]('전' 없음 = 반전 지점 부재) · [ARC](기/결 누락) ·
       [ARC-ORDER](순서 역행). 전부 warning — 빌드는 막지 않되 방치 금지.

[롱폼 v1.2] 2026-08-09 — 씬 글자수 상한 포크 버그 수정.
  숏폼의 "씬 텍스트 40자" 상한을 그대로 물려받아 **롱폼 씬(9~19초 ≈ 55~117자)이 전부 실패**했다.
  숏폼은 씬 1개=자막 1회 표시라 40자가 곧 자막 제약이었지만, 롱폼은 씬 하나가 여러 자막 청크로
  나뉘어 순차 표시된다 — 가독성은 자막 시뮬(청크별 2줄 검사)이 이미 따로 본다.
  상한 재설정: HOOK 70자 · 일반 130자(≈21초) · CTA 200자(콜백+애국+열린질문).

[롱폼 v1.1] 2026-08-09 — 목표 길이 재설정(Walter 승인).
  · 총 길이 480~560s → **540~660s(9~11분)**: 미드롤은 8:00 이상에서만 열리는데 하한 480s는
    마지노선에 붙어 있어 TTS 편차로 7분대 추락 위험. 60초 안전마진 확보.
  · 씬 수 25~60 → **30~70** (540~660s ÷ 씬당 9~19s)
  · [NO-CHAPTERS]: 0개일 때만 경고 → **3개 미만**이면 경고(유튜브 챕터 최소 요건)
  검사 로직 자체는 v1.0과 동일 — 상수와 경고 조건만 바뀌었다.
"""

"""
preflight_mil_v1.9.py — 렌더 전 최종 게이트 (설계서_v1.7 §6-5, T8)

★v1.9 (Walter 승인 2026-07-22):
 12. [AI-REQUEST] 차단(exit 1) — manifest에 fallback:"ai_request" 씬이 남아 있으면
     빌드 금지. footage_collect v3.2의 AI-first/개념씬 AI폴백 산출물로, Veo 프롬프트를
     게이트 A로 Walter에게 요청 → 파일 drop → ai_intake 반입까지 끝나야 통과.
 13. [VISUAL-MUST] 경고 — concept/ai_first 씬에 visual_must(화면 필수조건, 예:
     ["한국 공장","최신 설비"])가 없으면 경고. 눈검수가 "공장이긴 하네"로 통과시키던
     mil_032 그릴 사고의 근본대응 — 시트·프리뷰에서 이 조건과 대조해 O/X 판정한다.
 14. 길이 규정 개정 — 총 길이 상한 66→95s(완성도 우선, 쇼츠 3분 허용·완주율이 기준),
     씬 수 7~12→7~14. "압축으로 인과 다리 자르지 말고 씬을 분할하라"의 코드 반영.

하나라도 실패하면 exit 1 → military_build 진입 금지.
자막 폭 계산·상수는 최신 military_build_v*.py를 동적 임포트해 동일 로직 사용 (이중 구현 방지).

검사 항목:
  1. scenes.json 스키마 — subject 필수·씬 수 7~10·비트 순서(HOOK 첫/CTA 끝)·글자수·highlight 실존
  2. 제목 밴드 — line1≤12자·line2≤14자·accent 포함
  3. 팩트 — 숫자 포함 씬은 fact_ids 필수 + facts.json 대조
  4. manifest — 씬별 풋티지 존재·전 항목 verified(눈검수 게이트2 통과)·영상 길이·해상도
  5. 자막 시뮬 — 전 청크가 2줄 이하 + subtitle 존 안에 들어가는지
  6. 총 길이 480~560초 = 8~9분 (TTS 실측 합산 — 롱폼 전용 상수, 숏폼 35~95초와 무관)
  7. 시각 변화 — 단일 클립 영상 씬 12초 초과 금지 (롱폼: 숏폼의 4.5초 규칙 미적용)
  8. ★v1.4 흐름 검수(flow_check) — 스타일가이드 v2.5 §11 6규칙.
     휴리스틱이라 빌드를 막지 않는 warning으로 출력([FLOW] 접두).
     STEP 5에서 Claude가 필수 수정 항목으로 처리한다.

  9. ★v1.8 [MAP] 문장↔화면 게이트 (Walter 요청 2026-07-20)
     "영국 군사전문지 제인스가"라는 대본에 사막 클립이 배정되던 문제. concepts.json의
     ko_triggers가 대본에 나오는데 footage.concept이 없으면 경고하고 슬러그를 제안한다.
     지금까지 어떤 게이트도 '문장과 화면이 같은 걸 말하는가'를 보지 않았다 — 주제 일치
     게이트는 '무기가 맞나'만 봤다. warning(exit 0) — 오탐 가능하므로 Claude가 판단한다.
 10. ★v1.8 [WHY] 인과 한 칸 강제 (스타일가이드 §11-G)
     G규칙은 "Claude가 매번 자문·자답"이라는 훈시뿐이라 산출물이 없어 건너뛰어졌다.
     정보 씬(TENSION·VALUE·PROOF)에 why 필드(이 문장이 나오는 이유)를 **의무화**하고
     비었거나 text 복사면 **exit 1로 막는다.** 내용의 옳고 그름은 여전히 Claude 몫이지만,
     "쓰게 만드는 것"만으로 자문이 실제로 일어난다. 비상 우회: --skip-why
     ★하위호환: `_work/<run>/script_draft.md`(v2.3 STEP 1a 산출물)가 없으면 구 워크플로로
     쓰인 대본으로 보고 **경고로만 처리**한다. 진행 중인 다른 세션의 빌드를 깨지 않기 위함
     (2026-07-20 병렬 세션 실측 — mil_029가 구 SKILL로 돌고 있었다).
 11. ★v1.8 [CONCEPT-EMPTY] 개념 씬이 소재 0건으로 텍스트 카드가 된 경우 경고.
     v3.0은 concept 씬에서 무기 소스를 안 보므로(엉뚱한 전차 차단) 못 구하면 카드가 된다 —
     완성본을 보고서야 알게 되는 걸 막는다.

★v2.0 (Walter 지적 2026-07-23 — "다시 수정했는데도 거의 다 또 수정, 영상 보는 눈 강화"):
 15. [EVIDENCE] 시각 식별 근거 강제 (차단, exit 1) — [WHY] 게이트의 픽셀 버전.
     이번 세션에서 T-50을 KF-21로, FA-50을 KF-21로 오배정한 게 전부 '제목만 믿고
     앞뒤 1~2초만 본' 탓이었다. footage.weapon 또는 footage.visual_must가 있는 씬의
     verified 실사 영상 항목은 화면에서 찾은 식별 근거(evidence)가 있어야 한다 —
     manifest 항목 evidence 필드이거나, 그 md5가 _eyes.json에 evidence로 남아 있어야
     통과. 없으면 빌드를 막는다. footage_review_v2.0 --evidence로 기록한다.
     "제목이 KF-21이니 OK"로 못 넘어가고, 마커를 못 찾으면 그게 곧 reject 신호다.
     AI컷(source=ai)은 made-to-spec + 반입 눈검수로 이미 걸러지므로 면제.
     기록은 md5로 영구화 → 재수집 시 같은 클립은 재요구 안 함(런당 신규분만). 우회: --skip-evidence

사용: python3 preflight_mil_v1.9.py --run-id <run>
출력: stdout JSON {"pass": bool, "errors": [...], "warnings": [...]}
"""
import argparse
import glob
import hashlib
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent

# ── 최신 military_build 동적 임포트 (버전 하드코딩 금지 — 절대 규칙 7) ──
_mb_files = sorted(glob.glob(str(BASE / "military_build_v*.py")),
                   key=lambda p: [int(x) for x in re.findall(r"v(\d+)\.(\d+)", p)[0]])
if not _mb_files:
    print(json.dumps({"pass": False, "errors": ["military_build_v*.py 없음"]}, ensure_ascii=False))
    sys.exit(1)
_spec = importlib.util.spec_from_file_location("mb", _mb_files[-1])
mb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mb)

# 롱폼 v1.1 (2026-08-09, Walter 승인): 480~560s(8~9분) → 540~660s(9~11분)로 상향.
#   근거 ① 미드롤 광고는 **8:00 이상**에서만 열린다. v1.0 하한 480s는 마지노선에 딱 붙어 있어
#        TTS 합성 편차·씬 길이 반올림이 누적되면 7분대로 떨어져 미드롤이 통째로 날아간다
#        (실측 변동: 씬당 ±0.5초 × 40씬 ≈ ±20초). 하한 540s로 60초 안전마진 확보.
#   근거 ② 상한 660s는 완주율 하락을 감안한 실무 상한 — 넘으면 문장 압축이 아니라
#        가장 약한 챕터를 통째로 덜어낸다(대본_스타일가이드 §0).
MIN_TOTAL, MAX_TOTAL = 540.0, 660.0   # 롱폼 v1.1: 9~11분. 숏폼 35~95s에서 분리된 독립 상수
# ── v1.6 (2026-08-18, Walter 지시) 세그먼트 체류시간 ──────────────────────────
# v1.5까지 상한 12.0s는 "롱테이크를 4.5s로 끊지 않는다"는 숏폼 반작용으로 잡은 값인데,
# millong_001 완성본에서 **평균 8.22s·최대 13.5s·60씬 중 27씬이 8초 초과**로 나왔고
# Walter가 "한 화면이 너무 오래 나온다 + 소재와 대본이 안 맞는다"를 동시에 지적했다.
# 두 증상은 같은 뿌리다 — 클립 하나가 2~3문장을 덮으면 앞문장에 맞춘 화면이 뒷문장에서
# 반드시 어긋난다(실측: 씬22 "한국은 라인이 돌아갔다"에 폐허 공장, 씬28 수출국 나열에 잉크).
# 목표 5.0s는 대략 한 문장 = 한 화면이라 매칭이 구조적으로 유지되는 지점이다.
TARGET_SEG_DUR = float(os.environ.get("MIL_LONG_TARGET_SEG_DUR", "5.0"))   # 목표 세그먼트 길이
MAX_SINGLE_CLIP_DUR = float(os.environ.get("MIL_LONG_MAX_CLIP_DUR", "7.5"))  # 하드 상한(초과 시 exit 1)
MAX_CLIPS_PER_SCENE = int(os.environ.get("MIL_LONG_MAX_CLIPS_PER_SCENE", "5"))  # military_build v1.3과 동기
SEG_AVG_WARN = TARGET_SEG_DUR + 1.0   # 평균이 이걸 넘으면 [SEG-LONG] 경고
_seg_stat: list = []                  # [(scene_id, 세그먼트초, 실사여부)]
# v1.6: GREETING 신설 — 채널 인사 씬(콜드오픈 직후 고정). 정보 씬이 아니므로
# why·fact_ids·흐름 커넥터(규칙 A~F) 대상에서 자연히 빠진다(INFO_BEATS에 없음).
# 롱폼 전 편 공통 규칙이라 beat로 못 박아 두면 preflight가 존재 여부를 검사할 수 있다.
BEATS = {"HOOK", "GREETING", "TENSION", "VALUE", "PROOF", "CTA"}
GREETING_LINE = "안녕하세요. 대한의 밀리터리 입니다."   # 모든 롱폼 공통 첫 문장(Walter 확정)

# ── v1.4 흐름(§11) 상수 ──
INFO_BEATS = {"TENSION", "VALUE", "PROOF"}
# 규칙 A: 4종 커넥터 (씬 첫 어절이 앞 씬과의 논리 관계를 드러내야)
CONNECTORS = [
    "그래서", "그 결과", "덕분에", "그러니", "그러니까",          # 인과
    "그런데", "하지만", "그러나", "근데", "문제는", "오히려", "반면",  # 대조
    "게다가", "여기에", "여기서", "더 놀라운", "더 무서운", "그것도",   # 심화
    "그러자", "그 순간", "이윽고", "그렇게", "마침내", "결국",        # 시간
]
# 규칙 D: 지시대명사 (주어 실종 신호)
DEMONSTRATIVES = ["이 무기", "이 부대", "이 전차", "이 미사일", "이 자주포",
                  "이 전투기", "이 군단", "이 무기체계", "이 함정", "이 잠수함"]


def _clean(text):
    """pause 태그·선행 따옴표 제거한 낭독 텍스트."""
    t = re.sub(r"\s*\[pause[^\]]*\]\s*", " ", text or "")
    return t.strip().lstrip("'\"“”‘’ ")


def _concepts():
    """concepts.json (v1.8). 없으면 빈 dict — [MAP] 게이트만 조용히 비활성."""
    p = BASE / "concepts.json"
    if not p.exists():
        return {}
    return {k: v for k, v in json.loads(p.read_text(encoding="utf-8")).items()
            if not k.startswith("_")}


def map_check(scenes):
    """[MAP] 대본에 개념 명사가 나오는데 화면이 무기로 배정된 씬 — warning."""
    cons = _concepts()
    if not cons:
        return []
    warns = []
    for s in scenes:
        fo = s.get("footage") or {}
        if fo.get("concept") or fo.get("offtopic_ok"):
            continue
        t = _clean(s.get("text"))
        hits = [(slug, kw) for slug, c in cons.items()
                for kw in (c.get("ko_triggers") or []) if kw in t]
        if not hits:
            continue
        sug = ", ".join(sorted({f'{slug}(“{kw}”)' for slug, kw in hits}))
        warns.append(
            f"[MAP] 씬 {s.get('id')} “{t[:22]}…” — 대본은 개념을 말하는데 화면은 "
            f"'{fo.get('weapon') or fo.get('phrases') or '미지정'}' 배정. "
            f"후보: {sug} — 이 문장 구간이 무기를 보여줄 필요가 없다면 "
            f'footage.concept으로 교체(출처가 중요한 씬이면 그대로 두고 무시)')
    return warns


def why_check(scenes, legacy=False):
    """[WHY] 인과 한 칸(§11-G) 강제 — 정보 씬의 why 필드.

    legacy=True(구 워크플로로 쓰인 대본)면 차단하지 않고 경고만 낸다.
    판별 근거는 `_work/<run>/script_draft.md`(SKILL v2.3 STEP 1a 산출물)의 존재 여부다.
    이 파일이 없으면 v2.2 이전 방식으로 쓰인 대본이라 why가 있을 리 없다 —
    진행 중인 다른 세션의 빌드를 깨지 않기 위한 하위호환(2026-07-20, 병렬 세션 실측).
    """
    errs = []
    for s in scenes:
        if s.get("beat") not in INFO_BEATS:
            continue
        why = (s.get("why") or "").strip()
        text = _clean(s.get("text"))
        if not why:
            errs.append(f"[WHY] 씬 {s.get('id')} why 없음 — “이 문장, 왜?”의 답을 "
                        f"바로 앞 씬 내용만으로 한 줄 적어라(§11-G). "
                        f"답이 안 나오면 그게 흐름이 끊긴 지점이다")
        elif len(why) < 8:
            errs.append(f"[WHY] 씬 {s.get('id')} why 너무 짧음(“{why}”) — 인과를 문장으로")
        elif why.replace(" ", "") in text.replace(" ", ""):
            errs.append(f"[WHY] 씬 {s.get('id')} why가 text 복사본 — 이유가 아니라 요약이다")
    return errs


def flow_check(scenes):
    """스타일가이드 v2.5 §11 흐름 6규칙 — 전부 warning([FLOW] 접두)."""
    warns = []
    info_idx = [i for i, s in enumerate(scenes) if s.get("beat") in INFO_BEATS]

    # ── A. 전환 커넥터 ── (HOOK 직후 첫 정보씬 1개는 예외)
    exempt = set(info_idx[:1])  # 첫 정보씬 면제
    missing = []
    used_seq = []  # 커넥터 남용(3연속) 검사
    for i in info_idx:
        if i in exempt:
            continue
        sc = scenes[i]
        if sc.get("reveal"):      # 정체공개 씬은 "이름은~"으로 시작 가능
            used_seq.append(None)
            continue
        t = _clean(sc.get("text"))
        hit = next((c for c in CONNECTORS if t.startswith(c)), None)
        if hit:
            used_seq.append(hit)
        else:
            used_seq.append(None)
            missing.append(sc.get("id"))
    if missing:
        ratio = 1 - len(missing) / max(1, len(info_idx) - len(exempt))
        # 임계값: 명시 커넥터가 절반 미만일 때만 경고(문맥 연결은 기계가 못 봄 → 과탐 억제).
        if ratio < 0.5:
            warns.append(f"[FLOW-A] 커넥터 명시율 {ratio:.0%} (없이 시작: 씬 {missing}) — "
                         f"규칙 A 검토 권장: 각 이음매가 앞 씬과 인과/대조/심화/시간으로 "
                         f"이어지는지 확인(문맥으로 저절로 이어지면 통과)")
    # 같은 커넥터 3연속
    for i in range(len(used_seq) - 2):
        a, b, c = used_seq[i], used_seq[i + 1], used_seq[i + 2]
        if a and a == b == c:
            warns.append(f"[FLOW-A] 커넥터 '{a}' 3연속 — 단조로움, 다른 종류로 교체")
            break

    # ── C. 정체공개 씬 ──
    reveals = [i for i, s in enumerate(scenes) if s.get("reveal")]
    if not reveals:
        # 고유명사(라틴 제식명/하이픈)가 어딘가 노출됐는지로 심각도 구분
        name_shown = any(re.search(r"[A-Z]{1,3}[-\d]|[A-Z]{2,}", _clean(s.get("text")))
                         for s in scenes)
        if name_shown:
            warns.append("[FLOW-C] 정체공개 씬에 reveal:true 미지정 — 이름은 노출됐으나 "
                         "'감추기→밝히기' 지점을 플래그로 명시 권장(규칙 C)")
        else:
            warns.append("[FLOW-C] 정체공개 없음 — 규칙 C: ④VALUE 첫 씬에서 고유명사를 "
                         "처음 밝히고 reveal:true를 달아라(끝까지 '이 무기'로만 지칭 시 이탈)")
    else:
        first = reveals[0]
        if first > 4:
            warns.append(f"[FLOW-C] 정체공개가 씬 {scenes[first].get('id')}(너무 늦음) — "
                         f"④VALUE(대략 5번째 씬 이내) 권장")

    # ── D. 지시대명사 연속 3씬 ──
    streak = 0
    for s in scenes:
        t = _clean(s.get("text"))
        has_demon = any(d in t for d in DEMONSTRATIVES)
        # 고유명사(대문자 라틴/제식명 하이픈)가 같이 있으면 주어 실종 아님
        has_proper = bool(re.search(r"[A-Z]{1,3}[-\d]|[A-Z]{2,}", t))
        if has_demon and not has_proper:
            streak += 1
            if streak >= 3:
                warns.append(f"[FLOW-D] '이 무기/부대/전차' 지시대명사 {streak}씬 연속(씬 {s.get('id')}까지) — "
                             f"규칙 D: 정체공개 후 고유명사·별명을 명시하라")
                streak = 0  # 1회만 보고
        else:
            streak = 0

    # ── B. 오픈루프 쌍 ──
    opens = {}   # label -> index
    for i, s in enumerate(scenes):
        lbl = s.get("loop_open")
        if lbl:
            opens[lbl] = i
    closes = {}
    for i, s in enumerate(scenes):
        lbl = s.get("loop_close")
        if lbl:
            closes.setdefault(lbl, i)
    last = len(scenes) - 1
    for lbl, oi in opens.items():
        if lbl not in closes:
            warns.append(f"[FLOW-B] 오픈루프 '{lbl}'(씬 {scenes[oi].get('id')}) 회수(loop_close) 없음 — "
                         f"규칙 B: 최대 4씬 안에 닫아라(HOOK 루프는 CTA 콜백)")
        elif oi == 0 and closes[lbl] == last:
            pass  # HOOK→CTA 오프닝 콜백 = 전체 스팬 루프(규칙 B 허용), 거리 제약 면제
        elif closes[lbl] - oi > 4:
            warns.append(f"[FLOW-B] 오픈루프 '{lbl}' 회수까지 {closes[lbl]-oi}씬 — "
                         f"규칙 B: 4씬 이내 권장(질문을 잊는다)")
        elif closes[lbl] < oi:
            warns.append(f"[FLOW-B] 오픈루프 '{lbl}' 회수가 오픈보다 앞섬 — 순서 확인")

    # ── E. 고아 환산 (원수치 없이 환산어만) ──
    CONV_WORDS = ["아파트", "서울에서", "여의도", "축구장", "초등학생", "대학생",
                  "국민 1인당", "한 층", "한 채", "한 발", "몇 배", "배 무게", "배 수준"]
    for s in scenes:
        t = _clean(s.get("text"))
        has_conv = any(w in t for w in CONV_WORDS)
        has_num = bool(re.search(r"\d", t))
        if has_conv and not has_num and not s.get("fact_ids"):
            warns.append(f"[FLOW-E] 씬 {s.get('id')}: 체감환산 표현은 있는데 원수치가 없음 — "
                         f"규칙 E: [원수치]→[환산] 순서(앵커 먼저)")

    # ── F. CTA 주어 정합 (마지막 문장 '응원합니다' 앞이 무기/부대 주어인지) ──
    if scenes and scenes[-1].get("beat") == "CTA":
        t = _clean(scenes[-1].get("text"))
        m = re.search(r"([^.。]*)\s*대한민국을?\s*응원", t)
        if m:
            head = m.group(1)
            # 마침표 없이 무기/부대 주어가 응원에 바로 붙으면 주어 오류 위험
            if head and not head.strip().endswith((".", "다", "죠", "요", "!")) \
               and re.search(r"(전차|자주포|미사일|부대|군단|전투기|함|무기)(가|이|는|은)\s*$", head):
                warns.append("[FLOW-F] CTA 주어 정합 확인 — '…전차가 대한민국을 응원' 형태로 읽힘. "
                             "규칙 F: 앞 문장을 마침표로 끊고 주어를 화자(우리)로 리셋")
    return warns


def _file_md5(path):
    """v1.6: 눈검수 기록 조회 키. footage_collect v2.9 / footage_review v1.9와 동일 규약."""
    try:
        h = hashlib.md5()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def _probe_dur(path):
    """v1.5: 소스 컨테이너 길이(초). manifest에 duration_s가 없어도 클립 부족 게이트가
    동작해야 한다 — millong_001에서 71개 중 8개가 duration_s 없이 검사를 통과했다."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(path)], capture_output=True, text=True, timeout=20)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def _probe_wh(path):
    """v1.4: 화면에 보이는 (w, h). 회전 메타 ±90°면 뒤바꿔 반환. 실패 시 (0, 0).
    ai_ratio_backfill_v1.0 / ai_intake와 동일 규약 — ar 정의가 도구마다 갈리면 안 된다."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height:stream_tags=rotate:stream_side_data=rotation",
             "-of", "json", str(path)], capture_output=True, text=True, timeout=20)
        st = json.loads(r.stdout)["streams"][0]
    except Exception:
        return 0, 0
    w, h = int(st.get("width") or 0), int(st.get("height") or 0)
    rot = 0
    try:
        rot = int(float((st.get("tags") or {}).get("rotate") or 0))
    except Exception:
        pass
    for sd in (st.get("side_data_list") or []):
        if "rotation" in sd:
            try:
                rot = int(float(sd["rotation"]))
            except Exception:
                pass
    if abs(rot) % 180 == 90:
        w, h = h, w
    return w, h


def portrait_check(scenes, manifest):
    """[PORTRAIT-IN-LONG] 세로 소재 상한·간격 게이트 (v1.4).

    반환 (errors, warnings). 세로 판정은 파일 실측(ffprobe) — manifest 값은 못 믿는다.
    상한: 씬 수의 10%(내림) · 간격: 세로 씬끼리 3씬 이상.
    영상만 상한 대상이고 사진은 정보성 경고만 낸다(세로 사진 폴백은 정답인 경우가 많다).
    """
    errs, warns = [], []
    idx_of = {sc.get("id"): i for i, sc in enumerate(scenes)}
    port_v, port_p = [], []
    for it in manifest.get("items", []):
        p = it.get("path")
        if not p or not Path(p).exists():
            continue
        w, h = _probe_wh(p)
        if not w or not h or w >= h:
            continue
        rec = {"sid": it.get("scene_id"), "key": it.get("key", "?"),
               "name": Path(p).name, "wh": f"{w}x{h}", "ar": round(w / h, 3),
               "src": it.get("source", "")}
        (port_p if it.get("type") == "photo" else port_v).append(rec)

    if port_p:
        # v2.0: 사진도 차단(가로 소재만). v1.9까지는 정보성 경고였다.
        errs.append(
            f"[PORTRAIT-IN-LONG] 세로 **사진** {len(port_p)}건 — 롱폼은 가로 소재만 쓴다: "
            + ", ".join(f"씬{r['sid']}({r['wh']})" for r in port_p[:8])
            + (" …" if len(port_p) > 8 else "")
            + ". 가로 사진·영상·정보 그래픽으로 교체할 것. 비상 우회 --skip-portrait")
    if not port_v:
        return errs, warns

    sids = sorted({r["sid"] for r in port_v}, key=lambda s: idx_of.get(s, 10 ** 6))
    cap = 0   # v2.0: 롱폼은 가로 소재만(Walter 2026-10-12) — 상한 10% → 0건
    detail = " / ".join(f"씬{r['sid']} {r['key']} {r['wh']}(ar {r['ar']}) {r['name']}"
                        for r in port_v)
    warns.append(f"[PORTRAIT-IN-LONG] 세로 영상 {len(port_v)}건 / {len(sids)}씬 "
                 f"(v2.0 상한 0건 — 롱폼은 가로 소재만) {detail}")

    if len(sids) > cap:
        errs.append(
            f"[PORTRAIT-IN-LONG] 세로 영상 {len(sids)}씬 > 상한 {cap}씬 — "
            f"1920×1080에서 폭 28%대 블러 액자가 그만큼 나온다. 가로 소재로 교체하거나 "
            f"Flow에서 **가로 1080p 이상**으로 재생성(ai_intake 반입)할 것. "
            f"해당 씬: {sids}. 비상 우회 --skip-portrait")
    return errs, warns   # v2.0: 상한 0건이라 간격 검사는 의미가 없어 삭제


def _load_eyes():
    try:
        d = json.loads((BASE / "_library" / "_eyes.json").read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


# ── ★v1.7 [VERB] 건조 동사 오용 / [MONEY] 금액 낭독 (숏폼 preflight v2.2와 동일 규약) ──
# Walter 지적 2026-08-25: 배·항공기를 "짓는다"고 쓰는 실수가 매 편 반복돼 손으로 고쳤다.
# 짓는 것은 건물뿐이다. 탈것은 만든다·건조한다·제작한다.
_VESSEL_NOUNS = ("잠수함", "함정", "함선", "군함", "구축함", "호위함", "초계함", "상륙함",
                 "항공모함", "항모", "이지스함", "전투함", "수송함", "쇄빙선", "선박", "배",
                 "비행기", "전투기", "항공기", "수송기", "헬기", "헬리콥터", "전차", "장갑차",
                 "미사일", "위성", "로켓", "발사체", "엔진")
_BUILD_WRONG_RE = re.compile(r"(짓(습니다|는다|는|던|고|기|자|게|자고)?|지으(라|려|면|니)|"
                             r"지어(서|야|도|진|낸)?|지었|지은|지을)")
_BUILD_OK_HEADS = ("미소", "표정", "웃음", "울상", "인상", "한숨", "농사", "이름", "죄",
                   "무리", "짝", "매듭", "결론", "종지부", "무덤", "둥지", "집", "건물",
                   "공장", "발전소", "댐", "다리", "성", "절", "밥")
_MONEY_LEFTOVER_RE = re.compile(r"\d[\d,]*\s*(?=(천조|백조|십조|천억|백억|십억|천만|백만|십만|조|억|만|원|달러))")


def verb_check(scenes):
    errs = []
    for i, sc in enumerate(scenes):
        t = _clean(sc.get("text"))
        window = t + " " + (_clean(scenes[i - 1].get("text")) if i else "")
        for m in _BUILD_WRONG_RE.finditer(t):
            head = t[max(0, m.start() - 12):m.start()]
            if any(ok in head for ok in _BUILD_OK_HEADS):
                continue
            nouns = [n for n in _VESSEL_NOUNS if n in window]
            if not nouns:
                continue
            errs.append(f"[VERB] 씬{sc.get('id')}: \"…{t[max(0,m.start()-10):m.end()+6]}…\" — "
                        f"{nouns[0]}은(는) '짓다'로 만들지 않는다. "
                        f"'만듭니다/건조합니다/제작합니다'로 고칠 것 (우회 --skip-verb)")
    return errs


def money_check(scenes):
    try:
        import importlib.util
        cands = sorted(BASE.glob("tts_run_mil_v*.py"),
                       key=lambda q: [int(x) for x in re.findall(r"\d+", q.stem)])
        if not cands:
            return []
        spec = importlib.util.spec_from_file_location("_ttsmod", cands[-1])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        conv = mod.num_to_hangul_units
    except Exception as e:
        return [f"[MONEY] 낭독 사전 검사 생략(tts 모듈 로드 실패: {e})"]
    warns = []
    for sc in scenes:
        raw = _clean(sc.get("tts_text") or sc.get("text"))
        if not re.search(r"\d", raw):
            continue
        try:
            out = conv(raw)
        except Exception:
            continue
        hits = [m.group(0).strip() for m in _MONEY_LEFTOVER_RE.finditer(out)]
        if hits:
            warns.append(f"[MONEY] 씬{sc.get('id')}: 합성 문자열에 숫자가 그대로 남음 {hits} "
                         f"— tts_run_mil의 _UNITS_RE에 단위를 추가할 것")
    return warns



# ══ v2.0 다큐 게이트 ══════════════════════════════════════════════════════════════

_GFX = mb.LAYOUT.get("graphics", {})
GFX_MAX = float(_GFX.get("max_ratio", 0.20))
GFX_MIN_WARN = float(_GFX.get("min_ratio_warn", 0.05))
GFX_STREAK = int(_GFX.get("max_consecutive_scenes", 2))
GFX_CH_MAX = float(_GFX.get("chapter_max_ratio", 0.35))

# [HYPE] 다큐 톤 금지어 — 감정 형용사·과장·적대 조롱. 숫자와 사실로 대신 말한다(스타일가이드 v1.4 §D).
HYPE_HARD = ["압도적", "역대급", "넘사벽", "미쳤다", "미친 성능", "국뽕", "경악", "충격적", "충격과 공포",
             "세계가 놀란", "전 세계가 놀", "세계를 놀라게", "전세계가 경악", "세계 최강", "세계 최고의 무기",
             "클래스가 다른", "차원이 다른", "무릎을 꿇", "벌벌 떨", "두려워 떨", "꼼짝 못", "발끝에도",
             "상대가 안 되", "게임 체인저", "사기 무기", "치트키", "레전드", "갓성비"]
HYPE_SOFT = ["대한민국을 응원", "자랑스러운 대한민국", "국민 여러분의 자부심", "위대한 대한민국"]
HEDGE_WORDS = ["추정", "알려", "공개된", "따르면", "보도", "주장", "평가", "전망", "로 보인", "가능성",
               "밝힌", "제시한", "기준으로", "외신은", "분석"]
FACT_TIERS = {"A", "B", "C"}


def lower_third_check(chapter_scenes):
    """[LT-WIDTH] 좌하단 소제목 글자수·픽셀 폭. line1은 화면 폭 75% 안, line2는 80% 안."""
    errs = []
    hs = mb.LAYOUT.get("headline_style", {})
    lt = mb.LAYOUT.get("lower_third_style", {})
    try:
        from PIL import Image, ImageDraw
        d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        f1, _ = mb._load_font(int(lt.get("line1_size", 78)))
        f2, _ = mb._load_font(int(lt.get("line2_size", 42)))
    except Exception:
        d = None
    for sc in chapter_scenes:
        ct = sc.get("chapter_title") or {}
        l1, l2 = (ct.get("line1") or "").strip(), (ct.get("line2") or "").strip()
        if len(l1) > hs.get("line1_max_chars", 20):
            errs.append(f"[LT-WIDTH] 씬{sc.get('id')} 소제목 line1 {len(l1)}자 > {hs.get('line1_max_chars', 20)}자")
        if len(l2) > hs.get("line2_max_chars", 28):
            errs.append(f"[LT-WIDTH] 씬{sc.get('id')} 소제목 line2 {len(l2)}자 > {hs.get('line2_max_chars', 28)}자")
        if d is not None:
            if d.textlength(l1, font=f1) > mb.CANVAS_W * 0.75:
                errs.append(f"[LT-WIDTH] 씬{sc.get('id')} 소제목 line1 픽셀 폭이 화면 75% 초과 — 줄일 것")
            if l2 and d.textlength(l2, font=f2) > mb.CANVAS_W * 0.80:
                errs.append(f"[LT-WIDTH] 씬{sc.get('id')} 소제목 line2 픽셀 폭이 화면 80% 초과 — 줄일 것")
    return errs


def graphic_source_check(graphic_scenes):
    """[GFX-SOURCE] 그래픽 씬: 화면 출처 표기 + fact_ids 필수(숫자를 크게 보여주는 화면이라)."""
    errs = []
    for sc in graphic_scenes:
        g = (sc.get("footage") or {}).get("graphic") or {}
        if not (g.get("source") or "").strip():
            errs.append(f"[GFX-SOURCE] 씬{sc.get('id')}: footage.graphic.source(화면 하단 출처 표기) 없음 — "
                        f"예: \"출처: SIPRI Arms Transfers Database (2026)\"")
        if not sc.get("fact_ids"):
            errs.append(f"[GFX-SOURCE] 씬{sc.get('id')}: 그래픽 씬인데 fact_ids 없음 — 그래픽의 모든 "
                        f"숫자·연도·지명은 facts.json 근거가 있어야 한다")
    return errs


def _has_gfx_item(items):
    return [it for it in items if it.get("type") == "graphic"]


def graphic_ratio_check(scenes, pairs, by_scene, total):
    errs, warns = [], []
    if not total:
        return errs, warns
    sec_of, gsec_of, only_g = {}, {}, []
    for p in pairs:
        items = (by_scene.get(p["scene_id"]) or [])[:MAX_CLIPS_PER_SCENE]
        n = len(items) or 1
        g = len(_has_gfx_item(items))
        sec_of[p["scene_id"]] = p["dur"]
        gsec_of[p["scene_id"]] = p["dur"] * g / n
        only_g.append(bool(items) and g == len(items))
    gsec = sum(gsec_of.values())
    ratio = gsec / total
    print(f"  📊 정보 그래픽 {gsec:.1f}s / {total:.1f}s = {ratio:.1%} "
          f"(상한 {GFX_MAX:.0%}, 목표 {_GFX.get('target_ratio', [0.10, 0.15])})")
    if ratio > GFX_MAX:
        errs.append(f"[GFX-RATIO] 정보 그래픽 비중 {ratio:.1%} > {GFX_MAX:.0%} — 실사 영상이 주인공이다. "
                    f"그래픽 씬 중 실사로 보여줄 수 있는 것부터 되돌려라(약 {gsec - total * GFX_MAX:.0f}초 감축)")
    elif ratio < GFX_MIN_WARN:
        warns.append(f"[GFX-RATIO] 정보 그래픽 비중 {ratio:.1%} < {GFX_MIN_WARN:.0%} — 숫자 비교·위치·연대기 "
                     f"문장을 지도·타임라인·수치 카드로 보여줄 자리가 없는지 확인(목표 10~15%)")
    streak = 0
    for p, og in zip(pairs, only_g):
        streak = streak + 1 if og else 0
        if streak == GFX_STREAK + 1:
            warns.append(f"[GFX-STREAK] 그래픽만 있는 씬이 {streak}개 연속(씬{p['scene_id']}까지) — "
                         f"{GFX_STREAK}개 이하로, 사이에 실사를 넣어라(슬라이드쇼가 된다)")
    # 챕터별
    chap, cur = {}, None
    for sc in scenes:
        if (sc.get("chapter_title") or {}).get("line1"):
            cur = sc.get("id")
        if cur is not None and sc.get("id") in sec_of:
            a = chap.setdefault(cur, [0.0, 0.0])
            a[0] += gsec_of[sc["id"]]
            a[1] += sec_of[sc["id"]]
    for cid, (g, t) in chap.items():
        if t and g / t > GFX_CH_MAX:
            warns.append(f"[GFX-CHAPTER] 씬{cid} 챕터의 그래픽 비중 {g / t:.0%} > {GFX_CH_MAX:.0%} — "
                         f"한 챕터에 몰지 말고 분산")
    if _GFX.get("no_graphics_before_greeting", True):
        gi = next((i for i, s in enumerate(scenes) if s.get("beat") == "GREETING"), None)
        if gi:
            cold = [s.get("id") for s in scenes[:gi] if gsec_of.get(s.get("id"))]
            if cold:
                warns.append(f"[GFX-COLDOPEN] 콜드오픈 씬 {cold}에 그래픽 — 첫 화면은 실사로 사건 한복판을 보여줘라")
    return errs, warns


def fact_quality_check(scenes, facts):
    """[FACT-*] facts.json v2 출처 등급제. 참조된 팩트만 본다."""
    errs, warns = [], []
    used = {}
    for sc in scenes:
        for fid in sc.get("fact_ids") or []:
            used.setdefault(fid, []).append(sc)
    legacy = []
    for fid, scs in used.items():
        f = facts.get(fid)
        if not f:
            continue   # 존재 여부는 3번 팩트 게이트가 이미 보고
        srcs = f.get("sources")
        if not srcs:
            legacy.append(fid)
            continue
        tiers = [str(s.get("tier", "")).upper() for s in srcs]
        bad = [t for t in tiers if t not in FACT_TIERS]
        if bad:
            errs.append(f"[FACT-TIER] {fid}: tier {bad} 무효 — A/B/C 중 하나")
        if tiers and all(t == "C" for t in tiers):
            errs.append(f"[FACT-TIER] {fid}: 출처가 C등급뿐(위키·블로그·커뮤니티) — A(정부·군·의회·SIPRI·"
                        f"제조사 공시) 또는 B(주요 언론·전문지) 출처를 찾거나 문장에서 뺄 것")
        no_url = [i for i, s_ in enumerate(srcs) if not (s_.get("url") or s_.get("doc"))]
        if no_url:
            errs.append(f"[FACT-TIER] {fid}: sources[{no_url}]에 url(또는 doc) 없음 — 되짚을 수 없는 출처는 출처가 아니다")
        val = str(f.get("value", "")) + " " + str(f.get("claim", ""))
        indep = {(s_.get("publisher") or s_.get("url") or "").strip() for s_ in srcs}
        if re.search(r"\d", val) and len(indep) < 2:
            warns.append(f"[FACT-XCHECK] {fid}: 수치 팩트인데 독립 출처 {len(indep)}개 — 2개 이상 교차 확인 권장")
        conf = (f.get("confidence") or "confirmed").lower()
        if conf in ("estimated", "disputed", "reported"):
            for sc in scs:
                t = _clean(sc.get("text"))
                if not any(h in t for h in HEDGE_WORDS):
                    (errs if conf != "reported" else warns).append(
                        f"[HEDGE] 씬{sc.get('id')}: {fid}는 confidence={conf}인데 문장이 단정형 — "
                        f"\"~로 알려져 있습니다 / ~에 따르면 / 공개된 자료 기준\" 등 출처 성격을 문장에 담을 것")
    if legacy:
        warns.append(f"[FACT-LEGACY] 구 스키마 팩트 {len(legacy)}개({legacy[:6]}) — sources[{{publisher,url,tier,accessed}}] "
                     f"형식으로 옮기면 등급·교차검증 검사가 켜진다(대본_스타일가이드 v1.4 §F)")
    return errs, warns


def hype_check(scenes):
    errs, warns = [], []
    for sc in scenes:
        t = _clean(sc.get("text"))
        hits = [w for w in HYPE_HARD if w in t]
        if hits:
            errs.append(f"[HYPE] 씬{sc.get('id')}: {hits} — 다큐 톤 금지어. 감정 대신 숫자·사실로 다시 쓸 것 "
                        f"(비상 우회 --skip-hype)")
        soft = [w for w in HYPE_SOFT if w in t]
        if soft:
            warns.append(f"[HYPE-CTA] 씬{sc.get('id')}: {soft} — 다큐 결론은 응원 구호 대신 '그래서 무엇이 "
                         f"바뀌었나' + 열린 질문으로 맺는다(스타일가이드 v1.4 §D-5)")
    return errs, warns


def balance_check(scenes):
    if any(s.get("counterpoint") for s in scenes):
        return []
    return ["[BALANCE] counterpoint:true 씬 0개 — 한계·반론·실패·비용을 다루는 씬이 없다. 다큐는 반대편 "
            "근거를 정면으로 다룰 때 신뢰가 생긴다(최소 1개 챕터 또는 2~3개 씬 권장)"]


def quote_check(scenes):
    errs = []
    maxc = int(mb.LAYOUT.get("quote_style", {}).get("label_max_chars", 8))
    for sc in scenes:
        q = sc.get("quote")
        if not q:
            continue
        sp = (q.get("speaker") or "").strip()
        if not sp:
            errs.append(f"[QUOTE] 씬{sc.get('id')}: quote.speaker(발화 주체 라벨) 없음")
        elif len(sp) > maxc:
            errs.append(f"[QUOTE] 씬{sc.get('id')}: speaker '{sp}' {len(sp)}자 > {maxc}자 — 라벨 박스에 안 들어간다")
        if not sc.get("fact_ids"):
            errs.append(f"[QUOTE] 씬{sc.get('id')}: 인용인데 fact_ids 없음 — 누가 언제 어디서 한 말인지 "
                        f"facts.json에 원문과 출처를 남겨라(인용은 가장 강한 증거이자 가장 위험한 오류다)")
    return errs


def location_check(scenes):
    return [f"[LOCATION] 씬{s.get('id')}: location {len(s['location'])}자 > 30자 — 한 줄로 짧게"
            for s in scenes if len((s.get("location") or "")) > 30]


def check(run_id, allow_uneyed=False, skip_why=False, skip_evidence=False,
          skip_portrait=False, skip_verb=False, skip_shot=False, skip_hype=False):
    errors, warnings = [], []
    work = BASE / "_work" / run_id
    eyes = _load_eyes()
    # 도입기 안전장치: 기록이 0건이면 게이트를 걸지 않는다. 지금 실사 406개에 대한
    #   눈검수 기록이 없어서, 그대로 켜면 모든 런이 전부 막힌다(작업이 아니라 마비).
    #   1건이라도 쌓이는 순간부터 신규 소스를 막기 시작한다.
    if not eyes:
        allow_uneyed = True
        warnings.append("[EYES-EMPTY] _library/_eyes.json이 비어 인입 눈검수 게이트 비활성 — "
                        "footage_review_v1.9로 기록을 쌓기 시작하면 자동으로 켜진다")

    # ── 입력 로드 ──
    try:
        scenes_doc = json.loads((work / "scenes.json").read_text(encoding="utf-8"))
    except Exception as e:
        return [f"scenes.json 로드 실패: {e}"], warnings
    if scenes_doc.get("run_id") != run_id:
        return [f"run_id 불일치 (scenes.json={scenes_doc.get('run_id')})"], warnings

    scenes = scenes_doc.get("scenes", [])
    manifest = {}
    mp = work / "manifest.json"
    if mp.exists():
        manifest = json.loads(mp.read_text(encoding="utf-8"))
        if manifest.get("run_id") != run_id:
            errors.append("manifest.json run_id 불일치")
    else:
        errors.append("manifest.json 없음 (STEP 2 미실행)")

    facts = {}
    fp = work / "facts.json"
    if fp.exists():
        facts = {f["id"]: f for f in json.loads(fp.read_text(encoding="utf-8")).get("facts", [])}

    # ── 1. scenes 스키마 ──
    if not scenes_doc.get("subject"):
        errors.append("subject 필드 없음 — 주제 일치 게이트(§4-6) 불가")
    n = len(scenes)
    # 롱폼 v1.1: 540~660초 ÷ 씬당 9~19초 = 28~73씬 → 30~70으로 조정(v1.0은 25~60, 8~9분 기준)
    if not (30 <= n <= 70):
        errors.append(f"씬 수 {n}개 — 30~70개 필요(롱폼 9~11분 기준)")
    if scenes:
        if scenes[0].get("beat") != "HOOK":
            errors.append("첫 씬 beat가 HOOK이 아님")
        if scenes[-1].get("beat") != "CTA":
            errors.append("마지막 씬 beat가 CTA가 아님")
        # ── v1.6 [NO-GREETING] 채널 인사 (2026-08-18, Walter 지시: 모든 롱폼 공통) ──
        # 위치는 콜드오픈 직후로 고정한다. 맨 앞에 두면 유튜브의 첫 3초를 인사로 써
        # 훅이 죽고, 챕터1 뒤로 밀면 본론 도입을 끊는다.
        g_idx = [i for i, s in enumerate(scenes) if s.get("beat") == "GREETING"]
        if not g_idx:
            errors.append(
                f"[NO-GREETING] 채널 인사 씬 없음 — 모든 롱폼은 콜드오픈 직후에 "
                f"beat:\"GREETING\" 씬을 둔다(첫 문장 \"{GREETING_LINE}\")")
        else:
            if len(g_idx) > 1:
                errors.append(f"[NO-GREETING] GREETING 씬이 {len(g_idx)}개 — 1개만 둔다")
            gi = g_idx[0]
            # "콜드오픈 직후"의 실제 정의: 씬 0이 아니고(훅이 먼저), 첫 챕터 카드보다 앞.
            # 콜드오픈 씬들의 beat는 HOOK 하나로 통일되지 않는다(millong_001은 HOOK+TENSION 2개) —
            # beat로 판정하면 정상 대본이 걸린다. 챕터 경계가 유일하게 신뢰할 수 있는 기준이다.
            _first_ch = next((i for i, s in enumerate(scenes) if s.get("chapter_title")), None)
            if gi == 0:
                errors.append("[NO-GREETING] GREETING이 첫 씬 — 콜드오픈(훅) 뒤로 옮겨라. "
                              "유튜브 첫 3초를 인사에 쓰면 훅이 죽는다")
            if _first_ch is not None and gi > _first_ch:
                errors.append(f"[NO-GREETING] GREETING(씬{scenes[gi].get('id')})이 첫 챕터 "
                              f"카드(씬{scenes[_first_ch].get('id')})보다 뒤 — 본론 도입을 끊는다")
            if not (scenes[gi].get("text") or "").strip().startswith(GREETING_LINE):
                errors.append(
                    f"[NO-GREETING] GREETING 씬은 \"{GREETING_LINE}\"으로 시작해야 한다 "
                    f"(뒤에 편별 인사말을 이어 붙이는 것은 자유)")
            if scenes[gi].get("chapter_title"):
                errors.append("[NO-GREETING] GREETING 씬에 chapter_title 금지 — 챕터는 그다음 씬부터")
    for sc in scenes:
        sid = sc.get("id")
        beat = sc.get("beat")
        if beat not in BEATS:
            errors.append(f"씬{sid}: beat '{beat}' 무효")
        text = re.sub(r"\s*\[pause[^\]]*\]\s*", " ", (sc.get("text") or "")).strip()  # v1.3: 연출 태그는 글자수 제외
        # v1.5 마무리 우선 원칙(Walter 반복 지적 2026-07-18):
        #   마지막 착지(CTA)를 글자수 때문에 명사종결로 압축하면 TTS로 들을 때 어색하다.
        #   → CTA 씬만 상한을 80자로 완화해 완결된 문장을 허용한다(그 외 규칙은 동일).
        # ── 롱폼 v1.2 (2026-08-09): 숏폼 글자수 상한을 그대로 물려받아 **모든 롱폼 씬이
        #   실패하던 포크 버그를 수정.**
        #   숏폼은 "씬 1개 = 자막 1회 표시"라 40자가 곧 자막 2줄 제약이었다. 롱폼은 다르다 —
        #   씬 하나가 9~19초(≈55~117자, 6.15자/초)이고 그 안에서 자막이 여러 청크로 나뉘어
        #   순차 표시된다. 즉 롱폼에서 자막 가독성을 지키는 건 이 씬 글자수 게이트가 아니라
        #   아래 **자막 시뮬(청크별 2줄×폭 검사, layout.json 유도)** 이다.
        #   여기서는 "씬 하나가 화면 전환 없이 너무 오래 끌지 않는가"만 본다.
        if sc.get("type") == "hook" or beat == "HOOK":
            limit = 70    # 콜드오픈 ≈11초 — 롱폼도 도입은 짧게 끊는다
        elif beat == "CTA" or sc.get("type") == "cta":
            limit = 200   # 결론부(오프닝 콜백 + 애국 CTA + 열린 질문 1개)는 완결 문장 우선
        else:
            limit = 130   # ≈21초. 이 이상은 한 화면이 너무 길다 → 씬을 쪼개라
        if len(text) > limit:
            errors.append(f"씬{sid}: text {len(text)}자 > 제한 {limit}자 "
                          f"(≈{len(text)/6.15:.0f}초 — 화면 전환 없이 너무 길다, 씬 분할 권장)")
        for h in (sc.get("highlight") or []):
            if h not in text:
                errors.append(f"씬{sid}: highlight '{h}'가 text에 없음")

    # ── v1.9 [VISUAL-MUST] 개념·AI 씬 화면 필수조건 (warning) ──
    #   mil_032 실측: "로봇 팔 조립" 씬에 요리 그릴이 통과 — 눈검수에 "한국·최신 설비"
    #   같은 대조 항목이 없어서 "공장이긴 하네"로 approve됐다. visual_must가 있어야
    #   시트(footage_review v2.0)·프리뷰 눈선별이 항목별 O/X 대조를 할 수 있다.
    for sc in scenes:
        fo = sc.get("footage") or {}
        if (fo.get("concept") or fo.get("ai_first")) and not fo.get("visual_must"):
            warnings.append(
                f"[VISUAL-MUST] 씬 {sc.get('id')}: visual_must 없음 — 화면 필수조건을 "
                f"1~3개 명시하라(예: [\"한국(또는 국적 안 드러남)\", \"최신 설비\"]). "
                f"없으면 눈검수가 '비슷해 보이는' 오배정을 못 거른다")

    # ── 2. 챕터 타이틀 카드 (롱폼: 상시 헤드라인 밴드 대신 챕터 전환 트랜지언트 카드) ──
    #   숏폼의 scenes_doc["headline"](영상당 1개) 체계를 그대로 안 쓴다 — 롱폼은 씬마다
    #   chapter_title이 있을 수 있고(없어도 정상), 있으면 chapter_capture_v1.0.mjs가 만든
    #   PNG가 실제로 존재하는지만 확인한다(글자수 검증은 캡처 스크립트 자체가 이미 함).
    chapter_scenes = [sc for sc in scenes if (sc.get("chapter_title") or {}).get("line1")]
    if getattr(mb, "CHAPTER_MODE", "card") == "card":
        for sc in chapter_scenes:
            png = work / "chapters" / f"scene_{sc.get('id')}@2x.png"
            if not png.exists():
                errors.append(f"씬{sc.get('id')}: chapter_title 있는데 {png.name} 없음 — "
                              f"chapter_capture_v1.0.mjs 실행 필요")
    else:
        errors.extend(lower_third_check(chapter_scenes))   # v2.0: 빌드가 직접 그리는 좌하단 소제목
    # 롱폼 v1.1: 유튜브 챕터 기능은 **최소 3개**(각 10초↑·설명 첫 줄 0:00)를 요구한다.
    #   0개일 때만 경고하던 v1.0은 "챕터 2개"를 통과시켰는데, 그러면 유튜브가 챕터를
    #   아예 인식하지 않아 탐색성·미드롤 자연 지점이 둘 다 사라진다.
    if len(chapter_scenes) < 3:
        warnings.append(f"[NO-CHAPTERS] chapter_title 씬 {len(chapter_scenes)}개 — "
                        "유튜브 챕터는 최소 3개(각 10초↑, 설명 첫 줄 0:00)라 인식 안 됨. "
                        "롱폼 권장은 5~6개(미드롤 자연 지점 겸용)")

    # ── 2.2 롱폼 v1.3: 챕터 서사 역할(arc) 검사 — "중반 늘어짐" 방어 ─────────────
    #   왜: v1.2까지 구조 규정이 "챕터1 도입 / 챕터2~5 본론 / 챕터6 정점"이라 **본론이
    #   뭉뚱그려져** 있었다. 그러면 챕터 4개를 같은 톤으로 나열해도 어떤 게이트에도 안 걸리는데,
    #   롱폼 이탈이 가장 많이 나는 게 바로 그 중반부다. 90초 재훅은 문장 단위 장치라 이걸 못 잡는다.
    #   무엇을: 챕터마다 `chapter_title.arc`에 기/승/전/결 역할 하나. **시간배분·분량 하한은
    #   두지 않는다** — 고정 시간표 템플릿은 유튜브 비진정성 콘텐츠 정책 리스크라 의도적으로 뺐다.
    #   핵심은 `전`(판이 뒤집히는 챕터)을 대본 단계에서 반드시 지정하게 만드는 것이다.
    ARC_ORDER = {"기": 0, "승": 1, "전": 2, "결": 3}
    arcs = [((sc.get("chapter_title") or {}).get("arc") or "").strip() for sc in chapter_scenes]
    if chapter_scenes:
        bad = [(sc.get("id"), a) for sc, a in zip(chapter_scenes, arcs) if a and a not in ARC_ORDER]
        for sid, a in bad:
            errors.append(f"씬{sid}: chapter_title.arc '{a}' 무효 — 기/승/전/결 중 하나")
        if not any(arcs):
            warnings.append(
                "[NO-ARC] 챕터에 arc(기/승/전/결)가 하나도 없다 — 챕터가 같은 톤으로 나열되면 "
                "중반에서 이탈한다. 챕터마다 역할을 붙이고 특히 '전'을 하나 지정하라")
        else:
            missing = [k for k in ("기", "전", "결") if k not in arcs]
            if "전" in missing:
                warnings.append(
                    "[NO-TURN] '전' 챕터가 없다 — 판이 뒤집히는 지점이 대본에 없다는 뜻이다. "
                    "가장 아껴둔 사실·반전이 들어가는 챕터 하나에 arc:\"전\"을 지정하라")
            for k in missing:
                if k != "전":
                    warnings.append(f"[ARC] '{k}' 역할 챕터 없음 — 의도한 구성이면 무시 가능")
            seq = [ARC_ORDER[a] for a in arcs if a in ARC_ORDER]
            if seq != sorted(seq):
                warnings.append(
                    f"[ARC-ORDER] 챕터 arc 순서가 기→승→전→결이 아니다({'→'.join(a for a in arcs if a)}) — "
                    "같은 역할이 여러 챕터에 걸치는 건 정상이지만(승 2~3개 등) 순서가 뒤집히면 "
                    "이야기가 역행한다. 의도한 구성인지 확인하라")

    # ── 2.5 그래픽 카드 산출물 확인 (footage.type=graphic 씬) ──
    graphic_scenes = [sc for sc in scenes if (sc.get("footage") or {}).get("type") == "graphic"]
    for sc in graphic_scenes:
        # v2.0: docu_graphic 렌더러는 mp4(애니메이션)와 png(정지)를 함께 낸다 — 둘 중 하나면 통과
        cands = [work / "graphics" / f"scene_{sc.get('id')}.mp4",
                 work / "graphics" / f"scene_{sc.get('id')}@2x.png"]
        if not any(c.exists() for c in cands):
            errors.append(f"씬{sc.get('id')}: footage.type=graphic인데 graphics/scene_{sc.get('id')}"
                          f".mp4|@2x.png 없음 — docu_graphic_v*.mjs 실행 필요")
    errors.extend(graphic_source_check(graphic_scenes))     # v2.0 [GFX-SOURCE]

    # ── 3. 팩트 게이트 ──
    for sc in scenes:
        text = sc.get("text") or ""
        if re.search(r"\d", text):
            ids = sc.get("fact_ids") or []
            if not ids:
                errors.append(f"씬{sc.get('id')}: 수치 포함인데 fact_ids 없음 — facts.json 근거 필수")
            for fid in ids:
                if fid not in facts:
                    errors.append(f"씬{sc.get('id')}: fact_id '{fid}'가 facts.json에 없음")

    # ── v2.0 다큐 게이트 ──
    if scenes:
        fe, fw = fact_quality_check(scenes, facts)
        errors.extend(fe); warnings.extend(fw)
        he, hw = hype_check(scenes)
        (warnings if skip_hype else errors).extend(he); warnings.extend(hw)
        warnings.extend(balance_check(scenes))
        errors.extend(quote_check(scenes))
        warnings.extend(location_check(scenes))

    # ── 8. 흐름 검수 (v1.4, warning) ──
    if scenes:
        warnings.extend(flow_check(scenes))
        # ── 9. [MAP] 문장↔화면 (v1.8, warning) ──
        warnings.extend(map_check(scenes))
        warnings.extend(money_check(scenes))          # v1.7 [MONEY]
        if not skip_verb:
            errors.extend(verb_check(scenes))         # v1.7 [VERB] 차단
        # ── 10. [WHY] 인과 한 칸 (v1.8, 차단 / 구 대본은 경고) ──
        if not skip_why:
            legacy = not (work / "script_draft.md").exists()
            out = why_check(scenes, legacy=legacy)
            (warnings if legacy else errors).extend(out)
            if legacy and out:
                warnings.append(
                    "[WHY] 구 워크플로 대본으로 판정(script_draft.md 없음) → 경고로만 처리. "
                    "신규 대본은 SKILL v2.3 STEP 1a(산문 선행)부터 시작해 why를 채울 것")

    # ── 4~7. TTS 실측 기반 검사 ──
    tts_dir = work / "tts"
    by_scene = {}
    for it in manifest.get("items", []):
        if it.get("path"):
            by_scene.setdefault(it["scene_id"], []).append(it)

    # ── v1.9 [AI-REQUEST] 차단: AI 컷 대기 씬이 남아 있으면 빌드 금지 ──
    #   footage_collect v3.2가 ai_first/개념 소재 0건 씬에 남긴 placeholder.
    #   ai_intake가 반입 시 해당 씬 항목을 통째로 교체하므로, 남아 있다 = 아직 미반입.
    ai_wait = sorted({it["scene_id"] for it in manifest.get("items", [])
                      if it.get("fallback") == "ai_request"} - set(by_scene.keys()))
    for sid_ in ai_wait:
        errors.append(
            f"[AI-REQUEST] 씬{sid_}: AI 컷 대기 — Veo 프롬프트(가이드 6블록+visual_must)를 "
            f"게이트 A로 Walter에게 요청 → 파일 drop → ai_intake 반입 후 preflight 재실행. "
            f"★생성은 반드시 **가로(1920×1080 이상)** — 세로컷은 롱폼에서 폭 28%대 액자다")

    # ── v1.8 [NO-MATCH] 차단: 요구 화면(shot)을 만족하는 후보가 0건인 씬 ──
    #   v1.5까지는 이런 씬이 라이브러리 잡동사니로 조용히 채워졌다(숏폼 실측과 같은 경로).
    #   footage_collect v1.6이 그 침묵 폴백을 끊고 여기로 넘긴다.
    for it in manifest.get("items", []):
        if it.get("fallback") == "no_match":
            msg = (f"[NO-MATCH] 씬{it.get('scene_id')}: {it.get('reason','')} — "
                   f"①shot 조건 완화(action/setting, exclude 축소) ②소재 확충 "
                   f"③ai_first로 승격(★가로 생성) ④문장을 화면이 있는 것으로 수정. "
                   f"비상우회 --skip-shot")
            (warnings if skip_shot else errors).append(msg)

    # ── v1.8 [SHOT] 경고: weapon·concept 씬에 요구 화면이 없다 ──
    #   롱폼은 씬당 클립 상한이 5라 슬러그만으로는 한 씬에 오배정이 여러 개 들어올 수 있다.
    #   ★출력 집약(실측): 롱폼은 씬이 30~70개라 씬마다 안내하면 preflight 출력이
    #   6.4KB → 20KB로 3.1배가 된다. 자가복구 루프마다 그 비용을 다시 내므로 한 줄로 모은다.
    no_shot = [sc.get("id") for sc in scenes
               if ((sc.get("footage") or {}).get("weapon")
                   or (sc.get("footage") or {}).get("concept"))
               and not (sc.get("footage") or {}).get("shot")]
    if no_shot:
        warnings.append(
            f"[SHOT] shot 미기입 {len(no_shot)}개 씬: {no_shot} — 슬러그만으로는 "
            f"'무엇을 하는 화면인가'가 전달되지 않는다. footage에 "
            f'{{"subject":"<슬러그>","action":"…","setting":"…","exclude":[…]}} '
            f"추가(어휘: shot_vocab.json)")

    # ── v1.8 [SHOT-LOW] 경고: 배정은 됐지만 요구 화면 적합도가 임계 미만 ──
    for it in manifest.get("items", []):
        lo = it.get("shot_low")
        if lo:
            warnings.append(
                f"[SHOT-LOW] {it.get('key','?')} (씬{it.get('scene_id')}, "
                f"점수 {lo.get('score')}/{lo.get('min')}, 불일치 {lo.get('miss') or []}): "
                f"{it.get('title','')[:50]} — 요구 화면을 충분히 만족하지 못한 배정"
                f"{'(주체는 맞지만 행위가 다르다)' if lo.get('miss') == ['action'] else ''}. "
                f"눈검수에서 이 항목부터 볼 것")

    # ── v1.4 [PORTRAIT-IN-LONG]: 세로 소재 상한·간격 ──
    if scenes and manifest:
        p_err, p_warn = portrait_check(scenes, manifest)
        warnings.extend(p_warn)
        if skip_portrait:
            if p_err:
                warnings.append(f"[PORTRAIT-IN-LONG] --skip-portrait로 차단 {len(p_err)}건 "
                                f"우회됨 — 블러 액자를 알고 내보내는 것이다: {p_err}")
        else:
            errors.extend(p_err)

    total = 0.0
    pairs = []
    for i, sc in enumerate(scenes):
        mp3 = tts_dir / f"scene_{i:03d}.mp3"
        if not mp3.exists():
            errors.append(f"씬{sc.get('id')}: TTS 없음 (scene_{i:03d}.mp3)")
            continue
        lead = mb.scene_lead(sc) if hasattr(mb, "scene_lead") else 0.0   # v2.0: 소제목 무나레이션
        dur = mb.get_audio_duration(str(mp3)) + mb.SCENE_GAP + lead
        total += dur
        pairs.append({"index": i, "scene_id": sc["id"], "dur": dur, "lead": lead})

        items = by_scene.get(sc["id"], [])
        if not items:
            if sc.get("id") not in ai_wait:   # v1.9: AI 대기 씬은 위 [AI-REQUEST]로 이미 보고
                errors.append(f"씬{sc.get('id')}: 풋티지 없음 (manifest)")
            continue
        # ── v1.8 [CONCEPT-EMPTY]: 개념 씬이 조용히 카드로 떨어진 경우 ──
        #   v3.0은 concept 씬에서 무기 소스를 안 본다(엉뚱한 전차 차단). 그 대가로 개념 소재를
        #   못 구하면 텍스트 카드가 된다 — 완성본을 보고서야 알게 되면 늦으므로 여기서 알린다.
        #   스톡 API 키(PEXELS_API_KEY·PIXABAY_API_KEY) 미발급이 가장 흔한 원인.
        if (sc.get("footage") or {}).get("concept") and all(i.get("fallback") for i in items):
            warnings.append(
                f"[CONCEPT-EMPTY] 씬 {sc.get('id')} concept='{sc['footage']['concept']}' 소재 0건 "
                f"→ 텍스트 카드로 대체됨. 원인 후보: ①.env 스톡 API 키 미설정 "
                f"②concepts.json terms가 이 개념에 안 맞음(검색어 추가) "
                f"③이 문장은 애초에 개념이 아니라 무기 씬(concept 제거)")
        for it in items:
            # ── 롱폼 v1.9 [BANNED] ──
            _bmd5 = _file_md5(it["path"]) if it.get("path") and Path(it["path"]).exists() else ""
            _brec = eyes.get(_bmd5, {}) if _bmd5 else {}
            if it.get("banned") or (isinstance(_brec, dict) and _brec.get("verdict") == "bad"):
                errors.append(f"[BANNED] 씬{sc.get('id')}: {it.get('key','?')} 금지 소재(verdict=bad) — "
                              f"{((_brec.get('note') if isinstance(_brec, dict) else '') or '')[:50]} "
                              f"→ swap으로 교체. 금지를 풀려면 Walter 확인 후 footage_review --unban")
            if not it.get("verified"):
                errors.append(f"씬{sc.get('id')}: {it.get('key','?')} 눈검수 미통과(verified≠true) — "
                              f"footage_review --sheet 후 승인 필요 (§4-6 게이트2)")
            # v1.6 게이트3(인입 눈검수): 라이브러리에 처음 들어오는 소스는 _eyes.json에
            #   기록이 남아야 통과. verified는 이 런 한정 승인이라 **다음 영상으로 안 이어진다** —
            #   그게 지금까지 "본 것이 배치까지 이어지지 않던" 끊긴 지점이었다.
            #   비용은 유한하다: 이미 기록된 소스는 재수집돼도 무통과(런당 신규 5~15건).
            if not allow_uneyed and it.get("type") == "video" and Path(it["path"]).exists():
                md5 = _file_md5(it["path"])
                if md5 and md5 not in eyes:
                    errors.append(
                        f"씬{sc.get('id')}: {it.get('key','?')} **신규 소스 눈검수 기록 없음** "
                        f"(md5 {md5[:10]}) — footage_review_v1.9 --best/--skip 또는 "
                        f"--approve로 기록 필요. 기록은 _library/_eyes.json에 영구 저장돼 "
                        f"다음 영상에서 재사용된다")
            # ── v2.0 [EVIDENCE]: 무기·visual_must 씬 실사 영상은 시각 식별 근거 필수 ──
            #   T-50을 KF-21로, FA-50을 KF-21로 오배정한 근본대응. 근거가 manifest 항목이나
            #   그 md5의 _eyes.json에 있어야 통과. AI컷은 반입 눈검수로 이미 걸러져 면제.
            fo = sc.get("footage") or {}
            needs_evidence = (fo.get("weapon") or fo.get("visual_must"))
            if (not skip_evidence and needs_evidence and it.get("verified")
                    and it.get("type") == "video" and it.get("source") != "ai"
                    and Path(it["path"]).exists()):
                has_ev = bool(it.get("evidence"))
                if not has_ev:
                    md5e = _file_md5(it["path"])
                    has_ev = bool(md5e and eyes.get(md5e, {}).get("evidence"))
                if not has_ev:
                    trigger = "weapon" if fo.get("weapon") else "visual_must"
                    errors.append(
                        f"씬{sc.get('id')}: {it.get('key','?')} **시각 식별 근거 없음** "
                        f"({trigger} 씬) — 화면에서 실제로 무엇을 봤는지 근거를 남겨야 한다. "
                        f"footage_review_v2.0 --evidence \"{it.get('key','sNN')}:꼬리번호/마킹/"
                        f"실루엣 등 식별 근거\"로 기록(제목만 믿지 말 것). 비상우회 --skip-evidence")
            if not Path(it["path"]).exists():
                errors.append(f"씬{sc.get('id')}: 파일 없음 {it['path']}")
            if it["type"] == "video":
                # v1.5 (millong_001 실전 사고): v1.4는 (1) start_s를 빼지 않아 소스 전체 길이로
                # 비교했고 (2) manifest에 duration_s가 없으면 검사 자체를 건너뛰었다. 그래서
                # "소스 115초, start_s 110초, 필요 7.07초"인 클립이 115>8.07로 통과했다.
                # 세그먼트가 짧아지면 그 씬만 짧아지는 게 아니라 **뒤쪽 씬 전체가 앞으로 당겨지고**
                # 마지막에 -shortest가 오디오 꼬리를 잘라 CTA 문장이 통째로 사라진다(실측 2.94초).
                need = dur / min(len(items), MAX_CLIPS_PER_SCENE)   # v1.6: 상한 2 → 5
                src_len = it.get("duration_s") or _probe_dur(it["path"])
                if src_len:
                    start_s = float(it.get("start_s") or 0)
                    avail = src_len - start_s
                    if avail < need - 0.05:
                        errors.append(
                            f"씬{sc.get('id')}: {it.get('key','?')} 클립 가용 {avail:.2f}s "
                            f"< 필요 {need:.2f}s (소스 {src_len:.1f}s − start_s {start_s:.1f}s, "
                            f"{need - avail:.2f}s 부족) — 세그먼트가 짧아져 뒤쪽 씬이 통째로 "
                            f"앞당겨지고 끝에서 CTA가 잘린다. start_s를 앞당기거나 소재를 교체하라 "
                            f"(military_build v1.2+는 정지 프레임 홀드로 길이만 지킨다)")
                    elif avail < need + 0.5:
                        warnings.append(
                            f"[CLIP-TIGHT] 씬{sc.get('id')} {it.get('key','?')} 여유 "
                            f"{avail - need:.2f}s — start_s를 조금 앞당겨 두는 편이 안전하다")
        vids = [it for it in items if it["type"] == "video"]
        # ── v1.6 [SEG-LONG] 세그먼트 체류시간 게이트 ──────────────────────────────
        # v1.5까지는 `len(items)==1`일 때만 봤다. 그래서 20초 씬에 클립 2개면 10초짜리
        # 세그먼트 두 개가 그대로 통과했다(millong_001 실측 평균 8.22s·최대 13.5s).
        # 한 화면이 오래 머무는 것 자체가 이탈 요인이고, 동시에 그 클립이 여러 문장을
        # 덮으면서 뒷문장과 화면이 어긋나는 '매칭 붕괴'의 직접 원인이 된다.
        # → 항목 수와 무관하게 **실제 세그먼트 길이**를 본다.
        n_use = min(len(items), MAX_CLIPS_PER_SCENE) or 1
        seg = dur / n_use
        if vids and seg > MAX_SINGLE_CLIP_DUR:
            errors.append(
                f"씬{sc.get('id')}: 세그먼트 {seg:.1f}s > {MAX_SINGLE_CLIP_DUR}s "
                f"(씬 {dur:.1f}s ÷ 클립 {n_use}개) — 한 화면이 너무 오래 머문다. "
                f"클립을 {math.ceil(dur / TARGET_SEG_DUR)}개로 늘려라 "
                f"(같은 소스의 다른 start_s 구간도 유효한 분할이다)")
        elif not vids and seg > MAX_SINGLE_CLIP_DUR:
            # 그래픽 카드 단독 씬은 '읽는 화면'이라 하드 차단하지 않는다(정보 카드가 곧 내용).
            warnings.append(
                f"[SEG-GRAPHIC] 씬{sc.get('id')} 그래픽 카드 {seg:.1f}s 단독 노출 — "
                f"읽는 시간으로는 길다. 대본을 줄이거나 카드를 2단으로 나눌 것")
        _seg_stat.append((sc.get("id"), seg, bool(vids)))

    # ── v1.6 [SEG-LONG] 영상 전체 컷 리듬 집계 ──
    _live = [s for _, s, isv in _seg_stat if isv]
    if _live:
        _avg = sum(_live) / len(_live)
        _slow = sorted([(sid, s) for sid, s, isv in _seg_stat if isv and s > SEG_AVG_WARN],
                       key=lambda x: -x[1])
        print(f"  ⏱  실사 세그먼트 평균 {_avg:.2f}s / 최대 {max(_live):.2f}s "
              f"(목표 {TARGET_SEG_DUR:.1f}s · 상한 {MAX_SINGLE_CLIP_DUR:.1f}s) · "
              f"{SEG_AVG_WARN:.1f}s 초과 {len(_slow)}개")
        if _avg > SEG_AVG_WARN:
            warnings.append(
                f"[SEG-LONG] 실사 세그먼트 평균 {_avg:.2f}s > {SEG_AVG_WARN:.1f}s — 화면 전환이 "
                f"느려 한 컷이 여러 문장을 덮는다(매칭 붕괴의 직접 원인). 긴 씬부터 클립을 "
                f"늘려라: " + ", ".join(f"씬{sid}({s:.1f}s)" for sid, s in _slow[:8]))

    # ── v2.0 [GFX-RATIO] 정보 그래픽 비중 ──
    if pairs:
        ge, gw = graphic_ratio_check(scenes, pairs, by_scene, total)
        errors.extend(ge); warnings.extend(gw)

    # ── 6. 총 길이 ──
    if pairs:
        if total < MIN_TOTAL:
            errors.append(f"총 길이 {total:.1f}s < {MIN_TOTAL}s — 대본 보강 필요")
        elif total > MAX_TOTAL:
            errors.append(f"총 길이 {total:.1f}s > {MAX_TOTAL}s — 대본 압축 필요")

    # ── 5. 자막 시뮬 (빌드와 동일 로직·폰트) ──
    if pairs:
        try:
            from PIL import Image, ImageDraw
            font, _ = mb._load_font(mb.SUB_FONT_SZ)
            draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
            ascent, descent = font.getmetrics()
            line_h = ascent + descent
            zone_h = mb._SUBZ["y1"] - mb._SUBZ["y0"]
            chunks = mb.compute_subtitle_timing(pairs, scenes, str(tts_dir))
            for ch in chunks:
                if ch.get("quote") and hasattr(mb, "quote_layout"):   # v2.0: 인용 자막은 별도 배치
                    ko, orig, qh, _ = mb.quote_layout(ch["text"], ch["quote"].get("orig", ""), draw)
                    if len(ko) > 2 or len(orig) > 2:
                        errors.append(f"[QUOTE] 인용 '{ch['text'][:16]}…' 한국어 {len(ko)}줄·원문 "
                                      f"{len(orig)}줄 — 각 2줄 이하로 줄이거나 씬을 나눌 것")
                    if mb.SUB_ANCHOR_B - qh < mb._SUBZ["y0"]:
                        errors.append(f"[QUOTE] 인용 '{ch['text'][:16]}…' 띠 {qh}px가 자막 존 상단 이탈")
                    continue
                lines = mb._wrap_lines(draw, ch["text"], font, mb.SUB_MAX_W)
                if len(lines) > mb.LAYOUT["subtitle_style"]["max_lines"]:
                    errors.append(f"자막 '{ch['text'][:16]}…' {len(lines)}줄 > 2줄")
                box_h = line_h * len(lines) + mb.SUB_LINE_GAP * (len(lines) - 1) + mb.SUB_PAD_Y * 2
                if mb.SUB_ANCHOR_B - box_h < mb._SUBZ["y0"]:
                    errors.append(f"자막 '{ch['text'][:16]}…' 박스가 subtitle 존 상단 이탈")
                if box_h > zone_h:
                    errors.append(f"자막 '{ch['text'][:16]}…' 박스 높이 {box_h}px > 존 {zone_h}px")
        except Exception as e:
            warnings.append(f"자막 시뮬 생략: {e}")

    # 헤드라인 캡처 존재

    return errors, warnings, total if pairs else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--allow-uneyed", action="store_true",
                    help="인입 눈검수 게이트 우회(비상용). 상시 사용하면 게이트가 무의미해진다")
    ap.add_argument("--skip-why", action="store_true",
                    help="[WHY] 인과 한 칸 게이트 우회(비상용). 대본 흐름 검수를 포기하는 것과 같다")
    ap.add_argument("--skip-evidence", action="store_true",
                    help="[EVIDENCE] 시각 식별 근거 게이트 우회(비상용). 화면 검수를 포기하는 것과 같다")
    ap.add_argument("--skip-verb", action="store_true",
                    help="[VERB] 건조 동사 게이트 우회(비상용)")
    ap.add_argument("--skip-portrait", action="store_true",
                    help="[PORTRAIT-IN-LONG] 세로 상한·간격 차단 우회(비상용). "
                         "폭 28%%대 블러 액자를 알고 내보내는 것이다(경고는 계속 뜬다)")
    ap.add_argument("--skip-hype", action="store_true",
                    help="[HYPE] 국뽕·선정 표현 차단을 경고로 낮춘다(비상용)")
    ap.add_argument("--skip-shot", action="store_true",
                    help="[NO-MATCH] 차단을 경고로 낮춘다(비상용). 쓰는 순간 대본↔화면 "
                         "일치 검사를 포기하는 것")
    a = ap.parse_args()
    result = check(a.run_id, allow_uneyed=a.allow_uneyed, skip_why=a.skip_why,
                   skip_evidence=a.skip_evidence, skip_portrait=a.skip_portrait,
                   skip_verb=a.skip_verb, skip_shot=a.skip_shot, skip_hype=a.skip_hype)
    errors, warnings = result[0], result[1]
    total = result[2] if len(result) > 2 else 0
    report = {"pass": not errors, "run_id": a.run_id, "total_s": round(total, 1),
              "errors": errors, "warnings": warnings}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
