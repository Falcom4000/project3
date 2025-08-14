import logging
from langchain.tools import tool, Tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
import configparser
from langchain_core.prompts import ChatPromptTemplate

class TaskAgent():
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

    @tool("start_vehicle")
    def start_vehicle(self) -> str:
        """启动车辆"""
        logging.info("Executing: Start Vehicle")
        return "车辆已启动。"

    @tool("stop_vehicle")
    def stop_vehicle(self) -> str:
        """关闭车辆"""
        logging.info("Executing: Stop Vehicle")
        return "车辆已关闭。"

    def get_executor(self):
        tools = get_vehicle_tools(self)
        llm = ChatOpenAI(
            model=self.config.get('agent', 'model', fallback='gpt-3.5-turbo'),
            temperature=0,
            base_url=self.config.get('agent', 'base_url', fallback=None)
        )
        agent = create_tool_calling_agent(llm, tools, prompt=self.prompt_template)
        executor = AgentExecutor(agent=agent, tools=tools)
        return executor
        
    def execute(self, state: dict) -> dict:
        query = state.get('query')
        executor = self.get_executor()
        result = executor.invoke({"query": query,"messages": state.get('messages', [])})
        logging.info(f"TaskAgent Result: {result}")
        return {"response": result['output'], "messages": [result['output']]}

def get_vehicle_tools(agent: TaskAgent):
    return [
        Tool.from_function(
            agent.start_vehicle,
            name="start_vehicle",
            description="启动车辆"
        ),
        Tool.from_function(
            agent.stop_vehicle,
            name="stop_vehicle",
            description="关闭车辆"
        ),
    ]
