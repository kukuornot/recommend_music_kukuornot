import streamlit as st
from groq import Groq
import os
import json
import urllib.parse

# 1. Groq API 클라이언트 설정
try:
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
    
    prompt = f"""
    당신은 음악 전문가입니다. {user_age}세 사용자가 좋아할 만한 '{genre_input}' 관련 음악 3곡을 추천하세요.
    반드시 아래 JSON 형식으로만 응답하세요. 다른 설명은 하지 마세요.
    
    JSON 형식:
    {{
      "recommendations": [
        {{ 
          "title": "곡 제목", 
          "artist": "아티스트", 
          "reason": "{language_choice}로 작성된 상세한 추천 이유" 
        }}
      ]
    }}
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            # JSON 모드 활성화
            response_format={"type": "json_object"}
        )
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        return {"error": f"API 오류: {str(e)}"}

# --- UI 레이아웃 ---
st.set_page_config(page_title="AI 음악 추천", page_icon="⚡")
st.title("⚡ Groq 기반 음악 추천 AI")

selected_age = st.number_input("나이 입력:", min_value=1, max_value=100, value=25, step=1)
genre = st.text_input("좋아하는 장르/가수:", placeholder="예: 뉴진스, 재즈")
lang = st.selectbox("언어 선택:", ["Korean", "English", "Japanese"])

st.divider()

if st.button("음악 추천 받기 🚀", use_container_width=True):
    with st.spinner("AI가 분석 중입니다..."):
        result = get_recommendation(selected_age, genre, lang)
        
        if "error" in result:
            st.error(result["error"])
        else:
            # 에러가 났던 괄호 부분을 정확히 수정했습니다.
            recommendations = result.get("recommendations", [])
            for i, rec in enumerate(recommendations):
                with st.container():
                    st.subheader(f"{i+1}. {rec['title']} - {rec['artist']}")
                    st.info(f"💡 **추천 이유**: {rec['reason']}")
                    
                    # 유튜브 링크 생성
                    q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
                    st.markdown(f"[▶️ 유튜브에서 듣기](https://www.youtube.com/results?search_query={q})")
                    st.divider()

st.caption("Powered by Groq Llama 3.3")
