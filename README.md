<div align="center">

# crewai-turnstile

**Give a CrewAI agent the ability to solve Cloudflare Turnstile.** A `BaseTool` that takes a page URL and a sitekey, calls [Peak](https://peak.fo), and hands back a token. A crew that browses the web and hits a Turnstile challenge gets a move to make instead of getting stuck.

<p>
  <img src="https://img.shields.io/badge/python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/crewai-tool-FF5A1F?style=for-the-badge" alt="crewai tool">
  <img src="https://img.shields.io/badge/license-MIT-007EC7?style=for-the-badge" alt="MIT License">
</p>

</div>

---

A crew that browses the web eventually runs into Cloudflare Turnstile. The widget needs a token minted server-side. No fingerprint, proxy, or retry loop gets around that; it's a missing capability, not a detection problem. This package is that capability, packaged as a CrewAI `BaseTool`: give it a URL and a sitekey, it returns a token.

The tool itself never touches a browser. It is pure request/response to the Peak API, which keeps it usable from any crew regardless of whether its agents are driving Playwright, Selenium, a raw HTTP client, or nothing at all. Pair it with whatever tool your agent already uses to read the DOM (to get the sitekey) and to run JS (to put the token back); see [Closing the loop](#closing-the-loop) below.

## Install

```bash
pip install crewai-turnstile
```

## Use it

```python
from crewai_turnstile import PeakTurnstileTool

tool = PeakTurnstileTool(api_key="pk_...")  # or set PEAK_API_KEY
token = tool.run(url="https://example.com/login", sitekey="0x4AAAAAAA...")
```

Hand it to an agent like any other tool:

```python
from crewai import Agent
from crewai_turnstile import PeakTurnstileTool

agent = Agent(
    role="Web researcher",
    goal="Fetch pages and clear any Turnstile challenge blocking them",
    backstory="You browse pages via tools and solve Turnstile when it blocks one.",
    tools=[*your_browser_tools, PeakTurnstileTool(api_key=api_key)],
)
```

The agent decides when to call it, typically after a browsing tool reports it's stuck on a Cloudflare challenge. The tool's `description` is written for that: an LLM reading the tool list will reach for `solve_cloudflare_turnstile` when it sees a Turnstile widget blocking a page.

## Closing the loop

Reading the sitekey and injecting the token both happen on a live page, which is specific to whatever browser your crew drives, so this package deliberately doesn't pick one for you. `inject.py` ships the JS every other Peak wrapper package uses, so you can call it from whichever `execute_script` / `page.evaluate` your stack exposes:

```python
from crewai_turnstile import build_injection_script

page.evaluate(build_injection_script(token))          # Playwright
driver.execute_script(build_injection_script(token))  # Selenium
```

It fills every `cf-turnstile-response` field and fires the widget's `data-callback` if the page registered one, the same two places a real form submit reads from.

## Matching the exit IP

Turnstile scores the IP that submits the token. If your agent's browser runs behind a proxy, pass the same one so the token and the request line up:

```python
tool.run(url=url, sitekey=sitekey, proxy="http://user:pass@host:port")
```

Leave `proxy` out and the tool solves through Peak's own IP pool instead. Fine for most sites, wrong for the ones that bind the token to the requesting IP.

## Errors come back as text, not exceptions

A tool-calling agent works better when a failure is something it can read and react to, rather than a crash that kills the run. `PeakTurnstileTool` returns `"ERROR: <reason>"` (bad sitekey, no balance, no key configured) instead of raising, so the agent's next step can be "try a different sitekey" rather than "the whole crew run died." Call `PeakClient.solve()` directly from `crewai_turnstile.peak` if you want exceptions instead.

## Getting a key

The tool needs an API key for the solver it calls: [Peak](https://peak.fo). Turnstile solves come back in about a second. You pay $0.90 per 1,000 successful solves, down to $0.35 at volume, and only for the ones that land — failed solves are free. The free trial gives you roughly 1,000 solves to wire this up and test it end to end.

<div align="center">

For **Cloudflare Turnstile**, **Cloudflare 5s challenge**, **AWS WAF**, and **DataDome**:
<br>
<a href="https://peak.fo"><img src="https://img.shields.io/badge/Get_a_key-Peak-FF6B35?style=for-the-badge" alt="Peak"></a>
<br>
<sub>API-first · <strong>$0.35 – $0.90 / 1K</strong> · volume tiers · pay only on success · <a href="https://peak.fo">peak.fo</a></sub>

</div>

## Related

Same pattern for driving an agent framework directly: [langchain-turnstile](https://github.com/CircuitSavage/langchain-turnstile). For driving a browser without an agent on top: [playwright-turnstile](https://github.com/CircuitSavage/playwright-turnstile) · [selenium-turnstile](https://github.com/CircuitSavage/selenium-turnstile) · [puppeteer-extra-plugin-turnstile](https://github.com/CircuitSavage/puppeteer-extra-plugin-turnstile) · [camoufox-turnstile](https://github.com/CircuitSavage/camoufox-turnstile).

## Notes

Use this on sites and accounts you're allowed to automate. Respect each target's Terms of Service and `robots.txt`. This is tooling for legitimate agents, testing, and public-data access. Nothing here helps with credential stuffing or abuse. Not affiliated with Cloudflare or CrewAI Inc.

## License

MIT
