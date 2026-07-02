from streamlit_frontend_threading import ensure_session_state, reset_chat


def test_thread_ids_persist_across_reruns():
    state = {}

    ensure_session_state(state)
    first_thread_id = state["thread_id"]

    assert state["chat_threads"] == [first_thread_id]

    ensure_session_state(state)
    assert state["chat_threads"] == [first_thread_id]

    second_thread_id = reset_chat(state)

    assert second_thread_id != first_thread_id
    assert state["thread_id"] == second_thread_id
    assert state["chat_threads"] == [first_thread_id, second_thread_id]
    assert state["message_history"] == []
