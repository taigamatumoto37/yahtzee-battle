import streamlit as st
import random
from collections import Counter

# --- ページ設定 ---
st.set_page_config(page_title="Yahtzee Tactics: Error Fixed", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .main-header { text-align: center; color: #00d4ff; font-family: 'Courier New', Courier, monospace; }
    .player-card { 
        padding: 20px; border-radius: 15px; background: linear-gradient(145deg, #1e222d, #161922);
        border: 1px solid #3e4452; box-shadow: 5px 5px 15px rgba(0,0,0,0.3);
    }
    .active-p1 { border: 2px solid #ff4b4b !important; box-shadow: 0 0 20px rgba(255, 75, 75, 0.3); }
    .active-p2 { border: 2px solid #00d4ff !important; box-shadow: 0 0 20px rgba(0, 212, 255, 0.3); }
    .dice-container { display: flex; justify-content: center; gap: 20px; margin: 30px 0; }
    .dice-box { 
        font-size: 80px; background: #ffffff; color: #333; width: 100px; height: 100px; 
        display: flex; align-items: center; justify-content: center; border-radius: 12px; 
        box-shadow: inset -5px -5px 10px #bbb, 5px 5px 15px rgba(0,0,0,0.5);
    }
    .badge { padding: 4px 10px; border-radius: 12px; font-size: 0.8em; font-weight: bold; margin-right: 5px; }
    .bg-innate { background-color: #ff4b4b; color: white; }
    .bg-hand { background-color: #28a745; color: white; }
    </style>
    """, unsafe_allow_html=True)

DICE_ICONS = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

# --- 判定ロジック ---
def get_counts(d): return Counter(d)
def check_pair(d): return any(count >= 2 for count in get_counts(d).values())
def check_three(d): return any(count >= 3 for count in get_counts(d).values())
def check_small_straight(d): 
    u = sorted(list(set(d)))
    count = 1; max_count = 1
    for i in range(len(u)-1):
        if u[i+1] == u[i] + 1: count += 1
        else: count = 1
        max_count = max(max_count, count)
    return max_count >= 4
def check_full_house(d): 
    counts = sorted(get_counts(d).values())
    return counts == [2, 3] or counts == [5]
def check_yahtzee(d): return len(set(d)) == 1

def get_satisfied_condition(d, condition_func):
    if condition_func == check_pair and check_pair(d): return "ワンペア"
    if condition_func == check_three and check_three(d): return "スリーカード"
    if condition_func == check_small_straight and check_small_straight(d): return "Sストレート"
    if condition_func == check_full_house and check_full_house(d): return "フルハウス"
    if condition_func == check_yahtzee and check_yahtzee(d): return "ヤッツィー"
    return None

class Card:
    def __init__(self, name, ctype, value, condition, effect=None):
        self.name, self.type, self.value, self.condition, self.effect = name, ctype, value, condition, effect

def get_innate_deck():
    return [
        Card("固有:クイック・一閃", "attack", 10, check_pair, effect="draw"),
        Card("固有:スカウト・斬撃", "attack", 10, check_pair, effect="draw"),
        Card("固有:連撃・双刃", "attack", 20, check_pair),
        Card("固有:連撃・三刃", "attack", 35, check_three),
        Card("固有:ストレート・ブレイク", "attack", 45, check_small_straight),
        Card("固有:ストレート・エッジ", "attack", 45, check_small_straight),
        Card("固有:フルハウス・インパクト", "attack", 70, check_full_house),
        Card("固有:アルティメット・エンド", "attack", 110, check_yahtzee)
    ]

# --- 初期化 ---
if 'deck' not in st.session_state:
    common_deck = []
    for _ in range(15): common_deck.append(Card("アイアン・シールド", "guard", 25, check_pair))
    for _ in range(10): common_deck.append(Card("癒しのハーブ", "heal", 30, check_pair))
    for _ in range(5):  common_deck.append(Card("強襲・大剣", "attack", 55, check_three))
    random.shuffle(common_deck)
    st.session_state.update({
        'deck': common_deck, 
        'p1': {"hp": 150, "hand": [], "bonus": 0, "guard": 0, "innate": get_innate_deck()},
        'p2': {"hp": 150, "hand": [], "bonus": 0, "guard": 0, "innate": get_innate_deck()},
        'current_player': "P1", 'dice': [random.randint(1, 6) for _ in range(5)],
        'phase': "action", 'reroll_done': False, 'log': ["バトル開始！"]
    })

def switch_player():
    st.session_state.current_player = "P2" if st.session_state.current_player == "P1" else "P1"
    st.session_state.phase = "action"; st.session_state.reroll_done = False
    st.session_state.p1["guard"] = 0; st.session_state.p2["guard"] = 0
    st.session_state.dice = [random.randint(1, 6) for _ in range(5)]

# --- メインレイアウト ---
st.markdown("<h1 class='main-header'>⚔️ YAHTZEE TACTICS ⚔️</h1>", unsafe_allow_html=True)

# 現在のプレイヤーと相手を特定
p_now = st.session_state.p1 if st.session_state.current_player == "P1" else st.session_state.p2
p_opp = st.session_state.p2 if st.session_state.current_player == "P1" else st.session_state.p1

col_p1, col_vs, col_p2 = st.columns([4, 1, 4])
for i, (col, p_key) in enumerate(zip([col_p1, col_p2], ["p1", "p2"])):
    p = st.session_state[p_key]
    active_class = f"active-p{i+1}" if st.session_state.current_player == f"P{i+1}" else ""
    with col:
        st.markdown(f'<div class="player-card {active_class}"><h3>PLAYER {i+1}</h3><p>HP: {p["hp"]} / 150</p></div>', unsafe_allow_html=True)
        st.progress(max(0, min(p['hp'] / 150, 1.0)))
        st.write(f"✨ Bonus: +{p['bonus']} | 🛡️ Guard: {p['guard']}")
        st.write(f"🎴 固有: {len(p['innate'])} | 手札: {len(p['hand'])}/5")

st.divider()

if st.session_state.phase == "action":
    st.markdown(f"<h3 style='text-align:center;'>【{st.session_state.current_player}】 移動フェーズ</h3>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    can_draw = len(p_now["hand"]) < 5
    if c1.button("🎴 山札から引いて交代", use_container_width=True, disabled=not can_draw):
        if st.session_state.deck:
            p_now["hand"].append(st.session_state.deck.pop())
            st.session_state.log.insert(0, f"{st.session_state.current_player}がドロー")
            switch_player(); st.rerun()
    if c2.button("⚔️ 攻撃を仕掛ける（ダイスへ）", use_container_width=True, type="primary"):
        st.session_state.phase = "battle"; st.rerun()

elif st.session_state.phase == "battle":
    dice_html = "".join([f'<div class="dice-box">{DICE_ICONS[d]}</div>' for d in st.session_state.dice])
    st.markdown(f'<div class="dice-container">{dice_html}</div>', unsafe_allow_html=True)
    
    if not st.session_state.reroll_done:
        if st.button("🎲 ダイスを一度だけ振り直す", use_container_width=True):
            st.session_state.dice = [random.randint(1, 6) for _ in range(5)]
            st.session_state.reroll_done = True; st.rerun()

    all_cards = []
    # 固有と手札を合わせて判定
    for c in p_now["innate"] + p_now["hand"]:
        reason = get_satisfied_condition(st.session_state.dice, c.condition)
        if reason:
            source = "innate" if c in p_now["innate"] else "hand"
            all_cards.append((c, reason, source))

    if not all_cards:
        st.error("役が揃いませんでした。")
        if st.button("ターン終了", use_container_width=True): switch_player(); st.rerun()
    else:
        cols = st.columns(len(all_cards) if len(all_cards) <= 4 else 4)
        for idx, (card, reason, source) in enumerate(all_cards):
            with cols[idx % 4]:
                st.markdown(f"<span class='badge {'bg-innate' if source=='innate' else 'bg-hand'}'>{source.upper()}</span>", unsafe_allow_html=True)
                if st.button(f"{card.name}\n({reason})", key=f"btn_{idx}", use_container_width=True):
                    if card.type == "attack":
                        dmg = max(0, (card.value + p_now["bonus"]) - p_opp["guard"])
                        p_opp["hp"] -= dmg
                        if card.effect == "draw" and len(p_now["hand"]) < 5 and st.session_state.deck:
                            p_now["hand"].append(st.session_state.deck.pop())
                        st.session_state.log.insert(0, f"{card.name}！ {dmg}ダメ")
                    elif card.type == "guard":
                        p_now["guard"] = card.value
                        st.session_state.log.insert(0, f"{card.name}展開")
                    elif card.type == "heal":
                        p_now["hp"] += card.value
                        st.session_state.log.insert(0, f"{card.name}回復")

                    if source == "innate":
                        p_now["innate"].remove(card)
                        if not p_now["innate"]:
                            p_now["bonus"] += 10; p_now["innate"] = get_innate_deck()
                            st.session_state.log.insert(0, "🌟覚醒！")
                    else: p_now["hand"].remove(card)
                    switch_player(); st.rerun()

st.divider()
for l in st.session_state.log[:3]: st.write(f"- {l}")
