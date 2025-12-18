import streamlit as st
import google.generativeai as genai
import os
import json
import urllib.parse

# 1. API 클라이언트 설정
try:
    api_key = st.secrets.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    # 오직 Gemini 2.0 Flash 모델만 지정합니다.
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
except Exception as e:
    st.error(f"초기화 오류: {e}")
    st.stop()

def get_recommendation(user_age: int, preferred_genre: str, language_choice: str):
    genre_input = preferred_genre if preferred_genre.strip() else "최신 트렌디한 음악"
    
    prompt = f"""
    당신은 전문 음악 AI 큐레이터입니다. {user_age}세 사용자에게 '{genre_input}' 스타일의 음악 3곡을 추천하세요.
    반드시 아래 JSON 형식으로만 답변하세요.
    
    {{
      "recommendations": [
        {{ "title": "곡 제목", "artist": "아티스트", "reason": "{language_choice}로 작성된 상세 이유" }}
      ]
    }}
    """
    
    try:
        # Gemini 2.0 모델을 사용하여 콘텐츠 생성
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        # 에러 발생 시 다른 모델로 넘기지 않고 즉시 에러 메시지 반환
        return {"error": f"Gemini 2.0 호출 실패: {str(e)}"}

# --- UI 레이아웃 ---
st.set_page_config(page_title="Gemini 2.0 음악 추천", page_icon="🎧")
st.title("🎧 Gemini 2.0 전용 음악 큐레이터")

selected_age = st.number_input("나이를 입력하세요:", min_value=1, max_value=100, value=25)
genre = st.text_input("선호 장르/가수:", placeholder="예: 힙합, 아이브, 뉴진스")
lang = st.selectbox("추천 이유 언어:", ["Korean", "English", "Japanese"])

st.divider()

if st.button("2.0 모델로 추천 받기 🚀", use_container_width=True):
    with st.spinner("Gemini 2.0 분석 중..."):
        result = get_recommendation(selected_age, genre, lang)
        
        if "error" in result:
            st.error(result["error"])
        else:
            st.success("✅ Gemini 2.0 추천 성공!")
            for i, rec in enumerate(result.get("recommendations", [])):
                with st.container():
                    st.subheader(f"{i+1}. {rec['title']} - {rec['artist']}")
                    st.info(f"💡 **추천 이유**: {rec['reason']}")
                    q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
                    st.markdown(f"[▶️ 유튜브에서 듣기](https://www.youtube.com/results?search_query={q})")
                    st.divider()
