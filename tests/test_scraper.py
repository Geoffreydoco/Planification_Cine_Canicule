"""Tests for scraper._api_to_sessions, scrape_cinema_day, and scrape_all.

Architecture post-allocineAPI:
- _api_to_sessions(api_result, cinema_name, date_str) is the pure testable helper.
- scrape_cinema_day wraps _api_to_sessions + allocineAPI (mocked in tests).
- scrape_all creates one API instance and iterates over cinemas x dates (mocked).
"""
from unittest.mock import patch, Mock, MagicMock
import scraper
from scraper import _api_to_sessions, scrape_cinema_day, scrape_all

# Dictionnaire fixe pour les tests — on patche _fetch_cinema_ids pour retourner ceci
TEST_CINEMA_IDS = {
    "Cinéma Test A": "C001",
    "Cinéma Test B": "C002",
}

# ---------------------------------------------------------------------------
# Sample API response matching our enriched structure:
# {"title": str, "film_url": str, "duration": str,
#  "showtimes": [{"startsAt": ISO str, "diffusionVersion": str}]}
# diffusionVersion: "DUBBED" -> VF, "ORIGINAL" -> VO, "LOCAL" -> VF
# ---------------------------------------------------------------------------

SAMPLE_API_RESPONSE = [
    {
        "title": "Dune : Partie 2",
        "film_url": "https://www.allocine.fr/film/fichefilm_gen_cfilm=223395.html",
        "duration": "2h 46min",
        "poster_url": "https://fr.web.img6.acsta.net/pictures/24/02/28/dune2.jpg",
        "synopsis": "Paul Atréides s'unit aux Fremen pour mener la guerre contre les Harkonnen.",
        "showtimes": [
            {"startsAt": "2026-06-30T14:00:00", "diffusionVersion": "DUBBED"},
            {"startsAt": "2026-06-30T17:30:00", "diffusionVersion": "DUBBED"},
            {"startsAt": "2026-06-30T20:00:00", "diffusionVersion": "ORIGINAL"},
        ],
    },
    {
        "title": "Le Comte de Monte-Cristo",
        "film_url": "https://www.allocine.fr/film/fichefilm_gen_cfilm=278154.html",
        "duration": "4h 01min",
        "poster_url": "",
        "synopsis": "",
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
        required = {
            "cinema", "film", "film_url", "duration", "poster_url", "synopsis",
            "date", "heure", "version", "temperature",
            "director", "user_rating", "press_rating", "genres", "actors", "certificate",
        }
        for session in result:
            missing = required - set(session.keys())
            assert not missing, f"Clés manquantes : {missing}"

    def test_film_url_present(self):
        result = _api_to_sessions(SAMPLE_API_RESPONSE, "Pathé Bellecour", "2026-06-30")
        dune = [s for s in result if s["film"] == "Dune : Partie 2"][0]
        assert dune["film_url"] == "https://www.allocine.fr/film/fichefilm_gen_cfilm=223395.html"

    def test_duration_present(self):
        result = _api_to_sessions(SAMPLE_API_RESPONSE, "Pathé Bellecour", "2026-06-30")
        dune = [s for s in result if s["film"] == "Dune : Partie 2"][0]
        assert dune["duration"] == "2h 46min"

    def test_missing_film_url_defaults_empty(self):
        response = [{"title": "Film Test", "showtimes": [
            {"startsAt": "2026-06-30T10:00:00", "diffusionVersion": "DUBBED"}
        ]}]
        result = _api_to_sessions(response, "Test", "2026-06-30")
        assert result[0]["film_url"] == ""

    def test_missing_duration_defaults_empty(self):
        response = [{"title": "Film Test", "showtimes": [
            {"startsAt": "2026-06-30T10:00:00", "diffusionVersion": "DUBBED"}
        ]}]
        result = _api_to_sessions(response, "Test", "2026-06-30")
        assert result[0]["duration"] == ""

    def test_poster_url_present(self):
        result = _api_to_sessions(SAMPLE_API_RESPONSE, "Pathé Bellecour", "2026-06-30")
        dune = [s for s in result if s["film"] == "Dune : Partie 2"][0]
        assert "poster_url" in dune
        assert dune["poster_url"] != ""

    def test_synopsis_present(self):
        result = _api_to_sessions(SAMPLE_API_RESPONSE, "Pathé Bellecour", "2026-06-30")
        dune = [s for s in result if s["film"] == "Dune : Partie 2"][0]
        assert "synopsis" in dune
        assert "Atréides" in dune["synopsis"]

    def test_missing_poster_synopsis_defaults_empty(self):
        response = [{"title": "Film Test", "showtimes": [
            {"startsAt": "2026-06-30T10:00:00", "diffusionVersion": "DUBBED"}
        ]}]
        result = _api_to_sessions(response, "Test", "2026-06-30")
        assert result[0]["poster_url"] == ""
        assert result[0]["synopsis"] == ""

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
    """Tests for scrape_cinema_day with a mocked _get_showtime_enriched."""

    def test_returns_list(self):
        with patch("scraper._get_showtime_enriched", return_value=SAMPLE_API_RESPONSE):
            result = scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30", api=Mock())
        assert isinstance(result, list)

    def test_calls_enriched_with_correct_args(self):
        mock_api = Mock()
        with patch("scraper._get_showtime_enriched", return_value=[]) as mock_enrich:
            scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30", api=mock_api)
        mock_enrich.assert_called_once_with(mock_api, "P0012", "2026-06-30")

    def test_returns_correct_sessions(self):
        with patch("scraper._get_showtime_enriched", return_value=SAMPLE_API_RESPONSE):
            sessions = scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30", api=Mock())
        assert len(sessions) == 4

    def test_sessions_have_film_url_and_duration(self):
        with patch("scraper._get_showtime_enriched", return_value=SAMPLE_API_RESPONSE):
            sessions = scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30", api=Mock())
        for s in sessions:
            assert "film_url" in s
            assert "duration" in s

    def test_returns_empty_on_exception(self):
        with patch("scraper._get_showtime_enriched", side_effect=Exception("API error")):
            sessions = scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30", api=Mock())
        assert sessions == []

    def test_returns_empty_on_typeerror(self):
        # Matches the real P0050 bug where allocineAPI raises TypeError
        with patch("scraper._get_showtime_enriched", side_effect=TypeError("'NoneType' object is not subscriptable")):
            sessions = scrape_cinema_day("Institut Lumière", "P0050", "2026-06-30", api=Mock())
        assert sessions == []

    def test_creates_own_api_when_none_passed(self):
        with patch("scraper._AllocineAPIWithHeaders") as MockAPI, \
             patch("scraper._get_showtime_enriched", return_value=[]):
            scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30")
        MockAPI.assert_called_once()

    def test_uses_provided_api_instance(self):
        mock_api = Mock()
        with patch("scraper.allocineAPI") as MockAPI, \
             patch("scraper._get_showtime_enriched", return_value=[]):
            scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30", api=mock_api)
        # Should NOT create a new allocineAPI instance
        MockAPI.assert_not_called()


# ---------------------------------------------------------------------------
# Tests for scrape_all (API lifecycle and aggregation)
# ---------------------------------------------------------------------------

class TestScrapeAll:
    """Tests for scrape_all — dynamic cinema list × 21 dates."""

    def test_returns_list(self):
        with patch("scraper._fetch_cinema_ids", return_value=TEST_CINEMA_IDS), \
             patch("scraper._AllocineAPIWithHeaders"), \
             patch("scraper.time.sleep"), \
             patch("scraper._get_showtime_enriched", return_value=[]):
            result = scrape_all()
        assert isinstance(result, list)

    def test_calls_enriched_N_times(self):
        """scrape_all doit appeler _get_showtime_enriched une fois par cinéma × par date."""
        with patch("scraper._fetch_cinema_ids", return_value=TEST_CINEMA_IDS), \
             patch("scraper._AllocineAPIWithHeaders"), \
             patch("scraper.time.sleep"), \
             patch("scraper._get_showtime_enriched", return_value=[]) as mock_enrich:
            scrape_all()
        assert mock_enrich.call_count == len(TEST_CINEMA_IDS) * 21

    def test_creates_one_api_instance_per_cinema(self):
        """scrape_all doit créer une instance _AllocineAPIWithHeaders par cinéma (workers parallèles)."""
        with patch("scraper._fetch_cinema_ids", return_value=TEST_CINEMA_IDS), \
             patch("scraper._AllocineAPIWithHeaders") as MockAPI, \
             patch("scraper.time.sleep"), \
             patch("scraper._get_showtime_enriched", return_value=[]):
            scrape_all()
        assert MockAPI.call_count == len(TEST_CINEMA_IDS)

    def test_aggregates_all_sessions(self):
        """Les sessions de tous les appels cinéma/date sont concaténées."""
        one_session = {
            "title": "Film Test",
            "film_url": "https://www.allocine.fr/film/fichefilm_gen_cfilm=99999.html",
            "duration": "1h 30min",
            "showtimes": [{"startsAt": "2026-06-30T14:00:00", "diffusionVersion": "DUBBED"}],
        }
        with patch("scraper._fetch_cinema_ids", return_value=TEST_CINEMA_IDS), \
             patch("scraper._AllocineAPIWithHeaders"), \
             patch("scraper.time.sleep"), \
             patch("scraper._get_showtime_enriched", return_value=[one_session]):
            result = scrape_all()
        assert len(result) == len(TEST_CINEMA_IDS) * 21

    def test_progress_callback_called(self):
        """progress_callback doit être appelé pour chaque combinaison cinéma/date."""
        calls = []
        with patch("scraper._fetch_cinema_ids", return_value=TEST_CINEMA_IDS), \
             patch("scraper._AllocineAPIWithHeaders"), \
             patch("scraper.time.sleep"), \
             patch("scraper._get_showtime_enriched", return_value=[]):
            scrape_all(progress_callback=lambda cur, tot, name: calls.append((cur, tot, name)))
        assert len(calls) == len(TEST_CINEMA_IDS) * 21
        assert calls[0][0] == 1
        assert calls[-1][0] == len(TEST_CINEMA_IDS) * 21
        assert calls[0][1] == len(TEST_CINEMA_IDS) * 21

    def test_covers_21_dates(self):
        """Les dates scrappées doivent couvrir 21 jours distincts à partir d'aujourd'hui."""
        from datetime import datetime, timedelta
        scraped_dates = []

        def capture(api_instance, cinema_id, date_str):
            scraped_dates.append(date_str)
            return []

        with patch("scraper._fetch_cinema_ids", return_value=TEST_CINEMA_IDS), \
             patch("scraper._AllocineAPIWithHeaders"), \
             patch("scraper.time.sleep"), \
             patch("scraper._get_showtime_enriched", side_effect=capture):
            scrape_all()

        unique_dates = sorted(set(scraped_dates))
        assert len(unique_dates) == 21
        today = datetime.now().date().isoformat()
        assert unique_dates[0] == today
        last_expected = (datetime.now().date() + timedelta(days=20)).isoformat()
        assert unique_dates[-1] == last_expected

    def test_continues_on_api_error(self):
        """scrape_all ne doit pas lever même si certains appels API échouent."""
        call_count = 0

        def flaky(api_instance, cinema_id, date_str):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:
                raise Exception("Transient error")
            return []

        with patch("scraper._fetch_cinema_ids", return_value=TEST_CINEMA_IDS), \
             patch("scraper._AllocineAPIWithHeaders"), \
             patch("scraper.time.sleep"), \
             patch("scraper._get_showtime_enriched", side_effect=flaky):
            result = scrape_all()

        assert isinstance(result, list)
        assert call_count == len(TEST_CINEMA_IDS) * 21
