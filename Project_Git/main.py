import argparse
import sys ,json
from pathlib import Path

class Repository:
    #creating the .git folder
    def __init__(self,path="."):
        self.path = Path(path).resolve() #creates absolute path
        self.get_dir = self.path / ".pygit"

        #.git/objects
        self.objects_dir = self.get_dir / "objects"
        #.git/refs
        self.ref_dir = self.get_dir / "refs" # in refs we have another folder heads
        self.heads_dir = self.ref_dir / "heads" # with in it we have branch name
        #Head file
        self.head_file = self.get_dir / "HEAD"
        #.git/index
        self.index_file = self.get_dir /"index"

    def init(self) ->bool:

        if self.get_dir.exists():
            return False
        
        #create directories
        self.get_dir.mkdir()
        self.objects_dir.mkdir()
        self.ref_dir.mkdir()
        self.heads_dir.mkdir()

        #creates a head file that points to a branch
        self.head_file.write_text("ref: refs/heads/master\n")

        #creates a index file that stores the file in json format and creates a maping between filename and hashing releated to it
        self.index_file.write_text(json.dumps({},indent=2))

        print(f"Initialized empty Git repository in {self.get_dir}")
        return True

def main():
    parser = argparse.ArgumentParser(
        description="PyGit -A simple git clone!"
    )
    subparsers = parser.add_subparsers(dest="command",help="Availaible commands")

    # init command
    init_parser = subparsers.add_parser("init",help="Initialize a new respository")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "init":
            repo = Repository()
            if not repo.init():
                print("Repository already exists")
                return

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

main()