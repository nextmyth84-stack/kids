# -*- coding: utf-8 -*-
# 🩵 Cinnamo Kids EDU v6.0 — 예절놀이 기본 구조
# 주제 선택 → 상황 제시 → 도아 대답 → 시나모 칭찬 → 하트 보상

import json, os, random, tempfile, time
import streamlit as st
from openai import OpenAI
from io import BytesIO

st.set_page_config(page_title="시나모 예절놀이", layout="centered")
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))
ASSETS_DIR = "assets"
SCENARIO_PATH = os.path.join(ASSETS_DIR, "scenarios.json")
CHILD_NAME = "도아"

# ----------------------------
# 데이터 로드
# ----------------------------
with open(SCENARIO_PATH, "r", encoding="utf-8") as f:
    SCENARIOS = json.load(f)

# ----------------------------
# 함수
# ----------------------------
def tts_ko_bytes(text, voice="verse"):
    speech = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=text
    )
    return speech.read()

def transcribe_audio(bytes_wav):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(bytes_wav)
        path = tmp.name
    with open(path, "rb") as f:
        tr = client.audio.transcriptions.create(model="whisper-1", file=f, language="ko")
    os.remove(path)
    return tr.text.strip()

def get_praise(topic):
    return random.choice(SCENARIOS[topic]["praise"])

def match_answer(topic, user_text):
    valid = SCENARIOS[topic]["answers"]
    return any(word in user_text for word in valid)

# ----------------------------
# 메인 로직
# ----------------------------
st.title("🐶 시나모와 예쁜 마음 배우기")

if "hearts" not in st.session_state:
    st.session_state.hearts = 0

topic = st.selectbox("오늘은 어떤 마음을 배워볼까?", list(SCENARIOS.keys()))
situation = SCENARIOS[topic]["situation"]

st.markdown(f"### 🌸 상황: {situation}")
st.audio(tts_ko_bytes(situation), format="audio/mp3")

st.markdown("---")
st.markdown("🎙️ 도아야, 뭐라고 말할까?")
audio = st.audio_input("")

if st.button("▶️ 시나모에게 대답 보내기", use_container_width=True):
    if not audio:
        st.warning("먼저 말을 녹음해줘 ☁️")
    else:
        text = transcribe_audio(audio.getvalue())
        st.markdown(f"🗣️ 도아: {text}")

        if match_answer(topic, text):
            praise = get_praise(topic)
            st.session_state.hearts += 1
            st.success(f"💗 시나모: {praise}")
            st.audio(tts_ko_bytes(praise), format="audio/mp3")
        else:
            fb = f"시나모: 흠~ 조금 다르게 말해볼까? 예를 들어 '{SCENARIOS[topic]['answers'][0]}' 라고 해볼래?"
            st.info(fb)
            st.audio(tts_ko_bytes(fb), format="audio/mp3")

st.markdown("---")
st.markdown(f"❤️ 하트 개수: **{st.session_state.hearts}**")
