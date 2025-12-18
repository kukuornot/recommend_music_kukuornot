import streamlit as st
from google import genai
from google.genai import types
import os
import json
import urllib.parse

# 1. API 클라이언트 초기화
try:
    # Streamlit Secrets 또는 환경 변수에서 키를 로드합니다.
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("API 키를 찾을 수 없습니다. Streamlit Cloud의 Settings > Secrets에서 GEMINI_API_KEY를 설정해주세요.")
    st.stop()

def get_recommendation(age: int, preferred_genre: str, language_choice: str):
    genre_prompt = preferred_genre if preferred_genre.strip() else "현재 전 세계적으로 가장 인기 있는 음악"
    
    if language_choice == "선택 안 함":
        lang_instruction = "추천 이유를 가장 적절한 언어로 작성해 주세요."
    else:
        lang_instruction = f"추천 이유를 반드시 {language_choice}어로 상세히 작성해 주세요."
    
    prompt = f"""
    당신은 전문 음악 큐레이터입니다. {age}세 사용자를 위해 '{genre_prompt}' 관련 음악 3곡을 추천하고 {lang_instruction}
    매번 버튼을 누를 때마다 새로운 곡을 추천하도록 노력하세요.
    
    응답은 반드시 아래 JSON 스키마를 따르는 하나의 JSON 오브젝트여야 합니다. 
    다른 텍스트를 포함하지 말고 오직 JSON만 반환하세요.
    
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
        # 오류 해결의 핵심: 모델명을 'gemini-1.5-flash'로 명확히 설정합니다.
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.8
            )
        )
        
        # JSON 응답 정제 (마크다운 코드 블록 제거)
        raw_text = response.text.strip()
        if '```json' in raw_text:
            raw_text = raw_text.split('```json')[1].split('```')[0].strip()
        elif '```' in raw_text:
            raw_text = raw_text.split('```')[1].split('```')[0].strip()

        return json.loads(raw_text)
        
    except Exception as e:
        return {"error": f"추천을 가져오는 중 오류가 발생했습니다: {e}"}

# --- 스트림릿 UI 레이아웃 ---
st.set_page_config(page_title="🎶 AI 음악 추천 시스템", layout="centered")
st.title("🎵 음악 추천 AI")
st.markdown("나이와 선호 장르를 입력하고 추천 언어를 선택해 보세요.")

age = st.number_input("나이를 입력해 주세요:", min_value=1, max_value=100, value=25, step=1)
genre = st.text_input("선호하는 음악 장르를 입력해 주세요 (빈 칸은 인기곡 추천):", value="")

language_list = ['Korean', 'English', 'Japanese', 'Chinese', '선택 안 함']
selected_lang = st.selectbox("추천 결과를 보고 싶은 언어를 선택하세요:", options=language_list)

if st.button("음악 추천받기 🌟"):
    with st.spinner("AI가 음악을 고르는 중입니다..."):
        data = get_recommendation(age, genre, selected_lang)
        
        if "error" in data:
            st.error(data["error"])
        else:
            st.success("✅ 추천 완료!")
            for i, rec in enumerate(data.get("recommendations", [])):
                st.markdown(f"### {i+1}. {rec['title']} - {rec['artist']}")
                st.write(f"**추천 이유**: {rec['reason']}")
                
                # 유튜브 검색 링크
                query = urllib.parse.quote_plus(f"{rec['title']} {rec['artist']}")
                st.markdown(f"[▶️ YouTube에서 보기](https://www.youtube.com/results?search_query={query})")
                st.divider()
