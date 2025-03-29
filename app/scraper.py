import asyncio
from playwright.async_api import async_playwright

async def scrape_profiles(li_at, search_link, max_results=5):
    results = []
    scraped = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )

        context = await browser.new_context(
            storage_state={
                "cookies": [{
                    "name": "li_at",
                    "value": li_at,
                    "domain": ".linkedin.com",
                    "path": "/",
                    "httpOnly": True,
                    "secure": True,
                    "sameSite": "None"
                }],
                "origins": []
            }
        )

        page = await context.new_page()

        try:
            await page.goto("https://www.linkedin.com/feed/", timeout=60000)
            await page.wait_for_timeout(4000)
            await page.goto(search_link, timeout=60000)
            await page.wait_for_timeout(4000)
        except Exception as e:
            await browser.close()
            raise Exception(f"Page.goto error: {str(e)}")

        while scraped < max_results:
            for _ in range(3):
                await page.keyboard.press("End")
                await asyncio.sleep(1.5)

            profiles = await page.query_selector_all('.reusable-search__entity-result-list li')

            if not profiles:
                break

            for profile in profiles:
                if scraped >= max_results:
                    break

                try:
                    link_el = await profile.query_selector('a[data-test-app-aware-link]')
                    name_el = await profile.query_selector('span[aria-hidden="true"]')
                    job_el = await profile.query_selector('div.entity-result__primary-subtitle')
                    loc_el = await profile.query_selector('div.entity-result__secondary-subtitle')
                    
                    profil_link = await link_el.get_attribute('href') if link_el else ""
                    profil_name = await name_el.inner_text() if name_el else ""
                    profil_job = await job_el.inner_text() if job_el else ""
                    profil_local = await loc_el.inner_text() if loc_el else ""

                    results.append({
                        "Name": profil_name,
                        "Job": profil_job,
                        "Link": profil_link,
                        "Location": profil_local
                    })

                    scraped += 1
                    await asyncio.sleep(1)

                except Exception as e:
                    print(f"⚠️ Error parsing profile: {e}")

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
    return results
