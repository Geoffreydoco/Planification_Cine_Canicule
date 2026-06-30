import time
import json
import os
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

CINEMA_IDS = {
    "Pathé Bellecour":   "P0012",
    "Lumière Terreaux":  "P0017",
    "Lumière Fourmi":    "W6903",
    "Lumière Bellecour": "P0015",
    "Le Cinéma":         "P0009",
    "Cinéma Opéra":      "P0006",
    "Le Zola":           "P0014",
    "UGC Part-Dieu":     "P0036",
    "Institut Lumière":  "P0050",
}

# French abbreviated month names as they appear on AlloCiné calendar
_FR_MONTHS = {
    "janv.": 1, "janv": 1, "jan.": 1, "jan": 1,
    "févr.": 2, "févr": 2, "fév.": 2, "fév": 2,
    "mars":  3, "mars.": 3,
    "avr.":  4, "avr": 4,
    "mai":   5, "mai.": 5,
    "juin":  6, "juin.": 6,
    "juil.": 7, "juil": 7,
    "août":  8, "août.": 8, "aout": 8,
    "sept.": 9, "sept": 9,
    "oct.":  10, "oct": 10,
    "nov.":  11, "nov": 11,
    "déc.":  12, "déc": 12, "dec.": 12, "dec": 12,
}


def _make_driver():
    """Create a headless Chrome WebDriver instance."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )


def _parse_sessions(html, cinema_name, date_str):
    """Parse AlloCiné showtime HTML and return a list of session dicts.

    Pure function — no browser interaction, no side effects.
    Takes raw HTML string (from driver.page_source after date navigation),
    cinema_name and date_str ("YYYY-MM-DD"), returns:
        [{"cinema": str, "film": str, "date": str,
          "heure": str, "version": str, "temperature": None}, ...]
    """
    soup = BeautifulSoup(html, "html.parser")
    sessions = []

    for card in soup.select(".card.entity-card"):
        title_tag = card.select_one("h2")
        if not title_tag:
            continue
        film_title = title_tag.text.strip()

        for version_block in card.select(".showtimes-version"):
            text_div = version_block.select_one("div.text")
            if text_div:
                raw = text_div.text.strip()
                if " -" in raw:
                    version_label = raw.split(" -", 1)[1].strip()
                else:
                    version_label = raw.strip()
                version = (
                    version_label.replace("En ", "").strip()
                    if version_label.startswith("En ")
                    else version_label
                )
            else:
                version = "VF"

            for hour_tag in version_block.select(".showtimes-hour-item-value"):
                heure = hour_tag.text.strip()
                if not heure:
                    continue
                sessions.append({
                    "cinema": cinema_name,
                    "film": film_title,
                    "date": date_str,
                    "heure": heure,
                    "version": version,
                    "temperature": None,
                })

    return sessions


def _find_date_span(driver, date_str):
    """Find the calendar span element for the given date_str ("YYYY-MM-DD").

    Returns the WebElement if found and not disabled, else None.
    The AlloCiné calendar shows ~28 days from today, each as:
        <span class="calendar-date-link roller-item [current] [disabled]">
          <div class="day">mer.</div>
          <div class="num">1</div>
          <div class="month">juil.</div>
        </span>
    """
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    spans = driver.find_elements(By.CSS_SELECTOR, "span.calendar-date-link.roller-item")
    for span in spans:
        cls = span.get_attribute("class") or ""
        if "disabled" in cls:
            continue

        try:
            num_el = span.find_element(By.CSS_SELECTOR, "div.num")
            month_el = span.find_element(By.CSS_SELECTOR, "div.month")
        except Exception:
            continue

        day_num_text = num_el.text.strip()
        month_text = month_el.text.strip().lower()

        try:
            day_num = int(day_num_text)
        except ValueError:
            continue

        month_num = _FR_MONTHS.get(month_text)
        if month_num is None:
            continue

        # Determine year: if target month < current month, it's next year
        # (unlikely for 3-week window, but handle gracefully)
        year = target_date.year

        if day_num == target_date.day and month_num == target_date.month:
            return span

    return None


def scrape_cinema_day(cinema_name, cinema_id, date_str, driver=None):
    """Scrape séances for one cinema on a specific date using Selenium.

    If driver is provided, reuses it (for efficiency in scrape_all).
    Otherwise creates a new headless Chrome instance (and closes it after).

    date_str format: "2026-07-01" (YYYY-MM-DD)

    Returns a list of session dicts:
        {"cinema": str, "film": str, "date": str,
         "heure": str, "version": str, "temperature": None}
    Returns [] if the cinema is closed on that date or on error.
    """
    own_driver = driver is None
    if own_driver:
        driver = _make_driver()

    try:
        url = f"https://www.allocine.fr/seance/salle_gen_csalle={cinema_id}.html"
        driver.get(url)

        # Wait for the calendar to appear (proves JS has rendered)
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "span.calendar-date-link.roller-item")
                )
            )
        except Exception:
            # No calendar → page failed to load
            return []

        # Check if this is today (the default view) — no click needed
        today_str = datetime.now().strftime("%Y-%m-%d")
        if date_str == today_str:
            # Just wait for sessions to appear
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".card.entity-card"))
                )
            except Exception:
                pass
            return _parse_sessions(driver.page_source, cinema_name, date_str)

        # Find and click the target date
        span = _find_date_span(driver, date_str)
        if span is None:
            # Date not available (cinema closed or beyond the calendar range)
            return []

        driver.execute_script("arguments[0].click();", span)

        # Wait for sessions to refresh after date click.
        # Strategy: wait until the clicked span has the 'current' class
        try:
            WebDriverWait(driver, 10).until(
                lambda d: "current" in (span.get_attribute("class") or "")
            )
        except Exception:
            # Fallback: brief pause
            time.sleep(2)

        # Small extra pause to let session cards render
        time.sleep(1)

        return _parse_sessions(driver.page_source, cinema_name, date_str)

    except Exception:
        return []

    finally:
        if own_driver:
            driver.quit()


def scrape_all(progress_callback=None):
    """Scrape all 9 cinemas for 21 days (3 weeks) using a single Selenium browser.

    progress_callback(current, total, cinema_name) is called before each
    cinema/date combination.

    Returns a flat list of session dicts (without temperatures).
    """
    today = datetime.now().date()
    dates = [(today + timedelta(days=i)).isoformat() for i in range(21)]

    total = len(CINEMA_IDS) * len(dates)
    current = 0
    sessions = []

    driver = _make_driver()
    try:
        for cinema_name, cinema_id in CINEMA_IDS.items():
            for date_str in dates:
                current += 1
                if progress_callback:
                    progress_callback(current, total, cinema_name)
                day_sessions = scrape_cinema_day(
                    cinema_name, cinema_id, date_str, driver=driver
                )
                sessions.extend(day_sessions)
    finally:
        driver.quit()

    return sessions
