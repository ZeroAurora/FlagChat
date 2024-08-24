from datetime import datetime

import requests as rq
import streamlit as st
from sqlalchemy.dialects.sqlite import insert

from schemas import users

conn = st.connection("db", type="sql")

if "next_page" not in st.session_state:
    st.session_state.next_page = "app.py"


def verify_with_ret2shell(code: str) -> dict | None:
    r2s_url = st.secrets.ret2shell_url
    int_code = int(code, 16)
    query = rq.get(f"{r2s_url}/api/account/query", params={"code": int_code})
    if query.status_code == 200:
        return query.json()
    return None


def create_or_update_user(user: dict):
    with conn.session as s:
        s.execute(
            insert(users)
            .values(
                id=user["id"],
                username=user["account"],
                last_login=datetime.now().timestamp(),
            )
            .on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "last_login": datetime.now().timestamp(),
                },
            )
        )
        s.commit()


def login(user: dict):
    if user:
        st.session_state.id = user["id"]
        create_or_update_user(user)
        st.switch_page(st.session_state.next_page)
    else:
        st.error("登录失败，请检查用户识别码是否正确！")


if st.secrets.debug:
    login({"id": 0, "account": "test"})

st.title("Login with Ret2Shell")
code = st.text_input("请输入你的临时用户识别码：")

if st.button("登录"):
    user = verify_with_ret2shell(code)
    login(user)
