"""Tests pour scraper._parse_sessions, scrape_cinema_day et scrape_all.

Architecture post-Selenium :
- _parse_sessions(html, cinema_name, date_str) est la fonction pure testable.
- scrape_cinema_day wraps _parse_sessions + Selenium (driver mocké dans les tests).
- scrape_all crée un driver unique et itère sur cinémas × dates (driver mocké).
"""
from unittest.mock import patch, MagicMock, call
import pytest
import scraper
from scraper import _parse_sessions, scrape_cinema_day, scrape_all, CINEMA_IDS

# ---------------------------------------------------------------------------
# Minimal HTML that mirrors the real AlloCiné structure
# ---------------------------------------------------------------------------

SAMPLE_HTML = """
<html><body>

<!-- Film 1 : two version blocks (VF + VOST) -->
<div class="card entity-card entity-card-list movie-card-theater cf hred">
  <h2 class="meta-title">Inception</h2>
  <div class="showtimes-versions-holder">

    <div class="showtimes-version">
      <div class="text">30 juin 2026 -
                En VF</div>
      <div class="hours">
        <div class="showtimes-hour-block">
          <div class="showtimes-hour-item">
            <span class="showtimes-hour-item-value">10:30</span>
            <span class="showtimes-hour-item-booking">Réserver</span>
          </div>
        </div>
        <div class="showtimes-hour-block">
          <div class="showtimes-hour-item">
            <span class="showtimes-hour-item-value">14:00</span>
            <span class="showtimes-hour-item-booking">Réserver</span>
          </div>
        </div>
      </div>
    </div>

    <div class="showtimes-version">
      <div class="text">30 juin 2026 -
                En VOST</div>
      <div class="hours">
        <div class="showtimes-hour-block">
          <div class="showtimes-hour-item">
            <span class="showtimes-hour-item-value">20:00</span>
            <span class="showtimes-hour-item-booking">Réserver</span>
          </div>
        </div>
      </div>
    </div>

  </div>
</div>

<!-- Film 2 : one version block (VF only) -->
<div class="card entity-card entity-card-list movie-card-theater cf hred">
  <h2 class="meta-title">Dune</h2>
  <div class="showtimes-versions-holder">

    <div class="showtimes-version">
      <div class="text">30 juin 2026 -
                En VF</div>
      <div class="hours">
        <div class="showtimes-hour-block">
          <div class="showtimes-hour-item">
            <span class="showtimes-hour-item-value">16:15</span>
            <span class="showtimes-hour-item-booking">Réserver</span>
          </div>
        </div>
      </div>
    </div>

  </div>
</div>

</body></html>
"""

EMPTY_HTML = "<html><body></body></html>"


# ---------------------------------------------------------------------------
# Helper: build a mock Selenium WebDriver that returns SAMPLE_HTML
# ---------------------------------------------------------------------------

def _make_mock_driver(page_source=SAMPLE_HTML, has_calendar=True, has_sessions=True):
    """Return a MagicMock that behaves like a minimal Selenium WebDriver."""
    driver = MagicMock()
    driver.page_source = page_source

    # WebDriverWait(driver, N).until(...) — make it call the condition with driver
    # We do this by making find_elements return appropriate mocks
    if has_calendar:
        calendar_span = MagicMock()
        calendar_span.get_attribute.return_value = "calendar-date-link roller-item current"
        driver.find_elements.return_value = [calendar_span]
    else:
        driver.find_elements.return_value = []

    return driver


# ---------------------------------------------------------------------------
# Tests for _parse_sessions (pure parsing logic)
# ---------------------------------------------------------------------------

