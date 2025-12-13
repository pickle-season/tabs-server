from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from requests import get

from app.models import Song
from app.utils import log

async def get_chord_data(link: str):
    pass
async def get_tab_data(link: str):
    pass

async def get_song_data(login_data) -> tuple[list[Song], list[tuple[int, str, str]], list[tuple[int, str, str]]]:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
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

        # If there is the per page text, click on the ALL button
        per_page = page.locator("text=per page")
        try:
            await per_page.wait_for(state="attached", timeout=10000)
            log.debug("Per page found")
            await per_page.scroll_into_view_if_needed()
            await per_page.locator("xpath=.. >> text=ALL").click()

        except TimeoutError:
            log.debug("Per page not found")

        # TODO: Maybe redo with beautifulsoup?
        # Only extract the raw html from playwright, and use bs4 to find elements
        songs: list[Song] = []
        chords: list[tuple[int, str, str]] = []
        tabs: list[tuple[int, str, str]] = []
        rows = (await page.locator("article").first.locator("div").first.locator(":scope > div").all())[1:]
        for row in rows:
            info = row.locator("a")
            match await info.count():
                case 1:
                    inner_texts = await info.all_inner_texts()
                    split_title = inner_texts[0].split(" (ver ")
                    artist = songs[-1].artist

                    link = await info.first.get_attribute("href")
                case 2:
                    inner_texts = await info.all_inner_texts()
                    split_title = inner_texts[1].split(" (ver ")
                    artist = inner_texts[0]

                    link = await (await info.all())[1].get_attribute("href")
                case _:
                    log.warning("Unexpected number of elements in row: %s", info)
                    continue


            version = split_title[1][0] if len(split_title) > 1 else 1
            title = split_title[0]

            log.debug("%s - %s", artist, title)
            log.debug("link: %s", link)
            new_song = Song(artist=artist, title=title)

            if not new_song.title in [song.title for song in songs]:
                songs.append(new_song)

            current_song = next(filter(lambda song: song.title == new_song.title, songs))

            if await row.locator("text=chords").count() > 0:
                chords.append((version, link, current_song.title))
            else:
                tabs.append((version, link, current_song.title))


        await browser.close()
        return songs, chords, tabs

def get_content(url: str):
    log.debug(url)

    soup = BeautifulSoup(get(url).content, "html.parser")
    content = str(soup.find("div", {"class": "js-store"})).split("&quot;content&quot;:&quot;")[1].split("&quot;,")[0]
    return content
