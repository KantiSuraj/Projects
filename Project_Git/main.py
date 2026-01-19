import argparse
import sys ,json ,hashlib,zlib
from pathlib import Path
from typing import Dict


class GitObject:
    def __init__(self,obj_type:str,content:bytes):
        self.type = obj_type
        self.content = content
    
    def hash(self)->str:
        #f(<type> <size> \0<content>)
        header = f"{self.type} {len(self.content)}\0".encode()
        return hashlib.sha1(header + self.content).hexdigest()
    

    def serialize(self)->bytes: 
        #lossless compression
        header = f"{self.type} {len(self.content)}\0".encode()
        return zlib.compress(header + self.content)
    
    @classmethod
    # because we nedd to apply the logic to entire class not a aprticular object
    def deserialize(cls,data:bytes)->"GitObject": 
        decompressed = zlib.decompress(data) 
        null_idx = decompressed.find(b"\0")
        header = decompressed[:null_idx]
        content = decompressed[null_idx + 1:]

        obj_type , size = header.split(" ") 

        return cls(obj_type,content)
    
class Blob(GitObject):
    #(Binary Large object)
    def __init__(self,content:bytes):
        super().__init__('blob',content)
    
    def get_content(self)->bytes:
        return self.content

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
        self.save_index({})

        print(f"Initialized empty Git repository in {self.get_dir}")
        return True
     
    def store_object(self,obj:GitObject)->str:
        obj_hash = obj.hash()
        obj_dir = self.objects_dir / obj_hash[:2]
        obj_file = obj_dir / obj_hash[2:]

        if not obj_file.exists():
            obj_dir.mkdir(exist_ok=True)
            obj_file.write_bytes(obj.serialize())
        
        return obj_hash
    
    def load_index(self) -> Dict[str,str]:
        if not self.index_file.exists():
            return  {}
        try:
            return json.loads(self.index_file.read_text())
        except:
            return {}

    def save_index(self,index:Dict[str,str]):
        self.index_file.write_text(json.dumps(index,indent=2))

    def add_file(self,path:str):
        full_path = self.path / path
        if not full_path.exists():
           raise FileNotFoundError(f"Path {path} not found")
         
        #Read the file content
        content = full_path.read_bytes()

        #Create BLOB object from the content (Binary Large object) 
        blob = Blob(content)
        #store the blob object in database(./git/objects)
        blob_hash = self.store_object(blob)
        #update index to include the file
        index = self.load_index()
        index[path] = blob_hash
        self.save_index(index)

        print(f"Added {path}")

    def add_directory(self,path:str):
        full_path = self.path / path
        if not full_path.exists():
           raise FileNotFoundError(f"Path {path} not found")
        if not full_path.is_dir():
            raise ValueError(f"{path} is not a directory")
        index = self.load_index()
        added_count = 0
        #recursively traverse the directory
        for file_path in full_path.rglob("*"):#recursively yield file,directories matching the relative path in the sub tree
            
            if file_path.is_file():
                if ".pygit" in file_path.parts:
                    continue

                #creat blob objcts for all files
                content = file_path.read_bytes()
                blob = Blob(content)
                #store all blobs in the object database(.git/objects)
                blob_hash = self.store_object(blob)
                #update index
                rel_path = str(file_path.relative_to(self.path)) #we need rel path here file path is abs path
                index[rel_path] = blob_hash
                added_count += 1
        
        self.save_index(index)
        if added_count > 0:
            print(f"Added {added_count} files from directory {path}")
        else:
            print(f"Directory {path} already up to date")
        

        

    def add_path(self,path:str)->None:
        full_path = self.path / path
        if not full_path.exists():
            raise FileNotFoundError(f"Path {path} not found")
        if full_path.is_file():
            self.add_file(path)
        elif full_path.is_dir():
            self.add_directory(path)
        else:
            raise ValueError(f"{path} is neither a file nor a directory")
        


def main():
    parser = argparse.ArgumentParser(
        description="PyGit -A simple git clone!"
    )
    subparsers = parser.add_subparsers(dest="command",help="Availaible commands")

    # init command
    init_parser = subparsers.add_parser("init",help="Initialize a new respository")
    #add command
    add_parser = subparsers.add_parser("add",help="Add files and directories to the staging Area")
    add_parser.add_argument("paths",nargs='+',help="Files and directories to add")


    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return
    repo = Repository()
    try:
        if args.command == "init":
            if not repo.init():
                print("Repository already exists")
                return
        elif args.command == "add":
            if not repo.get_dir.exists():
                print("Not a git repository")  
                return
            for path in args.paths:
                repo.add_path(path)              


    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

main()