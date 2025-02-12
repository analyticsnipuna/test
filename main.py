from typing import List, Union
from langchain_experimental.tools import PythonAstREPLTool
from langchain_teddynote import logging
from langchain_teddynote.messages import AgentStreamParser, AgentCallbacks
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

##### 폰트 설정 #####
import platform

# OS 판단
current_os = platform.system()

if current_os == "Windows":
    # Windows 환경 폰트 설정
    font_path = "C:/Windows/Fonts/malgun.ttf"  # 맑은 고딕 폰트 경로
    fontprop = fm.FontProperties(fname=font_path, size=12)
    plt.rc("font", family=fontprop.get_name())
elif current_os == "Darwin":  # macOS
    # Mac 환경 폰트 설정
    plt.rcParams["font.family"] = "AppleGothic"
else:  # Linux 등 기타 OS
    if "NanumGothic" in fm.findSystemFonts():
        plt.rcParams["font.family"] = "NanumGothic"
    else:
        print("⚠️ NanumGothic 폰트를 찾을 수 없습니다. 시스템 기본 폰트 사용.")
        plt.rcParams["font.family"] = "sans-serif"
# else:  # Linux 등 기타 OS
#     # 기본 한글 폰트 설정 시도
#     try:
#         plt.rcParams["font.family"] = "NanumGothic"
#     except:
#         print("한글 폰트를 찾을 수 없습니다. 시스템 기본 폰트를 사용합니다.")

##### 마이너스 폰트 깨짐 방지 #####
plt.rcParams["axes.unicode_minus"] = False  # 마이너스 폰트 깨짐 방지

# API 키 및 프로젝트 설정
load_dotenv()
logging.langsmith("설문데이터 챗본")

# Streamlit 앱 설정
st.title("CSV 데이터 분석 챗봇 💬")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = []  # 대화 내용을 저장할 리스트 초기화


# 상수 정의
class MessageRole:
    """
    메시지 역할을 정의하는 클래스입니다.
    """

    USER = "user"  # 사용자 메시지 역할
    ASSISTANT = "assistant"  # 어시스턴트 메시지 역할


class MessageType:
    """
    메시지 유형을 정의하는 클래스입니다.
    """

    TEXT = "text"  # 텍스트 메시지
    FIGURE = "figure"  # 그림 메시지
    CODE = "code"  # 코드 메시지
    DATAFRAME = "dataframe"  # 데이터프레임 메시지


# 메시지 관련 함수
def print_messages():
    """
    저장된 메시지를 화면에 출력하는 함수입니다.
    """
    for role, content_list in st.session_state["messages"]:
        with st.chat_message(role):
            for content in content_list:
                if isinstance(content, list):
                    message_type, message_content = content
                    if message_type == MessageType.TEXT:
                        st.markdown(message_content)  # 텍스트 메시지 출력
                    elif message_type == MessageType.FIGURE:
                        st.pyplot(message_content)  # 그림 메시지 출력
                    elif message_type == MessageType.CODE:
                        with st.status("코드 출력", expanded=False):
                            st.code(
                                message_content, language="python"
                            )  # 코드 메시지 출력
                    elif message_type == MessageType.DATAFRAME:
                        st.dataframe(message_content)  # 데이터프레임 메시지 출력
                else:
                    raise ValueError(f"알 수 없는 콘텐츠 유형: {content}")


def add_message(role: MessageRole, content: List[Union[MessageType, str]]):
    """
    새로운 메시지를 저장하는 함수입니다.

    Args:
        role (MessageRole): 메시지 역할 (사용자 또는 어시스턴트)
        content (List[Union[MessageType, str]]): 메시지 내용
    """
    messages = st.session_state["messages"]
    if messages and messages[-1][0] == role:
        messages[-1][1].extend([content])  # 같은 역할의 연속된 메시지는 하나로 합칩니다
    else:
        messages.append([role, [content]])  # 새로운 역할의 메시지는 새로 추가합니다


