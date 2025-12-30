import streamlit as st
import random
from collections import Counter

# --- ページ設定 ---
st.set_page_config(page_title="Yahtzee Tactics: Debugged", layout="wide")

# 全体の背景と文字のコントラストを調整
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #ffffff; }
    /* 文字が白飛びしないよう色を固定 */
    .stMarkdown, p, h1, h2, h3, label { color: #ffffff !important; }
    /* メトリック（HP表示）の調整 */
    div[data-testid="stMetricValue"] > div { color: #00ffaa !important; }
    div[data-testid="stMetricLabel"] > div { color: #bbbbbb !important; }
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
        Card("クイック・一閃", "attack", 15, "check_pair", effect="draw"),
        Card("連撃・双刃", "attack", 25, "check_pair"),
        Card("毒液のナイフ", "status", 10, "check_pair", effect="poison", duration=3),
        Card("強撃・三枚", "attack", 45, "check_three"),
        Card("Sスト・ブレイク", "attack", 70, "check_small_straight"),
        Card("絶・フルハウス", "attack", 95, "check_full_house"),
        Card("極・ヤッツィー", "attack", 150, "check_yahtzee")
    ]

# --- 初期化 ---
if 'deck' not in st.session_state or st.sidebar.button("♻️ ゲームを再起動"):
    common_deck = []
    for _ in range(15): common_deck.append(Card("追撃・小剣", "attack", 20, "check_pair"))
    for _ in range(12): common_deck.append(Card("強襲・大剣", "attack", 65, "check_three"))
    for _ in range(10): common_deck.append(Card("アイアン・シールド", "guard", 40, "check_pair"))
    for _ in range(6):  common_deck.append(Card("猛毒の粉末", "status", 15, "check_pair", effect="poison", duration=3))
    random.shuffle(common_deck)
    st.session_state.update({
        'deck': common_deck, 
        'p1': {"hp": 150, "hand": [], "bonus": 0, "guard": 0, "innate": get_innate_deck(), "status": []},
        'p2': {"hp": 150, "hand": [], "bonus": 0, "guard": 0, "innate": get_innate_deck(), "status": []},
        'current_player': "P1", 'dice': [random.randint(1, 6) for _ in range(5)],
        'phase': "action", 'reroll_done': False, 'log': ["対戦開始！"], 'winner': None, 'pending_action': None
    })

def process_status_effects(player_key):
    p = st.session_state[player_key]
    new_status = []
    for s in p["status"]:
        if s["type"] == "poison":
            p["hp"] -= s["value"]
            st.session_state.log.insert(0, f"☣️ {player_key}に毒ダメージ: {s['value']}")
        s["duration"] -= 1
        if s["duration"] > 0: new_status.append(s)
    p["status"] = new_status

def check_victory():
    if st.session_state.p1["hp"] <= 0: st.session_state.winner = "PLAYER 2"
    elif st.session_state.p2["hp"] <= 0: st.session_state.winner = "PLAYER 1"

def switch_player():
    check_victory()
    if st.session_state.winner: return
    
    st.session_state.current_player = "P2" if st.session_state.current_player == "P1" else "P1"
    process_status_effects('p1' if st.session_state.current_player == "P1" else 'p2')
    st.session_state.phase = "action"
    st.session_state.reroll_done = False
    st.session_state.p1["guard"] = 0
    st.session_state.p2["guard"] = 0
    st.session_state.dice = [random.randint(1, 6) for _ in range(5)]
    st.session_state.pending_action = None

# --- UI構築 ---
st.title("⚔️ YAHTZEE TACTICS ⚔️")

if st.session_state.winner:
    st.balloons()
    st.success(f"🏆 {st.session_state.winner} の勝利！")
    if st.button("リスタート"):
        del st.session_state['deck']; st.rerun()
    st.stop()

# ステータス表示
col_p1, col_p2 = st.columns(2)
for i, (col, key) in enumerate(zip([col_p1, col_p2], ["p1", "p2"])):
    p = st.session_state[key]
    with col:
        turn_mark = " ✅" if st.session_state.current_player == f"P{i+1}" else ""
        st.subheader(f"PLAYER {i+1}{turn_mark}")
        st.metric("HP", f"{max(0, p['hp'])} / 150")
        st.write(f"🛡️ 次回ダメージ軽減: {p['guard']}")
        for s in p["status"]:
            st.warning(f"☣️ 猛毒状態: {s['value']}ダメ (残り{s['duration']}ターン)")

st.divider()

if st.session_state.phase == "action":
    st.info(f"👉 現在のターン: {st.session_state.current_player}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎴 山札から1枚引く", use_container_width=True):
            p_key = st.session_state.current_player.lower()
            if st.session_state.deck and len(st.session_state[p_key]["hand"]) < 5:
                st.session_state[p_key]["hand"].append(st.session_state.deck.pop())
                switch_player(); st.rerun()
    with c2:
        if st.button("⚔️ 攻撃フェーズへ", use_container_width=True, type="primary"):
            st.session_state.phase = "battle"; st.rerun()

elif st.session_state.phase == "battle":
    p_now = st.session_state.p1 if st.session_state.current_player == "P1" else st.session_state.p2
    p_opp = st.session_state.p2 if st.session_state.current_player == "P1" else st.session_state.p1
    
    # ダイス表示
    st.write("🎲 ダイスの目:")
    d_cols = st.columns(5)
    for i, d in enumerate(st.session_state.dice):
        d_cols[i].markdown(f"## {DICE_ICONS[d]}")
    
    if not st.session_state.reroll_done:
        if st.button("🎲 1回だけ振り直す"):
            st.session_state.dice = [random.randint(1, 6) for _ in range(5)]
            st.session_state.reroll_done = True; st.rerun()

    st.write("---")
    st.write("### 使うカードを選択してください")
    
    all_cards = []
    for c in p_now["innate"] + p_now["hand"]:
        reason = get_reason_text(st.session_state.dice, c.condition_name)
        if reason:
            source = "【固有】" if c in p_now["innate"] else "【手札】"
            all_cards.append((c, reason, source))

    if not all_cards:
        st.warning("出せる役がありません...")
        if st.button("ターンを終了する"): switch_player(); st.rerun()
    else:
        for idx, (card, reason, source) in enumerate(all_cards):
            row = st.container()
            c_left, c_right = row.columns([4, 1])
            with c_left:
                # 色付き説明（ボタンの外側に配置してバグを防ぐ）
                if card.type == "attack":
                    val = max(0, card.value - p_opp["guard"])
                    st.markdown(f"**{source} {card.name}** ({reason}) → :red[予測ダメ: {val}]")
                elif card.type == "status":
                    st.markdown(f"**{source} {card.name}** ({reason}) → :violet[毒付与: {card.value}]")
                else:
                    st.markdown(f"**{source} {card.name}** ({reason}) → :orange[防御UP: {card.value}]")
            with c_right:
                if st.button("使用", key=f"use_{idx}", use_container_width=True):
                    if card.type in ["attack", "status"]:
                        st.session_state.pending_action = {"card": card, "source": source}
                        st.session_state.phase = "counter"; st.rerun()
                    else:
                        if card.type == "guard": p_now["guard"] = card.value
                        if "固有" in source: p_now["innate"].remove(card)
                        else: p_now["hand"].remove(card)
                        switch_player(); st.rerun()

elif st.session_state.phase == "counter":
    opp_key = "p2" if st.session_state.current_player == "P1" else "p1"
    p_opp = st.session_state[opp_key]
    st.warning(f"🛡️ 防御確認: {opp_key.upper()} はガードカードを使いますか？")
    
    available_guards = [c for c in p_opp["hand"] if c.type == "guard"]
    options = ["防御しない"] + [f"{g.name} (軽減:{g.value})" for g in available_guards]
    selected = st.radio("（相手には伏せて選択）", options)

    if st.button("決定してダメージを処理", type="primary"):
        action = st.session_state.pending_action
        card = action["card"]
        p_now = st.session_state.p1 if st.session_state.current_player == "P1" else st.session_state.p2
        
        g_val = 0
        if selected != "防御しない":
            g_idx = options.index(selected) - 1
            g_card = available_guards[g_idx]
            g_val = g_card.value
            p_opp["hand"].remove(g_card)
        
        if card.type == "attack":
            dmg = max(0, card.value - g_val)
            p_opp["hp"] -= dmg
            st.session_state.log.insert(0, f"💥 {dmg}ダメージ！")
        elif card.type == "status":
            p_opp["status"].append({"type": card.effect, "value": card.value, "duration": card.duration})
            st.session_state.log.insert(0, f"☣️ 状態異常を与えた！")

        if "固有" in action["source"]: p_now["innate"].remove(card)
        else: p_now["hand"].remove(card)
        switch_player(); st.rerun()

st.write("---")
st.write("📜 バトル記録:")
for l in st.session_state.log[:3]: st.write(f"- {l}")
