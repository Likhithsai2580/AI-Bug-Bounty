import faiss
import numpy as np

class VectorDB:
    def __init__(self, dimension):
        self.index = faiss.IndexFlatL2(dimension)
        self.data = []

    def add(self, vector, metadata):
        self.index.add(np.array([vector], dtype=np.float32))
        self.data.append(metadata)

    def search(self, query_vector, k=1):
        distances, indices = self.index.search(np.array([query_vector], dtype=np.float32), k)
        return [self.data[i] for i in indices[0]]