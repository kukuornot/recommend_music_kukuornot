import streamlit as st
from openai import OpenAI
import os
import json
import urllib.parse

# 1. API 클라이언트 초기화
try:
    # Streamlit Secrets에서 OPENAI_API_KEY를 가져옵니다.
    api_key = st.secrets.get("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
except Exception:
    st.error("OpenAI API 키를 확인해주세요. Secrets에 OPENAI_API_KEY가 등록되어야 합니다.")
    st.stop()

def get_recommendation(age: int, preferred_genre: str, language_choice: str):
    genre_prompt = preferred_genre if preferred_genre.strip() else "최신 인기곡"
    
    prompt = f"""
    당신은 음악 전문가입니다. {age}세 사용자에게 '{genre_prompt}' 관련 음악 3곡을 추천하세요.
    결과는 반드시 JSON 형식으로만 응답하세요.
    
    JSON 형식:
    {{
      "recommendations": [
        {{ "title": "곡 제목", "artist": "아티스트", "reason": "{language_choice}로 작성된 추천 이유" }}
      ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 가장 빠르고 저렴하며 안정적인 모델
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" } # JSON 출력을 보장합니다
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        return {"error": f"API 호출 중 오류 발생: {str(e)}"}

# --- UI 레이아웃 ---
st.set_page_config(page_title="음악 추천 AI (OpenAI)", layout="centered")
st.title("🎵 AI 기반 음악 추천")

age = st.number_input("나이:", min_value=1, max_value=100, value=25)
genre = st.text_input("선호 장르/가수:", value="")
lang = st.selectbox("언어:", ["Korean", "English", "Japanese"])

if st.button("추천받기 ✨"):
    with st.spinner("AI가 음악을 고르는 중..."):
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

