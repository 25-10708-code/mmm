import streamlit as st
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import json

# 세션 상태 초기화 (결과 저장용)
if "poster_image" not in s:
    s.poster_image = None
if "recommendations" not in s:
    s.recommendations = None

# 스트림릿 페이지 설정
st.set_page_config(page_title="인생의 사운드트랙 (Life OST)", page_icon="🎬", layout="centered")

st.title("🎬 인생의 사운드트랙 (Life-Movie OST)")
st.subheader("오늘 당신의 하루를 영화로 만든다면 어울릴 OST는?")
st.write("오늘 있었던 일이나 감정을 한두 줄로 적어주세요. AI가 당신만을 위한 영화 포스터와 OST를 선물합니다.")

# 사이드바 - API 키 입력 (안전한 실행을 위함)
with st.sidebar:
    st.header("설정")
    api_key = st.text_input("OpenAI API Key를 입력하세요", type="password")
    st.markdown("[OpenAI API Key 발급받기](https://platform.openai.com/api-keys)")

# 메인 입력창
user_diary = st.text_area("✍️ 오늘의 일기 (한두 줄로 자유롭게 적어보세요)", placeholder="예: 오늘 중요한 미팅이 끝났다. 시원섭섭하지만 홀가분하다. 퇴근길 노을이 예쁘네.")

# 포스터에 사용할 감성 배경 테마 선택
theme_color = st.selectbox("🎨 포스터의 감성 테마 선택", ["새벽 감성 (Dark blue)", "따뜻한 위로 (Warm Beige)", "오늘의 열정 (Sunset Red)", "차분한 하루 (Minimal Gray)"])

# 테마별 색상 정의
color_map = {
    "새벽 감성 (Dark blue)": (20, 24, 45),
    "따뜻한 위로 (Warm Beige)": (245, 242, 235),
    "오늘의 열정 (Sunset Red)": (64, 25, 25),
    "차분한 하루 (Minimal Gray)": (240, 240, 240)
}
text_color_map = {
    "새벽 감성 (Dark blue)": (255, 255, 255),
    "따뜻한 위로 (Warm Beige)": (40, 40, 40),
    "오늘의 열정 (Sunset Red)": (255, 230, 230),
    "차분한 하루 (Minimal Gray)": (50, 50, 50)
}

# --- 로직 함수들 ---

def analyze_and_recommend(diary_text, client):
    """일기를 분석하여 감정 태그, 영화 제목, 추천 OST 3곡을 반환합니다."""
    prompt = f"""
    사용자가 쓴 오늘 하루의 일기입니다:
    "{diary_text}"
    
    이 일기의 감정선을 분석해서 다음 정보를 포함한 JSON 형태로만 응답해주세요. (마크다운 block 쓰지 마세요)
    {{
        "emotion_tag": "분석된 핵심 감정 단어 하나 (예: 홀가분함, 쓸쓸함, 잔잔한 기쁨)",
        "movie_title": "이 하루를 영화로 만든다면 어울릴 가상의 감성적인 영화 제목",
        "ost_list": [
            {{"title": "곡 제목 1", "artist": "아티스트 1", "reason": "이 곡을 추천하는 위로의 한마디"}},
            {{"title": "곡 제목 2", "artist": "아티스트 2", "reason": "이 곡을 추천하는 위로의 한마디"}},
            {{"title": "곡 제목 3", "artist": "아티스트 3", "reason": "이 곡을 추천하는 위로의 한마디"}}
        ]
    }}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=
