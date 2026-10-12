#!/usr/bin/env python3
"""
[롱폼 v1.5] 다큐 스타일 화면 (2026-10-12, Walter 지시 — 참고: 유튜브 '다큐9분').
  ① 폰트: layout.json fonts.main(GoshinGothic-SemiBold) 단일 소스. 롱폼 assets/fonts에 없으면
     fonts.fallbacks(숏폼 폴더 공유본) → AppleSDGothicNeo 순으로 찾는다.
  ② 나레이션 자막(A안): 둥근 검은 박스 → **화면 폭 전체 반투명 띠** + 흰 글자(그림자).
     숫자 노란 강조는 다큐 톤에 맞지 않아 layout subtitle_style.highlight_numbers=false가 기본.
  ③ 인용 자막(scene.quote) 신설: 좌측 흰 라벨 박스(발화 주체) + 한국어 + 원문 2단.
     인용 씬은 자막 1장이 씬 전체를 덮고, 그 동안 배경을 dim_alpha만큼 눌러 '기록'임을 표시한다.
  ④ 챕터 소제목: 전체화면 카드(chapters/*.png) → **좌측 하단 lower third**를 빌드가 직접 그린다
     (chapter_capture mjs 불필요). chapter_title이 있는 씬은 앞에 lead_s(기본 3.0s) 동안
     나레이션 없이 화면+BGM+소제목만 나오고, 그다음 나레이션이 시작된다 — 자막 띠와
     소제목이 시간상 절대 겹치지 않는다. lead는 총 길이에 포함된다(preflight도 같은 함수로 계산).
     layout.chapter_mode="card"면 v1.4 동작(전체화면 카드) 그대로.
  ⑤ 장소·시각 슈퍼(scene.location) 신설: 씬 시작 dur_s 동안 좌측 상단 한 줄.
  ⑥ 그래픽 영상: footage type=graphic 항목의 path가 .mp4/.mov면 HTML 애니메이션 렌더본으로 보고
     영상 입력으로 붙인다(확대·블러 없이 1920×1080 그대로, 부족분은 마지막 프레임 홀드).
     .png는 v1.4와 같은 미세 줌.
  ⑧ 16:9 소재 풀블리드(layout.fit.fullbleed_landscape, 기본 true): v1.10의 "항상 90% 축소+블러
     여백"은 숏폼(9:16에 가로 피사체가 잘리는 문제)에서 온 규칙인데, 롱폼에서 16:9 소재는 잘릴 것이
     없어 테두리만 생겼다(다큐 화면과 가장 다른 지점). 캔버스 비율 ±tol 안의 소재만 화면을 꽉 채우고
     아주 약한 줌(1.0↔zoom)만 준다. 4:3·1:1 등 나머지는 v1.10 fit 그대로. false면 v1.4 동작.
  ⑦ caption_note(자료화면·AI 고지)가 layout에 좌표가 없어 y=1218(화면 밖)로 그려져 **롱폼에서
     한 번도 보이지 않던 버그** 수정 — layout.caption_note_style을 좌측 상단으로 지정.
[롱폼 v1.3] 씬당 클립 상한 2개 → MIL_LONG_MAX_CLIPS_PER_SCENE(기본 5) (2026-08-18, Walter 지시).
  증상: millong_001 완성본에서 "한 화면이 너무 오래 나온다" + "소재와 대본이 안 맞는다".
  원인: `[:2]` 하드코딩이 씬당 클립을 2개로 잘라 20초짜리 씬도 10초 세그먼트 2개가 됐다.
  실측 평균 세그먼트 8.22s / 최대 13.5s / 60씬 중 27씬이 8초 초과.
  클립 하나가 2~3문장을 덮으니 앞문장에 맞춘 화면이 뒷문장에서 어긋난다 —
  "간격이 길다"와 "매칭이 안 맞는다"는 같은 뿌리다.
  → manifest에 배정된 항목을 상한까지 전부 쓴다(manifest가 계획의 단일 소스).
  세그먼트 보관(_library/_segments)에도 같은 상한을 적용해 계산이 어긋나지 않게 했다.

v1.4 (2026-10-07): 사용 구간 클립(_library/_segments/*.mp4) 저장 중단, index.json 기록만 유지.

[롱폼 v1.1] 숏폼 military_build_v1.11 이식(2026-08-09).
  tts_text(음성 낭독 교정본)가 자막으로 새던 버그 차단 — timing.json의 text는 합성 입력이라
  발음 교정본이 들어 있다(음성 "일 점 칠" ↔ 자막 "1.7"). tts_text가 있는 씬은 원문 text로
  자막을 그리고 타이밍만 청크 전체 구간에 재분배한다. 롱폼 고유 로직(챕터 카드·graphic 체인·
  1920x1080)은 v1.0 그대로.
"""

