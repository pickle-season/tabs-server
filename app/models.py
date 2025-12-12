from sqlmodel import Field, Session, SQLModel, create_engine, select

class Song(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    title: str = Field(sa_column_kwargs={"unique": True})
    artist: str = Field(default="")
