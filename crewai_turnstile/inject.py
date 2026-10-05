"""The DOM-injection half of the loop: put a solved token back on the page.

``PeakTurnstileTool`` only talks to the Peak API — it has no browser
dependency, so it works the same way regardless of which browsing stack a
crew's agent drives (Playwright, Selenium, a custom one). This module holds
the JS that every one of Peak's other wrapper packages uses to place the
token: fill every ``cf-turnstile-response`` field and fire the widget's
``data-callback`` if the page wired one up. Call it yourself with whatever
``execute_script`` / ``page.evaluate`` your browsing tool exposes.
"""

from __future__ import annotations

import json

# Sets every cf-turnstile-response field, dispatches input/change so
# listeners react, and calls the widget's data-callback if present. Returns
# True if it found somewhere to put the token.
INJECT_TOKEN_JS = r"""
(function (token) {
  var fields = document.querySelectorAll(
    'input[name="cf-turnstile-response"], textarea[name="cf-turnstile-response"]'
  );
  fields.forEach(function (f) {
    f.value = token;
    f.dispatchEvent(new Event('input', { bubbles: true }));
    f.dispatchEvent(new Event('change', { bubbles: true }));
  });
  var called = false;
  document.querySelectorAll('[data-callback]').forEach(function (w) {
    var name = w.getAttribute('data-callback');
    if (name && typeof window[name] === 'function') {
      window[name](token);
      called = true;
    }
  });
  return fields.length > 0 || called;
})
"""


def build_injection_script(token: str) -> str:
    """Return a ready-to-evaluate JS expression that injects ``token``.

    Works with Playwright's ``page.evaluate(script)`` (no args form) and
    Selenium's ``driver.execute_script(script)`` alike, since both accept a
    full expression string::

        page.evaluate(build_injection_script(token))          # Playwright
        driver.execute_script(build_injection_script(token))  # Selenium
    """
    return f"({INJECT_TOKEN_JS})({json.dumps(token)})"
