import streamlit as st
from openai import OpenAI
import json
import urllib.parse

# 1. API 설정
try:
    api_key = st.secrets.get("DEEPSEEK_API_KEY")
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
except Exception:
    st.error("DeepSeek API 키 설정을 확인해주세요 (Secrets 설정 필수).")
    st.stop()

# 2. 세션 상태 초기화
if "history" not in st.session_state:
    st.session_state.history = []
if "index" not in st.session_state:
    st.session_state.index = -1

def get_recommendation(user_age, preferred_genre):
    # 중복 추천 방지
    past_songs = [rec['title'] for h in st.session_state.history for rec in h.get('recommendations', [])]
    past_songs_str = ", ".join(past_songs[-20:]) 

    # [프롬프트 최종 수정] 아티스트-곡 제목 팩트체크 및 장르 기술적 분석 강화
    prompt = f"""
    당신은 대한민국 음악 데이터 검증 전문가입니다. {user_age}세 사용자에게 '{preferred_genre}' 장르의 곡 3개를 추천하세요.
    
    [실제 데이터 기반 추천 지침]
    1. **아티스트 일치 확인**: 반드시 곡 제목과 해당 아티스트가 실제와 일치하는지 두 번 검토하세요. (예: 'Hmm'은 BE'O의 곡, 'Dynamite'는 BTS의 곡)
    2. **장르 필터링**: 
       - 힙합/랩: 반드시 래핑이 80% 이상이며 비트가 주가 되어야 함. (댄스곡 제외)
       - 발라드: 2020년 이후 발매된 서정적인 곡.
    3. **최신성**: 반드시 2020년~2025년 사이 발매된 실제 곡만 선정하세요.
    4. **중복 금지**: [{past_songs_str}] 제외.
    5. **한국어 전용**: 모든 설명은 한국어로 전문적으로 작성하세요.
    
    JSON 형식:
    {{
      "recommendations": [
        {{ 
          "title": "실제 곡 제목", 
          "artist": "실제 아티스트 이름", 
          "reason": "해당 장르의 특징을 근거로 한 한국어 설명" 
        }}
      ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a professional music fact-checker. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.1 # 환각 방지를 위해 가장 낮은 수치 설정
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

# --- UI 레이아웃 ---
st.set_page_config(page_title="AI 음악 팩트체커", page_icon="🛡️")
st.title("🛡️ 팩트체크 기반 장르별 음악 추천")
st.write("아티스트와 곡 정보를 정밀 대조하여 2020-2025년 최신곡을 추천합니다.")

with st.sidebar:
    st.header("설정")
    age = st.number_input("나이:", 1, 100, 25)
    genre_choice = st.selectbox("장르 선택:", ["힙합/랩", "발라드", "K-POP/댄스", "R&B/소울"])
    extra = st.text_input("추가 정보 (가수 등):", placeholder="예: 비오, 에스파")

# 추천 실행 버튼
if st.button("데이터 검증 및 추천 받기 🚀", use_container_width=True):
    with st.spinner("음악 DB와 아티스트 정보를 대조 중..."):
        new_res = get_recommendation(age, f"{genre_choice} {extra}")
        if "error" not in new_res:
            st.session_state.history.append(new_res)
            st.session_state.index = len(st.session_state.history) - 1
        else:
            st.error("API 호출 실패. 잔액 혹은 키 설정을 확인하세요.")

# --- 히스토리 내비게이션 ---
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
            st.info(f"📑 **분석**: {rec['reason']}")
            
            # 유튜브 링크 (실제 곡 확인용)
            q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
            st.link_button("▶️ 유튜브 검색 확인", f"https://www.youtube.com/results?search_query={q}")
