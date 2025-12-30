import streamlit as st
import random
from collections import Counter

# --- ページ設定 ---
st.set_page_config(page_title="Yahtzee Tactics: Fixed Edition", layout="wide")

# 基本の文字色を強制的に白にするCSS
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    h1, h2, h3, p, label, .stMarkdown { color: #ffffff !important; }
    div[data-testid="stMetricValue"] > div { color: #00ffaa !important; }
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
        Card("固有:クイック・一閃", "attack", 15, "check_pair", effect="draw"),
        Card("固有:連撃・双刃", "attack", 25, "check_pair"),
        Card("固有:毒液のナイフ", "status", 10, "check_pair", effect="poison", duration=3),
        Card("固有:三枚・強撃", "attack", 40, "check_three"),
        Card("固有:Sスト・ブレイク", "attack", 65, "check_small_straight"),
        Card("固有:絶・フルハウス", "attack", 90, "check_full_house"),
        Card("固有:極・ヤッツィー", "attack", 140, "check_yahtzee")
    ]

# --- 初期化 ---
if 'deck' not in st.session_state or st.sidebar.button("♻️ ゲームを再起動"):
    common_deck = []
    for _ in range(15): common_deck.append(Card("追撃・小剣", "attack", 20, "check_pair"))
    for _ in range(12): common_deck.append(Card("強襲・大剣", "attack", 65, "check_three"))
    for _ in range(8):  common_deck.append(Card("アイアン・シールド", "guard", 35, "check_pair"))
    for _ in range(5):  common_deck.append(Card("癒しのハーブ", "heal", 30, "check_pair"))
    for _ in range(5):  common_deck.append(Card("猛毒の粉末", "status", 12, "check_pair", effect="poison", duration=3))
    random.shuffle(common_deck)
    st.session_state.update({
        'deck': common_deck, 
        'p1': {"hp": 150, "hand": [], "bonus": 0, "guard": 0, "innate": get_innate_deck(), "status": []},
        'p2': {"hp": 150, "hand": [], "bonus": 0, "guard": 0, "innate": get_innate_deck(), "status": []},
        'current_player': "P1", 'dice': [random.randint(1, 6) for _ in range(5)],
        'phase': "action", 'reroll_done': False, 'log': ["ゲーム開始！"], 'winner': None, 'pending_action': None
    })

def process_status_effects(player_key):
    p = st.session_state[player_key]
    new_status = []
    for s in p["status"]:
        if s["type"] == "poison":
            p["hp"] -= s["value"]
            st.session_state.log.insert(0, f"⚠️ {player_key}に毒ダメージ {s['value']}")
        s["duration"] -= 1
        if s["duration"] > 0: new_status.append(s)
    p["status"] = new_status

def switch_player():
    # 勝利判定
    if st.session_state.p1["hp"] <= 0:
        st.session_state.winner = "PLAYER 2"
        return
    elif st.session_state.p2["hp"] <= 0:
        st.session_state.winner = "PLAYER 1"
        return
        
    st.session_state.current_player = "P2" if st.session_state.current_player == "P1" else "P1"
    process_status_effects('p1' if st.session_state.current_player == "P1" else 'p2')
    st.session_state.phase = "action"; st.session_state.reroll_done = False
    st.session_state.p1["guard"] = 0; st.session_state.p2["guard"] = 0
    st.session_state.dice = [random.randint(1, 6) for _ in range(5)]
    st.session_state.pending_action = None

# --- UI構築 ---
st.title("⚔️ YAHTZEE TACTICS ⚔️")

# 勝利時の表示
if st.session_state.winner:
    st.balloons()
    st.header(f"🏆 {st.session_state.winner} の勝利！")
    if st.button("もう一度遊ぶ", use_container_width=True):
        del st.session_state['deck']; st.rerun()
    st.stop()

# プレイヤー情報表示エリア
col_p1, col_p2 = st.columns(2)
for i, (col, key) in enumerate(zip([col_p1, col_p2], ["p1", "p2"])):
    p = st.session_state[key]
    with col:
        is_active = " (ターン中)" if st.session_state.current_player == f"P{i+1}" else ""
        st.subheader(f"PLAYER {i+1}{is_active}")
        st.metric("HP", f"{max(0, p['hp'])} / 150")
        st.write(f"🛡️ 防御力: {p['guard']}")
        if p["status"]:
            for s in p["status"]:
                st.markdown(f":violet[⚠️ 毒状態: {s['value']}ダメ (残り{s['duration']}T)]")

st.divider()

# フェーズ：移動
if st.session_state.phase == "action":
    st.header(f"👉 {st.session_state.current_player} の番です")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎴 カードを1枚引いて交代", use_container_width=True):
            if st.session_state.deck and len(st.session_state[st.session_state.current_player.lower()]["hand"]) < 5:
                st.session_state[st.session_state.current_player.lower()]["hand"].append(st.session_state.deck.pop())
                switch_player(); st.rerun()
    with c2:
        if st.button("⚔️ 攻撃を開始する", use_container_width=True, type="primary"):
            st.session_state.phase = "battle"; st.rerun()

# フェーズ：バトル
elif st.session_state.phase == "battle":
    p_now = st.session_state.p1 if st.session_state.current_player == "P1" else st.session_state.p2
    p_opp = st.session_state.p2 if st.session_state.current_player == "P1" else st.session_state.p1
    
    # ダイス
    cols = st.columns(5)
    for i, d in enumerate(st.session_state.dice):
        cols[i].markdown(f"# {DICE_ICONS[d]}")
    
    if not st.session_state.reroll_done:
        if st.button("🎲 ダイスを振り直す (1回のみ)", use_container_width=True):
            st.session_state.dice = [random.randint(1, 6) for _ in range(5)]
            st.session_state.reroll_done = True; st.rerun()

    # カード判定
    st.write("---")
    all_cards = []
    for c in p_now["innate"] + p_now["hand"]:
        reason = get_reason_text(st.session_state.dice, c.condition_name)
        if reason:
            source = "固有" if c in p_now["innate"] else "手札"
            all_cards.append((c, reason, source))

    if not all_cards:
        st.warning("出せる役がありません。")
        if st.button("ターン終了"): switch_player(); st.rerun()
    else:
        st.write("### 使うカードを選んでください")
        for idx, (card, reason, source) in enumerate(all_cards):
            c_col1, c_col2 = st.columns([3, 1])
            with c_col1:
                if card.type == "attack":
                    val = max(0, card.value - p_opp["guard"])
                    st.markdown(f"**{source}: {card.name}** ({reason}) -> :red[予測ダメ: {val}]")
                elif card.type == "status":
                    st.markdown(f"**{source}: {card.name}** ({reason}) -> :violet[毒付与: {card.value}]")
                else:
                    st.markdown(f"**{source}: {card.name}** ({reason}) -> :orange[防御力: {card.value}]")
            with c_col2:
                if st.button("使用", key=f"use_{idx}"):
                    if card.type in ["attack", "status"]:
                        st.session_state.pending_action = {"card": card, "source": source}
                        st.session_state.phase = "counter"; st.rerun()
                    else:
                        if card.type == "guard": p_now["guard"] = card.value
                        if source == "固有": p_now["innate"].remove(card)
                        else: p_now["hand"].remove(card)
                        switch_player(); st.rerun()

# フェーズ：カウンター
elif st.session_state.phase == "counter":
    opp_key = "p2" if st.session_state.current_player == "P1" else "p1"
    p_opp = st.session_state[opp_key]
    st.header(f"🛡️ 防御フェーズ (受け手: {opp_key.upper()})")
    
    available_guards = [c for c in p_opp["hand"] if c.type == "guard"]
    # ブラフ：ガードがなくても「防御しない」を選ばせる
    options = ["防御しない"] + [f"{g.name} (軽減:{g.value})" for g in available_guards]
    selected = st.radio("ガードを使いますか？（相手には秘密）", options)

    if st.button("決定", type="primary"):
        action = st.session_state.pending_action
        card = action["card"]
        p_now = st.session_state.p1 if st.session_state.current_player == "P1" else st.session_state.p2
        
        # ガード適用
        g_val = 0
        if selected != "防御しない":
            g_idx = options.index(selected) - 1
            g_card = available_guards[g_idx]
            g_val = g_card.value
            p_opp["hand"].remove(g_card)
        
        # ダメージ
        if card.type == "attack":
            dmg = max(0, card.value - g_val)
            p_opp["hp"] -= dmg
            st.session_state.log.insert(0, f"{dmg}ダメージ！")
        elif card.type == "status":
            p_opp["status"].append({"type": card.effect, "value": card.value, "duration": card.duration})
            st.session_state.log.insert(0, f"状態異常を付与！")

        if action["source"] == "固有": p_now["innate"].remove(card)
        else: p_now["hand"].remove(card)
        switch_player(); st.rerun()

st.write("---")
st.write("📜 ログ:", st.session_state.log[:3])
