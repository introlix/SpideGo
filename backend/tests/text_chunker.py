from services.text_chunker import TextChunker

def test_empty_text():
    chunker = TextChunker(chunk_size=50)
    assert chunker.chunk_text("") == []

def test_basic_texts():
    """Here we have basic text with only one paragraph and 5 sentence and it be only in one chunk"""

    chunker = TextChunker(chunk_size=50)

    text = """
    This is a basic paragraph with only 5 sentences. This is the second sentence. And this result should have only one chunk. And this is the second last sentence. And now this is the final.
    """

    assert len(chunker.chunk_text(text)) == 1

def test_text_smaller_than_chunk_size():
    chunker = TextChunker(chunk_size=50)

    text = "This is only one sentence long."

    assert chunker.chunk_text(text)[0]['text'] == f"<p>{text}</p>"

def test_text_chunk_into_two():
    chunker = TextChunker(chunk_size=5)

    text = "This is the first sentence. And this should be second."


    assert chunker.chunk_text(text)[0]['text'] == "<p>This is the first sentence.</p>"
    assert chunker.chunk_text(text)[1]['text'] == "<p>And this should be second.</p>"

def test_if_it_split_markdown_correctly():
    chunker = TextChunker(chunk_size=10)

    text = """
    This is the first sentence.

    | Header 1 | Header 2 |
    | --- | --- |
    | Cell 1 | Cell 2 |

    * List item 1
    * List item 2

    # This is a header
    """

    result = chunker.chunk_text(text)

    assert len(result) == 3 # Since Table is considered as one token
    assert result[2]['text'] == "<h1>This is a header</h1>" # Last sentece should be a h1 as in markdown its #
    