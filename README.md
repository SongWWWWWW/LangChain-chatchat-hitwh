# 本项目继承Langchain-Chatchat


> [!IMPORTANT]
> 本项目中 config/model_config.py 没有添加，如果需要，请移步https://github.com/chatchat-space/Langchain-Chatchat
> 本项目默认用语言模型ChatGLM3-6B和嵌入模型BAAI/bge-large-zh
>```bash
>git lfs install
>git clone https://huggingface.co/THUDM/chatglm3-6b
>git clone https://huggingface.co/BAAI/bge-large-zh
>```
>初始化知识库和配置文件
>```python
>python copy_config_example.py
>python init_database.py --recreate-vs
>```
>更多内容请看项目简介https://github.com/chatchat-space/Langchain-Chatchat/wiki/


# 按照下面步骤进行环境配置
```bash
conda create -n chatchat python=3.10
conda activate chatchat
```
```python
pip install -r requirements.txt 
pip install -r requirements_api.txt
pip install -r requirements_webui.txt
```
## 相关的对话信息以及api的使用在
[webui_page/dialogue/dialogue.py](https://github.com/SongWWWWWW/LangChain-chatchat-hitwh/blob/main/webui_pages/dialogue/dialogue.py)
# 快速运行
`bash run.sh`
