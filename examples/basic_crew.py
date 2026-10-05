"""Give a CrewAI agent the ability to solve a Turnstile it hits.

    pip install crewai-turnstile crewai
    export PEAK_API_KEY=pk_xxx
    export OPENAI_API_KEY=sk_xxx
    python examples/basic_crew.py

This pairs the solver tool with a plain "fetch a page" tool so the agent
can read a sitekey off the HTML itself, call solve_cloudflare_turnstile,
then use the returned token however the rest of its flow needs it (a real
crew would likely pair this with a browser toolkit instead of fetch, so it
can also inject the token back into a live page — see inject.py).
"""

import os
import re

import httpx
from crewai import Agent, Crew, Task
from crewai.tools import BaseTool

from crewai_turnstile import PeakTurnstileTool


class FetchPageTool(BaseTool):
    name: str = "fetch_page"
    description: str = "Fetch a URL and return its raw HTML."

    def _run(self, url: str) -> str:
        resp = httpx.get(url, timeout=20, follow_redirects=True)
        return resp.text[:4000]


class FindSitekeyTool(BaseTool):
    name: str = "find_turnstile_sitekey"
    description: str = "Pull a Turnstile sitekey out of raw HTML, if one is present."

    def _run(self, html: str) -> str:
        match = re.search(r'data-sitekey="([^"]+)"', html)
        return match.group(1) if match else "no sitekey found on that page"


def main() -> None:
    solver = PeakTurnstileTool(api_key=os.environ["PEAK_API_KEY"])

    agent = Agent(
        role="Web researcher",
        goal="Fetch pages and clear any Cloudflare Turnstile challenge blocking them",
        backstory=(
            "You browse pages via tools, and when a Turnstile widget blocks "
            "one you solve it instead of giving up."
        ),
        tools=[FetchPageTool(), FindSitekeyTool(), solver],
        verbose=True,
    )

    task = Task(
        description=(
            "Fetch https://demo.turnstile.workers.dev/, find its Turnstile "
            "sitekey, and solve the challenge for that URL. Report the "
            "token you get back."
        ),
        expected_output="The solved Turnstile token string.",
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task])
    result = crew.kickoff()
    print(result)


if __name__ == "__main__":
    main()
