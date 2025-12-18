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
    genre_input = preferred_genre if preferred_genre.strip() else "최신 인기곡"
    
    prompt = f"""
    당신은 음악 전문가입니다. {user_age}세 사용자에게 '{genre_input}' 관련 음악 3곡을 추천하세요.
    응답은 반드시 아래 JSON 형식으로만 하세요. 다른 텍스트는 금지합니다.
    
    {{
      "recommendations": [
        {{ "title": "곡 제목", "artist": "아티스트", "reason": "{language_choice}로 작성된 추천 이유" }}
      ]
    }}
    """
    
    # [중요] 모델명을 가장 표준적인 형식으로 시도합니다.
    # 2.0이 차단되었을 수 있으므로 1.5를 기본으로 하되 경로를 명확히 합니다.
    try:
        # 'models/'를 생략하고 라이브러리가 자동으로 처리하게 합니다.
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        # 만약 위 방법이 실패하면 'models/'를 붙여서 마지막으로 시도합니다.
        try:
            model = genai.GenerativeModel('models/gemini-1.5-flash')
            response = model.generate_content(prompt)
            # 텍스트에서 JSON 부분만 추출하는 안전 장치
            res_text = response.text
            start = res_text.find('{')
            end = res_text.rfind('}') + 1
            return json.loads(res_text[start:end])
        except Exception as e2:
            return {"error": f"최종 호출 실패: {str(e2)}"}

# --- UI 레이아웃 ---
st.set_page_config(page_title="AI 음악 추천", page_icon="🎧")
st.title("🎶 최종 점검: 음악 추천 AI")

selected_age = st.number_input("나이:", min_value=1, max_value=100, value=25)
genre = st.text_input("선호 장르:", placeholder="예: 댄스, 발라드")
lang = st.selectbox("추천 언어:", ["Korean", "English", "Japanese"])

if st.button("음악 추천 받기 🚀", use_container_width=True):
    with st.spinner("분석 중..."):
        result = get_recommendation(selected_age, genre, lang)
        
        if "error" in result:
            st.error(result["error"])
            st.warning("⚠️ 계속 404가 뜬다면 아래 '마지막 조치'를 확인하세요.")
        else:
            for i, rec in enumerate(result.get("recommendations", [])):
                st.subheader(f"{i+1}. {rec['title']} - {rec['artist']}")
                st.write(f"**이유**: {rec['reason']}")
                q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
                st.markdown(f"[▶️ 유튜브 검색](https://www.youtube.com/results?search_query={q})")
                st.divider()
