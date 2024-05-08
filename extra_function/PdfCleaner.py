import os,sys
sys.path.append(os.path.dirname(__file__))
import fitz # pyMuPDF里面的fitz包，不要与pip install fitz混淆
from rapidocr_onnxruntime import RapidOCR
import numpy as np
from typing import List,Tuple,Optional
import tqdm
import re
from logger import Logger
RECOGNIZE_SENTENCE_LEN = 50
NUM_PERCENT = 0.6
class TitleTree:
    # 用单引号来包裹自身类作为参数传递，来解决无法将自身作为参数传递的问题
    def __init__(self, value:List[int]=[], parent: 'TitleTree' =None) -> None:
        self.value = value
        self.parent = parent
        self.sons : List[TitleTree] = []
class PaperCleaner:
    def __init__(self,path: str,debug=None) -> None:
        self.logger = Logger().get_logger
        self.RECOGNIZE_SENTENCE_LEN = 40 #识别句子的长度,找表格描述时小于这个长度被认为是疑似表格内容
        self.paper_path = path # pdf的path
        self.NUM_PERCENT = 0.4 # 句子被认为是表格内容的数字比例
        self.text :List[str] = None # paper原文本内容
        self.cleaned_text: List[str]=None # 删除table内容后的文本内容
        self.paper_table_name_type = 0 # 用来解决table的name的匹配问题
        self.paper_table_position_type = 0 # 用来解决table的内容的位置问题，0：在下方，1：在上方
        self.debug = debug
        self.MINI_LINES = 10 # 超短句子，被认为是表格的内容
        self.title_pattern = None # 用于确定title的模式
        self.title_tree = TitleTree(value=[])
        self.chunk_paper = []
        self.read()
        self.search_title()
        if self.title_pattern == 1:
            self.title_pattern_1()
        elif self.title_pattern == 2:
            self.title_pattern_2()
        else:
            self.logger.error("未找到title_pattern")
        self.find_matches()
        self.clean_table_context()
        self.chunk_by_title()
    def read(self) -> None:
        """
        读取paper的内容，返回List[str]
        """
        pattern1 = r'Table (\d+): .+?(?=\.|\s*\n)'
        pattern2 = r'Table (\d+)\. .+?(?=\.|\s*\n)'
        doc = fitz.open(self.paper_path)
        self.text = [""]*doc.page_count
        self.cleaned_text = [""]*doc.page_count
        print(doc.page_count)
        b_unit = tqdm.tqdm(total=doc.page_count, desc="PaperPDFLoader context page index: 0")
        for i, page in enumerate(doc):
            b_unit.set_description("PaperPDFLoader context page index: {}".format(i))
            b_unit.refresh()
            text = page.get_text("")
            cleaned_text = re.sub(r'<latexit[^>]*>(.*?)</latexit>', '', text, flags=re.DOTALL | re.IGNORECASE)
            # 第一页页脚不在最后
            if i != 0:
                self.text[i] = self.clean_page_num(cleaned_text)
            else:
                self.text[i] = cleaned_text
            # 判断一下paper的table标题的匹配模式 和 table的位置
            if not self.paper_table_name_type:
                matches = list(re.finditer(pattern1,self.text[i]))
                if matches:
                    self.paper_table_name_type = 1
                    self.seek_table_content_position(self.text[i],matches[0].start())
                else: 
                    matches = list(re.finditer(pattern2,self.text[i]))
                    if matches and not self.paper_table_name_type:
                        self.paper_table_name_type = 2
                        self.seek_table_content_position(self.text[i],matches[0].start())

            b_unit.update(1)
        print(f"Paper path: {self.paper_path} has already been read")
    def chunk_by_title(self):
        texts = ""
        for i in self.cleaned_text:
            texts += i + "\n"
        chunks = texts.split("###")
        for chunk in chunks:
            self.chunk_paper.append([(chunk.split("\n"))[0],chunk])
    def seek_table_content_position(self,text:str,head:int):
        """
        通过pos位置的上下文，来确定paper的表格内容的位置，先从上面找，如果找不到
        就再从下面找
        """
        if not text:
            return 
        # print(head,type(head))
        head_lines = text[:head].splitlines(keepends=True) # 保留换行符
        head_lines.reverse()
        reverse_text = ""
        for line in head_lines: # 反转查询
            if len(line) > self.RECOGNIZE_SENTENCE_LEN:
                break
            else:
                reverse_text += line
        if self.design_table_content(reverse_text):
            # print(reverse_text)
            self.paper_table_position_type = 1
            if self.debug:
                # print("\033[31m表格在上面\033[0m")
                self.logger.info("表格在上面")
            return 
        table_start,table_end =self.find_line_is_table_content(text[head:])
        if self.design_table_content(text[head+table_start:head+table_end]):
            self.paper_table_position_type = 0
            if self.debug:
                print("\033[31m表格在下面\033[0m")
                self.logger.info("表格在下面")
            return 
        # print("\033[31m没有找到table的内容的位置\033[0m")
        self.logger.warning("没有找到表格的内容")


    def clean_page_num(self,text:str):
        """
        清除页脚
        """
        log = 0
        pos = 0
        # print(repr(text[len(text)-70:]))
        # for index, chara in enumerate(text):
        #     if text[len(text)-1-index] >= '0' and text[len(text)-1-index] <= '9' :
        #         log = 1
        #         # print(text[len(text)-1-index])
        #     if log and text[len(text)-1-index] == '\n':
        #         pos = len(text) - 1 - index
        #         # print(repr(text[pos-8:pos+4]))
        #         break
        if self.is_num(text[len(text)-1]):
            log += 1
        if self.is_num(text[len(text)-2]):
            log += 1
        if self.is_num(text[len(text)-3]):
            log += 1
        return text[:len(text)-log]


    def find_matches(self) -> None:
        """
        调试函数，用来查看匹配的table
        """
        #  两种匹配模式
        # 第一种：Table 3: Experimental results on the DOTA dataset compared with state-of-the-art methods.
        # 第二种：Table 3. Experimental results on the DOTA dataset compared with state-of-the-art methods.
        pattern1 = r'Table (\d+): .+?(?=\.|\s*\n)'
        pattern2 = r'Table (\d+)\. .+?(?=\.|\s*\n)'
        print("="*100)
        for text in self.text:
            if self.paper_table_name_type == 1:
                matches = list(re.finditer(pattern1,text))
            else:
                matches = list(re.finditer(pattern2,text))
            for match in matches:
                print(match.group())  # 打印匹配的文本
                print(match)
        print("="*100)
    def is_num(self,c:str):
        if len(c) == 1:
            if c >= '0' and c <= '9':
                return True
        return False
    def design_table_content(self,text:str) -> bool:
        """
        1.用text的char的table类型占比得分来判断
        2.用数字比例大的行的占比来判断
        """
        num = 0
        if not text:
            return False
        for index,i in enumerate(text):
            if self.is_num(i):
                num += 1
            if i == "." :
                if index + 1 <= len(text) - 1:
                    if self.is_num(text[index-1]) and self.is_num(text[index+1]):
                        num += 2
                    else:
                        num += 1
            if i == '±' or i == "≤" or i == '≥': # 给权重
                num += 2
        num_line = 0
        chunk = text.split("\n")
        for k in chunk:
            if self.is_table_line(k):
                num_line += 1
        # print(num/len(text))
        # print(num_line/len(chunk))
        if num/len(text) >=  0.4 or num_line/len(chunk) >= 0.4:
            return True
        return False
    def is_table_line(self,text:str):
        """
        用text的table元素占比来判断是否是table的行
        """
        num = 0
        if not text:
            return False
        for i in text:
            if self.is_num(i) or i == '–'or i == '-' or i == '±' or i == '≤' or i == '≥' or i == '.' or i == '✓' or i == '✗':
                num += 1
        if num / len(text) >= 0.6:
            return True
        return False
    def find_row_low_50_next(self,text:str) -> int:
        """
        text: 传入text 
        从0位置开始，找到小于长度50且数字多的行开始。
        或者长度小于10的行

        """
        matches = re.finditer(r'\A.{0,49}\Z',text)
        for match in matches:
            if self.design_table_content(text[match.start(),match.end()]):
                if self.debug:
                    # print(f"\n\033[31m表格内容：数字多开始,{match.group}\033[0m\n")
                    self.logger.info("表格内容：数字多开始")
                return match.start()
            elif len(match.group) < self.MINI_LINES:
                if self.debug:
                    # print(f"\033[31m长度短{match.group}\033[0m")
                    self.logger.warning(f"长度短，{match.group}")
                return match.start()
        return len(text)-1
    def find_row_over_50_next(self,text:str) -> int:

        """
        text: 从第一个小于50且数字多的行开始，找到第一个长度大于50的非数字行
        int：返回大于50的非数字行的首字母的位置
        
        """
        # pos = self.find_row_low_50_next(text)
        # for match in re.finditer(r'^(.{51,})\n', text[pos:], re.DOTALL):
        #     if not self.design_excel_content(match):
        #         if match.start() > 0:
        #             print(f"\033[31m匹配到了{match.group}\033[0m")

        #             return match.start() + pos
        # return len(text)-1
        next_line_start = 0
        lines = text[next_line_start:].split("\n")
        table_position_start = 0
        table_position_end = 0
        # if self.debug:
        #     print(">"*100)
        for index,line in enumerate(lines):
            if self.debug:
                print(line)
            if len(line) >= self.RECOGNIZE_SENTENCE_LEN and not self.design_table_content(line):
                if self.debug:
                    # print("ok了，准备撤退")
                    self.logger.info("ok了，准备撤退")
                break
            else:
                if self.debug:
                    # print("不是")
                    self.logger.info("不是")
                table_position_end += len(line) + 1
        # if self.debug:
            # print("<"*100)
        ###################################测试代码#################################
        if self.debug:
        #     print("\033[31m\033>>>>find_line_is_table_content测试信息----------------开始-------\033[0m\033[0m")
        #     print("\033[31m\033[1m找到的text table 内容 \033[0m\033[0m")
        #     print(text[table_position_start:table_position_end])
        #     print("\033[31m\033<<<<find_line_is_table_content测试信息----------------结束-------\033[0m\033[0m")
            self.logger.info(f"找到的text table 内容,{text[table_position_start:table_position_end]}")
        ############################################################################

        return table_position_end
    def design_without_other_word(self,text:str) -> bool:
        """
        判断text之后在\n之前有无字符
        """
        for i in text:
            if i == ' ' or i == '.':
                continue
            elif i != '\n':
                return False
            elif i == '\n':
                return True
        return True
    def find_line_is_table_content(self,text:str)-> Tuple[int,int]:
        """
        找到table内容的开头和结尾+1
        开头是从第一个'\n'以后，找到'.'结尾的且长度小于50的或者之后小于50的句子
        结尾是超过50的行，且数字比例少
        """
        next_line_start = 0
        for index,character in enumerate(text):
            if character == "\n":
                next_line_start = index + 1
                break
        lines = text[next_line_start:].split("\n")
        table_position_start = next_line_start
        table_position_end = next_line_start
        transfer_travel = 0
        if self.debug:
            print(">"*100)
        for index,line in enumerate(lines):
            if self.debug:
                print(line)
            if not transfer_travel:
                # 找start，从第一个小于设定长度的句子开始
                if len(line) < self.RECOGNIZE_SENTENCE_LEN:
                    if line:
                        if line[-1] == '.':
                            table_position_start += len(line) + 1
                            table_position_end += len(line) + 1
                            transfer_travel = 1
                            if self.debug:
                                # print("找到.了，OK了") # 测试函数
                                self.logger.info("找到了，ok")
                            continue
                        elif index > 0 and lines[index-1][-1] == '.':
                            transfer_travel = 1
                            table_position_end += len(line) + 1
                            if self.debug:
                                # print("上一行最后是.")
                                self.logger.info("上一行最后是.")
                            continue
                        elif len(line) < self.MINI_LINES:
                            transfer_travel = 1
                            table_position_end += len(line) + 1
                            if self.debug:
                                # print("这一行很短，鉴定为表格内容")
                                self.logger.info("上一行最后是.")
                            continue
                    else:
                        table_position_end += 1
                        table_position_start += 1

                table_position_start += len(line) + 1
                table_position_end += len(line) + 1
            else:
                # 找end，从第一个
                if line == "###":
                    self.logger.warning(f"发现###，切除部分终止，后面是{lines[index+1]}")
                    break
                if len(line) >= self.RECOGNIZE_SENTENCE_LEN and not self.design_table_content(line):
                    if self.debug:
                        # print("ok了，准备撤退")
                        self.logger.info("ok了，准备撤退")
                    break
                else:
                    if self.debug:
                        # print("不是")
                        self.logger.info("不是")
                    table_position_end += len(line) + 1
        # if self.debug:
        #     print("<"*100)
        ###################################测试代码#################################
        if self.debug:
            # print("\033[31m\033>>>>find_line_is_table_content测试信息----------------开始-------\033[0m\033[0m")
            # print("\033[31m\033[1m找到的text table 内容 \033[0m\033[0m")
            # print(text[table_position_start:table_position_end])
            # print("\033[31m\033<<<<find_line_is_table_content测试信息----------------结束-------\033[0m\033[0m")
            self.logger.info(f"找到的text table内容,{text[table_position_start:table_position_end]}")
        ############################################################################

        return table_position_start,table_position_end        
    def cut_table_str(self,text:str,pos:int) -> str:
        """
        text: 需要切除table内容部分的text
        pos:text的table标题之后的第一个字符的位置
        
        """
        new_text = text
        table_start = 0
        table_end = 0
        # if not self.design_without_other_word(text[pos:]): # 判断table这一行之后还有没有内容
        #     table_start,table_end = self.find_line_is_table_content(text[pos:]) # 将标题的内容隔过去，找到tabel的前和后
        # else:
        #     # table_start = pos
        #     # table 这一行之后没有其他word，从下一行开始，找到长度小于设定长度且数字多的行
        #     # 或者找到行长度极其小的行
        #     table_end = self.find_row_over_50_next(text[pos:])
        table_start,table_end = self.find_line_is_table_content(text[pos:]) # 将标题的内容隔过去，找到tabel的前和后
        
            
        if self.design_table_content(text[pos+table_start:pos+table_end]):
            return text[:pos+table_start] + text[pos+table_end:]
        else:
            # print("\033[31m\033[1m error, 切除部分是非表格内容\033[0m\033[0m")
            # print("-"*100)
            # print(f"<<<<<<<<<<<<<<位置{pos+table_start}-{pos+table_end}>>>>>>>>>>>>>>>>>>>")
            # print("--------------切除内容开始--------------")
            # print(f"\033[34m{text[pos+table_start:pos+table_end]}\033[0m")
            # print("-"*100)
            self.logger.error(f"切除部分是非表格内容: {text[pos+table_start:pos+table_end]}")
        return new_text 
    def recognize_table(self,text:str) ->str:

        """
        识别table的内容，并且切除table内部的内容
        """
        pattern1 = r'Table (\d+): .+?(?=\.|\s*\n)'
        pattern2 = r'Table (\d+)\. .+?(?=\.|\s*\n)'
        # 在没有确定类型的时候，根据第一个匹配的table的类型类确定是哪种pattern
        if not self.paper_table_name_type:
            matches = list(re.finditer(pattern1, text))
            if matches:
                self.paper_table_name_type = 1
            else:
                matches = list(re.finditer(pattern2, text))
                if not self.paper_table_name_type and matches:
                        self.paper_table_name_type = 2
        else:
            if self.paper_table_name_type == 1:
                matches = list(re.finditer(pattern1, text))
            else:
                matches = list(re.finditer(pattern2, text))
        if not matches:  
            return text
        else:
            index_first = [] # 匹配的标题的首个字母的text中的位置
            index_end = [] # 匹配的标题的最后的字母的之后第一个text中的位置
            new_text = ""
            if self.paper_table_position_type == 0:
                for match in matches:
                    index_first.append(match.start())
                    index_end.append(match.end())
                index_first.append(len(text)-1) # 这里为了顺应后面的cut操作，通过添加一个元素，能够用index_first将text的分成若干个区间
                new_text += text[:index_first[0]] # 这里默认是table之后的内容是表格内容，之后会加入选择的情况
                for i in range(len(index_end)):
                    new_text += self.cut_table_str(text[index_first[i]:index_first[i+1]],index_end[i]-index_first[i])
                    # 上面将index_first分开的区间作为text传给cut函数，并将传入的text的table的长度传进去
                return new_text
            elif self.paper_table_position_type == 1:
                index_end.append(0)
                for match in matches:
                    index_first.append(match.start())
                    index_end.append(match.end())
                for i in range(len(index_first)):
                    new_text += self.cut_table_str_before(text[index_end[i]:index_first[i]]) if  self.cut_table_str_before(text[index_end[i]:index_first[i]]) is not None else ""
                    new_text += text[index_first[i]:index_end[i+1]]
                new_text += text[index_end[-1]:]
                return new_text
    def cut_table_str_before(self,text:str) -> str:
        text = text.splitlines(keepends=True)
        num_table_line = 0
        table_text = ""
        for index in range(len(text)):
            if len(text[len(text)-1-index]) > self.RECOGNIZE_SENTENCE_LEN:
                if self.is_table_line(text[len(text)-1-index]):
                    continue
                else:
                    num_table_line = len(text) -index
                    break
        if num_table_line > len(text) - 1:
            # print(f"\033[34m 表格在前,没有表格内容 \033[0m")
            # print(">"*100)
            # print(text)
            # print("<"*100)
            self.logger.warning(f"表格在前，没有表格内容 {text}")
            no_table_text = ""
            for line in text:
                no_table_text += line
            return no_table_text
        for line in text[num_table_line:]:
            # print("line")
            # print(line)
            table_text += line
        
        if self.design_table_content(table_text):
            no_table_text = ""
            for line in text[:num_table_line]:
                no_table_text += line
            return no_table_text
        else:
            # print("\033[31m\033[1m error, 切除部分是非表格内容\033[0m\033[0m")
            # print("-"*100)
            # print(f"<<<<<<<<<<<<<<<<<>>><<<<>>>>>>>>>>>>>>>>>>>")
            # print("--------------切除内容开始--------------")
            # print(f"\033[34m{table_text}\033[0m")
            # print("-"*100)
            self.logger.warning(f"切除部分是非表格部分，停止切除{table_text}")
    def clean_table_context(self) -> None:
        for index,text in enumerate(self.text):
            self.cleaned_text[index] = self.recognize_table(text)
            if self.debug:
                print(self.text[index])
    def list_to_str(self,L:List[str]) -> str :
        output = ""
        for i in L:
            output += str(i) + '.'
        return output[:-1]
    def design_en_or_space_1(self,text:str) -> bool:
        # 只有英文和空格,-,()，True
        log = 0
        for i in text:
            if log == 0 or log == 1:
                if i == ' ':
                    log = 2
                    continue
                if self.is_num(i) and log == 0:
                    log = 1
                elif i=='.' and log == 1:
                    log = 0
                else:
                    # self.logger.error(f"{text} 在 {i} 处没通过")
                    return False
            else:
                if i>='a' and i<='z' or i>='A' and i <='Z' or i==' ' or i == '-' or i == '(' or i == ')' or self.is_num(i):
                    log += 1
                    pass
                else:
                    # self.logger.error(f"{text} 在 {i} 处没通过")
                    return False
        if log >= 5:
            return True
        return False
    def design_en_or_space_2(self,text:str) -> bool:
        # 只有英文和空格,-,()，True
        log = 0
        for i in text:
            if i>='a' and i<='z' or i>='A' and i <='Z' or i==' ' or i == '-' or i == '(' or i == ')' or self.is_num(i) or \
                i == ":" or i=="−" or i==',':
                log += 1
            # else:
                # self.logger.error(f"{text} 在 {i} 处没通过")
                # return False
        if log >= 5 or log/len(text) > 0.8 :
            return True
        return False
    def search_title(self):
        # 先查找Abstract，然后找到Introduction的样式，根据Introduction的样式查找
        # Introduction样式
        # 1. Introduction
        # 3. Method
        # 3.1. Rotate the convolution kernels
        # 3.2. Routing function
        # 3.3. Adaptive rotated convolution module

        # 3. Background
        # 3.1 Denoising Diffusion Probabilistic Model
        
        # 1
        # Introduction

        # 判断逻辑，每行第一个是数字，根据标题树，判断属于兄弟节点还是父兄弟节点递归往上判断，或者给一个队列，把现在和下一个大标题的数字放进来
        # 俩都进行判断， 然后匹配以后之后插入树节点，在第一个空格之后逐个元素判断，只能是英文字母或者空格，匹配的话，记录下来，然后打上标记（放到一行），在进行删除表格操作的时候判断标题
        # design
        for index_text,text in enumerate(self.text):
            texts = text.split("\n")
            if self.title_pattern is not None:
                break
            for index_i,i in enumerate(texts):
                if "Introduction" in i:
                    if self.is_num(i[0]):
                        self.title_pattern = 1 # 1. Introduction
                        # self.title_tree = TitleTree(value=[])
                        # self.title_tree.sons = [TitleTree(value=["1"],parent=self.title_tree)]
                        # self.title_tree = self.title_tree.sons[0]
                        self.logger.info(f"paper标题模式确认，{i}")
                        break
                    elif self.is_num(texts[index_i-1][0]):
                        self.title_pattern = 2
                        # 1
                        # Introduction
                        # self.title_tree.sons = [TitleTree(value=["1"],parent=self.title_tree)]
                        # self.title_tree = self.title_tree.sons[0]
                        self.logger.info(f"paper标题模型确认，\n{texts[index_i-1]}\n{i}")
                        break
        if self.title_pattern is None:
            self.logger.error("标题未找到")
    def title_queue(self,title_node:TitleTree) -> List[int]:
        # 生成当前步的查询列表, 将可变对象赋值个一个新的变量，这个变量被认为是可变对象的别名，
        # 会和可变对象同步改变，用copy方法能够避免这种情况
        if title_node.value == []:
            name = []
        else:
             name = title_node.value.copy()
        output = []
        name.append(1)
        output.append(name) # 子树

        if title_node.parent:
            name = title_node.value.copy()
            name[-1] += 1
            output.append(name) # 兄弟树
            if title_node.parent.parent:
                name = title_node.parent.value.copy()
                name[-1] += 1
                output.append(name) # 父兄树
                # print(output)
                if title_node.parent.parent.parent:
                    name = title_node.parent.parent.value.copy()
                    name[-1] += 1
                    output.append(name) # 父父兄树
        # print(output)
        # self.logger.info(f"队列创建成功，{output}")
        return output

    def title_pattern_1(self):
        # 匹配模式为 1. Introduction
        # 从self.text中进行标记
        queue = []
        log_title = 0
        log_abstract = 0
        # 遍历每页
        for index,texts in enumerate(self.text):
            texts = texts.split("\n")
            self.text[index] = ""
            # 遍历每行
            for text in texts:
                if log_abstract == 0 and text == "Abstract":
                    self.text[index] += "#"*3 + "\n" + text + '\n'
                    self.logger.success(f"成功找到标题：{text}")
                    log_abstract = 1
                    log_title = 1
                    continue
                if text == "\n":
                    continue
                if queue == []:
                    queue = self.title_queue(self.title_tree)
                # 遍历每个可能的标题号
                for i,lis in enumerate(queue):
                    lis_to_str = self.list_to_str(lis)
                    if lis_to_str in text:
                        if self.design_en_or_space_1(text.strip(".")):
                            self.text[index] += "#"*3 + "\n" + text + "\n"
                            log_title = 1
                            queue = []
                            self.logger.success(f"成功找到标题：{text}")
                            if i == 0:
                                # self.logger.info("i==0")
                                if self.title_tree.value == []:
                                    self.title_tree.sons = [TitleTree(value=[1],parent=self.title_tree)]
                                else:
                                    _list = self.title_tree.value.copy()
                                    _list.append(1)
                                    self.title_tree.sons = [TitleTree(value=_list,parent=self.title_tree)]
                                self.title_tree = self.title_tree.sons[0]
                                # self.logger.info(f"end {self.title_tree.value}")

                            elif i == 1:
                                # self.logger.info("i=1")
                                _list = self.title_tree.value.copy()
                                _list[-1] += 1
                                self.title_tree.parent.sons.append(TitleTree(value=_list,parent=self.title_tree.parent))
                                self.title_tree = self.title_tree.parent.sons[-1]
                            elif i == 2:
                                # self.logger.info("i=2")
                                _list = self.title_tree.parent.value.copy()
                                _list[-1] += 1
                                self.title_tree.parent.parent.sons.append(TitleTree(value=_list,parent=self.title_tree.parent.parent))
                                self.title_tree = self.title_tree.parent.parent.sons[-1]
                            elif i == 3:
                                # self.logger.info("i=3")
                                _list = self.title_tree.parent.parent.value.copy()
                                _list[-1] += 1
                                self.title_tree.parent.parent.sons.append(TitleTree(value=_list,parent=self.title_tree.parent.parent.parent))
                                self.title_tree = self.title_tree.parent.parent.parent.sons[-1]
                            break
                if log_title==0:
                    self.text[index] += text + "\n"
                else:
                    log_title = 0

    def title_pattern_2(self):
            # 匹配模式为 1. Introduction
            # 从self.text中进行标记
            queue = []
            log_title = 0
            log_abstract = 0
            count = 0
            # 遍历每页
            for index,texts in enumerate(self.text):
                texts = texts.split("\n")
                self.text[index] = ""
                # 遍历每行
                for index_1,text in enumerate(texts):
                    if log_abstract == 0 and text == "Abstract":
                        self.text[index] += "#"*3 + "\n" + text + "\n"
                        self.logger.success(f"成功找到标题：{text}")
                        log_abstract = 1
                        log_title = 1
                        continue
                    if text == "\n":
                        continue
                    if queue == []:
                        queue = self.title_queue(self.title_tree)
                    # 遍历每个可能的标题号
                    for i,lis in enumerate(queue):
                        lis_to_str = self.list_to_str(lis)

                        if lis_to_str ==  text:
                            if index_1 != len(texts)-1: 
                                if self.design_en_or_space_2(texts[index_1+1].strip(".")):
                                    self.text[index] += "#"*3 + "\n" + text + " "
                                    log_title = 1
                                    queue = []
                                    self.logger.success(f"成功找到标题：{text} {texts[index_1+1]}")
                                    if i == 0:
                                        # self.logger.info("i==0")
                                        if self.title_tree.value == []:
                                            self.title_tree.sons = [TitleTree(value=[1],parent=self.title_tree)]
                                        else:
                                            _list = self.title_tree.value.copy()
                                            _list.append(1)
                                            self.title_tree.sons = [TitleTree(value=_list,parent=self.title_tree)]
                                        self.title_tree = self.title_tree.sons[0]
                                        # self.logger.info(f"end {self.title_tree.value}")

                                    elif i == 1:
                                        # self.logger.info("i=1")
                                        _list = self.title_tree.value.copy()
                                        _list[-1] += 1
                                        self.title_tree.parent.sons.append(TitleTree(value=_list,parent=self.title_tree.parent))
                                        self.title_tree = self.title_tree.parent.sons[-1]
                                    elif i == 2:
                                        # self.logger.info("i=2")
                                        _list = self.title_tree.parent.value.copy()
                                        _list[-1] += 1
                                        self.title_tree.parent.parent.sons.append(TitleTree(value=_list,parent=self.title_tree.parent.parent))
                                        self.title_tree = self.title_tree.parent.parent.sons[-1]
                                    elif i == 3:
                                        # self.logger.info("i=3")
                                        _list = self.title_tree.parent.parent.value.copy()
                                        _list[-1] += 1
                                        self.title_tree.parent.parent.sons.append(TitleTree(value=_list,parent=self.title_tree.parent.parent.parent))
                                        self.title_tree = self.title_tree.parent.parent.parent.sons[-1]
                                    break
                            else:
                                self.logger.warning(f"{text} ，达到了{index+1}页的末尾")
                    if log_title==0:
                        self.text[index] += text + "\n"
                    else:
                        log_title = 0
                    

            


            
        

    # 下面是新的函数用来将表格内容在上方的情况解决



