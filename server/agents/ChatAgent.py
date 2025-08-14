from langchain_community.chat_models import ChatOpenAI
from .AgentState import AgentState
import logging
import configparser
from langchain_core.prompts import ChatPromptTemplate

class ChatAgent():
    def __init__(self, config: configparser.ConfigParser):
        base_url = config.get('agent', 'base_url', fallback=None)
        model = config.get('agent', 'model', fallback='gpt-3.5-turbo')
        
        logging.info(f"Initializing QA_agent with model='{model}' and base_url='{base_url}'")
        
        chat_model = ChatOpenAI(
            model=model, 
            temperature=0,
            base_url=base_url
        )
        self.prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", "Please answer the question based on query and chat history of user"),
            ("system", "chat history: {messages}"),
            ("user", "{query}"),
        ])
        self.chat_model = self.prompt_template | chat_model
        

    def answer(self, state: AgentState) -> dict:
        """
        使用完整的对话历史来生成回答。
        """
        logging.info("Executing QA Agent with conversation history")
        try:
            response_message = self.chat_model.invoke({"query": state.get("query"),"messages": state.get('messages', [])})
            logging.info(f"ChatAgent Result: {response_message}")
            return {
                "messages": [response_message],
                "response": response_message.content
            }
        except Exception as e:
            logging.error(f"QA Agent Error: {e}")
            return {"response": f"QA Agent Error: {e}"}
