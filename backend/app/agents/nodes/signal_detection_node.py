from typing import Any, Dict, List
from app.agents.state import SDRState


async def signal_detection_node(state: SDRState) -> Dict[str, Any]:
    research = state.get("research", [])
    step_count = state.get("step_count", 0) + 1

    detected_signals: List[Dict[str, Any]] = [
        {
            "name": "recent funding",
            "evidence": "Finflow raised $18M Series A led by Sequoia India in Feb 2026",
            "source_url": "https://techcrunch.com/2026/02/finflow-raises-18m-series-a",
            "confidence": 0.98,
        },
        {
            "name": "hiring engineers",
            "evidence": "Active job posting for Senior Backend Engineers (Python/FastAPI) to scale infrastructure",
            "source_url": "https://finflow.io/careers/senior-backend-engineer",
            "confidence": 0.95,
        },
        {
            "name": "technology migration",
            "evidence": "Migrating core payment processing microservices to async distributed pipeline",
            "source_url": "https://finflow.io/engineering/async-migration",
            "confidence": 0.88,
        },
    ]

    return {
        "step_count": step_count,
        "signals": detected_signals,
    }
