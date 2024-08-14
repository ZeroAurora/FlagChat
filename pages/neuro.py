from datetime import datetime
import json

from jinja2 import Environment, FileSystemLoader
import streamlit as st
from sqlalchemy import insert, select, func
from openai import OpenAI

from schemas import messages
from utils.flag import get_flag

if "id" not in st.session_state:
    st.session_state.next_page = "pages/neuro.py"
    st.switch_page("pages/login.py")

openai = OpenAI(api_key=st.secrets.openai.api_key, base_url=st.secrets.openai.base_url)
conn = st.connection("db", type="sql")


@st.cache_resource
def jinja_env():
    return Environment(loader=FileSystemLoader("prompts/neuro"))


def make_prompt_chain(messages: list[dict], **kwargs):
    """Take a list of messages, prepend rendered system and user_prepend, and return a list of messages"""
    env = jinja_env()
    system = env.get_template("system.md.jinja").render(**kwargs)
    user_prepend = env.get_template("user_prepend.md.jinja").render(**kwargs)

    prepend = []
    if system:
        prepend.append({"role": "system", "content": system})
    if user_prepend:
        prepend.append({"role": "user", "content": user_prepend})
    return prepend + messages


# def guard():
#     pass


def reset_messages():
    st.session_state.messages = []
    st.session_state.filtered = False
    st.session_state.ended = False


def get_timeout_type(user_id: int):
    # allow 2 messages every minute
    # if there is a filtered message in the last hour, disallow sending more
    with conn.session as s:
        res = s.execute(
            select(func.count())
            .select_from(messages)
            .where(messages.c.user_id == user_id)
            .where(messages.c.is_filtered == True)
            .where(messages.c.timestamp > datetime.now().timestamp() - 3600)
        )
        if res.scalar() > 0:
            return "FILTERED"
        res = s.execute(
            select(func.count())
            .select_from(messages)
            .where(messages.c.user_id == user_id)
            .where(messages.c.timestamp > datetime.now().timestamp() - 60)
        )
        if res.scalar() >= 2:
            return "RATELIMIT"
        return "OK"


def log_message(user_id: int, msgs: str, is_filtered: bool):
    with conn.session as s:
        s.execute(
            insert(messages).values(
                user_id=user_id,
                timestamp=datetime.now().timestamp(),
                messages=msgs,
                type="neuro",
                is_filtered=is_filtered,
            )
        )
        s.commit()


def run_chat_complete():
    prompt = make_prompt_chain(
        st.session_state.messages, flag=get_flag(st.session_state.id, "neuro")
    )
    response = openai.chat.completions.create(
        messages=prompt, model=st.secrets.openai.model, temperature=0.1, max_tokens=500
    )

    resp_content = response.choices[0].message.content
    finish_reason = response.choices[0].finish_reason

    # guard later
    return resp_content, finish_reason


def render_completion(resp_content, finish_reason):
    if finish_reason != "content_filter":
        st.session_state.messages.append({"role": "assistant", "content": resp_content})
        with st.chat_message("assistant"):
            st.markdown(resp_content)
        if len(st.session_state.messages) > 10:
            st.session_state.ended = True
            with st.chat_message("system", avatar="🐢"):
                st.markdown("消息过多，请重新开始。")
    else:
        st.session_state.ended = True
        st.session_state.filtered = True
        with st.chat_message("system", avatar="🐢"):
            st.markdown("您的消息被过滤了，接下来一小时您将无法发送消息。")


# ----------

if "messages" not in st.session_state or "filtered" not in st.session_state:
    reset_messages()

if st.button("重置消息"):
    reset_messages()

timeout_type = get_timeout_type(st.session_state.id)
is_in_timeout = timeout_type != "OK"

# this might not be refreshed so further investigation is needed
st.button(f"用户 ID: {st.session_state.id} 当前状态: {timeout_type} 点击以重载")

with st.chat_message("system", avatar="🐢"):
    st.markdown(jinja_env().get_template("intro.md.jinja").render())

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input(
    "每分钟最多发送 2 条消息，如果消息触发上游过滤，则一小时之内无法发送消息。",
    disabled=is_in_timeout or st.session_state.ended,
):
    if is_in_timeout or st.session_state.ended:
        with st.chat_message("system", avatar="🐢"):
            st.markdown("当前无法发送消息。点击上面的重载按钮来刷新状态。")

    elif len(prompt) < 50:
        prompt = "Chat: " + prompt
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        resp_content, finish_reason = run_chat_complete()
        render_completion(resp_content, finish_reason)
        log_message(
            st.session_state.id,
            json.dumps(st.session_state.messages, ensure_ascii=False),
            st.session_state.filtered,
        )

    else:
        with st.chat_message("system", avatar="🐢"):
            st.markdown("消息过长，请重新发送。")