"""
military_build_v1.6.py — 밀리터리 숏폼 4레이어 합성기 (설계서_v1.7 §6-2, T6+T7)

레이어: L1 실사 풋티지 → L2 스크림 → L3 제목 밴드 → L4 자막(청크 타이밍)
자막 스택은 ../숏폼_자동화/video_build_v3.2.py 이식(무변경), 좌표만 layout.json 유도.

v1.1 (T7):
  ① 사진 Ken Burns — zoompan(줌 1→1.08 + 팬 방향 씬 순환), 2배 사전 스케일로 지터 방지
  ② BGM — assets/bgm/*.mp3 첫 트랙을 -28 LUFS 베드로 amix (없으면 경고 후 스킵)
  ③ 씬당 최대 2클립 하드컷 (manifest 항목 순서대로 씬 길이 균등 분할)
  ④ loudnorm 2패스 (측정→linear 적용) — v1.0 단일패스 언더슛(-15.5) 교정
  ⑤ 줌펀치 — 첫 씬 제외 모든 세그먼트 시작 5프레임 1.06→1.0
v1.0 (T6): 4레이어 합성, crop focus, 2패스 인코딩(crf16→18)
v1.2: manifest start_s 지원 — 같은 영상의 서로 다른 구간을 씬별로 잘라 사용 (collector v1.5 연동)
v1.5: 씬별 자료화면/AI 연출 캡션(scene.caption_note) — 타 무기 자료화면·AI 컷 사용 시
      화면 좌측(자막 밴드 위)에 작은 고지 박스 렌더 (사실 왜곡 방지, layout.caption_note_style)
v1.3 (Walter 피드백): ①item focus 우선(눈검수 --focus 기록값 > 씬 focus) — 피사체 중앙 크롭
  ②Ken Burns 줌인/줌아웃 교대(씬 홀짝) ③사용 세그먼트를 _library/_segments/에 자동 보관
v1.6 (피사체 센터링 강화 — footage_review v1.6 연동):
  ① 크롭 공식 교정: 기존 x=(iw-W)*f는 피사체를 원본과 같은 상대 위치에 둘 뿐 중앙 이동이
     아니었음 → x=clip(f*iw-W/2, 0, iw-W)로 피사체를 실제 중앙에 배치 (경계는 클램프)
  ② 세로 focus_y 지원: y도 clip(fy*ih-H/2, 0, ih-H) — 수직 구도(미사일 상승) 대응
  ③ 사진 Ken Burns를 피사체 앵커로: 사전 크롭이 피사체를 중앙에 두므로 팬 방향 순환을
     중앙 고정 줌(인/아웃 교대)으로 대체 — 팬이 피사체 반대로 가던 문제 제거
  ④ 동적 크롭: manifest focus_track [[t,fx],...] 있으면 크롭 x를 t의 조각별 선형 표현식으로
     생성해 이동 피사체 추적 (트랙은 start_s 기준 상대시간 — trim 후 t=0과 정렬)

v1.8 (피사체 전체보존 — footage_review v1.7 bbox 연동):
  ─ 문제: cover(force_original_aspect_ratio=increase) 크롭은 9:16을 항상 꽉 채우려
     소스를 확대·재단 → 가로로 넓은 피사체(전투기·함정·TEL)는 좌우가 무조건 잘림.
  ─ 해결: manifest `bbox`[x0,y0,x1,y1]로 "cover가 피사체를 자르는가"를 판정(fit_decision).
     자르면 fit 전환 — 블러·어둡게 처리한 배경 위에 피사체 전체를 축소 배치(중앙 정렬).
     엄격 모드: cover 가시영역의 98%(FIT_TOL) 초과로 넓으면 곧바로 fit → 피사체 안 잘림.
     fit 세그먼트는 피사체 재재단 방지를 위해 줌펀치·Ken Burns 미적용(정지 fit).
  ─ bbox 없으면(구버전 manifest·감지실패) 기존 cover 동작 유지(하위호환).

v1.9 (fit 세그먼트 정지 이미지 문제 해결 — Walter 피드백 "움직임이 없다"):
  ─ v1.8의 "정지 fit"이 화면 전체에서 차지하는 비중이 커지면서(넓은 피사체 다수)
     사진/영상이 그냥 멈춰 보이는 구간이 늘어남 → 안전하게 움직임 복원.
  ─ 전경(피사체) 안전존 줌: fgw 목표 크기(FIT_MARGIN 꽉 채운 값)는 그대로 상한으로 유지,
     FIT_FG_START(0.93)~1.0 사이에서만 scale(eval=frame, t 변수)로 줌인/줌아웃 — 상한을
     넘지 않으므로 피사체 재재단 없음.
  ─ 배경(블러) 레이어 독립 줌: 이미 cover로 꽉 채운 블러 배경이라 크롭 위치가 조금 바뀌어도
     피사체와 무관 — zoompan(FIT_BG_ZOOM)으로 전경과 반대 위상 줌 → 패럴랙스 효과.
  ─ 씬 홀짝(scene_order)으로 전경/배경 방향 교대, 기존 사진 Ken Burns와 동일한 관례 유지.

v1.10 (Walter 피드백 "테두리 고정하고 안에서만 움직여야 안 조잡하다" + fit 예외 전면 폐지):
  ─ 문제1: v1.9는 오버레이 컨테이너 자체 크기(테두리)가 매 프레임 변해 배경 패럴랙스와
     겹치면 두 레이어가 서로 다른 리듬으로 움직여 산만함.
  ─ 해결1: 전경 컨테이너 크기(fg_w,fg_h)를 픽셀 정수로 미리 계산해 오버레이 테두리를
     완전히 고정. 움직임은 컨테이너보다 1/FIT_FG_START배 크게 미리 스케일한 버퍼를
     zoompan으로 크롭해 만든다 — 컨테이너 크기(zoompan 출력 s=)는 절대 안 변하고,
     크롭 중심은 피사체(bbcx,bbcy)에 고정하며, z 상한이 정확히 기존 안전 상한(fg_w)과
     같아 피사체가 그 이상 커지지 않는다(재재단 없음).
  ─ 문제2: FULLFRAME 가드("이미 꽉 찬 샷")·FIT_TOL 관용("cover로도 안 잘림")이 남아있어
     일부 컷만 풀블리드로 나가고 나머지는 블러여백 fit으로 나가 톤이 안 맞고 반복될수록 산만함.
  ─ 해결2: fit_decision에서 두 예외 모두 `_WHOLE_FIT`(전체 프레임을 그대로 fit)으로 대체 —
     이제 fit_decision은 절대 None을 반환하지 않는다. bbox 감지 실패도 소스 전체를
     피사체로 간주한 레터박스로 강제 — 풀블리드 화면 자체가 나오지 않음.
  ─ 부수 정리: cover 전용이던 track_x_expr()·줌펀치(PUNCH_*)·일반 Ken Burns(KB_ZOOM) 경로가
     완전히 도달 불가능해져 삭제. segment_filter는 fit 전용 단일 경로로 단순화.

사용:
  python3 military_build_v1.10.py --run-id <run> [--out "<절대경로>"]
종료 코드: 0=성공 / 1=검증 실패 / 2=격리 위반
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAYOUT = json.loads(open(os.path.join(BASE_DIR, "layout.json"), encoding="utf-8").read())

FPS       = LAYOUT["canvas"]["fps"]
CANVAS_W  = LAYOUT["canvas"]["w"]
CANVAS_H  = LAYOUT["canvas"]["h"]
TARGET_I, TARGET_TP, TARGET_LRA = -14.0, -1.5, 11.0   # §1-2
BGM_I     = -28.0                                      # BGM 베드 레벨
SCENE_GAP = 0.15

# v1.3: 씬당 클립 상한. v1.2까지 `[:2]` 하드코딩이라 20초 씬도 10초 세그먼트 2개가 나왔다.
# 롱폼은 씬이 4~20초로 폭이 넓어 상한 2개로는 "한 화면이 오래 머무는" 구간을 못 막는다.
# footage_collect의 need 계산(TARGET_SEG_DUR 5.0s)이 씬당 최대 4개까지 만들므로 5로 잡아
# 수기 배정 여유를 1개 남긴다. manifest가 계획의 단일 소스이고 이건 안전 상한일 뿐이다.
MAX_CLIPS_PER_SCENE = int(os.environ.get("MIL_LONG_MAX_CLIPS_PER_SCENE", "5"))

# v1.10: 모든 세그먼트가 전체보존(fit·블러여백) 경로만 사용 — cover 풀블리드 폐지.
# footage_review v1.8과 반드시 동일 값 유지(눈검수 미리보기 = 실제 빌드).
CANVAS_AR    = CANVAS_W / CANVAS_H     # 9:16
FIT_MARGIN   = 0.90                    # fit 시 피사체가 캔버스 각 축의 90%까지만 차지
FIT_TOL      = 0.98                    # cover 가시영역의 98% 초과로 넓으면 잘림→fit (엄격)
FULLFRAME_W  = 0.95                    # bbox 가로≥95% AND
FULLFRAME_H  = 0.90                    # 세로≥90%면 '이미 꽉 찬 샷'→그래도 강제 축소(_WHOLE_FIT, 풀블리드 예외 폐지)
FIT_BLUR     = 24                      # 배경 블러 sigma
FIT_DARK     = 0.12                    # 배경 밝기 감쇠(-0.12)
FIT_BG_ZOOM  = 1.06                    # 배경(블러) 줌 폭 — 크롭 위치가 바뀌어도 무관, 패럴랙스용
FIT_FG_START = 0.93                    # 전경 내부 줌 버퍼 비율 — 컨테이너(테두리)는 고정, 그 1/FIT_FG_START배
                                        # 크게 미리 스케일한 버퍼를 zoompan으로 크롭해 내부만 움직임(재재단 없음)

# 자막 박스 — layout.json subtitle 존 유도 (하드코딩 금지)
_SUBZ        = LAYOUT["zones"]["subtitle"]
_SST         = LAYOUT["subtitle_style"]
SUB_MAX_W    = _SUBZ["max_w"]
SUB_ANCHOR_B = _SUBZ["y1"]                                      # v1.5: 띠 아래끝 = 존 하단
SUB_FONT_SZ  = _SST.get("font_size", 50)                         # v1.4: layout.json 단일 소스
SUB_PAD_X    = 32
SUB_PAD_Y    = int(_SST.get("band_pad_y", 22))                  # v1.5: 띠 상하 여백
SUB_RADIUS   = 8
SUB_LINE_GAP = int(_SST.get("line_gap", 10))
SUB_FADE_IN  = 0.12
SUB_ALIGN    = _SST.get("align", "center")
SUB_HILITE   = bool(_SST.get("highlight_numbers", False))       # v1.5: 다큐 톤 — 기본 끔
SUB_SHADOW   = bool(_SST.get("shadow", True))

QUOTE   = LAYOUT.get("quote_style", {})
LTHIRD  = LAYOUT.get("lower_third_style", {})
LOCSUP  = LAYOUT.get("location_super_style", {})
CHAPTER_MODE = LAYOUT.get("chapter_mode", "card")               # v1.5: "lower_third" | "card"(v1.4)


def _hex(c, a=255):
    c = (c or "#FFFFFF").lstrip("#")
    return tuple(int(c[i:i+2], 16) for i in (0, 2, 4)) + (a,)


# v1.5: 폰트 단일 소스 = layout.fonts.main → fonts.fallbacks → subtitle_style.font(구버전 layout) → 시스템
_FONTS = LAYOUT.get("fonts", {})
FONT_PRIMARY   = os.path.join(BASE_DIR, _FONTS.get("main") or _SST["font"])
FONT_FALLBACKS = ([os.path.normpath(os.path.join(BASE_DIR, f)) for f in _FONTS.get("fallbacks", [])]
                  + [os.path.join(BASE_DIR, _SST["font"]),
                     "/System/Library/Fonts/AppleSDGothicNeo.ttc"])

HILITE_COLOR   = _hex(_SST.get("highlight_color", "#FFD400"))
HILITE_OUTLINE = (60, 45, 0, 200)
NUM_PATTERN = re.compile(r'[+\-]?\d[\d,.]*\s*[%원만억천개회년월일배도시분초명건]?')

EXIT_OK, EXIT_VALIDATION, EXIT_ISOLATION = 0, 1, 2


# ══ 자막 분할·타이밍 (video_build_v3.2 이식 — 무변경) ══════════════════════════

_SENT_BOUNDARY = re.compile(r'(?<=[.!?。！？])(?=\s)')
_NUM_COMMA = re.compile(r'(?<=\d),(?=\d)')  # v1.7: "2,400" 같은 천단위 콤마는 문장 구분자가 아님


def _protect_num_commas(text):
    return _NUM_COMMA.sub('\x00', text)


def _restore_num_commas(text):
    return text.replace('\x00', ',')


def split_korean_natural(text, max_chars=12):
    if not text:
        return []
    sentences = re.split(r'(?<=[,，.。!?！？])\s*', _protect_num_commas(text))
    result = []
    for sent in sentences:
        sent = _restore_num_commas(sent.strip())
        if not sent:
            continue
        words = sent.split()
        current = ""
        for word in words:
            trial = (current + " " + word).strip() if current else word
            if len(trial) > max_chars and current:
                result.append(current)
                current = word
            else:
                current = trial
        if current:
            result.append(current)
    return [r for r in result if r.strip()]


def _split_sentences(text):
    parts = [p.strip() for p in _SENT_BOUNDARY.split(text) if p.strip()]
    return parts if parts else [text.strip()]


def _fits_one_line(text, draw, font, max_w):
    if draw is None or font is None:
        return True
    return draw.textlength(text, font=font) <= max_w


def _split_words_to_fit(text, draw, font, max_w):
    words = text.split()
    if not words:
        return [text]
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip() if cur else w
        if _fits_one_line(trial, draw, font, max_w):
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [text]


def _split_to_fit(text, draw, font, max_w):
    if _fits_one_line(text, draw, font, max_w):
        return [text]
    comma_parts = [_restore_num_commas(p.strip()) for p in re.split(r'(?<=[,，])\s*', _protect_num_commas(text)) if p.strip()]
    if len(comma_parts) <= 1:
        return _split_words_to_fit(text, draw, font, max_w)
    merged, cur = [], ""
    for p in comma_parts:
        trial = (cur + " " + p).strip() if cur else p
        if _fits_one_line(trial, draw, font, max_w):
            cur = trial
        else:
            if cur:
                merged.append(cur)
            cur = p
    if cur:
        merged.append(cur)
    result = []
    for m in merged:
        if _fits_one_line(m, draw, font, max_w):
            result.append(m)
        else:
            result.extend(_split_words_to_fit(m, draw, font, max_w))
    return result or [text]


def _wrap_chunk_by_time(text, start, end, draw, font, max_w):
    sents = _split_sentences(text)
    pieces = []
    for s in sents:
        pieces.extend(_split_to_fit(s, draw, font, max_w))
    if not pieces:
        pieces = [text]
    if len(pieces) <= 1:
        return [{"text": pieces[0], "start": start, "end": end}]
    total_ch = sum(max(len(p), 1) for p in pieces)
    span = max(end - start, 0.2)
    out, t = [], start
    for j, p in enumerate(pieces):
        e = end if j == len(pieces) - 1 else t + span * len(p) / total_ch
        out.append({"text": p, "start": t, "end": max(e, t + 0.2)})
        t = e
    return out


def scene_lead(scene):
    """v1.5: 챕터 소제목(lower third) 씬 앞에 붙는 무나레이션 구간(초).
    preflight가 같은 함수를 불러 총 길이·자막 시뮬을 계산한다(이중 구현 금지)."""
    if CHAPTER_MODE != "lower_third":
        return 0.0
    if not (scene.get("chapter_title") or {}).get("line1"):
        return 0.0
    return float(LTHIRD.get("lead_s", 3.0))


def compute_subtitle_timing(pairs, scenes, tts_dir):
    font = draw = None
    try:
        from PIL import Image, ImageDraw
        font, _ = _load_font(SUB_FONT_SZ)
        draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    except Exception:
        pass
    result, t_offset = [], 0.0
    for pair in pairs:
        idx = pair["index"]
        scene = scenes[idx] if 0 <= idx < len(scenes) else {}
        lead = float(pair.get("lead", 0.0))                  # v1.5: 소제목 구간만큼 자막도 늦춘다
        scene_dur = pair["dur"] - lead
        t_scene0 = t_offset
        t_offset += lead
        # v1.5: 인용 씬은 자막 1장(라벨+한국어+원문)이 나레이션 구간 전체를 덮는다
        q = scene.get("quote") or {}
        if q.get("speaker"):
            disp = (scene.get("text") or "").strip()
            result.append({"text": disp, "start": t_offset, "end": t_scene0 + pair["dur"] - SCENE_GAP,
                           "quote": {"speaker": q.get("speaker", ""), "orig": q.get("orig", "")}})
            t_offset = t_scene0 + pair["dur"]
            continue
        timing_path = os.path.join(tts_dir, f"scene_{idx:03d}_timing.json")
        if os.path.exists(timing_path):
            with open(timing_path, encoding="utf-8") as f:
                chunk_timing = json.load(f)
            # 롱폼 v1.1 (숏폼 v1.11 이식): tts_text(음성 낭독 교정본)가 자막으로 새는 것 차단.
            #   timing.json의 text는 실제 합성한 문장이라 tts_text가 들어 있다
            #   (예: 음성 "일 점 칠" ↔ 자막 "1.7"). 자막은 원문 text로 그리고,
            #   타이밍은 청크 전체 구간(첫 start~마지막 end)에 맞춰 재분배한다.
            if scene.get("tts_text") and chunk_timing:
                disp = (scene.get("text") or "").strip()
                if disp:
                    s = t_offset + chunk_timing[0].get("start", 0.0)
                    last_end = chunk_timing[-1].get("end", chunk_timing[-1].get("start", 0.0) + scene_dur)
                    e = max(t_offset + last_end, s + 0.2)
                    result.extend(_wrap_chunk_by_time(disp, s, e, draw, font, SUB_MAX_W))
                    t_offset = t_scene0 + pair["dur"]
                    continue
            for ct in chunk_timing:
                txt = (ct.get("text") or "").strip()
                if not txt:
                    continue
                s = t_offset + ct["start"]
                e = max(t_offset + ct.get("end", ct["start"] + scene_dur), s + 0.2)
                result.extend(_wrap_chunk_by_time(txt, s, e, draw, font, SUB_MAX_W))
        else:
            text = (scene.get("text") or "").strip()
            if text:
                sub_chunks = split_korean_natural(text)
                if sub_chunks:
                    total_ch = sum(max(len(c), 1) for c in sub_chunks)
                    ts = t_offset
                    for sc in sub_chunks:
                        sc_dur = max(scene_dur * len(sc) / total_ch, 0.2)
                        result.append({"text": sc, "start": ts, "end": ts + sc_dur})
                        ts += sc_dur
        t_offset = t_scene0 + pair["dur"]
    return result


# ══ 자막 PNG 렌더·오버레이 (v3.2 이식) ═════════════════════════════════════════

def _load_font(size):
    from PIL import ImageFont
    for fp in [FONT_PRIMARY] + FONT_FALLBACKS:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size=size), fp
            except Exception:
                continue
    return ImageFont.load_default(), "default"


def _wrap_lines(draw, text, font, max_w):
    words = text.split()
    if not words:
        return [text]
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if not cur or draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _draw_line_highlighted(draw, text, font, cx, ly, text_color, hilite_color, outline_col,
                           align="center"):
    segs, last = [], 0
    for m in (NUM_PATTERN.finditer(text) if SUB_HILITE else []):
        if m.start() > last:
            segs.append((text[last:m.start()], False))
        segs.append((text[m.start():m.end()], True))
        last = m.end()
    if last < len(text):
        segs.append((text[last:], False))
    if not segs:
        segs = [(text, False)]
    total_w = sum(draw.textlength(s, font=font) for s, _ in segs)
    x = cx - total_w / 2 if align == "center" else cx
    for s, is_num in segs:
        col = hilite_color if is_num else text_color
        if SUB_SHADOW:   # v1.5: 외곽선 대신 부드러운 그림자(다큐 톤)
            draw.text((x + 2, ly + 3), s, fill=(0, 0, 0, 170), font=font, anchor="lm")
        draw.text((x, ly), s, fill=col, font=font, anchor="lm")
        x += draw.textlength(s, font=font)


def subtitle_band_h(n_lines, line_h):
    """v1.5: 나레이션 자막 띠 높이(px). preflight 자막 시뮬도 이 함수를 쓴다."""
    return line_h * n_lines + SUB_LINE_GAP * (n_lines - 1) + SUB_PAD_Y * 2


def quote_layout(text, orig, draw=None):
    """v1.5: 인용 자막 배치 계산 — (ko_lines, orig_lines, band_h, fonts). preflight 공용."""
    from PIL import Image, ImageDraw
    draw = draw or ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    f_ko, _ = _load_font(int(QUOTE.get("ko_font_size", 46)))
    f_or, _ = _load_font(int(QUOTE.get("orig_font_size", 32)))
    f_lb, _ = _load_font(int(QUOTE.get("label_font_size", 44)))
    max_w = int(QUOTE.get("text_max_w", 1480))
    ko_lines = _wrap_lines(draw, text, f_ko, max_w) if text else []
    or_lines = _wrap_lines(draw, orig, f_or, max_w) if orig else []
    a, d = f_ko.getmetrics(); h_ko = a + d
    a, d = f_or.getmetrics(); h_or = a + d
    gap = int(QUOTE.get("line_gap", 8))
    pad = int(QUOTE.get("band_pad_y", 26))
    body = (h_ko * len(ko_lines) + h_or * len(or_lines)
            + gap * max(len(ko_lines) + len(or_lines) - 1, 0))
    return ko_lines, or_lines, body + pad * 2, (f_ko, f_or, f_lb, h_ko, h_or, gap, pad)


def _quote_png(chunk, png_path):
    """v1.5: 다큐9분 교신 자막 형식 — 화면 전체 dim + 하단 띠 + 좌측 흰 라벨 박스 + 한국어/원문."""
    from PIL import Image, ImageDraw
    q = chunk["quote"]
    ko_lines, or_lines, band_h, (f_ko, f_or, f_lb, h_ko, h_or, gap, pad) = \
        quote_layout(chunk["text"], q.get("orig", ""))
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H),
                    (0, 0, 0, int(255 * float(QUOTE.get("dim_alpha", 0.35)))))
    d = ImageDraw.Draw(img)
    y1 = SUB_ANCHOR_B
    y0 = y1 - band_h
    d.rectangle([(0, y0), (CANVAS_W, y1)],
                fill=_hex(_SST.get("band_color", "#000000"),
                          int(255 * float(_SST.get("band_alpha", 0.55)))))
    lw = int(QUOTE.get("label_box_w", 300))
    d.rectangle([(0, y0), (lw, y1)], fill=_hex(QUOTE.get("label_bg", "#FFFFFF")))
    d.text((lw - 28, (y0 + y1) // 2), q.get("speaker", ""), font=f_lb,
           fill=_hex(QUOTE.get("label_color", "#000000")), anchor="rm")
    x = int(QUOTE.get("text_x", 340))
    y = y0 + pad
    for ln in ko_lines:
        d.text((x + 2, y + h_ko // 2 + 3), ln, font=f_ko, fill=(0, 0, 0, 160), anchor="lm")
        d.text((x, y + h_ko // 2), ln, font=f_ko, fill=_hex(_SST.get("text_color", "#FFFFFF")), anchor="lm")
        y += h_ko + gap
    for ln in or_lines:
        d.text((x, y + h_or // 2), ln, font=f_or, fill=_hex(QUOTE.get("orig_color", "#D9D9D9")), anchor="lm")
        y += h_or + gap
    img.save(png_path, "PNG")


def create_subtitle_pngs(chunks_timed, temp_dir):
    from PIL import Image, ImageDraw
    os.makedirs(temp_dir, exist_ok=True)
    font, font_path = _load_font(SUB_FONT_SZ)
    print(f"  폰트: {os.path.basename(font_path)}")
    if "GoshinGothic" not in font_path:
        print(f"  ⚠️ 지정 폰트(GoshinGothic) 미발견 — {font_path}로 대체. "
              f"assets/fonts/에 파일을 두거나 layout.json fonts.fallbacks 경로를 확인할 것")
    band_fill = _hex(_SST.get("band_color", "#000000"), int(255 * float(_SST.get("band_alpha", 0.55))))
    text_color, outline_col = _hex(_SST.get("text_color", "#FFFFFF")), (30, 30, 30, 200)
    ascent, descent = font.getmetrics()
    line_h = ascent + descent
    dummy_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    result = []
    for i, chunk in enumerate(chunks_timed):
        png_path = os.path.join(temp_dir, f"sub_{i:04d}.png")
        if chunk.get("quote"):                      # v1.5: 인용 자막 — 화면 전체 PNG(y=0)
            _quote_png(chunk, png_path)
            result.append({**chunk, "png_path": png_path, "box_h": CANVAS_H, "y_abs": 0})
            continue
        lines = _wrap_lines(dummy_draw, chunk["text"], font, SUB_MAX_W)
        n = len(lines)
        box_h = subtitle_band_h(n, line_h)
        # v1.5: 화면 폭 전체 반투명 띠(다큐9분 형식). 둥근 박스 폐지
        img = Image.new("RGBA", (CANVAS_W, box_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, 0), (CANVAS_W, box_h)], fill=band_fill)
        cx = CANVAS_W // 2 if SUB_ALIGN == "center" else (CANVAS_W - SUB_MAX_W) // 2
        for li, ln in enumerate(lines):
            ly = SUB_PAD_Y + li * (line_h + SUB_LINE_GAP) + line_h // 2
            _draw_line_highlighted(draw, ln, font, cx, ly, text_color, HILITE_COLOR, outline_col,
                                   align=SUB_ALIGN)
        img.save(png_path, "PNG")
        result.append({**chunk, "png_path": png_path, "box_h": box_h})
    print(f"  ✓ 자막 PNG {len(result)}장 생성 (인용 {sum(1 for c in result if c.get('quote'))}장)")
    return result


def _shear_text_img(text, font, color, shear):
    """이탤릭 폰트 없이 기울임(다큐9분 부제 이탤릭) — 텍스트를 따로 그려 아핀 변환."""
    from PIL import Image, ImageDraw
    dd = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    w = int(dd.textlength(text, font=font)) + 8
    a, d = font.getmetrics()
    h = a + d + 8
    extra = int(h * abs(shear)) + 4
    im = Image.new("RGBA", (w + extra, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((extra, 4), text, font=font, fill=color)
    # x' = x + shear*y → 위쪽이 오른쪽으로 기운다
    return im.transform(im.size, Image.AFFINE, (1, shear, -shear * h, 0, 1, 0), resample=Image.BICUBIC)


def lower_third_png(chapter_title, png_path):
    """v1.5: 좌측 하단 소제목 — line1 큰 글씨, line2 기울임 작은 글씨, 좌하단 비네트."""
    from PIL import Image, ImageDraw, ImageFilter
    f1, _ = _load_font(int(LTHIRD.get("line1_size", 78)))
    f2, _ = _load_font(int(LTHIRD.get("line2_size", 42)))
    l1 = (chapter_title.get("line1") or "").strip()
    l2 = (chapter_title.get("line2") or "").strip()
    x = int(LTHIRD.get("x", 96))
    bottom = int(LTHIRD.get("bottom", 975))
    gap = int(LTHIRD.get("line_gap", 14))
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    # 좌하단 비네트(글자 가독성) — 세로·가로 그라데이션 곱
    va = float(LTHIRD.get("vignette_alpha", 0.55))
    if va > 0:
        vig = Image.new("L", (CANVAS_W, CANVAS_H), 0)
        vd = ImageDraw.Draw(vig)
        vd.ellipse([(-700, CANVAS_H - 520), (1300, CANVAS_H + 420)], fill=int(255 * va))
        vig = vig.filter(ImageFilter.GaussianBlur(140))
        img.paste((0, 0, 0, 255), (0, 0), vig)
    a1, d1 = f1.getmetrics()
    a2, d2 = f2.getmetrics()
    y2 = bottom - (a2 + d2) if l2 else bottom
    y1 = y2 - gap - (a1 + d1) if l2 else bottom - (a1 + d1)
    sh = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sa = int(255 * float(LTHIRD.get("shadow_alpha", 0.75)))
    sd.text((x + 3, y1 + 4), l1, font=f1, fill=(0, 0, 0, sa))
    sh = sh.filter(ImageFilter.GaussianBlur(4))
    img = Image.alpha_composite(img, sh)
    d = ImageDraw.Draw(img)
    d.text((x, y1), l1, font=f1, fill=_hex(LTHIRD.get("color", "#FFFFFF")))
    if l2:
        t2 = _shear_text_img(l2, f2, _hex(LTHIRD.get("line2_color", "#F0F0F0")),
                             float(LTHIRD.get("line2_shear", 0.21)))
        t2s = _shear_text_img(l2, f2, (0, 0, 0, sa), float(LTHIRD.get("line2_shear", 0.21)))
        img.alpha_composite(t2s, (x - 2 + 2, y2 - 4 + 3))
        img.alpha_composite(t2, (x - 2, y2 - 4))
    img.save(png_path, "PNG")


def create_overlay_pngs(pairs, scenes, temp_dir):
    """v1.5: 소제목(lower third) + 장소·시각 슈퍼. 반환 항목은 자막과 같은 오버레이 경로를 탄다
    (y_abs=0 화면 전체 PNG, fade_out 지원)."""
    from PIL import Image, ImageDraw
    os.makedirs(temp_dir, exist_ok=True)
    out, t_acc = [], 0.0
    fade = float(LTHIRD.get("fade_s", 0.35))
    for pp in pairs:
        sc = scenes[pp["index"]]
        t0 = t_acc
        t_acc += pp["dur"]
        ct = sc.get("chapter_title") or {}
        if CHAPTER_MODE == "lower_third" and ct.get("line1"):
            pth = os.path.join(temp_dir, f"lt_{pp['index']:03d}.png")
            lower_third_png(ct, pth)
            s = t0 + float(LTHIRD.get("show_from_s", 0.25))
            e = t0 + max(pp.get("lead", 0.0), 1.5)
            out.append({"text": ct.get("line1"), "start": s, "end": e, "png_path": pth,
                        "box_h": CANVAS_H, "y_abs": 0, "fade_in": fade, "fade_out": fade})
        loc = (sc.get("location") or "").strip()
        if loc:
            f, _ = _load_font(int(LOCSUP.get("font_size", 36)))
            img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            x, y = int(LOCSUP.get("x", 96)), int(LOCSUP.get("y", 72))
            d.text((x + 2, y + 3), loc, font=f, fill=(0, 0, 0, 180))
            d.text((x, y), loc, font=f, fill=(255, 255, 255, 240))
            pth = os.path.join(temp_dir, f"loc_{pp['index']:03d}.png")
            img.save(pth)
            ls = t0 + pp.get("lead", 0.0)
            out.append({"text": loc, "start": ls,
                        "end": min(ls + float(LOCSUP.get("dur_s", 3.5)), t0 + pp["dur"]),
                        "png_path": pth, "box_h": CANVAS_H, "y_abs": 0,
                        "fade_in": float(LOCSUP.get("fade_s", 0.3)),
                        "fade_out": float(LOCSUP.get("fade_s", 0.3))})
    if out:
        print(f"  ✓ 소제목·장소 슈퍼 {len(out)}개 생성")
    return out


def create_note_pngs(pairs, scenes, temp_dir):
    """씬별 caption_note(자료화면·AI 고지)를 좌측 하단 작은 박스 PNG로 — 자막과 같은 오버레이 경로."""
    from PIL import Image, ImageDraw
    cn = LAYOUT.get("caption_note_style", {})
    out, t_acc = [], 0.0
    notes = []
    for pp in pairs:
        sc = scenes[pp["index"]]
        note = (sc.get("caption_note") or "").strip()
        t0, t1 = t_acc + pp.get("lead", 0.0), t_acc + pp["dur"]
        t_acc = t1
        if note:
            notes.append((note, t0, t1))
    if not notes:
        return out
    os.makedirs(temp_dir, exist_ok=True)
    font, _ = _load_font(cn.get("font_size", 30))
    pad, x0 = 10, cn.get("x", 40)
    for i, (note, t0, t1) in enumerate(notes):
        dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        w = int(dummy.textlength(note, font=font))
        asc, desc = font.getmetrics()
        box_h = asc + desc + pad * 2
        img = Image.new("RGBA", (CANVAS_W, box_h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([(x0, 0), (x0 + w + pad * 2, box_h)], radius=6,
                            fill=(0, 0, 0, int(255 * cn.get("box_alpha", 0.45))))
        d.text((x0 + pad, pad), note, fill=(255, 255, 255, 235), font=font)
        pth = os.path.join(temp_dir, f"note_{i:02d}.png")
        img.save(pth)
        out.append({"text": note, "start": t0, "end": t1, "png_path": pth,
                    "box_h": box_h, "y_abs": cn.get("y", 130)})   # v1.5: 1218(화면 밖) 버그 수정
    print(f"  ✓ 고지 캡션 {len(out)}개 생성")
    return out


def apply_subtitle_overlay(pass1_path, chunks_timed, out_path, pop_in=True):
    if not chunks_timed:
        shutil.copy(pass1_path, out_path)
        return True
    cmd = ["ffmpeg", "-y", "-i", pass1_path]
    for ch in chunks_timed:
        if pop_in:
            cmd += ["-loop", "1", "-framerate", str(FPS), "-i", ch["png_path"]]
        else:
            cmd += ["-i", ch["png_path"]]
    fc_parts, in_label = [], "0:v"
    for i, ch in enumerate(chunks_timed):
        out_label = f"vo{i}"
        y_pos = ch.get("y_abs", SUB_ANCHOR_B - ch["box_h"])   # v1.5: 캡션 고지는 고정 y
        src = f"{i+1}:v"
        if pop_in:
            prep = f"fi{i}"
            fo = ch.get("fade_out")
            fo_s = (f",fade=t=out:st={max(ch['end'] - fo, ch['start']):.3f}:d={fo:.3f}:alpha=1"
                    if fo else "")
            fc_parts.append(
                f"[{src}]format=rgba,setpts=PTS-STARTPTS+{ch['start']:.3f}/TB,"
                f"fade=t=in:st={ch['start']:.3f}:d={ch.get('fade_in', SUB_FADE_IN)}:alpha=1{fo_s}[{prep}]")
            src = prep
        shortest = ":shortest=1" if pop_in else ""
        fc_parts.append(
            f"[{in_label}][{src}]overlay=0:{y_pos}:"
            f"enable='between(t,{ch['start']:.3f},{ch['end']:.3f})'{shortest}[{out_label}]")
        in_label = out_label
    cmd += ["-filter_complex", ";".join(fc_parts),
            "-map", f"[{in_label}]", "-map", "0:a",
            "-c:v", "libx264", "-preset", "slow", "-crf", "18",
            "-pix_fmt", "yuv420p", "-c:a", "copy", out_path]
    print(f"  [2패스] 자막 overlay {len(chunks_timed)}개 합성 중...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ⚠️ overlay 실패:\n{r.stderr[-500:]}")
        return False
    return True


# ══ 유틸 ══════════════════════════════════════════════════════════════════════

def get_audio_duration(path):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                        "-of", "json", path], capture_output=True, text=True)
    try:
        return float(json.loads(r.stdout)["format"]["duration"])
    except Exception:
        return 0.0


def run_ffmpeg(cmd, label):
    print(f"  [{label}] ffmpeg 실행...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ⚠️ {label} 실패:\n{r.stderr[-600:]}")
        sys.exit(EXIT_VALIDATION)
    return r


# ══ L1: 세그먼트 필터 (v1.10: 전체보존(fit) 단일 경로 — cover 풀블리드 폐지) ═════

def _src_ar(path, kind):
    """소스 종횡비(iw/ih). 실패 시 None → fit 판정 스킵(=cover 유지)."""
    if kind == "video":
        r = subprocess.run(["ffprobe", "-v", "quiet", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height",
                            "-of", "csv=p=0:s=x", str(path)],
                           capture_output=True, text=True)
        try:
            w, h = r.stdout.strip().split("x")[:2]
            w, h = float(w), float(h)
            return w / h if h else None
        except Exception:
            return None
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.width / im.height if im.height else None
    except Exception:
        return None


_WHOLE_FIT = (1.0, 1.0, 0.5, 0.5)          # v1.10: bbox 없음/이미꽉참/안잘림 — 전체 프레임을 그대로 fit


def fit_decision(bbox, src_ar):
    """cover 크롭이 피사체 bbox를 자르는가? 자르면 (bbw,bbh,bbcx,bbcy)로 피사체 앵커 축소.
    v1.10: 풀블리드(화면 꽉 채움) 완전 폐지 — 아래 세 경우 모두 전체 프레임을 그대로
    마진 안에 축소하는 _WHOLE_FIT을 반환해 항상 블러 여백이 생기도록 강제한다(Walter 명시 요청).
      ① bbox/src_ar 없음(감지 실패) ② 이미 꽉 찬 샷(FULLFRAME) ③ cover에 안 잘리는 샷(FIT_TOL)
    → 이제 fit_decision은 절대 None을 반환하지 않는다(항상 여백 O).
    footage_review v1.7과 동일 로직 — 눈검수 미리보기와 실제 빌드가 일치하도록 공유."""
    if not bbox or not src_ar or src_ar <= 0:
        return _WHOLE_FIT                   # ① 감지 실패 — 그래도 여백 강제
    x0, y0, x1, y1 = bbox
    rw, rh = x1 - x0, y1 - y0
    if rw >= FULLFRAME_W and rh >= FULLFRAME_H:
        return _WHOLE_FIT                   # ② 이미 꽉 찬 샷도 강제 축소(v1.8의 풀블리드 예외 폐지)
    bbw = max(0.06, rw)             # 0.06 하한: 극단 축소(과도 업스케일) 방지
    bbh = max(0.06, rh)
    bbcx, bbcy = (x0 + x1) / 2, (y0 + y1) / 2
    vis_w = min(1.0, CANVAS_AR / src_ar)
    vis_h = min(1.0, src_ar / CANVAS_AR)
    if rw <= vis_w * FIT_TOL and rh <= vis_h * FIT_TOL:
        return _WHOLE_FIT                   # ③ 안 잘리는 샷도 강제 축소(풀블리드 폐지)
    return (bbw, bbh, bbcx, bbcy)


def _fit_chain(in_label, label_out, kind, dur, start, fit, scene_order, src_ar):
    """전체보존(fit): 블러·어둡게 배경 위에 피사체 전체를 축소 배치(중앙 정렬).
    fit=(bbw,bbh,bbcx,bbcy).
    v1.10 (Walter 피드백 "테두리 고정하고 안에서만 움직여야 안 조잡하다"):
    전경 컨테이너 크기(fg_w,fg_h)를 픽셀 정수로 미리 계산해 오버레이 테두리를 완전히
    고정한다(v1.9는 오버레이 자체 크기가 매 프레임 변해 배경과 함께 흔들려 보였음).
    움직임은 컨테이너보다 1/FIT_FG_START배 크게 미리 스케일한 버퍼를 zoompan으로
    크롭해 만든다 — z가 1.0→1/FIT_FG_START로 커지는 동안 컨테이너 크기(출력 s=)는
    절대 안 변하고, 크롭 중심은 피사체(bbcx,bbcy)에 고정하며, z의 상한이 정확히
    기존 안전 상한(v1.8 fgw_max)과 같아 피사체가 그 이상은 절대 커지지 않는다(재재단 없음)."""
    bbw, bbh, bbcx, bbcy = fit
    tw, th = FIT_MARGIN * CANVAS_W, FIT_MARGIN * CANVAS_H
    # 컨테이너 크기 = 안전 상한(S*iw, S*ih) — src_ar(=iw/ih, Python 값)로 픽셀 정수 계산
    fg_w = min(tw / bbw, (th / bbh) * src_ar)
    fg_h = fg_w / src_ar
    fg_w = max(2, int(round(fg_w / 2)) * 2)              # yuv420p 짝수 정렬
    fg_h = max(2, int(round(fg_h / 2)) * 2)
    ox, oy = (CANVAS_W - fg_w) // 2, (CANVAS_H - fg_h) // 2   # 테두리 고정 — 캔버스 중앙 정적 배치
    pre_w = max(fg_w + 2, int(round((fg_w / FIT_FG_START) / 2)) * 2)   # 크롭 여유 버퍼(짝수)
    pre_h = max(fg_h + 2, int(round((fg_h / FIT_FG_START) / 2)) * 2)
    frames = max(int(round(dur * FPS)), 1)
    zoom_max = pre_w / fg_w                               # 버퍼 대비 상한 줌(=1/FIT_FG_START 근사, 반올림 보정)
    if scene_order % 2 == 0:
        fg_z = f"{zoom_max:.4f}-{zoom_max - 1:.4f}*on/{frames}"           # 줌아웃: 꽉참→여유
        bg_z = f"{FIT_BG_ZOOM:.3f}-{FIT_BG_ZOOM - 1:.3f}*on/{frames}"     # 배경 반대위상
    else:
        fg_z = f"1.0+{zoom_max - 1:.4f}*on/{frames}"                      # 줌인: 여유→꽉참
        bg_z = f"1.0+{FIT_BG_ZOOM - 1:.3f}*on/{frames}"
    # 크롭 중심을 피사체(bbcx,bbcy, pre_w/pre_h 기준 픽셀)에 고정 — 프레임 중심이 아니라 피사체 중심으로 줌
    cx, cy = bbcx * pre_w, bbcy * pre_h
    fg_x = f"clip({cx:.1f}-(iw/zoom)/2,0,iw-iw/zoom)"
    fg_y = f"clip({cy:.1f}-(ih/zoom)/2,0,ih-ih/zoom)"
    u = re.sub(r"[^0-9a-zA-Z]", "", label_out)          # 유니크 중간 라벨 접두
    if kind == "video":
        # v1.2 (millong_001 실전 발견): 소스가 start+dur보다 짧으면 trim이 소스 끝에서
        # 멈춰 세그먼트가 짧아진다. 그만큼 뒤쪽 씬이 전부 앞으로 밀리고(화면만 먼저 감),
        # 마지막에는 -shortest가 오디오 꼬리를 잘라 CTA 문장이 통째로 사라진다.
        # (실측: 3개 클립이 3.74초 부족 → 완성본에서 CTA 마지막 문장 소실)
        # tpad로 마지막 프레임을 홀드한 뒤 정확히 dur로 다시 잘라 길이를 보장한다.
        head = (f"[{in_label}]trim=start={start:.3f}:duration={dur:.3f},"
                f"setpts=PTS-STARTPTS,fps={FPS},"
                f"tpad=stop_mode=clone:stop_duration={dur:.3f},"
                f"trim=duration={dur:.3f},setpts=PTS-STARTPTS,"
                f"split=2[{u}bg][{u}fg];")
        tail = ""
    else:
        head = f"[{in_label}]fps={FPS},split=2[{u}bg][{u}fg];"
        tail = f",trim=duration={dur:.3f},setpts=PTS-STARTPTS"
    return (f"{head}"
            f"[{u}bg]scale={CANVAS_W}:{CANVAS_H}:force_original_aspect_ratio=increase,"
            f"crop={CANVAS_W}:{CANVAS_H},gblur=sigma={FIT_BLUR},"
            f"eq=brightness=-{FIT_DARK},"
            f"zoompan=z='{bg_z}':d=1:x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2'"
            f":s={CANVAS_W}x{CANVAS_H}:fps={FPS},setsar=1[{u}bgc];"
            f"[{u}fg]scale=w={pre_w}:h={pre_h},"
            f"zoompan=z='{fg_z}':d=1:x='{fg_x}':y='{fg_y}'"
            f":s={fg_w}x{fg_h}:fps={FPS},setsar=1[{u}fgc];"
            f"[{u}bgc][{u}fgc]overlay=x={ox}:y={oy}{tail}[{label_out}]")


GRAPHIC_ZOOM = 1.035   # 롱폼: 그래픽 카드 전용 미세 Ken Burns 폭(FIT_BG_ZOOM 1.06보다 절제 — 텍스트 위주라 과하면 어지럽다)


def _graphic_chain(in_label, label_out, dur, scene_order):
    """롱폼 전용: 인포그래픽 카드(graphic_card_capture로 이미 1920×1080 정확히 캔버스
    비율로 렌더된 풀프레임 정지화면)는 fit 체인(블러 여백·피사체 앵커)이 필요 없다 —
    크롭할 대상도, 여백을 만들 이유도 없다. 화면이 죽어 보이지 않게 아주 약한
    Ken Burns만 적용(zoompan은 이미 캔버스 크기인 입력에도 동작 — bg 체인과 동일 기법)."""
    frames = max(int(round(dur * FPS)), 1)
    if scene_order % 2 == 0:
        z = f"1.0+{GRAPHIC_ZOOM - 1:.4f}*on/{frames}"
    else:
        z = f"{GRAPHIC_ZOOM:.4f}-{GRAPHIC_ZOOM - 1:.4f}*on/{frames}"
    return (f"[{in_label}]fps={FPS},scale={CANVAS_W}:{CANVAS_H},"
            f"zoompan=z='{z}':d=1:x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2'"
            f":s={CANVAS_W}x{CANVAS_H}:fps={FPS},setsar=1,"
            f"trim=duration={dur:.3f},setpts=PTS-STARTPTS[{label_out}]")


def get_media_duration(path):
    """v1.2: 영상/오디오 컨테이너 길이(초). 실패하면 None."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(path)], capture_output=True, text=True)
        return float(r.stdout.strip())
    except Exception:
        return None


