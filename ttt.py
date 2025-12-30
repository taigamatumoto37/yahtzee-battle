import streamlit as st
import random

# --- ページ設定 ---
st.set_page_config(page_title="Yahtzee Tactics Online", layout="wide")

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

# --- 判定関数（条件ありのみに限定） ---
def check_sum_high(d): return sum(d) >= 20 # 合計20以上（高め）
def check_sum_low(d): return sum(d) <= 10  # 合計10以下（低め）
def check_all_even(d): return all(x % 2 == 0 for x in d) # 全て偶数
def check_all_odd(d): return all(x % 2 != 0 for x in d)  # 全て奇数
def check_small_straight(d): # 4連続（1-2-3-4など）
    s = sorted(list(set(d)))
    for i in range(len(s)-3):
        if s[i+3] - s[i] == 3: return True
    return False
def check_pair(d): return any(d.count(x) >= 2 for x in set(d))
def check_three(d): return any(d.count(x) >= 3 for x in set(d))
def check_full_house(d): 
    counts = [d.count(x) for x in set(d)]
    return 3 in counts and 2 in counts
def check_yahtzee(d): return len(set(d)) == 1

# 役名表示
def get_satisfied_condition(d, condition_func):
    if condition_func == check_sum_high and check_sum_high(d): return "合計20以上"
    if condition_func == check_sum_low and check_sum_low(d): return "合計10以下"
    if condition_func == check_all_even and check_all_even(d): return "オール偶数"
    if condition_func == check_all_odd and check_all_odd(d): return "オール奇数"
    if condition_func == check_small_straight and check_small_straight(d): return "Sストレート(4枚)"
    if condition_func == check_pair and check_pair(d): return "ワンペア"
    if condition_func == check_three and check_three(d): return "スリーカード"
    if condition_func == check_full_house and check_full_house(d): return "フルハウス"
    if condition_func == check_yahtzee and check_yahtzee(d): return "ヤッツィー"
    return None

class Card:
    def __init__(self, name, ctype, power, condition, rarity, status_effect=None):
        self.name, self.type, self.power, self.condition, self.rarity, self.status_effect = name, ctype, power, condition, rarity, status_effect

# --- ゲーム初期化 ---
if 'deck' not in st.session_state:
    deck = []
    # 【初級】合計値・偶数奇数
    for _ in range(12): deck.append(Card("ヘヴィ・インパクト", "attack", 25, check_sum_high, "初級"))
    for _ in range(12): deck.append(Card("アンダー・スナイプ", "attack", 25, check_sum_low, "初級"))
    for _ in range(8):  deck.append(Card("エレキ・偶数波", "attack", 30, check_all_even, "中級"))
    for _ in range(8):  deck.append(Card("バーン・奇数炎", "attack", 30, check_all_odd, "中級"))
    
    # 【中級】ペア・4連続
    for _ in range(15): deck.append(Card("ダブル・ブレード", "attack", 35, check_pair, "中級"))
    for _ in range(8):  deck.append(Card("流転の連撃", "attack", 40, check_small_straight, "中級"))
    for _ in range(6):  deck.append(Card("快癒の祈り", "heal", 40, check_pair, "レア"))
    
    # 【上級】役系
    for _ in range(6):  deck.append(Card("トライ・ブラスト", "attack", 50, check_three, "上級"))
    for _ in range(4):  deck.append(Card("神聖なる家園", "attack", 80, check_full_house, "レア"))
    for _ in range(2):  deck.append(Card("天罰・神の雷", "attack", 120, check_yahtzee, "レジェンド"))

    random.shuffle(deck)
    st.session_state.update({
        'deck': deck, 'p1': {"hp": 150, "hand": [], "bonus": 0, "statuses": {"poison": 0, "burn": 0}, "used_innate": []},
        'p2': {"hp": 150, "hand": [], "bonus": 0, "statuses": {"poison": 0, "burn": 0}, "used_innate": []},
        'current_player': "P1", 'dice': [random.randint(1, 6) for _ in range(5)],
        'phase': "action", 'reroll_done': False, 'log': ["真剣勝負開始！"]
    })

