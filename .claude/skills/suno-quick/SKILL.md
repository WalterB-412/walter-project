---
name: suno-quick
description: Suno AI 음원 프롬프트를 질문 없이 한 줄 명령으로 생성한다. 장르·테마·옵션을 인수로 받아 Styles 태그와 가사를 만들어 파일로 저장한다. "/suno-quick citypop ..." 형태의 호출이나 옵션을 이미 정해둔 음원 요청 시 사용. 질문을 받아가며 만들려면 suno 스킬을 쓴다.
---

# Suno 프롬프트 생성 (한 줄 명령)

저장 폴더: `02_콘텐츠/AI음원/`
상세 명세: `01_자동화/AI음원/Suno_CLI_설계도_v*.md` (최신 버전)

**질문하지 않는다.** 인수를 파싱해 바로 생성한다. 누락된 값은 기본값을 쓴다.

```bash
/suno-quick [장르] "[테마]" [옵션]
```

## 옵션

| 옵션 | 값 | 기본값 | 설명 |
|---|---|---|---|
| `--mood` | 무드들, 쉼표 구분 | 감성적 | 복수 가능 |
| `--lang` | ko / ja / en / fr / ko+en / ja+en / custom | ko | 혼합·사용자지정 지원 |
| `--mix` | `"verse=ko chorus=en"` | — | `--lang custom` 시 사용 |
| `--bpm` | 숫자 | 장르 추천값 | |
| `--vocal` | female / male / inst | female | inst면 가사 생략·구조 가이드만 |
| `--style` | `"창법키워드"` | 없음 | 따옴표 사용 |
| `--dur` | 30s / 1m / 2m / 3m / 4m / 8m | 2m | |
| `--count` | 1 / 2 / 3 | 1 | 버전 수 (inst면 무시) |
| `--random` | 플래그 | — | 장르 포함 전체 자동 (테마만 선택 입력) |

> **폴백**: `--lang custom`인데 `--mix`가 없으면 **ko 단일로 처리하고 경고**를 띄운다 — `⚠️ --mix 누락, 한국어 단일로 진행`

## 장르키 · 추천 BPM

`lofi` 80 · `cafe_bgm` 95 · `citypop` 110 · `acoustic` 90 · `cinematic` 70 · `kpop` 130 · `electronic` 138 · `korean_ballad` 70

## 사용 예시

```bash
# 기본 — 시티팝 2분
/suno-quick citypop "새벽 네온 골목 혼자 걷는 밤" --mood 감성적,그리움 --vocal male --style "김광석" --dur 2m

# 혼합 언어 — K-Pop식 (벌스 한국어, 후렴 영어)
/suno-quick kpop "첫사랑 설레는 고백" --lang ko+en --vocal female --dur 2m

# 섹션별 언어 직접 지정
/suno-quick citypop "새벽 감성" --lang custom --mix "verse=ko chorus=en bridge=ko" --dur 3m

# 다중 버전 3개 bundle
/suno-quick acoustic "이별 후 식은 커피" --mood 우울,그리움 --lang ko --vocal female --dur 3m --count 3

# 반랜덤 — 장르+테마만 지정
/suno-quick lofi "공부하는 새벽" --random

# 완전 랜덤 — 테마도 생략 가능
/suno-quick --random

# 연주곡·시네마틱·영어
/suno-quick cinematic "epic battle" --mood 긴장감,희망적 --lang en --vocal inst --dur 3m
```

## Styles 태그 · 가사 규칙 · 출력 형식

**`suno` 스킬과 동일하다.** 장르 기본 태그, 무드 영어 태그(중복 제거), BPM·언어·길이 힌트, 창법 변환표, 재생시간별 섹션 구조, 가사 작성 원칙 7개, 파일명 규칙, 출력 템플릿 모두 그쪽을 따른다.

핵심만 다시 적으면:

```
[장르 기본태그] + [무드 태그] + [BPM 힌트] + [보컬/창법 태그] + [언어 힌트] + [길이 힌트]
쉼표 구분 · 소문자 · 품질 권장 150~250자
```

- BPM 힌트: ~84 `slow tempo` / 85~115 `mid tempo` / 116~135 `upbeat tempo` / 136~ `fast tempo`
- 길이 힌트: 30s·1m `short form` / 2~3m `standard length` / 4m↑ `extended`
- 언어 힌트 누락은 발음 오인식으로 직결된다. ko는 `Korean lyrics, sung in Korean`.
- `--vocal inst`: Styles에 `instrumental` 추가 · `--count` 무시하고 single · 가사 대신 `[구조 가이드]`

## 파일 저장

```
02_콘텐츠/AI음원/NNN_single_YYYYMMDD_장르키_테마첫단어.txt   ← --count 1
02_콘텐츠/AI음원/NNN_bundle_YYYYMMDD_장르키_테마첫단어.txt   ← --count 2~3
```
```bash
ls "/Users/kakao/Documents/2. 개인/Walter Project/02_콘텐츠/AI음원/" | grep -oE '^[0-9]{3}' | sort -n | tail -1
```
