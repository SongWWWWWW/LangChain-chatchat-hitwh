from __future__ import annotations
from langchain.agents import Tool, AgentOutputParser
from langchain.prompts import StringPromptTemplate
from typing import List
from langchain.schema import AgentAction, AgentFinish

from configs import SUPPORT_AGENT_MODEL
from server.agent import model_container
import re
def get_action_input(input_string):
    # 使用正则表达式匹配"Action Input:"之后的所有内容
    # match = re.search(r'Action Input:\s*(.*)', input_string, re.DOTALL)
    match = re.search(r"'''python(.*?)'''", input_string, re.DOTALL)
    if not match:
        match = re.search(r"'''(.*?)'''", input_string, re.DOTALL)
    if match:
        # 如果找到匹配，返回匹配的组（即"Action Input:"之后的内容）
        print(match.group(1))
        return match.group(1)
    else:
        # 如果没有找到匹配，返回None或者一个空字符串
        return None

class CustomPromptTemplate(StringPromptTemplate):
    template: str
    tools: List[Tool]

    def format(self, **kwargs) -> str:
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        kwargs["agent_scratchpad"] = thoughts
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        return self.template.format(**kwargs)

class CustomOutputParser(AgentOutputParser):
    begin: bool = False
    def __init__(self):
        super().__init__()
        self.begin = True

    def parse(self, llm_output: str) -> AgentFinish | tuple[dict[str, str], str] | AgentAction:
        if not any(agent in model_container.MODEL for agent in SUPPORT_AGENT_MODEL) and self.begin:
            self.begin = False
            stop_words = ["Observation:"]
            min_index = len(llm_output)
            for stop_word in stop_words:
                index = llm_output.find(stop_word)
                if index != -1 and index < min_index:
                    min_index = index
                llm_output = llm_output[:min_index]

        if "Final Answer:" in llm_output:
            self.begin = True
            return AgentFinish(
                return_values={"output": llm_output.split("Final Answer:", 1)[-1].strip()},
                log=llm_output,
            )
        parts = llm_output.split("Action:")
        print("parts",parts)
        if len(parts) < 2:
            return AgentFinish(
                #return_values={"output": f"调用agent工具失败，该回答为大模型自身能力的回答:\n\n `{llm_output}`"},
                return_values={"`{llm_output}`"},
                log=llm_output,
            )
        print('-'*50)
        print(parts)
        print('-'*50)
        print(llm_output)
        print('-'*50)
        action = parts[1].split("Action Input:")[0].strip()
        print(action)
        if action == "```python":
            action = "python"
        # if action =="python":
        #     print("! ! ! python ! ! !")
        #     action_input = get_action_input(parts[1])
        # else:
        action_input = parts[1].split("Action Input:")[1].strip()
        try:
            ans = AgentAction(
                tool=action.strip("'''"),
                tool_input=action_input.strip(" ").strip('"').strip("```python").strip("```"),
                log=llm_output
            )
            print("\nans:",ans)
            return ans
        except:
            return AgentFinish(
                return_values={"output": f"调用agent失败: `{llm_output}`"},
                log=llm_output,
            )
