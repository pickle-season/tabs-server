from asyncio import sleep
from contextlib import contextmanager

from playwright.async_api import async_playwright, TimeoutError

from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session, select

from app.models import Song
from app.utils import log, LoginData


class TabsServer:
    def __init__(self):
        sqlite_file_name = "database.db"
        sqlite_url = f"sqlite:///{sqlite_file_name}"

        connect_args = {"check_same_thread": False}

        self.engine = create_engine(sqlite_url, connect_args=connect_args)

        self.create_db_and_tables()

    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)

    @contextmanager
    def session(self):
        with Session(self.engine) as session:
            yield session

    async def update_songs(self, login_data: LoginData) -> None:
        log.info("Getting songs")

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto('https://www.ultimate-guitar.com/')
            #log_in = await page.locator("text=Log in").first.text_content()
            #log.debug("found: %s", log_in)

            await page.click("text=i do not accept")
            await page.click("text=log in")

            await page.fill('input[name="username"]', login_data.username)
            await page.fill('input[name="password"]', login_data.password)

            await (await page.locator("text=LOG IN").all())[2].click()

            await page.click("text=my tabs")

            # If there is the per page text, click on all button
            per_page = page.locator("text=per page")
            try:
                await per_page.wait_for(state="attached", timeout=10000)
                log.debug("Per page found")
                await per_page.scroll_into_view_if_needed()
                await per_page.locator("xpath=.. >> text=ALL").click()

            except TimeoutError:
                log.debug("Per page not found")

            # TODO: extract song table

            await sleep(10)

            await browser.close()

        with self.session() as session:
            new_song = Song(title="test_title", artist="test_artist")

            session.add(new_song)
            session.commit()
            session.refresh(new_song)

    def get_songs(self) -> list[Song]:
        with self.session() as session:
            return list(session.exec(select(Song)).all())
