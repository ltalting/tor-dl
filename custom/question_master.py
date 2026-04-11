from typing import Any, Union
from .common_functs import any_to_str
from .log_util import log_msg

# Determines if any valid answers are "any", indicating any response will be deemed valid
# Used to skip more intricate check_answer() logic
def is_any_answer_valid(normalized_valid_answers: list[str]) -> bool:
    return "any" in normalized_valid_answers or len(normalized_valid_answers) == 0

# Convert list of tuple answers to list of str answers
# Also handles "any" keyword
def normalize_valid_answers(valid_answers: list[Union[Any, tuple[Any, bool]]]) -> list[str]:
    # Flatten tuple list by applying options to string
    normalized_valid_answers: list[str] = []
    for answer in valid_answers:
        if isinstance(answer, str):
            # By default, str-typed answers are case-insensitive
            normalized_valid_answers.append(answer.lower().strip())
        elif isinstance(answer, tuple):
            # Lower if case-insensitive flag is True, otherwise add
            normalized_valid_answers.append(answer[0].lower().strip() if answer[1] else answer[0].strip())
        else:
            try:
                normalized_valid_answer = any_to_str(answer)
                normalized_valid_answers.append(normalized_valid_answer.lower().strip())
            except Exception:
                log_msg(f"Invalid type in answers list: '{str(answer)}' is {type(answer)}", "red", exit = 1)
    return normalized_valid_answers, is_any_answer_valid(normalized_valid_answers)

# Returns true if answer is included in valid_answers
# valid_answers is a list of strs and tuples where
#   - strs will be case-insensitive by default
#   - tuples are handled as follows:
#       - [0] is a correct answer represented as a string
#       - [1] is a flag indicating that:
#           - When True, will not preserve case (will lower())
#           - When False, will preserve case
def check_answer(answer: str, valid_answers: list[Union[str, tuple[str, bool]]]) -> bool:
    is_valid: bool = False
    stripped_answer = answer.strip()
    normalized_answer = stripped_answer.lower()
    for valid_answer in valid_answers:
        if isinstance(valid_answer, str):
            if normalized_answer == valid_answer.strip().lower():
                is_valid = True
                break
        elif isinstance(valid_answer, tuple):
            stripped_valid_answer = valid_answer[0].strip()
            if valid_answer[1]:
                if normalized_answer == stripped_valid_answer.lower():
                    is_valid = True
                    break
            else:
                if stripped_answer == stripped_valid_answer:
                    is_valid = True
                    break
    return is_valid

# Ask a question and wait for input
# valid_answers - tuple structure is: "answer", case_insensitive
def ask_question(question: str, valid_answers: list[Union[Any, tuple[Any, bool]]] = [("any", True)], color: str = "white"):
    answer_pending = True
    normalized_valid_answers, any_answer_is_valid = normalize_valid_answers(valid_answers)
    # Check if we need to check_answer()
    if any_answer_is_valid:
        answer = input(f"{question.strip()} ").strip()
        answer_pending = False
    else:
        normalized_valid_answers_str = ", ".join(normalized_valid_answers)
        # Loop while checking responses against valid answers
        while answer_pending:
            log_msg(f"{question} [{normalized_valid_answers_str}]", color)
            answer = input().strip()
            if check_answer(answer, normalized_valid_answers):
                answer_pending = False
            else:
                log_msg(f"Invalid answer '{answer}'. Please try again or exit the script via Ctrl-C.", "yellow")
    return answer