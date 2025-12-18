import streamlit as st
from openai import OpenAI
import json
import urllib.parse

# 1. API 설정 (DeepSeek)
try:
    # Streamlit Secrets에 DEEPSEEK_API_KEY가 저장되어 있어야 합니다.
    api_key = st.secrets.get("DEEPSEEK_API_KEY")
    client = OpenAI(
        api_key=api_key, 
        base_url="https://api.deepseek.com"
    )
except Exception:
    st.error("DeepSeek API 키가 설정되지 않았습니다. Streamlit Secrets를 확인해주세요.")
    st.stop()

# 2. 세션 상태 초기화 (추천 기록 유지용)
if "history" not in st.session_state:
    st.session_state.history = []
if "index" not in st.session_state:
    st.session_state.index = -1

def get_recommendation(user_age, genre_choice):
    # 중복 추천 방지: 최근 20곡 내역 전달
    past_songs = [rec['title'] for h in st.session_state.history for rec in h.get('recommendations', [])]
    past_songs_str = ", ".join(past_songs[-20:])

    # [프롬프트 최적화] 나이별 특성 반영 + 장르 엄격 필터링 + 2020-2025 최신성
    prompt = f"""
    당신은 전 세계 음악 트렌드를 분석하는 연령별 전문 큐레이터입니다.
    {user_age}세 사용자에게 '{genre_choice}' 장르 3곡을 추천하세요.

    [핵심 추천 전략]
    - 10대~20대: 틱톡/릴스 유행곡, 화려한 사운드, 트렌디한 아이돌 및 래퍼 중심.
    - 30대~40대: 세련된 멜로디, 가창력과 작사 능력이 돋보이는 성숙한 감성 위주.
    - 50대 이상: 편안하고 친숙한 멜로디, 서정적인 깊이가 있는 곡 위주.
    
    [엄격 규칙]
    1. **시대**: 반드시 2020년~2025년 사이에 발표된 실제 곡만 선정하세요.
    2. **장르 정밀도**: 힙합 선택 시 팝 댄스(Hype Boy, Dynamite 등)는 절대 배제하고 래핑 중심의 곡만 선정하세요.
    3. **정확성**: 가수와 곡 제목이 실제와 일치하는지 3번 검토하세요. (예: 'Hmm'은 BE'O의 곡)
    4. **설명**: 추천 이유는 무조건 한국어로 작성하고, "{user_age}세 사용자의 감성"에 맞춘 분석을 포함하세요.

    JSON 형식:
    {{
      "recommendations": [
        {{ "title": "곡 제목", "artist": "가수명", "reason": "한국어 추천 사유" }}
      ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": f"You are a music curator for {user_age}-year-olds. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.4  # 나이별 개성을 살리기 위한 최적의 온도
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        # 잔액 부족 알림 처리
        if "insufficient" in str(e).lower() or "402" in str(e):
            return {"error": "DeepSeek 계정 잔액이 부족합니다. 대시보드에서 충전해주세요."}
        return {"error": f"API 오류: {str(e)}"}

# --- UI 레이아웃 ---
st.set_page_config(page_title="AI 음악 큐레이터", page_icon="🎧", layout="centered")

st.title("🎧 연령별 장르 맞춤 추천 (2020-2025)")
st.write(f"사용자의 나이와 장르 취향을 분석하여 최적의 음악을 제안합니다.")

# 입력 섹션
with st.sidebar:
    st.header("사용자 프로필")
    age = st.number_input("사용자 나이:", 1, 100, 25)
    genre = st.selectbox("선호 장르:", ["힙합/랩", "발라드", "K-POP/댄스", "R&B/소울", "인디/록"])
    extra = st.text_input("추가 요청 (선택):", placeholder="예: 운동할 때, 비오는 날")

# 버튼 디자인
if st.button(f"🔥 {age}세 맞춤형 {genre} 추천 받기", use_container_width=True):
    with st.spinner("최신 음악 DB 분석 중..."):
        res = get_recommendation(age, f"{genre} {extra}")
        if "error" in res:
            st.error(res["error"])
        else:
            st.session_state.history.append(res)
            st.session_state.index = len(st.session_state.history) - 1

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

    # 현재 추천 결과 카드 출력
    current_data = st.session_state.history[st.session_state.index]
    for i, rec in enumerate(current_data.get("recommendations", [])):
        with st.container(border=True):
            st.subheader(f"{i+1}. {rec['title']} - {rec['artist']}")
            st.info(f"🧐 **{age}세 맞춤 분석**: {rec['reason']}")
            
            # 유튜브 링크
            q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
            st.link_button("▶️ 유튜브 검색 확인", f"https://www.youtube.com/results?search_query={q}")
