import streamlit as st
from openai import OpenAI
import json
import urllib.parse

# 1. API 설정
try:
    api_key = st.secrets.get("DEEPSEEK_API_KEY")
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
except Exception:
    st.error("DeepSeek API 키 설정을 확인해주세요.")
    st.stop()

# 2. 세션 상태 초기화
if "history" not in st.session_state:
    st.session_state.history = []
if "index" not in st.session_state:
    st.session_state.index = -1

def get_recommendation(user_age, preferred_genre):
    past_songs = [rec['title'] for h in st.session_state.history for rec in h.get('recommendations', [])]
    past_songs_str = ", ".join(past_songs[-20:]) 

    # [프롬프트 핵심 수정] 장르의 '기술적 특징'을 강제하여 오분류 방지
    prompt = f"""
    당신은 전 세계 음악을 분석하는 정밀 큐레이터입니다. {user_age}세 사용자에게 '{preferred_genre}' 장르의 음악 3곡을 추천하세요.
    
    [장르 판별 필터링]
    1. **힙합/랩 (Hip-hop/Rap)**: 
       - 필수: 반드시 80% 이상의 비중이 '래핑(rapping)'으로 구성되어야 함. 
       - 제외: NewJeans의 Hype Boy, BTS의 Dynamite 같은 보컬 위주의 팝/댄스 곡은 '절대 금지'.
    2. **발라드 (Ballad)**: 
       - 필수: 70~100 BPM 이하의 느린 템포, 서정적 멜로디와 보컬 감성이 중심.
    3. **K-POP/댄스 (Pop/Dance)**: 
       - 필수: 퍼포먼스 중심, 중독성 있는 훅, 전자음 기반의 댄스 비트.
    
    [기타 조건]
    - 시대: 2020년~2025년 사이 발매된 실제 곡.
    - 언어: 모든 설명은 한국어로만 작성.
    
    JSON 형식:
    {{
      "recommendations": [
        {{ 
          "title": "실제 곡 제목", 
          "artist": "실제 아티스트", 
          "reason": "해당 장르({preferred_genre})의 기술적 특징을 근거로 한 한국어 추천 이유" 
        }}
      ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a professional music analyst. Output JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.2 # 정확도를 극대화하기 위해 낮춤
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

# --- UI 레이아웃 ---
st.set_page_config(page_title="정밀 장르 음악 추천", page_icon="🎵")
st.title("🎵 정밀 장르 매칭 AI (2020-2025)")

with st.sidebar:
    st.header("사용자 설정")
    age = st.number_input("나이:", 1, 100, 25)
    genre_choice = st.selectbox("정확한 장르 선택:", ["힙합/랩", "발라드", "K-POP/댄스", "R&B/소울"])
    extra_info = st.text_input("추가 키워드 (선택):", placeholder="예: 비트가 강한, 슬픈")

if st.button("전문 분석 기반 추천 받기 🚀", use_container_width=True):
    with st.spinner(f"'{genre_choice}' 데이터를 엄격히 대조 중..."):
        new_res = get_recommendation(age, f"{genre_choice} {extra_info}")
        if "error" not in new_res:
            st.session_state.history.append(new_res)
            st.session_state.index = len(st.session_state.history) - 1
        else:
            st.error("데이터를 가져오지 못했습니다.")

# --- 히스토리 내비게이션 (화살표) ---
if st.session_state.history:
    st.divider()
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("⬅️ 이전", disabled=(st.session_state.index <= 0)):
            st.session_state.index -= 1
            st.rerun()
    with c2:
        st.write(f"<center><b>{st.session_state.index + 1} / {len(st.session_state.history)}</b></center>", unsafe_allow_html=True)
    with c3:
        if st.button("다음 ➡️", disabled=(st.session_state.index >= len(st.session_state.history) - 1)):
            st.session_state.index += 1
            st.rerun()

    current_data = st.session_state.history[st.session_state.index]
    for i, rec in enumerate(current_data.get("recommendations", [])):
        with st.container(border=True):
            st.subheader(f"{i+1}. {rec['title']} - {rec['artist']}")
            st.info(f"🎤 **장르 분석 추천**: {rec['reason']}")
            
            q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
            st.link_button("▶️ 유튜브 확인", f"https://www.youtube.com/results?search_query={q}")
