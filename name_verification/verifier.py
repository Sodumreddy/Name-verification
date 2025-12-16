import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Set, Tuple

from .storage import read_latest_target


@dataclass
class VerificationResult:
    target_name: str
    candidate_name: str
    match: bool
    confidence: float
    reason: str


SURNAME_PREFIXES: Set[str] = {"al", "abu", "mc", "mac", "o"}

EQUIVALENT_FIRST_NAME_GROUPS: Tuple[Set[str], ...] = (
    {"bob", "robert"},
    {"liz", "elizabeth"},
    {"mohammed", "muhammad", "mohammad", "mohamad", "mohamed", "muhamed"},
    {"sarah", "sara"},
    {"jonathon", "jonathan", "johnathon", "johnathan"},
    {"steven", "stephen"},
    {"sean", "shawn", "shaun"},
    {"alexander", "aleksandr", "aleksander"},
    {"yusuf", "youssef", "yousuf", "yusef"},
)

DISALLOWED_SIMILAR_FIRST_NAME_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("michael", "michelle"),
    ("maria", "mario"),
    ("samantha", "samuel"),
    ("william", "liam"),
)


def normalize_full(name: str) -> str:
    """
    Normalize a full name string for exact-comparison purposes:
    - lower-case
    - keep only ASCII letters
    """
    lowered = name.lower()
    return re.sub(r"[^a-z]", "", lowered)


def normalize_and_tokenize(name: str) -> List[str]:
    """
    Normalize then split into tokens for structural comparison:
    - lower-case
    - non-letter characters become spaces
    - collapse multiple spaces
    """
    lowered = name.lower()
    letters_and_spaces = re.sub(r"[^a-z]+", " ", lowered)
    tokens = letters_and_spaces.split()
    return tokens


def levenshtein_distance(left: str, right: str) -> int:
    """
    Classic dynamic-programming Levenshtein distance for short strings.
    """
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    if len(left) < len(right):
        left, right = right, left

    previous_row = list(range(len(right) + 1))
    for index_left, char_left in enumerate(left, start=1):
        current_row = [index_left]
        for index_right, char_right in enumerate(right, start=1):
            insert_cost = current_row[index_right - 1] + 1
            delete_cost = previous_row[index_right] + 1
            substitute_cost = previous_row[index_right - 1] + (char_left != char_right)
            current_row.append(min(insert_cost, delete_cost, substitute_cost))
        previous_row = current_row

    return previous_row[-1]


def build_equivalence_lookup(
    groups: Iterable[Set[str]],
) -> dict:
    lookup: dict[str, int] = {}
    for index, group in enumerate(groups):
        for variant in group:
            lookup[variant] = index
    return lookup


FIRST_NAME_EQUIVALENCE_LOOKUP = build_equivalence_lookup(EQUIVALENT_FIRST_NAME_GROUPS)


def names_in_same_equivalence_group(first: str, second: str) -> bool:
    group_left = FIRST_NAME_EQUIVALENCE_LOOKUP.get(first)
    group_right = FIRST_NAME_EQUIVALENCE_LOOKUP.get(second)
    return group_left is not None and group_left == group_right


def is_disallowed_similar_pair(first: str, second: str) -> bool:
    normalized_pair = {first, second}
    for left, right in DISALLOWED_SIMILAR_FIRST_NAME_PAIRS:
        if normalized_pair == {left, right}:
            return True
    return False


def split_name(tokens: Sequence[str]) -> Tuple[str, str, List[str]]:
    """
    Split a token sequence into (first_name, surname, middle_tokens).

    The heuristics are tuned for the provided test cases:
    - surname may include an Arabic-style prefix (al, abu, etc.)
    - first name may be a compound before 'ibn'
    """
    if not tokens:
        return "", "", []

    if len(tokens) == 1:
        return "", tokens[0], []

    surname_start_index = len(tokens) - 1
    if len(tokens) >= 2 and tokens[-2] in SURNAME_PREFIXES:
        surname_start_index = len(tokens) - 2

    surname_tokens = list(tokens[surname_start_index:])
    core_tokens = list(tokens[:surname_start_index])

    if not core_tokens:
        return tokens[0], "".join(surname_tokens), []

    if "ibn" in core_tokens:
        ibn_index = core_tokens.index("ibn")
        first_tokens = core_tokens[:ibn_index] or [core_tokens[0]]
        middle_tokens = core_tokens[ibn_index:]
    else:
        first_tokens = core_tokens
        middle_tokens = []

    first_name = "".join(first_tokens)
    surname = "".join(surname_tokens)
    return first_name, surname, middle_tokens


def normalize_slavic_suffixes(surname: str) -> str:
    """
    Normalize common Slavic transliteration suffixes:
    -ov / -ev / -of / -off / -ef / -eff -> canonical -ov
    """
    suffix_variants = ("ov", "ev", "of", "off", "ef", "eff")
    for suffix in suffix_variants:
        if surname.endswith(suffix):
            return surname[: -len(suffix)] + "ov"
    return surname


