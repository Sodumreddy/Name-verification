import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from name_verification.verifier import verify_name_pair


def assert_match(target: str, candidate: str) -> None:
    result = verify_name_pair(target, candidate)
    assert result.match, f"Expected match for '{target}' vs '{candidate}', got non-match. Reason: {result.reason}"
    assert result.confidence >= 0.7


def assert_non_match(target: str, candidate: str) -> None:
    result = verify_name_pair(target, candidate)
    assert not result.match, f"Expected non-match for '{target}' vs '{candidate}', got match. Reason: {result.reason}"


def test_expected_matches():
    assert_match("Tyler Bliha", "Tlyer Bilha")
    assert_match("Al-Hilal", "alhilal")
    assert_match("Dargulov", "Darguloff")
    assert_match("Bob Ellensworth", "Robert Ellensworth")
    assert_match("Mohammed Al Fayed", "Muhammad Alfayed")
    assert_match("Sarah O'Connor", "Sara Oconnor")
    assert_match("Jonathon Smith", "Jonathan Smith")
    assert_match("Abdul Rahman ibn Saleh", "Abdulrahman ibn Saleh")
    assert_match("Al Hassan Al Saud", "Al-Hasan Al Saud")
    assert_match("Katherine McDonald", "Catherine Macdonald")
    assert_match("Yusuf Al Qasim", "Youssef Alkasim")
    assert_match("Steven Johnson", "Stephen Jonson")
    assert_match("Alexander Petrov", "Aleksandr Petrof")
    assert_match("Jean-Luc Picard", "Jean Luc Picard")
    assert_match("Mikhail Gorbachov", "Mikhail Gorbachev")
    assert_match("Elizabeth Turner", "Liz Turner")
    assert_match("Omar ibn Al Khattab", "Omar Ibn Alkhattab")
    assert_match("Sean O'Brien", "Shawn Obrien")


def test_expected_non_matches():
    assert_non_match("Emanuel Oscar", "Belinda Oscar")
    assert_non_match("Michael Thompson", "Michelle Thompson")
    assert_non_match("Ali Hassan", "Hassan Ali")
    assert_non_match("John Smith", "James Smith")
    assert_non_match("Abdullah ibn Omar", "Omar ibn Abdullah")
    assert_non_match("Maria Gonzalez", "Mario Gonzalez")
    assert_non_match("Christopher Nolan", "Christian Nolan")
    assert_non_match("Ahmed Al Rashid", "Ahmed Al Rashidi")
    assert_non_match("Samantha Lee", "Samuel Lee")
    assert_non_match("Ivan Petrov", "Ilya Petrov")
    assert_non_match("Fatima Zahra", "Zahra Fatima")
    assert_non_match("William Carter", "Liam Carter")
