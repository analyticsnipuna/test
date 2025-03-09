import streamlit as st
import os
import subprocess

# 캐시 폴더 생성
if not os.path.exists(".cache/files"):
    os.makedirs(".cache/files")

st.title("📄 PDF to Markdown Converter (Upstage Notebook)")
st.write("업로드한 PDF를 Markdown 파일로 변환합니다.")

# 파일 업로드
uploaded_file = st.file_uploader("PDF 파일 업로드", type=["pdf"])

if uploaded_file:
    # 저장할 파일 경로 설정
    file_path = os.path.join(".cache/files", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success("✅ 파일 업로드 완료!")

    # 변환 실행 버튼
    if st.button("📄 변환 시작"):
        with st.spinner("⏳ 변환 중... 잠시만 기다려 주세요."):
            # Jupyter Notebook 실행 (Python 변환된 코드 실행)
            result = subprocess.run(["python", "00Upstage.py", file_path], capture_output=True, text=True)

            if result.returncode == 0:
                st.success("✅ 변환 완료!")
                md_file_path = file_path.replace(".pdf", ".md")

                if os.path.exists(md_file_path):
                    with open(md_file_path, "r", encoding="utf-8") as md_file:
                        markdown_data = md_file.read()
                    st.download_button(label="📥 Markdown 다운로드", data=markdown_data, file_name=os.path.basename(md_file_path), mime="text/markdown")
                else:
                    st.error("🚨 변환된 Markdown 파일을 찾을 수 없습니다.")
            else:
                st.error("🚨 변환 중 오류 발생! 오류 로그:")
                st.text(result.stderr)