def _graphic_video_chain(in_label, label_out, dur):
    """v1.5: HTML 애니메이션 렌더본(mp4). 이미 1920×1080 완성 화면이라 확대·블러 없이 그대로,
    길이가 모자라면 마지막 프레임(애니메이션 완료 상태)을 홀드한다."""
    return (f"[{in_label}]fps={FPS},scale={CANVAS_W}:{CANVAS_H},setsar=1,"
            f"tpad=stop_mode=clone:stop_duration={dur:.3f},"
            f"trim=duration={dur:.3f},setpts=PTS-STARTPTS[{label_out}]")


_FIT = LAYOUT.get("fit", {})
FULLBLEED     = bool(_FIT.get("fullbleed_landscape", False))
FULLBLEED_TOL = float(_FIT.get("fullbleed_ar_tol", 0.03))
FULLBLEED_ZOOM = float(_FIT.get("fullbleed_zoom", 1.04))


def is_fullbleed(kind, src_ar):
    """v1.5: 캔버스와 같은 비율(16:9 ±tol)의 실사는 축소·블러 없이 꽉 채운다."""
    return (FULLBLEED and kind in ("video", "photo") and src_ar
            and abs(src_ar - CANVAS_AR) / CANVAS_AR <= FULLBLEED_TOL)


