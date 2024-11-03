from typing import List
from langchain.document_loaders.unstructured import UnstructuredFileLoader
import tqdm
from magic_pdf import DiskReaderWriter, UNIPipe
import os
class RapidOCRPDFLoader(UnstructuredFileLoader):
    def _get_elements(self) -> List:
        def pdf2text(filepath):
            import fitz # pyMuPDF里面的fitz包，不要与pip install fitz混淆
            from rapidocr_onnxruntime import RapidOCR
            import numpy as np
            ocr = RapidOCR()
            doc = fitz.open(filepath)
            resp = ""

            b_unit = tqdm.tqdm(total=doc.page_count, desc="RapidOCRPDFLoader context page index: 0")
            for i, page in enumerate(doc):

                # 更新描述
                b_unit.set_description("RapidOCRPDFLoader context page index: {}".format(i))
                # 立即显示进度条更新结果
                b_unit.refresh()
                # TODO: 依据文本与图片顺序调整处理方式
                text = page.get_text("")
                resp += text + "\n"

                img_list = page.get_images()
                for img in img_list:
                    pix = fitz.Pixmap(doc, img[0])
                    img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, -1)
                    result, _ = ocr(img_array)
                    if result:
                        ocr_result = [line[1] for line in result]
                        resp += "\n".join(ocr_result)

                # 更新进度
                b_unit.update(1)
            return resp

        text = pdf2text(self.file_path)
        from unstructured.partition.text import partition_text
        return partition_text(text=text, **self.unstructured_kwargs)


class MinerUPDFLoader(UnstructuredFileLoader):
    def _get_elements(self) -> List:
        def pdf2text(local_image_dir):
            image_writer = DiskReaderWriter(local_image_dir)
            image_dir = str(os.path.basename(local_image_dir))
            jso_useful_key = {"_pdf_type": "", "model_list": []}
            with open(local_image_dir, 'rb') as f:
                pdf_bytes = f.read()

            pipe = UNIPipe(pdf_bytes, jso_useful_key, image_writer)
            pipe.pipe_classify()
            pipe.pipe_analyze()
            pipe.pipe_parse()
            md_content = pipe.pipe_mk_markdown(image_dir, drop_mode="none")
            return md_content

        text = pdf2text(self.file_path)
        return text


if __name__ == "__main__":
    #loader = RapidOCRPDFLoader(file_path="../tests/samples/ocr_test.pdf")
    loader = MinerUPDFLoader(file_path="../transformer.pdf")

    docs = loader.load()
    print(docs)