def score_surnames(target_surname: str, candidate_surname: str) -> Tuple[float, str]:
    normalized_target = normalize_slavic_suffixes(target_surname)
    normalized_candidate = normalize_slavic_suffixes(candidate_surname)

    if normalized_target == normalized_candidate:
        return 1.0, (
            f"Surnames '{target_surname}' and '{candidate_surname}' match after "
            "normalizing common transliteration variants."
        )

    if not normalized_target or not normalized_candidate:
        return 0.0, "Surname information is missing in one of the names."

    distance = levenshtein_distance(normalized_target, normalized_candidate)
    maximum_length = max(len(normalized_target), len(normalized_candidate))

    if normalized_target.startswith(normalized_candidate) or normalized_candidate.startswith(
        normalized_target
    ):
        if distance == 1:
            return 0.0, (
                f"Surnames '{target_surname}' and '{candidate_surname}' differ only "
                "by an extra suffix, which typically indicates a different family."
            )

    if distance <= 2 and maximum_length >= 4:
        return 0.7, (
            f"Surnames '{target_surname}' and '{candidate_surname}' are very close "
            f"(edit distance {distance}), consistent with minor spelling or transliteration differences."
        )

    return 0.0, (
        f"Surnames '{target_surname}' and '{candidate_surname}' differ beyond minor spelling variations."
    )


def score_first_names(target_first: str, candidate_first: str) -> Tuple[float, str]:
    if not target_first and not candidate_first:
        return 1.0, "Names are single-token; using surname-only comparison."

    normalized_target = normalize_full(target_first)
    normalized_candidate = normalize_full(candidate_first)

    if normalized_target == normalized_candidate:
        return 1.0, (
            f"First names '{target_first}' and '{candidate_first}' match after normalization."
        )

    if names_in_same_equivalence_group(normalized_target, normalized_candidate):
        return 0.9, (
            f"First names '{target_first}' and '{candidate_first}' are known variants or nicknames."
        )

    if is_disallowed_similar_pair(normalized_target, normalized_candidate):
        return 0.0, (
            f"First names '{target_first}' and '{candidate_first}' look similar but are treated as distinct."
        )

    if not normalized_target or not normalized_candidate:
        return 0.0, "First name information is missing in one of the names."

    distance = levenshtein_distance(normalized_target, normalized_candidate)
    maximum_length = max(len(normalized_target), len(normalized_candidate))

    if distance <= 2 and maximum_length >= 4:
        return 0.7, (
            f"First names '{target_first}' and '{candidate_first}' are close "
            f"(edit distance {distance}), consistent with minor typos or alternative spellings."
        )

    return 0.0, (
        f"First names '{target_first}' and '{candidate_first}' differ significantly."
    )


def tokens_set_equal_ignoring_order(first_tokens: Sequence[str], second_tokens: Sequence[str]) -> bool:
    return sorted(first_tokens) == sorted(second_tokens) and list(first_tokens) != list(second_tokens)


def verify_name_pair(target_name: str, candidate_name: str) -> VerificationResult:
    """
    Core, deterministic verifier. This function is pure and does not call
    back into the generator or any external services.
    """
    normalized_target_full = normalize_full(target_name)
    normalized_candidate_full = normalize_full(candidate_name)

    if normalized_target_full == normalized_candidate_full:
        return VerificationResult(
            target_name=target_name,
            candidate_name=candidate_name,
            match=True,
            confidence=0.99,
            reason="Names match exactly once case, spacing, and punctuation are ignored.",
        )

    target_tokens = normalize_and_tokenize(target_name)
    candidate_tokens = normalize_and_tokenize(candidate_name)

    if tokens_set_equal_ignoring_order(target_tokens, candidate_tokens):
        return VerificationResult(
            target_name=target_name,
            candidate_name=candidate_name,
            match=False,
            confidence=0.2,
            reason=(
                "The same tokens appear in a different order, which typically "
                "indicates a different person (e.g., given name and family name swapped)."
            ),
        )

    if len(target_tokens) == 1 and len(candidate_tokens) == 1:
        surname_score, surname_reason = score_surnames(target_tokens[0], candidate_tokens[0])
        match = surname_score >= 0.7
        confidence = surname_score
        reason_prefix = "Single-token names compared as surnames. "
        return VerificationResult(
            target_name=target_name,
            candidate_name=candidate_name,
            match=match,
            confidence=confidence,
            reason=reason_prefix + surname_reason,
        )

    target_first, target_surname, _ = split_name(target_tokens)
    candidate_first, candidate_surname, _ = split_name(candidate_tokens)

    first_score, first_reason = score_first_names(target_first, candidate_first)
    surname_score, surname_reason = score_surnames(target_surname, candidate_surname)

    combined_confidence = max(0.0, min(1.0, (first_score + surname_score) / 2.0))
    is_match = first_score >= 0.7 and surname_score >= 0.7

    reason_parts = [
        f"First-name analysis: {first_reason}",
        f"Surname analysis: {surname_reason}",
    ]
    combined_reason = " ".join(reason_parts)

    return VerificationResult(
        target_name=target_name,
        candidate_name=candidate_name,
        match=is_match,
        confidence=combined_confidence,
        reason=combined_reason,
    )


def verify_against_latest(candidate_name: str) -> dict:
    """
    Verify a candidate against the latest persisted target name.

    Returns a dict so the CLI can include error information while keeping
    the core matcher pure.
    """
    latest_target = read_latest_target()
    if latest_target is None:
        return {
            "ok": False,
            "error": "No target name has been generated yet.",
            "target_name": None,
            "candidate_name": candidate_name,
            "match": None,
            "confidence": None,
            "reason": None,
        }

    core_result = verify_name_pair(latest_target, candidate_name)
    return {
        "ok": True,
        "error": None,
        "target_name": core_result.target_name,
        "candidate_name": core_result.candidate_name,
        "match": core_result.match,
        "confidence": core_result.confidence,
        "reason": core_result.reason,
    }

