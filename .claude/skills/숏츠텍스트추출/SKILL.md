---
name: 숏츠텍스트추출
description: 유튜브 숏츠·일반 영상 URL에서 텍스트를 추출한다. 자막이 있으면 자막을, 없으면 오디오를 받아 Whisper STT로 전사한다. 유튜브 링크를 주며 "내용 뽑아줘", "대본 추출", "받아쓰기", "이 영상 텍스트로" 요청 시 사용.
---

# 유튜브 텍스트 추출

작업 폴더: `01_자동화/유튜브_텍스트추출/`

## 실행

```bash
cd "/Users/kakao/Documents/2. 개인/Walter Project/01_자동화/유튜브_텍스트추출"
SCRIPT=$(ls extract_text_v*.py | sort -V | tail -1)   # 최고 버전 자동 선택
python3 "$SCRIPT" "<유튜브 URL>" [--lang ko] [--model small] [--out 저장폴더]
```

| 인자 | 설명 |
|---|---|
| `--lang` | 자막/전사 언어 (기본 ko) |
| `--model` | Whisper 모델 (tiny/base/small/medium/large). 기본 small |
| `--out` | 저장 폴더 지정 (기본 `output/`) |

## 동작

1. 자막이 있으면 **자막을 그대로** 가져온다 (빠르고 정확)
2. 자막이 없으면 오디오를 받아 **Whisper STT로 전사**한다

## 결과물

```
output/<video_id>/transcript.txt
```
제목 · 채널 · 출처 · URL 헤더 + 본문 순서로 저장된다.

## 의존성

```bash
pip3 install yt-dlp certifi openai-whisper
brew install ffmpeg
```

## 주의

⚠️ **Whisper STT는 자동 전사라 고유명사·숫자를 잘못 알아듣는다.** 추출한 텍스트를 콘텐츠 소스로 재활용하기 전에 사람이 검수한다. 특히 인명·부대명·무기명·금액·날짜는 원본 영상과 대조할 것.

자막으로 뽑은 경우에도 자동생성 자막이면 같은 위험이 있다 — 헤더에 어느 경로로 뽑았는지 남으므로 확인한다.
