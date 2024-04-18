# import openpyxl
# import matplotlib.pyplot as plt
# import numpy as np

# # 读取Excel文件
# wb = openpyxl.load_workbook("/home/root1/wcc/Langchain-Chatchat/save_excel/test.xlsx")
# ws = wb.active

# # 获取列名
# column_names = ws[1].column_names

# # 获取数据
# data = []
# for row in ws.iter_rows(min_row=2, values_only=True):
#     data.append(row)

# # 提取x和y列的数据
# x_data = [row[0] for row in data]
# y_data = [row[1] for row in data]

# # 创建折线图
# plt.plot(x_data, y_data)
# plt.xlabel("x")
# plt.ylabel("y")
# plt.title("Line Plot")
# plt.savefig("/home/root1/wcc/Langchain-Chatchat/coding/test.png")

# # 显示图形
# plt.show()
from langchain.text_splitter import CharacterTextSplitter
import re
from typing import List
from PdfCleaner import PaperCleaner
class AliTextSplitter(CharacterTextSplitter):
    def __init__(self, pdf: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.pdf = pdf

    def split_text(self, text: str) -> List[str]:
        # use_document_segmentation参数指定是否用语义切分文档，此处采取的文档语义分割模型为达摩院开源的nlp_bert_document-segmentation_chinese-base，论文见https://arxiv.org/abs/2107.09278
        # 如果使用模型进行文档语义切分，那么需要安装modelscope[nlp]：pip install "modelscope[nlp]" -f https://modelscope.oss-cn-beijing.aliyuncs.com/releases/repo.html
        # 考虑到使用了三个模型，可能对于低配置gpu不太友好，因此这里将模型load进cpu计算，有需要的话可以替换device为自己的显卡id
        if self.pdf:
            text = re.sub(r"\n{3,}", r"\n", text)
            text = re.sub('\s', " ", text)
            text = re.sub("\n\n", "", text)
        try:
            from modelscope.pipelines import pipeline
        except ImportError:
            raise ImportError(
                "Could not import modelscope python package. "
                "Please install modelscope with `pip install modelscope`. "
            )


        p = pipeline(
            task="document-segmentation",
            model='damo/nlp_bert_document-segmentation_chinese-base',
            device="gpu")
        result = p(documents=text)
        sent_list = [i for i in result["text"].split("\n\t") if i]
        print("pdf",'-'*100)
        print(sent_list[:5][:50])
        return sent_list
pdf = PaperCleaner(path="./共产党宣言.pdf")
text_splitter = AliTextSplitter()
text_splitter.split_text(pdf.text[0])
