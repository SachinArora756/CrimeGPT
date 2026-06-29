from sentence_transformers import SentenceTransformer

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return _model


async def get_embedding(text: str) -> list[float]:
    model = get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32)
    return embeddings.tolist()
