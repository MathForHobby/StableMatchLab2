import html
import itertools
import random
import time
from typing import Dict, List, Tuple, Any

import streamlit as st


st.set_page_config(
    page_title="Stable Match Lab2",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# Stable Match Lab2 v3.1
# Single-file version
# matching_engine.py 없이 app.py 하나만으로 동작하도록 핵심 로직을 포함합니다.
# ============================================================

Matching = Dict[str, str]
Preferences = Dict[str, List[str]]


MALE_KOREAN_NAMES = [
    "민준", "서준", "도윤", "예준", "시우", "하준", "주원", "지호",
    "지후", "준우", "현우", "도현", "건우", "우진", "선우", "유준",
    "은우", "연우", "이준", "지안", "태오", "윤재", "서진", "재원"
]

FEMALE_KOREAN_NAMES = [
    "서연", "서윤", "지우", "하은", "민서", "지유", "윤서", "채원",
    "수아", "지아", "지민", "은서", "예은", "다은", "하윤", "소율",
    "예린", "유나", "나은", "서현", "아린", "유진", "다연", "채은"
]


def generate_people(n: int, seed: int | None = None) -> Tuple[List[str], List[str]]:
    rng = random.Random(seed)

    if n > len(MALE_KOREAN_NAMES) or n > len(FEMALE_KOREAN_NAMES):
        raise ValueError("n is larger than the prepared Korean name pool.")

    men = rng.sample(MALE_KOREAN_NAMES, n)
    women = rng.sample(FEMALE_KOREAN_NAMES, n)

    return men, women


def generate_preferences(
    n: int,
    seed: int | None = None,
    name_seed: int | None = None,
) -> Tuple[List[str], List[str], Preferences, Preferences]:
    rng = random.Random(seed)

    men, women = generate_people(n, seed=name_seed)

    men_prefs: Preferences = {}
    women_prefs: Preferences = {}

    for m in men:
        prefs = women[:]
        rng.shuffle(prefs)
        men_prefs[m] = prefs

    for w in women:
        prefs = men[:]
        rng.shuffle(prefs)
        women_prefs[w] = prefs

    return men, women, men_prefs, women_prefs


def make_rankings(prefs: Preferences) -> Dict[str, Dict[str, int]]:
    return {
        person: {candidate: rank for rank, candidate in enumerate(pref_list)}
        for person, pref_list in prefs.items()
    }


def is_complete_one_to_one(matching: Matching, men: List[str], women: List[str]) -> Tuple[bool, str]:
    if set(matching.keys()) != set(men):
        return False, "왼쪽 그룹의 모든 사람이 매칭되어야 합니다."

    selected = list(matching.values())
    if any(w not in women for w in selected):
        return False, "선택한 상대 중 올바르지 않은 항목이 있습니다."

    if len(selected) != len(women):
        return False, "아직 매칭되지 않은 사람이 있습니다."

    if len(set(selected)) != len(selected):
        return False, "오른쪽 그룹의 한 사람이 두 번 이상 매칭되었습니다."

    return True, "완전한 1:1 매칭입니다."


def invert_matching(matching: Matching) -> Dict[str, str]:
    return {w: m for m, w in matching.items()}


def find_blocking_pairs(
    matching: Matching,
    men_prefs: Preferences,
    women_prefs: Preferences,
) -> List[Dict[str, Any]]:
    men_rank = make_rankings(men_prefs)
    women_rank = make_rankings(women_prefs)
    woman_to_man = invert_matching(matching)

    blocking_pairs: List[Dict[str, Any]] = []

    for m, current_w in matching.items():
        for w in men_prefs[m]:
            if w == current_w:
                break

            current_m = woman_to_man[w]

            man_prefers_w = men_rank[m][w] < men_rank[m][current_w]
            woman_prefers_m = women_rank[w][m] < women_rank[w][current_m]

            if man_prefers_w and woman_prefers_m:
                blocking_pairs.append(
                    {
                        "man": m,
                        "woman": w,
                        "man_current": current_w,
                        "woman_current": current_m,
                        "man_current_rank": men_rank[m][current_w] + 1,
                        "man_new_rank": men_rank[m][w] + 1,
                        "woman_current_rank": women_rank[w][current_m] + 1,
                        "woman_new_rank": women_rank[w][m] + 1,
                    }
                )

    return blocking_pairs


def is_stable(matching: Matching, men_prefs: Preferences, women_prefs: Preferences) -> bool:
    return len(find_blocking_pairs(matching, men_prefs, women_prefs)) == 0


def satisfaction_score(matching: Matching, men_prefs: Preferences, women_prefs: Preferences) -> int:
    n = len(matching)
    men_rank = make_rankings(men_prefs)
    women_rank = make_rankings(women_prefs)
    woman_to_man = invert_matching(matching)

    score = 0

    for m, w in matching.items():
        score += n - men_rank[m][w]

    for w, m in woman_to_man.items():
        score += n - women_rank[w][m]

    return score


def all_matchings(men: List[str], women: List[str]) -> List[Matching]:
    return [dict(zip(men, perm)) for perm in itertools.permutations(women)]


def stable_matchings(men: List[str], women: List[str], men_prefs: Preferences, women_prefs: Preferences) -> List[Matching]:
    return [
        matching
        for matching in all_matchings(men, women)
        if is_stable(matching, men_prefs, women_prefs)
    ]


def find_best_stable_matching(
    men: List[str],
    women: List[str],
    men_prefs: Preferences,
    women_prefs: Preferences,
) -> Tuple[Matching | None, int | None, List[Matching]]:
    candidates = stable_matchings(men, women, men_prefs, women_prefs)

    if not candidates:
        return None, None, []

    scored = [(satisfaction_score(m, men_prefs, women_prefs), m) for m in candidates]
    best_score = max(score for score, _ in scored)
    best = [m for score, m in scored if score == best_score]

    return best[0], best_score, best


def gale_shapley_trace(
    men: List[str],
    women: List[str],
    men_prefs: Preferences,
    women_prefs: Preferences,
) -> Tuple[Matching, List[Dict[str, Any]]]:
    """Return final men-proposing Gale-Shapley matching and full step trace."""
    women_rank = make_rankings(women_prefs)

    free_men = men[:]
    next_choice_index = {m: 0 for m in men}
    held_by_woman: Dict[str, str] = {}
    steps: List[Dict[str, Any]] = []

    def snapshot(
        action: str,
        proposer: str | None = None,
        target: str | None = None,
        accepted: str | None = None,
        rejected: str | None = None,
        event: str = "info",
    ):
        steps.append(
            {
                "step": len(steps),
                "action": action,
                "proposer": proposer,
                "target": target,
                "accepted": accepted,
                "rejected": rejected,
                "event": event,
                "held_by_woman": dict(held_by_woman),
                "free_men": free_men[:],
                "next_choice_index": dict(next_choice_index),
            }
        )

    snapshot("알고리즘을 시작합니다. 모든 남성이 아직 매칭되지 않은 상태입니다.", event="start")

    while free_men:
        m = free_men.pop(0)

        if next_choice_index[m] >= len(women):
            snapshot(
                f"{m}은/는 모든 사람에게 제안했지만 매칭되지 않았습니다.",
                proposer=m,
                event="exhausted",
            )
            continue

        w = men_prefs[m][next_choice_index[m]]
        next_choice_index[m] += 1

        if w not in held_by_woman:
            held_by_woman[w] = m
            snapshot(
                f"{m}이/가 {w}에게 제안합니다. {w}은/는 보류 중인 상대가 없으므로 {m}을/를 임시로 받아들입니다.",
                proposer=m,
                target=w,
                accepted=m,
                event="accept",
            )
        else:
            current_m = held_by_woman[w]

            if women_rank[w][m] < women_rank[w][current_m]:
                held_by_woman[w] = m
                free_men.append(current_m)
                snapshot(
                    f"{m}이/가 {w}에게 제안합니다. {w}은/는 기존의 {current_m}보다 {m}을/를 더 선호하므로 {m}을/를 보류하고 {current_m}을/를 거절합니다.",
                    proposer=m,
                    target=w,
                    accepted=m,
                    rejected=current_m,
                    event="switch",
                )
            else:
                free_men.append(m)
                snapshot(
                    f"{m}이/가 {w}에게 제안합니다. {w}은/는 현재 보류 중인 {current_m}을/를 더 선호하므로 {m}을/를 거절합니다.",
                    proposer=m,
                    target=w,
                    accepted=current_m,
                    rejected=m,
                    event="reject",
                )

    final_matching = {m: w for w, m in held_by_woman.items()}
    snapshot(
        "알고리즘이 종료되었습니다. 모든 남성이 매칭되었습니다.",
        event="done",
    )

    return final_matching, steps


def gale_shapley_men_propose(
    men: List[str],
    women: List[str],
    men_prefs: Preferences,
    women_prefs: Preferences,
) -> Tuple[Matching, List[str]]:
    final_matching, steps = gale_shapley_trace(men, women, men_prefs, women_prefs)
    return final_matching, [step["action"] for step in steps]


def explain_matching(matching: Matching) -> str:
    return ", ".join([f"{m}↔{w}" for m, w in sorted(matching.items())])



CSS = """
<style>
:root {
    --bg: #f6f7fb;
    --card: #ffffff;
    --ink: #172033;
    --muted: #64748b;
    --line: #e5e7eb;
    --blue: #2563eb;
    --blue-soft: #eff6ff;
    --green: #16a34a;
    --green-soft: #ecfdf5;
    --red: #dc2626;
    --red-soft: #fef2f2;
    --amber: #d97706;
    --amber-soft: #fffbeb;
    --purple: #7c3aed;
    --purple-soft: #f5f3ff;
}

.block-container {
    padding-top: 2.2rem;
    padding-bottom: 4rem;
    max-width: 1240px;
}

div[data-testid="stVerticalBlock"] {
    gap: 0.8rem;
}

.sml-hero {
    padding: 2.1rem 2.2rem;
    border-radius: 30px;
    background: radial-gradient(circle at top left, #dbeafe 0, transparent 30%),
                radial-gradient(circle at bottom right, #ede9fe 0, transparent 32%),
                linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    border: 1px solid #e5e7eb;
    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
    margin-bottom: 1.2rem;
}

.sml-title {
    font-size: 3.25rem;
    line-height: 1.05;
    font-weight: 900;
    letter-spacing: -0.065em;
    color: var(--ink);
    margin: 0 0 0.6rem 0;
}

.sml-subtitle {
    font-size: 1.07rem;
    color: var(--muted);
    max-width: 820px;
    margin: 0;
}

.stage-card, .level-card, .game-card {
    border-radius: 24px;
    background: var(--card);
    border: 1px solid var(--line);
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.055);
}

.stage-card {
    min-height: 285px;
    padding: 1.35rem;
}

.level-card {
    padding: 1rem;
    min-height: 158px;
}

.game-card {
    padding: 1rem;
}

.stage-card h3, .level-card h3 {
    margin: 0.45rem 0 0.45rem 0;
    letter-spacing: -0.03em;
    font-size: 1.28rem;
}

.stage-icon {
    width: 42px;
    height: 42px;
    border-radius: 16px;
    display: grid;
    place-items: center;
    font-size: 1.35rem;
    background: var(--blue-soft);
}

.stage-meta {
    display: inline-flex;
    gap: 0.35rem;
    flex-wrap: wrap;
    align-items: center;
    color: var(--muted);
    font-size: 0.88rem;
    margin: 0.35rem 0 0.7rem 0;
}

.pill {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 0.22rem 0.58rem;
    font-size: 0.78rem;
    font-weight: 800;
    margin: 0.16rem 0.18rem 0.16rem 0;
    border: 1px solid transparent;
    white-space: nowrap;
}

.pill-blue { background: var(--blue-soft); color: var(--blue); border-color: #bfdbfe; }
.pill-green { background: var(--green-soft); color: var(--green); border-color: #bbf7d0; }
.pill-red { background: var(--red-soft); color: var(--red); border-color: #fecaca; }
.pill-amber { background: var(--amber-soft); color: var(--amber); border-color: #fde68a; }
.pill-purple { background: var(--purple-soft); color: var(--purple); border-color: #ddd6fe; }
.pill-gray { background: #f8fafc; color: #475569; border-color: #e2e8f0; }

.section-title {
    font-size: 1.28rem;
    font-weight: 900;
    color: var(--ink);
    letter-spacing: -0.035em;
    margin: 0.35rem 0 0.55rem 0;
}

.person-card {
    border-radius: 22px;
    background: white;
    border: 1px solid var(--line);
    padding: 0.92rem;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.045);
    margin-bottom: 0.35rem;
}

.person-card.selected {
    border-color: #93c5fd;
    box-shadow: 0 14px 28px rgba(37, 99, 235, 0.14);
    background: linear-gradient(180deg, #ffffff 0%, #eff6ff 100%);
}

.person-card.danger {
    border-color: #fecaca;
    box-shadow: 0 12px 26px rgba(220, 38, 38, 0.09);
    background: linear-gradient(180deg, #fff 0%, #fff7f7 100%);
}

.person-card.gs-focus {
    border-color: #c4b5fd;
    box-shadow: 0 14px 28px rgba(124, 58, 237, 0.13);
    background: linear-gradient(180deg, #ffffff 0%, #f5f3ff 100%);
}

.person-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.48rem;
}

.person-name {
    font-size: 1.05rem;
    font-weight: 900;
    color: var(--ink);
}

.avatar {
    width: 34px;
    height: 34px;
    border-radius: 14px;
    display: grid;
    place-items: center;
    background: #f1f5f9;
}

.pref-list {
    display: grid;
    gap: 0.3rem;
}

.pref-row {
    display: flex;
    align-items: center;
    gap: 0.42rem;
    font-size: 0.88rem;
    color: #334155;
}

.rank-dot {
    width: 1.6rem;
    height: 1.6rem;
    border-radius: 999px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    display: grid;
    place-items: center;
    font-size: 0.76rem;
    font-weight: 850;
    color: #475569;
}

.drag-zone {
    border-radius: 28px;
    border: 1px dashed #cbd5e1;
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    padding: 1rem;
    min-height: 170px;
}

.connection-box {
    border-radius: 24px;
    border: 1px solid #dbeafe;
    background: #eff6ff;
    padding: 1rem;
    margin-bottom: 0.75rem;
    text-align: center;
}

.connection-names {
    font-size: 1.15rem;
    font-weight: 900;
    color: #1e3a8a;
}

.pair-chip {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.72rem 0.9rem;
    border-radius: 18px;
    border: 1px solid #dbeafe;
    background: #eff6ff;
    color: #1e3a8a;
    margin-bottom: 0.55rem;
    font-weight: 820;
}

.pair-chip.pending {
    border-color: #e5e7eb;
    background: #f8fafc;
    color: #64748b;
}

.feedback-card {
    border-radius: 24px;
    padding: 1.05rem;
    border: 1px solid var(--line);
    background: white;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
}

.feedback-card.success {
    border-color: #bbf7d0;
    background: linear-gradient(180deg, #ffffff 0%, #f0fdf4 100%);
}

.feedback-card.fail {
    border-color: #fecaca;
    background: linear-gradient(180deg, #ffffff 0%, #fef2f2 100%);
}

.feedback-card.info {
    border-color: #bfdbfe;
    background: linear-gradient(180deg, #ffffff 0%, #eff6ff 100%);
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.55rem;
}

.metric-box {
    border-radius: 18px;
    border: 1px solid #e2e8f0;
    background: #f8fafc;
    padding: 0.78rem;
}

.metric-label {
    color: #64748b;
    font-size: 0.76rem;
    font-weight: 850;
    text-transform: uppercase;
    letter-spacing: 0.035em;
}

.metric-value {
    color: #0f172a;
    font-size: 1.25rem;
    font-weight: 900;
}

.help-box {
    border: 1px dashed #cbd5e1;
    border-radius: 22px;
    padding: 1rem;
    background: #f8fafc;
    color: #334155;
}

.small-muted {
    color: var(--muted);
    font-size: 0.92rem;
}

.gs-log {
    border-radius: 20px;
    background: #0f172a;
    color: #e2e8f0;
    padding: 1rem;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.86rem;
    line-height: 1.65;
    max-height: 420px;
    overflow-y: auto;
}

.progress-bar {
    height: 10px;
    width: 100%;
    border-radius: 999px;
    background: #e2e8f0;
    overflow: hidden;
    margin-top: 0.45rem;
}

.progress-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #2563eb, #7c3aed);
}

.locked {
    opacity: 0.48;
    filter: grayscale(0.3);
}

.step-box {
    border-radius: 24px;
    border: 1px solid #ddd6fe;
    background: linear-gradient(180deg, #ffffff 0%, #f5f3ff 100%);
    padding: 1rem;
    margin-bottom: 0.75rem;
}

hr {
    margin: 1rem 0;
}
.control-panel {
    border-radius: 24px;
    border: 1px solid #e5e7eb;
    background: #ffffff;
    padding: 1rem;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.055);
    margin: 0.6rem 0 1rem 0;
}

.control-title {
    font-size: 0.9rem;
    font-weight: 850;
    color: #475569;
    margin-bottom: 0.35rem;
}

.sidebar-note {
    padding: 0.8rem;
    border-radius: 18px;
    border: 1px solid #dbeafe;
    background: #eff6ff;
    color: #1e3a8a;
    font-size: 0.9rem;
}

.nav-tip {
    border-radius: 20px;
    border: 1px solid #e5e7eb;
    background: #ffffff;
    padding: 0.9rem;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
    margin-bottom: 0.75rem;
}

</style>
"""


LEVELS = {
    1: [
        {"level": 1, "n": 3, "title": "첫 안정 매칭", "desc": "작은 규모에서 blocking pair를 찾아보세요."},
        {"level": 2, "n": 3, "title": "서로의 마음 읽기", "desc": "쌍방 선호가 동시에 움직이는지 확인하세요."},
        {"level": 3, "n": 3, "title": "불안정성 제거", "desc": "실패 이유를 보고 다시 고쳐보세요."},
        {"level": 4, "n": 4, "title": "네 쌍의 실험", "desc": "규모가 커지면 직관이 흔들립니다."},
        {"level": 5, "n": 4, "title": "숨은 blocking pair", "desc": "겉보기 좋은 매칭도 불안정할 수 있습니다."},
        {"level": 6, "n": 4, "title": "안정성 감각", "desc": "현재 상대와 더 선호하는 상대를 비교하세요."},
        {"level": 7, "n": 5, "title": "복잡한 선호표", "desc": "다섯 쌍의 선호를 동시에 추적합니다."},
        {"level": 8, "n": 5, "title": "연쇄적 불안정", "desc": "한 쌍을 고치면 다른 쌍이 흔들릴 수 있습니다."},
        {"level": 9, "n": 6, "title": "큰 보드", "desc": "여섯 쌍에서 안정 매칭을 찾아보세요."},
        {"level": 10, "n": 6, "title": "안정성 마스터", "desc": "큰 규모에서도 blocking pair를 제거하세요."},
    ],
    2: [
        {"level": 1, "n": 3, "title": "좋은 안정 매칭", "desc": "안정성과 점수를 함께 생각하세요."},
        {"level": 2, "n": 3, "title": "점수 개선", "desc": "안정적이지만 더 좋은 매칭이 있을 수 있습니다."},
        {"level": 3, "n": 4, "title": "최적성의 함정", "desc": "가장 좋아 보이는 매칭이 안정적이지 않을 수 있습니다."},
        {"level": 4, "n": 4, "title": "안정성과 만족도", "desc": "두 기준을 동시에 만족시켜야 합니다."},
        {"level": 5, "n": 4, "title": "균형 찾기", "desc": "개인 만족과 전체 만족의 균형을 보세요."},
        {"level": 6, "n": 5, "title": "최고 안정 점수", "desc": "가능한 stable matching들을 비교합니다."},
        {"level": 7, "n": 5, "title": "두 번째 기준", "desc": "stable만으로는 충분하지 않습니다."},
        {"level": 8, "n": 5, "title": "최적 안정성", "desc": "점수와 blocking pair를 함께 추적하세요."},
        {"level": 9, "n": 6, "title": "고난도 최적화", "desc": "큰 보드에서 최고 점수를 찾습니다."},
        {"level": 10, "n": 6, "title": "최적 매칭 마스터", "desc": "안정성과 최적성을 동시에 달성하세요."},
    ],
    3: [
        {"level": 1, "n": 3, "title": "첫 제안", "desc": "Gale-Shapley 결과를 예측합니다."},
        {"level": 2, "n": 3, "title": "임시 보류", "desc": "여성은 가장 좋은 제안만 보류합니다."},
        {"level": 3, "n": 3, "title": "거절과 재제안", "desc": "거절된 남성은 다음 순위에게 제안합니다."},
        {"level": 4, "n": 4, "title": "네 명의 제안자", "desc": "제안 흐름을 머릿속으로 따라가세요."},
        {"level": 5, "n": 4, "title": "교체 발생", "desc": "더 선호하는 제안이 오면 보류 상대가 바뀝니다."},
        {"level": 6, "n": 4, "title": "알고리즘 추적", "desc": "각 단계의 상태를 예측하세요."},
        {"level": 7, "n": 5, "title": "긴 제안 체인", "desc": "거절이 연쇄적으로 이어질 수 있습니다."},
        {"level": 8, "n": 5, "title": "남성 최적성", "desc": "남성 제안형 결과의 특징을 관찰하세요."},
        {"level": 9, "n": 6, "title": "복잡한 시뮬레이션", "desc": "큰 규모의 알고리즘 결과를 맞혀보세요."},
        {"level": 10, "n": 6, "title": "Gale-Shapley 마스터", "desc": "전체 과정을 예측해보세요."},
    ],
}


STAGE_INFO = {
    1: {
        "title": "1단계 — 안정 매칭",
        "short": "Blocking pair가 없도록 1:1 매칭을 만드세요.",
        "goal": "모든 사람을 1:1로 연결하되, 서로 현재 파트너보다 더 선호하는 두 사람이 생기지 않도록 만드세요.",
        "clear": "성공 조건: 완전한 1:1 매칭 + blocking pair 0개",
        "difficulty": "입문",
        "icon": "🧩",
        "tag": "안정성",
        "button": "레벨 선택",
    },
    2: {
        "title": "2단계 — 최적 안정 매칭",
        "short": "안정 매칭 중 전체 만족도 점수가 가장 높은 매칭을 찾으세요.",
        "goal": "안정 매칭은 여러 개일 수 있습니다. 그중 참가자들의 전체 만족도 점수가 가장 높은 매칭을 찾으세요.",
        "clear": "성공 조건: 안정 매칭 + 최고 만족도 점수",
        "difficulty": "중급",
        "icon": "🎯",
        "tag": "최적성",
        "button": "레벨 선택",
    },
    3: {
        "title": "3단계 — 게일-섀플리 챌린지",
        "short": "남성 제안형 Gale-Shapley 알고리즘의 결과를 예측하세요.",
        "goal": "선호표를 보고, 남성들이 차례로 제안할 때 Gale-Shapley 알고리즘이 만드는 최종 매칭을 예측하세요.",
        "clear": "성공 조건: 알고리즘 결과와 정확히 같은 매칭",
        "difficulty": "고급",
        "icon": "⚙️",
        "tag": "알고리즘",
        "button": "레벨 선택",
    },
}


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def esc(x):
    return html.escape(str(x))


def rank_badge(rank: int):
    if rank == 1:
        return "🥇"
    if rank == 2:
        return "🥈"
    if rank == 3:
        return "🥉"
    return str(rank)


def init_state():
    defaults = {
        "view": "home",
        "stage": 1,
        "level": 1,
        "pref_variant": 0,
        "name_variant": 0,
        "current_matching": {},
        "selected_man": None,
        "selected_woman": None,
        "submitted": False,
        "show_solution": False,
        "show_hint": False,
        "gs_step": 0,
        "unlocked": {1: 1, 2: 1, 3: 1},
        "records": {},
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_interaction_state():
    st.session_state.current_matching = {}
    st.session_state.selected_man = None
    st.session_state.selected_woman = None
    st.session_state.submitted = False
    st.session_state.show_solution = False
    st.session_state.show_hint = False
    st.session_state.gs_step = 0


def level_seed(stage: int, level: int) -> int:
    return 9187 + stage * 1000 + level * 137


def current_level_info():
    return LEVELS[st.session_state.stage][st.session_state.level - 1]


def current_seeds():
    base = level_seed(st.session_state.stage, st.session_state.level)
    name_seed = base + st.session_state.name_variant * 100_000
    pref_seed = base + st.session_state.pref_variant * 100_000 + 53
    return name_seed, pref_seed


def current_game_data():
    info = current_level_info()
    name_seed, pref_seed = current_seeds()
    return generate_preferences(info["n"], seed=pref_seed, name_seed=name_seed)


def sanitize_matching(men, women):
    current = st.session_state.current_matching
    current = {
        m: w
        for m, w in current.items()
        if m in men and w in women
    }

    used = set()
    clean = {}
    for m, w in current.items():
        if w not in used:
            clean[m] = w
            used.add(w)

    st.session_state.current_matching = clean


def go_home():
    st.session_state.view = "home"
    clear_interaction_state()
    st.rerun()


def go_stage_menu(stage: int):
    st.session_state.stage = stage
    st.session_state.view = "levels"
    clear_interaction_state()
    st.rerun()


def start_level(stage: int, level: int):
    st.session_state.stage = stage
    st.session_state.level = level
    st.session_state.view = "game"
    st.session_state.pref_variant = 0
    st.session_state.name_variant = 0
    clear_interaction_state()
    st.rerun()


def next_level():
    stage = st.session_state.stage
    level = st.session_state.level
    if level < len(LEVELS[stage]):
        start_level(stage, level + 1)
    else:
        go_stage_menu(stage)


def new_puzzle_same_level():
    st.session_state.name_variant += 1
    st.session_state.pref_variant += 1
    clear_interaction_state()
    st.rerun()


def reshuffle_preferences():
    st.session_state.pref_variant += 1
    clear_interaction_state()
    st.rerun()


def set_selected_man(m):
    st.session_state.selected_man = m
    st.rerun()


def set_selected_woman(w):
    st.session_state.selected_woman = w
    st.rerun()


def connect_selected():
    m = st.session_state.selected_man
    w = st.session_state.selected_woman

    if not m or not w:
        return

    matching = dict(st.session_state.current_matching)

    if m in matching:
        del matching[m]

    for old_m, old_w in list(matching.items()):
        if old_w == w:
            del matching[old_m]

    matching[m] = w
    st.session_state.current_matching = matching
    st.session_state.selected_man = None
    st.session_state.selected_woman = None
    st.session_state.submitted = False
    st.rerun()


def unmatch_man(m):
    matching = dict(st.session_state.current_matching)
    if m in matching:
        del matching[m]
    st.session_state.current_matching = matching
    st.session_state.submitted = False
    st.rerun()


def render_progress(stage: int):
    unlocked = st.session_state.unlocked.get(stage, 1)
    cleared = sum(
        1
        for level in range(1, len(LEVELS[stage]) + 1)
        if st.session_state.records.get((stage, level), {}).get("cleared")
    )
    total = len(LEVELS[stage])
    pct = int(100 * cleared / total)

    st.markdown(
        f"""
        <div class="help-box">
            <b>진행도</b> — {cleared}/{total} 클리어 · 현재 해금 레벨 {unlocked}
            <div class="progress-bar"><div class="progress-fill" style="width:{pct}%;"></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stage_card(stage: int):
    info = STAGE_INFO[stage]
    unlocked = st.session_state.unlocked.get(stage, 1)
    cleared = sum(
        1
        for level in range(1, len(LEVELS[stage]) + 1)
        if st.session_state.records.get((stage, level), {}).get("cleared")
    )

    st.markdown(
        f"""
        <div class="stage-card">
            <div class="stage-icon">{info["icon"]}</div>
            <h3>{info["title"]}</h3>
            <div class="stage-meta">
                <span class="pill pill-blue">{info["tag"]}</span>
                <span class="pill pill-gray">{info["difficulty"]}</span>
                <span class="pill pill-green">{cleared}/10 클리어</span>
                <span class="pill pill-amber">Lv.{unlocked} 해금</span>
            </div>
            <p class="small-muted">{info["short"]}</p>
            <div class="help-box" style="margin-top:0.8rem;">
                <b>목표</b><br/>
                {info["goal"]}<br/><br/>
                <b>성공 조건</b><br/>
                {info["clear"]}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(info["button"], key=f"stage_{stage}_menu", use_container_width=True):
        go_stage_menu(stage)


def render_home():
    st.markdown(
        """
        <div class="sml-hero">
            <div class="sml-title">Stable Match Lab2</div>
            <p class="sml-subtitle">
                매칭 이론을 게임처럼 익히는 퍼즐 실험실입니다.
                카드를 선택해 직접 연결하고, blocking pair를 피하고,
                최적 안정 매칭과 Gale-Shapley 알고리즘의 결과를 탐구해보세요.
            </p>
            <div style="margin-top:1rem;">
                <span class="pill pill-blue">매칭 이론</span>
                <span class="pill pill-green">카드형 인터랙션</span>
                <span class="pill pill-purple">레벨 시스템</span>
                <span class="pill pill-amber">GS 시뮬레이터</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    for i, stage in enumerate([1, 2, 3]):
        with cols[i]:
            stage_card(stage)

    st.markdown("<br/>", unsafe_allow_html=True)
    with st.expander("매칭 이론 빠른 설명"):
        st.markdown(
            """
            **안정 매칭 stable matching**은 현재 매칭을 깨고 서로 새롭게 짝을 이루고 싶어 하는 두 사람이 없는 매칭입니다.

            **Blocking pair**는 서로 현재 파트너보다 상대방을 더 선호하는 한 쌍입니다. Blocking pair가 하나라도 있으면 현재 매칭은 불안정합니다.

            **최적 안정 매칭**은 먼저 안정 매칭이어야 하고, 그 안정 매칭들 중 전체 만족도 점수가 가장 높은 매칭입니다.

            **Gale-Shapley 알고리즘**은 안정 매칭을 찾는 대표적인 알고리즘입니다. 남성 제안형에서는 남성이 선호 순서대로 제안하고, 여성은 지금까지 받은 제안 중 가장 선호하는 사람만 임시로 보류합니다.
            """
        )


def render_level_menu():
    stage = st.session_state.stage
    info = STAGE_INFO[stage]
    unlocked = st.session_state.unlocked.get(stage, 1)

    top_a, top_b = st.columns([1, 5])
    with top_a:
        if st.button("← 홈", use_container_width=True):
            go_home()
    with top_b:
        st.markdown(
            f"""
            <div class="sml-hero" style="padding:1.35rem 1.55rem;">
                <div style="font-size:2rem;font-weight:900;letter-spacing:-0.04em;">{info["icon"]} {info["title"]}</div>
                <p class="sml-subtitle">{info["goal"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_progress(stage)

    st.markdown('<div class="section-title">레벨 선택</div>', unsafe_allow_html=True)

    levels = LEVELS[stage]
    for row in range(0, len(levels), 5):
        cols = st.columns(5)
        for col, level_info in zip(cols, levels[row:row+5]):
            lv = level_info["level"]
            locked = lv > unlocked
            record = st.session_state.records.get((stage, lv), {})
            cleared = record.get("cleared", False)
            attempts = record.get("attempts", 0)
            cls = "level-card locked" if locked else "level-card"

            with col:
                status = "클리어" if cleared else ("잠김" if locked else "도전 가능")
                status_class = "pill-green" if cleared else ("pill-gray" if locked else "pill-blue")
                st.markdown(
                    f"""
                    <div class="{cls}">
                        <span class="pill {status_class}">{status}</span>
                        <span class="pill pill-purple">{level_info["n"]}쌍</span>
                        <h3>Lv.{lv}</h3>
                        <b>{esc(level_info["title"])}</b>
                        <p class="small-muted">{esc(level_info["desc"])}</p>
                        <span class="pill pill-amber">시도 {attempts}회</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("시작", key=f"start_{stage}_{lv}", disabled=locked, use_container_width=True):
                    start_level(stage, lv)


def render_stage_explanation(stage: int):
    info = STAGE_INFO[stage]
    level_info = current_level_info()
    st.markdown(
        f"""
        <div class="feedback-card info">
            <span class="pill pill-blue">{info["difficulty"]}</span>
            <span class="pill pill-purple">{info["tag"]}</span>
            <span class="pill pill-amber">Lv.{level_info["level"]} · {level_info["n"]}쌍</span>
            <h3 style="margin:0.4rem 0 0.4rem 0;">{esc(level_info["title"])}</h3>
            <p style="margin-bottom:0.5rem;">{info["goal"]}</p>
            <b>{info["clear"]}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_person_card_html(name: str, prefs: list[str], selected=False, danger=False, gs_focus=False, side="M", matched_to=None):
    classes = ["person-card"]
    if selected:
        classes.append("selected")
    if danger:
        classes.append("danger")
    if gs_focus:
        classes.append("gs-focus")

    avatar = "👨‍🔬" if side == "M" else "👩‍🔬"
    rows = "".join(
        [
            f'<div class="pref-row"><div class="rank-dot">{rank_badge(idx)}</div><div>{esc(partner)}</div></div>'
            for idx, partner in enumerate(prefs, start=1)
        ]
    )
    matched = f'<span class="pill pill-green">현재: {esc(matched_to)}</span>' if matched_to else '<span class="pill pill-gray">미매칭</span>'
    selected_badge = '<span class="pill pill-blue">선택됨</span>' if selected else ""

    return (
        f'<div class="{" ".join(classes)}">'
        f'<div class="person-head">'
        f'<div class="person-name">{esc(name)}</div>'
        f'<div class="avatar">{avatar}</div>'
        f'</div>'
        f'{matched}{selected_badge}'
        f'<div class="pref-list" style="margin-top:0.55rem;">{rows}</div>'
        f'</div>'
    )


def render_preference_cards(men, women, men_prefs, women_prefs, highlighted_men=None, highlighted_women=None):
    highlighted_men = highlighted_men or set()
    highlighted_women = highlighted_women or set()
    matching = st.session_state.current_matching
    inv = {w: m for m, w in matching.items()}

    st.markdown('<div class="section-title">선호도 카드</div>', unsafe_allow_html=True)
    col_m, col_w = st.columns(2)

    with col_m:
        st.markdown('<span class="pill pill-blue">남성</span>', unsafe_allow_html=True)
        for m in men:
            st.markdown(
                render_person_card_html(
                    m,
                    men_prefs[m],
                    selected=st.session_state.selected_man == m,
                    danger=m in highlighted_men,
                    side="M",
                    matched_to=matching.get(m),
                ),
                unsafe_allow_html=True,
            )
            b1, b2 = st.columns([1, 1])
            with b1:
                if st.button("카드 선택", key=f"select_m_{m}_{st.session_state.pref_variant}_{st.session_state.name_variant}", use_container_width=True):
                    set_selected_man(m)
            with b2:
                if st.button("해제", key=f"unmatch_m_{m}_{st.session_state.pref_variant}_{st.session_state.name_variant}", use_container_width=True, disabled=m not in matching):
                    unmatch_man(m)

    with col_w:
        st.markdown('<span class="pill pill-purple">여성</span>', unsafe_allow_html=True)
        for w in women:
            st.markdown(
                render_person_card_html(
                    w,
                    women_prefs[w],
                    selected=st.session_state.selected_woman == w,
                    danger=w in highlighted_women,
                    side="W",
                    matched_to=inv.get(w),
                ),
                unsafe_allow_html=True,
            )
            if st.button("카드 선택", key=f"select_w_{w}_{st.session_state.pref_variant}_{st.session_state.name_variant}", use_container_width=True):
                set_selected_woman(w)


def render_pair_builder(men, women):
    matching = st.session_state.current_matching
    st.markdown('<div class="section-title">연결 보드</div>', unsafe_allow_html=True)

    selected_man = st.session_state.selected_man
    selected_woman = st.session_state.selected_woman
    left = selected_man if selected_man else "남성 카드 선택"
    right = selected_woman if selected_woman else "여성 카드 선택"

    st.markdown(
        f"""
        <div class="drag-zone">
            <div class="connection-box">
                <div class="small-muted">카드를 하나씩 선택한 뒤 연결하세요</div>
                <div class="connection-names">{esc(left)} &nbsp; ↔ &nbsp; {esc(right)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("연결하기", type="primary", use_container_width=True, disabled=not (selected_man and selected_woman)):
            connect_selected()
    with c2:
        if st.button("선택 취소", use_container_width=True):
            st.session_state.selected_man = None
            st.session_state.selected_woman = None
            st.rerun()

    st.markdown('<div class="section-title">현재 매칭 보드</div>', unsafe_allow_html=True)
    st.markdown('<div class="game-card">', unsafe_allow_html=True)
    for m in men:
        w = matching.get(m)
        if w:
            st.markdown(f'<div class="pair-chip"><span>{esc(m)}</span><span>↔</span><span>{esc(w)}</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="pair-chip pending"><span>{esc(m)}</span><span>↔</span><span>아직 매칭 안 됨</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_metrics(matching, men_prefs, women_prefs, best_score=None, gs_target=None):
    complete_count = len(matching)
    n = len(men_prefs)

    score_text = "—"
    if complete_count == n and len(set(matching.values())) == n:
        score_text = str(satisfaction_score(matching, men_prefs, women_prefs))

    best_text = "—" if best_score is None else str(best_score)
    target_text = "숨김" if gs_target is not None else "—"

    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric-box">
                <div class="metric-label">매칭 완료</div>
                <div class="metric-value">{complete_count}/{n}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">내 점수</div>
                <div class="metric-value">{score_text}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">최고 안정 점수</div>
                <div class="metric-value">{best_text}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">GS 정답</div>
                <div class="metric-value">{target_text}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_blocking_pair_details(blocking_pairs):
    st.markdown("**발견된 blocking pair:**")
    for bp in blocking_pairs:
        st.markdown(
            f"""
            <div class="feedback-card fail" style="margin-bottom:0.6rem;">
                <span class="pill pill-red">{esc(bp["man"])} ↔ {esc(bp["woman"])}</span><br/>
                {esc(bp["man"])}은/는 현재 상대 {esc(bp["man_current"])}을/를 #{bp["man_current_rank"]}순위로 생각하지만,
                {esc(bp["woman"])}을/를 #{bp["man_new_rank"]}순위로 더 선호합니다.<br/>
                {esc(bp["woman"])}은/는 현재 상대 {esc(bp["woman_current"])}을/를 #{bp["woman_current_rank"]}순위로 생각하지만,
                {esc(bp["man"])}을/를 #{bp["woman_new_rank"]}순위로 더 선호합니다.
            </div>
            """,
            unsafe_allow_html=True,
        )


def evaluate_submission(stage, matching, men, women, men_prefs, women_prefs):
    complete, message = is_complete_one_to_one(matching, men, women)
    final_gs, gs_steps = gale_shapley_trace(men, women, men_prefs, women_prefs)
    best_matching, best_score, _ = find_best_stable_matching(men, women, men_prefs, women_prefs)

    if not complete:
        return {
            "ok": False,
            "kind": "incomplete",
            "title": "완전한 1:1 매칭이 아닙니다",
            "message": message,
            "blocking_pairs": [],
            "score": None,
            "best_score": best_score,
            "best_matching": best_matching,
            "gs_matching": final_gs,
            "gs_steps": gs_steps,
        }

    blocking_pairs = find_blocking_pairs(matching, men_prefs, women_prefs)
    score = satisfaction_score(matching, men_prefs, women_prefs)

    if stage == 1:
        if not blocking_pairs:
            return {
                "ok": True,
                "kind": "stable",
                "title": "성공! 안정 매칭입니다.",
                "message": "Blocking pair가 하나도 없습니다.",
                "blocking_pairs": [],
                "score": score,
                "best_score": best_score,
                "best_matching": best_matching,
                "gs_matching": final_gs,
                "gs_steps": gs_steps,
            }
        return {
            "ok": False,
            "kind": "blocking",
            "title": "불안정한 매칭입니다",
            "message": "Blocking pair가 존재합니다.",
            "blocking_pairs": blocking_pairs,
            "score": score,
            "best_score": best_score,
            "best_matching": best_matching,
            "gs_matching": final_gs,
            "gs_steps": gs_steps,
        }

    if stage == 2:
        if blocking_pairs:
            return {
                "ok": False,
                "kind": "blocking",
                "title": "아직 안정 매칭이 아닙니다",
                "message": "2단계에서는 먼저 blocking pair를 모두 없앤 뒤, 그중 가장 높은 만족도 점수를 찾아야 합니다.",
                "blocking_pairs": blocking_pairs,
                "score": score,
                "best_score": best_score,
                "best_matching": best_matching,
                "gs_matching": final_gs,
                "gs_steps": gs_steps,
            }

        if score == best_score:
            return {
                "ok": True,
                "kind": "optimal",
                "title": "완벽합니다! 최적 안정 매칭입니다.",
                "message": f"내 점수 {score}점이 가능한 최고 안정 점수와 같습니다.",
                "blocking_pairs": [],
                "score": score,
                "best_score": best_score,
                "best_matching": best_matching,
                "gs_matching": final_gs,
                "gs_steps": gs_steps,
            }

        return {
            "ok": False,
            "kind": "stable_not_optimal",
            "title": "안정적이지만 최적은 아닙니다",
            "message": f"현재 매칭은 안정적이지만 점수는 {score}점입니다. 가능한 최고 안정 점수는 {best_score}점입니다.",
            "blocking_pairs": [],
            "score": score,
            "best_score": best_score,
            "best_matching": best_matching,
            "gs_matching": final_gs,
            "gs_steps": gs_steps,
        }

    if stage == 3:
        if matching == final_gs:
            return {
                "ok": True,
                "kind": "gs_correct",
                "title": "정답입니다! Gale-Shapley 결과를 맞혔습니다.",
                "message": "이 매칭은 남성 제안형 Gale-Shapley 알고리즘의 결과와 정확히 같습니다.",
                "blocking_pairs": blocking_pairs,
                "score": score,
                "best_score": best_score,
                "best_matching": best_matching,
                "gs_matching": final_gs,
                "gs_steps": gs_steps,
            }

        return {
            "ok": False,
            "kind": "gs_wrong",
            "title": "Gale-Shapley 결과와 다릅니다",
            "message": "현재 매칭이 안정적일 수도 있지만, 남성 제안형 Gale-Shapley 알고리즘의 결과는 아닙니다.",
            "blocking_pairs": blocking_pairs,
            "score": score,
            "best_score": best_score,
            "best_matching": best_matching,
            "gs_matching": final_gs,
            "gs_steps": gs_steps,
        }


def update_records_after_submit(result):
    stage = st.session_state.stage
    level = st.session_state.level
    key = (stage, level)
    record = st.session_state.records.get(key, {"attempts": 0, "cleared": False, "best_score": None})
    record["attempts"] = record.get("attempts", 0) + 1

    if result["ok"]:
        record["cleared"] = True
        if result["score"] is not None:
            previous = record.get("best_score")
            record["best_score"] = result["score"] if previous is None else max(previous, result["score"])

        if level < len(LEVELS[stage]):
            st.session_state.unlocked[stage] = max(st.session_state.unlocked.get(stage, 1), level + 1)

    st.session_state.records[key] = record


def render_feedback(result):
    css_class = "success" if result["ok"] else "fail"
    icon = "✅" if result["ok"] else "❌"

    st.markdown(
        f"""
        <div class="feedback-card {css_class}">
            <h3 style="margin-top:0;">{icon} {esc(result["title"])}</h3>
            <p>{esc(result["message"])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if result["blocking_pairs"]:
        render_blocking_pair_details(result["blocking_pairs"])

    if result["score"] is not None:
        st.markdown(
            f"""
            <div class="feedback-card info">
                <span class="pill pill-blue">내 점수: {result["score"]}</span>
                <span class="pill pill-green">최고 안정 점수: {result["best_score"]}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if result["ok"]:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("다음 레벨", type="primary", use_container_width=True):
                next_level()
        with col2:
            if st.button("레벨 선택으로", use_container_width=True):
                go_stage_menu(st.session_state.stage)


def render_solution_panel(stage, result):
    if result is None:
        return

    if stage in [1, 2]:
        if st.button("최적 안정 매칭 보기", use_container_width=True):
            st.session_state.show_solution = not st.session_state.show_solution

        if st.session_state.show_solution and result.get("best_matching"):
            st.info(f"최적 안정 매칭: {explain_matching(result['best_matching'])}")
            st.info(f"최고 안정 점수: {result['best_score']}")

    if stage == 3:
        if st.button("Gale-Shapley 정답 보기", use_container_width=True):
            st.session_state.show_solution = not st.session_state.show_solution

        if st.session_state.show_solution:
            st.info(f"Gale-Shapley 결과: {explain_matching(result['gs_matching'])}")


def render_hint(stage, men, women, men_prefs, women_prefs, matching):
    if st.button("힌트", use_container_width=True):
        st.session_state.show_hint = not st.session_state.show_hint

    if not st.session_state.show_hint:
        return

    complete, _ = is_complete_one_to_one(matching, men, women)

    if not complete:
        st.warning("먼저 완전한 1:1 매칭을 만들어보세요. 같은 사람이 두 번 선택되면 안 됩니다.")

    elif stage in [1, 2]:
        blocking_pairs = find_blocking_pairs(matching, men_prefs, women_prefs)
        if blocking_pairs:
            bp = blocking_pairs[0]
            st.warning(
                f"{bp['man']}와 {bp['woman']}을/를 유심히 보세요. "
                f"두 사람이 서로 현재 파트너보다 상대방을 더 선호할 수 있습니다."
            )
        else:
            if stage == 1:
                st.success("이미 안정 매칭으로 보입니다. 제출해보세요!")
            else:
                best_matching, best_score, _ = find_best_stable_matching(men, women, men_prefs, women_prefs)
                score = satisfaction_score(matching, men_prefs, women_prefs)
                if score == best_score:
                    st.success("안정적이면서 최적인 매칭으로 보입니다. 제출해보세요!")
                else:
                    st.info("안정적이지만 더 높은 점수의 안정 매칭이 있을 수 있습니다.")

    else:
        st.info(
            "남성 제안형 Gale-Shapley에서는 남성들이 자신의 선호 순서대로 제안하고, "
            "여성은 지금까지 받은 제안 중 가장 선호하는 사람만 임시로 보류합니다."
        )


def render_gs_step_state(step, men, women, men_prefs, women_prefs):
    held = step["held_by_woman"]
    proposer = step.get("proposer")
    target = step.get("target")
    rejected = step.get("rejected")
    accepted = step.get("accepted")
    inverse = {m: w for w, m in held.items()}

    event = step.get("event", "info")
    event_class = {
        "start": "pill-blue",
        "accept": "pill-green",
        "switch": "pill-purple",
        "reject": "pill-red",
        "done": "pill-green",
    }.get(event, "pill-gray")

    st.markdown(
        f"""
        <div class="step-box">
            <span class="pill {event_class}">Step {step["step"]}</span>
            <p style="font-weight:850; margin:0.55rem 0 0.2rem 0;">{esc(step["action"])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown('<div class="section-title">보류 중인 매칭</div>', unsafe_allow_html=True)
        if held:
            for w in women:
                m = held.get(w)
                if m:
                    st.markdown(f'<div class="pair-chip"><span>{esc(m)}</span><span>↔</span><span>{esc(w)}</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="pair-chip pending">아직 보류 중인 매칭이 없습니다.</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="section-title">대기 중인 남성</div>', unsafe_allow_html=True)
        free = step.get("free_men", [])
        if free:
            st.markdown(
                "".join([f'<span class="pill pill-amber">{esc(m)}</span>' for m in free]),
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<span class="pill pill-green">대기자 없음</span>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">이번 단계</div>', unsafe_allow_html=True)
        if proposer:
            st.markdown(f'<span class="pill pill-blue">제안자: {esc(proposer)}</span>', unsafe_allow_html=True)
        if target:
            st.markdown(f'<span class="pill pill-purple">대상: {esc(target)}</span>', unsafe_allow_html=True)
        if accepted:
            st.markdown(f'<span class="pill pill-green">보류: {esc(accepted)}</span>', unsafe_allow_html=True)
        if rejected:
            st.markdown(f'<span class="pill pill-red">거절: {esc(rejected)}</span>', unsafe_allow_html=True)


def render_gs_simulator(men, women, men_prefs, women_prefs):
    final_matching, steps = gale_shapley_trace(men, women, men_prefs, women_prefs)
    max_step = len(steps) - 1
    st.session_state.gs_step = max(0, min(st.session_state.gs_step, max_step))

    st.markdown('<div class="section-title">Gale-Shapley 단계별 시뮬레이터</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="feedback-card info">
            이 시뮬레이터는 남성 제안형 Gale-Shapley 알고리즘을 한 단계씩 보여줍니다.
            3단계 챌린지에서는 정답이 드러날 수 있으므로, 먼저 직접 예측해본 뒤 확인하는 것을 추천합니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    control_cols = st.columns(5)
    with control_cols[0]:
        if st.button("처음", use_container_width=True):
            st.session_state.gs_step = 0
            st.rerun()
    with control_cols[1]:
        if st.button("이전", use_container_width=True, disabled=st.session_state.gs_step <= 0):
            st.session_state.gs_step -= 1
            st.rerun()
    with control_cols[2]:
        if st.button("다음", use_container_width=True, disabled=st.session_state.gs_step >= max_step):
            st.session_state.gs_step += 1
            st.rerun()
    with control_cols[3]:
        if st.button("끝", use_container_width=True):
            st.session_state.gs_step = max_step
            st.rerun()
    with control_cols[4]:
        auto = st.button("자동 재생", use_container_width=True)

    progress_pct = int(100 * st.session_state.gs_step / max_step) if max_step > 0 else 100
    st.markdown(
        f"""
        <div class="progress-bar"><div class="progress-fill" style="width:{progress_pct}%;"></div></div>
        <p class="small-muted">현재 단계: {st.session_state.gs_step} / {max_step}</p>
        """,
        unsafe_allow_html=True,
    )

    placeholder = st.empty()

    if auto:
        for idx in range(st.session_state.gs_step, max_step + 1):
            st.session_state.gs_step = idx
            with placeholder.container():
                render_gs_step_state(steps[idx], men, women, men_prefs, women_prefs)
            time.sleep(0.65)
        st.rerun()
    else:
        with placeholder.container():
            render_gs_step_state(steps[st.session_state.gs_step], men, women, men_prefs, women_prefs)

    if st.session_state.gs_step == max_step:
        st.success(f"최종 Gale-Shapley 결과: {explain_matching(final_matching)}")


def render_game():
    stage = st.session_state.stage
    level_info = current_level_info()
    stage_info = STAGE_INFO[stage]

    st.markdown(
        f"""
        <div class="sml-hero" style="padding:1.25rem 1.45rem;">
            <div style="font-size:1.95rem;font-weight:900;letter-spacing:-0.04em;">{stage_info["icon"]} {esc(level_info["title"])}</div>
            <p class="sml-subtitle">{esc(level_info["desc"])}</p>
            <div style="margin-top:0.7rem;">
                <span class="pill pill-amber">Lv.{level_info["level"]}</span>
                <span class="pill pill-blue">{esc(stage_info["title"])}</span>
                <span class="pill pill-purple">{level_info["n"]}쌍</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="control-panel">
            <div class="control-title">게임 메뉴</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_cols = st.columns([0.95, 0.95, 1.25, 1.25, 1.05, 1.0])
    with top_cols[0]:
        if st.button("← 레벨", use_container_width=True):
            go_stage_menu(stage)
    with top_cols[1]:
        if st.button("🏠 첫 화면", use_container_width=True):
            go_home()
    with top_cols[2]:
        if st.button("🎲 같은 레벨 새 퍼즐", use_container_width=True):
            new_puzzle_same_level()
    with top_cols[3]:
        if st.button("🔀 선호도 랜덤 변경", use_container_width=True):
            reshuffle_preferences()
    with top_cols[4]:
        if st.button("🧹 전체 초기화", use_container_width=True):
            clear_interaction_state()
            st.rerun()
    with top_cols[5]:
        st.markdown(f'<span class="pill pill-green">진행 중</span>', unsafe_allow_html=True)

    render_stage_explanation(stage)

    men, women, men_prefs, women_prefs = current_game_data()
    sanitize_matching(men, women)
    matching = st.session_state.current_matching

    highlighted_men, highlighted_women = set(), set()
    result_key = (stage, st.session_state.level, st.session_state.name_variant, st.session_state.pref_variant)
    if "last_result" in st.session_state and st.session_state.get("last_result_key") == result_key:
        last_result = st.session_state["last_result"]
        for bp in last_result.get("blocking_pairs", []):
            highlighted_men.add(bp["man"])
            highlighted_women.add(bp["woman"])

    best_matching, best_score, _ = find_best_stable_matching(men, women, men_prefs, women_prefs)
    gs_matching, gs_steps = gale_shapley_trace(men, women, men_prefs, women_prefs)

    main_left, main_right = st.columns([1.18, 0.82])

    with main_left:
        render_preference_cards(men, women, men_prefs, women_prefs, highlighted_men, highlighted_women)

    with main_right:
        render_pair_builder(men, women)

        st.markdown('<div class="section-title">상태</div>', unsafe_allow_html=True)
        render_metrics(matching, men_prefs, women_prefs, best_score=best_score, gs_target=gs_matching if stage == 3 else None)

        submit_col, clear_col = st.columns(2)
        with submit_col:
            if st.button("제출", type="primary", use_container_width=True):
                result = evaluate_submission(stage, matching, men, women, men_prefs, women_prefs)
                st.session_state.last_result = result
                st.session_state.last_result_key = result_key
                st.session_state.submitted = True
                st.session_state.show_solution = False
                update_records_after_submit(result)
                st.rerun()

        with clear_col:
            if st.button("첫 화면으로", use_container_width=True):
                go_home()

        st.markdown('<div class="section-title">도움말</div>', unsafe_allow_html=True)
        render_hint(stage, men, women, men_prefs, women_prefs, matching)

        if st.session_state.get("submitted") and st.session_state.get("last_result_key") == result_key:
            st.markdown('<div class="section-title">결과</div>', unsafe_allow_html=True)
            result = st.session_state["last_result"]
            render_feedback(result)
            render_solution_panel(stage, result)

    if stage == 3:
        st.divider()
        render_gs_simulator(men, women, men_prefs, women_prefs)


def render_sidebar_navigation():
    with st.sidebar:
        st.markdown("## Stable Match Lab2")
        st.markdown(
            '<div class="sidebar-note">게임 중 언제든 첫 화면이나 레벨 선택으로 돌아갈 수 있습니다.</div>',
            unsafe_allow_html=True,
        )
        st.write("")

        if st.button("🏠 첫 화면으로 돌아가기", use_container_width=True):
            go_home()

        if st.session_state.view == "game":
            if st.button("← 현재 단계 레벨 선택", use_container_width=True):
                go_stage_menu(st.session_state.stage)

        st.divider()
        st.markdown("### 단계 바로가기")

        for stage_id, info in STAGE_INFO.items():
            if st.button(f'{info["icon"]} {info["title"]}', key=f"sidebar_stage_{stage_id}", use_container_width=True):
                go_stage_menu(stage_id)

        st.divider()
        st.markdown("### 현재 상태")
        st.write(f"화면: {st.session_state.view}")
        st.write(f"현재 단계: {STAGE_INFO[st.session_state.stage]['title']}")
        st.write(f"현재 레벨: {st.session_state.level}")
        unlocked = st.session_state.unlocked.get(st.session_state.stage, 1)
        st.write(f"해금 레벨: {unlocked}")


def main():
    inject_css()
    init_state()
    render_sidebar_navigation()

    if st.session_state.view == "home":
        render_home()
    elif st.session_state.view == "levels":
        render_level_menu()
    else:
        render_game()


if __name__ == "__main__":
    main()
