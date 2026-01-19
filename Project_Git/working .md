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

