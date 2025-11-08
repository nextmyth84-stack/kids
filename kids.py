# -*- coding: utf-8 -*-
# 🩵 Cinnamo World v5.0 — OpenAI TTS (부드러운 시나모 목소리)
# 귀여운 시나모 캐릭터가 도아와 대화하며 자연스러운 음성으로 말하는 버전

import os, json, tempfile, time
from io import BytesIO
import streamlit as st
from openai import OpenAI

# ==============================================
# ⚙️ 기본 설정
# ==============================================
st.set_page_config(page_title="Cinnamo World", layout="centered")
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))

CHILD_NAME = "도아"
ASSETS_DIR = "assets"
os.makedirs(ASSETS_DIR, exist_ok=True)

# ==============================================
# 🎨 감정별 배경 + 애니메이션
# ==============================================
def set_emotion_bg(state: str):
    if state == "happy":
        color = "#FFE6F1"; symbol = "💗"; anim = "floatUp"
    elif state == "surprised":
        color = "#C7EDFF"; symbol = "✨"; anim = "blink"
    else:
        color = "#EDE7FF"; symbol = "☁️"; anim = "drift"

    st.markdown(f"""
    <style>
    html, body, .stApp {{
        background:{color};
        transition:background-color 0.8s ease;
        overflow:hidden;
    }}
    *{{font-family:'NanumSquareRound','Nunito',sans-serif;}}
    button[kind="primary"]{{
        background:#FFD6EC !important;color:#6B21A8 !important;
        border-radius:16px !important;font-weight:900 !important;
        box-shadow:0 4px 12px rgba(255,192,203,.35);
    }}
    .emoji {{
        position:fixed;
        bottom:-40px;
        font-size:36px;
        animation:{anim} 6s infinite ease-in-out;
        opacity:0.8; z-index:0;
    }}
    @keyframes floatUp {{
        0% {{transform:translateY(0); opacity:0;}}
        30% {{opacity:1;}}
        70% {{transform:translateY(-600px); opacity:1;}}
        100% {{opacity:0; transform:translateY(-800px);}}
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
    .mic-btn {{
        width:120px; height:120px;
        background:#FFCCE5; border-radius:60px;
        display:flex; justify-content:center; align-items:center;
        margin:20px auto; cursor:pointer;
        box-shadow:0 4px 12px rgba(0,0,0,0.15);
        font-size:48px;
        transition:transform .2s;
    }}
    .mic-btn:hover {{ transform:scale(1.05); background:#FFBBDD; }}
    </style>
    <div class="emoji" style="left:20%">{symbol}</div>
    <div class="emoji" style="left:50%">{symbol}</div>
    <div class="emoji" style="left:80%">{symbol}</div>
    """, unsafe_allow_html=True)

# ==============================================
# 🔊 OpenAI 부드러운 TTS
# ==============================================
def tts_ko_bytes(text: str, voice="soft", model="gpt-4o-mini-tts") -> bytes:
    """OpenAI TTS - 부드럽고 따뜻한 시나모 목소리"""
    speech = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text
    )
    return speech.read()

# ==============================================
# 🎤 음성 인식 + GPT 반응
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

def cinnamo_speak(prompt: str) -> str:
    rsp = client.responses.create(model="gpt-5-mini",
        input=[{"role":"system","content":
            f"너는 7세 어린이 '{CHILD_NAME}'의 친구인 부드러운 목소리의 강아지야. "
            "아이에게 따뜻하고 다정하게 한 문장으로만 대답해."},
            {"role":"user","content":prompt}]
    )
    return rsp.output_text.strip()

# ==============================================
# 👄 입 움직임 애니메이션
# ==============================================
def cinnamo_speaking_animation(state: str, duration: float = 3.5):
    normal_img = os.path.join(ASSETS_DIR, f"character_{state}.png")
    speak_img = os.path.join(ASSETS_DIR, f"character_{state}_speaking.png")

    if not os.path.exists(speak_img):
        st.image(normal_img, width=320)
        return

    end = time.time() + duration
    ph = st.empty()
    while time.time() < end:
        ph.image(speak_img, width=320)
        time.sleep(0.22)
        ph.image(normal_img, width=320)
        time.sleep(0.25)
    ph.image(normal_img, width=320)

# ==============================================
# 🩵 메인 대화 모드
# ==============================================
def main_mode():
    if "char_state" not in st.session_state:
        st.session_state.char_state = "normal"
    if "last_msg" not in st.session_state:
        st.session_state.last_msg = "안녕 도아! 나랑 이야기해볼래?"
    if "loop_stage" not in st.session_state:
        st.session_state.loop_stage = "init"

    set_emotion_bg(st.session_state.char_state)
    state = st.session_state.char_state

    char_map = {
        "normal": "character_normal.png",
        "happy": "character_happy.png",
        "surprised": "character_surprised.png"
    }

    st.markdown(f"""
    <div style='text-align:center;'>
      <img src='assets/{char_map[state]}' width='320'>
      <div style='font-size:22px; background:white; border-radius:20px;
           display:inline-block; padding:14px 24px; box-shadow:0 4px 10px rgba(0,0,0,.1);'>
        💬 {st.session_state.last_msg}
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.loop_stage == "init":
        msg = "도아야~ 오늘 기분은 어때? 시나모한테 말해볼래?"
        st.session_state.last_msg = msg
        st.session_state.loop_stage = "listen"
        with st.empty():
            cinnamo_speaking_animation("normal", 3.5)
        st.audio(tts_ko_bytes(msg), format="audio/mp3")

    st.markdown("---")
    st.markdown("<h3 style='text-align:center;'>🎙️ 시나모에게 말해보기</h3>", unsafe_allow_html=True)
    st.markdown("<div class='mic-btn'>🎤</div>", unsafe_allow_html=True)
    audio = st.audio_input("")

    if st.button("▶️ 시나모에게 보내기", use_container_width=True):
        if not audio:
            st.warning("먼저 도아의 말을 녹음해줘 ☁️")
        else:
            text = transcribe_audio(audio.getvalue())
            fb = cinnamo_speak(f"{CHILD_NAME}가 '{text}' 라고 말했어. 그에 다정하게 반응해줘.")

            if any(x in fb for x in ["좋아요","멋져요","행복","사랑","기뻐"]):
                state = "happy"
            elif any(x in fb for x in ["놀랐","깜짝","우와","헉"]):
                state = "surprised"
            else:
                state = "normal"
            st.session_state.char_state = state

            set_emotion_bg(state)
            with st.empty():
                cinnamo_speaking_animation(state, 3.5)
            st.audio(tts_ko_bytes(fb), format="audio/mp3")

            nxt = cinnamo_speak(f"다음으로 {CHILD_NAME}에게 귀여운 질문 하나 만들어줘. 짧고 따뜻하게 1문장으로.")
            st.session_state.last_msg = nxt
            with st.empty():
                cinnamo_speaking_animation(state, 3.5)
            st.audio(tts_ko_bytes(nxt), format="audio/mp3")

            st.markdown(f"""
            <div style='text-align:center; margin-top:10px;'>
              <div style='font-size:22px; background:white; border-radius:20px;
                   display:inline-block; padding:14px 24px; box-shadow:0 4px 10px rgba(0,0,0,.1);'>
                💬 {nxt}
              </div>
            </div>
            """, unsafe_allow_html=True)

# ==============================================
# 🚀 실행
# ==============================================
if "mode" not in st.session_state:
    st.session_state.mode = "main"

if st.session_state.mode == "main":
    main_mode()

st.caption("※ 본 프로젝트는 Sanrio와 무관한 교육용 데모입니다.")
