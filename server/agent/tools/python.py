from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
from pydantic import BaseModel, Field
import streamlit as st
import re
from PIL import Image
def python(string: str):
    print("python函数:\n",string)
    config_list = config_list_from_json(env_or_file="/home/root1/wcc/Langchain-Chatchat/server/agent/tools/OAI_CONFIG_LIST")
    user_proxy = UserProxyAgent("user_proxy", code_execution_config={"work_dir": "/home/root1/wcc/Langchain-Chatchat/coding"})
    code_message = {"content": string, "role": "system","language":  "python"}
    result = user_proxy.execute_code_blocks([(code_message["language"], code_message["content"])])
#     image_name = re.search(r"savefig\('(.+?)'\)",string)
#     if not image_name:
#          image_name = re.search(r"savefig\(\"(.+?)\"\)",string)
#     print("image_name: ",image_name,"group(1)",image_name.group(1))
#     if image_name:
#          image_path = "/home/root1/wcc/Langchain-Chatchat/coding/"+image_name.group(1)
#     else:
#          image_path = None
#     try:
#          image = Image.open(image_path)
#          st.image(image, caption=" LLM's Image", use_column_width=True)
#          string = "streamlit run /home/root1/wcc/Langchain-Chatchat/startup.py"
#          code_message = {"content": string, "role": "system","language":  "shell"}
#          results = user_proxy.execute_code_blocks([(code_message["language"], code_message["content"])])
    
#     except Exception  as e:
#          print("Error displaying image:",e)
    return result
class PythonInput(BaseModel):
     string: str = Field(description="一个能在python解释器运行的python代码")