def design_excel_content(text:str) -> bool:
    num = 0
    for i in text:
        if i>='0' or i<='9':
            num += 1
    if num/len(text) > NUM_PERCENT:
        return True
    return False
def find_row_low_50_next(text:str) -> int:
    """
    text: 从0位置开始，找到小于50且数字多的行开始。

    """
    matches = re.finditer(r'\A.{0,49}\Z',text)
    for match in matches:
        if design_excel_content(text[match.start(),match.end()]):
            return match.start()
    return len(text)-1
def find_row_over_50_next(text:str) -> int:

    """
    text: 从第一个小于50且数字多的行开始，找到第一个长度大于50的非数字行
    int：返回大于50的非数字行的首字母的位置
    
    """
    # print("`"*70)
    # print(text)
    # print("`"*70)
    # for match in re.finditer(r'(?!\n)(.{50,})(?!\n)', text, re.DOTALL):
    pos = find_row_low_50_next(text)
    for match in re.finditer(r'^(.{51,})\n', text[pos:], re.DOTALL):
        # 检查匹配的开始位置是否大于指定的开始位置
        # print(match.group(0))
        # print(match.start())
        # print(match.end())
        # print("`"*70)
        if not design_excel_content(match):
            if match.start() > 0:
                # print("match.start()",match.start())
                # 打印匹配的子字符串
                # print("找到长度大于50的子字符串:",text[match.start():match.end()])
                # 由于我们只需要找到第一个匹配，所以在这里我们可以停止搜索
                
                return match.start()
    return len(text)-1
