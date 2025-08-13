from flask import Flask, request, jsonify
from typing import Optional, Dict, Any, List
from contextlib import AsyncExitStack
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from pydantic import BaseModel, Field
import pandas as pd
import os
import json
import logging

class Arbitration_agent():
    def decide_and_update_state(self, state: dict) -> dict:
        """
        Analyzes the query to determine the task type and updates the state.
        This function acts as a node in the graph.
        """
        query = state.get('query', '').lower()
        vehicle_keywords = ["启动", "关闭"]
        if any(keyword in query for keyword in vehicle_keywords):
            logging.info("Arbitration: Decided on vehicle_task")
            return {"next_node": "vehicle_task"}
        
        logging.info("Arbitration: Decided on qa_task")
        return {"next_node": "qa_task"}

    def get_next_node(self, state: dict) -> str:
        """
        Reads the decision from the state to route to the next node.
        This function acts as the conditional edge router.
        """
        return state.get("next_node")