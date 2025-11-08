# -*- coding: utf-8 -*-
# 🩵 Cinnamo World v4.8 — Auto Dialogue Loop Edition
# 시나모가 먼저 말 걸고, 도아가 마이크로 답하면 대화가 자동 이어지는 감정 기반 대화놀이

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


    /* 💫 애니메이션 */
    .emoji {{
        position:fixed;
        bottom:-40px;
        font-size:36px;
        animation:{anim} 6s infinite ease-in-out;
        opacity:0.8;
        z-index:0;
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

    /* 🎙️ 마이크 버튼 */
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
# 📦 유틸
# ==============================================
def tts_ko_bytes(text: str, slow: bool=False) -> bytes:
    t = gTTS(text=text, lang="ko", slow=slow)
    buf = BytesIO()
    t.write_to_fp(buf)
    return buf.getvalue()

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
            f"너는 7세 어린이 '{CHILD_NAME}'의 친구인 귀여운 강아지야. "
            "아이에게 짧고 따뜻하게 말하고, 존댓말을 써줘."},
            {"role":"user","content":prompt}]
    )
    return rsp.output_text.strip()

# ==============================================
# 🩵 메인 모드
# ==============================================
def main_mode():
    if "char_state" not in st.session_state: st.session_state.char_state = "normal"
    if "last_msg" not in st.session_state: st.session_state.last_msg = "안녕 도아! 나랑 이야기해볼래?"
    if "auto_mode" not in st.session_state: st.session_state.auto_mode = True
    if "loop_stage" not in st.session_state: st.session_state.loop_stage = "init"
    set_emotion_bg(st.session_state.char_state)

    char_map = {
        "normal": "character_normal.png",
        "happy": "character_happy.png",
        "surprised": "character_surprised.png"
    }

    # 캐릭터 + 대화 표시
    st.markdown(f"""
    <div style='text-align:center;'>
      <img src='assets/{char_map[st.session_state.char_state]}' width='320'>
      <div style='font-size:22px; background:white; border-radius:20px;
           display:inline-block; padding:14px 24px; box-shadow:0 4px 10px rgba(0,0,0,.1);'>
        💬 {st.session_state.last_msg}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # 시나모가 먼저 말 걸기 (루프 시작)
    if st.session_state.loop_stage == "init":
        msg = "도아야~ 오늘은 어떤 기분이야? 시나모한테 말해볼래?"
        st.session_state.last_msg = msg
        st.session_state.loop_stage = "listen"
        st.audio(tts_ko_bytes(msg, slow=True), format="audio/mp3")

    st.markdown("---")
    st.markdown("<h3 style='text-align:center;'>🎙️ 시나모에게 말해보기</h3>", unsafe_allow_html=True)
    audio = st.audio_input("")

    # 🎙️ 마이크 버튼 표시
    st.markdown("<div class='mic-btn'>🎤</div>", unsafe_allow_html=True)

    if st.button("▶️ 시나모에게 보내기", use_container_width=True):
        if not audio:
            st.warning("먼저 마이크로 도아의 말을 녹음해줘 ☁️")
        else:
            text = transcribe_audio(audio.getvalue())
            fb = cinnamo_speak(f"{CHILD_NAME}가 '{text}' 라고 말했어. 그에 다정하게 반응해줘.")

            # 감정 분석
            if any(x in fb for x in ["좋아요","멋져요","행복","사랑","기뻐"]):
                st.session_state.char_state = "happy"
            elif any(x in fb for x in ["놀랐","깜짝","우와","헉"]):
                st.session_state.char_state = "surprised"
            else:
                st.session_state.char_state = "normal"
            set_emotion_bg(st.session_state.char_state)

            # 시나모 대답 표시 + 음성 출력
            st.session_state.last_msg = fb
            st.markdown(f"""
            <div style='text-align:center;'>
              <img src='assets/{char_map[st.session_state.char_state]}' width='320'>
              <div style='font-size:22px; background:white; border-radius:20px;
                   display:inline-block; padding:14px 24px; box-shadow:0 4px 10px rgba(0,0,0,.1);'>
                💬 {fb}
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.audio(tts_ko_bytes(fb, slow=True), format="audio/mp3")

            # 다음 질문 자동 생성 (루프 지속)
            nxt = cinnamo_speak(f"다음으로 {CHILD_NAME}에게 물어볼 귀여운 질문 하나 만들어줘. "
                                "짧고 따뜻하게, 1문장으로 말해.")
            st.session_state.last_msg = nxt
            st.session_state.loop_stage = "listen"
            st.audio(tts_ko_bytes(nxt, slow=True), format="audio/mp3")
            st.rerun()

# ==============================================
# 🚀 실행
# ==============================================
if "mode" not in st.session_state:
    st.session_state.mode = "main"

if st.session_state.mode == "main":
    main_mode()

st.caption("※ 본 프로젝트는 Sanrio와 무관한 교육용 데모입니다.")
