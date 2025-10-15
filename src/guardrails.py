import re
import yaml
from typing import Tuple
from pathlib import Path

# Load RAI configuration from YAML
config_path = Path(__file__).parent.parent / 'config' / 'rai.yaml'
with open(config_path, 'r') as f:
    RAI_CONFIG = yaml.safe_load(f)

# Build regex patterns from config
profanity_words = '|'.join(RAI_CONFIG['profanity_patterns'])
PROFANITY = re.compile(rf'\b({profanity_words})\b', re.IGNORECASE)

code_patterns = '|'.join(RAI_CONFIG['code_patterns'])
CODE_PATTERNS = re.compile(rf'({code_patterns})', re.IGNORECASE)

# Load lists from config
NEGATIVE_WORDS = RAI_CONFIG['negative_words']
SENSITIVE_TOPICS = RAI_CONFIG['sensitive_topics']
VAGUE_RESPONSES = RAI_CONFIG['vague_responses']
STOP_WORDS = set(RAI_CONFIG['stop_words'])

# Load limits
MAX_INPUT_LENGTH = RAI_CONFIG['limits']['max_input_length']
MIN_INPUT_LENGTH = RAI_CONFIG['limits']['min_input_length']
MAX_OUTPUT_LENGTH = RAI_CONFIG['limits']['max_output_length']

def validate_input(input_text: str) -> Tuple[bool, str]:
    """
    Validate user input. Returns (is_valid, message/input).
    If invalid, message explains why; if valid, returns sanitized input.
    """
    # Length check
    if len(input_text) > MAX_INPUT_LENGTH:
        return False, f"Input too long (max {MAX_INPUT_LENGTH} characters). Please shorten your query."

    # Empty or gibberish check
    if not input_text.strip() or len(input_text.strip()) < MIN_INPUT_LENGTH:
        return False, "Input is empty or too short. Please provide a meaningful query."

    # Profanity check
    if PROFANITY.search(input_text):
        return False, "Input contains inappropriate language. Please rephrase."

    # Code injection check
    if CODE_PATTERNS.search(input_text):
        return False, "Input contains potentially harmful code. Please use plain text."

    # Sanitize: strip excessive whitespace
    sanitized = ' '.join(input_text.strip().split())
    return True, sanitized

def validate_output(response: str, input_text: str) -> Tuple[bool, str]:
    """
    Validate agent output against input. Returns (is_valid, response).
    If invalid, returns fixed response or error message.
    """
    # Length check
    if len(response) > MAX_OUTPUT_LENGTH:
        return False, "Response too long; shortened: " + response[:MAX_OUTPUT_LENGTH]

    # Profanity check
    if PROFANITY.search(response):
        return False, "Response contains inappropriate language. Rephrasing: Let's keep it friendly!"

    # Negative tone check
    if any(word in response.lower() for word in NEGATIVE_WORDS):
        return False, "Response contains negative tone. Rephrasing: Here's a positive take!"

    # Sensitive topics check
    if any(topic in response.lower() for topic in SENSITIVE_TOPICS):
        return False, "Response touches on sensitive topics. Let's discuss something else."

    # # Relevance check: ensure some input keywords appear in response (relaxed)
    # input_words = set(input_text.lower().split()) - STOP_WORDS
    # response_words = set(response.lower().split())
    # # Only flag if response is very short and has NO overlap at all
    # if len(response) < 50 and len(input_words) > 2 and not input_words & response_words:
    #     return False, "Response seems off-topic. Could you clarify your query?"

    # Clarity check: avoid vague responses
    if response.lower().strip() in VAGUE_RESPONSES:
        return False, "I need more context to answer clearly. Could you provide more details?"

    return True, response