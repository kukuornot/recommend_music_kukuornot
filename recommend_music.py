import streamlit as st
from groq import Groq
import os
import json
import urllib.parse

# 1. API 클라이언트 초기화
try:
    # Streamlit Secrets에서 GROQ_API_KEY를 가져옵니다.
    api_key = st.secrets.get("GROQ_API_KEY")
    client = Groq(api_key=api_key)
except Exception:
    st.error("GROQ_API_KEY를 설정해주세요.")
    st.stop()

def get_recommendation(age: int, preferred_genre: str, language_choice: str):
    genre_prompt = preferred_genre if preferred_genre.strip() else "최신 인기곡"
    
    # Groq은 Llama 3 모델을 사용하며 JSON 모드를 지원합니다.
    prompt = f"""
    당신은 음악 전문가입니다. {age}세 사용자에게 '{genre_prompt}' 관련 음악 3곡을 추천하세요.
    반드시 JSON 형식으로만 응답하세요.
    
    JSON 형식:
    {{
      "recommendations": [
        {{ "title": "곡 제목", "artist": "아티스트", "reason": "{language_choice}로 작성된 추천 이유" }}
      ]
    }}
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", # 고성능 무료 모델
            response_format={"type": "json_object"}
        )
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        return {"error": f"Groq API 오류: {str(e)}"}

# --- UI 레이아웃 (기존과 동일) ---
st.set_page_config(page_title="음악 추천 AI (Groq)", layout="centered")
st.title("⚡ 초고속 AI 음악 추천")

age = st.number_input("나이:", min_value=1, max_value=100, value=25)
genre = st.text_input("장르/가수:", value="")
lang = st.selectbox("언어:", ["Korean", "English", "Japanese"])

if st.button("추천받기"):
    with st.spinner("AI가 1초 만에 분석 중..."):
        result = get_recommendation(age, genre, lang)
        if "error" in result:
            st.error(result["error"])
        else:
            for rec in result.get("recommendations", []):
                st.subheader(f"{rec['title']} - {rec['artist']}")
                st.write(f"**이유**: {rec['reason']}")
                q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
                st.markdown(f"[▶️ YouTube 검색](https://www.youtube.com/results?search_query={q})")
                st.divider()