class TestParseSessions:
    """Tests de la fonction de parsing HTML pure."""

    def test_returns_list(self):
        result = _parse_sessions(SAMPLE_HTML, "Pathé Bellecour", "2026-06-30")
        assert isinstance(result, list)

    def test_correct_total_count(self):
        # Inception: 2 VF + 1 VOST = 3; Dune: 1 VF = 1 → total 4
        result = _parse_sessions(SAMPLE_HTML, "Pathé Bellecour", "2026-06-30")
        assert len(result) == 4

    def test_all_required_keys_present(self):
        result = _parse_sessions(SAMPLE_HTML, "Pathé Bellecour", "2026-06-30")
        required = {"cinema", "film", "date", "heure", "version", "temperature"}
        for session in result:
            assert required == set(session.keys()), f"Missing keys in {session}"

    def test_temperature_is_none(self):
        result = _parse_sessions(SAMPLE_HTML, "Pathé Bellecour", "2026-06-30")
        for session in result:
            assert session["temperature"] is None

    def test_cinema_name_correct(self):
        result = _parse_sessions(SAMPLE_HTML, "Pathé Bellecour", "2026-06-30")
        for session in result:
            assert session["cinema"] == "Pathé Bellecour"

    def test_date_correct(self):
        result = _parse_sessions(SAMPLE_HTML, "Pathé Bellecour", "2026-06-30")
        for session in result:
            assert session["date"] == "2026-06-30"

    def test_film_titles_extracted(self):
        result = _parse_sessions(SAMPLE_HTML, "Pathé Bellecour", "2026-06-30")
        films = {s["film"] for s in result}
        assert "Inception" in films
        assert "Dune" in films

    def test_vf_version_extracted(self):
        result = _parse_sessions(SAMPLE_HTML, "Pathé Bellecour", "2026-06-30")
        vf_sessions = [s for s in result if s["version"] == "VF"]
        assert len(vf_sessions) == 3  # 2 Inception VF + 1 Dune VF

    def test_vost_version_extracted(self):
        result = _parse_sessions(SAMPLE_HTML, "Pathé Bellecour", "2026-06-30")
        vost_sessions = [s for s in result if s["version"] == "VOST"]
        assert len(vost_sessions) == 1
        assert vost_sessions[0]["film"] == "Inception"
        assert vost_sessions[0]["heure"] == "20:00"

    def test_inception_vf_heures(self):
        result = _parse_sessions(SAMPLE_HTML, "Pathé Bellecour", "2026-06-30")
        inception_vf = [s for s in result if s["film"] == "Inception" and s["version"] == "VF"]
        heures = {s["heure"] for s in inception_vf}
        assert heures == {"10:30", "14:00"}

    def test_dune_heure(self):
        result = _parse_sessions(SAMPLE_HTML, "Pathé Bellecour", "2026-06-30")
        dune = [s for s in result if s["film"] == "Dune"]
        assert len(dune) == 1
        assert dune[0]["heure"] == "16:15"
        assert dune[0]["version"] == "VF"

    def test_empty_html_returns_empty_list(self):
        result = _parse_sessions(EMPTY_HTML, "Pathé Bellecour", "2026-06-30")
        assert result == []

    def test_date_str_propagated_correctly(self):
        result = _parse_sessions(SAMPLE_HTML, "Test Cinéma", "2026-07-15")
        for session in result:
            assert session["date"] == "2026-07-15"

    def test_cinema_name_propagated_correctly(self):
        result = _parse_sessions(SAMPLE_HTML, "UGC Part-Dieu", "2026-06-30")
        for session in result:
            assert session["cinema"] == "UGC Part-Dieu"


# ---------------------------------------------------------------------------
# Tests for scrape_cinema_day (Selenium driver mocked)
# ---------------------------------------------------------------------------

def _make_webdriverwait_patch(condition_result=True):
    """Patch WebDriverWait so .until() returns immediately without blocking."""
    mock_wait = MagicMock()
    mock_wait.__enter__ = MagicMock(return_value=mock_wait)
    mock_wait.__exit__ = MagicMock(return_value=False)
    mock_wait.until.return_value = True
    return mock_wait


class TestScrapecinemadayWithMockDriver:
    """Tests de scrape_cinema_day avec un driver Selenium mocké."""

    def _make_driver_mock(self, page_source=SAMPLE_HTML):
        driver = MagicMock()
        driver.page_source = page_source
        # find_elements for calendar spans → return an empty list by default
        # (WebDriverWait will be patched, so calendar detection path is bypassed)
        driver.find_elements.return_value = []
        return driver

    def test_returns_list(self):
        driver = self._make_driver_mock()
        with patch("scraper.WebDriverWait") as mock_wdw:
            mock_wdw.return_value.until.return_value = True
            result = scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30", driver=driver)
        assert isinstance(result, list)

    def test_calls_driver_get(self):
        driver = self._make_driver_mock()
        with patch("scraper.WebDriverWait") as mock_wdw:
            mock_wdw.return_value.until.return_value = True
            scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30", driver=driver)
        driver.get.assert_called_once()
        called_url = driver.get.call_args[0][0]
        assert "P0012" in called_url
        assert "allocine.fr" in called_url

    def test_uses_parse_sessions_helper(self):
        driver = self._make_driver_mock()
        with patch("scraper.WebDriverWait") as mock_wdw, \
             patch("scraper._parse_sessions", return_value=[{"cinema": "X"}]) as mock_parse:
            mock_wdw.return_value.until.return_value = True
            result = scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30", driver=driver)
        mock_parse.assert_called_once()

    def test_returns_empty_on_exception(self):
        driver = self._make_driver_mock()
        driver.get.side_effect = Exception("Network error")
        result = scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30", driver=driver)
        assert result == []

    def test_does_not_quit_reused_driver(self):
        """When a driver is passed in, scrape_cinema_day must NOT quit it."""
        driver = self._make_driver_mock()
        with patch("scraper.WebDriverWait") as mock_wdw:
            mock_wdw.return_value.until.return_value = True
            scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30", driver=driver)
        driver.quit.assert_not_called()

    def test_creates_and_quits_own_driver_when_none_passed(self):
        """When no driver is passed, scrape_cinema_day creates and quits its own."""
        own_driver = self._make_driver_mock()
        with patch("scraper._make_driver", return_value=own_driver) as mock_make, \
             patch("scraper.WebDriverWait") as mock_wdw:
            mock_wdw.return_value.until.return_value = True
            scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30")
        mock_make.assert_called_once()
        own_driver.quit.assert_called_once()


