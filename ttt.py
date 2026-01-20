import streamlit as st
import random
import time
from collections import Counter

# --- ページ設定 ---
st.set_page_config(page_title="Yahtzee Tactics: Sorted Dice", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #ffffff; }
    h1, h2, h3, p, label { color: #ffffff !important; }
    div[data-testid="stMetricValue"] > div { color: #00ffaa !important; }
    .dice-box {
        background: radial-gradient(circle, #1a2a3a 0%, #0b0e14 100%);
        border: 2px solid #00d4ff;
        border-radius: 15px;
        box-shadow: 0 0 15px #00d4ff55;
        font-size: 3.5rem; text-align: center; padding: 10px; margin: 5px;
        color: #00d4ff; text-shadow: 0 0 10px #00d4ff;
    }
    .hand-card {
        background: #1a1c23; border-left: 4px solid #00d4ff;
        padding: 5px 10px; margin-bottom: 5px; border-radius: 4px; font-size: 0.9rem;
    }
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
        Card("固有:癒歌", "heal", 30, "check_pair"),
        Card("固有:毒液", "status", 10, "check_pair", effect="poison", duration=3),
        Card("固有:強撃", "attack", 45, "check_three"),
        Card("固有:爆裂", "attack", 70, "check_small_straight"),
        Card("固有:絶技", "attack", 90, "check_full_house"),
        Card("固有:神域", "attack", 150, "check_yahtzee")
    ]

# --- 初期化 ---
if 'deck' not in st.session_state or st.sidebar.button("♻️ ゲームをリセット"):
    common_deck = []
    for _ in range(15): common_deck.append(Card("追撃・小剣", "attack", 25, "check_pair"))
    for _ in range(10): common_deck.append(Card("強襲・大剣", "attack", 65, "check_three"))
    for _ in range(6):  common_deck.append(Card("アイアン・ガード", "guard", 45, "check_pair"))
    for _ in range(5):  common_deck.append(Card("癒しのハーブ", "heal", 35, "check_pair"))
    for _ in range(3):  common_deck.append(Card("癒しの香水", "status", 15, "check_pair", effect="regen", duration=3))
    for _ in range(4):  common_deck.append(Card("猛毒の粉末", "status", 12, "check_pair", effect="poison", duration=3))
    for _ in range(4):  common_deck.append(Card("攻撃強化の粉末", "status", 12, "check_pair", effect="buff", duration=3))

    random.shuffle(common_deck)
    initial_dice = [random.randint(1, 6) for _ in range(5)]
    initial_dice.sort() # 初期ダイスをソート
    st.session_state.update({
        'deck': common_deck, 
        'p1': {"hp": 150, "hand": [], "innate": get_innate_deck(), "guard": 0, "bonus": 0, "status": []},
        'p2': {"hp": 150, "hand": [], "innate": get_innate_deck(), "guard": 0, "bonus": 0, "status": []},
        'current_player': "P1", 'dice': initial_dice,
        'phase': "action", 'reroll_done': False, 
        'log_entries': [{"icon": "⚔️", "msg": "宿命の対決開始"}], 
        'winner': None, 'pending_action': None
    })

def add_log(icon, msg):
    st.session_state.log_entries.insert(0, {"icon": icon, "msg": msg})

def process_status_effects(player_key):
    p = st.session_state[player_key]
    new_status = []
    for s in p["status"]:
        if s["type"] == "poison":
            p["hp"] -= s["value"]; add_log("☣️", f"{player_key}に毒ダメージ: {s['value']}")
        elif card.type == "status" and card.effect == "buff":
            p_now["bonus"] += card.value

        elif s["type"] == "regen":
            p["hp"] = min(150, p["hp"] + s["value"]); add_log("💖", f"{player_key}が再生回復: {s['value']}")
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
    new_dice = [random.randint(1, 6) for _ in range(5)]
    new_dice.sort() # 交代時のダイスをソート
    st.session_state.dice = new_dice
    st.session_state.pending_action = None

# --- UI Layout ---
with st.sidebar:
    st.header("📜 戦況記録書")
    for entry in st.session_state.log_entries[:8]:
        with st.chat_message("user", avatar=entry["icon"]): st.write(entry["msg"])
    st.divider()
    st.header("🎴 あなたの手札")
    me = st.session_state[st.session_state.current_player.lower()]
    for c in me["innate"]: st.markdown(f'<div class="hand-card">💎 {c.name}</div>', unsafe_allow_html=True)
    for c in me["hand"]: st.markdown(f'<div class="hand-card">📜 {c.name}</div>', unsafe_allow_html=True)

st.title("⚔️ YAHTZEE TACTICS ⚔️")

if st.session_state.winner:
    st.success(f"🏆 {st.session_state.winner} の勝利！")
    if st.button("再戦"): del st.session_state['deck']; st.rerun()
    st.stop()

cols = st.columns(2)
for i, (col, key) in enumerate(zip(cols, ["p1", "p2"])):
    p = st.session_state[key]
    with col:
        st.subheader(f"PLAYER {i+1} {'🔥' if st.session_state.current_player == f'P{i+1}' else ''}")
        st.metric("HP", f"{max(0, p['hp'])} / 150")
        for s in p["status"]:
            color = "violet" if s["type"]=="poison" else "green"
            st.markdown(f":{color}[[{'毒' if s['type']=='poison' else '再生'}] {s['value']} (残り{s['duration']}T)]")

st.divider()

if st.session_state.phase == "action":
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎴 カードを引いて交代", use_container_width=True, type="primary"):
            p = st.session_state[st.session_state.current_player.lower()]
            if st.session_state.deck and len(p["hand"]) < 5:
                p["hand"].append(st.session_state.deck.pop())
                switch_player(); st.rerun()
    with c2:
        if st.button("⚔️ 攻撃フェーズへ", use_container_width=True, type="primary"):
            st.session_state.phase = "battle"; st.rerun()

elif st.session_state.phase == "battle":
    p_now = st.session_state[st.session_state.current_player.lower()]
    p_opp = st.session_state["p2" if st.session_state.current_player == "P1" else "p1"]
    
    st.write("### 🎲 運命の刻印")
    d_cols = st.columns(5)
    for i, d in enumerate(st.session_state.dice):
        d_cols[i].markdown(f'<div class="dice-box">{DICE_ICONS[d]}</div>', unsafe_allow_html=True)
    
    if not st.session_state.reroll_done:
        if st.button("🎲 振り直す", type="primary", use_container_width=True):
            # 演出用のランダム表示
            ph = st.empty()
            for _ in range(4):
                tmp = [random.randint(1, 6) for _ in range(5)]
                with ph.container():
                    cols_anim = st.columns(5)
                    for idx, td in enumerate(tmp): cols_anim[idx].markdown(f'<div class="dice-box">{DICE_ICONS[td]}</div>', unsafe_allow_html=True)
                time.sleep(0.1)
            ph.empty()
            
            final_dice = [random.randint(1, 6) for _ in range(5)]
            final_dice.sort() # 振り直し後の結果をソート
            st.session_state.dice = final_dice
            st.session_state.reroll_done = True; st.rerun()

    st.write("---")
    available = []
    cards_to_check = [(c, "固有") for c in p_now["innate"]] + [(c, "手札") for c in p_now["hand"]]
    for c, t in cards_to_check:
        reason = get_reason_text(st.session_state.dice, c.condition_name)
        if reason: available.append((c, reason, t))

    if not available:
        if st.button("ターンを終える", type="primary"): switch_player(); st.rerun()
    else:
        grid = st.columns(3)
        for idx, (card, reason, tag) in enumerate(available):
            with grid[idx % 3]:
                st.markdown(f"**{card.name}**")
                if card.type == "attack":
                    total_dmg = max(0, card.value + p_now["bonus"] - p_opp["guard"])
                    st.markdown(f":red[威力: {total_dmg}]")
                elif card.type == "status": st.markdown(f":violet[効果: {card.value}]")
                elif card.type == "heal": st.markdown(f":green[回復: {card.value}]")
                elif card.type == "guard": st.markdown(f":blue[防御: {card.value}]")
                
                st.caption(f"条件: {reason}")
                
                if st.button("発動", key=f"btn_{idx}", use_container_width=True, type="primary"):
                    if card.type == "attack" or (card.type == "status" and card.effect == "poison"):
                        st.session_state.pending_action = {"card": card, "source": tag}
                        st.session_state.phase = "counter"; st.rerun()
                    else:
                        if card.type == "heal": p_now["hp"] = min(150, p_now["hp"] + card.value)
                        elif card.type == "guard": p_now["guard"] = card.value
                        elif card.type == "status" and card.effect == "regen":
                           p_now["status"].append({"type": "regen","value": card.value,"duration": card.duration})
                            target_list = p_now["innate"] if tag == "固有" else p_now["hand"]
                            add_log("🔥", f"攻撃力 +{card.value}")
                        
                        for i, item in enumerate(target_list):
                            if item.name == card.name:
                                target_list.pop(i); break
                        
                        if tag == "固有" and not p_now["innate"]:
                            p_now["innate"] = get_innate_deck(); p_now["bonus"] += 10
                            add_log("🔥", "覚醒！固有復活")
                        
                        switch_player(); st.rerun()

elif st.session_state.phase == "counter":
    atk_id = st.session_state.current_player
    opp_key = "p2" if atk_id == "P1" else "p1"
    p_now, p_opp = st.session_state[atk_id.lower()], st.session_state[opp_key]
    action = st.session_state.pending_action
    card = action["card"]

    st.subheader(f"🛡️ 防御確認")
    base_dmg = card.value + p_now["bonus"] if card.type == "attack" else 0
    
    guards = [c for c in p_opp["hand"] if c.type == "guard"]
    options = ["防御しない"] + [f"{g.name} ({g.value}軽減)" for g in guards]
    choice = st.radio("ガード選択:", options)

    g_val = 0
    if "防御しない" not in choice:
        g_val = guards[options.index(choice) - 1].value
    
    final_dmg = max(0, base_dmg - g_val)
    if card.type == "attack": st.metric("ダメージ予定", final_dmg, delta=-g_val)

    if st.button("結果を確定", type="primary", use_container_width=True):
        if g_val > 0:
            for i, c in enumerate(p_opp["hand"]):
                if c.name == guards[options.index(choice)-1].name:
                    p_opp["hand"].pop(i); break
        
        if card.type == "status":
            p_opp["status"].append({"type": card.effect, "value": card.value, "duration": card.duration})
        elif card.type == "attack":
            p_opp["hp"] -= final_dmg
            add_log("💥", f"{final_dmg} ダメージ")

        target_list = p_now["innate"] if action["source"] == "固有" else p_now["hand"]
        for i, item in enumerate(target_list):
            if item.name == card.name:
                target_list.pop(i); break
        
        if action["source"] == "固有" and not p_now["innate"]:
            p_now["innate"] = get_innate_deck(); p_now["bonus"] += 10
            add_log("🔥", "覚醒！固有復活")

        switch_player(); st.rerun()




