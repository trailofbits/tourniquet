import example
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="""
    A utility to process the JSON and raw output of 'polytracker' with a
    polytracker.json and a polytracker_forest.bin
    """
    )
    print("Hello world!")
    parser.add_argument("--json", "-j", type=str, default=None, help="Path to polytracker json file")
    parser.add_argument("--forest", "-f", type=str, default=None, help="Path to the polytracker forest bin")
    parser.add_argument("--debug", "-d", action="store_true", default=None, help="Enables debug logging")
    parser.add_argument("--draw-forest", action="store_true", default=None, help="Produces a taint forest dot file")
    parser.add_argument("--outfile", type=str, default=None, help="Specify outfile JSON path/name")

    args = parser.parse_args(sys.argv[1:])


if __name__ == "__main__":
    print("we did it reddit")
    main()
