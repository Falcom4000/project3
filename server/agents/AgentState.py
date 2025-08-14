from typing import TypedDict, List, Any, Annotated
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    query: str
    response: str
    next_node: str
    messages: Annotated[List[BaseMessage], operator.add]