import streamlit as st
from google import genai
from google.genai import types
import os
import json
import urllib.parse

# Gemini 클라이언트 초기화
try:
    client = genai.Client()
except Exception:
    st.error("Gemini 클라이언트 초기화에 실패했습니다. 환경 변수 GEMINI_API_KEY가 설정되었는지 확인해 주세요.")
    st.stop()
    
def get_recommendation(age: int, preferred_genre: str, language_choice: str):
    """나이, 장르, 언어 기반으로 Gemini API로부터 음악 추천을 받습니다."""
    
    # --- 1. 프롬프트 조건 설정 ---
    
    # 1-1. 선호 장르가 없을 경우 인기곡 추천으로 변경
    if not preferred_genre.strip():
        genre_prompt = "전 세계적으로 실시간 인기가 많은 (Popular trending) 곡"
    else:
        genre_prompt = preferred_genre
        
    # 1-2. 언어 선택에 따른 추천 언어 설정
    if language_choice == "선택 안 함":
        language_instruction = "추천 이유를 언어에 구애받지 않고 가장 적절하다고 판단되는 언어(예: 한국어, 영어)로 작성해 주세요."
        output_language = "자유"
    else:
        language_instruction = f"추천 이유를 {language_choice}어로 간결하게 설명해 주세요."
        output_language = language_choice
    
    # --- 2. 모델에 전달할 프롬프트 작성 ---
    
    prompt = f"""
    당신은 전문 음악 큐레이터입니다. 
    다음 사용자의 정보를 분석하여, 음악 3곡을 추천하고 {language_instruction}
    
    응답은 반드시 아래 JSON 스키마를 따르는 하나의 JSON 오브젝트여야 합니다. 
    다른 설명이나 텍스트를 JSON 바깥에 포함하지 마세요.
    
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
    
    # --- 3. API 호출 및 파싱 ---
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7 
            )
        )
        
        # JSON 응답 파싱
        raw_text = response.text.strip()
        if raw_text.startswith('```json'):
            raw_text = raw_text[7:].strip()
        if raw_text.endswith('```'):
            raw_text = raw_text[:-3].strip()

        return json.loads(raw_text)
        
    except json.JSONDecodeError:
        return {"error": f"Gemini 응답을 JSON으로 처리하는 데 실패했습니다. 원본 응답의 일부: {response.text[:100]}..."}
    except Exception as e:
        return {"error": f"API 호출 중 오류가 발생했습니다: {e}"}

# --- 4. Streamlit 앱 레이아웃 설정 ---

st.set_page_config(page_title="🎶 AI 음악 추천 시스템", layout="centered")
st.title("🎵 개인화된 음악 추천 AI")
st.markdown("나이, 선호 장르를 입력하고 추천 언어를 선택하세요.")

# 입력 폼
with st.form("recommendation_form"):
    
    age = st.number_input("나이를 입력해 주세요:", min_value=1, max_value=100, value=25, step=1)
    
    genre = st.text_input("선호하는 음악 장르를 입력해 주세요 (빈 칸은 실시간 인기곡 추천):", 
                          value="")
    
    # 언어 선택 드롭다운 (선택 안 함 옵션 추가)
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
    
    submitted = st.form_submit_button("음악 추천받기 🌟")

# 버튼이 눌렸을 때 로직 실행
if submitted:
    with st.spinner("Gemini가 당신의 취향을 분석하고 음악을 고르는 중입니다..."):
        
        recommendation_data = get_recommendation(age, genre, selected_language_key)
        
        if "error" in recommendation_data:
            st.error(recommendation_data["error"])
        else:
            st.success("✅ 추천 완료!")
            
            # 장르가 비어있을 경우 헤더 변경
            if not genre.strip():
                st.subheader("🔥 실시간 인기곡 기반 음악 추천 결과:")
            else:
                st.subheader("🎧 당신만을 위한 음악 추천 결과:")
                
            
            # 결과 출력 및 YouTube 링크 생성
            for i, rec in enumerate(recommendation_data.get("recommendations", [])):
                title = rec.get("title", "제목 없음")
                artist = rec.get("artist", "아티스트 정보 없음")
                reason = rec.get("reason", "추천 이유 없음")
                
                # YouTube 검색어 생성 및 URL 인코딩
                search_query = f"{title} {artist}"
                encoded_query = urllib.parse.quote_plus(search_query)
                youtube_link = f"https://www.youtube.com/results?search_query={encoded_query}"
                
                st.markdown(f"**{i+1}. {title}** (by **{artist}**)")
                st.markdown(f"**추천 이유**: {reason}")
                st.markdown(f"[▶️ **YouTube에서 음악 듣기**]({youtube_link})")
                st.markdown("---")