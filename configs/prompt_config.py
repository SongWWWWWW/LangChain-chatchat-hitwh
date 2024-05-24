# prompt模板使用Jinja2语法，简单点就是用双大括号代替f-string的单大括号
# 本配置文件支持热加载，修改prompt模板后无需重启服务。

# LLM对话支持的变量：
#   - input: 用户输入内容

# 知识库和搜索引擎对话支持的变量：
#   - context: 从检索结果拼接的知识文本
#   - question: 用户提出的问题

# Agent对话支持的变量：

#   - tools: 可用的工具列表
#   - tool_names: 可用的工具名称列表
#   - history: 用户和Agent的对话历史
#   - input: 用户输入内容
#   - agent_scratchpad: Agent的思维记录
Excel_path = None
save_path = None

PROMPT_TEMPLATES = {
    "llm_chat": {
        "default":
            '{{ input }}',

        "with_history":
            'The following is a friendly conversation between a human and an AI. '
            'The AI is talkative and provides lots of specific details from its context. '
            'If the AI does not know the answer to a question, it truthfully says it does not know.\n\n'
            'Current conversation:\n'
            '{history}\n'
            'Human: {input}\n'
            'AI:',

        "py":
            '你是一个聪明的代码助手，请你给我写出简单的py代码。 \n'
            '{{ input }}',

        "translator":
            '你是翻译论文方面的专家，以下给出相应的论文内容，请进行翻译。注意，'
            '1. 每句话都要翻译.'
            '2. 如果遇到你不确定的词汇，请在你翻译的这个词之后直接用小括号标注原文的这个词'
            '3. 翻译要做到语言连贯，上下文内容衔接。'
            '4. 翻译目标语言为中文'
            '如果没有给出相应的论文内容，请提醒用户上传文件'
            '以下为论文内容，请开始进行翻译:\n'
            '用户输入：{{ input }}',

        "summary":
            '1. Mark the title of the paper (with Chinese translation)\n'
            '2. list all the authors\' names (use English) \n'
            '3. mark the first author\'s affiliation (output Chinese translation only) \n'
            '4. mark the keywords of this article (use English)\n'
            '5. link to the paper, Github code link (if available, fill in Github:None if not)\n'
            '6. summarize according to the following four points.Be sure to use Chinese answers (proper nouns need to be marked in English)\n'
            '   - (1):What is the research background of this article?(use Chinese)\n'
            '   - (2):What are the past methods? What are the problems with them? Is the approach well motivated?(use Chinese)\n'
            '   - (3):What is the research methodology proposed in this paper?(use Chinese)\n'
            '   - (4):On what task and what performance is achieved by the methods in this paper? Can the performance support their goals?(use Chinese)\n'
            'Follow the format of the output that follows:\n'
            '   1. Title: xxx\n\n'
            '   2. Authors: xxx\n\n'
            '   3. Affiliation: xxx\n\n'
            '   4. Keywords: xxx\n\n'
            '   5. Urls: xxx or xxx , xxx \n\n'
            '   6. Summary: \n\n'
            '       - (1):xxx;\n'
            '       - (2):xxx;\n'
            '       - (3):xxx;\n'
            '       - (4):xxx.\n\n'
            'Be sure to use Chinese answers (proper nouns need to be marked in English), statements as concise and academic as possible,\n'
            'do not have too much repetitive information, numerical values using the original numbers.\n'
            'Artical content is: \n'
            '{{ input }}',
        "summary_paper":
            '你是一个请按照以下步骤进行，并为每个部分提供详细的总结：'

            '1.标题和摘要:(60字)'

            '简要描述论文的主题和研究范围。'
            '摘要中提出了哪些关键点？'
            '2.研究问题和目的:(60字)'

            '明确指出作者旨在解答的问题或研究的主要目的。'
            '3.研究背景:(100字)'

            '概括研究背景，包括研究领域的现状和研究的必要性。'

            '4.研究方法:(100字)'

            '描述作者使用的研究设计、样本选择、数据收集和分析方法。'
            '5.主要发现:(50字)'

            '突出显示论文中的主要研究结果和发现。'
            '6.讨论:(50字)'

            '概述作者如何解释研究结果及其对现有理论和实践的意义。'

            '7.结论:(50字)'

            '总结作者的结论，并评估其对研究领域的贡献。'
            '引用和参考文献:'


            '8.研究的原创性和创新点:(60字)'

            '识别研究的新颖之处和对现有知识体系的贡献。'

            '9.未来研究方向:(50字)'

            '基于对论文的分析，提出未来研究的可能方向。'

            '请在阅读完论文后，提供一份包含以上各点的详细总结，请按照实际标定字数进行总结，不能太少。这将帮助我们更好地理解论文内容，并在必要时进行深入讨论。(注意，请用中文回答)'
            '论文内容如下：\n',
        "SWOT分析":
            '你是SWOT分析方面的专家，你能根据给定的信息进行详细而又准确的分析。'
            '请提供SWOT分析的全面内容，确保包括以下方面：\n'
            '- Strengths (优势)：组织或项目的内部优势因素，帮助实现目标和成功的方面。\n'
            '- Weaknesses (劣势)：组织或项目的内部不利因素，可能阻碍实现目标和成功的方面。\n'
            '- Opportunities (机会)：外部环境中组织或项目可以利用的有利条件或情况。\n'
            '- Threats (威胁)：外部环境中可能对组织或项目造成负面影响的不利条件或情况。\n'
            '确保对每个方面进行详细描述，并提供具体的例子或数据支持。'
            '{{ input }}',
        "文献综述":
            '你是综合文献综述撰写助手'

            '根据以下提供的多篇文献的总结，我需要你帮我撰写一篇综合文献综述。请按照以下步骤进行：'

            '1.引言:(200字)'

            '简要介绍研究领域和文献综述的目的。'
            '阐述文献综述的范围和所涵盖的文献。'

            '2.研究背景和现状:(200字)'

            '综合各篇文献的背景信息，概述研究领域的现状。'

            '3.研究问题和目的的比较:(200字)'

            '对比不同文献中提出的研究问题和目的，找出共性和差异。'

            '4.文献回顾的综合:(200字)'

            '汇总并分析不同文献对现有研究的回顾，识别研究领域中的主要理论和概念。'
            
            '5.研究方法的对比分析:(200字)'

            '对比不同文献中使用的研究方法，包括研究设计、样本选择和数据分析。'
            '6.主要发现的汇总:(200字)'

            '综合各篇文献的主要发现，概括研究领域的关键结果。'
            '7.讨论:(200字)'

            '分析不同研究结果之间的一致性和差异性，并讨论其对理论和实践的影响。'
            '8.研究限制的总结:(200字)'

            '总结各篇文献中提到的研究限制，并讨论这些限制对整个研究领域的共同影响。'
            '9.结论的提炼:(200字)'

            '从各篇文献的结论中提炼出核心观点，并综合形成整体研究领域的结论。'
            '10.研究原创性和创新点的归纳:(200字)'

            '归纳各篇文献的原创性和创新之处，展现研究领域的新进展。'
            '11.实际应用的探讨:(200字)'

            '探讨研究结果对实践领域的潜在应用和影响。'
            '12.未来研究方向的展望:(200字)'

            '基于综合分析，提出未来研究的可能方向和建议。'
            '13.总结:(400字)'

            '对文献综述进行总结，强调研究领域的重要性和未来研究的潜力。'
            '请确保文献综述中引用的文献信息准确无误并且确保按照相应的字数进行编写，并在综述中体现批判性思维。撰写完成后，进行校对，确保文献综述的流畅性和逻辑性（注意，请用中文回答）'
            '下面是相关文献的综述:\n',
                },

    "knowledge_base_chat": {
        "default":
            '<指令>根据已知信息，简洁和专业的来回答问题。如果无法从中得到答案，请说 “根据已知信息无法回答该问题”，'
            '不允许在答案中添加编造成分，答案请使用中文。 </指令>\n'
            '<已知信息>{{ context }}</已知信息>\n'
            '<问题>{{ question }}</问题>\n',

        "text":
            '<指令>根据已知信息，简洁和专业的来回答问题。如果无法从中得到答案，请说 “根据已知信息无法回答该问题”，答案请使用中文。 </指令>\n'
            '<已知信息>{{ context }}</已知信息>\n'
            '<问题>{{ question }}</问题>\n',

        "empty":  # 搜不到知识库的时候使用
            '请你回答我的问题:\n'
            '{{ question }}\n\n',
        "文献综述":
            '你是写文献综述方面的专家，请根据提供的信息，按要求用文献综述的格式给出一段文献综述: \n'
            '{{ question }}\n\n',
        "文献总结":
            '你是文献总结方面的专家，请根据提供的信息进行详细整体的概括，给出一个详细的总结\n'
            '给出人类可能感兴趣的几个问题供选择'
            '{{ question }}\n\n',
         "SWOT分析":
            '你是SWOT分析方面的专家，你能根据给定的信息进行详细而又准确的分析'
            '{{ input }}',  
         "论文润色":
            '你是论文润色方面的专家，你能根据给定的论文内容提供高质量的论文润色服务'
            '服务内容：\n-仔细校对和编辑给定论文内容，确保语法、拼写和标点的准确性。\n- 优化论文结构和段落组织，以确保逻辑清晰、表达流畅。\n-检查参考文献和引用格式，确保符合学术规范。\n'
            '在润色过程中确保用原文章的语言进行润色，回答直接从文章的润色开始，不需要加入任何的提示信息，不要省略任何内容。'
            '给出具体需要润色的地方，并给出润色结果'
            '{{ input }}',
        "论文翻译":
            '你是论文翻译方面的专家，你能根据给定的信息进行详细而又准确的翻译，你的翻译结果基本和原文的文字数量能进行一一对应，而不是进行总结翻译。'
            '翻译遵守：\n- 专业的翻译论文从原文翻译为中文，确保内容的完整和准确性。\n- 对翻译文稿进行校对和润色，以确保语言表达流畅、通顺。\n- 可根据需要提供专业术语的翻译和解释，确保翻译结果符合学术标准。'
            '用户输入：{{ input }}',
        "文章总结":
            '你是文章总结方面的专家，你能根据给定的信息进行详细而又准确的总结，确保不遗漏任何一个重点，你能够提供出色的文章总结服务'
            '服务内容：\n- 仔细阅读和理解文章，把握文章的核心思想和主题。\n- 撰写简洁清晰的文章总结，突出文章的重点和亮点。\n- 确保文章总结符合读者的阅读习惯和理解水平，简洁明了。'
            '{{ input }}',
        "论文英文纠错":
            '你是论文英文方面的专家，你能根据给定的论文信息进行细致而又谨慎的纠错，并指出纠错原因和出错位置。你能够提供出色论文英文纠错的服务'
            '服务内容：\n- 对您的论文进行全面的语法、拼写和标点符号的校对和修正。\n- 优化论文的句子结构和语言表达，确保论文通顺、流畅。\n- 检查参考文献和引用格式，确保符合学术规范和期刊要求。'
            '{{ input }}',
    },


    "search_engine_chat": {
        "default":
            '<指令>这是我搜索到的互联网信息，请你根据这些信息进行提取并有调理，简洁的回答问题。'
            '如果无法从中得到答案，请说 “无法搜索到能回答问题的内容”。 </指令>\n'
            '<已知信息>{{ context }}</已知信息>\n'
            '<问题>{{ question }}</问题>\n',

        "search":
            '<指令>根据已知信息，简洁和专业的来回答问题。如果无法从中得到答案，请说 “根据已知信息无法回答该问题”，答案请使用中文。 </指令>\n'
            '<已知信息>{{ context }}</已知信息>\n'
            '<问题>{{ question }}</问题>\n',
    },

    
    "agent_chat": {
        "default":
            'Answer the following questions as best you can. If it is in order, you can use some tools appropriately. '
            'You have access to the following tools:\n\n'
            '{tools}\n\n'
            'Use the following format:\n'
            'Question: the input question you must answer1\n'
            'Thought: you should always think about what to do and what tools to use.\n'
            'Action: the action to take, should be one of [{tool_names}]\n'
            'Action Input: the input to the action\n'
            'Observation: the result of the action\n'
            '... (this Thought/Action/Action Input/Observation can be repeated zero or more times)\n'
            'Thought: I now know the final answer\n'
            'Final Answer: the final answer to the original input question\n'
            'Begin!\n\n'
            'history: {history}\n\n'
            'Question: {input}\n\n'
            'Thought: {agent_scratchpad}\n',

        "ChatGLM3":
            'You can answer using the tools, or answer directly using your knowledge without using the tools. '
            'Respond to the human as helpfully and accurately as possible.\n'
            'You have access to the following tools:\n'
            '{tools}\n'
            'Use a json blob to specify a tool by providing an action key (tool name) '
            'and an action_input key (tool input).\n'
            'Valid "action" values: "Final Answer" or  [{tool_names}]'
            'Provide only ONE action per $JSON_BLOB, as shown:\n\n'
            '```\n'
            '{{{{\n'
            '  "action": $TOOL_NAME,\n'
            '  "action_input": $INPUT\n'
            '}}}}\n'
            '```\n\n'
            'Follow this format:\n\n'
            'Question: input question to answer\n'
            'Thought: consider previous and subsequent steps\n'
            'Action:\n'
            '```\n'
            '$JSON_BLOB\n'
            '```\n'
            'Observation: action result\n'
            '... (repeat Thought/Action/Observation N times)\n'
            'Thought: I know what to respond\n'
            'Action:\n'
            '```\n'
            '{{{{\n'
            '  "action": "Final Answer",\n'
            '  "action_input": "Final response to human"\n'
            '}}}}\n'
            'Begin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary. '
            'Respond directly if appropriate. Format is Action:```$JSON_BLOB```then Observation:.\n'
            'history: {history}\n\n'
            'Question: {input}\n\n'
            'Thought: {agent_scratchpad}',
        "绘制柱形图":
            # '用户需要你绘制柱形图，请利用python工具进行绘制'
            # '绘制过程如果需要代码，请将代码一次性输出'
            # '使用下面的格式:\n'
            # 'Question: 你必须回答用户的问题\n'
            # 'Thought: 你应该时刻思考做什么.\n'
            # 'Action: 你应执行的操作应为 [{python: "Use python interpreter to run python code"}, {show_image: "display image by passing an address"}]\n'
            # 'Action Input: 操作的输入\n'
            # 'Observation: 操作的结果\n'
            # '... ( Thought/Action/Action Input/Observation 能够被重复多次)\n'
            # 'Thought: 我现在知道了最终答案\n'
            # 'Final Answer: 原始输入的最终答案\n'
            # 'Begin!\n\n'
            # 'history: {history}\n\n'
            # 'Question: {input}\n\n'
            # 'Thought: {agent_scratchpad}\n',
            'Answer the following questions as best you can. If it is in order, you can use some tools appropriately. '
            'You have access to the following tools:\n\n'
            '{tools}\n\n'
            '!!!Note that when you discover errors, please wash and correct the code and provide it in its entirety!!!'
            'Use the following format:\n'
            'Question: the input question you must answer1\n'
            'Thought: you should always think about what to do and what tools to use.\n'
            'Action: the action to take, should be one of [{tool_names}]\n'
            'Action Input: the input to the action\n'
            'Observation: the result of the action\n'
            '... (this Thought/Action/Action Input/Observation can be repeated zero or more times)\n'
            'Thought: I now know the final answer\n'
            'Final Answer: the final answer to the original input question\n'
            'Begin!\n\n'
            'history: {history}\n\n'
            'Question: {input}\n\n'
            'Thought: {agent_scratchpad}\n',
        "绘制折线图":
            '用户需要你绘制折线图，你可以使用python代码 '
            '绘制过程如果需要代码，请将代码一次性输出'
            '使用下面的格式:\n'
            'Question: 你必须回答的的问题\n'
            'Thought: 你应该时刻思考做什么，用什么工具来做.\n'
            'Action: 你应执行的操作应为 [{python: "Use python interpreter to run python code"}]\n'
            'Action Input: 操作的输入\n'
            'Observation: 操作的结果\n'
            '... ( Thought/Action/Action Input/Observation 能够被重复多次)\n'
            'Thought: 我现在知道了最终答案\n'
            'Final Answer: 原始输入的最终答案\n'
            'Begin!\n\n'
            'history: {history}\n\n'
            'Question: {input}\n\n'
            'Thought: {agent_scratchpad}\n',
        
    }
}