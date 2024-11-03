from fastapi.responses import StreamingResponse
from typing import List, Optional
import openai
from openai import AsyncOpenAI
from configs.model_config import ONLINE_LLM_MODEL as config 
aclient = AsyncOpenAI(api_key=config["openai-api"].get("api_key", "EMPTY"))
from configs import LLM_MODELS, logger, log_verbose
from server.utils import get_model_worker_config, fschat_openai_api_address
from pydantic import BaseModel


class OpenAiMessage(BaseModel):
    role: str = "user"
    content: str = "hello"


class OpenAiChatMsgIn(BaseModel):
    model: str = config["openai-api"].get("model_name", "EMPTY")
    messages: List[OpenAiMessage]
    temperature: float = 0.7
    n: int = 1
    max_tokens: Optional[int] =4096
    stop: List[str] = []
    stream: bool = True
    presence_penalty: int = 0
    frequency_penalty: int = 0


async def openai_chat(msg: OpenAiChatMsgIn):
    config = get_model_worker_config(msg.model)
    # print(f"{openai.api_key=}")
    # TODO: The 'openai.api_base' option isn't read in the client API. You will need to pass it when you instantiate the client, e.g. 'OpenAI(base_url=config.get("api_base_url", fschat_openai_api_address()))'
    # openai.api_base = config.get("api_base_url", fschat_openai_api_address())
    # print(f"{openai.api_base=}")
    print(msg)
    print(config)

    async def get_response(msg):
        data = msg.dict()

        try:
            response = await aclient.chat.completions.create(**data)
            if msg.stream:
                async for chunk in response:
                    if chunk.choices:
                        choice = chunk.choices[0]
                        if choice.delta and choice.delta.content:
                            print(choice.delta.content, end="", flush=True)
                            yield choice.delta.content
            else:
                if response.choices:
                    answer = response.choices[0].message.content
                    print(answer)
                    yield answer
        except Exception as e:
            msg = f"获取ChatCompletion时出错：{e}"
            logger.error(f'{e.__class__.__name__}: {msg}', exc_info=e if log_verbose else None)

    return StreamingResponse(
        get_response(msg),
        media_type='text/event-stream',
    )
