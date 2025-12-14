from sqlmodel import Field, SQLModel, Relationship


class Song(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    title: str = Field(sa_column_kwargs={"unique": True})
    artist: str

    chords: list["Chords"] = Relationship(back_populates="song")
    tabs: list["Tab"] = Relationship(back_populates="song")

class Chords(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    version: int
    url: str

    song_id: int = Field(foreign_key="song.id")
    song: Song = Relationship(back_populates="chords")

class Tab(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    version: int
    url: str
    bass: bool

    song_id: int = Field(foreign_key="song.id")
    song: Song = Relationship(back_populates="tabs")
