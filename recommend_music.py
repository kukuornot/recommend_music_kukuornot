import streamlit as st
import google.generativeai as genai
import os
import json
import urllib.parse

# 1. API 클라이언트 설정
try:
    api_key = st.secrets.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"초기화 오류: {e}")
    st.stop()

def get_recommendation(user_age: int, preferred_genre: str, language_choice: str):
    genre_input = preferred_genre if preferred_genre.strip() else "최신 트렌디한 음악"
    
    prompt = f"""
    당신은 전문 음악 큐레이터입니다. {user_age}세 사용자에게 '{genre_input}' 관련 음악 3곡을 추천하세요.
    응답은 반드시 아래 JSON 형식이어야 합니다. 다른 말은 하지 마세요.
    
    {{
      "recommendations": [
        {{ "title": "곡 제목", "artist": "아티스트", "reason": "{language_choice}로 작성된 상세 이유" }}
      ]
    }}
    """
    
    # 시도할 모델 리스트 (2.0 먼저, 안되면 1.5)
    models_to_try = ['gemini-2.0-flash-exp', 'gemini-1.5-flash']
    
    last_error = ""
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            last_error = str(e)
            continue # 다음 모델로 시도
            
    return {"error": f"모든 모델 호출 실패. 마지막 오류: {last_error}"}

# --- UI 레이아웃 ---
st.set_page_config(page_title="AI 음악 추천 (Gemini 2.0)", page_icon="🎧")
st.title("🎧 Gemini 2.0 음악 큐레이터")

selected_age = st.number_input("나이를 입력하세요:", min_value=1, max_value=100, value=25)
genre = st.text_input("선호 장르/아티스트:", placeholder="예: 힙합, 아이브, 잔잔한 곡")
lang = st.selectbox("추천 언어:", ["Korean", "English", "Japanese"])

st.divider()

if st.button("2.0 모델로 추천 받기 ✨", use_container_width=True):
    with st.spinner("Gemini 2.0이 음악을 분석 중입니다..."):
        result = get_recommendation(selected_age, genre, lang)
        
        if "error" in result:
            st.error(result["error"])
            st.info("💡 404가 뜬다면 아직 계정에 2.0 권한이 없는 것입니다. AI Studio에서 2.0 사용 설정을 확인하세요.")
        else:
            st.success(f"✅ 추천 완료!")
            for i, rec in enumerate(result.get("recommendations", [])):
                with st.container():
                    st.subheader(f"{i+1}. {rec['title']} - {rec['artist']}")
                    st.write(f"**이유**: {rec['reason']}")
                    q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
                    st.markdown(f"[▶️ 유튜브 검색](https://www.youtube.com/results?search_query={q})")
                    st.divider()
