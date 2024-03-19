import streamlit as st
from webui_pages.utils import *
from streamlit_chatbox import *
from streamlit_modal import Modal
from datetime import datetime
import os
import re
import time
from configs import (TEMPERATURE, HISTORY_LEN, PROMPT_TEMPLATES,
                     DEFAULT_KNOWLEDGE_BASE, DEFAULT_SEARCH_ENGINE, SUPPORT_AGENT_MODEL)
from server.knowledge_base.utils import LOADER_DICT
import uuid
from typing import List, Dict
from PIL import Image
global NAME_EXCEL
NAME_EXCEL = ""
chat_box = ChatBox(
    assistant_avatar=os.path.join(
        "img",
        "chatchat_icon_blue_square_v2.png"
    )
)


def get_messages_history(history_len: int, content_in_expander: bool = False) -> List[Dict]:
    '''
    返回消息历史。
    content_in_expander控制是否返回expander元素中的内容，一般导出的时候可以选上，传入LLM的history不需要
    '''

    def filter(msg):
        content = [x for x in msg["elements"] if x._output_method in ["markdown", "text"]]
        if not content_in_expander:
            content = [x for x in content if not x._in_expander]
        content = [x.content for x in content]

        return {
            "role": msg["role"],
            "content": "\n\n".join(content),
        }

    return chat_box.filter_history(history_len=history_len, filter=filter)


@st.cache_data
def upload_temp_docs(files, _api: ApiRequest) -> str:
    '''
    将文件上传到临时目录，用于文件对话
    返回临时向量库ID
    '''
    return _api.upload_temp_docs(files).get("data", {}).get("id")


def parse_command(text: str, modal: Modal) -> bool:
    '''
    检查用户是否输入了自定义命令，当前支持：
    /new {session_name}。如果未提供名称，默认为“会话X”
    /del {session_name}。如果未提供名称，在会话数量>1的情况下，删除当前会话。
    /clear {session_name}。如果未提供名称，默认清除当前会话
    /help。查看命令帮助
    返回值：输入的是命令返回True，否则返回False
    '''
    if m := re.match(r"/([^\s]+)\s*(.*)", text):
        cmd, name = m.groups()
        name = name.strip()
        conv_names = chat_box.get_chat_names()
        if cmd == "help":
            modal.open()
        elif cmd == "new":
            if not name:
                i = 1
                while True:
                    name = f"会话{i}"
                    if name not in conv_names:
                        break
                    i += 1
            if name in st.session_state["conversation_ids"]:
                st.error(f"该会话名称 “{name}” 已存在")
                time.sleep(1)
            else:
                st.session_state["conversation_ids"][name] = uuid.uuid4().hex
                st.session_state["cur_conv_name"] = name
        elif cmd == "del":
            name = name or st.session_state.get("cur_conv_name")
            if len(conv_names) == 1:
                st.error("这是最后一个会话，无法删除")
                time.sleep(1)
            elif not name or name not in st.session_state["conversation_ids"]:
                st.error(f"无效的会话名称：“{name}”")
                time.sleep(1)
            else:
                st.session_state["conversation_ids"].pop(name, None)
                chat_box.del_chat_name(name)
                st.session_state["cur_conv_name"] = ""
        elif cmd == "clear":
            chat_box.reset_history(name=name or None)
        return True
    return False


