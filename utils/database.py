from datetime import datetime

import streamlit as st
from sqlalchemy import func, insert, select

from schemas import messages

conn = st.connection("db", type="sql")

def get_timeout_type(user_id: int, msgs_per_min: int = 2):
    # some backdoor for testing
    if user_id == 0:
        return "OK"
    
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
        if res.scalar() >= msgs_per_min:
            return "RATELIMIT"
        return "OK"
    
def log_message(user_id: int, type: str, msgs: str, is_filtered: bool):
    with conn.session as s:
        s.execute(
            insert(messages).values(
                user_id=user_id,
                timestamp=datetime.now().timestamp(),
                messages=msgs,
                type=type,
                is_filtered=is_filtered,
            )
        )
        s.commit()
