from typing import TypedDict, List, Any, Annotated
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    query: str
    response: str
    # 仲裁代理的决定
    next_node: str
    # 使用 Annotated 和 operator.add 来告诉 LangGraph 将新消息附加到列表中，而不是替换它
    messages: Annotated[List[BaseMessage], operator.add]