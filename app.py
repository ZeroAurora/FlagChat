import streamlit as st
from sqlalchemy import text

from schemas import metadata_obj

conn = st.connection("db", type="sql")
metadata_obj.create_all(conn.engine)
with conn.session as s:
    s.execute(text("PRAGMA journal_mode=WAL;"))

if st.button("Neuro"):
    st.switch_page("pages/neuro.py")

if st.button("Evil"):
    st.switch_page("pages/evil.py")

if st.button("Complete"):
    st.switch_page("pages/complete.py")

if st.button("Complete Revenge"):
    st.switch_page("pages/complete_rev.py")