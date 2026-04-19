import re
import json
import streamlit as st

def parse_ai_json(ai_response: str):
    """AI 응답에서 JSON 부분을 추출하여 파싱합니다."""
    try:
        # JSON 블록 추출 ({ ... })
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        st.error(f"JSON 파싱 오류: {e}")
    return None
