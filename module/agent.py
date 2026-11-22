from typing import Any, AsyncIterator, Dict, List, Optional, Union, Type
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from pydantic import BaseModel
from loguru import logger


class Agent:
    def __init__(
        self,
        model: str = "Qwen/Qwen2.5-14B-Instruct-GPTQ-Int4",
        base_url: str = "https://llm.bkhightech.net/v1",
        api_key: str = "sk-vllm-bkhightech",
        temperature: float = 0,
        max_completion_tokens: int = 7000,
        default_headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = 300,
    ) -> None:
        self.model = ChatOpenAI(
            model=model,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
            max_completion_tokens=max_completion_tokens,
            default_headers={"User-Agent": "Mozilla/5.0"},
            timeout=timeout,
        )

    @staticmethod
    def _build_content(
        user_prompt: Union[str, List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        if isinstance(user_prompt, str):
            return [{"type": "text", "text": user_prompt}]
        return user_prompt

    @staticmethod
    def _bind_response_schema(llm, response_schema):
        if response_schema is None:
            return llm
        if isinstance(response_schema, type) and issubclass(response_schema, BaseModel):
            return llm.with_structured_output(response_schema)
        if isinstance(response_schema, dict):
            return llm.bind(
                response_format={
                    "type": "json_schema",
                    "json_schema": response_schema,
                }
            )
        return llm

    async def generate(
        self,
        *,
        system_prompt: Optional[str] = None,
        user_prompt: Union[str, List[Dict[str, Any]]],
        response_schema: Optional[Union[Type[BaseModel], Dict[str, Any]]] = None,
        tools: Optional[List[Any]] = None,
        max_tool_rounds: int = 3,
    ) -> Any:
        messages: List[Any] = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=self._build_content(user_prompt)))

        # Không apply schema trong pha tool
        llm = self.model
        if tools:
            llm = llm.bind_tools(tools)

        # Nếu không có tools: gọi 1 phát với schema (nếu có)
        if not tools:
            final_llm = self._bind_response_schema(llm, response_schema)
            resp = await final_llm.ainvoke(messages)
            return resp if response_schema else getattr(resp, "content", resp)

        # Có tools: loop thực thi tool -> gửi ToolMessage -> lặp đến khi hết tool_calls
        history: List[Any] = messages[:]
        ai_msg = await llm.ainvoke(history)
        history.append(ai_msg)

        rounds = 0
        name_to_tool = {
            getattr(t, "name", getattr(t, "name", None))
            or getattr(t, "__name__", ""): t
            for t in (tools or [])
        }

        while getattr(ai_msg, "tool_calls", None) and rounds < max_tool_rounds:
            tool_msgs: List[ToolMessage] = []
            for tc in ai_msg.tool_calls:
                name = tc.get("name")
                args = tc.get("args", {})
                tool_id = tc.get("id")
                tool_obj = name_to_tool.get(name)
                if tool_obj is None:
                    tool_msgs.append(
                        ToolMessage(
                            content=f"Unknown tool: {name}",
                            name=name or "unknown",
                            tool_call_id=tool_id,
                        )
                    )
                    continue
                try:
                    if hasattr(tool_obj, "ainvoke"):
                        result = await tool_obj.ainvoke(args)
                    elif hasattr(tool_obj, "invoke"):
                        result = tool_obj.invoke(args)
                    else:
                        result = tool_obj(**args)
                except Exception as e:
                    result = f"Tool execution error: {e}"
                tool_msgs.append(
                    ToolMessage(content=str(result), name=name, tool_call_id=tool_id)
                )

            history.extend(tool_msgs)
            ai_msg = await llm.ainvoke(history)
            history.append(ai_msg)
            rounds += 1

        # Pha cuối: áp dụng schema để sinh câu trả lời cuối cùng (không tool)
        final_llm = self._bind_response_schema(self.model, response_schema)
        final_llm = final_llm.bind(tool_choice="none")
        final = await final_llm.ainvoke(history)
        return final if response_schema else getattr(final, "content", final)

    async def astream_generate(
        self,
        *,
        system_prompt: Optional[str] = None,
        user_prompt: Union[str, List[Dict[str, Any]]],
    ) -> AsyncIterator[str]:
        """
        Stream tokens từ LLM.

        Note: Không hỗ trợ tools và response_schema trong streaming mode.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt

        Yields:
            Tokens as strings
        """
        messages: List[Any] = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=self._build_content(user_prompt)))

        async for chunk in self.model.astream(messages):
            content = getattr(chunk, "content", None)
            if content:
                yield content

    def _run_coro(self, coro):
        """Run coroutine from sync code, with Jupyter-friendly fallback."""
        try:
            return asyncio.run(coro)
        except RuntimeError:
            try:
                import nest_asyncio

                nest_asyncio.apply()
            except Exception:
                pass
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(coro)

    def generate_sync(
        self,
        *,
        system_prompt: Optional[str] = None,
        user_prompt: Union[str, List[Dict[str, Any]]],
        response_schema: Optional[Union[Type[BaseModel], Dict[str, Any]]] = None,
        tools: Optional[List[Any]] = None,
        max_tool_rounds: int = 3,
    ) -> Any:
        """Synchronous wrapper around async `generate` for convenience."""
        return self._run_coro(
            self.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=response_schema,
                tools=tools,
                max_tool_rounds=max_tool_rounds,
            )
        )


import datetime
from langchain_core.tools import tool
import asyncio


class ResponseFormat(BaseModel):
    answer: str
    question: str


@tool
def now_iso():
    """Get the current time in ISO format"""
    return datetime.datetime.now().isoformat()


async def main():
    client = Agent()

    res = await client.generate(
        system_prompt="Bạn là một trợ lý tư vấn viên hữu ích và chính xác.",
        user_prompt="Bây giờ là mấy giờ và ngày mấy?",
        response_schema=ResponseFormat,
    )
    print(res)


if __name__ == "__main__":
    asyncio.run(main())
