# Stable Match Lab v3.1 single-file UI fixed

Stable Match Lab v3.1은 매칭 이론을 게임처럼 익히는 Streamlit 기반 퍼즐 앱입니다.

이 버전은 다음 조건을 모두 반영한 안정화 버전입니다.

- `matching_engine.py` 없이 `app.py` 하나만으로 동작
- 카드 선택 → 카드 선택 → 연결하기 방식의 드래그 앤 드롭 느낌 UI
- Gale-Shapley 단계별 시뮬레이터
- 스테이지 / 레벨 시스템
- 상단 메뉴 잘림 문제 개선
- 사이드바에 항상 첫 화면 복귀 / 레벨 선택 기능 제공

## 주요 기능

### 1. 카드형 연결 UI

기존 드롭다운 방식 대신 다음 흐름으로 매칭합니다.

1. 남성 카드 선택
2. 여성 카드 선택
3. 연결하기

Streamlit 기본 기능만 사용하므로 진짜 마우스 drag-and-drop은 아니지만, 텍스트 입력보다 게임형 인터랙션에 가깝습니다.

### 2. Gale-Shapley 단계별 시뮬레이터

3단계에서는 남성 제안형 Gale-Shapley 알고리즘을 단계별로 확인할 수 있습니다.

- 처음
- 이전
- 다음
- 끝
- 자동 재생

각 단계에서 다음 정보를 보여줍니다.

- 누가 누구에게 제안했는지
- 누가 임시 보류되었는지
- 누가 거절되었는지
- 현재 보류 중인 매칭
- 대기 중인 남성

### 3. 스테이지 / 레벨 시스템

세 개의 스테이지가 있고, 각 스테이지는 10개 레벨로 구성됩니다.

- 1단계 — 안정 매칭
- 2단계 — 최적 안정 매칭
- 3단계 — Gale-Shapley 챌린지

성공하면 다음 레벨이 해금됩니다. 기록은 현재 브라우저 세션 기준으로 저장됩니다.

## 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

## GitHub 업로드

아래 파일만 올리면 됩니다.

```text
app.py
requirements.txt
README.md
.gitignore
.streamlit/config.toml
```

`matching_engine.py`는 필요하지 않습니다.

기존 저장소에 `matching_engine.py`가 남아 있어도 이 버전의 `app.py`는 그것을 import하지 않으므로 동작에는 영향이 없습니다.
