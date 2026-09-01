import tiktoken
import re
from typing import List, Dict, Tuple


class TextChunker:
    def __init__(
        self, model_name: str = "cl100k_base", chunk_size: int = 1000, overlap: int = 2
    ):
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
        """Split text into individual sentence/content units."""

        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Markdown headings / bold sections are boundaries
        text = re.sub(r"\s+(?=#{1,6}\s+)", "\n", text)
        text = re.sub(r"\s+(?=\*\*[^*]+\*\*)", "\n", text)

        # Normalize spaces but preserve newlines
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{2,}", "\n", text).strip()

        result = []

        for line in text.split("\n"):
            line = line.strip()
            
            if not line:
                continue

            # Split normal sentences inside this line
            parts = re.split(
                r'(?<=[.!?])(?:["\')\]]+)?\s+(?=[A-Z0-9])',
                line
            )

            for i, part in enumerate(parts):
                part = part.strip()

                if not part:
                    continue

                if i == 0:
                    part = "\n" + part

                result.append(part)

        return result

    def split_by_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs"""
        paragraphs = re.split(r"\n\s*\n", text)
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
            return [
                self._create_chunk_dict(
                    text.strip(), 0, self.count_tokens(text.strip())
                )
            ]

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
                                current_chunk, current_tokens = self._add_overlap(
                                    chunks[-1]["text"], current_chunk
                                )
                            chunks.append(
                                self._create_chunk_dict(
                                    current_chunk, chunk_id, current_tokens
                                )
                            )
                            chunk_id += 1

                        current_chunk = sentence
                        current_tokens = sentence_tokens

                if current_chunk.strip():
                    if chunks:
                        current_chunk, current_tokens = self._add_overlap(
                            chunks[-1]["text"], current_chunk
                        )
                    chunks.append(
                        self._create_chunk_dict(current_chunk, chunk_id, current_tokens)
                    )
                    chunk_id += 1
                    current_chunk = ""
                    current_tokens = 0

            elif paragraph_tokens + current_tokens <= self.chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + paragraph
                current_tokens += paragraph_tokens
            else:
                if current_chunk.strip():
                    if chunks:
                        current_chunk, current_tokens = self._add_overlap(
                            chunks[-1]["text"], current_chunk
                        )
                    chunks.append(
                        self._create_chunk_dict(current_chunk, chunk_id, current_tokens)
                    )
                    chunk_id += 1

                current_chunk = paragraph
                current_tokens = paragraph_tokens

        if current_chunk.strip():
            if chunks:
                current_chunk, current_tokens = self._add_overlap(
                    chunks[-1]["text"], current_chunk
                )
            chunks.append(
                self._create_chunk_dict(current_chunk, chunk_id, current_tokens)
            )

        return chunks

    def _add_overlap(self, previous_chunk: str, current_chunk: str) -> Tuple[str, int]:
        """Add overlap to the current chunk"""
        if not previous_chunk or not previous_chunk.strip():
            return current_chunk, self.count_tokens(current_chunk)

        sentences = self.split_by_sentences(previous_chunk)
        overlap_sentences = sentences[-self.overlap :] if sentences else []

        if not overlap_sentences:
            return current_chunk, self.count_tokens(current_chunk)

        overlap_text = " ".join(sentence.strip() for sentence in overlap_sentences)
        new_chunk = (overlap_text + " " + current_chunk).strip()
        new_chunk_tokens = self.count_tokens(new_chunk)
        return new_chunk, new_chunk_tokens

    def _create_chunk_dict(self, text: str, chunk_id: int, token_count: int) -> Dict:
        """Create a structured chunk dictionary"""
        return {
            "chunk_id": chunk_id,
            "text": text,
            "token_count": token_count,
        }

if __name__ == "__main__":
    test_chunk = """## ENCYCLOPEDIC ENTRY Open Educational Resource. ## ENCYCLOPEDIC ENTRY # Photosynthesis # Photosynthesis Photosynthesis is the process by which plants use sunlight, water, and carbon dioxide to create oxygen and energy in the form of sugar. ### Grades 5 - 8. ### Subjects Biology. ## Learning materials Most life on Earth depends on photosynthesis.The process is carried out by plants, algae, and some types of bacteria, which capture energy from sunlight to produce oxygen (O<sub>2</sub>) and chemical energy stored in glucose (a sugar). Herbivores then obtain this energy by eating plants, and carnivores obtain it by eating herbivores. **The process** During photosynthesis, plants take in carbon dioxide (CO<sub>2</sub>) and water (H<sub>2</sub>O) from the air and soil. Within the plant cell, the water is oxidized, meaning it loses electrons, while the carbon dioxide is reduced, meaning it gains electrons. This transforms the water into oxygen and the carbon dioxide into glucose. The plant then releases the oxygen back into the air, and stores energy within the glucose molecules. **Chlorophyll** Inside the plant cell are small organelles called chloroplasts, which store the energy of sunlight. Within the thylakoid membranes of the chloroplast is a light-absorbing pigment called chlorophyll, which is responsible for giving the plant its green color. During photosynthesis, chlorophyll absorbs energy from blue- and red-light waves, and reflects green-light waves, making the plant appear green. **Light-dependent Reactions vs. Light-independent Reactions** While there are many steps behind the process of photosynthesis, it can be broken down into two major stages: light-dependent reactions and light-independent reactions. The light-dependent reaction takes place within the thylakoid membrane and requires a steady stream of sunlight, hence the name light-*dependent* reaction. The chlorophyll absorbs energy from the light waves, which is converted into chemical energy in the form of the molecules ATP and NADPH.
"""
    chunker = TextChunker(chunk_size=20, overlap=0)
    result = chunker.split_by_sentences(test_chunk)

    print(result)