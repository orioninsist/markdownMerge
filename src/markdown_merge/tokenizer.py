import tiktoken


class TokenCounter:
    def __init__(self, model: str = "gpt-4o"):
        self.encoding = tiktoken.encoding_for_model(model)

    def count(self, text: str) -> int:
        return len(
            self.encoding.encode(
                text,
                disallowed_special=(),
            )
        )


def count_tokens(text: str) -> int:
    counter = TokenCounter()
    return counter.count(text)
