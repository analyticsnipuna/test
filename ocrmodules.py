#!/usr/bin/env python
# coding: utf-8



from dotenv import load_dotenv

load_dotenv()


# In[2]:


from langchain_teddynote import logging

logging.langsmith("TeddyNote-Parser", set_enable=False)

# Streamlit에서 전달된 PDF 파일 경로를 가져오기
import sys
if len(sys.argv) < 2:
    print("❌ PDF 파일 경로가 제공되지 않았습니다. 실행 예시: python 01-Developing-Modules.py /path/to/pdf")
    sys.exit(1)

pdf_file_path = sys.argv[1]  # Streamlit에서 전달된 PDF 경로

# ## 이전 단계까지의 내용 재사용

# ### `upstage_parser_graph` 생성
# 
# - `batch_size`: 한번에 처리할 페이지 수
# - `test_page`: 테스트할 페이지 번호
# - `verbose`: 디버깅 메시지 출력 여부
# 

# In[3]:


from layoutparse.teddynote_parser import create_upstage_parser_graph

# 그래프 생성
upstage_parser_graph = create_upstage_parser_graph(
    batch_size=30, test_page=None, verbose=True, visualize=True
)


# ### `upstage_parser_graph` 사용
# 
# - `filepath`: 분석할 PDF 파일의 경로

# In[4]:


import uuid
from langchain_core.runnables import RunnableConfig
from langchain_teddynote.messages import stream_graph

# 옵션 설정
config = RunnableConfig(
    recursion_limit=300,
    configurable={"thread_id": str(uuid.uuid4())},
)

# filepath: 분석할 PDF 파일의 경로
inputs = {
    #"filepath": "data/argus-bitumen.pdf",
    "filepath": pdf_file_path
}

stream_graph(upstage_parser_graph, inputs, config=config)



# 그래프 처리를 위한 필수 라이브러리들을 임포트
from langgraph.graph import StateGraph, END
from layoutparse.state import ParseState
import layoutparse.export as export
from langchain_teddynote.graphs import visualize_graph

"""
후처리 워크플로우를 생성하고 관리하는 클래스입니다.
이미지, HTML, 마크다운, CSV 등 다양한 포맷으로 변환하는 작업을 처리합니다.
"""

# ParseState를 상태 관리자로 사용하는 StateGraph 인스턴스를 생성합니다
export_workflow = StateGraph(ParseState)

# 각각의 export 컴포넌트들을 verbose 모드로 초기화합니다
export_image = export.ExportImage(verbose=True)  # 이미지 export 담당
export_html = export.ExportHTML(verbose=True)  # HTML export 담당
export_markdown = export.ExportMarkdown(verbose=True)  # 마크다운 export 담당
export_table_csv = export.ExportTableCSV(verbose=True)  # CSV export 담당

# 워크플로우에 각 컴포넌트들을 노드로 추가합니다
export_workflow.add_node("export_image", export_image)
export_workflow.add_node("export_html", export_html)
export_workflow.add_node("export_markdown", export_markdown)
export_workflow.add_node("export_table_to_csv", export_table_csv)

# export_image 노드에서 다른 노드들로 연결되는 엣지를 추가합니다
export_workflow.add_edge("export_image", "export_html")
export_workflow.add_edge("export_image", "export_markdown")
export_workflow.add_edge("export_image", "export_table_to_csv")

# 각 export 노드에서 END로 연결되는 엣지를 추가합니다
export_workflow.add_edge("export_html", END)
export_workflow.add_edge("export_markdown", END)
export_workflow.add_edge("export_table_to_csv", END)

# 워크플로우의 시작점을 export_image로 설정합니다
export_workflow.set_entry_point("export_image")

# 워크플로우를 컴파일하고 시각화합니다
export_graph = export_workflow.compile()
visualize_graph(export_graph)


# In[7]:


# 이전 단계의 실행 결과를 사용합니다
previous_state = upstage_parser_graph.get_state(config).values


# In[ ]:


# 추출된 요소들을 확인합니다
# previous_state["elements_from_parser"][:10]


# In[9]:


# 이전 단계의 실행 결과를 복사하여 입력으로 사용합니다
inputs = previous_state.copy()


# 매번 최신 코드를 반영하기 위한 `importlib` 

# In[10]:


import importlib

# export 모듈을 새로 리로드하여 최신 상태를 유지합니다
importlib.reload(export)

# 각각의 export 컴포넌트들을 verbose 모드로 초기화합니다
export_image = export.ExportImage(verbose=True)
export_html = export.ExportHTML(verbose=True, ignore_new_line_in_text=True)
export_markdown = export.ExportMarkdown(
    verbose=True, ignore_new_line_in_text=True, show_image=False
)
export_table_csv = export.ExportTableCSV(verbose=True)


# 단계별 상태를 업데이트 후 반영합니다.

# In[11]:


inputs2 = export_image(inputs)
inputs.update(inputs2)


# In[12]:


# 반영된 결과
inputs["elements_from_parser"][-30:-25]


# In[13]:


export_html(inputs)


# 입력으로 들어가는 상태 확인

# In[14]:


inputs["elements_from_parser"][0]


# ### Markdown

# In[15]:


export_markdown(inputs)
