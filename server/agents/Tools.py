import logging
from langchain_core.tools import tool, Tool
from langgraph.prebuilt import ToolNode

@tool("start_vehicle")
def start_vehicle() -> str:
    """启动车辆"""
    logging.info("Executing: Start Vehicle")
    return "车辆已启动。"

@tool("stop_vehicle")
def stop_vehicle() -> str:
    """关闭车辆"""
    logging.info("Executing: Stop Vehicle")
    return "车辆已关闭。"

def get_vehicle_tools():
    return [
        Tool(
            name="start_vehicle",
            func=start_vehicle,
            description="启动车辆"
        ),
        Tool(
            name="stop_vehicle",
            func=stop_vehicle,
            description="关闭车辆"
        )
    ]
ToolsNode = ToolNode(get_vehicle_tools())
