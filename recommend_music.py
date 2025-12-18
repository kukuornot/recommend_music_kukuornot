import streamlit as st
from google import genai
from google.genai import types
import os
import json
import urllib.parse

# 1. Gemini 클라이언트 초기화 (배포 및 로컬 환경 모두 대응)
try:
    api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("Gemini API 키를 설정해주세요. (로컬: 환경변수 / 배포: Streamlit Secrets)")
    st.stop()

def get_recommendation(age: int, preferred_genre: str, language_choice: str):
    # 장르 미입력 시 실시간 인기곡으로 자동 설정
    genre_prompt = preferred_genre if preferred_genre.strip() else "전 세계적으로 실시간 인기가 많은 (Popular trending) 곡"
    
    # 언어 선택에 따른 지침 설정
    if language_choice == "선택 안 함":
        language_instruction = "추천 이유를 언어에 구애받지 않고 가장 적절하다고 판단되는 언어(예: 한국어, 영어)로 작성해 주세요."
        output_language = "자유"
    else:
        language_instruction = f"추천 이유를 {language_choice}어로 간결하게 설명해 주세요."
        output_language = language_choice
    
    # AI에게 전달할 프롬프트 구성
    prompt = f"""
    당신은 전문 음악 큐레이터입니다. 
    다음 사용자의 정보를 분석하여, 음악 3곡을 추천하고 {language_instruction}
    사용자가 버튼을 누를 때마다 매번 새로운 곡을 추천하도록 노력하세요.
    
    응답은 반드시 아래 JSON 스키마를 따르는 하나의 JSON 오브젝트여야 합니다. 
    
    사용자 정보:
    - 나이: {age}세
    - 선호 음악: {genre_prompt}
    - 추천 언어: {output_language}
    
    JSON 스키마:
    {{
      "recommendations": [
        {{
          "title": "노래 제목",
          "artist": "아티스트 이름",
          "reason": "추천 이유"
        }}
      ]
    }}
    """
    
    try:
        # 404 에러를 방지하기 위해 가장 최신 모델인 'gemini-2.0-flash' 사용
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.8 # 다양성을 위해 높은 창의성 수치 적용
            )
        )
        
        # JSON 응답에서 불필요한 마크다운 기호 제거 후 파싱
        raw_text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(raw_text)
        
    except Exception as e:
        return {"error": f"추천을 가져오는 중 오류가 발생했습니다: {e}"}

# --- UI 레이아웃 시작 ---
st.set_page_config(page_title="🎶 AI 음악 추천 시스템", layout="centered")
st.title("🎵 음악 추천 AI")
st.markdown("나이와 선호 장르를 입력하고 추천 언어를 선택해 보세요.")

# 나이 입력 (number_input)
age = st.number_input("나이를 입력해 주세요:", min_value=1, max_value=100, value=25, step=1)

# 장르 입력 (text_input + 줄바꿈 레이아웃 적용)
genre = st.text_input("선호하는 음악 장르를 입력해 주세요  \n(빈 칸은 실시간 인기곡 추천):", value="")

# 언어 선택 드롭다운
language_full_list = ['선택 안 함', 'Korean', 'English', 'Japanese', 'Chinese']
language_display = {
    'Korean': 'Korean (한국어)', 
    'English': 'English (영어)', 
    'Japanese': 'Japanese (일본어)', 
    'Chinese': 'Chinese (중국어)',
    '선택 안 함': '선택 안 함'
}

selected_language_key = st.selectbox(
    "추천 결과를 보고 싶은 언어를 선택하세요:",
    options=language_full_list,
    format_func=lambda x: language_display[x]
)

# 추천 버튼 (st.form을 사용하지 않아 연속 클릭 가능)
if st.button("음악 추천받기 🌟"):
    with st.spinner("Gemini가 당신을 위한 새로운 음악을 고르는 중입니다..."):
        data = get_recommendation(age, genre, selected_language_key)
        
        if "error" in data:
            st.error(data["error"])
        else:
            st.success("✅ 추천이 완료되었습니다!")
            
            # 제목 표시
            if not genre.strip():
                st.subheader("🔥 실시간 인기곡 기반 추천 결과:")
            else:
                st.subheader("🎧 당신을 위한 맞춤 추천 결과:")
                
            # 결과 리스트 출력
            for i, rec in enumerate(data.get("recommendations", [])):
                st.markdown(f"### {i+1}. {rec['title']} - {rec['artist']}")
                st.markdown(f"**추천 이유**: {rec['reason']}")
                
                # YouTube 검색 링크 생성 (URL 인코딩 포함)
                search_query = f"{rec['title']} {rec['artist']}"
                encoded_query = urllib.parse.quote_plus(search_query)
                youtube_link = f"https://www.youtube.com/results?search_query={encoded_query}"
                
                st.markdown(f"[▶️ YouTube에서 음악 듣기]({youtube_link})")
                st.divider()
            
            st.info("💡 다른 곡을 더 추천받고 싶다면 버튼을 다시 눌러보세요!")
