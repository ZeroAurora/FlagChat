from hashlib import md5
import streamlit as st

def get_flag(user_id: int):
    prefix = st.secrets.flag_prefix
    salt = st.secrets.flag_salt
    hash = md5(f"{user_id}{salt}".encode()).hexdigest()
    return prefix + "{" + hash + "}"
