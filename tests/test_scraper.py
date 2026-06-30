"""Tests for scraper._api_to_sessions, scrape_cinema_day, and scrape_all.

Architecture post-allocineAPI:
- _api_to_sessions(api_result, cinema_name, date_str) is the pure testable helper.
- scrape_cinema_day wraps _api_to_sessions + allocineAPI (mocked in tests).
- scrape_all creates one API instance and iterates over cinemas x dates (mocked).
"""
from unittest.mock import patch, Mock, MagicMock
import scraper
from scraper import _api_to_sessions, scrape_cinema_day, scrape_all, CINEMA_IDS

# ---------------------------------------------------------------------------
# Sample API response matching the real allocineAPI structure:
# {"title": str, "showtimes": [{"startsAt": ISO str, "diffusionVersion": str}]}
# diffusionVersion: "DUBBED" -> VF, "ORIGINAL" -> VO, "LOCAL" -> VF
# ---------------------------------------------------------------------------

SAMPLE_API_RESPONSE = [
    {
        "title": "Dune : Partie 2",
        "showtimes": [
            {"startsAt": "2026-06-30T14:00:00", "diffusionVersion": "DUBBED"},
            {"startsAt": "2026-06-30T17:30:00", "diffusionVersion": "DUBBED"},
            {"startsAt": "2026-06-30T20:00:00", "diffusionVersion": "ORIGINAL"},
        ],
    },
    {
        "title": "Le Comte de Monte-Cristo",
        "showtimes": [
            {"startsAt": "2026-06-30T15:00:00", "diffusionVersion": "DUBBED"},
        ],
    },
]


# ---------------------------------------------------------------------------
# Tests for _api_to_sessions (pure conversion logic)
# ---------------------------------------------------------------------------

class TestApiToSessions:
    """Tests for the pure _api_to_sessions helper."""

    def test_returns_list(self):
        result = _api_to_sessions(SAMPLE_API_RESPONSE, "Pathé Bellecour", "2026-06-30")
        assert isinstance(result, list)

    def test_correct_total_count(self):
        # Dune: 2 VF + 1 VO = 3; Monte-Cristo: 1 VF → total 4
        result = _api_to_sessions(SAMPLE_API_RESPONSE, "Pathé Bellecour", "2026-06-30")
        assert len(result) == 4

    def test_all_required_keys_present(self):
        result = _api_to_sessions(SAMPLE_API_RESPONSE, "Pathé Bellecour", "2026-06-30")
        required = {"cinema", "film", "date", "heure", "version", "temperature"}
        for session in result:
            assert required == set(session.keys()), f"Missing keys in {session}"

    def test_temperature_is_none(self):
        result = _api_to_sessions(SAMPLE_API_RESPONSE, "Pathé Bellecour", "2026-06-30")
        for session in result:
            assert session["temperature"] is None

    def test_cinema_name_correct(self):
        result = _api_to_sessions(SAMPLE_API_RESPONSE, "Pathé Bellecour", "2026-06-30")
        for session in result:
            assert session["cinema"] == "Pathé Bellecour"

    def test_date_correct(self):
        result = _api_to_sessions(SAMPLE_API_RESPONSE, "Pathé Bellecour", "2026-06-30")
        for session in result:
            assert session["date"] == "2026-06-30"

    def test_film_titles_extracted(self):
        result = _api_to_sessions(SAMPLE_API_RESPONSE, "Pathé Bellecour", "2026-06-30")
        films = {s["film"] for s in result}
        assert "Dune : Partie 2" in films
        assert "Le Comte de Monte-Cristo" in films

    def test_dubbed_maps_to_vf(self):
        result = _api_to_sessions(SAMPLE_API_RESPONSE, "Pathé Bellecour", "2026-06-30")
        vf_sessions = [s for s in result if s["version"] == "VF"]
        assert len(vf_sessions) == 3  # 2 Dune VF + 1 Monte-Cristo VF

    def test_original_maps_to_vo(self):
        result = _api_to_sessions(SAMPLE_API_RESPONSE, "Pathé Bellecour", "2026-06-30")
        vo_sessions = [s for s in result if s["version"] == "VO"]
        assert len(vo_sessions) == 1
        assert vo_sessions[0]["film"] == "Dune : Partie 2"
        assert vo_sessions[0]["heure"] == "20:00"

    def test_local_maps_to_vf(self):
        local_response = [
            {"title": "Film Local", "showtimes": [
                {"startsAt": "2026-06-30T18:00:00", "diffusionVersion": "LOCAL"}
            ]}
        ]
        result = _api_to_sessions(local_response, "Test", "2026-06-30")
        assert result[0]["version"] == "VF"

    def test_heure_extracted_from_startsAt(self):
        result = _api_to_sessions(SAMPLE_API_RESPONSE, "Pathé Bellecour", "2026-06-30")
        dune_vf = [s for s in result if s["film"] == "Dune : Partie 2" and s["version"] == "VF"]
        heures = {s["heure"] for s in dune_vf}
        assert heures == {"14:00", "17:30"}

    def test_empty_list_returns_empty(self):
        assert _api_to_sessions([], "Test", "2026-06-30") == []

    def test_none_returns_empty(self):
        assert _api_to_sessions(None, "Test", "2026-06-30") == []

    def test_film_with_no_title_skipped(self):
        bad_response = [
            {"title": "", "showtimes": [{"startsAt": "2026-06-30T10:00:00", "diffusionVersion": "DUBBED"}]},
            {"title": "Bon Film", "showtimes": [{"startsAt": "2026-06-30T12:00:00", "diffusionVersion": "DUBBED"}]},
        ]
        result = _api_to_sessions(bad_response, "Test", "2026-06-30")
        assert len(result) == 1
        assert result[0]["film"] == "Bon Film"

    def test_date_str_propagated_correctly(self):
        result = _api_to_sessions(SAMPLE_API_RESPONSE, "Test Cinéma", "2026-07-15")
        for session in result:
            assert session["date"] == "2026-07-15"

    def test_cinema_name_propagated_correctly(self):
        result = _api_to_sessions(SAMPLE_API_RESPONSE, "UGC Part-Dieu", "2026-06-30")
        for session in result:
            assert session["cinema"] == "UGC Part-Dieu"


