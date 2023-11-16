import streamlit as st
from llama_index import VectorStoreIndex, ServiceContext
from llama_index.llms import OpenAI
import openai
from llama_index import SimpleDirectoryReader
import hmac

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the passward is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()  # Do not continue if check_password is not True.

openai_api_key = st.sidebar.text_input('OpenAI API Key')
openai.api_key = openai_api_key

st.header("Chat with the Developertown docs 💬 📚")

if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me a question about Developertown's policies!"}
    ]

system_prompt = """You are an expert on DeveloperTown's policies and procedures, 
your job is to answer questions policy questions. Assume that all questions are related to these documents. Keep your
answers based on facts. If you can't find the answer in the supplied documents say 'Sorry, I don't know the answer to that'. 
Do not hallucinate information."""

if not openai_api_key.startswith('sk-'):
    st.warning('Please enter your OpenAI API key!', icon='⚠')
else:
    @st.cache_resource(show_spinner=False)
    def load_data():
        with st.spinner(text="Loading and indexing DT docs, hang tight! This should take 1-2 minutes."):

            reader = SimpleDirectoryReader(input_dir='./data', recursive=True)
            docs = reader.load_data()
            service_context = ServiceContext.from_defaults(llm=OpenAI(model="gpt-3.5-turbo-1106", temperature="0.5", system_prompt=system_prompt))
            index = VectorStoreIndex.from_documents(docs, service_context=service_context)
            return index
        
    index = load_data()
    chat_engine = index.as_chat_engine(chat_mode="condense_question", verbose = True)

    if prompt := st.chat_input("Your questions"):
        st.session_state.messages.append({"role": "user", "content": prompt})

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = chat_engine.chat(prompt)
                st.write(response.response)
                message = {"role": "assistant", "content": response.response}
                st.session_state.messages.append(message)