---
name: suno
description: Suno AI 음원 생성용 프롬프트(Styles 태그 + 가사)를 대화형 질문 7~8단계로 만들어 파일로 저장한다. API 키 없이 Claude가 직접 가사를 쓴다. "수노", "AI 음원 만들어줘", "노래 가사 프롬프트" 요청 시 사용. 한 줄 명령으로 빠르게 만들려면 suno-quick 스킬을 쓴다.
---

# Suno 프롬프트 생성 (대화형)

저장 폴더: `02_콘텐츠/AI음원/`
상세 명세: `01_자동화/AI음원/Suno_CLI_설계도_v*.md` (최신 버전)

## 플로우

```
Q0. 설정 방식 선택  ← 장르 선택보다 먼저
 ├─ 1) 직접 설정 → Q1~Q7 전부 질문
 ├─ 2) 반랜덤    → Q1(장르)+Q2(테마)만 받고 나머지 자동 선택 후 표시
 └─ 3) 완전 랜덤 → Q2(테마)만 선택 입력, 장르 포함 전체 자동
Q8. 가사 버전 수 (1/2/3)  ← 보컬=연주곡이면 스킵
→ 생성 → 파일 저장
```

**질문은 한 번에 하나씩** 던지고 답을 받은 뒤 다음으로 넘어간다.

### Q1 — 장르

| # | 장르 | 장르키 | 특징 | 추천 BPM |
|---|---|---|---|---|
| 1 | Lo-Fi 힙합 | `lofi` | 공부·수면 BGM | 80 |
| 2 | 카페 BGM | `cafe_bgm` | 보사노바·재즈 | 95 |
| 3 | 시티팝 | `citypop` | 새벽·네온·80s | 110 |
| 4 | 어쿠스틱 | `acoustic` | 인스타 바이럴·포크 | 90 |
| 5 | 시네마틱 | `cinematic` | 스톡뮤직 오케스트라 | 70 |
| 6 | K-Pop | `kpop` | 쇼츠 바이럴·댄스팝 | 130 |
| 7 | 일렉트로닉 | `electronic` | 클럽·EDM | 138 |
| 8 | 한국 옛날 발라드 | `korean_ballad` | 80~90s·김광석 스타일 | 70 |

### Q2 — 테마/키워드 (자유 입력)

### Q3 — 무드 (복수 선택 가능)

| # | 한국어 | 영어 태그 | | # | 한국어 | 영어 태그 |
|---|---|---|---|---|---|---|
| 1 | 감성적 | emotional, wistful | | 6 | 설레임 | hopeful, uplifting |
| 2 | 몽환적 | dreamy, ethereal | | 7 | 그리움 | nostalgic, longing |
| 3 | 에너지틱 | energetic, driving | | 8 | 희망적 | triumphant, uplifting |
| 4 | 잔잔함 | peaceful, calm | | 9 | 긴장감 | tense, dramatic |
| 5 | 우울 | melancholic, somber | | 10 | 평화로운 | serene, tranquil |

> 복수 선택 시 영어 태그를 병합한 뒤 **중복 단어 제거** (6+8 → `uplifting` 1회만).

### Q4 — 가사 언어

```
단일: 1) 한국어  2) 일본어  3) 영어  4) 프랑스어
혼합: 5) 한국어+영어 [K-Pop식]  — Verse·Bridge·Intro·Outro=한국어 / Chorus·Pre-Chorus=영어
      6) 일본어+영어 [J-Pop식]  — 동일 규칙
      7) 사용자 지정 → Q7 완료 후 Q7.5에서 섹션별 지정
```

### Q5 — BPM (Enter = 장르 추천값)

### Q6 — 보컬 + 창법

보컬: `1) 여성` `2) 남성` `3) 연주곡`

> **연주곡(inst) 선택 시**: Q8 스킵 · Styles에 `instrumental` 강제 추가 · LYRICS 블록을 `[구조 가이드]`(섹션 흐름·악기 전개만)로 대체 · 창법 입력은 무시하거나 악기 디렉션으로 재해석.

**공통 창법**: 허스키=husky / 부드러운=soft, smooth / 파워풀=powerful, strong / 청량한=clear, crisp, refreshing tone / 중저음=deep baritone / 고음=high tenor, clear high notes

**한국 발라드 아티스트 참조**
| 키워드 | 영어 변환 |
|---|---|
| 김광석 | husky breathy tenor, raw emotional folk delivery, 80s Korean folk ballad style |
| 이문세 | warm smooth baritone, polished classic ballad, velvety tone |
| 임재범 | powerful high tenor, intense emotional delivery, rock ballad style |
| 박효신 | soft falsetto, emotional R&B ballad, gentle yet powerful |
| 조용필 | rich tenor, legendary Korean pop, expressive diverse delivery |

**장르별 창법**
| 장르 | 키워드 | 영어 변환 |
|---|---|---|
| K-Pop | 청순 / 걸크러쉬 | airy falsetto, breathy pop, idol-style clean vocal / powerful belt, charismatic delivery, sharp diction |
| 시티팝 | 재즈팝 / 시티감성 | sultry jazz pop, laid-back phrasing, smoky tone / mellow pop vocal, breezy delivery, 80s Japanese pop style |
| 일렉트로닉 | 일렉보컬 / 감성일렉 | vocoder, auto-tune, robotic pitch-shift / ethereal whisper, breathy synth-pop vocal |
| Lo-Fi·카페 | 나른한 | lazy lo-fi vocal, whispery delivery, bedroom pop |
| 어쿠스틱 | 포크 | raw folk vocal, fingerpicking accompaniment, intimate delivery |

### Q7 — 재생시간 → 가사 구조

