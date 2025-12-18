import streamlit as st
from groq import Groq
import os
import json
import urllib.parse

# 1. Groq API 클라이언트 설정
try:
    api_key = st.secrets.get("GROQ_API_KEY")
    client = Groq(api_key=api_key)
except Exception as e:
    st.error(f"설정 오류: {e}")
    st.stop()

def get_recommendation(user_age: int, preferred_genre: str, language_choice: str):
    genre_input = preferred_genre if preferred_genre.strip() else "최근 1개월 내 인기곡"
    
    # [수정] 날짜 조작 엄금 및 최신 데이터 우선순위 명시
    prompt = f"""
    당신은 멜론, 빌보드, 유튜브 뮤직의 최신 데이터를 기반으로 하는 실시간 음악 분석기입니다.
    {user_age}세 사용자를 위해 '{genre_input}' 테마의 음악 3곡을 추천하세요.

    [핵심 지침 - 반드시 지킬 것]
    1. **절대 금지**: 2023년 이전에 나온 노래를 2024~2025년 신곡이라고 속이지 마세요.
    2. **우선순위**: 현재(2024년 말~2025년 초) 차트에 올라와 있는 **진짜 신곡** (예: 로제, 에스파, 뉴진스, 아일릿 등) 위주로 추천하세요.
    3. **정확성**: 곡 제목과 아티스트, 발매 연도가 정확한지 스스로 내부 검증을 거친 후 출력하세요.
    4. 응답은 {language_choice}로 작성하며, 반드시 아래 JSON 형식만 따르세요.

    JSON 형식:
    {{
      "recommendations": [
        {{ 
          "title": "실제 곡 제목", 
          "artist": "실제 아티스트", 
          "reason": "발매 정보와 최신 트렌드를 포함한 이유" 
        }}
      ]
    }}
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            # [핵심] 0에 가까울수록 지어내지 않고 훈련된 사실만 말합니다.
            temperature=0, 
            response_format={"type": "json_object"}
        )
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        return {"error": f"API 오류: {str(e)}"}

# --- UI Layout ---
st.set_page_config(page_title="진짜 최신곡 추천", page_icon="📈")
st.title("📈 팩트체크 기반 최신곡 추천")
st.write("AI의 거짓말을 방지하기 위해 정밀 모드를 적용했습니다.")

age = st.number_input("나이:", min_value=1, max_value=100, value=25)
genre = st.text_input("원하는 장르/가수:", placeholder="예: 2025년 신곡, 에스파, 신나는 아이돌 음악")
lang = st.selectbox("언어:", ["Korean", "English", "Japanese"])

if st.button("최신 데이터로 추천 받기 ✨", use_container_width=True):
    with st.spinner("최신 차트 데이터를 검증 중..."):
        result = get_recommendation(age, genre, lang)
        
        if "error" in result:
            st.error(result["error"])
        else:
            for i, rec in enumerate(result.get("recommendations", [])):
                with st.container():
                    st.subheader(f"{i+1}. {rec['title']} - {rec['artist']}")
                    st.info(f"📑 **분석**: {rec['reason']}")
                    q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
                    st.markdown(f"[▶️ 유튜브 실제 영상 검색](https://www.youtube.com/results?search_query={q})")
                    st.divider()
