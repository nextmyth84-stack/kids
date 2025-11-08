# -*- coding: utf-8 -*-
# 🩵 Cinnamo World v4.4 — 2D Dialogue Edition
# 아이들이 시나모롤 스타일 캐릭터와 음성으로 대화하며 배우는 감정 놀이

import os, json, random, tempfile
import streamlit as st
from openai import OpenAI
from streamlit_drawable_canvas import st_canvas

# ==============================================
# 🔧 기본 설정
# ==============================================
st.set_page_config(page_title="Cinnamo World", layout="centered")
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))

DATA_DIR = "data"
ASSETS_DIR = "assets"
os.makedirs(DATA_DIR, exist_ok=True)

# 파일 경로
USER_FILE = os.path.join(DATA_DIR, "user_data.json")
SKY_FILE = os.path.join(DATA_DIR, "decorations.json")
ROOM_FILE = os.path.join(DATA_DIR, "room.json")

# ==============================================
# 🎨 CSS (공용)
# ==============================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@700;900&display=swap');
html, body, .stApp {background:linear-gradient(to bottom,#C7EDFF,#FCE6F5);}
*{font-family:'Nunito','NanumSquareRound',sans-serif;}
button[kind="primary"]{
 background:#FFD6EC !important;color:#6B21A8 !important;
 border-radius:16px !important;font-weight:900 !important;
 box-shadow:0 4px 12px rgba(255,192,203,.35);
}
button[kind="primary"]:hover{transform:scale(1.03);}
.progress-cute > div > div{
 background:linear-gradient(90deg,#A5F3FC,#F9A8D4);
 border-radius:999px;
}
</style>
""", unsafe_allow_html=True)

# ==============================================
# ⚙️ 데이터 로드/저장 함수
# ==============================================
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def asset(file):  # 자산 경로
    p = os.path.join(ASSETS_DIR, file)
    return p if os.path.exists(p) else None

# ==============================================
# 🗣️ 음성 인식 + 피드백
# ==============================================
def transcribe_audio(bytes_wav: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(bytes_wav)
        path = tmp.name
    try:
        with open(path, "rb") as f:
            tr = client.audio.transcriptions.create(model="whisper-1", file=f, language="ko")
        return tr.text.strip()
    finally:
        os.remove(path)

def cinnamo_feedback(scene: str, utter: str) -> str:
    sys = ("너는 7세 어린이의 친구인 귀여운 강아지 캐릭터야. "
           "아이의 말을 듣고 다정하고 따뜻하게 한 문장으로 반응해줘. "
           "출력은 시나모롤처럼 귀엽고 짧게, 존댓말로 해줘.")
    user = f"상황: {scene}\n아이가 한 말: {utter}"
    rsp = client.responses.create(model="gpt-5-mini", input=[{"role":"system","content":sys},{"role":"user","content":user}])
    return rsp.output_text.strip()

def tiny_sfx(file):
    path = asset(file)
    if path: st.audio(path, format="audio/mp3")

# ==============================================
# 🩵 메인 대화 화면 (2D 캐릭터 중심)
# ==============================================
def main_mode():
    st.markdown("""
    <style>
    .cinnamo2d{text-align:center;margin-top:-30px;}
    .cinnamo2d img.char{width:240px;animation:float 3s ease-in-out infinite;}
    .bubble2d{
        background:white;border-radius:24px;padding:16px 22px;
        display:inline-block;box-shadow:0 4px 10px rgba(0,0,0,.1);
        font-size:20px;color:#444;margin-top:12px;
    }
    @keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
    </style>
    """, unsafe_allow_html=True)

    if "char_state" not in st.session_state:
        st.session_state.char_state = "normal"

    char_map = {
        "normal": "character_normal.png",
        "happy": "character_happy.png",
        "surprised": "character_surprised.png"
    }

    st.markdown("<div class='cinnamo2d'>", unsafe_allow_html=True)
    st.image(f"assets/{char_map[st.session_state.char_state]}", width=260)
    st.markdown("<div class='bubble2d'>안녕! 나랑 이야기해볼래? ☁️</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🎤 말해볼까?")
    audio = st.audio_input("시나모에게 말해보세요 🎙️")

    if st.button("▶️ 보내기", use_container_width=True):
        if not audio:
            st.warning("먼저 말을 녹음해줘 ☁️")
        else:
            text = transcribe_audio(audio.getvalue())
            fb = cinnamo_feedback("자유 대화", text)

            # 표정 판정
            if any(x in fb for x in ["좋아요","멋져요","잘했어요","행복","사랑","기뻐"]):
                st.session_state.char_state = "happy"
            elif any(x in fb for x in ["놀랐","깜짝","우와","헉"]):
                st.session_state.char_state = "surprised"
            else:
                st.session_state.char_state = "normal"

            st.markdown(f"""
            <div class='cinnamo2d'>
              <img src='assets/{char_map[st.session_state.char_state]}' width='260' class='char'>
              <div class='bubble2d'>💬 {fb}</div>
            </div>
            """, unsafe_allow_html=True)
            tiny_sfx("sound_save.mp3")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("☁️ 하늘 꾸미기"):
            st.session_state.mode = "decorate_sky"; st.experimental_rerun()
    with c2:
        if st.button("🏠 방 꾸미기"):
            st.session_state.mode = "decorate_room"; st.experimental_rerun()

# ==============================================
# ☁️ 하늘 꾸미기
# ==============================================
def decorate_sky_mode():
    st.header("☁️ 하늘 꾸미기")
    prev = load_json(SKY_FILE, {})
    bg_img = asset("bg_sky.png")
    canvas_result = st_canvas(
        fill_color="rgba(255,255,255,0.3)",
        stroke_width=1,
        height=500, width=700,
        drawing_mode="transform",
        key="decorate_sky",
        background_image=bg_img if bg_img else None,
        initial_drawing=prev if prev else None,
    )
    if st.button("💾 저장하기"):
        save_json(SKY_FILE, canvas_result.json_data)
        st.success("하늘이 저장되었어요 ☁️")
        tiny_sfx("sound_save.mp3")

    if st.button("🔙 돌아가기"):
        st.session_state.mode = "main"; st.experimental_rerun()

# ==============================================
# 🏠 방 꾸미기
# ==============================================
def decorate_room_mode():
    st.header("🏠 방 꾸미기")
    prev = load_json(ROOM_FILE, {})
    bg_img = asset("bg_room.png")
    canvas_result = st_canvas(
        fill_color="rgba(255,255,255,0.3)",
        stroke_width=1,
        height=500, width=700,
        drawing_mode="transform",
        key="decorate_room",
        background_image=bg_img if bg_img else None,
        initial_drawing=prev if prev else None,
    )
    if st.button("💾 저장하기"):
        save_json(ROOM_FILE, canvas_result.json_data)
        st.success("방이 저장되었어요 🏠")
        tiny_sfx("sound_save.mp3")

    if st.button("🔙 돌아가기"):
        st.session_state.mode = "main"; st.experimental_rerun()

# ==============================================
# 🚀 실행 (라우팅)
# ==============================================
if "mode" not in st.session_state:
    st.session_state.mode = "main"

if st.session_state.mode == "main":
    main_mode()
elif st.session_state.mode == "decorate_sky":
    decorate_sky_mode()
elif st.session_state.mode == "decorate_room":
    decorate_room_mode()

st.caption("※ 본 프로젝트는 Sanrio와 무관한 교육용 데모입니다.")