# 사이드바 설정
with st.sidebar:
    clear_btn = st.button("대화 초기화")  # 대화 내용을 초기화하는 버튼
    uploaded_file = st.file_uploader(
        "CSV 파일을 업로드 해주세요.", type=["csv"]
    )  # CSV 파일 업로드 기능
    selected_model = st.selectbox(
        "OpenAI 모델을 선택해주세요.", 
        ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"], 
        index=0
    )  # OpenAI 모델 선택 옵션
    uploaded_txt = st.file_uploader(
        "컬럼 가이드라인 TXT파일을 업로드 해주세요.", type=["txt"]
    )  # 컬럼 가이드라인 업로드


    # 세션 상태 초기화 (프롬프트 기본값)
    if "user_prefix_prompt" not in st.session_state:
        st.session_state["user_prefix_prompt"] = (
            "1. Please answer excluding null values ​​in the data, and if you excluded them, please tell me how many were excluded.\
            2. Please provide an answer to the analysis by itemizing them into 3~4 bullet points with reference to examples of analysis results.\
                - Question: How is short-form content usually consumed?\
                - Examples of analysis results:\
                    * Short-form users mainly consume content based on recommendations from the algorithm.\
                    * More than 70% of all short-form users consume videos recommended by the algorithm.\
                    * The proportion of those who consume only videos that appear in the algorithm is 29.0%.\
            3. When there are 2 dimensions to analyze, please show them in the form of cross-tabulation.\
            4. MUST SHOW all data along with the **calculated statistical values**, so that you can draw conclusions based on the numbers.\
            5. All answers MUST be written in Korean."
        )

    # if "user_postfix_prompt" not in st.session_state:
    #     st.session_state["user_postfix_prompt"] = (
    #         "1.통찰을 반드시 요약하고, 주요 수치는 그래프로 시각화해주세요.\
    #         2.데이터에 대한 집계 결과를 이야기할 때는 가독성을 위해서 표 형태로 보여주세요."
    #     )
    # 사용자 입력 필드
    user_prefix_prompt = st.text_area(
        "사전 프롬프트 (prefix_prompt):",
        key="user_prefix_prompt",
    )

    user_postfix_prompt = st.text_area(
        "후속 프롬프트 (postfix_prompt):",
        key="user_postfix_prompt",
    )

    apply_btn = st.button("데이터 분석 시작")  # 데이터 분석을 시작하는 버튼

    # txt_column_guideline = st.empty()


##### 1️⃣ LABELS.txt에서 컬럼 및 값 매핑 자동 생성 #####
def extract_mappings(label_file):
    """LABELS.txt에서 컬럼 이름과 값 매핑을 추출하여 딕셔너리로 변환"""
    column_mapping = {}
    value_mapping = {}

    lines = label_file.getvalue().decode("utf-8").splitlines()

    current_section = None  # "VARIABLE LABELS" or "VALUE LABELS" 구분

    for line in lines:
        line = line.strip()
        if not line or line.startswith("/"):  # 빈 줄 또는 주석 제외
            continue
        
        if "VARIABLE LABELS" in line:
            current_section = "VARIABLE"
            continue
        elif "VALUE LABELS" in line:
            current_section = "VALUE"
            continue
        
        # 컬럼명 매핑 저장
        if current_section == "VARIABLE":
            parts = line.split("\"")
            if len(parts) >= 2:
                col_name = parts[0].strip()
                col_label = parts[1].strip()

                # 중괄호 포함된 질문은 제외
                if "{" in col_label or "}" in col_label:
                    print(f"⚠️ WARNING: 중괄호 포함된 질문 제외: {col_label}")
                    continue
                
                column_mapping[col_name] = col_label  # 컬럼 이름 매핑 저장
        
        # 데이터 값 매핑 저장
        elif current_section == "VALUE":
            parts = line.split()
            if len(parts) < 2:
                continue  # 데이터가 부족하면 건너뛰기
            
            col_name = parts[0].strip()
            if col_name not in value_mapping:
                value_mapping[col_name] = {}

            for i in range(1, len(parts)-1, 2):  # 짝수 개의 값을 읽어야 하므로 len(parts)-1까지 범위 설정
                try:
                    value_mapping[col_name][parts[i]] = parts[i+1].strip("\"")
                except IndexError:
                    print(f"⚠️ WARNING: 잘못된 VALUE LABELS 라인: {line}")  # 문제 발생 시 디버깅 메시지 출력

    return column_mapping, value_mapping


##### 2️⃣ CSV 데이터 로드 및 매핑 적용 #####
def load_and_transform_data(csv_file, column_mapping, value_mapping):
    """CSV 데이터를 로드하고 컬럼명 및 값 매핑을 적용"""
    df = pd.read_csv(csv_file)

    # 컬럼명 매핑 적용
    df.rename(columns=column_mapping, inplace=True)

    # 값 매핑 적용 (숫자 → 라벨)
    for col in df.columns:
        if col in value_mapping:  # 해당 컬럼에 대한 매핑이 존재하면 변환
            df[col] = df[col].astype(str).map(value_mapping[col]).fillna(df[col])

    return df




