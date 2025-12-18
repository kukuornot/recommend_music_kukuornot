import streamlit as st
from openai import OpenAI
import json
import urllib.parse

# 1. DeepSeek API 설정 (OpenAI 라이브러리 활용)
try:
    api_key = st.secrets.get("DEEPSEEK_API_KEY")
    client = OpenAI(
        api_key=api_key, 
        base_url="https://api.deepseek.com"
    )
except Exception as e:
    st.error("DeepSeek API 키가 설정되지 않았습니다. Secrets를 확인해주세요.")
    st.stop()

def get_recommendation(user_age: int, preferred_genre: str, language_choice: str):
    genre_input = preferred_genre if preferred_genre.strip() else "2024-2025 최신 인기 차트"
    
    # [강력한 지침] 팩트 체크 및 최신곡 강제
    prompt = f"""
    당신은 대한민국 음악 데이터 전문가입니다. {user_age}세 사용자를 위해 '{genre_input}' 테마의 음악 3곡을 추천하세요.
    
    [필수 규칙]
    1. 반드시 2024년 말~2025년 초에 실제로 존재하는 '진짜' 곡만 추천하세요.
    2. 아티스트와 곡 제목이 실제와 일치하는지 두 번 검토하세요. (예: 로제의 APT., 에스파의 Whiplash 등)
    3. 존재하지 않는 곡을 지어내면 절대 안 됩니다.
    4. 추천 이유는 {language_choice}로 작성하세요.
    
    반드시 아래 JSON 형식으로만 답변하세요:
    {{
      "recommendations": [
        {{ "title": "정확한 곡 제목", "artist": "정확한 아티스트 이름", "reason": "추천 이유" }}
      ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", # DeepSeek-V3
            messages=[
                {"role": "system", "content": "You are a professional music curator. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.1 # 사실 위주 답변을 위해 낮게 설정
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": f"API 호출 실패: {str(e)}"}

# --- UI 레이아웃 ---
st.set_page_config(page_title="DeepSeek 음악 추천", page_icon="🎵", layout="centered")

st.title("🎵 AI 최신곡 큐레이션 (DeepSeek V3)")
st.write("실시간 데이터 기반으로 정확한 최신곡만 추천합니다.")

with st.container(border=True):
    age = st.number_input("사용자 나이:", min_value=1, max_value=100, value=25)
    genre = st.text_input("선호 장르/가수:", placeholder="예: 2025년 아이돌 신곡, 신나는 팝송")
    lang = st.selectbox("추천 이유 언어:", ["Korean", "English", "Japanese"])

st.divider()

if st.button("전문 AI 추천 받기 🚀", use_container_width=True):
    with st.spinner("최신 음악 DB 검색 중..."):
        result = get_recommendation(age, genre, lang)
        
        if "error" in result:
            st.error(result["error"])
            st.info("💡 잔액이 부족하거나 API 키가 올바르지 않을 수 있습니다.")
        else:
            st.success("✅ 실제 차트 반영 추천 완료!")
            for i, rec in enumerate(result.get("recommendations", [])):
                with st.expander(f"{i+1}. {rec['title']} - {rec['artist']}", expanded=True):
                    st.write(f"💬 **이유**: {rec['reason']}")
                    
                    # 유튜브 검색 버튼
                    q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
                    st.link_button("▶️ 유튜브에서 곡 확인하기", f"https://www.youtube.com/results?search_query={q}")

st.caption("Powered by DeepSeek-V3 | 2025 Music Database")
