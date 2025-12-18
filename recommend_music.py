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
    
    # 2.0 모델 성능을 극대화하기 위한 프롬프트
    prompt = f"""
    당신은 음악 전문 AI 큐레이터입니다. {user_age}세 사용자에게 '{genre_input}' 스타일의 음악 3곡을 추천하세요.
    반드시 아래 JSON 형식으로만 답변하세요.
    
    {{
      "recommendations": [
        {{ "title": "곡 제목", "artist": "아티스트", "reason": "{language_choice}로 작성된 상세 이유" }}
      ]
    }}
    """
    
    try:
        # [핵심] 404 방지를 위해 모델명을 정확히 'gemini-2.0-flash-exp'로 지정
        # (현재 2.0은 Experimental 버전으로 제공됩니다)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        # 만약 2.0 모델이 아직 계정에서 지원되지 않는다면 1.5로 자동 전환 (안전장치)
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e2:
            return {"error": f"최종 오류: {str(e2)}"}

# --- UI 레이아웃 ---
st.set_page_config(page_title="AI 음악 추천 (Gemini 2.0)", page_icon="🎧")
st.title("🎧 Gemini 2.0 맞춤 음악 큐레이션")

# 입력창
selected_age = st.number_input("나이를 입력하세요:", min_value=1, max_value=100, value=25)
genre = st.text_input("선호 장르/가수:", placeholder="예: 힙합, 아이브, 뉴진스")
lang = st.selectbox("추천 이유 언어:", ["Korean", "English", "Japanese"])

st.divider()

if st.button("음악 추천 받기 🚀", use_container_width=True):
    with st.spinner("Gemini 2.0이 최적의 음악을 찾는 중..."):
        result = get_recommendation(selected_age, genre, lang)
        
        if "error" in result:
            st.error(result["error"])
        else:
            st.success("✅ 추천 결과가 도착했습니다!")
            for i, rec in enumerate(result.get("recommendations", [])):
                with st.container():
                    st.subheader(f"{i+1}. {rec['title']} - {rec['artist']}")
                    st.info(f"💡 **추천 이유**: {rec['reason']}")
                    q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
                    st.markdown(f"[▶️ 유튜브에서 듣기](https://www.youtube.com/results?search_query={q})")
                    st.divider()
