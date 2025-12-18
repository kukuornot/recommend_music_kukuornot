import streamlit as st
import google.generativeai as genai
import os
import json
import urllib.parse

# 1. API 클라이언트 설정
try:
    api_key = st.secrets.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    # [수정포인트] 모델 이름을 'models/' 없이 'gemini-1.5-flash'로만 설정
    # 라이브러리가 내부적으로 적절한 경로를 찾도록 합니다.
    model = genai.GenerativeModel('gemini-1.5-flash-lastest')
except Exception as e:
    st.error(f"초기화 오류: {e}")
    st.stop()

def get_recommendation(user_age: int, preferred_genre: str, language_choice: str):
    genre_input = preferred_genre if preferred_genre.strip() else "최신 인기 차트 곡"
    
    prompt = f"""
    당신은 대한민국 최고의 음악 큐레이터입니다.
    {user_age}세 사용자가 좋아할 만한 '{genre_input}' 스타일의 음악 3곡을 추천하세요.
    응답은 반드시 아래 JSON 형식이어야 합니다.
    
    {{
      "recommendations": [
        {{ "title": "곡 제목", "artist": "아티스트", "reason": "{language_choice}로 작성된 상세 이유" }}
      ]
    }}
    """
    
    try:
        # 응답 형식을 JSON으로 강제하여 안정성 확보
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e)}

# --- UI 레이아웃 ---
st.set_page_config(page_title="AI 음악 큐레이터", page_icon="🎵")
st.title("🎶 맞춤형 AI 음악 추천")

# 나이 직접 입력 (사용자 요청 반영)
selected_age = st.number_input("나이를 입력해 주세요:", min_value=1, max_value=100, value=25, step=1)
genre = st.text_input("평소 즐겨 듣는 장르나 가수:", placeholder="예: 아이브, 재즈, 신나는 곡")
lang = st.selectbox("추천 이유 언어:", ["Korean", "English", "Japanese"])

st.divider()

if st.button("음악 추천 받기 🎧", use_container_width=True):
    with st.spinner("AI가 음악을 분석 중입니다..."):
        result = get_recommendation(selected_age, genre, lang)
        
        if "error" in result:
            # 404 에러가 또 발생할 경우를 대비한 안내
            if "404" in result["error"]:
                st.error("모델을 찾을 수 없습니다(404).")
                st.info("💡 해결 방법: 코드를 'gemini-1.5-flash-latest'로 수정하거나 API 키를 새로 발급받아 보세요.")
            else:
                st.error(f"오류: {result['error']}")
        else:
            for i, rec in enumerate(result.get("recommendations", [])):
                with st.container():
                    st.subheader(f"{i+1}. {rec['title']} - {rec['artist']}")
                    st.info(f"💡 **추천 이유**: {rec['reason']}")
                    q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
                    st.markdown(f"[▶️ 유튜브에서 듣기](https://www.youtube.com/results?search_query={q})")
                    st.divider()

