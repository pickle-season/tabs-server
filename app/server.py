from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session, select

from app.models import Song, Chords, Tab
from app.utils import log, LoginData
from app.scraping import get_song_data, get_content


class TabsServer:
    def __init__(self):
        sqlite_file_name = "database.db"
        sqlite_url = f"sqlite:///{sqlite_file_name}"

        connect_args = {"check_same_thread": False}

        self.engine = create_engine(sqlite_url, connect_args=connect_args)

        self.create_db_and_tables()

    def create_db_and_tables(self):
        # TODO: For debug
        SQLModel.metadata.drop_all(self.engine)

        SQLModel.metadata.create_all(self.engine)

    def _download(self):
        chord_path = Path("./tabs_chords/chords")
        tabs_path = Path("./tabs_chords/tabs")

        chord_path.mkdir(parents=True, exist_ok=True)
        tabs_path.mkdir(parents=True, exist_ok=True)

        with self.session() as session:
            import ast
            for chord in session.exec(select(Chords)).all():
                log.info("downloading: %s", chord.url)

                content = get_content(chord.url)
                text = ast.literal_eval(f'"{content}"')

                with (chord_path / f"{chord.song.title}-{chord.version}.txt").open(mode="w") as f:
                    f.write(text)

            for tab in session.exec(select(Tab)).all():
                log.info("downloading: %s", tab.url)

                content = get_content(tab.url)
                text = ast.literal_eval(f'"{content}"')

                with (tabs_path / f"{tab.song.title}-{tab.version}.txt").open(mode="w") as f:
                    f.write(text)


    @contextmanager
    def session(self):
        with Session(self.engine) as session:
            yield session

    def clean_db(self):
        with self.session() as session:
            # Delete everything
            for db_tab in session.exec(select(Tab)).all():
                session.delete(db_tab)
            for db_chords in session.exec(select(Chords)).all():
                session.delete(db_chords)
            for db_song in session.exec(select(Song)).all():
                session.delete(db_song)

            # Refresh all
            for db_song in session.exec(select(Song)).all():
                session.refresh(db_song)
            for db_chords in session.exec(select(Chords)).all():
                session.refresh(db_chords)
            for db_tab in session.exec(select(Tab)).all():
                session.refresh(db_tab)

            session.commit()

    # TODO: refactor into separate functions for db update, refresh, extract song, chord, tab info, etc
    async def update_songs(self, login_data: LoginData) -> None:
        log.info("Getting songs")

        songs, chords, tabs = await get_song_data(login_data)

        self.clean_db()

        with self.session() as session:
            session.add_all(songs)
            for db_song in session.exec(select(Song)).all():
                session.refresh(db_song)

            for new_chords in chords:
                session.add(
                    Chords(
                        version=new_chords[0],
                        url=new_chords[1],
                        song_id=next(filter(lambda song: song.title == new_chords[2], songs)).id
                    )
                )
            for new_tab in tabs:
                session.add(
                    Tab(
                        version=new_tab[0],
                        url=new_tab[1],
                        bass=new_tab[2],
                        song_id=next(filter(lambda song: song.title == new_tab[3], songs)).id
                    )
                )

            session.commit()

    def get_songs(self):
        with self.session() as session:
            return [
                {
                    "id": song.id,
                    "artist": song.artist,
                    "title": song.title,
                    "chords": song.chords,
                    "tabs": song.tabs
                }
                for song in list(session.exec(select(Song)).all())
            ]


    def get_chords(self, chords_id: int):
        with self.session() as session:
            url = session.get(Chords, chords_id).url

        return {"content": get_content(url)}

    def get_tab(self, tab_id: int):
        with self.session() as session:
            url = session.get(Tab, tab_id).url

        return {"content": get_content(url)}


