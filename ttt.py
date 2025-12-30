import streamlit as st
import random

# --- ページ設定 ---
st.set_page_config(page_title="Yahtzee Battle Online", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1e2130; border-radius: 10px; padding: 10px; border: 1px solid #4B4B4B; }
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

# --- カードクラス ---
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
    for i in range(20): deck.append(Card("ジェミニ・ダガー", "attack", 15, check_pair, "弱"))
    for i in range(16): deck.append(Card("トライ・ブラスト", "attack", 25, check_three, "中"))
    for i in range(2):  deck.append(Card("崩壊の紫煙(毒)", "status", 0, check_three, "中", ("poison", 3)))
    for i in range(10): deck.append(Card("天階の連撃", "attack", 40, check_straight, "強"))
    for i in range(2):  deck.append(Card("煉獄の業火(炎)", "status", 0, check_straight, "強", ("burn", 2)))
    for i in range(5):  deck.append(Card("慈悲の祝福", "heal", 30, check_pair, "レア"))
    for i in range(5):  deck.append(Card("終焉の聖家", "attack", 60, check_full_house, "レア"))
    random.shuffle(deck)
    st.session_state.deck = deck
    st.session_state.p1 = {"hp": 100, "hand": [], "bonus": 0, "statuses": {"poison": 0, "burn": 0}, "used_innate": []}
    st.session_state.p2 = {"hp": 100, "hand": [], "bonus": 0, "statuses": {"poison": 0, "burn": 0}, "used_innate": []}
    st.session_state.turn = 1
    st.session_state.current_player = "P1"
    st.session_state.dice = [1, 1, 1, 1, 1]
    st.session_state.phase = "start"
    st.session_state.rerolled = False  # 振り直しフラグを初期化
    st.session_state.log = ["ゲーム開始！"]

# 固有技
innate_cards = [
    Card("固有:トリニティ・インパクト", "attack", 20, check_three, "固有"),
    Card("固有:五連光破斬", "attack", 25, check_straight, "固有"),
    Card("固有:神罰の五連星", "attack", 50, check_yahtzee, "固有")
]

def add_log(msg):
    st.session_state.log.insert(0, msg)

def switch_player():
    st.session_state.current_player = "P2" if st.session_state.current_player == "P1" else "P1"
    st.session_state.phase = "start"
    st.session_state.rerolled = False  # 交代時にフラグをリセット
    st.session_state.turn += 1

# --- UI表示 ---
st.title("🎲 Yahtzee Battle Tactics")

col1, col2 = st.columns(2)
for i, p_key in enumerate(["p1", "p2"]):
    p = st.session_state[p_key]
    with (col1 if i == 0 else col2):
        player_title = f"👤 PLAYER {i+1}"
        if st.session_state.current_player == f"P{i+1}":
            st.success(f"**{player_title} (手番)**")
        else:
            st.subheader(player_title)
        
        st.metric(label="HP", value=f"{p['hp']} / 100", delta=None)
        st.write(f"⚔️ Bonus: +{p['bonus']}")
        status_str = ", ".join([f"{k}({v}T)" for k, v in p["statuses"].items() if v > 0])
        st.write(f"⚠️ 状態: {status_str if status_str else 'なし'}")

st.divider()

p_now = st.session_state.p1 if st.session_state.current_player == "P1" else st.session_state.p2
p_opp = st.session_state.p2 if st.session_state.current_player == "P1" else st.session_state.p1

if p_now["hp"] <= 0:
    st.error(f"💀 {st.session_state.current_player} は敗北した！")
    if st.button("リセットして再戦"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()
    st.stop()

if st.session_state.phase == "start":
    for s, t in p_now["statuses"].items():
        if t > 0:
            dmg = 5 if s == "poison" else 10
            p_now["hp"] -= dmg
            p_now["statuses"][s] -= 1
            add_log(f"{st.session_state.current_player} は {s} で {dmg} ダメージを受けた")
    st.session_state.dice = [random.randint(1, 6) for _ in range(5)]
    st.session_state.phase = "action"

st.write(f"### 🎲 ダイス: {' '.join([f'[{d}]' for d in st.session_state.dice])}")

if st.session_state.phase == "action":
    c1, c2 = st.columns(2)
    if len(p_now["hand"]) < 5:
        if c1.button("カードをドローして終了"):
            if st.session_state.deck:
                new_c = st.session_state.deck.pop()
                p_now["hand"].append(new_c)
                add_log(f"{st.session_state.current_player} がドローした")
                switch_player()
                st.rerun()
    if c2.button("攻撃フェーズへ"):
        st.session_state.phase = "battle"
        st.rerun()

elif st.session_state.phase == "battle":
    # 振り直しボタンの制御
    if not st.session_state.rerolled:
        if st.button("一度だけ振り直す"):
            st.session_state.dice = [random.randint(1, 6) for _ in range(5)]
            st.session_state.rerolled = True  # ここでフラグを立てる
            add_log("ダイスを振り直した")
            st.rerun()
    else:
        st.info("⚠️ 振り直し済みです。")

    pool = [c for c in innate_cards if c.name not in p_now["used_innate"]] + p_now["hand"]
    available = [c for c in pool if c.condition(st.session_state.dice)]

    if not available:
        st.error("役が揃いませんでした！")
        if p_now["hand"]:
            discard_idx = st.selectbox("手札を1枚選んで廃棄:", range(len(p_now["hand"])), format_func=lambda x: p_now["hand"][x].name)
            if st.button("廃棄して終了"):
                card = p_now["hand"].pop(discard_idx)
                add_log(f"{card.name} を捨てた")
                switch_player()
                st.rerun()
        else:
            if st.button("パスして終了"):
                switch_player()
                st.rerun()
    else:
        selected_idx = st.radio("使用するカードを選択:", range(len(available)), format_func=lambda x: f"{available[x].name} ({available[x].rarity}) - 威力:{available[x].power}")
        if st.button("発動！"):
            selected_card = available[selected_idx]
            if selected_card.type == "attack":
                dmg = selected_card.power + p_now["bonus"]
                p_opp["hp"] -= dmg
                add_log(f"{selected_card.name}！ {dmg}ダメージ！")
            elif selected_card.type == "heal":
                p_now["hp"] += selected_card.power
                add_log(f"{selected_card.name}！ {selected_card.power}回復！")
            elif selected_card.type == "status":
                s_name, s_turn = selected_card.status_effect
                p_opp["statuses"][s_name] = s_turn
                add_log(f"{selected_card.name}！ 相手を{s_name}にした")

            found_in_hand = False
            for i, c in enumerate(p_now["hand"]):
                if c is selected_card:
                    p_now["hand"].pop(i)
                    found_in_hand = True
                    break
            if not found_in_hand:
                p_now["used_innate"].append(selected_card.name)
                if len(p_now["used_innate"]) == 3:
                    p_now["used_innate"] = []
                    p_now["bonus"] += 10
                    add_log("★覚醒！ボーナス+10！")

            switch_player()
            st.rerun()

st.divider()
st.write("### 📜 バトルログ")
for l in st.session_state.log[:10]:
    st.write(l)