def _fullbleed_chain(in_label, label_out, kind, dur, start, scene_order):
    frames = max(int(round(dur * FPS)), 1)
    zm = FULLBLEED_ZOOM
    z = (f"{zm:.4f}-{zm - 1:.4f}*on/{frames}" if scene_order % 2 == 0
         else f"1.0+{zm - 1:.4f}*on/{frames}")
    if kind == "video":
        head = (f"[{in_label}]trim=start={start:.3f}:duration={dur:.3f},"
                f"setpts=PTS-STARTPTS,fps={FPS},"
                f"tpad=stop_mode=clone:stop_duration={dur:.3f},"
                f"trim=duration={dur:.3f},setpts=PTS-STARTPTS,")
        tail = ""
    else:
        head = f"[{in_label}]fps={FPS},"
        tail = f",trim=duration={dur:.3f},setpts=PTS-STARTPTS"
    return (f"{head}scale={CANVAS_W}:{CANVAS_H}:force_original_aspect_ratio=increase,"
            f"crop={CANVAS_W}:{CANVAS_H},"
            f"zoompan=z='{z}':d=1:x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2'"
            f":s={CANVAS_W}x{CANVAS_H}:fps={FPS},setsar=1{tail}[{label_out}]")


def is_graphic_video(it):
    return it.get("type") == "graphic" and str(it.get("path", "")).lower().endswith((".mp4", ".mov", ".webm"))


