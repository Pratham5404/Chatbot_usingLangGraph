import streamlit as st  # Streamlit manages the browser UI and session state
from langgraph_database_backend import chatbot, retrieve_all_threads, get_thread_label  # Chatbot backend object used for model interactions
from langchain_core.messages import HumanMessage  # Message type for user messages
import uuid  # Used to create unique conversation thread IDs
# Utility functions

def generate_thread_id():
    # Generate a unique identifier for a new conversation thread
    thread_id = uuid.uuid4()
    return thread_id


def reset_chat():
    # Reset the current chat by creating a new thread and clearing history
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id  # update the current thread id
    add_thread(st.session_state['thread_id'])  # make sure the new thread is tracked
    st.session_state['message_history'] = []  # clear the current chat history


def add_thread(thread_id):
    # Add a new thread id to the saved thread list if it is not already there
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)


def load_conversation(thread_id):
    # Load saved conversation messages for the selected thread id from the backend
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    # Return the stored messages list, or an empty list if no messages are available
    return state.values.get('messages', [])


# Session Setup
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []  # initialize message history if missing

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()  # initialize current thread id if missing

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = list(retrieve_all_threads())  # initialize saved thread list if missing

if 'thread_labels' not in st.session_state:
    st.session_state['thread_labels'] = {}  # store display names/first messages for each thread
    # Load labels from database for all existing threads
    for thread_id in st.session_state['chat_threads']:
        st.session_state['thread_labels'][thread_id] = get_thread_label(thread_id)

add_thread(st.session_state['thread_id'])  # ensure current thread is included in the saved thread list

# Sidebar Setup
st.sidebar.title('LangGraph ChatBot')  # sidebar title

if st.sidebar.button("New Conversation"):
    reset_chat()  # start a fresh conversation when the button is clicked

st.sidebar.header('My Conversations')  # header shown above the thread list

for thread_id in st.session_state['chat_threads'][::-1]:
    # Show the most recent threads first by iterating in reverse order
    # Get the label for this thread (first message or default to truncated thread_id)
    if thread_id in st.session_state['thread_labels']:
        label = st.session_state['thread_labels'][thread_id]
    else:
        label = str(thread_id)[:8] + "..."  # fallback to truncated thread_id
    
    if st.sidebar.button(label, key=f"thread_{thread_id}"):
        st.session_state['thread_id'] = thread_id  # switch to the selected thread
        messages = load_conversation(thread_id)  # load previously saved messages

        temp_message = []  # temporary storage for restored messages
        for message in messages:
            if isinstance(message, HumanMessage):
                role = 'user'  # human messages are user role
            else:
                role = 'assistant'  # all other messages are assistant role
            temp_message.append({'role': role, 'content': message.content})
        st.session_state['message_history'] = temp_message  # restore history to session state


CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}  # config passed to backend for current thread

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])  # render every message from the current history

user_input = st.chat_input("Type here....")  # chat input field for the user
if user_input:
    # Store the first message as the thread label if this is the first message
    if st.session_state['thread_id'] not in st.session_state['thread_labels']:
        # Truncate first message to 50 chars for display
        label = user_input[:50] + ("..." if len(user_input) > 50 else "")
        st.session_state['thread_labels'][st.session_state['thread_id']] = label
    
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})  # save the new user message
    with st.chat_message('user'):
        st.text(user_input)  # show the user's message immediately

    with st.chat_message('assistant'):
        assistant_reply = st.write_stream(
            message_chunk.content for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )
        )  # stream assistant response from backend
    st.session_state['message_history'].append({'role': 'assistant', 'content': assistant_reply})  # save assistant response