import streamlit as st
import random
from collections import Counter

# --- ページ設定 ---
st.set_page_config(page_title="Yahtzee Tactics: Final Edition", layout="wide")

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
    .badge { padding: 4px 10px; border-radius: 12px; font-size: 0.8em; font-weight: bold; margin-bottom: 5px; display: inline-block; }
    .bg-innate { background-color: #ff4b4b; color: white; }
    .bg-hand { background-color: #28a745; color: white; }
    .dmg-text { color: #ffcc00; font-weight: bold; font-size: 1.1em; }
    </style>
    """, unsafe_allow_html=True)

DICE_ICONS = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

# --- 判定ロジック ---
def check_condition(dice, condition_name):
    counts = Counter(dice).values()
    unique_sorted = sorted(list(set(dice)))
    if condition_name == "check_pair": return any(c >= 2 for c in counts)
    if condition_name == "check_three": return any(c >= 3 for c in counts)
    if condition_name == "check_small_straight":
        if len(unique_sorted) < 4: return False
        consecutive = 1; max_c = 1
        for i in range(len(unique_sorted)-1):
            if unique_sorted[i+1] == unique_sorted[i] + 1: consecutive += 1
            else: consecutive = 1
            max_c = max(max_c, consecutive)
        return max_c >= 4
    if condition_name == "check_full_house":
        c_list = sorted(list(counts))
        return c_list == [2, 3] or c_list == [5]
    if condition_name == "check_yahtzee": return len(set(dice)) == 1
    return False

def get_reason_text(dice, condition_name):
    names = {"check_pair": "ワンペア", "check_three": "スリーカード", "check_small_straight": "Sストレート", "check_full_house": "フルハウス", "check_yahtzee": "ヤッツィー"}
    return names.get(condition_name) if check_condition(dice, condition_name) else None

class Card:
    def __init__(self, name, ctype, value, condition_name, effect=None):
        self.name, self.type, self.value, self.condition_name, self.effect = name, ctype, value, condition_name, effect

def get_innate_deck():
    return [
        Card("クイック・一閃", "attack", 10, "check_pair", effect="draw"),
        Card("スカウト・斬撃", "attack", 10, "check_pair", effect="draw"),
        Card("連撃・双刃", "attack", 20, "check_pair"),
        Card("連撃・三刃", "attack", 35, "check_three"),
        Card("ストレート・ブレイク", "attack", 45, "check_small_straight"),
        Card("ストレート・エッジ", "attack", 45, "check_small_straight"),
        Card("フルハウス・インパクト", "attack", 70, "check_full_house"),
        Card("アルティメット・エンド", "attack", 110, "check_yahtzee")
    ]

# --- 初期化 ---
if 'deck' not in st.session_state or st.sidebar.button("♻️ ゲームをリセット"):
    common_deck = []
    for _ in range(15): common_deck.append(Card("アイアン・シールド", "guard", 25, "check_pair"))
    for _ in range(10): common_deck.append(Card("癒しのハーブ", "heal", 30, "check_pair"))
    for _ in range(5):  common_deck.append(Card("強襲・大剣", "attack", 55, "check_three"))
    random.shuffle(common_deck)
    st.session_state.update({
        'deck': common_deck, 'p1': {"hp": 150, "hand": [], "bonus": 0, "guard": 0, "innate": get_innate_deck()},
        'p2': {"hp": 150, "hand": [], "bonus": 0, "guard": 0, "innate": get_innate_deck()},
        'current_player': "P1", 'dice': [random.randint(1, 6) for _ in range(5)],
        'phase': "action", 'reroll_done': False, 'log': ["バトル開始！"], 'winner': None
    })

def switch_player():
    if st.session_state.p1["hp"] <= 0: st.session_state.winner = "PLAYER 2"
    elif st.session_state.p2["hp"] <= 0: st.session_state.winner = "PLAYER 1"
    
    if st.session_state.winner: return
    
    st.session_state.current_player = "P2" if st.session_state.current_player == "P1" else "P1"
    st.session_state.phase = "action"; st.session_state.reroll_done = False
    st.session_state.p1["guard"] = 0; st.session_state.p2["guard"] = 0
    st.session_state.dice = [random.randint(1, 6) for _ in range(5)]

# --- メインレイアウト ---
st.markdown("<h1 class='main-header'>⚔️ YAHTZEE TACTICS ⚔️</h1>", unsafe_allow_html=True)

# 勝利判定
if st.session_state.winner:
    st.balloons()
    st.markdown(f"<h1 style='text-align:center; color:#ffcc00;'>🏆 {st.session_state.winner} の勝利！</h1>", unsafe_allow_html=True)
    if st.button("もう一度遊ぶ", use_container_width=True):
        del st.session_state['deck']
        st.rerun()
    st.stop()

p_now = st.session_state.p1 if st.session_state.current_player == "P1" else st.session_state.p2
p_opp = st.session_state.p2 if st.session_state.current_player == "P1" else st.session_state.p1

col_p1, col_vs, col_p2 = st.columns([4, 1, 4])
for i, (col, p_key) in enumerate(zip([col_p1, col_p2], ["p1", "p2"])):
    p = st.session_state[p_key]
    active_class = f"active-p{i+1}" if st.session_state.current_player == f"P{i+1}" else ""
    with col:
        st.markdown(f'<div class="player-card {active_class}"><h3>PLAYER {i+1}</h3><p>HP: {max(0, p["hp"])} / 150</p></div>', unsafe_allow_html=True)
        st.progress(max(0, min(p['hp'] / 150, 1.0)))
        st.write(f"✨ Bonus: +{p['bonus']} | 🛡️ Guard: {p['guard']}")

st.divider()

if st.session_state.phase == "action":
    st.markdown(f"<h3 style='text-align:center;'>【{st.session_state.current_player}】 移動フェーズ</h3>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    can_draw = len(p_now["hand"]) < 5
    if c1.button("🎴 ドローして交代", use_container_width=True, disabled=not can_draw):
        if st.session_state.deck:
            p_now["hand"].append(st.session_state.deck.pop())
            st.session_state.log.insert(0, f"{st.session_state.current_player}がドロー"); switch_player(); st.rerun()
    if c2.button("⚔️ 攻撃を仕掛ける", use_container_width=True, type="primary"):
        st.session_state.phase = "battle"; st.rerun()

elif st.session_state.phase == "battle":
    dice_html = "".join([f'<div class="dice-box">{DICE_ICONS[d]}</div>' for d in st.session_state.dice])
    st.markdown(f'<div class="dice-container">{dice_html}</div>', unsafe_allow_html=True)
    
    if not st.session_state.reroll_done:
        if st.button("🎲 ダイスを振り直す", use_container_width=True):
            st.session_state.dice = [random.randint(1, 6) for _ in range(5)]; st.session_state.reroll_done = True; st.rerun()

    all_cards = []
    for c in p_now["innate"]:
        reason = get_reason_text(st.session_state.dice, c.condition_name)
        if reason: all_cards.append((c, reason, "innate"))
    for c in p_now["hand"]:
        reason = get_reason_text(st.session_state.dice, c.condition_name)
        if reason: all_cards.append((c, reason, "hand"))

    if not all_cards:
        st.error("役が揃いませんでした。")
        if st.button("交代する"): switch_player(); st.rerun()
    else:
        st.write("### 発動するカードを選択：")
        cols = st.columns(len(all_cards) if len(all_cards) <= 4 else 4)
        for idx, (card, reason, source) in enumerate(all_cards):
            with cols[idx % 4]:
                st.markdown(f"<span class='badge {'bg-innate' if source=='innate' else 'bg-hand'}'>{source.upper()}</span>", unsafe_allow_html=True)
                
                # ダメージ・回復・防御力の計算表示
                detail_text = ""
                if card.type == "attack":
                    raw_dmg = card.value + p_now["bonus"]
                    actual_dmg = max(0, raw_dmg - p_opp["guard"])
                    detail_text = f"\n威力:{raw_dmg} (実ダメ:{actual_dmg})"
                elif card.type == "guard":
                    detail_text = f"\n防御力:{card.value}"
                elif card.type == "heal":
                    detail_text = f"\n回復量:{card.value}"

                if st.button(f"{card.name}\n({reason}){detail_text}", key=f"btn_{idx}", use_container_width=True):
                    if card.type == "attack":
                        dmg = max(0, (card.value + p_now["bonus"]) - p_opp["guard"])
                        p_opp["hp"] -= dmg
                        st.session_state.log.insert(0, f"{st.session_state.current_player}の{card.name}！ {dmg}ダメージ！")
                        if card.effect == "draw" and len(p_now["hand"]) < 5 and st.session_state.deck:
                            p_now["hand"].append(st.session_state.deck.pop())
                    elif card.type == "guard":
                        p_now["guard"] = card.value
                        st.session_state.log.insert(0, f"{st.session_state.current_player}は守りを固めた！")
                    elif card.type == "heal":
                        p_now["hp"] += card.value
                        st.session_state.log.insert(0, f"{st.session_state.current_player}は{card.value}回復した！")

                    if source == "innate":
                        p_now["innate"].remove(card)
                        if not p_now["innate"]:
                            p_now["bonus"] += 15; p_now["innate"] = get_innate_deck()
                            st.session_state.log.insert(0, f"🌟 {st.session_state.current_player} 覚醒！ 攻撃ボーナス増加！")
                    else: p_now["hand"].remove(card)
                    
                    switch_player(); st.rerun()

st.divider()
for l in st.session_state.log[:3]: st.write(f"- {l}")
