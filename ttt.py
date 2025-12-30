import streamlit as st
import random
from collections import Counter

# --- ページ設定 ---
st.set_page_config(page_title="Yahtzee Tactics: Balanced", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #ffffff; }
    h1, h2, h3, p, label { color: #ffffff !important; }
    div[data-testid="stMetricValue"] > div { color: #00ffaa !important; }
    .card-box { border: 1px solid #3e4452; padding: 10px; border-radius: 8px; background-color: #1a1c23; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

DICE_ICONS = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

# --- ロジック ---
def check_condition(dice, condition_name):
    counts = Counter(dice).values()
    u = sorted(list(set(dice)))
    if condition_name == "check_pair": return any(c >= 2 for c in counts)
    if condition_name == "check_three": return any(c >= 3 for c in counts)
    if condition_name == "check_small_straight":
        if len(u) < 4: return False
        consecutive = 1; max_c = 1
        for i in range(len(u)-1):
            if u[i+1] == u[i] + 1: consecutive += 1
            else: consecutive = 1
            max_c = max(max_c, consecutive)
        return max_c >= 4
    if condition_name == "check_full_house":
        c_list = sorted(list(counts))
        return c_list == [2, 3] or c_list == [5]
    if condition_name == "check_yahtzee": return len(set(dice)) == 1
    return False

def get_reason_text(dice, condition_name):
    names = {"check_pair": "ペア", "check_three": "三枚", "check_small_straight": "Sスト", "check_full_house": "フルハ", "check_yahtzee": "ヤッツィー"}
    return names.get(condition_name) if check_condition(dice, condition_name) else None

class Card:
    def __init__(self, name, ctype, value, condition_name, effect=None, duration=0):
        self.name, self.type, self.value, self.condition_name, self.effect, self.duration = name, ctype, value, condition_name, effect, duration

def get_innate_deck():
    return [
        Card("固有:一閃", "attack", 15, "check_pair"),
        Card("固有:双刃", "attack", 25, "check_pair"),
        Card("固有:毒液", "status", 10, "check_pair", effect="poison", duration=3),
        Card("固有:強撃", "attack", 45, "check_three"),
        Card("固有:爆裂", "attack", 70, "check_small_straight"),
        Card("固有:絶技", "attack", 90, "check_full_house"),
        Card("固有:神域", "attack", 150, "check_yahtzee")
    ]

# --- 初期化 ---
if 'deck' not in st.session_state or st.sidebar.button("♻️ ゲームをリセット"):
    common_deck = []
    # バランス調整済みの山札
    for _ in range(15): common_deck.append(Card("追撃・小剣", "attack", 25, "check_pair"))
    for _ in range(10): common_deck.append(Card("強襲・大剣", "attack", 65, "check_three"))
    for _ in range(6):  common_deck.append(Card("アイアン・ガード", "guard", 45, "check_pair")) # 削減
    for _ in range(5):  common_deck.append(Card("癒しのハーブ", "heal", 35, "check_pair")) # 追加：即時回復
    for _ in range(3):  common_deck.append(Card("癒しの香水", "status", 15, "check_pair", effect="regen", duration=3)) # 追加：持続回復
    for _ in range(4):  common_deck.append(Card("猛毒の粉末", "status", 12, "check_pair", effect="poison", duration=3))
    
    random.shuffle(common_deck)
    st.session_state.update({
        'deck': common_deck, 
        'p1': {"hp": 150, "hand": [], "innate": get_innate_deck(), "guard": 0, "bonus": 0, "status": []},
        'p2': {"hp": 150, "hand": [], "innate": get_innate_deck(), "guard": 0, "bonus": 0, "status": []},
        'current_player': "P1", 'dice': [random.randint(1, 6) for _ in range(5)],
        'phase': "action", 'reroll_done': False, 'log': ["対戦開始！"], 'winner': None, 'pending_action': None
    })

def process_status_effects(player_key):
    p = st.session_state[player_key]
    new_status = []
    for s in p["status"]:
        if s["type"] == "poison":
            p["hp"] -= s["value"]
            st.session_state.log.insert(0, f"⚠️ {player_key}は毒で {s['value']} ダメージ")
        elif s["type"] == "regen":
            p["hp"] = min(150, p["hp"] + s["value"])
            st.session_state.log.insert(0, f"💖 {player_key}は再生で {s['value']} 回復")
        s["duration"] -= 1
        if s["duration"] > 0: new_status.append(s)
    p["status"] = new_status

def switch_player():
    if st.session_state.p1["hp"] <= 0: st.session_state.winner = "PLAYER 2"
    elif st.session_state.p2["hp"] <= 0: st.session_state.winner = "PLAYER 1"
    if st.session_state.winner: return
    
    st.session_state.current_player = "P2" if st.session_state.current_player == "P1" else "P1"
    process_status_effects('p1' if st.session_state.current_player == "P1" else 'p2')
    st.session_state.phase = "action"; st.session_state.reroll_done = False
    st.session_state.p1["guard"] = 0; st.session_state.p2["guard"] = 0
    st.session_state.dice = [random.randint(1, 6) for _ in range(5)]
    st.session_state.pending_action = None

# --- UI ---
st.title("⚔️ YAHTZEE TACTICS ⚔️")

if st.session_state.winner:
    st.balloons(); st.success(f"🏆 {st.session_state.winner} の勝利！")
    if st.button("もう一度遊ぶ", use_container_width=True):
        del st.session_state['deck']; st.rerun()
    st.stop()

# ステータス表示
cols = st.columns(2)
for i, (col, key) in enumerate(zip(cols, ["p1", "p2"])):
    p = st.session_state[key]
    with col:
        st.subheader(f"PLAYER {i+1} {'🔥' if st.session_state.current_player == f'P{i+1}' else ''}")
        st.metric("HP", f"{max(0, p['hp'])} / 150")
        st.write(f"⚔️ 攻撃バフ: +{p['bonus']} | 🛡️ ガード: {p['guard']}")
        for s in p["status"]:
            label = "毒" if s["type"]=="poison" else "再生"
            color = "violet" if s["type"]=="poison" else "green"
            st.markdown(f":{color}[{label}: {s['value']} (残り{s['duration']}T)]")

st.divider()

if st.session_state.phase == "action":
    st.info(f"👉 現在のターン: {st.session_state.current_player}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎴 山札からドローして交代", use_container_width=True):
            p = st.session_state[st.session_state.current_player.lower()]
            if st.session_state.deck and len(p["hand"]) < 5:
                p["hand"].append(st.session_state.deck.pop())
                switch_player(); st.rerun()
    with c2:
        if st.button("⚔️ バトルフェーズへ", use_container_width=True, type="primary"):
            st.session_state.phase = "battle"; st.rerun()

elif st.session_state.phase == "battle":
    p_now = st.session_state[st.session_state.current_player.lower()]
    p_opp = st.session_state["p2" if st.session_state.current_player == "P1" else "p1"]
    
    d_cols = st.columns(5)
    for i, d in enumerate(st.session_state.dice): d_cols[i].markdown(f"## {DICE_ICONS[d]}")
    if not st.session_state.reroll_done:
        if st.button("🎲 振り直す"):
            st.session_state.dice = [random.randint(1, 6) for _ in range(5)]; st.session_state.reroll_done = True; st.rerun()

    st.write("---")
    st.subheader("使用可能なカード")
    available = []
    for c in p_now["innate"]:
        reason = get_reason_text(st.session_state.dice, c.condition_name)
        if reason: available.append((c, reason, "固有"))
    for c in p_now["hand"]:
        reason = get_reason_text(st.session_state.dice, c.condition_name)
        if reason: available.append((c, reason, "手札"))

    if not available:
        st.warning("出せる役がありません。")
        if st.button("ターン終了"): switch_player(); st.rerun()
    else:
        grid = st.columns(3)
        for idx, (card, reason, source) in enumerate(available):
            with grid[idx % 3]:
                st.markdown(f"**{source}: {card.name}**")
                if card.type == "attack":
                    total = max(0, card.value + p_now["bonus"] - p_opp["guard"])
                    st.markdown(f":red[攻撃: {total}] ({reason})")
                elif card.type == "heal":
                    st.markdown(f":green[回復: {card.value}] ({reason})")
                elif card.type == "status":
                    color = "violet" if card.effect == "poison" else "green"
                    label = "毒付与" if card.effect == "poison" else "再生付与"
                    st.markdown(f":{color}[{label}: {card.value}] ({reason})")
                else:
                    st.markdown(f":blue[防御: {card.value}] ({reason})")
                
                if st.button("発動", key=f"btn_{idx}", use_container_width=True):
                    if card.type in ["attack", "status"] and card.effect != "regen":
                        st.session_state.pending_action = {"card": card, "source": source}
                        st.session_state.phase = "counter"; st.rerun()
                    else:
                        # 回復・防御・リジェネは即時処理
                        if card.type == "heal": p_now["hp"] = min(150, p_now["hp"] + card.value)
                        elif card.type == "guard": p_now["guard"] = card.value
                        elif card.type == "status" and card.effect == "regen":
                            p_now["status"].append({"type": "regen", "value": card.value, "duration": card.duration})
                        
                        if source == "固有":
                            p_now["innate"].remove(card)
                            if not p_now["innate"]:
                                p_now["innate"] = get_innate_deck(); p_now["bonus"] += 10
                                st.session_state.log.insert(0, "✨ 固有復活 ＆ 攻撃力+10")
                        else: p_now["hand"].remove(card)
                        switch_player(); st.rerun()

elif st.session_state.phase == "counter":
    opp_key = "p2" if st.session_state.current_player == "P1" else "p1"
    p_opp = st.session_state[opp_key]
    st.warning(f"🛡️ 防御確認: {opp_key.upper()}")
    guards = [c for c in p_opp["hand"] if c.type == "guard"]
    options = ["防御しない"] + [f"{g.name} ({g.value})" for g in guards]
    choice = st.radio("ガード選択", options)

    if st.button("結果確定", type="primary"):
        action = st.session_state.pending_action
        card = action["card"]
        p_now = st.session_state[st.session_state.current_player.lower()]
        g_val = 0
        if choice != "防御しない":
            g_idx = options.index(choice) - 1
            g_card = guards[g_idx]; g_val = g_card.value; p_opp["hand"].remove(g_card)
        
        if card.type == "attack":
            dmg = max(0, (card.value + p_now["bonus"]) - g_val)
            p_opp["hp"] -= dmg
            st.session_state.log.insert(0, f"💥 {dmg}ダメ！")
        elif card.type == "status":
            p_opp["status"].append({"type": card.effect, "value": card.value, "duration": card.duration})
            st.session_state.log.insert(0, f"☣️ 毒付与！")

        if action["source"] == "固有":
            p_now["innate"].remove(card)
            if not p_now["innate"]:
                p_now["innate"] = get_innate_deck(); p_now["bonus"] += 10
        else: p_now["hand"].remove(card)
        switch_player(); st.rerun()

st.write("---")
st.write("📜 ログ:", st.session_state.log[:3])
