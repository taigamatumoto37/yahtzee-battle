import streamlit as st
import random
from collections import Counter

# --- ページ設定 ---
st.set_page_config(page_title="Yahtzee Tactics: High Visibility", layout="wide")

# CSSの修正：全体をより見やすく
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .main-header { text-align: center; color: #00ffaa; margin-bottom: 20px; }
    
    /* プレイヤー情報ボックス */
    .player-card { 
        padding: 15px; border-radius: 10px; background-color: #1e222d;
        border: 2px solid #3e4452; margin-bottom: 10px;
    }
    .active-p1 { border-color: #ff4b4b; box-shadow: 0 0 10px rgba(255, 75, 75, 0.4); }
    .active-p2 { border-color: #00d4ff; box-shadow: 0 0 10px rgba(0, 212, 255, 0.4); }

    /* ダイス表示 */
    .dice-box { 
        font-size: 50px; background-color: #ffffff; color: #111111; 
        width: 70px; height: 70px; display: inline-flex; 
        align-items: center; justify-content: center; 
        border-radius: 10px; margin: 5px; font-weight: bold;
    }

    /* ログの文字色 */
    .log-text { color: #bbbbbb; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

DICE_ICONS = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

# --- 判定・ロジック ---
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
if 'deck' not in st.session_state or st.sidebar.button("♻️ ゲームをリセット"):
    common_deck = []
    for _ in range(15): common_deck.append(Card("追撃・小剣", "attack", 20, "check_pair"))
    for _ in range(12): common_deck.append(Card("強襲・大剣", "attack", 65, "check_three"))
    for _ in range(8):  common_deck.append(Card("アイアン・シールド", "guard", 35, "check_pair"))
    for _ in range(5):  common_deck.append(Card("癒しのハーブ", "heal", 30, "check_pair"))
    for _ in range(5):  common_deck.append(Card("猛毒の粉末", "status", 12, "check_pair", effect="poison", duration=3))
    for _ in range(3):  common_deck.append(Card("癒しの香水", "status", 15, "check_pair", effect="regen", duration=3))
    random.shuffle(common_deck)
    st.session_state.update({
        'deck': common_deck, 
        'p1': {"hp": 150, "hand": [], "bonus": 0, "guard": 0, "innate": get_innate_deck(), "status": []},
        'p2': {"hp": 150, "hand": [], "bonus": 0, "guard": 0, "innate": get_innate_deck(), "status": []},
        'current_player': "P1", 'dice': [random.randint(1, 6) for _ in range(5)],
        'phase': "action", 'reroll_done': False, 'log': ["バトル開始！"], 'winner': None, 'pending_action': None
    })

def switch_player():
    if st.session_state.p1["hp"] <= 0: st.session_state.winner = "PLAYER 2"
    elif st.session_state.p2["hp"] <= 0: st.session_state.winner = "PLAYER 1"
    if st.session_state.winner: return
    st.session_state.current_player = "P2" if st.session_state.current_player == "P1" else "P1"
    st.session_state.phase = "action"; st.session_state.reroll_done = False
    st.session_state.p1["guard"] = 0; st.session_state.p2["guard"] = 0
    st.session_state.dice = [random.randint(1, 6) for _ in range(5)]
    st.session_state.pending_action = None

# --- メインUI ---
st.markdown("<h1 class='main-header'>⚔️ ATTACKER'S YAHTZEE ⚔️</h1>", unsafe_allow_html=True)

p_now = st.session_state.p1 if st.session_state.current_player == "P1" else st.session_state.p2
p_opp = st.session_state.p2 if st.session_state.current_player == "P1" else st.session_state.p1

# プレイヤー情報表示
col1, col2 = st.columns(2)
for i, (col, p_key) in enumerate(zip([col1, col2], ["p1", "p2"])):
    p = st.session_state[p_key]
    active_class = f"active-p{i+1}" if st.session_state.current_player == f"P{i+1}" else ""
    with col:
        st.markdown(f"""
            <div class='player-card {active_class}'>
                <h3 style='margin:0;'>PLAYER {i+1}</h3>
                <p style='font-size:1.2em; color:#00ffaa;'>HP: {max(0, p["hp"])} / 150</p>
                <p style='color:#ffeb3b;'>現在のガード: {p["guard"]}</p>
            </div>
        """, unsafe_allow_html=True)

st.divider()

# フェーズ管理
if st.session_state.phase == "action":
    st.subheader(f"【{st.session_state.current_player}】 移動フェーズ")
    if st.button("🎴 カードを引いて交代", use_container_width=True):
        if st.session_state.deck and len(p_now["hand"]) < 5:
            p_now["hand"].append(st.session_state.deck.pop())
            switch_player(); st.rerun()
    if st.button("⚔️ バトル開始 (ダイスを振る)", use_container_width=True, type="primary"):
        st.session_state.phase = "battle"; st.rerun()

elif st.session_state.phase == "battle":
    # ダイス表示
    dice_html = "".join([f'<div class="dice-box">{DICE_ICONS[d]}</div>' for d in st.session_state.dice])
    st.markdown(dice_html, unsafe_allow_html=True)
    
    if not st.session_state.reroll_done:
        if st.button("🎲 1回だけ振り直す"):
            st.session_state.dice = [random.randint(1, 6) for _ in range(5)]; st.session_state.reroll_done = True; st.rerun()

    # カード選択
    st.write("### 使用するカードを選択：")
    all_cards = []
    for c in p_now["innate"] + p_now["hand"]:
        reason = get_reason_text(st.session_state.dice, c.condition_name)
        if reason:
            source = "固有" if c in p_now["innate"] else "手札"
            all_cards.append((c, reason, source))

    if not all_cards:
        st.error("出せる役がありません。")
        if st.button("ターン終了"): switch_player(); st.rerun()
    else:
        cols = st.columns(min(len(all_cards), 4))
        for idx, (card, reason, source) in enumerate(all_cards):
            with cols[idx % 4]:
                # --- 色付き情報の表示 (Markdownを使用) ---
                st.write(f"**{source}: {card.name}**")
                if card.type == "attack":
                    total_dmg = max(0, (card.value + p_now["bonus"]) - p_opp["guard"])
                    st.markdown(f":red[予測ダメ: {total_dmg}] ({reason})")
                elif card.type == "heal":
                    st.markdown(f":green[回復: {card.value}] ({reason})")
                elif card.type == "guard":
                    st.markdown(f":orange[防御力: {card.value}] ({reason})")
                elif card.type == "status":
                    color = "violet" if card.effect == "poison" else "green"
                    st.markdown(f":{color}[効果: {card.value}×{card.duration}T]")

                if st.button("このカードを使う", key=f"btn_{idx}", use_container_width=True):
                    if card.type in ["attack", "status"] and card.effect != "regen":
                        st.session_state.pending_action = {"card": card, "source": source}
                        st.session_state.phase = "counter"; st.rerun()
                    else:
                        # 即時効果（回復・防御など）
                        if card.type == "heal": p_now["hp"] += card.value
                        elif card.type == "guard": p_now["guard"] = card.value
                        
                        if source == "固有": p_now["innate"].remove(card)
                        else: p_now["hand"].remove(card)
                        switch_player(); st.rerun()

elif st.session_state.phase == "counter":
    st.warning("⚠️ 防御確認フェーズ：相手の攻撃をブロックしますか？")
    available_guards = [c for c in p_opp["hand"] if c.type == "guard"]
    
    # ブラフ選択肢
    options = ["防御しない"] + [f"{g.name} (軽減:{g.value})" for g in available_guards]
    selected = st.radio("ガードカード選択（相手には中身は見えません）", options)

    if st.button("決定してダメージ処理", type="primary"):
        action = st.session_state.pending_action
        atk_card = action["card"]
        current_guard = 0
        if selected != "防御しない":
            g_idx = options.index(selected) - 1
            g_card = available_guards[g_idx]
            current_guard = g_card.value
            p_opp["hand"].remove(g_card)
        
        # 計算
        if atk_card.type == "attack":
            dmg = max(0, (atk_card.value + p_now["bonus"]) - current_guard)
            p_opp["hp"] -= dmg
            st.session_state.log.insert(0, f"💥 {dmg}ダメージを与えた！")
        
        if action["source"] == "固有": p_now["innate"].remove(atk_card)
        else: p_now["hand"].remove(atk_card)
        switch_player(); st.rerun()

st.divider()
st.write("⚡ 最近のログ:")
for l in st.session_state.log[:3]: st.write(f"- {l}")
