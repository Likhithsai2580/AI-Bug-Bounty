import faiss
import numpy as np
import logging

logger = logging.getLogger(__name__)

class VectorDB:
    def __init__(self, dimension):
        logger.debug(f"Initializing VectorDB with dimension: {dimension}")
        self.index = faiss.IndexFlatL2(dimension)
        self.data = []
        logger.debug("VectorDB initialized")

    def add(self, vector, metadata):
        logger.debug(f"Adding vector with metadata: {metadata}")
        self.index.add(np.array([vector], dtype=np.float32))
        self.data.append(metadata)
        logger.debug(f"Vector added. Total vectors: {len(self.data)}")

    def search(self, query_vector, k=1):
        logger.debug(f"Searching for {k} nearest neighbors")
        distances, indices = self.index.search(np.array([query_vector], dtype=np.float32), k)
        logger.debug(f"Search completed. Distances: {distances}, Indices: {indices}")
        results = [self.data[i] for i in indices[0]]
        logger.debug(f"Returning search results: {results}")
        return results