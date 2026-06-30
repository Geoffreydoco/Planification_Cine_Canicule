"""Tests pour scraper.scrape_cinema_day et scraper.scrape_all."""
from unittest.mock import patch, MagicMock
import pytest
from scraper import scrape_cinema_day, scrape_all

# ---------------------------------------------------------------------------
# Minimal HTML that mirrors the real AlloCiné structure discovered by
# inspecting https://www.allocine.fr/seance/salle_gen_csalle=P0012.html
# Structure:
#   .card.entity-card
#     h2  (film title)
#     .showtimes-versions-holder
#       .showtimes-version   (one per language version)
#         div.text           "30 juin 2026 - En VF"
#         div.hours
#           .showtimes-hour-block
#             .showtimes-hour-item
#               span.showtimes-hour-item-value  "10:40"
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


def _make_response(status_code=200, text=SAMPLE_HTML):
    """Helper: build a mock requests.Response."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.text = text
    if status_code >= 400:
        from requests.exceptions import HTTPError
        mock_resp.raise_for_status.side_effect = HTTPError(response=mock_resp)
    else:
        mock_resp.raise_for_status.return_value = None
    return mock_resp


def _make_side_effect(*responses):
    """Return a side-effect list so successive requests.get calls return
    different mock responses (useful for the 404-then-200 fallback)."""
    return list(responses)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestScrapecinemadayStructure:
    """Tests de la structure de la valeur de retour."""

    def _sessions(self):
        with patch("scraper.requests.get", return_value=_make_response()):
            return scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30")

    def test_returns_list(self):
        result = self._sessions()
        assert isinstance(result, list)

    def test_correct_total_count(self):
        # Inception: 2 VF + 1 VOST = 3 ; Dune: 1 VF = 1 → total 4
        result = self._sessions()
        assert len(result) == 4

    def test_all_required_keys_present(self):
        result = self._sessions()
        required = {"cinema", "film", "date", "heure", "version", "temperature"}
        for session in result:
            assert required == set(session.keys()), f"Missing keys in {session}"

    def test_temperature_is_none(self):
        result = self._sessions()
        for session in result:
            assert session["temperature"] is None

    def test_cinema_name_correct(self):
        result = self._sessions()
        for session in result:
            assert session["cinema"] == "Pathé Bellecour"

    def test_date_correct(self):
        result = self._sessions()
        for session in result:
            assert session["date"] == "2026-06-30"


class TestScrapecinemadayValues:
    """Tests des valeurs extraites."""

    def _sessions(self):
        with patch("scraper.requests.get", return_value=_make_response()):
            return scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30")

    def test_film_titles_extracted(self):
        result = self._sessions()
        films = {s["film"] for s in result}
        assert "Inception" in films
        assert "Dune" in films

    def test_vf_version_extracted(self):
        result = self._sessions()
        vf_sessions = [s for s in result if s["version"] == "VF"]
        assert len(vf_sessions) == 3  # 2 Inception VF + 1 Dune VF

    def test_vost_version_extracted(self):
        result = self._sessions()
        vost_sessions = [s for s in result if s["version"] == "VOST"]
        assert len(vost_sessions) == 1
        assert vost_sessions[0]["film"] == "Inception"
        assert vost_sessions[0]["heure"] == "20:00"

    def test_inception_vf_heures(self):
        result = self._sessions()
        inception_vf = [s for s in result if s["film"] == "Inception" and s["version"] == "VF"]
        heures = {s["heure"] for s in inception_vf}
        assert heures == {"10:30", "14:00"}

    def test_dune_heure(self):
        result = self._sessions()
        dune = [s for s in result if s["film"] == "Dune"]
        assert len(dune) == 1
        assert dune[0]["heure"] == "16:15"
        assert dune[0]["version"] == "VF"


class TestScrapecinemadayErrors:
    """Tests de gestion des erreurs.

    Note : scrape_cinema_day utilise uniquement l'URL sans date (URL undatée),
    conformément à la limitation AlloCiné — les URLs datées renvoient 404 et le
    paramètre ?shwt_date= est ignoré côté serveur (navigation JS uniquement).
    """

    def test_returns_empty_list_on_http_500(self):
        with patch("scraper.requests.get", return_value=_make_response(500)):
            result = scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30")
        assert result == []

    def test_returns_empty_list_on_http_404(self):
        with patch("scraper.requests.get", return_value=_make_response(404)):
            result = scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30")
        assert result == []

    def test_returns_empty_list_on_connection_error(self):
        import requests as req_lib
        with patch("scraper.requests.get", side_effect=req_lib.ConnectionError("no network")):
            result = scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30")
        assert result == []

    def test_returns_empty_list_on_empty_html(self):
        with patch("scraper.requests.get", return_value=_make_response(text="<html></html>")):
            result = scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30")
        assert result == []

    def test_only_one_http_request_per_call(self):
        """scrape_cinema_day must make exactly one HTTP request (undated URL only)."""
        with patch("scraper.requests.get", return_value=_make_response()) as mock_get:
            scrape_cinema_day("Pathé Bellecour", "P0012", "2026-06-30")
        assert mock_get.call_count == 1
        called_url = mock_get.call_args[0][0]
        assert "P0012" in called_url
        # Must NOT contain d_date or shwt_date
        assert "d_date" not in called_url
        assert "shwt_date" not in called_url


class TestScrapeAll:
    """Tests pour scrape_all — scrape le jour courant pour tous les cinémas."""

    def test_returns_list(self):
        with patch("scraper.requests.get", return_value=_make_response()):
            with patch("scraper.time.sleep"):
                result = scrape_all()
        assert isinstance(result, list)

    def test_calls_each_cinema_once(self):
        """scrape_all doit faire exactement un appel HTTP par cinéma."""
        from scraper import CINEMA_IDS
        with patch("scraper.requests.get", return_value=_make_response()) as mock_get:
            with patch("scraper.time.sleep"):
                scrape_all()
        assert mock_get.call_count == len(CINEMA_IDS)

    def test_aggregates_sessions_from_all_cinemas(self):
        """scrape_all doit agréger les séances de tous les cinémas."""
        from scraper import CINEMA_IDS
        with patch("scraper.requests.get", return_value=_make_response()):
            with patch("scraper.time.sleep"):
                result = scrape_all()
        # SAMPLE_HTML has 4 sessions; with 9 cinemas that is 9*4 = 36
        assert len(result) == len(CINEMA_IDS) * 4

    def test_all_sessions_have_today_date(self):
        """Toutes les séances doivent avoir la date du jour courant."""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        with patch("scraper.requests.get", return_value=_make_response()):
            with patch("scraper.time.sleep"):
                result = scrape_all()
        for session in result:
            assert session["date"] == today
