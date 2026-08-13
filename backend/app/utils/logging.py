"""Conservative logging — avoid dumping full user prompts by default."""

import logging

logger = logging.getLogger("prompt_enhancer")


def log_request_meta(*, prompt_len: int, mode: str, target: str) -> None:
    logger.info(
        "enhance request mode=%s target=%s prompt_chars=%s",
        mode,
        target,
        prompt_len,
    )