def cut_middle_str(text:str,pos:int) -> str:
    """
    text: 需要切除table内容部分的text
    pos:text的table标题之后的第一个字符的位置
    
    """
    new_text = text
    middle = find_row_over_50_next(text[pos:])
    if design_excel_content(text[pos:pos+middle]):
        new_text = text[:pos] +"\n"+ text[pos + middle:]
    else:
        pass
    # print("*"*100)
    # print("cut_middle_str"+"-"*30)
    # print(text[pos:pos+middle])
    # print("*"*100)

    return new_text 
def recognize_table(text:str) ->str:

    """
    识别table的内容，并且切除table内部的内容
    """
    pattern1 = r'Table (\d+): .+?(?=\.|\s*\n)'
    pattern2 = r'Table (\d+)\. .+?(?=\.|\s*\n)'

    matches = list(re.finditer(pattern1, text))
    if not matches:
        matches = list(re.finditer(pattern2, text))
    if not matches:  
        return text
    else:
        index_first = []
        index_end = []
        new_text = ""
        for match in matches:
             index_first.append(match.start())
             index_end.append(match.end())
        index_first.append(len(text)-1)
        new_text += text[:index_first[0]]
        print("-=-=-=-=-=-==-=--=========-=-=-=-=--=-=--===--=")
        
        print("len(index_end):  ",len(index_end))
        print("-=-=-=-=-=-==-=--=========-=-=-=-=--=-=--===--=")
        for i in range(len(index_end)):
             new_text += cut_middle_str(text[index_first[i]:index_first[i+1]],index_end[i]-index_first[i])
        return new_text 
