import sys
from pprint import pprint

from main import debug_full_pipeline


DEFAULT_INPUT = "pain near belly button then moved to right lower abdomen and feel sick"


def main() -> None:
	text = " ".join(sys.argv[1:]).strip() or DEFAULT_INPUT
	pprint(debug_full_pipeline(text), sort_dicts=False)


if __name__ == "__main__":
	main()