def segment_filter(label_out, in_label, kind, dur, scene_order, start=0.0, bbox=None, src_ar=None):
    """세그먼트 하나(클립 1개)를 1920×1080로 만드는 필터.
    v1.10: fit_decision이 항상 fit 튜플을 반환(풀블리드 폐지) — 모든 세그먼트가
    _fit_chain(블러 여백, 고정 테두리+내부 줌) 경로만 사용. focus/track 기반 직접
    cover 크롭·줌펀치·일반 Ken Burns 경로는 완전히 도달 불가해져 삭제
    (과거 로직은 _versions/military_build_v1.9.py에 보존).
    롱폼 v1.0: kind=="graphic"만 예외 — _graphic_chain(단순 스케일+미세 줌)으로 분기."""
    if kind == "graphic":
        return _graphic_chain(in_label, label_out, dur, scene_order)
    if is_fullbleed(kind, src_ar):                       # v1.5: 16:9 실사는 꽉 채움
        return _fullbleed_chain(in_label, label_out, kind, dur, start, scene_order)
    fit = fit_decision(bbox, src_ar)
    return _fit_chain(in_label, label_out, kind, dur, start, fit, scene_order, src_ar or (16 / 9))


# ══ 오디오 (v1.1: BGM + loudnorm 2패스) ═══════════════════════════════════════

