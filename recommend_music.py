import streamlit as st
from google import genai
from google.genai import types
import os
import json
import urllib.parse

# 1. 클라이언트 초기화
try:
    api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("Gemini API 키를 설정해주세요. (로컬: 환경변수 / 배포: Streamlit Secrets)")
    st.stop()

def get_recommendation(age: int, preferred_genre: str, language_choice: str):
    genre_prompt = preferred_genre if preferred_genre.strip() else "전 세계적으로 실시간 인기가 많은 곡"
    
    if language_choice == "선택 안 함":
        language_instruction = "추천 이유를 가장 적절한 언어로 작성해 주세요."
    else:
        language_instruction = f"추천 이유를 {language_choice}어로 작성해 주세요."
    
    prompt = f"""
    당신은 음악 전문가입니다. {age}세 사용자를 위해 {genre_prompt} 장르의 음악 3곡을 추천하세요.
    응답은 반드시 아래 JSON 스키마를 따르는 하나의 JSON 오브젝트여야 하며, 다른 설명 텍스트는 포함하지 마세요.
    
    JSON 스키마:
    {{
      "recommendations": [
        {{ "title": "제목", "artist": "아티스트", "reason": "{language_instruction}" }}
      ]
    }}
    """
    
    try:
        # 오류 해결의 핵심: 모델명을 'models/gemini-1.5-flash'로 전체 경로 명시
        response = client.models.generate_content(
            model='models/gemini-1.5-flash', 
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7
            )
        )
        
        # JSON 텍스트 추출 로직 강화
        raw_text = response.text.strip()
        if '```json' in raw_text:
            raw_text = raw_text.split('```json')[1].split('```')[0].strip()
        elif '```' in raw_text:
            raw_text = raw_text.split('```')[1].split('```')[0].strip()

        return json.loads(raw_text)
        
    except Exception as e:
        return {"error": f"추천을 가져오는 중 오류가 발생했습니다: {e}"}

# --- UI 레이아웃 ---
st.set_page_config(page_title="🎶 AI 음악 추천 시스템", layout="centered")
st.title("🎵 음악 추천 AI")
st.markdown("나이와 선호 장르를 입력하고 추천 언어를 선택해 보세요.")

age = st.number_input("나이를 입력해 주세요:", min_value=1, max_value=100, value=25)
genre = st.text_input("선호하는 음악 장르를 입력해 주세요  \n(빈 칸은 실시간 인기곡 추천):", value="")

language_display = {
    'Korean': 'Korean (한국어)', 'English': 'English (영어)', 
    'Japanese': 'Japanese (일본어)', 'Chinese': 'Chinese (중국어)', '선택 안 함': '선택 안 함'
}
selected_language = st.selectbox("추천 언어 선택:", options=list(language_display.keys()), format_func=lambda x: language_display[x])

if st.button("음악 추천받기 🌟"):
    with st.spinner("음악을 고르는 중입니다..."):
        data = get_recommendation(age, genre, selected_language)
        
        if "error" in data:
            st.error(data["error"])
        else:
            st.success("✅ 추천 완료!")
            for i, rec in enumerate(data.get("recommendations", [])):
                st.markdown(f"### {i+1}. {rec['title']} - {rec['artist']}")
                st.write(f"**이유**: {rec['reason']}")
                query = urllib.parse.quote_plus(f"{rec['title']} {rec['artist']}")
                st.markdown(f"[▶️ YouTube에서 듣기](https://www.youtube.com/results?search_query={query})")
                st.divider()
