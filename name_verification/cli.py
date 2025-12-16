import argparse

from .generator import generate_target_name
from .verifier import verify_against_latest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Target name generator and verifier (technical screen task)."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate a new target name.")
    generate_parser.add_argument(
        "prompt",
        type=str,
        help="Free-form prompt describing the desired name.",
    )

    verify_parser = subparsers.add_parser("verify", help="Verify a candidate name.")
    verify_parser.add_argument(
        "candidate",
        type=str,
        help="Candidate name to check against the latest target name.",
    )

    arguments = parser.parse_args()

    if arguments.command == "generate":
        target_name = generate_target_name(arguments.prompt)
        print(f"Generated target name: {target_name}")
    elif arguments.command == "verify":
        result = verify_against_latest(arguments.candidate)
        if not result["ok"]:
            print(f"Error: {result['error']}")
            return
        print(f"Latest target name : {result['target_name']}")
        print(f"Candidate name     : {result['candidate_name']}")
        print(f"Match              : {result['match']}")
        print(f"Confidence         : {result['confidence']:.2f}")
        print(f"Reason             : {result['reason']}")


if __name__ == "__main__":
    main()

