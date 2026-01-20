import argparse
import sys ,json ,hashlib,zlib,time
from pathlib import Path
from typing import Dict,List,Tuple


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
        header = decompressed[:null_idx].decode()
        content = decompressed[null_idx + 1:]

        obj_type , size = header.split(" ") 

        return cls(obj_type,content)
    
class Blob(GitObject):
    #(Binary Large object)
    def __init__(self,content:bytes):
        super().__init__('blob',content)
    
    def get_content(self)->bytes:
        return self.content

class Tree(GitObject):
    #Tree object for hierarchy
    
    def __init__(self,entries:List[Tuple[str,str,str]]=None):
        self.entries = entries or []
        content = self._serialize_entries() #of the entire list contains multiple files folder 
        super().__init__('tree',content)
        
    def _serialize_entries(self)->bytes:
        #<mode> <name>\0<hash><mode> <name>\0<hash><mode> <name>\0<hash> tree content is like this
        #why sorted to give (a.txt,b.txt) or we do (b.txt,a.txt) hash reamins same
        content = b""
        for mode,name,obj_hash in sorted(self.entries):
            content += f"{mode} {name}\0".encode()
            content += bytes.fromhex(obj_hash)#hash is hexa_Decimal so we convert back to bytes
        return content
    
    def add_entry(self,mode:str,name:str,obj_hash:str):
        self.entries.append((mode,name,obj_hash))
        self.content = self._serialize_entries() #directly changing the content variable og gitobj class

    @classmethod
    # because we nedd to apply the logic to entire class not a particular object
    def from_content(cls,content:bytes)->"Tree": 
        tree = cls() # empty instance of the class being assigned to the variable name tree
        i = 0

        while i < len(content):
            null_idx = content.find(b"\0",i)
            # 100644 README.md\0[20bytes of content hash]100644 xyz.md\0[20bytes of content hash]
            if null_idx == -1:
                break
            mode_name = content[i:null_idx].decode()
            mode,name = mode_name.split(' ',1)
            obj_hash = content[null_idx + 1 : null_idx + 21].hex()
            tree.entries.append((mode,name,obj_hash))#class method

            i = null_idx + 1
        return tree


