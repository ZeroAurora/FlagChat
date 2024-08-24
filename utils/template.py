import streamlit as st
from jinja2 import Environment, FileSystemLoader


@st.cache_resource
def jinja_env(problem: str):
    return Environment(loader=FileSystemLoader(f"prompts/{problem}"))


def make_prompt_chain(problem: str, messages: list[dict], **kwargs):
    """Take a list of messages, prepend rendered system and user_prepend, and return a list of messages"""
    env = jinja_env(problem)
    system = env.get_template("system.md.jinja").render(**kwargs)
    user_prepend = env.get_template("user_prepend.md.jinja").render(**kwargs)

    prepend = []
    if system:
        prepend.append({"role": "system", "content": system})
    if user_prepend:
        prepend.append({"role": "user", "content": user_prepend})
    return prepend + messages
