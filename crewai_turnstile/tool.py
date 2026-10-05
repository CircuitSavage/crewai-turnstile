"""A CrewAI Tool that solves Cloudflare Turnstile via the Peak API.

Give a crew's agent this tool alongside a browsing toolkit (Playwright,
Selenium, a custom fetch tool, whatever reads the DOM) and it can clear a
Turnstile challenge it just ran into: read the sitekey itself, call this
tool with the (url, sitekey) pair, and get back a token to drop into the
page.

This tool does not touch a browser. It is pure request/response, which
keeps it usable from any crew regardless of which browsing stack it has
wired up. See ``inject.py`` for the DOM-injection half of the loop.
"""

from __future__ import annotations

import os
from typing import Optional, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from .peak import DEFAULT_API_URL, PeakClient, PeakError

__all__ = ["PeakTurnstileTool", "TurnstileInput"]


class TurnstileInput(BaseModel):
    url: str = Field(
        description=(
            "The full page URL the Turnstile widget is embedded on "
            "(e.g. https://example.com/login)."
        )
    )
    sitekey: str = Field(
        description=(
            "The widget's sitekey, read from the page's "
            "[data-sitekey] attribute or the challenges.cloudflare.com "
            "iframe src. Looks like 0x4AAAAAAA... or the test key "
            "1x00000000000000000000AA."
        )
    )
    proxy: Optional[str] = Field(
        default=None,
        description=(
            "Proxy URL matching the browser's exit IP, as "
            "http://user:pass@host:port. Leave unset to solve through "
            "Peak's own IP pool instead — fine for most sites, wrong for "
            "ones that bind the token to the requesting IP."
        ),
    )


class PeakTurnstileTool(BaseTool):
    """Solve a Cloudflare Turnstile challenge and return the token.

    Example:
        from crewai_turnstile import PeakTurnstileTool

        tool = PeakTurnstileTool(api_key="pk_...")
        token = tool.run(url="https://example.com/login", sitekey="0x...")

    ``api_key`` falls back to the ``PEAK_API_KEY`` environment variable.
    Pair this with a crew agent that reads the DOM (to get the sitekey) and
    :func:`crewai_turnstile.inject.build_injection_script` (to place the
    token back on the page) for a full agent loop.
    """

    name: str = "solve_cloudflare_turnstile"
    description: str = (
        "Solve a Cloudflare Turnstile challenge blocking a page. Give it the "
        "page URL and the widget's sitekey; it returns a token string to "
        "inject into the page's cf-turnstile-response field (or its "
        "data-callback) so the form or navigation can proceed. Use this "
        "when a browsing tool reports it is stuck on a Cloudflare "
        "verification / Turnstile widget."
    )
    args_schema: Type[BaseModel] = TurnstileInput

    api_key: Optional[str] = None
    api_url: str = DEFAULT_API_URL
    proxy: Optional[str] = None
    timeout: float = 180.0

    def _client(self) -> PeakClient:
        key = self.api_key or os.environ.get("PEAK_API_KEY")
        return PeakClient(key, api_url=self.api_url, proxy=self.proxy, timeout=self.timeout)

    def _run(
        self,
        url: str,
        sitekey: str,
        proxy: Optional[str] = None,
    ) -> str:
        try:
            return self._client().solve(sitekey, url, proxy=proxy)
        except PeakError as exc:
            # Returned, not raised: an agent can read "insufficient balance"
            # or "invalid sitekey" and decide what to do next, rather than
            # the whole crew run crashing on a tool-level error.
            return f"ERROR: {exc}"
