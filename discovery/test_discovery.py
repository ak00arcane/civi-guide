"""Offline tests for the discovery stage. No network access required."""

from classify import extract_text, score_page
from harvest import is_blocked, links_from_html, matches_keyword, parse_sitemap

KEYWORDS = ["scheme", "yojana", "thittam", "pension"]
BLOCKLIST = ["/tender", "/recruitment", ".zip"]


# -- harvest: url filtering --------------------------------------------


def test_keyword_match_is_case_insensitive():
    assert matches_keyword("https://tn.gov.in/Scheme/Pudhumai", KEYWORDS) == "scheme"


def test_keyword_match_returns_none_when_absent():
    assert matches_keyword("https://tn.gov.in/about-us", KEYWORDS) is None


def test_regional_keyword_matches():
    assert matches_keyword("https://tn.gov.in/thittam/123", KEYWORDS) == "thittam"


def test_blocklist_catches_tenders():
    assert is_blocked("https://x.gov.in/tender/scheme-notice", BLOCKLIST)


def test_blocklist_allows_normal_page():
    assert not is_blocked("https://x.gov.in/scheme/pension-old-age", BLOCKLIST)


# -- harvest: sitemap parsing ------------------------------------------

URLSET = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://x.gov.in/scheme/a</loc></url>
  <url><loc>https://x.gov.in/scheme/b</loc></url>
</urlset>"""

SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://x.gov.in/sitemap-1.xml</loc></sitemap>
  <sitemap><loc>https://x.gov.in/sitemap-2.xml</loc></sitemap>
</sitemapindex>"""

URLSET_NO_NS = """<urlset>
  <url><loc>https://x.gov.in/yojana/c</loc></url>
</urlset>"""


def test_parse_urlset_returns_pages_and_no_children():
    pages, children = parse_sitemap(URLSET)
    assert pages == ["https://x.gov.in/scheme/a", "https://x.gov.in/scheme/b"]
    assert children == []


def test_parse_sitemap_index_returns_children_not_pages():
    pages, children = parse_sitemap(SITEMAP_INDEX)
    assert pages == []
    assert len(children) == 2


def test_parse_sitemap_without_namespace():
    pages, _ = parse_sitemap(URLSET_NO_NS)
    assert pages == ["https://x.gov.in/yojana/c"]


def test_parse_sitemap_survives_garbage():
    assert parse_sitemap("<html>not a sitemap") == ([], [])


# -- harvest: index page links -----------------------------------------

INDEX_HTML = """
<html><body>
  <a href="/scheme/one">One</a>
  <a href="scheme/two">Two</a>
  <a href="https://other.example.com/scheme/three">Offsite</a>
  <a href="#top">Anchor</a>
  <a href="mailto:x@y.in">Mail</a>
  <a href="/scheme/one">Duplicate</a>
</body></html>
"""


def test_links_are_absolute_same_host_and_deduped():
    links = links_from_html(INDEX_HTML, "https://x.gov.in/schemes")
    assert links == ["https://x.gov.in/scheme/one", "https://x.gov.in/scheme/two"]


# -- classify: text extraction -----------------------------------------


def test_extract_text_drops_scripts_and_keeps_title():
    html = "<html><head><title>Old Age Pension</title></head><body><script>x=1</script><p>Hello  world</p></body></html>"
    title, text = extract_text(html)
    assert title == "Old Age Pension"
    assert "x=1" not in text
    assert text == "Hello world"


# -- classify: scoring -------------------------------------------------

SCHEME_TEXT = (
    "Indira Gandhi National Old Age Pension Scheme. Department of Social Welfare, "
    "Government of Tamil Nadu. Eligibility: the applicant must be a resident of Tamil Nadu, "
    "aged 60 years or above, and belong to a below poverty line household. Benefits: a monthly "
    "financial assistance of Rs. 1,200 is credited to the beneficiary account. How to apply: "
    "submit the application form at the taluk office. Documents required: age proof, ration card, "
    "and Aadhaar. The scheme is administered by the Directorate of Social Welfare. " * 3
)

TENDER_TEXT = (
    "Tender notice for supply of furniture under the welfare scheme wing. Bid document may be "
    "downloaded from the portal. Earnest money deposit of Rs. 50,000 is required. Last date for "
    "submission of bids is 30 September. The department of social welfare invites sealed bids "
    "from registered vendors with prior experience. " * 4
)

BROCHURE_TEXT = (
    "About the mission. The Government of India launched this mission to improve rural livelihoods "
    "across the country. It is administered by the Ministry of Rural Development and has reached "
    "many districts. The programme continues to expand its footprint each year with sustained "
    "budgetary support and strong state participation. " * 5
)


def test_real_scheme_page_is_accepted():
    v = score_page("Old Age Pension Scheme", SCHEME_TEXT)
    assert v.is_scheme
    assert v.score >= 0.55
    assert "eligibility" in v.signals
    assert "how_to_apply" in v.signals


def test_tender_page_is_rejected_despite_scheme_word():
    v = score_page("Tender Notice", TENDER_TEXT)
    assert not v.is_scheme
    assert "tender" in v.penalties


def test_brochure_without_eligibility_is_rejected():
    v = score_page("About the Mission", BROCHURE_TEXT)
    assert not v.is_scheme
    assert "no_eligibility_section" in v.penalties


def test_short_page_is_rejected_early():
    v = score_page("Scheme", "Eligibility: everyone. Benefits: money.")
    assert not v.is_scheme
    assert v.reason == "too_short"


def test_error_page_is_rejected():
    text = "Page not found. The page you are looking for does not exist. " * 20
    v = score_page("404", text)
    assert not v.is_scheme


def test_score_is_clamped_to_unit_range():
    v = score_page("Old Age Pension Scheme", SCHEME_TEXT)
    assert 0.0 <= v.score <= 1.0


BORDERLINE_TEXT = (
    "Eligibility for this scheme is limited to residents of the state who meet the stated "
    "conditions. Benefits are provided in the form of assistance to the selected applicants "
    "under the programme as notified from time to time by the competent authority. " * 5
)


def test_threshold_is_respected():
    lenient = score_page("State Scheme", BORDERLINE_TEXT, threshold=0.40)
    strict = score_page("State Scheme", BORDERLINE_TEXT, threshold=0.90)
    assert lenient.is_scheme
    assert not strict.is_scheme
    assert strict.reason == "below_threshold"
    assert lenient.score == strict.score  # threshold changes the verdict, not the score
