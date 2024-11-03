# import pytesseract
# from pdf2image import convert_from_path

# # 将PDF的每一页转换为图片
# images = convert_from_path("transformer.pdf")

# # 在Linux上，通常不需要指定tesseract_cmd
# # pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"  

# # 遍历所有图片并使用Tesseract识别文本
# for i, image in enumerate(images):
#     text = pytesseract.image_to_string(image, lang='eng')  # 使用英文语言模型
#     print(f"Page {i+1}:")
#     print(text)





# import pytesseract
# from pdf2image import convert_from_path

# def pdf_to_text_list(pdf_path):
#     # 将PDF的每一页转换为图片
#     images = convert_from_path(pdf_path, 500)  # 500是DPI设置，可以根据需要调整

#     # 初始化Tesseract引擎
#     #pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"  # 
#     # 遍历所有图片并使用Tesseract识别文本
#     text_list = []
#     for i, image in enumerate(images):
#         text = pytesseract.image_to_string(image, lang='eng')  # 使用英文语言模型
#         text_list.append(f"Page {i+1}:\n{text}\n")  # 添加页码和换行符

#     return text_list

# # 使用示例
# pdf_path = "transformer.pdf"  # 替换为您的PDF文件路径
# text_list = pdf_to_text_list(pdf_path)

# # 输出结果
# i = 1
# for text in text_list:
#     # print('-'*200)
#     # print(str(i)*200)
#     # print('\n'+'\n')
#     print(text)
#     #i+=1





from langchain.text_splitter import CharacterTextSplitter, LatexTextSplitter
import re
from typing import List
# import PyPDF2
import pytesseract
from pdf2image import convert_from_path

def extract_text_from_pdf(pdf_path):
    texts = ""
    # with open(pdf_path, 'rb') as file:
    #     reader = PyPDF2.PdfReader(file)
    images = convert_from_path(pdf_path)

    # 遍历所有图片并使用Tesseract识别文本
    for i, image in enumerate(images):
        text = pytesseract.image_to_string(image, lang='eng')  # 使用英文语言模型
        texts +=  text
        texts += '\n'        
    return texts
class AliTextSplitter(CharacterTextSplitter):
    def __init__(self, pdf: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.pdf = pdf

        def split_text(self, text: str) -> List[str]:
            if self.pdf:
                # text = re.sub(r"\n{3,}", r"\n", text)
                # text = re.sub('\s', " ", text)
                # text = re.sub("\n\n", "", text)
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
                return sent_list
pdf_path="transformer.pdf"
pdf = extract_text_from_pdf(pdf_path)
# print(pdf)
# print('\n'*10)
text_splitter = AliTextSplitter(pdf=True)
result = text_splitter.split_text(pdf)
# latex_splitter = LatexTextSplitter(chunk_size=100,chunk_overlap=0)
# docs = latex_splitter.create_documents([pdf])
for i in result:
    print("---===---"*50)
    print(i)
    