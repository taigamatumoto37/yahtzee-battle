import streamlit as st
import random

# --- ページ設定 ---
st.set_page_config(page_title="Yahtzee Tactics: Awakening & Reset", layout="wide")

# CSS: UI装飾
st.markdown("""
    <style>
    .stApp { background-color: #1a1c23; color: #ffffff; }
    .player-box { padding: 20px; border-radius: 15px; border: 2px solid #343a40; background-color: #242933; margin-bottom: 10px; }
    .active-player { border: 2px solid #4CAF50 !important; background-color: #2e3b2e !important; box-shadow: 0 0 15px rgba(76, 175, 80, 0.4); }
    .dice-container { display: flex; justify-content: center; gap: 15px; margin: 25px 0; }
    .dice-icon { 
        font-size: 70px; background: white; color: #333; width: 90px; height: 90px; 
        display: flex; align-items: center; justify-content: center; border-radius: 15px; 
        box-shadow: 4px 4px 0px #888, 0 10px 20px rgba(0,0,0,0.5); border: 2px solid #ddd;
    }
    </style>
    """, unsafe_allow_html=True)

DICE_ICONS = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

# --- 判定関数 ---
def check_pair(d): return any(d.count(x) >= 2 for x in set(d))
def check_three(d): return any(d.count(x) >= 3 for x in set(d))
def check_small_straight(d): 
    s = sorted(list(set(d)))
    for i in range(len(s)-3):
        if s[i+3] - s[i] == 3: return True
    return False
def check_full_house(d): 
    counts = [d.count(x) for x in set(d)]
    return 3 in counts and 2 in counts
def check_yahtzee(d): return len(set(d)) == 1

def get_satisfied_condition(d, condition_func):
    if condition_func == check_pair: return "ワンペア" if check_pair(d) else None
    if condition_func == check_three: return "スリーカード" if check_three(d) else None
    if condition_func == check_small_straight: return "Sストレート" if check_small_straight(d) else None
    if condition_func == check_full_house: return "フルハウス" if check_full_house(d) else None
    if condition_func == check_yahtzee: return "ヤッツィー" if check_yahtzee(d) else None
    return None

class Card:
    def __init__(self, name, ctype, value, condition, effect=None):
        self.name, self.type, self.value, self.condition, self.effect = name, ctype, value, condition, effect

# --- 固有カード8枚（攻撃特化）の定義 ---
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

# --- ゲーム初期化 ---
if 'deck' not in st.session_state:
    common_deck = []
    for _ in range(10): common_deck.append(Card("アイアン・シールド", "guard", 20, check_pair))
    for _ in range(5):  common_deck.append(Card("クリスタル・ガード", "guard", 40, check_three))
    for _ in range(10): common_deck.append(Card("癒しのハーブ", "heal", 20, check_pair))
    for _ in range(5):  common_deck.append(Card("強襲・グレートソード", "attack", 50, check_three))
    random.shuffle(common_deck)

    st.session_state.update({
        'deck': common_deck, 
        'p1': {"hp": 150, "hand": [], "bonus": 0, "guard_value": 0, "innate": get_innate_deck()},
        'p2': {"hp": 150, "hand": [], "bonus": 0, "guard_value": 0, "innate": get_innate_deck()},
        'current_player': "P1", 'dice': [random.randint(1, 6) for _ in range(5)],
        'phase': "action", 'reroll_done': False, 'log': ["バトル開始！"]
    })

def add_log(msg): st.session_state.log.insert(0, msg)

def switch_player():
    st.session_state.current_player = "P2" if st.session_state.current_player == "P1" else "P1"
    st.session_state.phase = "action"
    st.session_state.reroll_done = False
    st.session_state.p1["guard_value"] = 0
    st.session_state.p2["guard_value"] = 0
    st.session_state.dice = [random.randint(1, 6) for _ in range(5)]

# --- UI ---
st.title("🎲 Yahtzee Tactics: Awakening & Reset")

c1, c2 = st.columns(2)
for i, (col, p_key) in enumerate(zip([c1, c2], ["p1", "p2"])):
    p = st.session_state[p_key]
    is_active = st.session_state.current_player == f"P{i+1}"
    with col:
        st.markdown(f"""
            <div class="player-box {'active-player' if is_active else ''}">
                <h3>PLAYER {i+1}</h3>
                <h2 style="color: #4CAF50;">HP: {p['hp']}</h2>
                <p>Bonus: +{p['bonus']} | 固有技残り: {len(p['innate'])}/8</p>
            </div>
        """, unsafe_allow_html=True)

st.divider()
p_now = st.session_state.p1 if st.session_state.current_player == "P1" else st.session_state.p2
p_opp = st.session_state.p2 if st.session_state.current_player == "P1" else st.session_state.p1

dice_html = "".join([f'<div class="dice-icon">{DICE_ICONS[d]}</div>' for d in st.session_state.dice])
st.markdown(f'<div class="dice-container">{dice_html}</div>', unsafe_allow_html=True)

if st.session_state.phase == "action":
    cols = st.columns(2)
    if cols[0].button("🎴 山札から引いて終了", use_container_width=True):
        if st.session_state.deck: p_now["hand"].append(st.session_state.deck.pop())
        add_log(f"{st.session_state.current_player}がドロー")
        switch_player(); st.rerun()
    if cols[1].button("⚔️ バトルフェーズへ", use_container_width=True):
        st.session_state.phase = "battle"; st.rerun()

elif st.session_state.phase == "battle":
    if not st.session_state.reroll_done:
        if st.button("🎲 ダイスを一度だけ振り直す", type="primary", use_container_width=True):
            st.session_state.dice = [random.randint(1, 6) for _ in range(5)]
            st.session_state.reroll_done = True; st.rerun()

    pool = p_now["innate"] + p_now["hand"]
    available = []
    for c in pool:
        reason = get_satisfied_condition(st.session_state.dice, c.condition)
        if reason: available.append((c, reason))

    if not available:
        st.warning("出せるカードがありません。")
        if st.button("ターン終了"): switch_player(); st.rerun()
    else:
        selected_idx = st.radio("カード選択:", range(len(available)), 
                               format_func=lambda x: f"[{available[x][0].type.upper()}] {available[x][0].name} ({available[x][1]})")
        
        if st.button("🔥 発動！", use_container_width=True):
            card, reason = available[selected_idx]
            
            # 効果処理
            if card.type == "attack":
                dmg = max(0, (card.value + p_now["bonus"]) - p_opp["guard_value"])
                p_opp["hp"] -= dmg
                msg = f"{card.name}！ {dmg}ダメージ！"
                if card.effect == "draw" and st.session_state.deck:
                    p_now["hand"].append(st.session_state.deck.pop())
                    msg += "（追加ドロー！）"
                add_log(msg)
            elif card.type == "guard":
                p_now["guard_value"] = card.value
                add_log(f"{card.name}！ ガード値{card.value}展開")
            elif card.type == "heal":
                p_now["hp"] += card.value
                add_log(f"{card.name}！ {card.value}回復")

            # 【重要】消費とリセット（復活）のロジック
            if card in p_now["innate"]:
                p_now["innate"].remove(card)
                # すべて使い切ったら復活！
                if len(p_now["innate"]) == 0:
                    p_now["bonus"] += 10
                    p_now["innate"] = get_innate_deck() # 固有カードを再セット
                    add_log("🌟 覚醒！固有技が全て復活し、Bonus+10！")
            else:
                p_now["hand"].remove(card)
            
            switch_player(); st.rerun()

st.divider()
st.write("### 📜 ログ")
for l in st.session_state.log[:5]: st.write(f"- {l}")