class Commit(GitObject):
    def __init__(
            self,
            tree_hash:str,
            parent_hashes:List[str],
            author:str,
            committer:str,
            message:str,
            timestamp:int = None,
        ):
            self.tree_hash = tree_hash
            self.parent_hashes = parent_hashes 
            self.author = author
            self.committer=committer
            self.message = message
            self.timestamp =timestamp or int(time.time())

            content = self._serialize_commit()
            super().__init__("commit",content)
        
    def _serialize_commit(self):
        lines = [f"tree {self.tree_hash}"]
        for parent in self.parent_hashes:
            lines.append(f"parent {parent}")   
        lines.append(f"author {self.author} {self.timestamp} +0000")
        lines.append(f"committer {self.committer} {self.timestamp} +0000")
        lines.append("")
        lines.append(self.message)

        return "\n".join(lines).encode()
    
    @classmethod
    def from_content(cls,content:bytes)->"Commit":
        lines = content.decode().split("\n")
        tree_hash = None
        parent_hashes = []
        author = None
        committer =None
        message_start = 0

        for i , line in enumerate(lines):
            if line.startswith("tree "):
                tree_hash = line[5:]
            elif line.startswith("parent "):
                parent_hashes.append(line[7:])
            elif line.startswith("author "):
                author_parts = line[7:].rsplit(" ",2)
                author = author_parts[0]
                timestamp = int(author_parts[1])
            elif line.startswith("committer "):
                commit_parts = line[10:].rsplit(" ",2)
                committer = commit_parts[0]
            elif line == "":
                message_start = i + 1
                break
        message = "\n".join(lines[message_start:])
        commit = cls(tree_hash,parent_hashes,author,committer,message,timestamp)

        return commit
            



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

    def load_object(self,obj_hash:str)->GitObject:
        obj_dir = self.objects_dir / obj_hash[:2]
        obj_file = obj_dir / obj_hash[2:]

        if not obj_file.exists():
            raise FileNotFoundError(f"Object {obj_hash} not found")
        return GitObject.deserialize(obj_file.read_bytes())
    

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

    def create_tree_from_index(self):
        index = self.load_index()
        if not index:
            tree = Tree()
            return self.store_object(tree)
        
        dirs = {}
        files = {}
        for file_path,blob_hash in index.items():
            parts = file_path.split("/")
            if len(parts) == 1:
                #file in root
                files[parts[0]] = blob_hash
            else:
                dir_name = parts[0]
                if dir_name not in dirs:
                    dirs[dir_name] = {}
                
                current = dirs[dir_name]
                for part in parts[1:-1]: #last part not included
                    if part not in current:
                        current[part] = {}

                    current = current[part]   
                current[parts[-1]] = blob_hash

        def create_tree_recursively(entries_dict:Dict):
            tree = Tree()

            for name,blob_hash in entries_dict.items():
                if isinstance(blob_hash,str):
                    tree.add_entry("100644",name,blob_hash)
                
                if isinstance(blob_hash,dict):
                    subtree_hash = create_tree_recursively(blob_hash)
                    tree.add_entry("40000",name,subtree_hash)
                
            return self.store_object(tree)

        #decomposing it into one root directory
        root_entries = {**files}
        for dir_name,dir_contents in dirs.items():
            root_entries[dir_name] = dir_contents
        #do we need to write index to with root_dir no index is always a flat list of paths
        return create_tree_recursively(root_entries)
       
    #current branch is stored in the HEAD file  
    def get_current_branch(self)->str:
        if not self.head_file.exists():
            return "master"
        head_content = self.head_file.read_text().strip()
        if head_content.startswith("ref: refs/heads/"):
            return head_content[16:]
        return "HEAD" #detached Head
    
    #current commit is present in refs/head/filename(poimting to a commit_hash)
    def get_branch_commit(self,current_branch:str):
        branch_file = self.heads_dir / current_branch

        if branch_file.exists():
            return branch_file.read_text().strip()
        return None

    def set_branch_commit(self,current_branch:str,commit_hash):
        branch_file = self.heads_dir / current_branch
        branch_file.write_text(commit_hash + "\n")
        

    def commit(self,message:str,author:str):
        # create the tree object from the index (staging area)
        tree_hash = self.create_tree_from_index()

        current_branch = self.get_current_branch()
        parent_commit = self.get_branch_commit(current_branch)
        parent_hashes = [parent_commit] if parent_commit else [] #subsequent commit: parent_commit holds the hash of the previous commit. This line creates a list with that one hash inside it: ["abc123..."].
        
        index = self.load_index()
        if not index:
            print("nothing to commit working tree clean")
            return None
        
        if parent_commit:
            parent_git_commit_obj = self.load_object(parent_commit)
            parent_commit_data = Commit.from_content(parent_git_commit_obj.content) 
            if tree_hash == parent_commit_data.tree_hash:
                print("nothing to commit,working tree clean")
                return None

        commit = Commit(
            tree_hash=tree_hash,
            parent_hashes = parent_hashes,
            author=author,
            committer=author,
            message=message,
        )
        #Save the commit object to the objects database
        commit_hash = self.store_object(commit)
        # 5. UPDATE THE BRANCH POINTER
        self.set_branch_commit(current_branch,commit_hash)
        self.save_index({})
        print(f"Created commit {commit_hash} on branch {current_branch}")
        return commit_hash
        

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

    #commit command

    commit_parser = subparsers.add_parser("commit",help="commit the latest changes")
    commit_parser.add_argument("-m","--message",help="Create a new commit",required=True)
    commit_parser.add_argument("--author",help="Author nameand email")



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
        elif args.command == "commit":
            if not repo.get_dir.exists():
                print("Not a git repository")  
                return
            author = args.author or "PyGit user <user@pygit.com>"
            repo.commit(args.message,author)



    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

main()