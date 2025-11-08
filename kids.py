# -*- coding: utf-8 -*-
# 🩵 Cinnamo World v4.7 — Emotion & TTS Edition
# 시나모롤 감성의 강아지가 도아와 음성으로 대화하며 감정에 따라 배경이 변하는 교육용 대화놀이

import os, json, tempfile
from io import BytesIO
import streamlit as st
from openai import OpenAI
from gtts import gTTS
from streamlit_drawable_canvas import st_canvas

# ==============================================
# ⚙️ 기본 설정
# ==============================================
st.set_page_config(page_title="Cinnamo World", layout="centered")
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))

CHILD_NAME = "도아"
DATA_DIR = "data"
ASSETS_DIR = "assets"
os.makedirs(DATA_DIR, exist_ok=True)

# ==============================================
# 🎨 감정별 배경 + 애니메이션
# ==============================================
def set_emotion_bg(state: str):
    """감정 상태에 따라 배경색 + 애니메이션 지정"""
    if state == "happy":
        color = "#FFE6F1"
        symbol = "💗"
        anim = "floatUp"
    elif state == "surprised":
        color = "#C7EDFF"
        symbol = "✨"
        anim = "blink"
    else:
        color = "#EDE7FF"
        symbol = "☁️"
        anim = "drift"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@700;900&display=swap');

    html, body, .stApp {{
        background:{color};
        transition:background-color 0.8s ease;
        overflow:hidden;
    }}

    *{{font-family:'Nunito','NanumSquareRound',sans-serif;}}

    button[kind="primary"]{{
        background:#FFD6EC !important;color:#6B21A8 !important;
        border-radius:16px !important;font-weight:900 !important;
        box-shadow:0 4px 12px rgba(255,192,203,.35);
    }}
    button[kind="primary"]:hover{{transform:scale(1.03);}}


    /* 💫 떠오르는 이모지 애니메이션 */
    .emoji {{
        position:fixed;
        bottom:-40px;
        font-size:36px;
        animation:{anim} 6s infinite ease-in-out;
        opacity:0.8;
        z-index:0;
    }}

    @keyframes floatUp {{
        0% {{transform:translateY(0) scale(0.8); opacity:0;}}
        30% {{opacity:1;}}
        70% {{opacity:1; transform:translateY(-600px) scale(1.2);}}
        100% {{opacity:0; transform:translateY(-800px) scale(1.3);}}
    }}
    @keyframes blink {{
        0%,100% {{opacity:0;}}
        50% {{opacity:1; transform:scale(1.3);}}
    }}
    @keyframes drift {{
        0% {{transform:translateX(-100px); opacity:0.6;}}
        50% {{transform:translateX(100px); opacity:0.8;}}
        100% {{transform:translateX(-100px); opacity:0.6;}}
    }}
    </style>

    <div class="emoji" style="left:20%">{symbol}</div>
    <div class="emoji" style="left:50%">{symbol}</div>
    <div class="emoji" style="left:80%">{symbol}</div>
    """, unsafe_allow_html=True)

# ==============================================
# 📦 유틸
# ==============================================
def asset(name):
    path = os.path.join(ASSETS_DIR, name)
    return path if os.path.exists(path) else None

def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==============================================
# 🎤 음성 인식 + GPT 피드백
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
    sys = (f"너는 7세 어린이 '{CHILD_NAME}'의 친구인 귀여운 강아지 캐릭터야. "
           "아이의 말을 듣고 따뜻하게 한 문장으로 반응해줘. "
           "출력은 항상 '{CHILD_NAME}야, ~'로 시작하고, 시나모롤처럼 짧고 다정하게 말해줘.")
    user = f"상황: {scene}\n아이가 한 말: {utter}"
    rsp = client.responses.create(model="gpt-5-mini",
                                  input=[{"role":"system","content":sys},
                                         {"role":"user","content":user}])
    return rsp.output_text.strip()

# ==============================================
# 🔊 TTS (gTTS 캐시)
# ==============================================
@st.cache_data(show_spinner=False)
def tts_ko_bytes(text: str, slow: bool=False) -> bytes:
    t = gTTS(text=text, lang="ko", slow=slow)
    buf = BytesIO()
    t.write_to_fp(buf)
    return buf.getvalue()

# ==============================================
# 🩵 메인 대화 모드
# ==============================================
def main_mode():
    # 초기화
    if "char_state" not in st.session_state:
        st.session_state.char_state = "normal"
    if "char_size" not in st.session_state:
        st.session_state.char_size = 320
    if "tts_on" not in st.session_state:
        st.session_state.tts_on = True
    if "tts_slow" not in st.session_state:
        st.session_state.tts_slow = False

    # 감정 배경 적용
    set_emotion_bg(st.session_state.char_state)

    # 컨트롤 UI
    c1, c2, c3 = st.columns([2,1,1])
    with c1:
        st.session_state.char_size = st.slider("캐릭터 크기", 220, 440, st.session_state.char_size, step=10)
    with c2:
        st.session_state.tts_on = st.toggle("시나모 목소리", value=st.session_state.tts_on)
    with c3:
        st.session_state.tts_slow = st.toggle("느리게", value=st.session_state.tts_slow)

    # 캐릭터 표시
    char_map = {
        "normal": "character_normal.png",
        "happy": "character_happy.png",
        "surprised": "character_surprised.png"
    }

    st.markdown("<div style='text-align:center;margin-top:-25px;'>", unsafe_allow_html=True)
    st.image(f"assets/{char_map[st.session_state.char_state]}",
             width=st.session_state.char_size)
    st.markdown(f"<div style='font-size:22px; background:white; "
                "display:inline-block; padding:14px 24px; border-radius:20px; "
                "box-shadow:0 4px 10px rgba(0,0,0,.1);'>"
                f"안녕 {CHILD_NAME}! 나랑 이야기해볼래? ☁️</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 인사 TTS
    if st.session_state.tts_on:
        try:
            st.audio(tts_ko_bytes(f"안녕 {CHILD_NAME}! 나랑 이야기해볼래?", slow=True), format="audio/mp3")
        except:
            pass

    st.markdown("---")
    st.subheader("🎤 말해볼까?")
    audio = st.audio_input(f"{CHILD_NAME}가 시나모에게 말해보세요 🎙️")

    if st.button("▶️ 보내기", use_container_width=True):
        if not audio:
            st.warning("먼저 말을 녹음해줘 ☁️")
        else:
            text = transcribe_audio(audio.getvalue())
            fb = cinnamo_feedback("자유 대화", text)

            # 감정 상태 업데이트
            if any(x in fb for x in ["좋아요","멋져요","잘했어요","행복","사랑","기뻐"]):
                st.session_state.char_state = "happy"
            elif any(x in fb for x in ["놀랐","깜짝","우와","헉"]):
                st.session_state.char_state = "surprised"
            else:
                st.session_state.char_state = "normal"

            set_emotion_bg(st.session_state.char_state)

            st.markdown(f"""
            <div style='text-align:center;'>
              <img src='assets/{char_map[st.session_state.char_state]}' 
                   width='{st.session_state.char_size}'>
              <div style='font-size:22px; background:white; border-radius:20px;
                   display:inline-block; padding:14px 24px; box-shadow:0 4px 10px rgba(0,0,0,.1);'>
                💬 {fb}
              </div>
            </div>
            """, unsafe_allow_html=True)

            # TTS 재생
            if st.session_state.tts_on:
                try:
                    mp3_bytes = tts_ko_bytes(fb, slow=st.session_state.tts_slow)
                    st.audio(mp3_bytes, format="audio/mp3")
                except Exception as e:
                    st.warning(f"TTS 오류: {e}")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("☁️ 하늘 꾸미기"):
            st.session_state.mode = "decorate_sky"; st.experimental_rerun()
    with c2:
        if st.button("🏠 방 꾸미기"):
            st.session_state.mode = "decorate_room"; st.experimental_rerun()

# ==============================================
# ☁️ 하늘 / 🏠 방 꾸미기
# ==============================================
def decorate_sky_mode():
    st.header("☁️ 하늘 꾸미기")
    prev = load_json(os.path.join(DATA_DIR,"decorations.json"), {})
    bg = asset("bg_sky.png")
    result = st_canvas(height=500, width=700,
                       drawing_mode="transform",
                       background_image=bg if bg else None,
                       initial_drawing=prev)
    if st.button("💾 저장하기"):
        save_json(os.path.join(DATA_DIR,"decorations.json"), result.json_data)
        st.success("하늘이 저장되었어요 ☁️")
    if st.button("🔙 돌아가기"):
        st.session_state.mode = "main"; st.experimental_rerun()

def decorate_room_mode():
    st.header("🏠 방 꾸미기")
    prev = load_json(os.path.join(DATA_DIR,"room.json"), {})
    bg = asset("bg_room.png")
    result = st_canvas(height=500, width=700,
                       drawing_mode="transform",
                       background_image=bg if bg else None,
                       initial_drawing=prev)
    if st.button("💾 저장하기"):
        save_json(os.path.join(DATA_DIR,"room.json"), result.json_data)
        st.success("방이 저장되었어요 🏠")
    if st.button("🔙 돌아가기"):
        st.session_state.mode = "main"; st.experimental_rerun()

# ==============================================
# 🚀 실행
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
