import logging
import numpy as np
from openai import AsyncOpenAI
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

client = AsyncOpenAI(api_key=settings.openai_api_key)


async def embed_text(text: str) -> list[float]:
    """Embed a single text string."""
    response = await client.embeddings.create(
        model=settings.openai_embedding_model,
        input=text.replace("\n", " "),
    )
    return response.data[0].embedding


async def embed_texts(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    """Embed a list of texts in batches."""
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i: i + batch_size]
        cleaned = [t.replace("\n", " ") for t in batch]

        response = await client.embeddings.create(
            model=settings.openai_embedding_model,
            input=cleaned,
        )
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)
        logger.info(f"Embedded batch {i // batch_size + 1} ({len(batch)} texts)")

    return all_embeddings


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec_a)
    b = np.array(vec_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))
