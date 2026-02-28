import streamlit as st
from openai import OpenAI
import httpx
from streamlit_js_eval import streamlit_js_eval



st.set_page_config(page_title="Chat", page_icon=":robot:")
st.header("ChatBot")

st.write(st.secrets["OPENAI_API_KEY"])
st.write(st.secrets["OPENAI_API_BASE"])

# region vars
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "messages" not in st.session_state:
        st.session_state.messages = []
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False

def setup_complete():
    st.session_state.setup_complete = True
def feedback_shown():
    st.session_state.feedback_shown = True
# endregion

# region set up data
if not st.session_state.setup_complete:
    # region Personal info
    st.subheader("Personal info", divider="rainbow")

    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""

    st.session_state["name"] = st.text_input(label="Name", max_chars=50, value=st.session_state["name"], placeholder="Enter your fucking name!")
    st.session_state["experience"] = st.text_area(label="Experience", value=st.session_state["experience"], height=None, max_chars=200, placeholder="Enter your experience")
    st.session_state["skills"] = st.text_area(label="Skills", value=st.session_state["skills"], height=None, max_chars=200, placeholder="List your skills")

    st.write(f"Name: {st.session_state["name"]}")
    st.write(f"Your experience: {st.session_state["experience"]}")
    st.write(f"Skils: {st.session_state["skills"]}")
    # endregion

    # region Company info
    st.subheader("Company and position", divider="rainbow")

    if "level" not in st.session_state:
        st.session_state["level"] = ""
    if "position" not in st.session_state:
        st.session_state["position"] = ""
    if "company" not in st.session_state:
        st.session_state["company"] = ""

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["level"] = st.radio("Choose level", key="visibility", options=["Junior", "Middle", "Senior", "Lead"])
    with col2:
        st.session_state["position"] = st.selectbox("Choose position", options=["Frontend", "Backend", "Fullstack", "DevOps", "QA", "PM", "Designer", "Data Scientist"])
    st.session_state["company"] = st.selectbox("Choose company", options=["Apple", "Google", "Microsoft", "Amazon", "Facebook", "Twitter", "Netflix", "Uber", "Airbnb", "Spotify"])

    st.write(f"Company info: {st.session_state["level"]} {st.session_state["position"]} at {st.session_state["company"]}")
    # endregion

    if st.button("Start Interview", on_click=setup_complete):
        st.write("SetUp complete. Starting interview...")
# endregion

#region interview chat
if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:
    
    st.info("Start by introducing yourself.", icon="👌")
    
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url=st.secrets["OPENAI_API_BASE"], http_client=httpx.Client(verify=False))
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4.1-nano"

    if not st.session_state.messages:
        st.session_state.messages = [
            {"role": "system", 
            "content": f"You are an HR executive that interviews an interviewee called {st.session_state["name"]} with experience {st.session_state["experience"]} and skills {st.session_state["skills"]}. You should interview them for the position {st.session_state["level"]} {st.session_state["position"]} at the company {st.session_state["company"]}."}
        ]

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input("Your answer", max_chars=1000):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            if st.session_state.user_message_count < 5:
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = ""
                    for response in client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                        stream=True,
                    ):
                        full_response += (response.choices[0].delta.content or "")
                        message_placeholder.markdown(full_response + "|")
                    message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.session_state.user_message_count += 1
    else:
        st.session_state.chat_complete = True
# endregion


if st.session_state.chat_complete:# and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=feedback_shown):
        st.write("Generating feedback...")

        conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])
        
        feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url=st.secrets["OPENAI_API_BASE"], http_client=httpx.Client(verify=False))
        
        feedback_prompt = """
                        You are helpful tool that provides feedback on an interviewee performance.
                        Before the Feedback give a score of 1 to 10.
                        Follow this format:
                        Overal Score: //Your score
                        Feedback: //Here you put your feedback
                        Give only the feedback do not ask any additional questions.
                        """

        feedback_complition = feedback_client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": "system", "content": feedback_prompt},
                {"role": "user", "content": conversation_history}
            ]
        )

        st.write(feedback_complition.choices[0].message.content)

        if st.button("Restart Interview", type="primary"):
            streamlit_js_eval(js_expressions="parent.window.location.reload()")
