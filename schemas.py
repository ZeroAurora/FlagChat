from sqlalchemy import Boolean, Column, Float, Integer, MetaData, String, Table

metadata_obj = MetaData()

users = Table(
    "users",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("username", String),
    Column("last_login", Float),
)

messages = Table(
    "messages",
    metadata_obj,
    Column("user_id", Integer),
    Column("timestamp", Float),
    Column("messages", String),
    Column("type", String),
    Column("is_filtered", Boolean),
)
