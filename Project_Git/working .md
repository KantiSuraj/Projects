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

# current commit is present in refs/head/filename(contains the commit_hash)
# current branch is stored in the HEAD file

The commit hash contains every thing thing tree_hash,parent_hash commiter,etc when hash created we get the parent_commit from get_branch_commit parent_commit is passed into load_object() it basically loads the entire data which was compressed and stored in objects folder/obj_dir[:2]/obj_dir[:2] return a (Gitobj type-> commit,content)object (data stored and compressed) 

Now we have the latest object of commit type now we call the from_content method the returned object_type and pass obj.content what it does is beautifully deserialize the commit and we can find it's commit.tree_hash and compare with the current tree hash that means nothing new is added nothing to commit working tree clean   

/**
Upto Here how does it works -> we made changes we made a commit we do main.py add . it will update the index now we commit index is cleared now without making changes if we again do main.py add . index is updated now if we do main.py commit then it checks the previous parent commit and checks if they are  equal if they are nothing to commit working tree clean **/

Checkout command we have to two options either we create a new branch checkout to that or to checkout to a existing branch :
branch name is checked on the refs/head_directory if branch is present the new branch is created with the same commit hash the current branch and write in the head file the current branch name basically where the head points

Important Logic if we have two branch let say master and feature and we checkout to feature commit some changes and we don't want those commits are tracked in the master branch commit hash

To implement this we need to get the previous_branch and clear all the files from the working directory we don't need to store it because it was already stored in the object database we will get the previous commit hash from self .loadobject we will load the data bytes and store it in prev_commit_obj we will extract the prev_commit from commit.fromcontent(). we will get the tree_hash from it (prev_commit.tree_hash ) we intended to find the tree_hash to get the file and directoris to clear. Tree_hash was recursively created from all the files and directories so now we will again use a recursive function to get file from tree recursive

2. Why "Clear" the files? Are we losing data?
In Git, you never lose data if it has been committed. Commits are permanent snapshots in your .pygit/objects folder.

The "clearing" happens in your Working Directory (the actual folders you see on your desktop), not in the repository's memory.(What does it mean what does it clear is it clearing the index file or something related to hash)

Why we do it: Imagine you are on the feature branch, and you created a file called experimental.py. Now you switch back to master. That file experimental.py doesn't exist in master. If you don't delete it from your folder during the checkout, it will just sit there, confusing you into thinking it's part of the master branch.

The Workflow:

Identify: Find all files belonging to the current branch (files_to_clear).

Delete: Physically remove them from the disk.(Here we are deleting the file from the working directory we never delete the file from the object store )

Restore: Find all files belonging to the new branch and write them to the disk.

3. What if there are more than two branches?
The logic stays the same no matter how many branches you have.

A branch is just a pointer to one specific commit hash.

That commit hash points to one specific tree (snapshot).

When you checkout any branch, Git says: "Remove whatever the current branch has, and give me exactly what the target branch has." It doesn't matter if you have 2 branches or 200; Git only cares about the "From" and the "To."

1. The Core Concept: Two Different "Worlds"
The Object Database (.pygit/objects): This is the "Memory." Every blob, tree, and commit you have ever made is saved here forever (unless you manually delete the .pygit folder). These files are compressed and permanent.

The Working Directory (Your project folder): This is the "Stage." This is where you actually see main.py or readme.txt.

2. Resolving your "Data Loss" Fear
When we say "Delete from disk," we mean we are deleting the files from the Working Directory, NOT the Object Database.

Analogy: Imagine you are an actor.

Object Database: This is the costume room. It has every costume for every play you've ever performed.

Working Directory: This is your body on stage.

Checkout: If you switch from playing Batman to playing Superman, you have to take off the Batman suit (Delete/Clear) and put on the Superman suit (Restore).

Are you losing the Batman suit? No! It’s still safely hanging in the costume room (.pygit/objects). You just aren't wearing it right now.

When we say "Delete from disk," we mean we are deleting the files from the Working Directory, NOT the Object Database.

Analogy: Imagine you are an actor.

Object Database: This is the costume room. It has every costume for every play you've ever performed.

Working Directory: This is your body on stage.

Checkout: If you switch from playing Batman to playing Superman, you have to take off the Batman suit (Delete/Clear) and put on the Superman suit (Restore).

