import os
from pathlib import Path
from typing import Dict, Optional

PROMPTS_DIR = Path(__file__).parent


class PromptLoader:
    """Utility service for loading versioned prompt templates and injecting runtime variables."""

    @staticmethod
    def load_prompt(agent_name: str, version: str = "v1", variables: Optional[Dict[str, str]] = None) -> str:
        """
        Loads a versioned text prompt template from disk for the specified agent persona.
        Substitutes double-curly-brace placeholder tags ({{variable}}) with provided variable mappings.
        """
        prompt_path = PROMPTS_DIR / agent_name / f"{version}.txt"
        if not prompt_path.exists():
            # Fallback default prompt template
            content = f"Execute GTM task for {agent_name} with parameters: " + str(variables)
        else:
            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read()

        if variables:
            for key, val in variables.items():
                content = content.replace(f"{{{{{key}}}}}", str(val))
        return content


prompt_loader = PromptLoader()
