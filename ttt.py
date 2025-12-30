import streamlit as st
import random

# --- ページ設定 ---
st.set_page_config(page_title="Yahtzee Tactics Online", layout="wide")

# カスタムCSS：カード風のデザインと色分け
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .player-box { padding: 20px; border-radius: 15px; border: 2px solid #343a40; background-color: #161b22; margin-bottom: 10px; }
    .active-player { border: 2px solid #00ff00 !important; background-color: #0d2a1d !important; }
    .card-weak { padding: 10px; border-radius: 8px; background-color: #2d333b; border-left: 5px solid #8b949e; margin: 5px 0; }
    .card-mid { padding: 10px; border-radius: 8px; background-color: #2d333b; border-left: 5px solid #1f6feb; margin: 5px 0; }
    .card-strong { padding: 10px; border-radius: 8px; background-color: #2d333b; border-left: 5px solid #ab7df8; margin: 5px 0; }
    .card-rare { padding: 10px; border-radius: 8px; background-color: #2d333b; border-left: 5px solid #f8e3a1; margin: 5px 0; }
    .dice-val { font-size: 40px; font-weight: bold; color: #ffeb3b; letter-spacing: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 判定関数ロジック ---
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
        self.name = name
        self.type = ctype
        self.power = power
        self.condition = condition
        self.rarity = rarity
        self.status_effect = status_effect

# --- ゲームデータの初期化 ---
if 'deck' not in st.session_state:
    deck = []
    for _ in range(20): deck.append(Card("ジェミニ・ダガー", "attack", 15, check_pair, "弱"))
    for _ in range(16): deck.append(Card("トライ・ブラスト", "attack", 25, check_three, "中"))
    for _ in range(2):  deck.append(Card("崩壊の紫煙(毒)", "status", 0, check_three, "中", ("poison", 3)))
    for _ in range(10): deck.append(Card("天階の連撃", "attack", 40, check_straight, "強"))
    for _ in range(2):  deck.append(Card("煉獄の業火(炎)", "status", 0, check_straight, "強", ("burn", 2)))
    for _ in range(5):  deck.append(Card("慈悲の祝福", "heal", 30, check_pair, "レア"))
    for _ in range(5):  deck.append(Card("終焉の聖家", "attack", 60, check_full_house, "レア"))
    random.shuffle(deck)
    st.session_state.deck = deck
    st.session_state.p1 = {"hp": 100, "hand": [], "bonus": 0, "statuses": {"poison": 0, "burn": 0}, "used_innate": []}
    st.session_state.p2 = {"hp": 100, "hand": [], "bonus": 0, "statuses": {"poison": 0, "burn": 0}, "used_innate": []}
    st.session_state.current_player = "P1"
    st.session_state.dice = [random.randint(1, 6) for _ in range(5)]
    st.session_state.phase = "action" # action, battle
    st.session_state.reroll_count = 0
    st.session_state.log = ["バトル開始！"]

innate_cards = [
    Card("固有:トリニティ", "attack", 20, check_three, "固有"),
    Card("固有:五連光破斬", "attack", 25, check_straight, "固有"),
    Card("固有:神罰の五連星", "attack", 50, check_yahtzee, "固有")
]

def add_log(msg): st.session_state.log.insert(0, msg)

def switch_player():
    st.session_state.current_player = "P2" if st.session_state.current_player == "P1" else "P1"
    st.session_state.phase = "action"
    st.session_state.reroll_count = 0
    # ターン開始時に毒などのダメージ
    p = st.session_state.p1 if st.session_state.current_player == "P1" else st.session_state.p2
    for s, t in p["statuses"].items():
        if t > 0:
            dmg = 5 if s == "poison" else 10
            p["hp"] -= dmg
            p["statuses"][s] -= 1
            add_log(f"{st.session_state.current_player} は {s} で {dmg} ダメージを受けた")
    st.session_state.dice = [random.randint(1, 6) for _ in range(5)]

# --- メイン画面 ---
st.title("🎲 Yahtzee Tactics")

# プレイヤーエリア
c1, c2 = st.columns(2)
for i, (col, p_key) in enumerate(zip([c1, c2], ["p1", "p2"])):
    p = st.session_state[p_key]
    is_active = st.session_state.current_player == f"P{i+1}"
    with col:
        box_class = "player-box active-player" if is_active else "player-box"
        st.markdown(f"""<div class="{box_class}">
            <h3>PLAYER {i+1} {'(TURN)' if is_active else ''}</h3>
            <h2 style="color: #00ff00;">HP: {p['hp']}</h2>
            <p>⚔️ Bonus: +{p['bonus']} | ⚠️ Status: {', '.join([f'{k}({v})' for k,v in p['statuses'].items() if v>0]) or 'Normal'}</p>
            </div>""", unsafe_allow_html=True)

st.divider()

# 現在のプレイヤー
p_now = st.session_state.p1 if st.session_state.current_player == "P1" else st.session_state.p2
p_opp = st.session_state.p2 if st.session_state.current_player == "P1" else st.session_state.p1

if p_now["hp"] <= 0:
    st.error(f"💀 {st.session_state.current_player} は敗退しました")
    if st.button("リセット"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
    st.stop()

# ダイスと操作エリア
st.markdown(f'<div class="dice-val">{" ".join([f"[{d}]" for d in st.session_state.dice])}</div>', unsafe_allow_html=True)

if st.session_state.phase == "action":
    st.info("💡 アクションを選択してください")
    cols = st.columns(3)
    if len(p_now["hand"]) < 5:
        if cols[0].button("🎴 カードをドローして終了", use_container_width=True):
            if st.session_state.deck:
                card = st.session_state.deck.pop()
                p_now["hand"].append(card)
                add_log(f"{st.session_state.current_player} が {card.name} を引いた")
                switch_player()
                st.rerun()
    
    if cols[1].button("⚔️ 攻撃フェーズへ", use_container_width=True):
        st.session_state.phase = "battle"
        st.rerun()

elif st.session_state.phase == "battle":
    st.warning("⚔️ 技を選択してください（1度だけ振り直し可能）")
    
    # 振り直しボタン
    if st.session_state.reroll_count == 0:
        if st.button("🎲 一度だけ振り直す", type="primary"):
            st.session_state.dice = [random.randint(1, 6) for _ in range(5)]
            st.session_state.reroll_count = 1
            add_log(f"{st.session_state.current_player} がダイスを振り直した")
            st.rerun()
    
    # カードリストの表示と選択
    pool = [c for c in innate_cards if c.name not in p_now["used_innate"]] + p_now["hand"]
    available = [c for c in pool if c.condition(st.session_state.dice)]

    if not available:
        st.error("揃っている役がありません！")
        if p_now["hand"]:
            discard_idx = st.selectbox("廃棄するカードを選択:", range(len(p_now["hand"])), format_func=lambda x: p_now["hand"][x].name)
            if st.button("🗑️ 廃棄して交代"):
                c = p_now["hand"].pop(discard_idx)
                add_log(f"{st.session_state.current_player} は役が揃わず {c.name} を捨てた")
                switch_player()
                st.rerun()
        elif st.button("ターンをパスする"):
            switch_player()
            st.rerun()
    else:
        # カードの見た目を整理
        selected_idx = st.radio("発動する技を選んでください:", range(len(available)), 
                               format_func=lambda x: f"{available[x].name} ({available[x].rarity}) - 威力:{available[x].power}")
        
        if st.button("🔥 技を発動！", use_container_width=True):
            card = available[selected_idx]
            if card.type == "attack":
                dmg = card.power + p_now["bonus"]
                p_opp["hp"] -= dmg
                add_log(f"{card.name} 発動！ {dmg}ダメージ！")
            elif card.type == "heal":
                p_now["hp"] += card.power
                add_log(f"{card.name} 発動！ {card.power}回復！")
            elif card.type == "status":
                s_name, s_turn = card.status_effect
                p_opp["statuses"][s_name] = s_turn
                add_log(f"{card.name} 発動！ 相手を{s_name}状態にした")

            # 消費処理
            found = False
            for i, h_card in enumerate(p_now["hand"]):
                if h_card is card:
                    p_now["hand"].pop(i)
                    found = True; break
            if not found:
                p_now["used_innate"].append(card.name)
                if len(p_now["used_innate"]) == 3:
                    p_now["used_innate"] = []; p_now["bonus"] += 10
                    add_log("🌟 固有技を使い切り、覚醒した！")
            
            switch_player()
            st.rerun()

# ログと所持カード
st.divider()
la, lb = st.columns([1, 1])
with la:
    st.write("### 📜 バトルログ")
    for l in st.session_state.log[:5]:
        st.write(f"- {l}")
with lb:
    st.write("### 🎴 現在の手札")
    for c in p_now["hand"]:
        color = {"弱":"#8b949e", "中":"#1f6feb", "強":"#ab7df8", "レア":"#f8e3a1"}.get(c.rarity, "#ffffff")
        st.markdown(f'<div style="border-left: 5px solid {color}; padding-left: 10px;">{c.name} ({c.rarity})</div>', unsafe_allow_html=True)