# 콜백 함수
def tool_callback(tool) -> None:
    """
    도구 실행 결과를 처리하는 콜백 함수입니다.

    Args:
        tool (dict): 실행된 도구 정보
    """
    if tool_name := tool.get("tool"):
        if tool_name == "python_repl_tool":
            tool_input = tool.get("tool_input", {})
            query = tool_input.get("code")
            if query:
                df_in_result = None
                with st.status("데이터 분석 중...", expanded=True) as status:
                    st.markdown(f"```python\n{query}\n```")
                    add_message(MessageRole.ASSISTANT, [MessageType.CODE, query])
                    if "df" in st.session_state:
                        result = st.session_state["python_tool"].invoke(
                            {"query": query}
                        )
                        if isinstance(result, pd.DataFrame):
                            df_in_result = result
                    status.update(label="코드 출력", state="complete", expanded=False)

                if df_in_result is not None:
                    st.dataframe(df_in_result)
                    add_message(
                        MessageRole.ASSISTANT, [MessageType.DATAFRAME, df_in_result]
                    )

                if "plt.show" in query:
                    fig = plt.gcf()
                    st.pyplot(fig)
                    add_message(MessageRole.ASSISTANT, [MessageType.FIGURE, fig])

                return result
            else:
                st.error(
                    "데이터프레임이 정의되지 않았습니다. CSV 파일을 먼저 업로드해주세요."
                )
                return


def observation_callback(observation) -> None:
    """
    관찰 결과를 처리하는 콜백 함수입니다.

    Args:
        observation (dict): 관찰 결과
    """
    if "observation" in observation:
        obs = observation["observation"]
        if isinstance(obs, str) and "Error" in obs:
            st.error(obs)
            st.session_state["messages"][-1][
                1
            ].clear()  # 에러 발생 시 마지막 메시지 삭제


def result_callback(result: str) -> None:
    """
    최종 결과를 처리하는 콜백 함수입니다.

    Args:
        result (str): 최종 결과
    """
    pass  # 현재는 아무 동작도 하지 않습니다


# 에이전트 생성 함수
def create_agent(
    dataframe,
    selected_model="gpt-4o",
    user_prefix_prompt=None,
    user_postfix_prompt=None,
    # user_column_guideline=None,
):
    """
    데이터프레임 에이전트를 생성하는 함수입니다.

    Args:
        dataframe (pd.DataFrame): 분석할 데이터프레임
        selected_model (str, optional): 사용할 OpenAI 모델. 기본값은 "gpt-4o"

    Returns:
        Agent: 생성된 데이터프레임 에이전트
    """
    from dataanalysis import DataAnalysisAgent

    return DataAnalysisAgent(
        dataframe,
        model_name=selected_model,
        prefix_prompt=user_prefix_prompt,
        postfix_prompt=user_postfix_prompt,
        # column_guideline=user_column_guideline,
    )


# 질문 처리 함수
def ask(query):
    """
    사용자의 질문을 처리하고 응답을 생성하는 함수입니다.

    Args:
        query (str): 사용자의 질문
    """
    if "agent" in st.session_state:
        st.chat_message("user").write(query)
        add_message(MessageRole.USER, [MessageType.TEXT, query])

        agent = st.session_state["agent"]
        response = agent.stream(query, "abc123")

        ai_answer = ""
        parser_callback = AgentCallbacks(
            tool_callback, observation_callback, result_callback
        )
        stream_parser = AgentStreamParser(parser_callback)

        with st.chat_message("assistant"):
            for step in response:
                stream_parser.process_agent_steps(step)
                if "output" in step:
                    ai_answer += step["output"]
            st.write(ai_answer)

        add_message(MessageRole.ASSISTANT, [MessageType.TEXT, ai_answer])




# 메인 로직
if clear_btn:
    st.session_state["messages"] = []  # 대화 내용 초기화

if apply_btn and uploaded_file and uploaded_txt:
    column_mapping, value_mapping = extract_mappings(uploaded_txt)  # 매핑 딕셔너리 생성
    loaded_data = load_and_transform_data(uploaded_file, column_mapping, value_mapping)  # CSV 데이터 변환
    st.session_state["df"] = loaded_data  # 데이터프레임 저장
    st.session_state["python_tool"] = PythonAstREPLTool()  # Python 실행 도구 생성
    st.session_state["python_tool"].locals[
        "df"
    ] = loaded_data  # 데이터프레임을 Python 실행 환경에 추가
    st.session_state["agent"] = create_agent(
        loaded_data,
        selected_model,
        user_prefix_prompt=None,
        user_postfix_prompt=None,
        # user_column_guideline=user_column_guideline,
    )  # 에이전트 생성

    st.success("설정이 완료되었습니다. 대화를 시작해 주세요!")
elif apply_btn:
    st.warning("파일을 업로드 해주세요.")


# if "agent" in st.session_state:
#     updated_column_guideline = txt_column_guideline.markdown(
#         f"**컬럼 가이드라인**\n\n```\n{st.session_state['agent'].column_guideline}\n```"
#     )

print_messages()  # 저장된 메시지 출력

user_input = st.chat_input("궁금한 내용을 물어보세요!")  # 사용자 입력 받기
if user_input:
    ask(user_input)  # 사용자 질문 처리
