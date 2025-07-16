import logging
from typing import List, Optional, Dict, Any, Literal
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
from langchain.embeddings.base import Embeddings

logger = logging.getLogger(__name__)


class HugginFaceEmbedding(Embeddings):
    """
    HugginFace embedding model for LangChain.
    """

    def __init__(
            self,
            model_name: str = "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext",
            device: Literal['auto', 'cuda', 'mps', 'cpu'] = "auto",
            max_length: int = 512,
            batch_size: int = 32,
            normalize_embeddings: bool = True,
            pooling_strategy: Literal['cls', 'mean', 'max', 'mean_max'] = "cls",
            model_kwargs: Optional[Dict[str, Any]] = None,
            tokenizer_kwargs: Optional[Dict[str, Any]] = None,
            **kwargs
    ):
        """
        Args:
            model_name: Model name to use for embeddings
            device: Device to run the model on ('cpu', 'cuda', 'auto')
            max_length: Maximum sequence length for tokenization
            batch_size: Batch size for processing multiple texts
            normalize_embeddings: Whether to normalize embeddings to unit length
            model_kwargs: Additional arguments to pass to the model
            tokenizer_kwargs: Additional arguments to pass to the tokenizer
        """
        super().__init__(**kwargs)

        self.model_name = model_name
        self.max_length = max_length
        self.batch_size = batch_size
        self.normalize_embeddings = normalize_embeddings
        self.model_kwargs = model_kwargs or {}
        self.tokenizer_kwargs = tokenizer_kwargs or {}
        self._device = device

        self.pooling_strategy = pooling_strategy

        # Validate pooling strategy
        valid_strategies = ["cls", "mean", "max", "mean_max"]
        if pooling_strategy not in valid_strategies:
            raise ValueError(f"Invalid pooling strategy. Must be one of: {valid_strategies}")


        # Load model and tokenizer
        self._load_model()

    def _load_model(self):
        """Load the Specter2 model and tokenizer."""
        try:
            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                **self.tokenizer_kwargs
            )

            # Load model
            self._model = AutoModel.from_pretrained(
                self.model_name,
                **self.model_kwargs
            )

            self._model.to(self.device)
            self._model.eval()

            logger.info(f"Loaded Specter2 model '{self.model_name}' on device '{self.device}'")

        except Exception as e:
            raise RuntimeError(f"Failed to load Specter2 model: {str(e)}")

    @property
    def device(self):
        if self._device != "auto":
            return torch.device(self._device)

        if torch.cuda.is_available():
            return torch.device("cuda")
        elif torch.backends.mps.is_available():
            return torch.device("mps")
        else:
            return torch.device("cpu")

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for a list of texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings as lists of floats
        """
        all_embeddings = []

        # Process texts in batches
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            batch_embeddings = self._embed_batch(batch_texts)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a batch of texts with advanced pooling strategies.

        Args:
            texts: Batch of texts to embed

        Returns:
            List of embeddings for the batch
        """
        # Tokenize texts
        inputs = self._tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt"
        )

        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Get embeddings
        with torch.no_grad():
            outputs = self._model(**inputs)
            hidden_states = outputs.last_hidden_state
            attention_mask = inputs["attention_mask"]

            # Apply different pooling strategies
            if self.pooling_strategy == "cls":
                embeddings = hidden_states[:, 0, :]
            elif self.pooling_strategy == "mean":
                embeddings = self._mean_pooling(hidden_states, attention_mask)
            elif self.pooling_strategy == "max":
                embeddings = self._max_pooling(hidden_states, attention_mask)
            elif self.pooling_strategy == "mean_max":
                mean_emb = self._mean_pooling(hidden_states, attention_mask)
                max_emb = self._max_pooling(hidden_states, attention_mask)
                embeddings = torch.cat([mean_emb, max_emb], dim=1)

            # Normalize if requested
            if self.normalize_embeddings:
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

            # Convert to numpy and then to lists
            embeddings_np = embeddings.cpu().numpy()

        return embeddings_np.tolist()

    def _mean_pooling(self, hidden_states: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """Apply mean pooling to hidden states."""
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(hidden_states.size()).float()
        return torch.sum(hidden_states * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    def _max_pooling(self, hidden_states: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """Apply max pooling to hidden states."""
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(hidden_states.size()).float()
        hidden_states[input_mask_expanded == 0] = -1e9  # Set padding tokens to large negative value
        return torch.max(hidden_states, 1)[0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents.

        Args:
            texts: List of documents to embed

        Returns:
            List of embeddings, one for each document
        """
        logger.debug(f"Embedding {len(texts)} documents")
        return self._get_embeddings(texts)

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query text.

        Args:
            text: Query text to embed

        Returns:
            Embedding as a list of floats
        """
        logger.debug("Embedding query")
        return self._get_embeddings([text])[0]

    def similarity_search_with_score(
            self,
            query: str,
            documents: List[str],
            k: int = 16
    ) -> List[tuple]:
        """
        Perform similarity search with scores.

        Args:
            query: Query text
            documents: List of documents to search
            k: Number of top results to return

        Returns:
            List of (document, score) tuples
        """
        # Get embeddings
        query_embedding = self.embed_query(query)
        doc_embeddings = self.embed_documents(documents)

        # Calculate cosine similarities
        query_embedding = np.array(query_embedding)
        doc_embeddings = np.array(doc_embeddings)

        # Normalize if not already normalized
        if not self.normalize_embeddings:
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
            doc_embeddings = doc_embeddings / np.linalg.norm(doc_embeddings, axis=1, keepdims=True)

        # Calculate similarities
        similarities = np.dot(doc_embeddings, query_embedding)

        # Get top k results
        top_indices = np.argsort(similarities)[::-1][:k]

        results = []
        for idx in top_indices:
            results.append((documents[idx], float(similarities[idx])))

        return results

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.

        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.model_name,
            "device": self.device,
            "max_length": self.max_length,
            "batch_size": self.batch_size,
            "normalize_embeddings": self.normalize_embeddings,
            "embedding_dimension": self._model.config.hidden_size if self._model else None,
            "vocabulary_size": self._tokenizer.vocab_size if self._tokenizer else None,
        }




# Example usage and testing
if __name__ == "__main__":
    # Sample scientific texts
    sample_texts = [
        "Deep learning models have revolutionized natural language processing tasks.",
        "Transformers architecture has become the foundation of modern NLP systems.",
        "BERT and GPT models represent significant advances in language understanding.",
        "Computer vision applications benefit from convolutional neural networks.",
        "Quantum computing promises to solve complex optimization problems.",
    ]

    # Test basic Specter2 embeddings
    print("Testing Specter2Embeddings...")
    embeddings = HugginFaceEmbedding(
        batch_size=2,
        max_length=256
    )

    # Test embedding documents
    doc_embeddings = embeddings.embed_documents(sample_texts)
    print(f"Document embeddings shape: {len(doc_embeddings)} x {len(doc_embeddings[0])}")

    # Test embedding query
    query = "What are the latest advances in neural networks?"
    query_embedding = embeddings.embed_query(query)
    print(f"Query embedding shape: {len(query_embedding)}")

    # Test similarity search
    results = embeddings.similarity_search_with_score(query, sample_texts, k=3)
    print("Top 3 similar documents:")
    for doc, score in results:
        print(f"  Score: {score:.4f} - {doc}")

    # Display model info
    print("\nModel Information:")
    info = embeddings.get_model_info()
    for key, value in info.items():
        print(f"  {key}: {value}")

    # Test advanced embeddings
    print("\nTesting Advanced Embeddings with mean pooling...")
    advanced_embeddings = HugginFaceEmbedding(
        pooling_strategy="mean",
        batch_size=2
    )

    advanced_query_embedding = advanced_embeddings.embed_query(query)
    print(f"Advanced query embedding shape: {len(advanced_query_embedding)}")