def dialogue_page(api: ApiRequest, is_lite: bool = False):
    st.session_state.setdefault("conversation_ids", {})
    st.session_state["conversation_ids"].setdefault(chat_box.cur_chat_name, uuid.uuid4().hex)
    st.session_state.setdefault("file_chat_id", None)
    default_model = api.get_default_llm_model()[0]

    if not chat_box.chat_inited:
        st.toast(
            f"欢迎使用 [`Langchain-Chatchat`](https://github.com/chatchat-space/Langchain-Chatchat) ! \n\n"
            f"当前运行的模型`{default_model}`, 您可以开始提问了."
        )
        chat_box.init_session()

    # 弹出自定义命令帮助信息
    modal = Modal("自定义命令", key="cmd_help", max_width="500")
    if modal.is_open():
        with modal.container():
            cmds = [x for x in parse_command.__doc__.split("\n") if x.strip().startswith("/")]
            st.write("\n\n".join(cmds))
    with st.sidebar:
        # 多会话
        conv_names = list(st.session_state["conversation_ids"].keys())
        index = 0
        if st.session_state.get("cur_conv_name") in conv_names:
            index = conv_names.index(st.session_state.get("cur_conv_name"))
        conversation_name = st.selectbox("当前会话：", conv_names, index=index)
        chat_box.use_chat_name(conversation_name)
        conversation_id = st.session_state["conversation_ids"][conversation_name]

        # TODO: 对话模型与会话绑定
        def on_mode_change():
            mode = st.session_state.dialogue_mode
            text = f"已切换到 {mode} 模式。"
            if mode == "知识库问答":
                cur_kb = st.session_state.get("selected_kb")
                if cur_kb:
                    text = f"{text} 当前知识库： `{cur_kb}`。"
            st.toast(text)

        dialogue_modes = ["LLM 对话",
                        "知识库问答",
                        "文件对话",
                        "搜索引擎问答",
                        "自定义Agent问答",
                        ]
        dialogue_mode = st.selectbox("请选择对话模式：",
                                     dialogue_modes,
                                     index=0,
                                     on_change=on_mode_change,
                                     key="dialogue_mode",
                                     )

        def on_llm_change():
            if llm_model:
                config = api.get_model_config(llm_model)
                if not config.get("online_api"):  # 只有本地model_worker可以切换模型
                    st.session_state["prev_llm_model"] = llm_model
                st.session_state["cur_llm_model"] = st.session_state.llm_model

        def llm_model_format_func(x):
            if x in running_models:
                return f"{x} (Running)"
            return x

        running_models = list(api.list_running_models())
        available_models = []
        config_models = api.list_config_models()
        if not is_lite:
            for k, v in config_models.get("local", {}).items(): # 列出配置了有效本地路径的模型
                if (v.get("model_path_exists")
                    and k not in running_models):
                    available_models.append(k)
        for k, v in config_models.get("online", {}).items():  # 列出ONLINE_MODELS中直接访问的模型
            if not v.get("provider") and k not in running_models:
                available_models.append(k)
        llm_models = running_models + available_models
        cur_llm_model = st.session_state.get("cur_llm_model", default_model)
        if cur_llm_model in llm_models:
            index = llm_models.index(cur_llm_model)
        else:
            index = 0
        llm_model = st.selectbox("选择LLM模型：",
                                 llm_models,
                                 index,
                                 format_func=llm_model_format_func,
                                 on_change=on_llm_change,
                                 key="llm_model",
                                 )
        if (st.session_state.get("prev_llm_model") != llm_model
                and not is_lite
                and not llm_model in config_models.get("online", {})
                and not llm_model in config_models.get("langchain", {})
                and llm_model not in running_models):
            with st.spinner(f"正在加载模型： {llm_model}，请勿进行操作或刷新页面"):
                prev_model = st.session_state.get("prev_llm_model")
                r = api.change_llm_model(prev_model, llm_model)
                if msg := check_error_msg(r):
                    st.error(msg)
                elif msg := check_success_msg(r):
                    st.success(msg)
                    st.session_state["prev_llm_model"] = llm_model

        index_prompt = {
            "LLM 对话": "llm_chat",
            "自定义Agent问答": "agent_chat",
            "搜索引擎问答": "search_engine_chat",
            "知识库问答": "knowledge_base_chat",
            "文件对话": "knowledge_base_chat",
        }
        prompt_templates_kb_list = list(PROMPT_TEMPLATES[index_prompt[dialogue_mode]].keys())
        prompt_template_name = prompt_templates_kb_list[0]
        if "prompt_template_select" not in st.session_state:
            st.session_state.prompt_template_select = prompt_templates_kb_list[0]

        def prompt_change():
            text = f"已切换为 {prompt_template_name} 模板。"
            st.toast(text)

        prompt_template_select = st.selectbox(
            "请选择Prompt模板：",
            prompt_templates_kb_list,
            index=0,
            on_change=prompt_change,
            key="prompt_template_select",
        )
        prompt_template_name = st.session_state.prompt_template_select
        temperature = st.slider("Temperature：", 0.0, 1.0, TEMPERATURE, 0.05)
        history_len = st.number_input("历史对话轮数：", 0, 20, HISTORY_LEN)

        def on_kb_change():
            st.toast(f"已加载知识库： {st.session_state.selected_kb}")

        if dialogue_mode == "知识库问答":
            with st.expander("知识库配置", True):
                kb_list = api.list_knowledge_bases()
                index = 0
                if DEFAULT_KNOWLEDGE_BASE in kb_list:
                    index = kb_list.index(DEFAULT_KNOWLEDGE_BASE)
                selected_kb = st.selectbox(
                    "请选择知识库：",
                    kb_list,
                    index=index,
                    on_change=on_kb_change,
                    key="selected_kb",
                )
                kb_top_k = st.number_input("匹配知识条数：", 1, 20, VECTOR_SEARCH_TOP_K)

                ## Bge 模型会超过1
                score_threshold = st.slider("知识匹配分数阈值：", 0.0, 2.0, float(SCORE_THRESHOLD), 0.01)
        elif dialogue_mode == "文件对话":
            with st.expander("文件对话配置", True):
                files = st.file_uploader("上传知识文件：",
                                        [i for ls in LOADER_DICT.values() for i in ls],
                                        accept_multiple_files=True,
                                        )
                kb_top_k = st.number_input("匹配知识条数：", 1, 20, VECTOR_SEARCH_TOP_K)
                
                ## Bge 模型会超过1
                score_threshold = st.slider("知识匹配分数阈值：", 0.0, 2.0, float(SCORE_THRESHOLD), 0.01)
                if st.button("开始上传", disabled=len(files)==0):
                    st.session_state["file_chat_id"] = upload_temp_docs(files, api)
        elif dialogue_mode == "搜索引擎问答":
            search_engine_list = api.list_search_engines()
            if DEFAULT_SEARCH_ENGINE in search_engine_list:
                index = search_engine_list.index(DEFAULT_SEARCH_ENGINE)
            else:
                index = search_engine_list.index("duckduckgo") if "duckduckgo" in search_engine_list else 0
            with st.expander("搜索引擎配置", True):
                search_engine = st.selectbox(
                    label="请选择搜索引擎",
                    options=search_engine_list,
                    index=index,
                )
                se_top_k = st.number_input("匹配搜索结果条数：", 1, 20, SEARCH_ENGINE_TOP_K)

    # Display chat messages from history on app rerun
    chat_box.output_messages()

    chat_input_placeholder = "请输入对话内容，换行请使用Shift+Enter。输入/help查看自定义命令 "

    def on_feedback(
        feedback,
        message_id: str = "",
        history_index: int = -1,
    ):
        reason = feedback["text"]
        score_int = chat_box.set_feedback(feedback=feedback, history_index=history_index)
        api.chat_feedback(message_id=message_id,
                          score=score_int,
                          reason=reason)
        st.session_state["need_rerun"] = True

    feedback_kwargs = {
        "feedback_type": "thumbs",
        "optional_text_label": "欢迎反馈您打分的理由",
    }


    if prompt := st.chat_input(chat_input_placeholder, key="prompt"):
        # 先判断是否输出了，再将输出赋给prompt

        ####################################################################
        #global IMPORT_IMAGE
        #IMPORT_IMAGE = 0
        #global NAME_EXCEL
        # 获得文件名称
        # 查找最后一个点的索引，即文件后缀的起始位置
        #last_dot_index = NAME_EXCEL.rfind(".")
        # 如果找到了点，截取文件名
        # if last_dot_index != -1:
        #     file_name_without_extension = NAME_EXCEL[:last_dot_index]
        # else:
        #     # 如果没有找到点，整个字符串都是文件名
        #     file_name_without_extension = NAME_EXCEL
        # if IMPORT_IMAGE>0:
        #     import pandas as pd
        #     def get_excel_info(file_path, sheet_name="Sheet1"):
        #         try:
        #             # 读取 Excel 文件
        #             df = pd.read_excel(file_path, sheet_name)
                    
        #             # 获取数据结构和列信息
        #             data_structure = df.shape
        #             column_names = df.columns.tolist()
                    
        #             # 打印信息
        #             print(f"数据结构：{data_structure}")
        #             print(f"列名：{column_names}")
                    
        #             # 返回结果
        #             return data_structure, column_names
        #         except Exception as e:
        #             print(f"发生错误：{e}")
        #             return None
        #     excel_file_path = "/home/root1/wcc/Langchain-Chatchat/save_excel/"+NAME_EXCEL  # 替换为你的 Excel 文件路径
        #     data_structure, column_names = get_excel_info(excel_file_path)
        #     pre_prompt = f'''1.如果用户想要得到对应图像，请一次性输出相应要求的全部python代码包括导入的包，\n
        #                      2.所有的对话文字全部以注释的形式给出\n
        #                      3.用户输入的表格路径为：{"/home/root1/wcc/Langchain-Chatchat/save_excel/"+NAME_EXCEL},\n
        #                      4.需要保存图像的路径为：/home/root1/wcc/Langchain-Chatchat/coding/{file_name_without_extension}.png\n
        #                      5.excel的结构为{data_structure}，excel的column_names为{column_names}\n
        #                      6.用户的要求为： {prompt}\n  '''

        if parse_command(text=prompt, modal=modal): # 用户输入自定义命令
            st.rerun()
        else:
            history = get_messages_history(history_len)
            # if IMPORT_IMAGE<=0:
            #     chat_box.user_say(prompt)
            # else:
            #     chat_box.user_say(pre_prompt)
            chat_box.user_say(prompt)
            if dialogue_mode == "LLM 对话":
                # if IMPORT_IMAGE<=0:
                chat_box.ai_say("正在思考...")
                text = ""
                message_id = ""
                r = api.chat_chat(prompt,
                                history=history,
                                conversation_id=conversation_id,
                                model=llm_model,
                                prompt_name=prompt_template_name,
                                temperature=temperature)
                for t in r:
                    if error_msg := check_error_msg(t):  # check whether error occured
                        st.error(error_msg)
                        break
                    text += t.get("text", "")
                    chat_box.update_msg(text)
                    message_id = t.get("message_id", "")
                        # print(t)
                        # global IMPORT_IMAGE
                        # if "寄" in text and IMPORT_IMAGE==1:
                        #     print("t中有地址")
                        #     image_path = "/home/root1/wcc/Langchain-Chatchat/Figure_1.png
                        #     st.image(image_path, caption=" LLM's Image", use_column_width=True)
                        #     IMPORT_IMAGE = 0
                        #     print("\n")
                        #     print(IMPORT_IMAGE)
                    # print(r)
                    # if "寄" in r:
                    #     print("<IMAGE>")
                    #     image_path = "/home/root1/wcc/Langchain-Chatchat/Figure_1.png"
                    #     st.image(image_path, caption=" LLM's Image", use_column_width=True)
                    # chat_box.update_msg(text)
                # else:
                #     chat_box.ai_say("正在思考...")
                #     text = ""
                #     message_id = ""
                #     r = api.chat_chat(pre_prompt,
                #                     history=history,
                #                     conversation_id=conversation_id,
                #                     model=llm_model,
                #                     prompt_name=prompt_template_name,
                #                     temperature=temperature)
                #     for t in r:
                #         if error_msg := check_error_msg(t):  # check whether error occured
                #             st.error(error_msg)
                #             break
                #         text += t.get("text", "")
                #         chat_box.update_msg(text)
                #         message_id = t.get("message_id", "")
                #     from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
                #     config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")
                #     user_proxy = UserProxyAgent("user_proxy", code_execution_config={"work_dir": "/home/root1/wcc/Langchain-Chatchat/coding"})
                #     def extract_code_from_input(user_input, code_start_marker="```python", code_end_marker="```"):
                #         start_index = user_input.find(code_start_marker)
                #         end_index = user_input.find(code_end_marker, start_index + len(code_start_marker))

                #         if start_index != -1 and end_index != -1:
                #             return user_input[start_index + len(code_start_marker):end_index].strip()

                #         return None

                #     content = extract_code_from_input(text)
                    
                #     code_message = {"content": content, "role": "system","language":  "python"}
                    
                #     result = user_proxy.execute_code_blocks([(code_message["language"], code_message["content"])])
                    
                #     print(result)
                    # IMPORT_IMAGE -= 0.4
                    # if IMPORT_IMAGE <=0 : 
                    #     IMPORT_IMAGE=0
                metadata = {
                    "message_id": message_id,
                    }
                #image_path = "/home/root1/wcc/Langchain-Chatchat/coding/"+file_name_without_extension+".png"
                chat_box.update_msg(text, streaming=False, metadata=metadata)  # 更新最终的字符串，去除光标
                #st.image(image_path, caption=" LLM's Image", use_column_width=True)
                print("text\n"*10+text)
                chat_box.show_feedback(**feedback_kwargs,
                                    key=message_id,
                                    on_submit=on_feedback,
                                    kwargs={"message_id": message_id, "history_index": len(chat_box.history) - 1})

            elif dialogue_mode == "自定义Agent问答":
                if not any(agent in llm_model for agent in SUPPORT_AGENT_MODEL):
                    chat_box.ai_say([
                        f"正在思考... \n\n <span style='color:red'>该模型并没有进行Agent对齐，请更换支持Agent的模型获得更好的体验！</span>\n\n\n",
                        Markdown("...", in_expander=True, title="思考过程", state="complete"),

                    ])
                else:
                    chat_box.ai_say([
                        f"正在思考...",
                        Markdown("...", in_expander=True, title="思考过程", state="complete"),

                    ])
                text = ""
                ans = ""


                global NAME_EXCEL
                # 上传文件
                import pandas as pd
                def get_excel_info(file_path, sheet_name="Sheet1"):
                    try:
                        # 读取 Excel 文件
                        df = pd.read_excel(file_path, sheet_name)
                        
                        # 获取数据结构和列信息
                        data_structure = df.shape
                        column_names = df.columns.tolist()
                        
                        # 打印信息
                        print(f"数据结构：{data_structure}")
                        print(f"列名：{column_names}")
                        
                        # 返回结果
                        return data_structure, column_names
                    except Exception as e:
                        print(f"发生错误：{e}")
                        return None
                print(NAME_EXCEL)
                excel_file_path = "/home/root1/wcc/Langchain-Chatchat/save_excel/"+NAME_EXCEL  # 替换为你的 Excel 文件路径
                data_structure, column_names = get_excel_info(excel_file_path)
                if data_structure:
                    pre_prompt = f'''
                                System message:
                                The user has upload a excel file. The path of excel file is {"/home/root1/wcc/Langchain-Chatchat/save_excel/"+NAME_EXCEL}.The file structure is {data_structure}, the first column names is {column_names},
                                You should save image just using image name. Please follow the user's instructions.
                                '''
                else:
                    pre_prompt = ""
                for d in api.agent_chat(prompt+pre_prompt,
                                        history=history,
                                        model=llm_model,
                                        prompt_name=prompt_template_name,
                                        temperature=temperature,
                                        ):
                    try:
                        d = json.loads(d)
                        # print("\n\n\n\n\nd:",d)
                    except:
                        pass
                    if error_msg := check_error_msg(d):  # check whether error occured
                        st.error(error_msg)
                    if chunk := d.get("answer"):
                        text += chunk
                        #print("chunk:answer,text",chunk)
                        chat_box.update_msg(text, element_index=1)
                    if chunk := d.get("final_answer"):
                        ans += chunk
                        #print("chunk:final_answer,ans",chunk)
                        chat_box.update_msg(ans, element_index=0)
                    if chunk := d.get("tools"):
                        text += "\n\n".join(d.get("tools", []))
                        #print("chunk:tools,text",chunk)
                        print("\ntext,tools",d.get("tools",[]))
                        chat_box.update_msg(text, element_index=1)
                print("text\n"*10+text)
                print("\ntext"*10)
                image_name = re.search(r"savefig\('(.+?)'\)",text)
                if not image_name:
                    image_name = re.search(r"savefig\(\"(.+?)\"\)",text)
                #print("image_name: ",image_name,"group(1)",image_name.group(1))
                if image_name:
                    if "/home/root1/wcc/Langchain-Chatchat" in image_name.group(1):
                        image_path = image_name.group(1)
                    else:
                        image_path = "/home/root1/wcc/Langchain-Chatchat/coding/"+image_name.group(1)
                else:
                    image_path = None
                try:
                    image = Image.open(image_path)
                    st.image(image, caption=" LLM's Image", use_column_width=True)
                    # string = "streamlit run /home/root1/wcc/Langchain-Chatchat/startup.py"
                    # code_message = {"content": string, "role": "system","language":  "shell"}
                    # results = user_proxy.execute_code_blocks([(code_message["language"], code_message["content"])])
                except Exception  as e:
                    print("Error displaying image:",e)
                chat_box.update_msg(ans, element_index=0, streaming=False)
                chat_box.update_msg(text, element_index=1, streaming=False)
            elif dialogue_mode == "知识库问答":
                chat_box.ai_say([
                    f"正在查询知识库 `{selected_kb}` ...",
                    Markdown("...", in_expander=True, title="知识库匹配结果", state="complete"),
                ])
                text = ""
                for d in api.knowledge_base_chat(prompt,
                                                knowledge_base_name=selected_kb,
                                                top_k=kb_top_k,
                                                score_threshold=score_threshold,
                                                history=history,
                                                model=llm_model,
                                                prompt_name=prompt_template_name,
                                                temperature=temperature):
                    if error_msg := check_error_msg(d):  # check whether error occured
                        st.error(error_msg)
                    elif chunk := d.get("answer"):
                        text += chunk
                        chat_box.update_msg(text, element_index=0)
                #print("text\n"*10+text)
                chat_box.update_msg(text, element_index=0, streaming=False)
                chat_box.update_msg("\n\n".join(d.get("docs", [])), element_index=1, streaming=False)
            elif dialogue_mode == "文件对话":
                if st.session_state["file_chat_id"] is None:
                        st.error("请先上传文件再进行对话")
                        st.stop()
                if prompt_template_name == "文献综述":
                    chat_box.ai_say([
                        f"正在查询`文件1`..."
                    ])
                    def convert_file(file, filename=None):
                        if isinstance(file, bytes): # raw bytes
                            file = BytesIO(file)
                        elif hasattr(file, "read"): # a file io like object
                            filename = filename or file.name
                        else: # a local path
                            file = Path(file).absolute().open("rb")
                            filename = filename or os.path.split(file.name)[-1]
                        return filename, file
                    files = [convert_file(file) for file in files]
                    print( (filename,file) for filename,file in files)
                    chat_box.update_msg("hello")
                else:
                    chat_box.ai_say([
                        f"正在查询文件 `{st.session_state['file_chat_id']}` ...",
                        Markdown("...", in_expander=True, title="文件匹配结果", state="complete"),
                    ])
                    text = ""
                    print("="*50)
                    print(prompt_template_name,"      ->prompt_template_name")
                    print("="*50)
                    for d in api.file_chat(prompt,
                                            knowledge_id=st.session_state["file_chat_id"],
                                            top_k=kb_top_k,
                                            score_threshold=score_threshold,
                                            history=history,
                                            model=llm_model,
                                            prompt_name=prompt_template_name,
                                            temperature=temperature):
                        if error_msg := check_error_msg(d):  # check whether error occured
                            st.error(error_msg)
                        elif chunk := d.get("answer"):
                            text += chunk
                            chat_box.update_msg(text, element_index=0)
                    chat_box.update_msg(text, element_index=0, streaming=False)
                    chat_box.update_msg("\n\n".join(d.get("docs", [])), element_index=1, streaming=False)
            elif dialogue_mode == "搜索引擎问答":
                chat_box.ai_say([
                    f"正在执行 `{search_engine}` 搜索...",
                    Markdown("...", in_expander=True, title="网络搜索结果", state="complete"),
                ])
                text = ""
                for d in api.search_engine_chat(prompt,
                                                search_engine_name=search_engine,
                                                top_k=se_top_k,
                                                history=history,
                                                model=llm_model,
                                                prompt_name=prompt_template_name,
                                                temperature=temperature,
                                                split_result=se_top_k > 1):
                    if error_msg := check_error_msg(d):  # check whether error occured
                        st.error(error_msg)
                    elif chunk := d.get("answer"):
                        text += chunk
                        chat_box.update_msg(text, element_index=0)
                chat_box.update_msg(text, element_index=0, streaming=False)
                chat_box.update_msg("\n\n".join(d.get("docs", [])), element_index=1, streaming=False)

    if st.session_state.get("need_rerun"):
        st.session_state["need_rerun"] = False
        st.rerun()

    now = datetime.now()
    with st.sidebar:

        cols = st.columns(2)
        export_btn = cols[0]
        if cols[1].button(
                "清空对话",
                use_container_width=True,
        ):
            chat_box.reset_history()
            st.rerun()

    export_btn.download_button(
        "导出记录",
        "".join(chat_box.export2md()),
        file_name=f"{now:%Y-%m-%d %H.%M}_对话记录.md",
        mime="text/markdown",
        use_container_width=True,
    )