# ---------------------------------------------------------------------------
# Tests for scrape_cinema_day (allocineAPI mocked)
# ---------------------------------------------------------------------------

class TestScrapeCinemaDay:
    """Tests for scrape_cinema_day with a mocked allocineAPI."""

    def test_returns_list(self):
        mock_api = Mock()
        mock_api.get_showtime.return_value = SAMPLE_API_RESPONSE
        result = scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30", api=mock_api)
        assert isinstance(result, list)

    def test_calls_get_showtime_with_correct_args(self):
        mock_api = Mock()
        mock_api.get_showtime.return_value = SAMPLE_API_RESPONSE
        scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30", api=mock_api)
        mock_api.get_showtime.assert_called_once_with("P0012", "2026-06-30")

    def test_returns_correct_sessions(self):
        mock_api = Mock()
        mock_api.get_showtime.return_value = SAMPLE_API_RESPONSE
        sessions = scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30", api=mock_api)
        assert len(sessions) == 4

    def test_returns_empty_on_exception(self):
        mock_api = Mock()
        mock_api.get_showtime.side_effect = Exception("API error")
        sessions = scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30", api=mock_api)
        assert sessions == []

    def test_returns_empty_on_typeerror(self):
        # Matches the real P0050 bug where allocineAPI raises TypeError
        mock_api = Mock()
        mock_api.get_showtime.side_effect = TypeError("'NoneType' object is not subscriptable")
        sessions = scrape_cinema_day("Institut Lumière", "P0050", "2026-06-30", api=mock_api)
        assert sessions == []

    def test_creates_own_api_when_none_passed(self):
        with patch("scraper.allocineAPI") as MockAPI:
            mock_instance = MockAPI.return_value
            mock_instance.get_showtime.return_value = []
            scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30")
        MockAPI.assert_called_once()

    def test_uses_provided_api_instance(self):
        mock_api = Mock()
        mock_api.get_showtime.return_value = []
        with patch("scraper.allocineAPI") as MockAPI:
            scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30", api=mock_api)
        # Should NOT create a new allocineAPI instance
        MockAPI.assert_not_called()


