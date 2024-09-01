from string import printable
import json

import streamlit as st
from openai import OpenAI

from utils.database import get_timeout_type, log_message
from utils.flag import get_flag
from utils.template import jinja_env

openai = OpenAI(api_key=st.secrets.openai.api_key, base_url=st.secrets.openai.base_url)


def get_prefix(flag: str):
    env = jinja_env("complete_rev")
    return env.get_template("prompt_prefix.md.jinja").render(flag=flag)


def make_prompt(user_input: str):
    prefix = get_prefix(
        flag=get_flag(user_id=st.session_state.id, problem="complete_rev")
    )
    return f"{prefix}\n\n{user_input}"


def run_completion(user_input: str):
    response = openai.completions.create(
        model=st.secrets.openai.completion_model,
        prompt=make_prompt(user_input),
        max_tokens=10,
        temperature=0.1,
    )

    resp_content = response.choices[0].text
    finish_reason = response.choices[0].finish_reason

    return resp_content, finish_reason


def prefilter(user_input: str):
    return any([c in printable for c in user_input]) or len(user_input) > 20

def postfilter(resp_content: str):
    return any([c in printable for c in resp_content])


def render_completion(resp_content, finish_reason):
    if finish_reason == "content_filter":
        st.error("您的消息被过滤了，接下来一小时您将无法发送消息。")
    elif postfilter(resp_content):
        st.error("输出限制：禁止包含 ASCII Printable。请重新发送。")
    else:
        st.markdown(resp_content)


# ----------


if "id" not in st.session_state:
    st.session_state.next_page = "pages/complete_rev.py"
    st.switch_page("pages/login.py")

timeout_type = get_timeout_type(st.session_state.id, msgs_per_min=10)
is_in_timeout = timeout_type != "OK"

# this might not be refreshed, so double check on input
st.button(f"用户 ID: {st.session_state.id} 当前状态: {timeout_type} 点击以重载")

with st.expander("阅读 Prompt 前缀"):
    st.markdown(get_prefix(flag="fake_flag{try_to_find_me}"))

with st.form("form"):
    user_input = st.text_area(
        "输入 Prompt 后继，这部分内容将直接与前缀拼接"
    )
    submit = st.form_submit_button("提交")

if submit:
    if prefilter(user_input):
        st.error("输入限制：禁止包含 ASCII Printable，最多 20 个 Unicode 字符。请重新发送。")
    elif not is_in_timeout:
        resp_content, finish_reason = run_completion(user_input)
        render_completion(resp_content, finish_reason)
        log_message(
            user_id=st.session_state.id,
            type="complete_rev",
            msgs=json.dumps({"prompt": user_input, "response": resp_content}, ensure_ascii=False),
            is_filtered=finish_reason == "content_filter",
        )
    else:
        st.error(f"您处于 {timeout_type} 状态，无法发送消息。")
