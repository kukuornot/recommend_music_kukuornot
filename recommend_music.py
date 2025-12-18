import streamlit as st
from google import genai
from google.genai import types
import os
import json
import urllib.parse

# 1. API 클라이언트 초기화
try:
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    # API 버전을 명시하지 않고 클라이언트를 생성합니다.
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("API 키를 확인해주세요. Streamlit Secrets에 GEMINI_API_KEY가 등록되어 있어야 합니다.")
    st.stop()

def get_recommendation(age: int, preferred_genre: str, language_choice: str):
    genre_prompt = preferred_genre if preferred_genre.strip() else "최신 인기 팝송과 K-POP"
    
    # 프롬프트 설정
    prompt = f"""
    당신은 음악 전문가입니다. {age}세 사용자에게 '{genre_prompt}' 관련 음악 3곡을 추천하세요.
    응답은 반드시 아래 JSON 형식만 반환하세요.
    
    {{
      "recommendations": [
        {{ "title": "곡 제목", "artist": "아티스트", "reason": "추천 이유({language_choice})" }}
      ]
    }}
    """
    
    try:
        # 해결책: 모델 이름을 가장 단순한 'gemini-1.5-flash'로 입력합니다.
        # 만약 이래도 404가 뜨면 'models/gemini-1.5-flash'로 바꿔보세요.
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7
            )
        )
        
        # 결과 텍스트에서 JSON만 추출
        res_text = response.text.strip()
        if "```json" in res_text:
            res_text = res_text.split("```json")[1].split("```")[0].strip()
        elif "```" in res_text:
            res_text = res_text.split("```")[1].split("```")[0].strip()
            
        return json.loads(res_text)
        
    except Exception as e:
        # 에러 메시지를 더 자세히 출력하여 원인을 파악합니다.
        return {"error": f"상세 오류: {str(e)}"}

# --- UI 레이아웃 ---
st.set_page_config(page_title="음악 추천 AI", layout="centered")
st.title("🎶 Gemini 1.5 음악 추천")

age = st.number_input("나이:", min_value=1, max_value=100, value=25)
genre = st.text_input("선호 장르:", value="")
lang = st.selectbox("언어:", ["Korean", "English", "Japanese"])

if st.button("추천받기"):
    with st.spinner("AI 분석 중..."):
        result = get_recommendation(age, genre, lang)
        
        if "error" in result:
            st.error(result["error"])
            st.info("💡 만약 404가 계속 뜨면, Google AI Studio에서 새 API 키를 받아보세요.")
        else:
            for rec in result.get("recommendations", []):
                st.subheader(f"{rec['title']} - {rec['artist']}")
                st.write(rec['reason'])
                q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
                st.markdown(f"[YouTube 검색](https://www.youtube.com/results?search_query={q})")
                st.divider()
