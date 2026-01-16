import argparse

def main():
    parser = argparse.ArgumentParser(
        description="PyGit -A simple git clone!"
    )
    subparsers = parser.add_subparsers(dest="command",help="Availaible commands")

    # init command
    init_parser = subparsers.add_parser("init",help="Initialize a new respository")

    args = parser.parse_args()
    print(args)

main()