import streamlit as st
from google import genai
from google.genai import types
import os
import json
import urllib.parse

# 1. 클라이언트 초기화
try:
    # Streamlit Secrets 또는 환경 변수에서 키 로드
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("Gemini API 키가 설정되지 않았습니다. Manage app -> Settings -> Secrets를 확인해 주세요.")
    st.stop()

def get_recommendation(age: int, preferred_genre: str, language_choice: str):
    # 장르 미입력 처리
    genre_prompt = preferred_genre if preferred_genre.strip() else "전 세계 실시간 인기곡 (Trending now)"
    
    # 언어 지침 설정
    if language_choice == "선택 안 함":
        lang_instruction = "언어에 상관없이 가장 적절한 언어로 추천 이유를 작성하세요."
    else:
        lang_instruction = f"추천 이유를 반드시 {language_choice}어로 작성하세요."
    
    # 프롬프트 구성
    prompt = f"""
    당신은 음악 전문가입니다. {age}세 사용자를 위해 '{genre_prompt}' 관련 음악 3곡을 추천하세요.
    
    조건:
    1. {lang_instruction}
    2. 결과는 반드시 아래 JSON 형식만 반환하세요.
    
    JSON 형식:
    {{
      "recommendations": [
        {{ "title": "곡 제목", "artist": "아티스트", "reason": "추천 이유" }}
      ]
    }}
    """
    
    try:
        # 모델명을 gemini-2.0-flash로 설정
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7 # 너무 높으면 할당량 소모가 빠를 수 있어 약간 낮춤
            )
        )
        
        # JSON 텍스트 정제
        raw_text = response.text.strip()
        if '```json' in raw_text:
            raw_text = raw_text.split('```json')[1].split('```')[0].strip()
        elif '```' in raw_text:
            raw_text = raw_text.split('```')[1].split('```')[0].strip()

        return json.loads(raw_text)
        
    except Exception as e:
        # 429 오류(할당량 초과) 발생 시 사용자에게 안내
        if "429" in str(e):
            return {"error": "현재 사용자가 많아 할당량이 초과되었습니다. 1분 후 다시 시도해 주세요."}
        return {"error": f"오류 발생: {e}"}

# --- UI 레이아웃 ---
st.set_page_config(page_title="🎶 AI 음악 추천 시스템", layout="centered")
st.title("🎵 음악 추천 AI")

age = st.number_input("나이를 입력하세요:", min_value=1, max_value=100, value=25)
genre = st.text_input("선호 장르 (빈 칸은 인기곡 추천):", value="")
language_list = ['선택 안 함', 'Korean', 'English', 'Japanese', 'Chinese']
selected_lang = st.selectbox("언어 선택:", options=language_list)

if st.button("음악 추천받기 🌟"):
    with st.spinner("Gemini 2.0이 음악을 분석 중입니다..."):
        data = get_recommendation(age, genre, selected_lang)
        
        if "error" in data:
            st.error(data["error"])
        else:
            st.success("✅ 추천 완료!")
            for i, rec in enumerate(data.get("recommendations", [])):
                st.markdown(f"### {i+1}. {rec['title']} - {rec['artist']}")
                st.write(f"**이유**: {rec['reason']}")
                query = urllib.parse.quote_plus(f"{rec['title']} {rec['artist']}")
                st.markdown(f"[▶️ YouTube에서 보기](https://www.youtube.com/results?search_query={query})")
                st.divider()

