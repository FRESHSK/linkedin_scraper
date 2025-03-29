import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)


async def scrape_profiles(li_at, search_link, max_results):
    results = []
    scraped = 0

    async with async_playwright() as p:
        logging.info("🚀 Lancement de Chromium headless...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            storage_state={
                "cookies": [
                    {
                        "name": "li_at",
                        "value": li_at,
                        "domain": ".linkedin.com",
                        "path": "/",
                        "httpOnly": True,
                        "secure": True,
                        "sameSite": "None"
                    }
                ],
                "origins": []
            }
        )

        page = await context.new_page()

        # 🔁 Ne PAS visiter /feed sur Render
        # logging.info("🔐 Accès au feed pour valider l'authentification...")
        # await page.goto("https://www.linkedin.com/feed/", timeout=60000)
        # await page.wait_for_timeout(4000)

        logging.info("🔍 Accès à la recherche LinkedIn...")
        await page.goto(search_link, timeout=90000)
        await page.wait_for_timeout(5000)

        while scraped < max_results:
            logging.info(f"🔄 Scrolling... ({scraped}/{max_results})")
            for _ in range(3):
                await page.keyboard.press("End")
                await asyncio.sleep(2)

            profiles = await page.query_selector_all('.search-results-container .list-style-none li')

            if not profiles:
                break

            for profile in profiles:
                if scraped >= max_results:
                    break

                try:
                    link_el = await profile.query_selector('a[data-test-app-aware-link]')
                    name_el = await profile.query_selector('a span[aria-hidden="true"]')
                    job_el = await profile.query_selector('div.t-14.t-black.t-normal')
                    loc_el = await profile.query_selector('div.t-14.t-normal:not(.t-black)')
                    span_el = await profile.query_selector('p.entity-result__summary--2-lines > span.white-space-pre:nth-of-type(2)')

                    profil_link = await link_el.get_attribute('href') if link_el else ""
                    profil_name = await name_el.inner_text() if name_el else ""
                    profil_job = await job_el.inner_text() if job_el else ""
                    profil_local = await loc_el.inner_text() if loc_el else ""

                    current_company = await page.evaluate("""
                        (span) => {
                            if (span && span.nextSibling) {
                                return span.nextSibling.textContent.trim();
                            }
                            return '';
                        }
                    """, span_el) if span_el else ""

                    results.append({
                        "Name": profil_name,
                        "Job": profil_job,
                        "Company": current_company,
                        "Link": profil_link,
                        "Location": profil_local
                    })

                    scraped += 1
                    await asyncio.sleep(1)

                except Exception as e:
                    logging.warning(f"Erreur d'extraction : {e}")

            try:
                next_button = await page.query_selector('//button[@aria-label="Suivant"]')
                if next_button:
                    await next_button.scroll_into_view_if_needed()
                    await asyncio.sleep(1)
                    await next_button.click()
                    await asyncio.sleep(4)
                else:
                    break
            except:
                break

        await browser.close()
        logging.info("✅ Extraction terminée.")

    return results
