from typing import Optional, Dict, Any, List, TypedDict
class AgentState(TypedDict):
    query: str
    response: str
    next_node: str