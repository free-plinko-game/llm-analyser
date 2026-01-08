import re
from urllib.parse import urlparse
from typing import List, Dict, Optional


class CitationParser:
    """Extracts and parses URLs from ChatGPT responses."""

    # Common URL patterns
    URL_PATTERN = re.compile(
        r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\-.?=&#%]*'
    )

    # Page type classification patterns
    PAGE_TYPE_PATTERNS = {
        'homepage': [r'^https?://[^/]+/?$', r'^https?://www\.[^/]+/?$'],
        'article': [r'/article/', r'/news/', r'/blog/', r'/post/'],
        'product': [r'/product/', r'/item/', r'/p/'],
        'category': [r'/category/', r'/c/', r'/topics/'],
        'review': [r'/review/', r'/reviews/'],
        'comparison': [r'/compare/', r'/vs/', r'/comparison/'],
        'guide': [r'/guide/', r'/how-to/', r'/tutorial/'],
        'odds': [r'/odds/', r'/betting-odds/', r'/markets/'],
    }

    @classmethod
    def extract_urls(cls, text: str) -> List[str]:
        """Extract all URLs from text."""
        if not text:
            return []
        return cls.URL_PATTERN.findall(text)

    @classmethod
    def extract_domain(cls, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove www. prefix for consistency
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain.lower()
        except Exception:
            return ''

    @classmethod
    def classify_page_type(cls, url: str) -> Optional[str]:
        """Classify the type of page based on URL patterns."""
        url_lower = url.lower()

        for page_type, patterns in cls.PAGE_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    return page_type

        return None

    @classmethod
    def extract_snippet(cls, text: str, url: str, context_chars: int = 200) -> Optional[str]:
        """Extract text snippet around a URL citation."""
        if not text or not url:
            return None

        idx = text.find(url)
        if idx == -1:
            return None

        start = max(0, idx - context_chars)
        end = min(len(text), idx + len(url) + context_chars)

        snippet = text[start:end].strip()
        if start > 0:
            snippet = '...' + snippet
        if end < len(text):
            snippet = snippet + '...'

        return snippet

    @classmethod
    def parse_response(cls, response_text: str) -> List[Dict]:
        """
        Parse a ChatGPT response and extract citation data.

        Returns list of dicts with keys: url, domain, page_type, position, snippet
        """
        urls = cls.extract_urls(response_text)
        citations = []
        seen_urls = set()

        for position, url in enumerate(urls, start=1):
            # Skip duplicate URLs in same response
            if url in seen_urls:
                continue
            seen_urls.add(url)

            domain = cls.extract_domain(url)
            if not domain:
                continue

            citations.append({
                'url': url,
                'domain': domain,
                'page_type': cls.classify_page_type(url),
                'position': position,
                'snippet': cls.extract_snippet(response_text, url)
            })

        return citations

    @classmethod
    def parse_web_search_annotations(cls, annotations: List[Dict]) -> List[Dict]:
        """
        Parse citations from OpenAI web search annotations.

        The responses API returns structured annotations when web_search is used.
        """
        citations = []
        seen_urls = set()

        for position, annotation in enumerate(annotations, start=1):
            if annotation.get('type') != 'url_citation':
                continue

            url = annotation.get('url', '')
            if not url or url in seen_urls:
                continue

            seen_urls.add(url)
            domain = cls.extract_domain(url)
            if not domain:
                continue

            citations.append({
                'url': url,
                'domain': domain,
                'page_type': cls.classify_page_type(url),
                'position': position,
                'snippet': annotation.get('title', '')
            })

        return citations
