from flask import Flask, request, jsonify
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
import os
import configparser
import logging
import uuid # 导入 uuid 模块
from langchain_core.messages import HumanMessage

# Import agent classes
from agents.ArbitrationAgent import ArbitrationAgent
from agents.ChatAgent import ChatAgent
from agents.AgentState import AgentState
from agents.TaskAgent import TaskAgent

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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()  # Also log to console
    ]
)
# --- End Logging Setup ---
class Server():
    def __init__(self):
        self.app = Flask(__name__)
        self.app.add_url_rule('/query', view_func=self.handle_query, methods=['POST'])
        self.memory = InMemorySaver()
        # Read configuration
        config = configparser.ConfigParser()
        config_path = os.path.join(config_dir, 'config.ini')
        config.read(config_path)
        self.host = config.get('server', 'host', fallback='0.0.0.0')
        self.port = config.getint('server', 'port', fallback=5000)

        # Instantiate agents
        self.arbitration_agent = ArbitrationAgent()
        self.qa_agent = ChatAgent(config) # Pass config to agent
        self.task_agent = TaskAgent()

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
        workflow.add_edge('vehicle_task', END)

        return workflow.compile(checkpointer=self.memory)

    def run(self):
        logging.info(f"Starting server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=True)

    def handle_query(self):
        """
        Handles a query from the client by running it through the graph,
        maintaining conversation history via checkpointer.
        """
        data = request.get_json()
        if not data:
            logging.error("Received request without JSON body")
            return jsonify({"error": "Request must be JSON"}), 400

        query = data.get('text')
        # 从客户端获取 session_id，如果没有则创建一个新的
        session_id = data.get('session_id', str(uuid.uuid4()))

        if not query:
            logging.error("Received JSON but missing 'text' field")
            return jsonify({"error": "Missing 'text' in request body"}), 400
        
        logging.info(f"Received query for session {session_id}: {query}")

        # 为 LangGraph 的 checkpointer 设置配置
        config = {"configurable": {"thread_id": session_id}}

        # 关键改动：将输入包装成 HumanMessage 并放入 messages 列表
        # AgentState 中的 'query' 字段也会被设置
        inputs = {"messages": [HumanMessage(content=query)], "query": query}
        
        # 使用 config 调用图，LangGraph 会自动处理状态的保存和加载
        # 它会将新的 HumanMessage 添加到历史记录中
        final_state = self.graph.invoke(inputs, config=config)

        # 从最终状态中获取响应
        # 假设您的 ChatAgent 会将最终回复放入 'response' 字段
        response_text = final_state.get("response", "No response generated.")
        logging.info(f"Sending response for session {session_id}: {response_text}")

        # 在响应中返回 session_id，以便客户端可以在下一轮请求中使用
        return jsonify({"text": response_text, "session_id": session_id})

if __name__ == '__main__':
    server = Server()
    server.run()