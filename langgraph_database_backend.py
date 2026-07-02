from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import operator
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver # persistance concept 
import sqlite3

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


conn = sqlite3.connect(database='chatbot.db', check_same_thread=False) #as we will me using multiple thread so this feature in default cases check whether the works are done single threaddly or not

checkpointer = SqliteSaver(conn = conn)

graph = StateGraph(ChatState)
graph.add_node('chat_node', chat_node)
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)


chatbot = graph.compile(checkpointer = checkpointer)

def retrieve_all_threads(): 
    all_thread = set()
    for checkpoint in checkpointer.list(None): # none here is to say that we dont need check point for a single thread instead all the thread that exist in the database
        all_thread.add(checkpoint.config['configurable']['thread_id'])
    return all_thread


def get_thread_label(thread_id):
    """Retrieve the first user message from a thread to use as a label"""
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    messages = state.values.get('messages', [])
    
    # Find the first user message
    for message in messages:
        if isinstance(message, HumanMessage):
            label = message.content[:50] + ("..." if len(message.content) > 50 else "")
            return label
    
    # Fallback to truncated thread_id if no messages found
    return str(thread_id)[:8] + "..."