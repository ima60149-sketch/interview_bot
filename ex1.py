import streamlit as st

st.title("nested buttons")
if "show_second_button" not in st.session_state:
    st.session_state.show_second_button = False

if st.button("first button"):
    st.session_state.show_second_button = True

if st.session_state.show_second_button:
    st.write("1 clicked")
    if st.button("sec button"):
        st.write("2 clicked")