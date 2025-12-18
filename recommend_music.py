import streamlit as st
from google import genai
from google.genai import types
import os
import json
import urllib.parse

# 1. API 클라이언트 초기화
try:
    # Streamlit Secrets 또는 환경 변수에서 키를 가져옵니다.
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("API 키를 찾을 수 없습니다. Streamlit Cloud의 Settings > Secrets에서 GEMINI_API_KEY를 설정해주세요.")
    st.stop()

def get_recommendation(age: int, preferred_genre: str, language_choice: str):
    # 장르 기본값 설정
    genre_prompt = preferred_genre if preferred_genre.strip() else "현재 전 세계적으로 가장 인기 있는 음악"
    
    # 언어 설정 지침
    if language_choice == "선택 안 함":
        lang_instruction = "추천 이유를 가장 적절한 언어로 작성해 주세요."
    else:
        lang_instruction = f"추천 이유를 반드시 {language_choice}어로 상세히 작성해 주세요."
    
    # 프롬프트 작성
    prompt = f"""
    당신은 전문 음악 큐레이터입니다. {age}세 사용자를 위해 '{genre_prompt}' 장르의 음악 3곡을 추천하세요.
    매번 버튼을 누를 때마다 다른 곡을 추천하도록 노력하세요.
    
    응답은 반드시 아래 JSON 스키마를 따르는 하나의 JSON 오브젝트여야 합니다. 
    다른 텍스트를 포함하지 말고 오직 JSON만 반환하세요.
    
    JSON 스키마:
    {{
      "recommendations": [
        {{
          "title": "노래 제목",
          "artist": "아티스트 이름",
          "reason": "{lang_instruction}"
        }}
      ]
    }}
    """
    
    try:
        # 핵심 해결책: 2.0 대신 가장 안정적인 1.5-flash 모델 사용
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.8
            )
        )
        
        # JSON 데이터 추출 및 정제
        raw_text = response.text.strip()
        if '```json' in raw_text:
            raw_text = raw_text.split('```json')[1].split('```')[0].strip()
        elif '```' in raw_text:
            raw_text = raw_text.split('```')[1].split('```')[0].strip()

        return json.loads(raw_text)
        
    except Exception as e:
        # 오류 메시지를 사용자 친화적으로 변경
        error_msg = str(e)
        if "429" in error_msg:
            return {"error": "현재 Google API 할당량이 초과되었습니다. 잠시 후(약 1분 뒤) 다시 시도하거나, 다른 구글 계정의 API 키를 사용해 보세요."}
        return {"error": f"추천을 가져오는 중 오류가 발생했습니다: {e}"}

# --- 스트림릿 UI 레이아웃 ---
st.set_page_config(page_title="🎶 AI 음악 추천 시스템", layout="centered")

st.title("🎵 개인 맞춤형 음악 추천 AI")
st.markdown("당신의 나이와 취향에 딱 맞는 음악을 Gemini AI가 골라드립니다.")

# 입력 섹션
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("나이를 입력하세요:", min_value=1, max_value=100, value=25)
    with col2:
        language_list = ['Korean', 'English', 'Japanese', 'Chinese', '선택 안 함']
        selected_lang = st.selectbox("추천 이유 언어:", options=language_list)

    genre = st.text_input("좋아하는 장르나 아티스트를 입력하세요 (예: 재즈, 뉴진스):", value="")

st.divider()

# 추천 버튼
if st.button("음악 추천받기 🌟", use_container_width=True):
    with st.spinner("AI가 당신을 위한 최적의 음악을 찾는 중입니다..."):
        data = get_recommendation(age, genre, selected_lang)
        
        if "error" in data:
            st.error(data["error"])
            # 비상 안내
            st.info("💡 429 오류가 계속된다면, 학교 Wi-Fi나 휴대폰 핫스팟 등 다른 네트워크를 사용해 보세요.")
        else:
            st.success("✅ 추천 결과가 도착했습니다!")
            
            for i, rec in enumerate(data.get("recommendations", [])):
                with st.expander(f"{i+1}. {rec['title']} - {rec['artist']}", expanded=True):
                    st.write(f"**💡 추천 이유**: {rec['reason']}")
                    
                    # 유튜브 검색 링크 생성
                    query = f"{rec['title']} {rec['artist']}"
                    encoded_query = urllib.parse.quote_plus(query)
                    yt_url = f"https://www.youtube.com/results?search_query={encoded_query}"
                    
                    st.markdown(f"[▶️ YouTube에서 감상하기]({yt_url})")

st.caption("© 2025 AI Music Curator Project. Powered by Gemini 1.5 Flash.")