def build_audio(pairs, tmp: Path) -> Path:
    # 1) 나레이션 concat (+씬 갭)
    nar = tmp / "nar.wav"
    cmd = ["ffmpeg", "-y"]
    for p in pairs:
        cmd += ["-i", p["mp3"]]
    # v1.5: 소제목 씬은 앞에 lead초 무음(adelay) — 화면·BGM·소제목만 흐르는 '숨' 구간
    fc = "".join(
        f"[{i}:a]aresample=44100,"
        + (f"adelay=delays={int(round(p.get('lead', 0.0) * 1000))}:all=1," if p.get("lead") else "")
        + f"apad=pad_dur={SCENE_GAP}[a{i}];"
        for i, p in enumerate(pairs))
    fc += "".join(f"[a{i}]" for i in range(len(pairs)))
    fc += f"concat=n={len(pairs)}:v=0:a=1[out]"
    cmd += ["-filter_complex", fc, "-map", "[out]", "-c:a", "pcm_s16le", str(nar)]
    run_ffmpeg(cmd, "오디오-나레이션")

    # 2) BGM 믹스 (assets/bgm/*.mp3 첫 트랙, -28 LUFS 베드)
    bgm_files = sorted(Path(BASE_DIR, "assets", "bgm").glob("*.mp3"))
    mix = tmp / "mix.wav"
    if bgm_files:
        total = get_audio_duration(str(nar))
        cmd = ["ffmpeg", "-y", "-i", str(nar), "-stream_loop", "-1", "-i", str(bgm_files[0]),
               "-filter_complex",
               f"[1:a]aresample=44100,loudnorm=I={BGM_I}:TP=-2:LRA=7,atrim=0:{total:.3f}[b];"
               f"[0:a][b]amix=inputs=2:duration=first:normalize=0[out]",
               "-map", "[out]", "-c:a", "pcm_s16le", str(mix)]
        run_ffmpeg(cmd, f"오디오-BGM({bgm_files[0].name})")
    else:
        print("  ⚠️ assets/bgm 비어있음 — BGM 없이 진행 (suno 트랙 추가 시 자동 사용)")
        mix = nar

    # 3) loudnorm 2패스 — 측정 후 linear 적용 (v1.0 단일패스 언더슛 교정)
    r = run_ffmpeg(["ffmpeg", "-i", str(mix), "-af",
                    f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json",
                    "-f", "null", "-"], "오디오-측정")
    m = json.loads(re.search(r"\{[^{}]+\}", r.stderr[-1200:], re.S).group(0))
    audio = tmp / "audio.m4a"
    ln = (f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:"
          f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
          f"offset={m['target_offset']}:linear=true")
    run_ffmpeg(["ffmpeg", "-y", "-i", str(mix), "-af", ln,
                "-c:a", "aac", "-b:a", "192k", str(audio)], "오디오-정규화(2패스)")
    return audio


