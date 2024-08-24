from hashlib import sha256

import streamlit as st


def get_flag_prefix(problem: str) -> str:
    return st.secrets.flag[problem]["prefix"]

@st.cache_data
def get_flag_content(user_id: int, problem: str):
    salt = st.secrets.flag[problem]["salt"]
    hash = sha256(f"{user_id}{salt}".encode()).hexdigest()[:16]
    return hash

@st.cache_data
def get_flag(user_id: int, problem: str):
    prefix = get_flag_prefix(problem)
    content = get_flag_content(user_id, problem)
    return prefix + "{" + content + "}"
