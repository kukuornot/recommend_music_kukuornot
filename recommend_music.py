import streamlit as st
from google import genai
from google.genai import types
import os
import json
import urllib.parse

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
        output_language = "자유"
    else:
        language_instruction = f"추천 이유를 {language_choice}어로 간결하게 설명해 주세요."
        output_language = language_choice
    
    prompt = f"""
    당신은 전문 음악 큐레이터입니다. 
    다음 사용자의 정보를 분석하여 음악 3곡을 추천하고 {language_instruction}
    매번 버튼을 누를 때마다 새로운 곡을 추천하도록 노력하세요.
    
    응답은 반드시 아래 JSON 스키마를 따르는 하나의 JSON 오브젝트여야 합니다. 
    
    사용자 정보:
    - 나이: {age}세
    - 선호 음악: {genre_prompt}
    
    JSON 스키마:
    {{
      "recommendations": [
        {{
          "title": "노래 제목",
          "artist": "아티스트 이름",
          "reason": "추천 이유"
        }}
      ]
    }}
    """
    
    try:
        # 모델명을 가장 기본 형식인 'gemini-1.5-flash'로 설정
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.8
            )
        )
        
        # JSON 응답 정제
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

age = st.number_input("나이를 입력해 주세요:", min_value=1, max_value=100, value=25, step=1)
genre = st.text_input("선호하는 음악 장르를 입력해 주세요  \n(빈 칸은 실시간 인기곡 추천):", value="")

language_full_list = ['선택 안 함', 'Korean', 'English', 'Japanese', 'Chinese']
language_display = {
    'Korean': 'Korean (한국어)', 
    'English': 'English (영어)', 
    'Japanese': 'Japanese (일본어)', 
    'Chinese': 'Chinese (중국어)',
    '선택 안 함': '선택 안 함'
}

selected_language_key = st.selectbox(
    "추천 결과를 보고 싶은 언어를 선택하세요:",
    options=language_full_list,
    format_func=lambda x: language_display[x]
)

if st.button("음악 추천받기 🌟"):
    with st.spinner("Gemini가 새로운 음악을 고르는 중입니다..."):
        data = get_recommendation(age, genre, selected_language_key)
        
        if "error" in data:
            st.error(data["error"])
        else:
            st.success("✅ 추천 완료!")
            if not genre.strip():
                st.subheader("🔥 실시간 인기곡 기반 추천 결과:")
            else:
                st.subheader("🎧 당신을 위한 맞춤 추천 결과:")
                
            for i, rec in enumerate(data.get("recommendations", [])):
                st.markdown(f"### {i+1}. {rec['title']} - {rec['artist']}")
                st.markdown(f"**추천 이유**: {rec['reason']}")
                
                search_query = f"{rec['title']} {rec['artist']}"
                encoded_query = urllib.parse.quote_plus(search_query)
                youtube_link = f"https://www.youtube.com/results?search_query={encoded_query}"
                
                st.markdown(f"[▶️ YouTube에서 음악 듣기]({youtube_link})")
                st.divider()
