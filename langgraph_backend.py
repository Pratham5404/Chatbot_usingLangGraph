from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import operator
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver, InMemorySaver # persistance concept 

load_dotenv()

llm = HuggingFaceEndpoint(
    repo_id = 'meta-llama/Llama-3.3-70B-Instruct',
    task = 'text-generation'
)
model = ChatHuggingFace(llm = llm)

class ChatState(TypedDict):
    messages : Annotated[list[BaseMessage], add_messages] # we could have used normal operator.add function but in langgraph it is adviced to use this funciton as it is specifically designed for BaseMessage

def chat_node(state: ChatState):
    message = state['messages']

    response = model.invoke(message)
    return {'messages': [response]}

checkpointer = InMemorySaver()

graph = StateGraph(ChatState)
graph.add_node('chat_node', chat_node)
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)


chatbot = graph.compile(checkpointer = checkpointer)
