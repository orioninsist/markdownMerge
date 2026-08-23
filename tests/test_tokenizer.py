from markdown_merge.tokenizer import count_tokens


def test_count_tokens():
    assert count_tokens("hello world") > 0