# ---------------------------------------------------------------------------
# Tests for scrape_all (driver lifecycle and aggregation)
# ---------------------------------------------------------------------------

class TestScrapeAll:
    """Tests pour scrape_all — 9 cinémas × 21 jours avec un seul driver."""

    def _patched_scrape_all(self, sessions_per_call=None):
        """Run scrape_all with _make_driver and scrape_cinema_day both mocked."""
        mock_driver = MagicMock()
        call_results = sessions_per_call or [
            [{"cinema": "C", "film": "F", "date": "2026-06-30",
              "heure": "14:00", "version": "VF", "temperature": None}]
        ]
        # Make scrape_cinema_day return call_results cyclically
        import itertools
        cycle = itertools.cycle(call_results)

        with patch("scraper._make_driver", return_value=mock_driver), \
             patch("scraper.scrape_cinema_day", side_effect=lambda *a, **kw: next(cycle)) as mock_scd:
            result = scrape_all()
        return result, mock_driver, mock_scd

    def test_returns_list(self):
        result, _, _ = self._patched_scrape_all()
        assert isinstance(result, list)

    def test_calls_scrape_cinema_day_for_each_cinema_and_date(self):
        """scrape_all must call scrape_cinema_day exactly 9 × 21 = 189 times."""
        result, _, mock_scd = self._patched_scrape_all()
        assert mock_scd.call_count == len(CINEMA_IDS) * 21

    def test_driver_quit_called_once(self):
        """The shared driver must be quit exactly once after all scraping."""
        _, mock_driver, _ = self._patched_scrape_all()
        mock_driver.quit.assert_called_once()

    def test_driver_quit_called_even_on_exception(self):
        """Driver.quit() must be called even if scrape_cinema_day raises."""
        mock_driver = MagicMock()
        with patch("scraper._make_driver", return_value=mock_driver), \
             patch("scraper.scrape_cinema_day", side_effect=Exception("boom")):
            try:
                scrape_all()
            except Exception:
                pass
        mock_driver.quit.assert_called_once()

    def test_aggregates_all_sessions(self):
        """Sessions from all cinema/date calls are concatenated."""
        one_session = [{"cinema": "C", "film": "F", "date": "d",
                        "heure": "10:00", "version": "VF", "temperature": None}]
        result, _, _ = self._patched_scrape_all(sessions_per_call=[one_session])
        # 9 cinemas × 21 days = 189 calls, 1 session each → 189 sessions
        assert len(result) == len(CINEMA_IDS) * 21

    def test_progress_callback_called(self):
        """progress_callback must be called for each cinema/date combination."""
        calls = []
        mock_driver = MagicMock()
        with patch("scraper._make_driver", return_value=mock_driver), \
             patch("scraper.scrape_cinema_day", return_value=[]):
            scrape_all(progress_callback=lambda cur, tot, name: calls.append((cur, tot, name)))
        assert len(calls) == len(CINEMA_IDS) * 21
        # Progress counter starts at 1 and reaches total
        assert calls[0][0] == 1
        assert calls[-1][0] == len(CINEMA_IDS) * 21
        assert calls[0][1] == len(CINEMA_IDS) * 21

    def test_covers_21_dates(self):
        """Dates scraped must span 21 distinct days starting from today."""
        from datetime import datetime, timedelta
        scraped_dates = []
        mock_driver = MagicMock()

        def capture_date(cinema_name, cinema_id, date_str, driver=None):
            scraped_dates.append(date_str)
            return []

        with patch("scraper._make_driver", return_value=mock_driver), \
             patch("scraper.scrape_cinema_day", side_effect=capture_date):
            scrape_all()

        unique_dates = sorted(set(scraped_dates))
        assert len(unique_dates) == 21
        today = datetime.now().date().isoformat()
        assert unique_dates[0] == today
        last_expected = (datetime.now().date() + timedelta(days=20)).isoformat()
        assert unique_dates[-1] == last_expected
