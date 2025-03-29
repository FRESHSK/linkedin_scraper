import asyncio
from playwright.async_api import async_playwright
import time

async def scrape_profiles(li_at, search_link, max_results):
    results = []
    scraped = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
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

        # Visite LinkedIn Feed pour authentifier le cookie
        await page.goto("https://www.linkedin.com/feed/", timeout=180000, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)

        await page.goto(search_link, timeout=180000, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)

        while scraped < max_results:
            # Scroll pour charger plus de profils
            for _ in range(3):
                await page.mouse.wheel(0, 10000)
                await asyncio.sleep(2)

            profiles = await page.query_selector_all('.reusable-search__entity-result-list > li')

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

                    current_company = await page.evaluate("""(span) => {
                        if (span && span.nextSibling) {
                            return span.nextSibling.textContent.trim();
                        }
                        return '';
                    }""", span_el) if span_el else ""

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
                    print(f"Error extracting profile: {e}")

            try:
                next_button = await page.query_selector('//button[@aria-label="Suivant"]')
                if next_button:
                    await next_button.scroll_into_view_if_needed()
                    await asyncio.sleep(1)
                    await next_button.click()
                    await asyncio.sleep(5)
                else:
                    break
            except:
                break

        await browser.close()

    return results
