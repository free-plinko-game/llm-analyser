import pytest
from app.services.citation_parser import CitationParser


class TestCitationParser:
    """Tests for CitationParser service."""

    def test_extract_urls_single(self):
        """Test extracting a single URL."""
        text = "Check out https://example.com for more info."
        urls = CitationParser.extract_urls(text)
        assert urls == ["https://example.com"]

    def test_extract_urls_multiple(self):
        """Test extracting multiple URLs."""
        text = "Visit https://site1.com or https://site2.com/page"
        urls = CitationParser.extract_urls(text)
        assert len(urls) == 2
        assert "https://site1.com" in urls
        assert "https://site2.com/page" in urls

    def test_extract_urls_empty(self):
        """Test with no URLs."""
        text = "No URLs here"
        urls = CitationParser.extract_urls(text)
        assert urls == []

    def test_extract_domain_simple(self):
        """Test domain extraction."""
        domain = CitationParser.extract_domain("https://example.com/page")
        assert domain == "example.com"

    def test_extract_domain_with_www(self):
        """Test domain extraction removes www."""
        domain = CitationParser.extract_domain("https://www.example.com/page")
        assert domain == "example.com"

    def test_extract_domain_subdomain(self):
        """Test domain extraction with subdomain."""
        domain = CitationParser.extract_domain("https://blog.example.com/post")
        assert domain == "blog.example.com"

    def test_extract_domain_au(self):
        """Test Australian domain extraction."""
        domain = CitationParser.extract_domain("https://www.sportsbet.com.au/racing")
        assert domain == "sportsbet.com.au"

    def test_classify_page_type_homepage(self):
        """Test homepage classification."""
        assert CitationParser.classify_page_type("https://example.com") == "homepage"
        assert CitationParser.classify_page_type("https://example.com/") == "homepage"

    def test_classify_page_type_article(self):
        """Test article classification."""
        assert CitationParser.classify_page_type("https://site.com/blog/post-title") == "article"
        assert CitationParser.classify_page_type("https://site.com/news/story") == "article"

    def test_classify_page_type_review(self):
        """Test review classification."""
        assert CitationParser.classify_page_type("https://site.com/review/product") == "review"
        assert CitationParser.classify_page_type("https://site.com/reviews/app") == "review"

    def test_classify_page_type_odds(self):
        """Test odds page classification."""
        assert CitationParser.classify_page_type("https://betting.com/odds/afl") == "odds"
        assert CitationParser.classify_page_type("https://site.com/betting-odds/nrl") == "odds"

    def test_classify_page_type_unknown(self):
        """Test unknown page type."""
        assert CitationParser.classify_page_type("https://site.com/random/path") is None

    def test_extract_snippet(self):
        """Test snippet extraction."""
        text = "Before text. Check this https://example.com for info. After text."
        snippet = CitationParser.extract_snippet(text, "https://example.com", context_chars=20)
        assert "https://example.com" in snippet
        assert snippet.startswith("...")

    def test_parse_response(self):
        """Test full response parsing."""
        text = """Here are the best betting sites:
        1. https://sportsbet.com.au - Great for AFL
        2. https://www.bet365.com.au/odds/nrl - Good for NRL
        3. https://tab.com.au - Racing specialist
        """
        citations = CitationParser.parse_response(text)

        assert len(citations) == 3
        assert citations[0]['domain'] == "sportsbet.com.au"
        assert citations[0]['position'] == 1
        assert citations[1]['domain'] == "bet365.com.au"
        assert citations[1]['page_type'] == "odds"
        assert citations[2]['domain'] == "tab.com.au"

    def test_parse_response_deduplicates(self):
        """Test that duplicate URLs are removed."""
        text = "Visit https://example.com then https://example.com again"
        citations = CitationParser.parse_response(text)
        assert len(citations) == 1

    def test_parse_web_search_annotations(self):
        """Test parsing web search annotations."""
        annotations = [
            {'type': 'url_citation', 'url': 'https://example.com', 'title': 'Example'},
            {'type': 'url_citation', 'url': 'https://other.com/review/page', 'title': 'Review'},
            {'type': 'other', 'data': 'ignored'},
        ]
        citations = CitationParser.parse_web_search_annotations(annotations)

        assert len(citations) == 2
        assert citations[0]['domain'] == 'example.com'
        assert citations[0]['snippet'] == 'Example'
        assert citations[1]['page_type'] == 'review'
