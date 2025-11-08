# -*- coding: utf-8 -*-
# 🌈 시나모롤의 마음별 이야기 v4.3 — Cinnamo World Cute Edition
# 배포: Streamlit Cloud (Settings → Secrets에 OPENAI_API_KEY 등록)
# 주의: 시나모롤은 Sanrio의 IP. 공개/상용 전 권리 검토 필요.

import os, json, random, tempfile
import streamlit as st
from openai import OpenAI
from streamlit_drawable_canvas import st_canvas

# ============ 기본 설정 ============
st.set_page_config(page_title="시나모롤의 마음별 이야기", layout="centered")
API_KEY = st.secrets.get("OPENAI_API_KEY", "")
client = OpenAI(api_key=API_KEY)

DATA_DIR = "data"
ASSETS_DIR = "assets"
os.makedirs(DATA_DIR, exist_ok=True)

USER_FILE = os.path.join(DATA_DIR, "user_data.json")
SCENE_FILE = os.path.join(DATA_DIR, "scenes.json")
SKY_FILE   = os.path.join(DATA_DIR, "decorations.json")
ROOM_FILE  = os.path.join(DATA_DIR, "room.json")

# ============ 귀여운 UI CSS ============
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@700;900&display=swap');
html, body, .stApp { background: linear-gradient(to bottom, #C7EDFF, #FCE6F5); }
* { font-family: 'Nunito','NanumSquareRound',sans-serif; }
h1,h2,h3 { color:#374151; }
button[kind="primary"]{
  background:#FFD6EC !important; color:#6B21A8 !important; border-radius:16px !important;
  font-weight:900 !important; box-shadow:0 4px 12px rgba(255,192,203,.35);
  transition:all .2s ease-in-out;
}
button[kind="primary"]:hover{ transform:scale(1.03); }
.progress-cute > div > div{ background:linear-gradient(90deg,#A5F3FC,#F9A8D4); border-radius:999px; }
.badge{display:inline-block;padding:6px 12px;border-radius:999px;background:#e0f2fe;color:#0369a1;font-weight:900}
.bubble{background:white;border-radius:20px;padding:10px 16px;display:inline-block;
  box-shadow:0 4px 12px rgba(0,0,0,.08);max-width:92%;}
.cinnamo{position:fixed;right:16px;bottom:14px;font-size:40px;animation:float 3s ease-in-out infinite;}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 12px 0;align-items:center}
.toolbtn{padding:6px;border-radius:12px;background:#fff;border:1px solid #e5e7eb;
  box-shadow:0 2px 6px rgba(0,0,0,.06);cursor:pointer}
.toolbtn img{width:52px;height:52px;display:block}
.bg-card{border-radius:16px;border:1px solid #e5e7eb;background:rgba(255,255,255,.5);padding:8px}
.footer-note{opacity:.6}
</style>
<div class="cinnamo">🐶☁️</div>
""", unsafe_allow_html=True)

# ============ 데이터 유틸 ============
DEFAULT_SCENES = {
    "친구가 넘어졌어요": ["괜찮아요", "싫어요", "몰라요"],
    "새 친구가 인사했어요": ["안녕", "누구야", "몰라"],
    "친구가 도와줬어요": ["고마워요", "응", "나중에"],
    "내가 실수했어요(장난감 떨어뜨림)": ["미안해요", "그냥 줘", "도망가요"],
    "그네를 같이 타고 싶대요": ["먼저 타!", "내가 먼저야!", "그냥 가자"],
    "그림 대회에서 떨어졌대요": ["다음엔 잘 될 거야", "하하!", "그럴 줄 알았어"],
    "학교에서 줄 서는 중": ["차례대로 서요", "밀지 마요", "몰라요"],
    "선생님이 질문했어요": ["손들고 말해요", "큰소리로 끼어들기", "조용히 있기만"],
    "가족이 도와달래요": ["같이 해요", "싫어요", "몰라요"],
    "동생이 장난감을 원해요": ["같이 놀아요", "내 거야!", "모른 척"],
    "친구가 울고 있어요": ["괜찮아? 이야기해줄래", "웃지 마", "지나가기"],
    "친구가 선물을 줬어요": ["고마워요", "응", "그냥 받기"]
}

def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 세션 초기화
if "user" not in st.session_state:
    st.session_state.user = load_json(USER_FILE, {"hearts": 0, "log": [], "diary": []})
if "mode" not in st.session_state:
    st.session_state.mode = "main"  # main / decorate_sky / decorate_room
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "feedback" not in st.session_state:
    st.session_state.feedback = ""

# 최초 scenes 생성
if not os.path.exists(SCENE_FILE):
    save_json(SCENE_FILE, DEFAULT_SCENES)

# ============ 공용 함수 ============
def asset(path):  # 자산 존재 안하면 None 반환 (안전)
    p = os.path.join(ASSETS_DIR, path)
    return p if os.path.exists(p) else None

def transcribe_audio(bytes_wav: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(bytes_wav); tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as f:
            tr = client.audio.transcriptions.create(model="whisper-1", file=f, language="ko")
        return tr.text.strip()
    finally:
        try: os.remove(tmp_path)
        except: pass

def cinnamo_feedback(scene: str, utter: str) -> str:
    sys = ("너는 7세 아동의 예의·배려 학습을 돕는 시나모롤 톤의 도우미야. "
           "아이가 한 말을 배려/공감/무관심/공격 중 하나로 분류하고, "
           "시나모롤 말투로 1문장 피드백을 해줘. "
           "출력 형식: [분류] 시나모롤: (한 문장)")
    user = f'상황: "{scene}"\n아이의 말: "{utter}"'
    rsp = client.responses.create(
        model="gpt-5-mini",
        input=[{"role":"system","content":sys},{"role":"user","content":user}]
    )
    return rsp.output_text.strip()

def praise_for_decor(kind: str) -> str:
    prompt = f"너는 시나모롤이야. 아이가 { '하늘을' if kind=='sky' else '방을' } 예쁘게 꾸몄어. 귀엽고 다정하게 한 문장으로 칭찬해줘."
    rsp = client.responses.create(model="gpt-5-mini", input=prompt)
    return rsp.output_text.strip()

# ============ 공용: BGM/효과음 UI ============
def audio_player(title:str, file_name:str):
    path = asset(file_name)
    if path:
        st.audio(path, format="audio/mp3", loop=True)
    else:
        st.caption(f"🎵 {title}: assets/{file_name} 를 넣으면 자동 재생됩니다.")

def tiny_sfx(file_name:str):
    path = asset(file_name)
    if path:
        st.audio(path, format="audio/mp3")
    # 없으면 조용히 패스

# ============ 하늘 꾸미기 ============
def decorate_sky_mode():
    st.markdown("## ☁️ 하늘 꾸미기")
    audio_player("하늘 BGM", "bgm_sky.mp3")

    hearts = st.session_state.user["hearts"]
    st.caption("마음별로 아이템 잠금 해제!")
    unlocked = []
    if hearts >= 10: unlocked.append("구름")
    if hearts >= 20: unlocked.append("무지개")
    if hearts >= 30: unlocked.append("별")
    if hearts >= 40: unlocked.append("집")
    if hearts >= 50: unlocked.append("나무")
    st.markdown(f"<span class='badge'>획득</span> {' · '.join(unlocked) if unlocked else '아직 없어요 ☁️'}", unsafe_allow_html=True)

    # PNG 툴바 안내 (버튼 동작은 Canvas transform 중심이므로 안내용)
    st.markdown("<div class='toolbar bg-card'>", unsafe_allow_html=True)
    for icon in ["cloud.png","rainbow.png","star.png","house.png","tree.png"]:
        path = asset(icon)
        if path:
            st.markdown(f"<div class='toolbtn'><img src='{path}'></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='toolbtn'>🔲 {icon}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 이전 저장 복원
    prev = load_json(SKY_FILE, {})
    if prev: st.info("이전에 꾸민 하늘을 불러왔어요 ☁️")

    # 배경 이미지/색 자동 선택
    bg_img = asset("bg_sky.png")
    canvas_kwargs = dict(
        fill_color="rgba(255,255,255,0.3)",
        stroke_width=1,
        height=500, width=700,
        drawing_mode="transform",
        key="decorate_sky",
        initial_drawing=prev if prev else None,
    )
    if bg_img:
        canvas_kwargs["background_image"] = bg_img
    else:
        canvas_kwargs["background_color"] = "#87CEEB"

    canvas_result = st_canvas(**canvas_kwargs)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("저장하기 💾", use_container_width=True):
            save_json(SKY_FILE, canvas_result.json_data)
            st.success("하늘이 저장되었어요!")
            tiny_sfx("sound_save.mp3")
            try:
                st.markdown(f"<div class='bubble'>💬 시나모롤: {praise_for_decor('sky')}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"AI 칭찬 실패: {e}")
            st.balloons()
    with c2:
        if st.button("방 꾸미기로 🏠", use_container_width=True):
            st.session_state.mode = "decorate_room"; st.experimental_rerun()
    with c3:
        if st.button("메인으로 🔙", use_container_width=True):
            st.session_state.mode = "main"; st.experimental_rerun()

# ============ 방 꾸미기 ============
def decorate_room_mode():
    st.markdown("## 🏠 시나모롤의 방 꾸미기")
    audio_player("방 BGM", "bgm_room.mp3")

    hearts = st.session_state.user["hearts"]
    st.caption("마음별을 모아 가구/소품을 언락하세요 ✨")
    unlocked = []
    if hearts >= 5: unlocked.append("의자")
    if hearts >= 10: unlocked.append("침대")
    if hearts >= 15: unlocked.append("커튼")
    if hearts >= 20: unlocked.append("책장")
    if hearts >= 30: unlocked.append("케이크")
    if hearts >= 40: unlocked.append("인형")
    st.markdown(f"<span class='badge'>획득</span> {' · '.join(unlocked) if unlocked else '아직 없어요 ☁️'}", unsafe_allow_html=True)

    st.markdown("<div class='toolbar bg-card'>", unsafe_allow_html=True)
    for icon in ["chair.png","bed.png","curtain.png","bookcase.png","cake.png","dog.png"]:
        path = asset(icon)
        if path:
            st.markdown(f"<div class='toolbtn'><img src='{path}'></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='toolbtn'>🔲 {icon}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    prev = load_json(ROOM_FILE, {})
    if prev: st.info("이전에 꾸민 방을 불러왔어요 🏠")

    bg_img = asset("bg_room.png")
    canvas_kwargs = dict(
        fill_color="rgba(255,255,255,0.3)",
        stroke_width=1,
        height=500, width=700,
        drawing_mode="transform",
        key="decorate_room",
        initial_drawing=prev if prev else None,
    )
    if bg_img:
        canvas_kwargs["background_image"] = bg_img
    else:
        canvas_kwargs["background_color"] = "#FFF4DE"

    canvas_result = st_canvas(**canvas_kwargs)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("저장하기 💾", use_container_width=True):
            save_json(ROOM_FILE, canvas_result.json_data)
            st.success("방 안이 저장되었어요!")
            tiny_sfx("sound_save.mp3")
            try:
                st.markdown(f"<div class='bubble'>💬 시나모롤: {praise_for_decor('room')}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"AI 칭찬 실패: {e}")
            st.balloons()
    with c2:
        if st.button("하늘 꾸미기로 ☁️", use_container_width=True):
            st.session_state.mode = "decorate_sky"; st.experimental_rerun()
    with c3:
        if st.button("메인으로 🔙", use_container_width=True):
            st.session_state.mode = "main"; st.experimental_rerun()

# ============ 학습(메인) ============
def main_mode():
    st.markdown("<h1 style='text-align:center;'>☁️ 시나모롤의 마음별 이야기</h1>", unsafe_allow_html=True)
    st.caption("따뜻한 말을 하면 하늘마을이 더 밝아져요 🌈 (오디오는 서버 저장 없이 즉시 변환 후 폐기)")

    scenes = load_json(SCENE_FILE, DEFAULT_SCENES)
    scene = st.selectbox("상황을 골라볼까요?", list(scenes.keys()))
    st.markdown(f"🩵 {scene}")

    st.markdown("---")
    st.subheader("🎤 시나모롤에게 뭐라고 말해줄까?")
    audio = st.audio_input("마이크로 녹음해보세요 🎙️")

    if st.button("Whisper로 인식 ▶️"):
        if not audio:
            st.warning("먼저 음성을 녹음해주세요.")
        else:
            try:
                text = transcribe_audio(audio.getvalue())
                st.session_state.transcript = text
                st.success(f"🗣️ 인식된 말: {text}")
            except Exception as e:
                st.error(f"음성 인식 실패: {e}")

    if st.button("AI 피드백 받기 💡"):
        utter = st.session_state.transcript or "(음성 없음)"
        try:
            fb = cinnamo_feedback(scene, utter)
            st.session_state.feedback = fb
            st.markdown(f"<div class='bubble'>💬 {fb}</div>", unsafe_allow_html=True)

            add = 5 if ("배려" in fb or "공감" in fb) else 1 if "무관심" in fb else 0
            st.session_state.user["hearts"] += add
            st.session_state.user["log"].append({"scene": scene, "utter": utter, "feedback": fb, "score": add})
            save_json(USER_FILE, st.session_state.user)

            st.markdown("<div class='progress-cute'>", unsafe_allow_html=True)
            st.progress(min(st.session_state.user["hearts"], 100)/100)
            st.markdown("</div>", unsafe_allow_html=True)
            st.caption(f"획득 점수: +{add}")
        except Exception as e:
            st.error(f"AI 응답 실패: {e}")

    st.markdown("---")
    st.subheader("🔤 한글 매칭")
    opts = scenes[scene][:]
    random.shuffle(opts)
    ans = scenes[scene][0]
    choice = st.radio("친구에게 어떤 말을 해줄까?", opts)
    if st.button("정답 확인 ✅"):
        if choice == ans:
            st.session_state.user["hearts"] += 3
            save_json(USER_FILE, st.session_state.user)
            st.success("🌈 좋은 말이에요! 마음별 +1")
        else:
            st.warning("☁️ 조금 더 다정한 말을 선택해볼까요?")

    st.markdown("---")
    hearts = st.session_state.user["hearts"]
    st.markdown("<div class='progress-cute'>", unsafe_allow_html=True)
    st.progress(min(hearts, 100)/100)
    st.markdown("</div>", unsafe_allow_html=True)
    st.write(f"✨ 지금까지 모은 마음별: **{hearts}**")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🎨 하늘 꾸미기", use_container_width=True):
            st.session_state.mode = "decorate_sky"; st.experimental_rerun()
    with c2:
        if st.button("🏠 방 꾸미기", use_container_width=True):
            st.session_state.mode = "decorate_room"; st.experimental_rerun()
    with c3:
        with st.expander("📝 오늘의 기분 일기"):
            diary = st.text_area("오늘 있었던 일을 써볼까요? (선택)")
            if st.button("일기 저장 💾"):
                st.session_state.user["diary"].append(diary)
                st.session_state.user["log"].append({"scene":"일기","utter":diary,"feedback":"일기 저장"})
                save_json(USER_FILE, st.session_state.user)
                st.success("저장 완료!")
                tiny_sfx("sound_save.mp3")

    st.markdown("---")
    st.subheader("🌟 시나모롤의 내일 미션")
    if st.button("추천 받기 ✨"):
        # 최근 일기 기반 간단 추천
        diary_text = st.session_state.user["diary"][-1] if st.session_state.user["diary"] else ""
        try:
            prompt = f"""너는 시나모롤이야. 아래는 아이의 최근 일기야.
"{diary_text}"
이 아이가 내일 해보면 좋은 따뜻한 행동 한 가지를 귀엽게 한 문장으로 추천해줘."""
            rsp = client.responses.create(model="gpt-5-mini", input=prompt)
            st.success(f"🌈 내일 미션: {rsp.output_text.strip()}")
        except Exception as e:
            st.error(f"미션 추천 실패: {e}")

# ============ 라우팅 ============
if st.session_state.mode == "main":
    main_mode()
elif st.session_state.mode == "decorate_sky":
    decorate_sky_mode()
elif st.session_state.mode == "decorate_room":
    decorate_room_mode()

st.caption("※ 시나모롤은 Sanrio의 IP입니다. 초기 배포는 유사 감성 캐릭터/아이콘 사용을 권장합니다.")
