from json import loads

from bs4 import BeautifulSoup
from fastapi import HTTPException
from playwright._impl._api_structures import SetCookieParam
from playwright.async_api import async_playwright, Page
from requests import get
from playwright.async_api import TimeoutError
from html import unescape

from app.models import Song
from app.utils import log

async def get_chord_data(link: str):
    pass

async def get_tab_data(link: str):
    pass

async def log_in(context, username: str, password: str) -> Page:
    page = await context.new_page()
    await page.goto('https://www.ultimate-guitar.com/')
    # log_in = await page.locator("text=Log in").first.text_content()
    # log.debug("found: %s", log_in)

    await page.click("text=i do not accept")
    await page.click("text=log in")

    await page.fill('input[name="username"]', username)
    await page.fill('input[name="password"]', password)

    await (await page.locator("text=LOG IN").all())[2].click()
    return page

async def get_song_data(login_data) -> tuple[list[Song], list[tuple[int, str, str]], list[tuple[int, str, bool, str]]]:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        with open("cookies.json", "r") as file:
            cookies = loads(file.read())
        await context.add_cookies(
            [
                SetCookieParam(
                    name=k,
                    value=v,
                    domain="www.ultimate-guitar.com" if k in ("_csrf", "g_state", "static_cache_key_v2") else ".ultimate-guitar.com",
                    path="/courses" if k in ("appUtmCampaign",) else "/"
                )
                for k, v in cookies.items()
            ]
        )

        #page = await log_in(context, login_data.username, login_data.password)
        page = await context.new_page()
        await page.goto('https://www.ultimate-guitar.com/')
        await page.click("text=i do not accept")

        try:
            await page.click("text=my tabs")
        except TimeoutError:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # If there is the per page text, click on the ALL button
        per_page = page.locator("text=per page")
        try:
            await per_page.wait_for(state="attached", timeout=10000)
            log.debug("Per page found")
            await per_page.scroll_into_view_if_needed()
            await per_page.locator("xpath=.. >> text=ALL").click()

        except TimeoutError:
            log.debug("Per page not found")

        songs: list[Song] = []
        chords: list[tuple[int, str, str]] = [] # version, url, song title
        tabs: list[tuple[int, str, bool, str]] = [] # version, url, bass, song title
        rows = BeautifulSoup(await page.content(), "html.parser").article.div.find_all("div", recursive=False)[1:]
        for row in rows:
            info = row.find_all("a")
            match len(info):
                case 1:
                    inner_texts = [el.get_text(strip=True) for el in info]

                    split_title = inner_texts[0].split(" (ver ")
                    artist = songs[-1].artist

                    url = info[0]["href"]
                case 2:
                    inner_texts = [el.get_text(strip=True) for el in info]

                    split_title = inner_texts[1].split(" (ver ")
                    artist = inner_texts[0]

                    url = info[1]["href"]
                case _:
                    log.warning("Unexpected number of elements in row: %s", info)
                    continue


            version = split_title[1][0] if len(split_title) > 1 else 1
            title = split_title[0]

            log.debug("%s - %s", artist, title)
            log.debug("link: %s", url)
            new_song = Song(artist=artist, title=title)

            if not new_song.title in [song.title for song in songs]:
                songs.append(new_song)

            current_song = next(filter(lambda song: song.title == new_song.title, songs))

            div_texts = [div.get_text() for div in row.find_all("div")]
            if "Chords" in div_texts:
                chords.append((version, url, current_song.title))
            elif "Bass" in div_texts:
                tabs.append((version, url, True, current_song.title))
            else:
                tabs.append((version, url, False, current_song.title))

        await browser.close()
        return songs, chords, tabs

def get_content(url: str):
    soup = BeautifulSoup(get(url).content, "html.parser")
    #log.debug(soup)
    try:
        content = unescape(str(soup.find("div", {"class": "js-store"})).split("&quot;content&quot;:&quot;")[1].split("&quot;,&quot;revision_id")[0])
    except IndexError:
        raise HTTPException(status_code=401, detail="Probably need to solve captcha")
    return content
