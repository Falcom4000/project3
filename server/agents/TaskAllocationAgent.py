import logging
from langchain.tools import tool, Tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
import configparser
from langchain_core.prompts import ChatPromptTemplate
from agents.Tools import get_vehicle_tools
class TaskAllocationAgent():
    def __init__(self, config: configparser.ConfigParser):
        self.config = config
        base_url = config.get('agent', 'base_url', fallback=None)
        model = config.get('agent', 'model', fallback='gpt-3.5-turbo')
        logging.info(f"Initializing QA_agent with model='{model}' and base_url='{base_url}'")
        self.prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", "Please choose the best function to perform based on query of user"),
        ("system", "chat history: {messages}"),
        ("user", "{query}"),
        ("placeholder", "{agent_scratchpad}")
    ]
)
    def get_executor(self):
        tools = get_vehicle_tools()
        llm = ChatOpenAI(
            model=self.config.get('agent', 'model', fallback='gpt-3.5-turbo'),
            temperature=0,
            base_url=self.config.get('agent', 'base_url', fallback=None)
        )
        return self.prompt_template | llm.bind_tools(tools)

    def execute(self, state: dict) -> dict:
        query = state.get('query')
        executor = self.get_executor()
        result = executor.invoke({"query": query,"messages": state.get('messages', [])})
        logging.info(f"TaskAgent Result: {result}")
        return {"messages": [result],"response": result.content}

