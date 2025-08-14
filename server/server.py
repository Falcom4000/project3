from flask import Flask, request, jsonify
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import tools_condition
from langgraph.checkpoint.redis import RedisSaver
import os
import configparser
import logging
import uuid
from langchain_core.messages import HumanMessage

# Import agent classes
from agents.ArbitrationAgent import ArbitrationAgent
from agents.ChatAgent import ChatAgent
from agents.AgentState import AgentState
from agents.TaskAllocationAgent import TaskAllocationAgent
from agents.ApproveAgent import ApproveAgent
from agents.Tools import ToolsNode

# Define base path to locate config and log files
base_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(base_dir, '..')
config_dir = os.path.join(project_root, 'config')

# Load environment variables for OpenAI API key from config/.env
env_path = os.path.join(config_dir, '.env')
load_dotenv(dotenv_path=env_path)

# --- Logging Setup ---
log_dir = os.path.join(project_root, 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, 'server.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
    ]
)
# --- End Logging Setup ---
class Server():
    def __init__(self):
        # Read configuration
        config = configparser.ConfigParser()
        self.config = config
        config_path = os.path.join(config_dir, 'config.ini')
        config.read(config_path)
        self.app = Flask(config.get('server', 'name', fallback=__name__))
        self.app.add_url_rule('/query', view_func=self.handle_query, methods=['POST'])

        self.checkpointer = None
        with RedisSaver.from_conn_string(self.config.get('redis', 'connection_string', fallback='redis://localhost:6379/0')) as cp:
            cp.setup()
            self.checkpointer = cp

        self.host = config.get('server', 'host', fallback='0.0.0.0')
        self.port = config.getint('server', 'port', fallback=5000)

        # Instantiate agents
        self.arbitration_agent = ArbitrationAgent()
        self.qa_agent = ChatAgent(config)
        self.task_agent = TaskAllocationAgent(config)
        self.tool_node = ToolsNode
        self.approval_agent = ApproveAgent()

        # Build the graph
        self.graph = self._build_graph()
        logging.info("Server initialized and graph built.")

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        # Add nodes for each agent's action
        # The arbitration agent now has a node function
        workflow.add_node("arbitration", self.arbitration_agent.decide_and_update_state)
        workflow.add_node("qa_task", self.qa_agent.answer)
        workflow.add_node("vehicle_task", self.task_agent.execute)
        workflow.add_node("tools", self.tool_node.invoke)
        workflow.add_node("approve", self.approval_agent.human_approval)


        # The entry point is the arbitration node
        workflow.set_entry_point("arbitration")

        # The conditional edge now reads the decision from the state
        workflow.add_conditional_edges(
            "arbitration",
            self.arbitration_agent.get_next_node, # Use the new router method
            {
                "qa_task": "qa_task",
                "vehicle_task": "vehicle_task",
            }
        )

        # The specialist agents finish the process
        workflow.add_edge('qa_task', END)
        workflow.add_conditional_edges("vehicle_task", tools_condition, {"tools": "approve", "__end__": "__end__"})
        workflow.add_edge("approve", "tools")
        workflow.add_edge("approve", END)
        return workflow.compile(checkpointer=self.checkpointer)

    def run(self):
        logging.info(f"Starting server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=True)

    def handle_query(self):
        data = request.get_json()
        if not data:
            logging.error("Received request without JSON body")
            return jsonify({"error": "Request must be JSON"}), 400

        session_id = data.get('session_id', str(uuid.uuid4()))
        config = {"configurable": {"thread_id": session_id}}

        # 判断是否是 resume 输入（人类审批等）
        if 'resume' in data:
            # resume 输入直接作为 Command 传给 graph
            from langgraph.types import Command
            resume_value = data['resume']
            logging.info(f"Received resume input for session {session_id}: {resume_value}")
            final_state = self.graph.invoke(Command(resume=resume_value), config=config)
        else:
            query = data.get('text')
            if not query:
                logging.error("Received JSON but missing 'text' field")
                return jsonify({"error": "Missing 'text' in request body"}), 400
            logging.info(f"Received query for session {session_id}: {query}")
            inputs = {"messages": [HumanMessage(content=query)], "query": query}
            final_state = self.graph.invoke(inputs, config=config)

        # 检查是否需要人类输入
        if '__interrupt__' in final_state:
            interrupt_info = final_state['__interrupt__']
            logging.info(f"Interrupt detected for session {session_id}: {interrupt_info}")
            # 取第一个 Interrupt 对象
            if isinstance(interrupt_info, list) and interrupt_info:
                interrupt_obj = interrupt_info[0]
                interrupt_value = getattr(interrupt_obj, "value", {})
            else:
                interrupt_value = interrupt_info if isinstance(interrupt_info, dict) else {}
            question = interrupt_value.get('question', 'Please provide input for approval.')
            function_calls = interrupt_value.get('function', [])
            # 如果 function_calls 是列表，取第一个工具的 name 和 args
            if function_calls and isinstance(function_calls, list):
                function_name = function_calls[0].get('name', '')
                function_args = function_calls[0].get('args', {})
            else:
                function_name = ''
                function_args = {}
            return jsonify({
                "interrupt": True,
                "question": question,
                "function": function_name,
                "args": function_args,
                "session_id": session_id
            })

        response_text = final_state.get("response", "No response generated.")
        logging.info(f"Sending response for session {session_id}: {final_state}")
        return jsonify({"text": response_text, "session_id": session_id})

if __name__ == '__main__':
    server = Server()
    server.run()