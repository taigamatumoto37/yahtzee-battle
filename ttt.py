import streamlit as st
import random
from collections import Counter

# --- ページ設定 ---
st.set_page_config(page_title="Yahtzee Tactics: Visible UI", layout="wide")

# スタイルの修正：文字色を明示し、ボタン内の色分けを強化
st.markdown("""
    <style>
    /* 全体の背景と基本文字色 */
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* ヘッダー */
    .main-header { text-align: center; color: #00ffaa; font-family: 'Courier New', Courier, monospace; text-shadow: 2px 2px 4px #000; }
    
    /* プレイヤーカード */
    .player-card { 
        padding: 20px; border-radius: 15px; background-color: #1e222d;
        border: 2px solid #3e4452; color: #ffffff;
    }
    .active-p1 { border: 3px solid #ff4b4b !important; box-shadow: 0 0 15px rgba(255, 75, 75, 0.5); }
    .active-p2 { border: 3px solid #00d4ff !important; box-shadow: 0 0 15px rgba(0, 212, 255, 0.5); }
    
    /* ダイス */
    .dice-container { display: flex; justify-content: center; gap: 15px; margin: 20px 0; }
    .dice-box { 
        font-size: 60px; background-color: #ffffff; color: #111; width: 80px; height: 80px; 
        display: flex; align-items: center; justify-content: center; border-radius: 10px; 
        box-shadow: 3px 3px 10px rgba(0,0,0,0.5);
    }
    
    /* カードバッジ */
    .badge { padding: 4px 10px; border-radius: 12px; font-size: 0.8em; font-weight: bold; color: white; margin-bottom: 5px; display: inline-block; }
    .bg-innate { background-color: #e91e63; }
    .bg-hand { background-color: #607d8b; }
    
    /* 効果の色分け */
    .text-attack { color: #ff4b4b; font-weight: bold; } /* 赤色：攻撃 */
    .text-heal { color: #00ffaa; font-weight: bold; }   /* 緑色：回復 */
    .text-guard { color: #ffeb3b; font-weight: bold; }  /* 黄色：防御 */
    .text-poison { color: #b388ff; font-weight: bold; } /* 紫色：毒 */
    
    /* ステータスバッジ */
    .status-badge { background-color: #673ab7; color: white; padding: 2px 8px; border-radius: 5px; font-size: 0.8em; margin-right: 5px; }

    /* Streamlit標準要素の文字色強制 */
    .stMarkdown, p, h1, h2, h3, label { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

DICE_ICONS = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

# --- 判定ロジック ---
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

def process_status_effects(player_key):
    p = st.session_state[player_key]
    new_status = []
    for s in p["status"]:
        if s["type"] == "poison":
            p["hp"] -= s["value"]
            st.session_state.log.insert(0, f"⚠️ {player_key}は毒で{s['value']}ダメ")
        elif s["type"] == "regen":
            p["hp"] += s["value"]
            st.session_state.log.insert(0, f"💖 {player_key}は再生で{s['value']}回復")
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
st.markdown("<h1 class='main-header'>⚔️ ATTACKER'S YAHTZEE ⚔️</h1>", unsafe_allow_html=True)

if st.session_state.winner:
    st.balloons()
    st.markdown(f"<h1 style='text-align:center; color:#ffcc00;'>🏆 {st.session_state.winner} の勝利！</h1>", unsafe_allow_html=True)
    if st.button("もう一度遊ぶ", use_container_width=True):
        del st.session_state['deck']; st.rerun()
    st.stop()

p_now = st.session_state.p1 if st.session_state.current_player == "P1" else st.session_state.p2
p_opp = st.session_state.p2 if st.session_state.current_player == "P1" else st.session_state.p1

col_p1, col_vs, col_p2 = st.columns([4, 1, 4])
for i, (col, p_key) in enumerate(zip([col_p1, col_p2], ["p1", "p2"])):
    p = st.session_state[p_key]
    active = f"active-p{i+1}" if st.session_state.current_player == f"P{i+1}" else ""
    with col:
        st.markdown(f'<div class="player-card {active}"><h3>PLAYER {i+1}</h3><p style="font-size:20px;">HP: {max(0, p["hp"])} / 150</p></div>', unsafe_allow_html=True)
        st.progress(max(0, min(p['hp'] / 150, 1.0)))
        for s in p["status"]:
            st.markdown(f"<span class='status-badge'>{'毒' if s['type']=='poison' else '再生'} ({s['duration']}T)</span>", unsafe_allow_html=True)

st.divider()

if st.session_state.phase == "action":
    st.markdown(f"### 【{st.session_state.current_player}】 移動フェーズ")
    c1, c2 = st.columns(2)
    if c1.button("🎴 カードをドロー", use_container_width=True, disabled=len(p_now["hand"])>=5):
        if st.session_state.deck:
            p_now["hand"].append(st.session_state.deck.pop())
            st.session_state.log.insert(0, f"{st.session_state.current_player}がドロー"); switch_player(); st.rerun()
    if c2.button("⚔️ バトル開始", use_container_width=True, type="primary"):
        st.session_state.phase = "battle"; st.rerun()

elif st.session_state.phase == "battle":
    dice_html = "".join([f'<div class="dice-box">{DICE_ICONS[d]}</div>' for d in st.session_state.dice])
    st.markdown(f'<div class="dice-container">{dice_html}</div>', unsafe_allow_html=True)
    if not st.session_state.reroll_done:
        if st.button("🎲 振り直す", use_container_width=True):
            st.session_state.dice = [random.randint(1, 6) for _ in range(5)]; st.session_state.reroll_done = True; st.rerun()

    all_cards = []
    for c in p_now["innate"] + p_now["hand"]:
        reason = get_reason_text(st.session_state.dice, c.condition_name)
        if reason:
            source = "innate" if c in p_now["innate"] else "hand"
            all_cards.append((c, reason, source))

    if not all_cards:
        st.error("役なし..."); 
        if st.button("ターン終了"): switch_player(); st.rerun()
    else:
        st.write("### 使用するカードを選択：")
        cols = st.columns(len(all_cards) if len(all_cards) <= 4 else 4)
        for idx, (card, reason, source) in enumerate(all_cards):
            with cols[idx % 4]:
                st.markdown(f"<span class='badge {'bg-innate' if source=='innate' else 'bg-hand'}'>{source.upper()}</span>", unsafe_allow_html=True)
                
                # --- 色分けされたラベルの生成 ---
                label = f"**{card.name}**\n({reason})"
                if card.type == "attack":
                    total_dmg = max(0, (card.value + p_now["bonus"]) - p_opp["guard"])
                    label += f"\n<span class='text-attack'>予測ダメ: {total_dmg}</span>"
                elif card.type == "status" and card.effect == "poison":
                    label += f"\n<span class='text-poison'>毒: {card.value}×{card.duration}T</span>"
                elif card.type == "heal":
                    label += f"\n<span class='text-heal'>回復: {card.value}</span>"
                elif card.type == "guard":
                    label += f"\n<span class='text-guard'>防御: {card.value}</span>"
                elif card.type == "status" and card.effect == "regen":
                    label += f"\n<span class='text-heal'>再生: {card.value}×{card.duration}T</span>"

                if st.button(label, key=f"btn_{idx}", use_container_width=True):
                    if card.type in ["attack", "status"] and card.effect != "regen":
                        st.session_state.pending_action = {"card": card, "source": source, "reason": reason}
                        st.session_state.phase = "counter"; st.rerun()
                    else:
                        if card.type == "heal": p_now["hp"] += card.value
                        elif card.type == "status": p_now["status"].append({"type": card.effect, "value": card.value, "duration": card.duration})
                        elif card.type == "guard": p_now["guard"] = card.value
                        if source == "innate": p_now["innate"].remove(card)
                        else: p_now["hand"].remove(card)
                        st.session_state.log.insert(0, f"{st.session_state.current_player}が{card.name}を発動"); switch_player(); st.rerun()

elif st.session_state.phase == "counter":
    target_p_id = "P2" if st.session_state.current_player == "P1" else "P1"
    st.warning(f"⚔️ {st.session_state.current_player}の攻撃！ 【{target_p_id}】防御確認")
    available_guards = [c for c in p_opp["hand"] if c.type == "guard"]
    options = ["防御しない"] + [f"{g.name} (軽減:{g.value})" for g in available_guards]
    selected = st.radio("ガードを選択（ブラフ）:", options)

    if st.button("決定", use_container_width=True, type="primary"):
        action = st.session_state.pending_action
        atk_card = action["card"]
        current_guard = 0
        if selected != "防御しない":
            g_idx = options.index(selected) - 1
            g_card = available_guards[g_idx]
            current_guard = g_card.value
            p_opp["hand"].remove(g_card)
        
        if atk_card.type == "attack":
            dmg = max(0, (atk_card.value + p_now["bonus"]) - current_guard)
            p_opp["hp"] -= dmg
            st.session_state.log.insert(0, f"💥 {dmg}ダメ付与")
        elif atk_card.type == "status":
            p_opp["status"].append({"type": atk_card.effect, "value": atk_card.value, "duration": atk_card.duration})
            st.session_state.log.insert(0, f"☣️ 状態異常付与")

        if action["source"] == "innate": p_now["innate"].remove(atk_card)
        else: p_now["hand"].remove(atk_card)
        switch_player(); st.rerun()

st.divider()
for l in st.session_state.log[:3]: st.write(f"- {l}")
