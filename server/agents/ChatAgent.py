from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import logging
import configparser

class ChatAgent():
    def __init__(self, config: configparser.ConfigParser):
        base_url = config.get('agent', 'base_url', fallback=None)
        model = config.get('agent', 'model', fallback='gpt-3.5-turbo')
        
        logging.info(f"Initializing QA_agent with model='{model}' and base_url='{base_url}'")
        
        self.chat_model = ChatOpenAI(
            model=model, 
            temperature=0,
            base_url=base_url
        )
        self.prompt = PromptTemplate.from_template("请回答以下问题: {query}")
        self.chain = self.prompt | self.chat_model

    def answer(self, state: dict) -> dict:
        """
        Handles QA tasks using a language model.
        """
        logging.info("Executing QA Agent")
        query = state.get('query')
        try:
            response = self.chain.invoke({"query": query})
            return {"response": response.content}
        except Exception as e:
            logging.error(f"QA Agent Error: {e}")
            return {"response": f"QA Agent Error: {e}"}
