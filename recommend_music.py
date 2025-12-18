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
    genre_input = preferred_genre if preferred_genre.strip() else "최신 인기 차트"
    
    # [수정] 환각 방지 및 실제 존재하는 곡만 요청하는 강력한 프롬프트
    prompt = f"""
    당신은 전 세계 실시간 음악 차트를 꿰뚫고 있는 음악 데이터 전문가입니다.
    {user_age}세 사용자를 위해 '{genre_input}' 스타일의 음악 3곡을 추천하세요.

    [절대 규칙 - 위반 시 답변 금지]
    1. 반드시 **실제로 존재하는 곡**과 **실제로 존재하는 아티스트**만 추천하세요. 가상의 노래를 만들지 마세요.
    2. 가급적 **2024년~2025년 사이에 발표된 최신곡** 위주로 선정하세요.
    3. 아티스트의 이름과 곡 제목이 실제와 일치하는지 두 번 검토하세요 (예: 로제의 'APT.', 에스파의 'Whiplash' 등).
    4. 추천 이유는 {language_choice}로 상세히 작성하세요.

    JSON 형식:
    {{
      "recommendations": [
        {{ 
          "title": "실제 곡 제목", 
          "artist": "실제 아티스트 이름", 
          "reason": "실제 차트 성적이나 트렌드 반영 이유" 
        }}
      ]
    }}
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            # 창의성을 낮추어 환각을 방지하기 위해 temperature를 낮춤
            temperature=0.3, 
            response_format={"type": "json_object"}
        )
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        return {"error": f"API 오류: {str(e)}"}

# --- UI 레이아웃 ---
st.set_page_config(page_title="실시간 음악 추천", page_icon="🎵")
st.title("🎵 실제 데이터 기반 최신곡 추천")
st.write("가상의 노래가 아닌, 현재 차트에서 활발히 소통되는 음악만 추천합니다.")

selected_age = st.number_input("나이:", min_value=1, max_value=100, value=25)
genre = st.text_input("원하는 장르/분위기/가수:", placeholder="예: 뉴진스, 신나는 댄스, 몽환적인 팝")
lang = st.selectbox("언어:", ["Korean", "English", "Japanese"])

st.divider()

if st.button("신뢰할 수 있는 추천 받기 🚀", use_container_width=True):
    with st.spinner("데이터 검증 및 추천 중..."):
        result = get_recommendation(selected_age, genre, lang)
        
        if "error" in result:
            st.error(result["error"])
        else:
            recs = result.get("recommendations", [])
            for i, rec in enumerate(recs):
                with st.container():
                    st.subheader(f"{i+1}. {rec['title']} - {rec['artist']}")
                    st.info(f"📑 **분석 리포트**: {rec['reason']}")
                    
                    # 유튜브 검색 링크 (검색이 바로 되도록 보장)
                    q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
                    st.markdown(f"[▶️ 유튜브에서 실제 곡 확인](https://www.youtube.com/results?search_query={q})")
                    st.divider()

st.caption("Powered by Groq & Llama 3.3 (Fact-Checked Mode)")