Are you losing the Batman suit? No! It’s still safely hanging in the costume room (.pygit/objects). You just aren't wearing it right now.

3. Connecting the Dots: The Checkout Workflow
When you run checkout master, here is the exact internal logic:

Step A: Identifying the "Old" State
We use get_files_from_tree_recursive on the current branch's tree. This gives us a list of every file that currently exists in your folder because of the branch you are leaving.

Step B: The "Clear" (Deleting from Disk)
We loop through that list and physically delete those files from your computer.

Why? Because we want a "Clean Slate." If we don't delete them, and the new branch doesn't have those files, they will just sit there like ghosts from a previous version.

Step C: The "Index" Update
We also clear the index file. Remember, the index is a map of what is currently "tracked." Since we are moving to a new branch, the old map is no longer valid. We will rebuild the index to match the new branch's tree.

Step D: The "Restore" (Re-materializing)
We go to the Target Branch's Tree, recursively find all its Blobs, and write them back to the disk.
1.Target Branch ---> Commit ---> Tree.
2.Tree lists hello.txt has hash abcd123.
3.We look in .pygit/objects/ab/cd123....
4.We decompress that data and save it as a file named hello.txt in your folder.

it doesn't matter if you have 100 branches. Because each branch points to a Commit, and each Commit has a Tree Hash, a Tree is essentially a "Snapshot of the Entire Project."

When you move from Branch A to Branch B:

Git "Wipes" the Stage (Working Directory) based on A's Snapshot.

Git "Populates" the Stage (Working Directory) based on B's Snapshot

2. Why we must "Remove" (The 3 Main Reasons)
Reason A: Avoiding "Ghost Files"
Imagine you are on a branch called feature-login which has a file login_helper.py. You switch back to master, which does not have that file. If we didn't "remove" it, login_helper.py would still be sitting in your folder. You might try to run your code, it might import that file, and it might work—but that's a bug! Your master branch shouldn't have that file. By deleting it, Git ensures your folder is a perfect mirror of the branch you selected.

Reason B: Handling Renames
If you renamed script.py to app.py in a new branch, Git needs to:

Delete script.py.

Restore app.py. If it didn't delete the old one, you would end up with two copies of the same code under different names.

Reason C: The "Clean Slate" for the Index
Your index (staging area) is a map of what's on your disk. When you switch branches, your index needs to be updated to match the new branch. By clearing the "old" files and the "old" index, we ensure that the next time you run git status, it correctly compares your folder to the new branch's head.

# The "Data Chain"
1. The "Data Chain" (Your flow is correct)Blobs: Raw file code ----> Compressed ----> Blob Hash.
2. Trees: Filenames + Blob Hashes ----> Formatted into a list ----> Compressed ----> Tree Hash.
3. Commits: Tree Hash + Parent Hash + Metadata ----> Formatted into text ----> Compressed ----> Commit Hash.
4. Refs: The Commit Hash (just the 40-character string) is written into a plain text file like .pygit/refs/heads/master.
5. HEAD: A file containing ref: refs/heads/master tells Git which "sticky note" to look at.

#   The "Coding Perspective" of Loading When you "load" for a checkout, you are doing the reverse of your flow:

1. Read HEAD: Find out you are on master.
2. Read Ref: Go to refs/heads/master and get the string abc123....
3. Load Commit: Go to .pygit/objects/ab/c123..., decompress it, and find the line tree xyz987....
4. Load Tree: Go to .pygit/objects/xy/z987..., decompress it, and see the list of files.
5. Load Blobs: For every file in that list, go to its specific object file, decompress it, and write those bytes to your actual physical folder.


After we have all the files in the working directory we unlink them clear them from working_dir and at last do the same i.e find the commit_hash of target branch -> tree_hash -> contents --> find all the files and directory and recursively load them back to working directory

Before you delete anything or move the branch pointer, you need to compare three things:

The HEAD (The last commit): What the project looked like when you last saved.
The Index (Staging Area): What you have "added" but not yet committed.
The Working Directory (Real Files): What is actually sitting on your disk right now.

Modified but not added: Working Dir != Index.
Added but not committed: Index != HEAD.
Clean: Working Dir == Index == HEAD.