from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import AIMessage
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
        
        # 从 state 中获取完整的消息历史
        
        try:
            # 直接将历史消息列表传递给模型
            response_message = self.chat_model.invoke({"query": state.get("query"),"messages": state.get('messages', [])})
            logging.info(f"ChatAgent Result: {response_message}")
            # 返回一个字典来更新 state。
            # 1. 将 AI 的回复（AIMessage 对象）添加到 messages 列表中，以便 LangGraph 保存
            # 2. 将回复的文本内容放入 'response' 字段，以便 server.py 返回给客户端
            return {
                "messages": [response_message],
                "response": response_message.content
            }
        except Exception as e:
            logging.error(f"QA Agent Error: {e}")
            return {"response": f"QA Agent Error: {e}"}
