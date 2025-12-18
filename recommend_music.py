import streamlit as st
import google.generativeai as genai
import os
import json
import urllib.parse

# 1. API 클라이언트 설정
try:
    api_key = st.secrets.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    st.error("API 키를 확인해주세요. Streamlit Secrets에 GEMINI_API_KEY가 필요합니다.")
    st.stop()

def get_recommendation(user_age: int, preferred_genre: str, language_choice: str):
    genre_input = preferred_genre if preferred_genre.strip() else "최신 인기 차트 곡"
    
    prompt = f"""
    당신은 대한민국 최고의 음악 큐레이터입니다.
    {user_age}세 사용자가 좋아할 만한 '{genre_input}' 스타일의 음악 3곡을 추천하세요.
    
    [조건]
    1. 각 곡마다 추천 이유를 반드시 {language_choice}로 상세하게 작성하세요.
    2. 중복되지 않는 최신곡이나 명곡 위주로 선정하세요.
    3. 반드시 아래 JSON 형식을 엄격히 지켜서 응답하세요.

    JSON 형식:
    {{
      "recommendations": [
        {{ "title": "곡 제목", "artist": "아티스트", "reason": "상세한 추천 이유" }}
      ]
    }}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                candidate_count=1,
                temperature=0.8,
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e)}

# --- UI 레이아웃 (순서 교정됨) ---
st.set_page_config(page_title="AI 음악 큐레이터", page_icon="🎵")
st.title("🎶 맞춤형 AI 음악 추천")

# 사이드바에서 변수를 먼저 정의
with st.sidebar:
    st.header("설정")
    selected_age = st.slider("나이 선택", 10, 60, 25) # 여기서 age 정의
    lang = st.selectbox("추천 이유 언어", ["Korean", "English", "Japanese"])

# 정의된 변수를 아래에서 사용
st.write(f"**{selected_age}세** 취향 저격 음악을 추천해 드립니다.")

genre = st.text_input("평소 즐겨 듣는 장르나 가수 (예: 아이브, 재즈, 신나는 곡)", placeholder="입력하지 않으면 인기곡을 추천합니다.")

if st.button("추천 받기 🎧", use_container_width=True):
    with st.spinner("사용자님의 취향을 분석하고 있습니다..."):
        result = get_recommendation(selected_age, genre, lang)
        
        if "error" in result:
            st.error(f"오류가 발생했습니다: {result['error']}")
            st.info("💡 429 에러라면 API 할당량 문제이니 다른 구글 계정의 키를 사용해 보세요.")
        else:
            for i, rec in enumerate(result.get("recommendations", [])):
                with st.container():
                    st.subheader(f"{i+1}. {rec['title']} - {rec['artist']}")
                    st.info(f"💡 **추천 이유**: {rec['reason']}")
                    
                    q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
                    st.markdown(f"[▶️ 유튜브에서 바로 듣기](https://www.youtube.com/results?search_query={q})")
                    st.divider()
