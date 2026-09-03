import tiktoken
import re
from inspect import cleandoc
from typing import List, Dict
from marko.ext.gfm import GFM
from marko import Markdown

MARKDOWN_PATTERNS = [
    re.compile(r"^#{1,6}\s"),  # heading
    re.compile(r"^\s*[-*+]\s+"),  # bullet list
    re.compile(r"^\s*\d+\.\s+"),  # numbered list
    re.compile(r"^\s*>"),  # blockquote
    re.compile(r"^\s*\|.*\|\s*$"),  # table row
]

CODE_PATTERNS = [
    re.compile(
        r"^\s*(import|from|def|class|function|const|let|var|return|export|async|await)\b"
    ),
    re.compile(r"^\s*(if|elif|else|for|while|switch)\b.*[:{]"),
    re.compile(r"^\s*(pip|python|node|npm|yarn|git|docker)\b"),
    re.compile(r"[{};]\s*$"),
    re.compile(r"\w+\([^)]*\)"),
    re.compile(r"^\s*//"),
    re.compile(r"^\s*/\*"),
]


def is_it_code(text: str) -> bool:
    text = text.strip()

    if not text:
        return False

    # If it still has fences, it is code.
    if text.startswith("```") or text.startswith("~~~"):
        return True

    lines = [line.rstrip() for line in text.splitlines() if line.strip()]

    if not lines:
        return False

    markdown_lines = 0
    code_lines = 0

    for line in lines:
        if any(pattern.search(line) for pattern in MARKDOWN_PATTERNS):
            markdown_lines += 1

        if any(pattern.search(line) for pattern in CODE_PATTERNS):
            code_lines += 1

    # It is not a code if it has more than 2 markdown lines
    if markdown_lines >= 2 and markdown_lines >= code_lines:
        return False

    if code_lines > 0:
        return True

    # Natural language usually has many words and few symbols.
    words = len(re.findall(r"\b[\w'-]+\b", text))
    symbols = len(re.findall(r"[{}()\[\];=<>]", text))

    symbol_ratio = symbols / max(words, 1)

    # If there more more symbols than words then its a code.
    if symbol_ratio >= 0.10:
        return True

    # If there are more words than symbols then its a natural language.
    if words > 25 and symbol_ratio < 0.04:
        return False

    return True


