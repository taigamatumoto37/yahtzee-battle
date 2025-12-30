import streamlit as st
import random

# --- ページ設定 ---
st.set_page_config(page_title="Yahtzee Tactics Online", layout="wide")

# 【ダイスの見た目をカスタマイズするCSS】
st.markdown("""
    <style>
    .stApp { background-color: #1a1c23; color: #ffffff; }
    
    /* プレイヤー情報エリア */
    .player-box { padding: 20px; border-radius: 15px; border: 2px solid #343a40; background-color: #242933; margin-bottom: 10px; }
    .active-player { border: 2px solid #4CAF50 !important; background-color: #2e3b2e !important; box-shadow: 0 0 15px rgba(76, 175, 80, 0.4); }
    
    /* ダイスコンテナ */
    .dice-container { 
        display: flex; 
        justify-content: center; 
        gap: 15px; 
        margin: 30px 0; 
    }
    
    /* ダイス1個の見た目（ここをいじると色や形が変わります） */
    .dice-icon { 
        font-size: 80px;      /* サイコロの大きさ */
        background: #ffffff;  /* サイコロの色 */
        color: #333333;       /* 目の色 */
        width: 100px; 
        height: 100px; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        border-radius: 18px;  /* 角の丸み */
        box-shadow: 4px 4px 0px #888, 0 10px 20px rgba(0,0,0,0.5); /* 3D風の影 */
        border: 2px solid #dddddd;
        transition: transform 0.2s;
    }
    .dice-icon:hover { transform: scale(1.1); } /* マウスを乗せると少し大きく */
    </style>
    """, unsafe_allow_html=True)

# ダイス数値に対応するUnicode文字
DICE_ICONS = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

# --- 判定関数（役名付き） ---
def get_satisfied_condition(d, condition_func):
    if condition_func == check_pair and check_pair(d): return "ワンペア以上"
    if condition_func == check_three and check_three(d): return "スリーカード"
    if condition_func == check_straight and check_straight(d): return "ストレート"
    if condition_func == check_full_house and check_full_house(d): return "フルハウス"
    if condition_func == check_yahtzee and check_yahtzee(d): return "ヤッツィー(ALL)"
    return None

def check_pair(d): return any(d.count(x) >= 2 for x in set(d))
def check_three(d): return any(d.count(x) >= 3 for x in set(d))
def check_straight(d): 
    s = sorted(list(set(d)))
    return any(s[i:i+5] == list(range(s[i], s[i]+5)) for i in range(len(s)-4))
def check_full_house(d): 
    counts = [d.count(x) for x in set(d)]
    return 3 in counts and 2 in counts
def check_yahtzee(d): return len(set(d)) == 1

class Card:
    def __init__(self, name, ctype, power, condition, rarity, status_effect=None):
        self.name, self.type, self.power, self.condition, self.rarity, self.status_effect = name, ctype, power, condition, rarity, status_effect

# --- ゲーム初期化 ---
if 'deck' not in st.session_state:
    deck = []
    # カード追加（新カード含む）
    for _ in range(15): deck.append(Card("ジェミニ・ダガー", "attack", 15, check_pair, "弱"))
    for _ in range(10): deck.append(Card("トライ・ブラスト", "attack", 25, check_three, "中"))
    for _ in range(8):  deck.append(Card("天階の連撃", "attack", 40, check_straight, "強"))
    for _ in range(4):  deck.append(Card("終焉の聖家", "attack", 60, check_full_house, "レア"))
    for _ in range(3):  deck.append(Card("崩壊の紫煙(毒)", "status", 0, check_three, "中", ("poison", 3)))
    for _ in range(3):  deck.append(Card("煉獄の業火(炎)", "status", 0, check_straight, "強", ("burn", 2)))
    for _ in range(5):  deck.append(Card("慈悲の祝福", "heal", 30, check_pair, "レア"))
    for _ in range(3):  deck.append(Card("フルカウンター", "attack", 35, check_straight, "強"))
    for _ in range(2):  deck.append(Card("ライトニング・ノヴァ", "attack", 85, check_yahtzee, "超レア"))
    for _ in range(4):  deck.append(Card("運命のダイス", "heal", 20, check_three, "中")) 
    for _ in range(3):  deck.append(Card("スフィア・シールド", "heal", 45, check_full_house, "レア"))

    random.shuffle(deck)
    st.session_state.update({
        'deck': deck, 'p1': {"hp": 100, "hand": [], "bonus": 0, "statuses": {"poison": 0, "burn": 0}, "used_innate": []},
        'p2': {"hp": 100, "hand": [], "bonus": 0, "statuses": {"poison": 0, "burn": 0}, "used_innate": []},
        'current_player': "P1", 'dice': [random.randint(1, 6) for _ in range(5)],
        'phase': "action", 'reroll_done': False, 'log': ["バトル開始！"]
    })

innate_cards = [
    Card("固有:トリニティ", "attack", 20, check_three, "固有"), 
    Card("固有:五連光破斬", "attack", 25, check_straight, "固有"), 
    Card("固有:神罰の五連星", "attack", 50, check_yahtzee, "固有")
]

