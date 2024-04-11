# 本项目继承Langchain-Chatchat
# <span style="color:red"> 注意，本项目config/model_config.py没有添加,	如需使用手动添加，参考https://github.com/chatchat-space/Langchain-Chatchat</span>
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
## 相关的对话信息以及api的使用在webui_page/dialogue/dialogue.py文件中
# 快速运行
`bash run.sh`
