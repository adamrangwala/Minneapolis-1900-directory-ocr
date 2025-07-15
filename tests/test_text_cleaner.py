from src.ocr.text_cleaner import TextCleaner
import pytest

@pytest.fixture
def default_config():
    return {
        'remove_noise_characters': True,
        'merge_continuation_lines': True,
        'min_line_length': 3,
        'noise_characters': "~`!@#$%^&*()_+=[]{}|\\:;\"'<>?,./",
        'allowed_leading_chars': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789&'
    }

@pytest.fixture
def text_cleaner(default_config):
    return TextCleaner(**default_config)
