import streamlit as st
from groq import Groq
import os
import json
import urllib.parse

# 1. Groq API 클라이언트 설정
try:
    # Streamlit Secrets에 GROQ_API_KEY 라는 이름으로 키를 저장하세요.
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY가 Secrets에 설정되지 않았습니다.")
        st.stop()
    client = Groq(api_key=api_key)
except Exception as e:
    st.error(f"설정 오류: {e}")
    st.stop()

def get_recommendation(user_age: int, preferred_genre: str, language_choice: str):
    genre_input = preferred_genre if preferred_genre.strip() else "최신 트렌디한 인기곡"
    
    # 정확도를 높이기 위한 상세 프롬프트
    prompt = f"""
    당신은 음악 전문가입니다. {user_age}세 사용자가 좋아할 만한 '{genre_input}' 관련 음악 3곡을 추천하세요.
    반드시 아래 JSON 형식으로만 응답하세요. 다른 설명 문구는 일체 배제하세요.
    
    JSON 형식:
    {{
      "recommendations": [
        {{ 
          "title": "곡 제목", 
          "artist": "아티스트", 
          "reason": "{language_choice}로 작성된 아주 구체적인 추천 이유" 
        }}
      ]
    }}
    """
    
    try:
        # Groq에서 가장 성능이 좋은 모델 사용
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        return {"error": f"Groq API 호출 중 오류가 발생했습니다: {str(e)}"}

# --- UI 레이아웃 ---
st.set_page_config(page_title="음악 추천 AI (Groq)", page_icon="⚡")
st.title("⚡ 초고속 AI 음악 큐레이터")
st.write("Groq Llama 3.3 모델을 사용하여 실시간으로 음악을 추천합니다.")

# 입력 섹션
selected_age = st.number_input("나이를 입력하세요:", min_value=1, max_value=100, value=25, step=1)
genre = st.text_input("좋아하는 장르나 가수 (예: 뉴진스, 힙합, 재즈):", placeholder="입력하지 않으면 인기곡을 추천합니다.")
lang = st.selectbox("추천 이유 언어:", ["Korean", "English", "Japanese"])

st.divider()

if st.button("음악 추천 받기 🚀", use_container_width=True):
    with st.spinner("Groq AI가 빛의 속도로 분석 중..."):
        result = get_recommendation(selected_age, genre, lang)
        
        if "error" in result:
            st.error(result["error"])
        else:
            st.success("✅ 추천이 완료되었습니다!")
            for i, rec in enumerate(result.get("recommendations", []
