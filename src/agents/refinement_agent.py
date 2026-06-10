from __future__ import annotations

import re


class RefinementAgent:
    def refine(self, draft_text: str) -> str:
        text = draft_text.replace("  ", " ")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.replace("This branch is currently under-populated in the extracted corpus and should be treated as an emerging trend.", "This branch remains relatively small in the current corpus and should be interpreted as an emerging trend rather than a fully mature family.")
        return text.strip() + "\n"