# ══ 메인 빌드 ═════════════════════════════════════════════════════════════════

CHAPTER_CARD_DUR = 3.5   # 롱폼: 챕터 전환 카드 노출 시간(초) — 숏폼의 상시 headline과 달리 트랜지언트


def build(run_id, out_dir):
    work = Path(BASE_DIR) / "_work" / run_id
    scenes_json = work / "scenes.json"
    manifest_json = work / "manifest.json"
    tts_dir = work / "tts"
    chapters_idx = work / "chapters" / "index.json"
    scrim_png = Path(BASE_DIR) / "assets" / "scrim.png"

    for p, name in [(scenes_json, "scenes.json"), (manifest_json, "manifest.json"),
                    (tts_dir, "tts/"), (scrim_png, "scrim.png")]:
        if not p.exists():
            print(f"⛔ 입력 없음: {name} ({p})")
            sys.exit(EXIT_VALIDATION)
    # v1.5: chapter_mode=lower_third면 chapters/index.json을 쓰지 않는다(빌드가 직접 그림).
    # chapters/index.json은 선택(챕터 없는 대본 허용) — chapter_capture_v1.0.mjs가
    # 챕터 0개일 때도 빈 배열로 정상 생성하므로, 파일 자체가 없으면 롱폼 STEP 2 순서 누락으로 간주.
    chapters = json.loads(chapters_idx.read_text(encoding="utf-8")) if chapters_idx.exists() else []

    scenes_doc = json.loads(scenes_json.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    if scenes_doc.get("run_id") != run_id or manifest.get("run_id") != run_id:
        print(f"⛔ run_id 불일치 — 격리 위반")
        sys.exit(EXIT_ISOLATION)

    scenes = scenes_doc["scenes"]
    by_scene = {}
    for it in manifest["items"]:
        if it.get("path"):
            by_scene.setdefault(it["scene_id"], []).append(it)

    pairs = []
    for i, sc in enumerate(scenes):
        mp3 = tts_dir / f"scene_{i:03d}.mp3"
        if not mp3.exists():
            print(f"⛔ TTS 없음: {mp3.name}")
            sys.exit(EXIT_VALIDATION)
        lead = scene_lead(sc)                      # v1.5: 소제목 무나레이션 구간
        pairs.append({"index": i, "scene_id": sc["id"], "lead": lead,
                      "dur": get_audio_duration(str(mp3)) + SCENE_GAP + lead, "mp3": str(mp3)})

    total = sum(p["dur"] for p in pairs)
    print(f"[military_build 롱폼 v1.5 · chapter_mode={CHAPTER_MODE}] 씬 {len(pairs)}개 · 챕터 {len(chapters)}개 · 총 {total:.1f}초 · run={run_id}")

    tmp = Path(tempfile.mkdtemp(prefix=f"milbuild_{run_id}_"))
    audio_path = build_audio(pairs, tmp)

    # 씬별 절대 시작시각·길이(챕터 카드 오버레이 시간창 계산용)
    scene_start_t, scene_dur_t = {}, {}
    t_acc = 0.0
    for p in pairs:
        scene_start_t[p["scene_id"]] = t_acc
        scene_dur_t[p["scene_id"]] = p["dur"]
        t_acc += p["dur"]

    # ── 1패스: 세그먼트(전체보존 fit + 배경 패럴랙스) → concat → 스크림 → 제목 ──
    cmd = ["ffmpeg", "-y"]
    seg_filters, seg_labels, n_in = [], [], 0
    for p in pairs:
        items = (by_scene.get(p["scene_id"]) or [])[:MAX_CLIPS_PER_SCENE]   # v1.3: 상한 2 → 5
        if not items:
            print(f"⛔ 씬 {p['scene_id']} 풋티지 없음 (manifest)")
            sys.exit(EXIT_VALIDATION)
        sub_dur = p["dur"] / len(items)
        for k, it in enumerate(items):
            bbox = it.get("bbox")                  # v1.8: 피사체 전체보존 판정용 (review v1.8)
            # v1.10: fit이 항상 적용되므로 bbox 유무와 무관하게 src_ar 필요 (실패 시 16:9 폴백)
            src_ar = _src_ar(it["path"], it["type"]) or (16 / 9)
            if it["type"] == "video" or is_graphic_video(it):   # v1.5: 그래픽 mp4도 영상 입력
                cmd += ["-i", it["path"]]
            else:
                cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{sub_dur:.3f}", "-i", it["path"]]
            label = f"seg{p['index']}_{k}"
            if it["type"] == "graphic":
                print(f"  📊 그래픽 카드(fit 생략): {it.get('key', label)}")
            elif is_fullbleed(it["type"], src_ar):
                print(f"  🖼  풀블리드(16:9): {it.get('key', label)} ar={src_ar:.2f}")
            else:
                fit_kind = "피사체앵커" if fit_decision(bbox, src_ar) != _WHOLE_FIT else "전체프레임"
                print(f"  🔲 전체보존(fit·{fit_kind}): {it.get('key', label)} ar={src_ar:.2f}")
            # v1.2: 클립 가용 길이 사전 점검 — 부족분은 tpad가 정지 프레임으로 메우므로
            # 타임라인은 안 밀리지만, 그 씬은 끝에서 화면이 멈춘다(=소재 교체 신호).
            if it["type"] == "video":
                _sl = get_media_duration(it["path"])
                _avail = (_sl - float(it.get("start_s") or 0)) if _sl else None
                if _avail is not None and _avail < sub_dur - 0.05:
                    print(f"     ⚠️ 클립 부족 {sub_dur - _avail:.2f}초 "
                          f"(필요 {sub_dur:.2f}s / 가용 {_avail:.2f}s) — 끝 구간 정지 프레임 홀드")
            if is_graphic_video(it):
                seg_filters.append(_graphic_video_chain(f"{n_in}:v", label, sub_dur))
            else:
                seg_filters.append(segment_filter(label, f"{n_in}:v", it["type"],
                                                  sub_dur, p["index"],
                                                  start=float(it.get("start_s") or 0),
                                                  bbox=bbox, src_ar=src_ar))
            seg_labels.append(label)
            n_in += 1

    scrim_idx = n_in
    cmd += ["-i", str(scrim_png)]
    # 롱폼: 챕터 카드는 영상당 1장(숏폼 headline)이 아니라 씬마다 여러 장 — 각각을
    # 별도 입력으로 붙이고 enable='between(t,t0,t0+CHAPTER_CARD_DUR)'로 시간창을 준다.
    chapter_inputs = []   # [(ffmpeg_input_idx, start_t, end_t), ...]
    for ch in (chapters if CHAPTER_MODE == "card" else []):   # v1.5: lower_third 모드는 2패스에서 그린다
        t0 = scene_start_t.get(ch["scene_id"])
        if t0 is None or not Path(ch["png"]).exists():
            continue
        # 카드가 다음 씬으로 새지 않게 노출시간을 그 씬 자체 길이로 클램프
        sdur = scene_dur_t.get(ch["scene_id"], CHAPTER_CARD_DUR)
        t1 = t0 + min(CHAPTER_CARD_DUR, sdur)
        chapter_inputs.append((n_in + 1 + len(chapter_inputs), t0, t1))
        cmd += ["-i", ch["png"]]
    au_idx = n_in + 1 + len(chapter_inputs)
    cmd += ["-i", str(audio_path)]

    fc = ";".join(seg_filters) + ";"
    fc += "".join(f"[{l}]" for l in seg_labels)
    fc += f"concat=n={len(seg_labels)}:v=1:a=0[base];"
    fc += f"[base][{scrim_idx}:v]overlay=0:0[l2];"
    prev = "l2"
    for i, (idx, t0, t1) in enumerate(chapter_inputs):
        scaled = f"ch{i}s"
        outl = f"l3_{i}"
        fc += f"[{idx}:v]scale={CANVAS_W}:{CANVAS_H}[{scaled}];"
        fc += (f"[{prev}][{scaled}]overlay=0:0:"
               f"enable='between(t,{t0:.3f},{t1:.3f})'[{outl}];")
        prev = outl
    fc += f"[{prev}]null[vout]"   # 챕터 0개여도 [vout] 라벨을 일관되게 노출(relabel passthrough)

    pass1 = tmp / "pass1.mp4"
    cmd += ["-filter_complex", fc, "-map", "[vout]", "-map", f"{au_idx}:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "16",
            "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", str(pass1)]
    run_ffmpeg(cmd, f"1패스(세그먼트 {len(seg_labels)}개+스크림+제목)")

    # ── 2패스: 자막 + 자료화면/AI 캡션(v1.5 — drawtext 미지원 ffmpeg 대응, PNG 오버레이) ──
    chunks = compute_subtitle_timing(pairs, scenes, str(tts_dir))
    chunks_png = create_subtitle_pngs(chunks, str(tmp / "subs"))
    chunks_png += create_note_pngs(pairs, scenes, str(tmp / "notes"))
    chunks_png += create_overlay_pngs(pairs, scenes, str(tmp / "overlays"))   # v1.5 소제목·장소

    os.makedirs(out_dir, exist_ok=True)
    topic = re.sub(r"[^\w가-힣]+", "_", scenes_doc.get("topic", "무제"))[:20]
    out_path = os.path.join(out_dir, f"long_mil_{topic}_{datetime.now():%Y%m%d_%H%M%S}.mp4")
    if not apply_subtitle_overlay(str(pass1), chunks_png, out_path):
        sys.exit(EXIT_VALIDATION)

    export_segments(pairs, by_scene, scenes, run_id)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"✅ 완성: {out_path}  ({total:.1f}초)")
    return out_path