def add_log(msg): st.session_state.log.insert(0, msg)

def switch_player():
    st.session_state.current_player = "P2" if st.session_state.current_player == "P1" else "P1"
    st.session_state.phase = "action"
    st.session_state.reroll_done = False
    p = st.session_state.p1 if st.session_state.current_player == "P1" else st.session_state.p2
    for s, t in p["statuses"].items():
        if t > 0:
            dmg = 5 if s == "poison" else 10
            p["hp"] -= dmg
            p["statuses"][s] -= 1
            add_log(f"{st.session_state.current_player} は {s} で {dmg} ダメージを受けた")
    st.session_state.dice = [random.randint(1, 6) for _ in range(5)]

# --- UI ---
st.title("🎲 Yahtzee Tactics Online")
c1, c2 = st.columns(2)
for i, (col, p_key) in enumerate(zip([c1, c2], ["p1", "p2"])):
    p = st.session_state[p_key]
    is_active = st.session_state.current_player == f"P{i+1}"
    with col:
        st.markdown(f'<div class="player-box {"active-player" if is_active else ""}"><h3>PLAYER {i+1} {"(TURN)" if is_active else ""}</h3><h2 style="color: #4CAF50;">HP: {p["hp"]}</h2><p>⚔️ Bonus: +{p["bonus"]} | ⚠️ Status: {", ".join([f"{k}({v})" for k,v in p["statuses"].items() if v>0]) or "Normal"}</p></div>', unsafe_allow_html=True)

st.divider()
p_now = st.session_state.p1 if st.session_state.current_player == "P1" else st.session_state.p2
p_opp = st.session_state.p2 if st.session_state.current_player == "P1" else st.session_state.p1

# ダイス表示エリア
dice_html = "".join([f'<div class="dice-icon">{DICE_ICONS[d]}</div>' for d in st.session_state.dice])
st.markdown(f'<div class="dice-container">{dice_html}</div>', unsafe_allow_html=True)

# --- ロジック ---
if st.session_state.phase == "action":
    cols = st.columns(2)
    if len(p_now["hand"]) < 5:
        if cols[0].button("🎴 カードをドローして終了", use_container_width=True):
            if st.session_state.deck:
                card = st.session_state.deck.pop()
                p_now["hand"].append(card)
                add_log(f"{st.session_state.current_player} ドロー")
                switch_player()
                st.rerun()
    if cols[1].button("⚔️ 攻撃フェーズへ", use_container_width=True):
        st.session_state.phase = "battle"
        st.rerun()

elif st.session_state.phase == "battle":
    if not st.session_state.reroll_done:
        if st.button("🎲 一度だけ振り直す", type="primary", use_container_width=True):
            st.session_state.dice = [random.randint(1, 6) for _ in range(5)]
            st.session_state.reroll_done = True
            add_log(f"ダイスを振り直した")
            st.rerun()

    pool = [c for c in innate_cards if c.name not in p_now["used_innate"]] + p_now["hand"]
    available_with_reason = []
    for c in pool:
        reason = get_satisfied_condition(st.session_state.dice, c.condition)
        if reason: available_with_reason.append((c, reason))

    if not available_with_reason:
        st.error("役が揃いませんでした！")
        if len(p_now["hand"]) < 5:
            if st.button("🎴 代わりにカードをドローして終了", use_container_width=True):
                if st.session_state.deck:
                    card = st.session_state.deck.pop()
                    p_now["hand"].append(card)
                    add_log(f"役不足のためドロー")
                    switch_player()
                    st.rerun()
        if p_now["hand"]:
            discard_idx = st.selectbox("廃棄するカード:", range(len(p_now["hand"])), format_func=lambda x: p_now["hand"][x].name)
            if st.button("🗑️ 廃棄して交代"):
                p_now["hand"].pop(discard_idx)
                switch_player(); st.rerun()
    else:
        selected_idx = st.radio("技を選択:", range(len(available_with_reason)), 
                               format_func=lambda x: f"{available_with_reason[x][0].name} 【{available_with_reason[x][1]}】 (威力:{available_with_reason[x][0].power})")
        if st.button("🔥 発動！", use_container_width=True):
            card, reason = available_with_reason[selected_idx]
            if card.type == "attack": p_opp["hp"] -= (card.power + p_now["bonus"])
            elif card.type == "heal": p_now["hp"] += card.power
            elif card.type == "status": 
                s_name, s_turn = card.status_effect
                p_opp["statuses"][s_name] = s_turn
            add_log(f"{card.name}({reason}) 発動")
            found = False
            for i, h_card in enumerate(p_now["hand"]):
                if h_card is card: p_now["hand"].pop(i); found = True; break
            if not found: p_now["used_innate"].append(card.name)
            switch_player(); st.rerun()

st.divider()
la, lb = st.columns(2)
with la:
    st.write("### 📜 ログ")
    for l in st.session_state.log[:5]: st.write(f"- {l}")
with lb:
    st.write("### 🎴 手札")
    for c in p_now["hand"]: st.markdown(f"- {c.name} ({c.rarity})")
