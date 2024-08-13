from hashlib import sha256
import streamlit as st

def get_flag(user_id: int, problem: str):
    prefix = st.secrets.flag[problem]["prefix"]
    salt = st.secrets.flag[problem]["salt"]
    hash = sha256(f"{user_id}{salt}".encode()).hexdigest()[:16]
    return prefix + "{" + hash + "}"
