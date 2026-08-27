import tiktoken
import re
from typing import List, Dict, Tuple

class TextChunker:
    def __init__(self, model_name: str = "cl100k_base", chunk_size: int = 1000, overlap: int = 2):
        """
        Initialize the chunker with token counting capability
        
        Args:
            model_name: Encoding model for token counting (cl100k_base for GPT-4, p50k_base for GPT-3)
            chunk_size: Maximum tokens per chunk
            overlap: Number of tokens to overlap between chunks
        """
        self.model_name = model_name
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.encoding = tiktoken.get_encoding(model_name)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if not text or not text.strip():
            return 0
        return len(self.encoding.encode(text))
    
    def split_by_sentences(self, text: str) -> List[str]:
        """Split text into sentences while preserving meaning"""
        # Enhanced sentence splitting pattern
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(sentence_pattern, text)
        
        # Clean and filter sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def split_by_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs"""
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        return paragraphs

    def chunk_text(self, text: str) -> List[Dict]:
        """
        Chunk text into manageable pieces with overlap

        If a paragraph exceeds chunk size, it is further split by sentences. It doesn't split sentences.
        So, if a single sentence exceeds chunk size, it will not be split and will exceed the chunk size.
        """
        if not text or not text.strip():
            return []
        
        # If text is already within chunk size, return as a single chunk
        if self.count_tokens(text) <= self.chunk_size:
            return [self._create_chunk_dict(text.strip(), 0, self.count_tokens(text.strip()))]
        
        paragraphs = self.split_by_paragraphs(text)
        chunks = []
        current_chunk = ""
        current_tokens = 0
        chunk_id = 0

        for paragraph in paragraphs:
            paragraph_tokens = self.count_tokens(paragraph)

            # if a single paragraph exceeds chunk size, split it by sentences
            if paragraph_tokens > self.chunk_size:
                sentences = self.split_by_sentences(paragraph)

                for sentence in sentences:
                    sentence_tokens = self.count_tokens(sentence)

                    if current_tokens + sentence_tokens <= self.chunk_size:
                        current_chunk += (" " if current_chunk else "") + sentence
                        current_tokens += sentence_tokens
                    else:
                        if current_chunk.strip():
                            if chunks:
                                current_chunk, current_tokens = self._add_overlap(chunks[-1]['text'], current_chunk)
                            chunks.append(self._create_chunk_dict(current_chunk, chunk_id, current_tokens))
                            chunk_id += 1

                        current_chunk = sentence
                        current_tokens = sentence_tokens
                        
                if current_chunk.strip():
                    if chunks:
                        current_chunk, current_tokens = self._add_overlap(chunks[-1]['text'], current_chunk)
                    chunks.append(self._create_chunk_dict(current_chunk, chunk_id, current_tokens))
                    chunk_id += 1
                    current_chunk = ""
                    current_tokens = 0

            elif paragraph_tokens + current_tokens <= self.chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + paragraph
                current_tokens += paragraph_tokens
            else:
                if current_chunk.strip():
                    if chunks:
                        current_chunk, current_tokens = self._add_overlap(chunks[-1]['text'], current_chunk)
                    chunks.append(self._create_chunk_dict(current_chunk, chunk_id, current_tokens))
                    chunk_id += 1

                current_chunk = paragraph
                current_tokens = paragraph_tokens

        if current_chunk.strip():
            if chunks:
                current_chunk, current_tokens = self._add_overlap(chunks[-1]['text'], current_chunk)
            chunks.append(self._create_chunk_dict(current_chunk, chunk_id, current_tokens))

        return chunks

    def _add_overlap(self, previous_chunk: str, current_chunk: str) -> Tuple[str, int]:
        """Add overlap to the current chunk"""
        if not previous_chunk or not previous_chunk.strip():
            return current_chunk, self.count_tokens(current_chunk)
        
        sentences = self.split_by_sentences(previous_chunk)
        overlap_sentences = sentences[-self.overlap:] if sentences else []

        if not overlap_sentences:
            return current_chunk, self.count_tokens(current_chunk)

        overlap_text = " ".join(sentence.strip() for sentence in overlap_sentences)
        new_chunk = (overlap_text + " " + current_chunk).strip()
        new_chunk_tokens = self.count_tokens(new_chunk)
        return new_chunk, new_chunk_tokens
    
    def _create_chunk_dict(self, text: str, chunk_id: int, token_count: int) -> Dict:
        """Create a structured chunk dictionary"""
        return {
            'chunk_id': chunk_id,
            'text': text,
            'token_count': token_count,
        }