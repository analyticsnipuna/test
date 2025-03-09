import streamlit as st
import os
import subprocess

# 캐시 폴더 생성
if not os.path.exists(".cache/files"):
    os.makedirs(".cache/files")

st.title("📄 PDF to Markdown & HTML Converter")
st.write("업로드한 PDF를 Markdown 및 HTML 파일로 변환합니다.")

# 파일 업로드
uploaded_file = st.file_uploader("PDF 파일 업로드", type=["pdf"])

# Session State 초기화 (최초 실행 시)
if "md_file_path" not in st.session_state:
    st.session_state["md_file_path"] = None
if "html_file_path" not in st.session_state:
    st.session_state["html_file_path"] = None
if "converted" not in st.session_state:
    st.session_state["converted"] = False  # 변환 여부 체크

if uploaded_file:
    # 저장할 파일 경로 설정
    file_path = os.path.join(".cache/files", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success("✅ 파일 업로드 완료!")

    # 변환 실행 (이미 변환되었으면 다시 실행 안 함)
    if not st.session_state["converted"]:
        with st.spinner("⏳ 변환 중... 잠시만 기다려 주세요."):
            # Jupyter Notebook 실행 (Python 변환된 코드 실행)
            result = subprocess.run(["python", "02-Developing-Modules.py", file_path], capture_output=True, text=True)

            if result.returncode == 0:
                st.success("✅ 변환 완료!")

                # 변환된 파일 경로 설정
                md_file_path = file_path.replace(".pdf", ".md")
                html_file_path = file_path.replace(".pdf", ".html")

                # 변환된 파일 경로를 Session State에 저장
                st.session_state["md_file_path"] = md_file_path
                st.session_state["html_file_path"] = html_file_path
                st.session_state["converted"] = True  # 변환 완료 상태

    # 변환된 파일 다운로드 버튼 (변환이 완료되었을 때만 표시)
    if st.session_state["converted"]:
        # Markdown 다운로드 버튼
        if os.path.exists(st.session_state["md_file_path"]):
            with open(st.session_state["md_file_path"], "r", encoding="utf-8") as md_file:
                markdown_data = md_file.read()
            st.download_button(label="📥 Markdown 다운로드", data=markdown_data, file_name=os.path.basename(st.session_state["md_file_path"]), mime="text/markdown")

        # HTML 다운로드 버튼
        if os.path.exists(st.session_state["html_file_path"]):
            with open(st.session_state["html_file_path"], "r", encoding="utf-8") as html_file:
                html_data = html_file.read()
            st.download_button(label="📥 HTML 다운로드", data=html_data, file_name=os.path.basename(st.session_state["html_file_path"]), mime="text/html")