def pdf_page_2text(filepath) ->List[str]:
    """
    读取每页pdf，返回List[page.content]，用的是fitz（pyMuPDF）
    """
    # ocr = RapidOCR()
    doc = fitz.open(filepath)
    resp = [""]*doc.page_count
    print(doc.page_count)
    b_unit = tqdm.tqdm(total=doc.page_count, desc="RapidOCRPDFLoader context page index: 0")
    for i, page in enumerate(doc):
        b_unit.set_description("RapidOCRPDFLoader context page index: {}".format(i))
        b_unit.refresh()
        text = page.get_text("")
        # 清除latex的公式内容
        cleaned_text = re.sub(r'<latexit[^>]*>(.*?)</latexit>', '', text, flags=re.DOTALL | re.IGNORECASE)
        resp[i] = cleaned_text + "\n"

        # 识别表格内容并进行清除
        resp[i] = recognize_table(resp[i])
        b_unit.update(1)
    return resp
def find_matches(text:str) -> int:
    """
    调试函数，用来查看匹配的table
    """
    log_pattern = 0
    #  两种匹配模式
    # 第一种：Table 3: Experimental results on the DOTA dataset compared with state-of-the-art methods.
    # 第二种：Table 3. Experimental results on the DOTA dataset compared with state-of-the-art methods.
    pattern1 = r'Table (\d+): .+?(?=\.|\s*\n)'
    pattern2 = r'Table (\d+)\. .+?(?=\.|\s*\n)'

    matches = list(re.finditer(pattern1, text))
    print(matches)
    if not matches:
        matches = re.finditer(pattern2, text)
        print("kong")
        
    print("="*100)
    for match1 in matches:
        print(match1.group())  # 打印匹配的文本
        print(match1)
    print("="*100)
    return log_pattern 

        #  print(text[match.start():match.end()])
    print("="*100)
if __name__ == "__main__": 

    files = PaperCleaner("./5.pdf")
    # files.search_title()
    # tree = TitleTree(value=[1])
    # tree1 = TitleTree(value=[1,1],parent=tree)
    # tree2 = TitleTree(value=[1,1,1],parent=tree1)
    # files.title_queue(tree2)
    # files.title_pattern_1()
    # with open("log.txt",'w') as f:
    #     for text in files.text:
    #         # print(text)
    #         f.write(text)
    for i in files.chunk_paper:
        print("-"*10)
        print(i[1])


# 对表格的内容清除还不到位
