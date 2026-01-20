When you run git add <filename>, Git performs three main steps.

1. The Hashing (SHA-1)
Git doesn't care about the filename yet. It looks at the content of the file. It calculates a SHA-1 hash of your file's data. This is a 40-character hexadecimal string (e.g., 5d392...).

The Content: "hello world"

The Hash: 5d392607b0c958467554f762635904d90f8450f3

2. The Folder Structure (.git/objects)
To keep the filesystem from slowing down (and because many OSs struggle with 10,000 files in one folder), Git splits that 40-character hash:

First 2 characters: Become the folder name (5d).

Remaining 38 characters: Become the filename (392607b0c...).

Path: .git/objects/5d/392607b0c958467554f762635904d90f8450f3

Inside that file, Git stores a compressed version (using Zlib) of your file's content, prefixed with a header: blob <size>\0.

3. The Index (The "Staging Area")
This is the part that links the filename to that hash. The .git/index is a binary file. It acts as a map (a table). When you "add" a file, Git updates this table

File Path,    Object Hash (the one we just made)
hello.txt,    5d392607b0c958467554f762635904d90f8450f3


Why this is genius: If you have 10 identical images with different filenames, Git only creates one object in .git/objects, but the index will have 10 entries pointing to that same hash. This is called deduplication.


Your Mental Model,Actual Git Internal
"""Stores filename in index folder""","The Index is actually a single binary file (usually .git/index), not a folder."
"""Creates a folder in objects""",Correct! It uses the first 2 chars of the hash as the folder name.
"""Folder contains another folder""",Close—it's usually Folder -> File. No second nested folder.
"""Contains a file in bytes""","Correct! It's a Zlib-compressed ""Blob"" (Binary Large Object)."

1. The "Content" is the Raw DataIn your code, the content passed to the GitObject.__init__ is always the uncompressed, raw data of that specific object type.
For a Blob: The content is just the raw bytes of your file (e.g., the text inside hello.txt).For a Tree: The content is the list of files and their hashes, formatted specifically: <mode> <name>\0<binary_hash>.
None of the objects pass compressed data to GitObject. Compression only happens inside the serialize() method.2. 
Why the Tree "Content" looks differentA Blob is simple: it's just a bucket of data. But a Tree is a directory listing. 
To make it "Git-compliant," we have to format that listing into a single byte-string 
so we can hash it.When you do content += bytes.fromhex(obj_hash), 
you are converting the 40-character hex string (like 5e1c...) into 20 raw bytes.
This makes the Tree object very compact.3. 
Here is the logical flow for both Blobs and Trees:

Prepare Raw Content: * Blob: b"hello world"

Tree: b"100644 file.txt\0<20-byte-hash>"

Calculate Hash: * The GitObject.hash() method takes that raw content, adds a header (tree <size>\0), and runs SHA-1.

Crucial: We hash the uncompressed data. This ensures that even if compression algorithms change in the future, the hash remains the same.

Serialize (Compress):

Only when we call serialize() to save the file to .pygit/objects do we use zlib.compress().

The Hierarchy
Think of it like this: A Tree is just a "special file" that contains a map of other files.

# Why we need Tree Object as well as commit object ?

We need tree for hierarchy, Tree can point to blob_hash and it can point to other Tree
how does the member variable list of the tree:
[[<mode><name><hash>],[<mode><name><hash>],[<mode><name><hash>],[<mode><name><hash>]]
<mode(str) -> mode(bytes)> <filename(str) - filename(bytes)>\0<hash(hexa_decimal {40 bytes}) -> hash(binary {20 bytes})>

This is what is stored in the the object in i.e passed to super().__init__('tree',content)
the deserialize or from_content() methos is used to decode what we have encoded and passed as content in serialize method back in the original structure
# 100644 README.md\0[20bytes of content hash]100644 xyz.md\0[20bytes of content hash]

Why we might need it let me give the flow again We need Tree object to create the 
tree_hash = self.create_tree_from_index(). Before we commit we create git add. we add all the file in the staging area the index file is built index as 

{
  "main.py": "a2b3f2405dce714edbb366453831306a33888c67",
  "structure.md": "1f79fcadcd2bbebda623838302bf29ece1d1484e",
    "test/test1/xyz.txt = "hash1"
    "test/test1/test2/.abc.txt = "hash2"
    test/test3/pqr.txt = "hash3"
    script/exe.py = "hash4"
}

here we call the create_tree_from_index() 
when create tree called first the root_dict is created it remember tree contains both blob and point to another tree
//running a for loop we create file_dict , dirs_dict and then finally combine them to make root_dict it will look like this

{ 
    "main.py": "a2b3f2405dce714edbb366453831306a33888c67",
    "structure.md": "1f79fcadcd2bbebda623838302bf29ece1d1484e",
    test{
        test1{
            xyz.txt : "hash1
            test2{
                abc.txt : "hash2
            }
        }
        test3{
            pqr.txt : "hash3"
        }

    }
    script {
        exe.py : "hash5"
    }
}

remember this dictionary is created each time we create a root_dict

now we pass this root_dict to create_tree_recursive(root_dict) it would recursively create the entries list [[<mode> <name><hash>],[<mode> <name>\0<hash>],[<mode> <name>\0<hash>]]

In the commit object we need tree_hash that's why needed the tree object apart from tree_hash we need parent_hash,messaege(it was directly pass in git commit -m "message") and author and commiter in our case both are same , then we create the content string by cleverly manipulating string and call the super().__init__ function . so that we can now perform all sorts of GitObject member functions on it like hashing, compressing etc .

 The Execution Flow --> When creating a commit:You call Commit(tree_hash="abc...", message="First commit", ...)__init__ runs._serialize_commit runs to create the text body.The result is passed to super().__init__ so it can be hashed and stored.

When reading a commit:You read the bytes from .pygit/objects/xx/xxxx...You decompress them.You pass those bytes to Commit.from_content(data).from_content parses the text.from_content finally calls return cls(...) (which is __init__) to give you a nice Python object.

# current branch is stored in the HEAD file get_current_branch(self)->str:

# current commit is present in refs/head/filename(pointing to a commit_hash) get_branch_commit(self,current_branch:str):

The commit function takes the message , author as input prepare the commit object

commit = Commit(
            tree_hash=tree_hash,
            parent_hashes = parent_hashes,
            author=author,
            committer=author,
            message=message,
        )
# Gets the current branch and  parent_commit
current_branch = self.get_current_branch()
parent_commit = self.get_branch_commit(current_branch) 

# Store / Update the Branch Pointer with set_branch_commit(current_branch,commit_hash)
# return commit_hash which it got when passed commit object was passed to store_obj()

The reason we pass the entire commit object to store_objects instead of just the bytes is that the object "carries" everything it needs to know about itself.

If you passed only the bytes to self.store_objects(bytes), the function wouldn't know if those bytes represent a Blob, a Tree, or a Commit. It would just be a pile of data. By passing the object, you are passing the data and the tools to handle that data.

The store_objects(object)  inherits from GitObject, it has access to self.hash() and self.serialize(). When you pass the object commit, the repository simply asks the object: "Hey, give me your hash and your compressed bytes," and the object complies.