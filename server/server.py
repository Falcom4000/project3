from flask import Flask, request, jsonify
from typing import Optional, Dict, Any, List, TypedDict
from contextlib import AsyncExitStack
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
import os
import configparser
import logging

# Import agent classes
from Arbitration_agent import Arbitration_agent
from QA_agent import QA_agent
from Task_agent import Task_agent

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

# Define the state for our graph
class AgentState(TypedDict):
    query: str
    response: str
    next_node: str # Add key to store routing decision

class Server():
    def __init__(self):
        self.app = Flask(__name__)
        self.app.add_url_rule('/query', view_func=self.handle_query, methods=['POST'])
        
        # Read configuration
        config = configparser.ConfigParser()
        config_path = os.path.join(config_dir, 'config.ini')
        config.read(config_path)
        self.host = config.get('server', 'host', fallback='0.0.0.0')
        self.port = config.getint('server', 'port', fallback=5000)

        # Instantiate agents
        self.arbitration_agent = Arbitration_agent()
        self.qa_agent = QA_agent(config) # Pass config to agent
        self.task_agent = Task_agent()

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

        return workflow.compile()

    def run(self):
        logging.info(f"Starting server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=True)

    def handle_query(self):
        """
        Handles a query from the client by running it through the graph.
        """
        data = request.get_json()
        if not data:
            logging.error("Received request without JSON body")
            return jsonify({"error": "Request must be JSON"}), 400

        query = data.get('text')
        if not query:
            logging.error("Received JSON but missing 'text' field")
            return jsonify({"error": "Missing 'text' in request body"}), 400
        
        logging.info(f"Received query: {query}")
        # Run the query through the graph
        inputs = {"query": query}
        final_state = self.graph.invoke(inputs)

        response_text = final_state.get("response", "No response generated.")
        logging.info(f"Sending response: {response_text}")

        return jsonify({"text": response_text})

if __name__ == '__main__':
    server = Server()
    server.run()
    server = Server()
    server.run()
