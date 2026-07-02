import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

CONFIG = {'configurable' : {'thread_id' : 'thread_1'}}

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input("Type here....")
if user_input:
    # Append the user's message instead of overwriting the history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    # Placeholder assistant reply (echo). Replace with actual assistant call.
    with st.chat_message('assistant'):
        assistant_reply = st.write_stream(
            message_chunk.content for message_chunk, metadata in chatbot.stream(
                {'messages' : [HumanMessage(content = user_input)]},
                config = CONFIG,
                stream_mode= 'messages'
            )
        )
    st.session_state['message_history'].append({'role': 'assistant', 'content': assistant_reply})