# 固有技
innate_cards = [
    Card("固有:パワーストライク", "attack", 30, check_sum_high, "固有"), 
    Card("固有:トリプルアクセル", "attack", 45, check_three, "固有"), 
    Card("固有:終焉の刻", "attack", 90, check_yahtzee, "固有")
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
            add_log(f"{st.session_state.current_player}は{s}で{dmg}ダメ")
    st.session_state.dice = [random.randint(1, 6) for _ in range(5)]

# --- UI ---
st.title("🎲 Yahtzee Tactics: Professional")
c1, c2 = st.columns(2)
for i, (col, p_key) in enumerate(zip([c1, c2], ["p1", "p2"])):
    p = st.session_state[p_key]
    is_active = st.session_state.current_player == f"P{i+1}"
    with col:
        st.markdown(f'<div class="player-box {"active-player" if is_active else ""}"><h3>PLAYER {i+1}</h3><h2 style="color: #4CAF50;">HP: {p["hp"]}</h2><p>Bonus: +{p["bonus"]}</p></div>', unsafe_allow_html=True)

st.divider()
p_now = st.session_state.p1 if st.session_state.current_player == "P1" else st.session_state.p2
p_opp = st.session_state.p2 if st.session_state.current_player == "P1" else st.session_state.p1

# ダイス
dice_html = "".join([f'<div class="dice-icon">{DICE_ICONS[d]}</div>' for d in st.session_state.dice])
st.markdown(f'<div class="dice-container">{dice_html}</div>', unsafe_allow_html=True)

if st.session_state.phase == "action":
    cols = st.columns(2)
    if len(p_now["hand"]) < 5:
        if cols[0].button("🎴 カードを引いて交代", use_container_width=True):
            if st.session_state.deck:
                p_now["hand"].append(st.session_state.deck.pop())
                add_log(f"{st.session_state.current_player}がドロー")
                switch_player(); st.rerun()
    if cols[1].button("⚔️ 攻撃フェーズへ", use_container_width=True):
        st.session_state.phase = "battle"; st.rerun()

elif st.session_state.phase == "battle":
    if not st.session_state.reroll_done:
        if st.button("🎲 1度だけ振り直す", type="primary", use_container_width=True):
            st.session_state.dice = [random.randint(1, 6) for _ in range(5)]
            st.session_state.reroll_done = True; st.rerun()

    pool = [c for c in innate_cards if c.name not in p_now["used_innate"]] + p_now["hand"]
    available = []
    for c in pool:
        reason = get_satisfied_condition(st.session_state.dice, c.condition)
        if reason: available.append((c, reason))

    if not available:
        st.error("条件を満たすカードがありません！")
        if len(p_now["hand"]) < 5:
            if st.button("🎴 代わりにドローして終了", use_container_width=True):
                if st.session_state.deck: p_now["hand"].append(st.session_state.deck.pop())
                switch_player(); st.rerun()
        if p_now["hand"] and st.button("🗑️ 手札を1枚捨てて交代"):
            p_now["hand"].pop(0); switch_player(); st.rerun()
        elif st.button("パス"): switch_player(); st.rerun()
    else:
        selected_idx = st.radio("カード選択:", range(len(available)), 
                               format_func=lambda x: f"{available[x][0].name} [{available[x][1]}] (ATK:{available[x][0].power})")
        if st.button("🔥 発動！", use_container_width=True):
            card, reason = available[selected_idx]
            if card.type == "attack": p_opp["hp"] -= (card.power + p_now["bonus"])
            elif card.type == "heal": p_now["hp"] += card.power
            add_log(f"{card.name}({reason})！")
            found = False
            for i, h_card in enumerate(p_now["hand"]):
                if h_card is card: p_now["hand"].pop(i); found = True; break
            if not found: p_now["used_innate"].append(card.name)
            switch_player(); st.rerun()

st.divider()
st.write("### 📜 ログ")
for l in st.session_state.log[:5]: st.write(f"- {l}")
