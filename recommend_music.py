import streamlit as st
import google.generativeai as genai  # 라이브러리 호출 방식 변경
import os
import json
import urllib.parse

# 1. API 클라이언트 설정
try:
    api_key = st.secrets.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    # 가장 범용적인 모델 설정
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    st.error("API 키를 확인해주세요. Streamlit Secrets에 GEMINI_API_KEY가 필요합니다.")
    st.stop()

def get_recommendation(age: int, preferred_genre: str, language_choice: str):
    genre_input = preferred_genre if preferred_genre.strip() else "최신 인기 차트 곡"
    
    # AI에게 주는 지침 (정확도를 높이기 위해 페르소나 부여)
    prompt = f"""
    당신은 멜론, 스포티파이 데이터에 정통한 대한민국 최고의 음악 큐레이터입니다.
    {age}세 사용자가 좋아하는 '{genre_input}' 스타일의 음악 3곡을 추천하세요.
    
    [조건]
    1. 각 곡마다 추천 이유를 반드시 {language_choice}로 상세하게 작성하세요.
    2. 중복되지 않는 최신곡이나 명곡 위주로 선정하세요.
    3. 반드시 아래 JSON 형식을 엄격히 지켜서 응답하세요. 다른 서술형 문장은 포함하지 마세요.

    JSON 형식:
    {{
      "recommendations": [
        {{ "title": "곡 제목", "artist": "아티스트", "reason": "상세한 추천 이유" }}
      ]
    }}
    """
    
    try:
        # 안전한 호출 방식 (GenerationConfig 활용)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                candidate_count=1,
                temperature=0.8, # 창의적인 추천을 위해 약간 높임
                response_mime_type="application/json" # JSON 출력 강제
            )
        )
        
        return json.loads(response.text)
        
    except Exception as e:
        if "429" in str(e):
            return {"error": "할당량 초과! 다른 구글 계정의 API 키로 교체해 주세요."}
        return {"error": f"오류 발생: {str(e)}"}

# --- UI 레이아웃 ---
st.set_page_config(page_title="AI 음악 큐레이터", page_icon="🎵")
st.title("🎶 맞춤형 AI 음악 추천")
st.write(f"{age}세 취향 저격 음악을 추천해 드립니다.")

with st.sidebar:
    st.header("설정")
    age = st.slider("나이 선택", 10, 60, 25)
    lang = st.selectbox("추천 이유 언어", ["Korean", "English", "Japanese"])

genre = st.text_input("평소 즐겨 듣는 장르나 가수 (예: 아이브, 인디 밴드, 신나는 곡)", placeholder="입력하지 않으면 인기곡을 추천합니다.")

if st.button("추천 받기 🎧", use_container_width=True):
    with st.spinner("사용자님의 취향을 분석하고 있습니다..."):
        result = get_recommendation(age, genre, lang)
        
        if "error" in result:
            st.error(result["error"])
        else:
            for i, rec in enumerate(result.get("recommendations", [])):
                with st.container():
                    st.subheader(f"{i+1}. {rec['title']} - {rec['artist']}")
                    st.info(f"💡 **추천 이유**: {rec['reason']}")
                    
                    # 유튜브 링크 생성
                    q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
                    st.markdown(f"[▶️ 유튜브에서 바로 듣기](https://www.youtube.com/results?search_query={q})")
                    st.divider()
