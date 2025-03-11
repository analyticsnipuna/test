import streamlit as st
import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import List

# 환경 변수 로드
load_dotenv()

st.set_page_config(page_title="Meta Prompt Generator", layout="wide")
st.title("🧠 Meta Prompt Generator")
st.write("AI 기반으로 사용자 요구사항을 반영한 완벽한 프롬프트를 생성합니다.")

# OpenAI API 모델 설정
MODEL_NAME = "gpt-4"
llm = ChatOpenAI(temperature=0, model=MODEL_NAME)

# 프롬프트를 만들기 위해 반드시 물어볼 4가지 질문
REQUIRED_QUESTIONS = [
    "프롬프트의 목표는 무엇인가요?",
    "어떤 변수가 프롬프트 템플릿에 전달될 것인가요?",
    "출력 결과에서 절대로 하지 않아야 할 것은 무엇인가요?",
    "출력 결과가 반드시 준수해야 하는 요구사항은 무엇인가요?"
]

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0
if "final_prompt" not in st.session_state:
    st.session_state.final_prompt = None

# 대화 UI 출력
for chat in st.session_state.messages:
    with st.chat_message("user" if chat["role"] == "user" else "assistant"):
        st.write(chat["content"])

# 현재 질문 표시
if st.session_state.current_question_index < len(REQUIRED_QUESTIONS):
    current_question = REQUIRED_QUESTIONS[st.session_state.current_question_index]
    with st.chat_message("assistant"):
        st.write(current_question)

    user_input = st.chat_input("답변을 입력하세요:")

    if user_input:
        st.session_state.answers[current_question] = user_input
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.current_question_index += 1
        st.rerun()
else:
    if st.session_state.final_prompt is None:
        # 모든 질문에 답변을 받았을 때 최종 프롬프트 생성
        META_PROMPT = """Given a task description or existing prompt, produce a detailed system prompt to guide a language model in completing the task effectively.

# Guidelines

- Understand the Task: Grasp the main objective, goals, requirements, constraints, and expected output.
- Minimal Changes: If an existing prompt is provided, improve it only if it's simple. For complex prompts, enhance clarity and add missing elements without altering the original structure.
- Reasoning Before Conclusions**: Encourage reasoning steps before any conclusions are reached. ATTENTION! If the user provides examples where the reasoning happens afterward, REVERSE the order! NEVER START EXAMPLES WITH CONCLUSIONS!
    - Reasoning Order: Call out reasoning portions of the prompt and conclusion parts (specific fields by name). For each, determine the ORDER in which this is done, and whether it needs to be reversed.
    - Conclusion, classifications, or results should ALWAYS appear last.
- Examples: Include high-quality examples if helpful, using placeholders [in brackets] for complex elements.
   - What kinds of examples may need to be included, how many, and whether they are complex enough to benefit from placeholders.
- Clarity and Conciseness: Use clear, specific language. Avoid unnecessary instructions or bland statements.
- Formatting: Use markdown features for readability. DO NOT USE ``` CODE BLOCKS UNLESS SPECIFICALLY REQUESTED.
- Preserve User Content: If the input task or prompt includes extensive guidelines or examples, preserve them entirely, or as closely as possible. If they are vague, consider breaking down into sub-steps. Keep any details, guidelines, examples, variables, or placeholders provided by the user.
- Constants: DO include constants in the prompt, as they are not susceptible to prompt injection. Such as guides, rubrics, and examples.
- Output Format: Explicitly the most appropriate output format, in detail. This should include length and syntax (e.g. short sentence, paragraph, JSON, etc.)
    - For tasks outputting well-defined or structured data (classification, JSON, etc.) bias toward outputting a JSON.
    - JSON should never be wrapped in code blocks (```) unless explicitly requested.

# Based on the following requirements, write a good prompt template:

{reqs}
""".format(
            reqs=f"""
            - Objective: {st.session_state.answers[REQUIRED_QUESTIONS[0]]}
            - Variables: {st.session_state.answers[REQUIRED_QUESTIONS[1]]}
            - Constraints: {st.session_state.answers[REQUIRED_QUESTIONS[2]]}
            - Requirements: {st.session_state.answers[REQUIRED_QUESTIONS[3]]}
            """
        )

        response = llm.invoke([SystemMessage(content=META_PROMPT)])
        st.session_state.final_prompt = response if isinstance(response, str) else response["content"]

    with st.chat_message("assistant"):
        st.write("### 🎯 최적의 프롬프트:")
        st.code(st.session_state.final_prompt)
