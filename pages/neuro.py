import json

import streamlit as st
from openai import OpenAI

from utils.database import get_timeout_type, log_message
from utils.flag import get_flag
from utils.template import jinja_env, make_prompt_chain

openai = OpenAI(api_key=st.secrets.openai.api_key, base_url=st.secrets.openai.base_url)


def reset_messages():
    st.session_state.messages = []
    st.session_state.filtered = False
    st.session_state.ended = False


def run_chat_complete():
    prompt = make_prompt_chain(
        "neuro", st.session_state.messages, flag=get_flag(st.session_state.id, "neuro")
    )
    response = openai.chat.completions.create(
        messages=prompt, model=st.secrets.openai.model, temperature=0.1, max_tokens=500
    )

    resp_content = response.choices[0].message.content
    finish_reason = response.choices[0].finish_reason

    return resp_content, finish_reason


def render_completion(resp_content, finish_reason):
    if finish_reason != "content_filter":
        st.session_state.messages.append({"role": "assistant", "content": resp_content})
        with st.chat_message("assistant"):
            st.markdown(resp_content)
        if len(st.session_state.messages) >= 10:
            st.session_state.ended = True
            with st.chat_message("system", avatar="🐢"):
                st.markdown("消息过多（至多 5 轮对话），请点击“重置消息”重新开始。")
    else:
        st.session_state.ended = True
        st.session_state.filtered = True
        with st.chat_message("system", avatar="🐢"):
            st.markdown("您的消息被过滤了，接下来一小时您将无法发送消息。")


# ----------

if "id" not in st.session_state:
    st.session_state.next_page = "pages/neuro.py"
    st.switch_page("pages/login.py")

if "messages" not in st.session_state or "filtered" not in st.session_state:
    reset_messages()

if st.button("重置消息"):
    reset_messages()

timeout_type = get_timeout_type(st.session_state.id)
is_in_timeout = timeout_type != "OK"

# this might not be refreshed, so double check on input
st.button(f"用户 ID: {st.session_state.id} 当前状态: {timeout_type} 点击以重载")

with st.chat_message("system", avatar="🐢"):
    st.markdown(jinja_env("neuro").get_template("intro.md.jinja").render())

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input(
    "每分钟最多发送 2 条消息，如果消息触发上游过滤，则一小时之内无法发送消息。",
    disabled=is_in_timeout or st.session_state.ended,
):
    if is_in_timeout or st.session_state.ended:
        with st.chat_message("system", avatar="🐢"):
            st.markdown(f"当前无法发送消息（{timeout_type}）。点击上面的重载按钮来刷新状态。")

    elif len(prompt) <= 50:
        prompt = "Chat: " + prompt
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        resp_content, finish_reason = run_chat_complete()
        render_completion(resp_content, finish_reason)
        log_message(
            user_id=st.session_state.id,
            type="neuro",
            msgs=json.dumps(st.session_state.messages, ensure_ascii=False),
            is_filtered=st.session_state.filtered,
        )

    else:
        with st.chat_message("system", avatar="🐢"):
            st.markdown("消息过长，请重新发送。（最多 50 字）")