class TextChunker:
    def __init__(self, model_name: str = "cl100k_base", chunk_size: int = 1000):
        self.model_name = model_name
        self.chunk_size = chunk_size
        self.encoding = tiktoken.get_encoding(model_name)

        self.parser = Markdown(extensions=[GFM])

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text using the specified encoding. For code and table blocks, count them as 1 token each."""
        if not text or not text.strip():
            return 0
        token_size = 0
        text = cleandoc(text).strip()
        blocks = self.split_blocks(text)
        for block in blocks:
            if block["type"] in ["code", "table"]:
                token_size += 1
            else:
                token_size += len(self.encoding.encode(block["text"]))
        return token_size

    def split_blocks(self, text: str) -> List[Dict]:
        text = cleandoc(text).strip()
        doc = self.parser.parse(text)

        blocks = []
        type_mapping = {
            "Paragraph": "p",
            "Heading": "heading",
            "Table": "table",
            "List": "list",
            "CodeBlock": "code",
            "FencedCode": "code",
            "Quote": "blockquote",
        }

        for child in doc.children:
            classname = child.__class__.__name__

            block_type = type_mapping.get(classname, classname.lower())
            block_text = self.parser.render(child)

            if classname == "CodeBlock":
                if is_it_code(block_text):
                    block_type = "code"
                else:
                    block_type = "p"

                    words_to_remove = ["<pre>", "</pre>", "<code>", "</code>"]
                    pattern = "|".join(map(re.escape, words_to_remove))

                    block_text = re.sub(pattern, "", block_text).strip()

                    block_text = f"<p>{block_text}</p>"

            if block_text.strip():
                blocks.append({"type": block_type, "text": block_text.strip()})

        return blocks

    def split_by_sentences(self, text: str) -> List[str]:

        if not text or not text.strip():

            return []

        blocks = self.split_blocks(text)

        sentences = []

        for block in blocks:

            block_text = block["text"]

            block_type = block["type"]

            # Not going to split code or table blocks into sentences as this will cause problems with code snippets and table formatting.
            if block_type in ["code", "table"]:

                sentences.append(block_text)

            else:

                # Split the block into sentences using regex

                # Keep the outer HTML tag intact while splitting its content.
                match = re.match(
                    r"^<([a-zA-Z0-9]+)(?:\s[^>]*)?>(.*?)</\1>$", block_text, re.DOTALL
                )

                if match:
                    tag = match.group(1)
                    content = match.group(2)
                else:
                    tag = None
                    content = block_text

                parts = re.split(
                    r'(?<=[.!?])(?:["”’\'\)\]]+)?\s+(?=[A-Z0-9"“‘\(\[]|$)', content
                )

                for part in parts:

                    part = part.strip()

                    if part:

                        # Now adding the outer HTML tag back to each sentence.
                        sentences.append(f"<{tag}>{part}</{tag}>" if tag else part)

        return [unit for unit in sentences if unit and unit.strip()]

    def chunk_text(self, text: str) -> List[Dict]:
        if not text or not text.strip():
            return []

        blocks = self.split_blocks(text)
        chunks = []
        current_chunk = ""
        current_tokens = 0
        chunk_id = 0

        for block in blocks:
            block_text = block["text"]
            block_type = block["type"]

            if block_type in ["code", "table"]:
                block_len = 1
            else:
                block_len = len(self.encoding.encode(block_text))

            if block_len > self.chunk_size:
                if current_chunk.strip():
                    chunks.append(
                        self._create_chunk_dict(current_chunk, chunk_id, current_tokens)
                    )
                    chunk_id += 1
                    current_chunk = ""
                    current_tokens = 0

                # Not going to split code and table block in sentences
                if block_type in ["code", "table"]:
                    chunks.append(
                        self._create_chunk_dict(block_text, chunk_id, block_len)
                    )
                    chunk_id += 1
                else:
                    # Split normal text by sentences
                    sentences = self.split_by_sentences(block_text)
                    for sentence in sentences:
                        sentence_len = len(self.encoding.encode(sentence))
                        if current_tokens + sentence_len <= self.chunk_size:
                            current_chunk += (
                                (" " + sentence) if current_chunk else sentence
                            )
                            current_tokens += sentence_len
                        else:
                            if current_chunk.strip():
                                chunks.append(
                                    self._create_chunk_dict(
                                        current_chunk, chunk_id, current_tokens
                                    )
                                )
                                chunk_id += 1
                            current_chunk = sentence
                            current_tokens = sentence_len

                    # still there could be some sentences there.
                    if current_chunk.strip():
                        chunks.append(
                            self._create_chunk_dict(
                                current_chunk, chunk_id, current_tokens
                            )
                        )
                        chunk_id += 1
                        current_chunk = ""
                        current_tokens = 0

            else:
                if current_tokens + block_len <= self.chunk_size:
                    # Fits perfectly in current chunk
                    current_chunk += (
                        ("\n\n" + block_text) if current_chunk else block_text
                    )
                    current_tokens += block_len
                else:
                    # Doesn't fit in current chunk

                    if block_type in ["code", "table"]:
                        if current_chunk.strip():
                            chunks.append(
                                self._create_chunk_dict(
                                    current_chunk, chunk_id, current_tokens
                                )
                            )
                            chunk_id += 1
                        current_chunk = block_text
                        current_tokens = block_len
                    else:
                        # THis is a normal block. So, we going to split it.
                        sentences = self.split_by_sentences(block_text)

                        for sentence in sentences:
                            sentence_len = len(self.encoding.encode(sentence))
                            if current_tokens + sentence_len <= self.chunk_size:
                                current_chunk += (
                                    (" " + sentence) if current_chunk else sentence
                                )
                                current_tokens += sentence_len
                            else:
                                # Flush current chunk
                                if current_chunk.strip():
                                    chunks.append(
                                        self._create_chunk_dict(
                                            current_chunk, chunk_id, current_tokens
                                        )
                                    )
                                    chunk_id += 1
                                current_chunk = sentence
                                current_tokens = sentence_len

        # Still there are some texts left so append it to chunk
        if current_chunk.strip():
            chunks.append(
                self._create_chunk_dict(current_chunk, chunk_id, current_tokens)
            )

        return chunks

    def _create_chunk_dict(self, text: str, chunk_id: int, token_count: int) -> Dict:
        return {"chunk_id": chunk_id, "text": text, "token_count": token_count}


if __name__ == "__main__":
    test_chunk = """Type “easiest programming language” into Google and you’ll get a dozen listicles that crown the same winner and move on. They’re not wrong about the winner. They’re wrong about the question.
    
    Easy doesn’t matter if it leads nowhere. The simplest language in the world is useless if nobody’s hiring for it. The smart first pick sits at the intersection of two things: gentle enough that you don’t quit in week three, and in demand enough that learning it actually opens a door.
    
    So this guide ranks beginner languages on both. How easy each one is to pick up, and how many jobs wait on the other side. We pulled demand data from job boards and the most recent developer surveys, and we’ll tell you the one most people should start with, plus the ones to skip for now.
    
    ## Table of contents

    | Header 1 | Header 2 |
    | --- | --- |
    | Cell 1 | Cell 2 |

    * List item 1
    * List item 2
    
    ## What makes a programming language easy to learn
    
    “Easy” isn’t one thing. A few factors decide whether a language welcomes beginners or fights them.
    
    Readable syntax is the big one. Python reads almost like English. C++ reads like punctuation had an argument. The closer the code looks to plain instructions, the faster a beginner can follow what’s happening.
    
    Then there’s how much you have to know before you can run anything. Some languages let you write one line and see a result. Others make you set up a compiler, declare types, and wrap everything in boilerplate before “hello world” works. Fast feedback keeps beginners motivated. Setup friction makes them quit.
    
    The last factor is the ecosystem around the language: tutorials, free courses, Stack Overflow answers, and a community that’s seen your exact error before. A language with a huge beginner community is easier to learn even if the syntax is identical, simply because help is everywhere.
    
    ## The easiest programming languages, ranked
    
    Here’s how the most common starter languages stack up on a straight beginner-friendliness score. This is purely about ease of learning, not about jobs (that’s the next chart).
    
    A quick honesty check on this chart. HTML and CSS aren’t really programming languages (they describe and style pages, they don’t compute), but almost everyone starts there, so they belong in the conversation. SQL is shockingly beginner-friendly for how powerful it is, because you’re basically writing structured questions about data. And Python sits at the top for a reason we’ll get into.
    
    ## Easy vs. employable: the chart that matters
"""
    chunker = TextChunker(chunk_size=50)
    result = chunker.chunk_text(test_chunk)

    print(result)
    print(f"Number of blocks: {len(result)}")
