"""crewai-turnstile: a CrewAI Tool for solving Cloudflare Turnstile via Peak.

Public API::

    from crewai_turnstile import PeakTurnstileTool
    tool = PeakTurnstileTool(api_key="pk_...")
    token = tool.run(url="https://example.com/login", sitekey="0x...")
"""

from __future__ import annotations

from .inject import INJECT_TOKEN_JS, build_injection_script
from .peak import (
    DEFAULT_API_URL,
    TASK_TURNSTILE,
    TASK_TURNSTILE_PROXYLESS,
    PeakClient,
    PeakError,
    build_solve_payload,
)
from .tool import PeakTurnstileTool, TurnstileInput

__version__ = "0.1.1"

__all__ = [
    "PeakTurnstileTool",
    "TurnstileInput",
    "PeakClient",
    "PeakError",
    "build_solve_payload",
    "build_injection_script",
    "INJECT_TOKEN_JS",
    "DEFAULT_API_URL",
    "TASK_TURNSTILE",
    "TASK_TURNSTILE_PROXYLESS",
    "__version__",
]