| # | 시간 | 섹션 구조 | 섹션당 줄 수 |
|---|---|---|---|
| 1 | 30초 | Chorus · End | 2~3줄 |
| 2 | 1분 | Verse · Pre-Chorus · Chorus | 3~4줄 |
| 3 | 2분 (표준) | Verse 1 · Chorus · Verse 2 · Chorus · Bridge · Outro | 4~6줄 |
| 4 | 3분 | Intro · Verse 1 · Pre-Chorus · Chorus · Verse 2 · Pre-Chorus · Chorus · Bridge · Outro | 4~6줄 |
| 5 | 4분 | 3분 구조 + Bridge 후 Chorus · Verse 3 · Final Chorus · Outro | 4~6줄 |
| 6 | 8분 ⚠️Pro | 멀티파트 — Verse 1~3, Pre-Chorus ×3, Chorus ×4, Bridge, Final Chorus ×2, Outro | 4~5줄 |

### Q7.5 — 섹션별 언어 지정 (Q4=7일 때만)

Q7 완료 후 **실제 섹션 목록을 보여주고** 지정받는다.
```
형식: 섹션명=언어코드 (띄어쓰기 구분) · 언어코드: ko en ja fr
예시(2분): verse=ko chorus=en bridge=ko outro=ko
지정 안 된 섹션 → 첫 번째 입력 언어로 기본 적용
```

### Q8 — 가사 버전 수

1개=`single` / 2개(A·B)=`bundle` / 3개(A·B·C)=`bundle`
같은 테마·구조·무드이되 **단어·이미지·표현은 완전히 달라야 한다.**

## Styles 태그 생성 공식

```
[장르 기본태그] + [무드 태그] + [BPM 힌트] + [보컬/창법 태그] + [언어 힌트] + [길이 힌트]
쉼표 구분 · 소문자 · 상한 1,000자 · 품질 권장 150~250자 · 핵심 태그를 앞쪽에
```

**장르 기본 태그**
| 장르키 | 태그 |
|---|---|
| `lofi` | lo-fi hip hop, chill beats, dusty vinyl, mellow piano, relaxed |
| `cafe_bgm` | bossa nova, jazz cafe, warm acoustic guitar, laid-back, cozy |
| `citypop` | city pop, 80s Japanese aesthetic, mellow synth, smooth bass, neon nights |
| `acoustic` | acoustic folk, fingerpicking guitar, intimate, organic, singer-songwriter |
| `cinematic` | cinematic orchestral, epic strings, sweeping, film score, emotional |
| `kpop` | K-pop, dance pop, polished production, catchy hook, modern K-pop |
| `electronic` | electronic dance, synthesizer, four-on-the-floor, club, EDM |
| `korean_ballad` | 80s Korean ballad, acoustic guitar, orchestral strings, raw emotional, retro pop |

**BPM 힌트**: ~84 `slow tempo` / 85~115 `mid tempo` / 116~135 `upbeat tempo` / 136~ `fast tempo`

**언어 힌트** (발음 정확도에 직결 — 누락 시 영어식 발음 오인식): ko `Korean lyrics, sung in Korean` / ja `Japanese lyrics` / en 생략 가능 / fr `French lyrics` / ko+en `bilingual Korean-English vocals` / ja+en `bilingual Japanese-English vocals` / custom 주 언어 힌트 + `multilingual vocals`. **연주곡은 언어 힌트 생략.**

**길이 힌트**: 30초·1분 `short form` / 2~3분 `standard length` / 4분↑ `extended`

## 가사 작성 원칙

1. **오리지널만** — 기존 곡 표절 절대 금지
2. **장면 묘사** — 직접적 감정 대신 구체적 시각 이미지
   - ❌ `"널 사랑해 / 보고싶어"`
   - ✅ `"성수동 카페 창가에 / 식어가는 아인슈페너처럼"`
3. **감각 묘사** — 장소·사물·시간·소리·질감
4. **Suno 형식** — `[Verse 1]` `[Chorus]` 섹션 태그, 재생시간별 줄 수 준수
5. **혼합 언어** — 지정 섹션 **전체**를 해당 언어로
6. **다중 버전** — 구조·테마 동일, 단어·이미지·표현 완전 상이
7. **연주곡** — 가사 없이 섹션 구조 가이드만

## 파일 저장

```
02_콘텐츠/AI음원/NNN_single_YYYYMMDD_장르키_테마첫단어.txt
02_콘텐츠/AI음원/NNN_bundle_YYYYMMDD_장르키_테마첫단어.txt
```
`NNN` = 폴더 내 최대 번호 +1 (3자리 0패딩):
```bash
ls "/Users/kakao/Documents/2. 개인/Walter Project/02_콘텐츠/AI음원/" | grep -oE '^[0-9]{3}' | sort -n | tail -1
```

### 출력 형식

```
═══════════════════════════════════════════════
🎵 SUNO 프롬프트 생성 완료  [002_bundle · 3개 버전]
═══════════════════════════════════════════════
장르: 시티팝 | 테마: 새벽 네온 골목 | 무드: 감성적, 그리움
BPM: 105 | 보컬: 남성 (김광석) | 언어: 한국어 | 재생: 2분

📋 STYLES (공통)
──────────────────────────────
city pop, 80s Japanese aesthetic, ...

╔══════════════════ 버전 A ══════════════════╗

📝 LYRICS — 버전 A
──────────────────────────────
[가사 A]

╠══════════════════ 버전 B ══════════════════╣
...
╚═══════════════════════════════════════════╝

💡 알고리즘 최적화 팁
──────────────────────────────
→ 팁 1~3
```

> 연주곡: `LYRICS` 블록을 `[구조 가이드]`로 대체, single 고정.
