from langchain_community.chat_models import ChatOpenAI
from .AgentState import AgentState
import logging
import configparser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import interrupt, Command
from typing import Literal, TypedDict
from langgraph.graph import StateGraph, END
class ApproveAgent():
    def human_approval(self, state: AgentState) -> Command[Literal["tools", END]]:
        messages = state.get('messages', [])
        tool_calls = getattr(messages[-1], "tool_calls", None) if messages else None
        if not tool_calls:
            logging.error("No tool calls found in the last message.")
            return Command(goto=END)
        decision = interrupt({
            "question": "Do you approve the following tool calls? Type 'yes' to approve.",
            "function": tool_calls,
        })

        if decision and decision.lower() in ["yes", "y"]:
            return Command(goto="tools")
        else:
            return Command(goto=END)