def export_segments(pairs, by_scene, scenes, run_id):
    """v1.3: 이번 영상에 실제로 쓰인 구간을 개별 클립으로 _library/_segments/에 보관.
    다음 영상 제작 시 보조 소스로 재사용 (인덱스: _segments/index.json)."""
    seg_dir = Path(BASE_DIR) / "_library" / "_segments"
    seg_dir.mkdir(parents=True, exist_ok=True)
    idx_path = seg_dir / "index.json"
    idx = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else []
    added = 0
    seen = {e.get("file") for e in idx}
    for p in pairs:
        items = (by_scene.get(p["scene_id"]) or [])[:MAX_CLIPS_PER_SCENE]   # v1.3: 상한 2 → 5
        sub_dur = p["dur"] / max(len(items), 1)
        for it in items:
            if it.get("type") != "video" or not it.get("path"):
                continue
            start = float(it.get("start_s") or 0)
            slug = re.sub(r"[^\w가-힣]+", "-",
                          (it.get("title") or Path(it["path"]).stem))[:40].strip("-")
            name = f"{slug}__{start:.1f}s_{sub_dur:.1f}s.mp4"
            # v1.4: 클립 파일은 만들지 않고 사용 기록만(숏폼 build v1.20과 동일)
            if name in seen:
                continue
            seen.add(name)
            if True:
                idx.append({"file": name, "source_id": it.get("source_id", ""),
                            "license": it.get("license", ""), "credit": it.get("credit", ""),
                            "start_s": start, "dur_s": round(sub_dur, 1), "run_id": run_id})
                added += 1
    idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✓ 사용 구간 기록: {added}개 → _library/_segments/index.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--out", default=os.path.join(BASE_DIR, "..", "..", "02_콘텐츠", "밀리터리"))
    a = ap.parse_args()
    build(a.run_id, os.path.abspath(a.out))


if __name__ == "__main__":
    main()
