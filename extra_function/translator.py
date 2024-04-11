from openai import OpenAI
import requests
import simplejson
import time
import os
import sys
from loguru import logger
from typing import List
from .PdfCleaner import PaperCleaner
from configs.model_config import ONLINE_LLM_MODEL
from typing import Generator
LOG_FILE = "translation.log"
ROTATION_TIME = "02:00"
class Logger:
    def __init__(self, name="translation", log_dir="logs", debug=False):
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file_path = os.path.join(log_dir, LOG_FILE)

        # Remove default loguru handler
        logger.remove()

        # Add console handler with a specific log level
        level = "DEBUG" if debug else "INFO"
        logger.add(sys.stdout, level=level)
        # Add file handler with a specific log level and timed rotation
        logger.add(log_file_path, rotation=ROTATION_TIME, level="DEBUG")
        self.logger = logger

LOG = Logger(debug=True).logger
client = OpenAI(api_key = ONLINE_LLM_MODEL["openai-api"]["api_key"])
class OpenAIModel():
    def __init__(self, model: str):
        self.model = model
    def make_request(self, prompt):
        attempts = 0
        while attempts < 3:
            try:
                if self.model == "gpt-3.5-turbo":
                    response = client.chat.completions.create(model=self.model,
                                                            #   api_key=self.api_key,
                    messages=[
                        {"role": "user", "content": prompt}
                    ])
                    translation = response.choices[0].message.content.strip()
                else:
                    response = client.completions.create(model=self.model,
                    prompt=prompt,
                    max_tokens=150,
                    temperature=0)
                    translation = response.choices[0].text.strip()
                print(translation)
                return translation, True
            except Exception as e:
                attempts += 1
                if attempts < 3:
                    LOG.warning("Rate limit reached. Waiting for 60 seconds before retrying.")
                    time.sleep(30)
                else:
                    raise Exception("Rate limit reached. Maximum attempts exceeded.")
                print(e)
        return "", False
class PDFTranslator:
    def __init__(self, model):
        self.model = model
        self.prompt = """你是翻译论文方面的专家，以下给出相应的论文内容，请进行翻译。注意，
        1. 每句话都要翻译.
        2. 如果遇到你不确定的词汇，请在你翻译的这个词之后直接用小括号标注原文的这个词
        3. 翻译要做到语言连贯，上下文内容衔接。
        以下给出相应的论文内容，请开始进行翻译:\n"""

    def translate_pdf(self,texts: List[str]) -> Generator[str,None,None]:
        for index,text in enumerate(texts):
            yield f"\033[30m\033[1m第 {index + 1}页的翻译\033[0m\033[0m\n" + self.model.make_request(self.prompt + text)[0] 

            
