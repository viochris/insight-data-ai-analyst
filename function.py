import streamlit as st
import pandas as pd
import os

def init_state():
    """
    Initializes the Streamlit session state variables if they do not already exist.
    This ensures that the application has the necessary persistent storage for
    messages, uploaded files, the dataframe, the LLM instance, and conversation memory
    before any logic is executed.
    """
    # Check and initialize 'messages' list to store chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Check and initialize 'processed_files' list to track uploaded files
    if "processed_files" not in st.session_state:
        st.session_state.processed_files = []
    
    # Check and initialize 'final_df' to hold the main DataFrame
    if "final_df" not in st.session_state:
        st.session_state.final_df = []
    
    # Check and initialize 'llm' for the language model instance
    if "llm" not in st.session_state:
        st.session_state.llm = None
    
    # Check and initialize 'agent_memory' for conversation context
    if "agent_memory" not in st.session_state:
        st.session_state.agent_memory = None

def reset_conversation():
    """
    Clears the chat history specifically.
    This allows the user to start a fresh conversation topic without deleting
    the uploaded data or re-initializing the model.
    """
    st.session_state.messages = []
    st.toast("Chat history cleared!", icon="🧹")

def reset_state():
    """
    Performs a full system reset.
    This function clears ALL session state variables, including uploaded files,
    the active dataframe, the LLM, and the agent executor. It effectively
    restarts the user session from scratch.
    """
    st.session_state.messages = []
    st.session_state.processed_files = []
    st.session_state.final_df = []
    st.session_state.agent_memory = None
    st.session_state.llm = None
    
    # Safely remove the 'agent_executor' from session state if it exists
    # This forces the app to rebuild the agent with fresh settings next time
    st.session_state.pop("agent_executor", None)
    
    st.toast("System state has been fully reset!", icon="🔄")

def change_on_api_key():
    """
    Callback function triggered when the user modifies the Google API Key input.
    It performs a hard reset of the session (clearing messages, files, and model)
    to ensure security and force the agent to re-initialize with the new credentials.
    """
    st.session_state.messages = []
    st.session_state.processed_files = []
    st.session_state.final_df = []
    st.session_state.agent_memory = None
    st.session_state.llm = None
    
    # Remove the existing agent executor so it can be rebuilt with the new API key
    st.session_state.pop("agent_executor", None)
    
    st.toast("API Key changed. Session refreshed.", icon="🔑")

def change_on_lan():
    """
    Triggered when the user modifies the 'Language' selection in the sidebar.
    This performs a specific reset to ensure the new language preference is 
    injected into the Agent's system prompt.
    """
    # 1. Destroy the current Agent Executor
    # We must remove it from the session state so that the app detects it's missing
    # and rebuilds it with the new 'chosen_language' variable in the prompt.
    st.session_state.pop("agent_executor", None)
    
    # 2. Notify the user of the update
    # Provides visual feedback that the system is re-configuring its 'brain' for the new language.
    st.toast("Language preference updated! Reconfiguring AI Agent...", icon="🌐")

def read_files(uploaded_file):
    """
    Reads an uploaded file object and converts it into a pandas DataFrame.
    
    Args:
        uploaded_file: The file object returned by streamlit's file_uploader.
        
    Returns:
        pd.DataFrame: The loaded data if the format is valid (.csv or .xlsx).
        None: If the file extension is not supported.
    """
    filenames = uploaded_file.name.lower()
    ext = os.path.splitext(filenames)[-1]

    # Check file extension and use the appropriate pandas loading function
    if ext == ".csv" and filenames.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif ext == ".xlsx" and filenames.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    else:
        # Return None if the file format matches neither CSV nor Excel
        df = None

    return df