# ---------------------------------------------------------------------------
# Tests for scrape_all (API lifecycle and aggregation)
# ---------------------------------------------------------------------------

class TestScrapeAll:
    """Tests for scrape_all — 9 cinemas × 21 days."""

    def test_returns_list(self):
        with patch("scraper.allocineAPI") as MockAPI, \
             patch("scraper.time.sleep"):
            MockAPI.return_value.get_showtime.return_value = []
            result = scrape_all()
        assert isinstance(result, list)

    def test_calls_get_showtime_189_times(self):
        """scrape_all must call get_showtime exactly 9 × 21 = 189 times."""
        with patch("scraper.allocineAPI") as MockAPI, \
             patch("scraper.time.sleep"):
            mock_instance = MockAPI.return_value
            mock_instance.get_showtime.return_value = []
            scrape_all()
        assert mock_instance.get_showtime.call_count == len(CINEMA_IDS) * 21

    def test_creates_single_api_instance(self):
        """scrape_all must create exactly one allocineAPI instance."""
        with patch("scraper.allocineAPI") as MockAPI, \
             patch("scraper.time.sleep"):
            MockAPI.return_value.get_showtime.return_value = []
            scrape_all()
        assert MockAPI.call_count == 1

    def test_aggregates_all_sessions(self):
        """Sessions from all cinema/date calls are concatenated."""
        one_session = {
            "title": "Film Test",
            "showtimes": [{"startsAt": "2026-06-30T14:00:00", "diffusionVersion": "DUBBED"}],
        }
        with patch("scraper.allocineAPI") as MockAPI, \
             patch("scraper.time.sleep"):
            MockAPI.return_value.get_showtime.return_value = [one_session]
            result = scrape_all()
        # 9 cinemas × 21 days = 189 calls, 1 session each
        assert len(result) == len(CINEMA_IDS) * 21

    def test_progress_callback_called(self):
        """progress_callback must be called for each cinema/date combination."""
        calls = []
        with patch("scraper.allocineAPI") as MockAPI, \
             patch("scraper.time.sleep"):
            MockAPI.return_value.get_showtime.return_value = []
            scrape_all(progress_callback=lambda cur, tot, name: calls.append((cur, tot, name)))
        assert len(calls) == len(CINEMA_IDS) * 21
        assert calls[0][0] == 1
        assert calls[-1][0] == len(CINEMA_IDS) * 21
        assert calls[0][1] == len(CINEMA_IDS) * 21

    def test_covers_21_dates(self):
        """Dates scraped must span 21 distinct days starting from today."""
        from datetime import datetime, timedelta
        scraped_dates = []

        def capture(*args, **kwargs):
            # args[1] is date_str in get_showtime(cinema_id, date_str)
            scraped_dates.append(args[1])
            return []

        with patch("scraper.allocineAPI") as MockAPI, \
             patch("scraper.time.sleep"):
            MockAPI.return_value.get_showtime.side_effect = capture
            scrape_all()

        unique_dates = sorted(set(scraped_dates))
        assert len(unique_dates) == 21
        today = datetime.now().date().isoformat()
        assert unique_dates[0] == today
        last_expected = (datetime.now().date() + timedelta(days=20)).isoformat()
        assert unique_dates[-1] == last_expected

    def test_continues_on_api_error(self):
        """scrape_all must not raise even if some API calls fail."""
        call_count = 0

        def flaky(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:
                raise Exception("Transient error")
            return []

        with patch("scraper.allocineAPI") as MockAPI, \
             patch("scraper.time.sleep"):
            MockAPI.return_value.get_showtime.side_effect = flaky
            result = scrape_all()

        assert isinstance(result, list)
        assert call_count == len(CINEMA_IDS) * 21
