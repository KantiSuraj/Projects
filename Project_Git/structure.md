Structure: Subparsers are added to an existing ArgumentParser instance using the add_subparsers() method. Each individual sub-command is then created by calling the add_parser() method on the object returned by add_subparsers().

Positional Argument: The user specifies which subparser to use by providing its name as a positional argument on the command line. This name triggers the corresponding subparser to handle the subsequent arguments.

The dest='command' parameter: This tells argparse to store the name of the sub-command used (e.g., "add") into a variable called args.command. This is useful for logging or simple logic.

The "Function Mapping" Pattern: By using set_defaults(func=...), you avoid a messy if/elif chain. Instead of checking if args.command == 'add':, you simply execute whatever function is attached to the result.

The Fallback: If you just ran python script.py without "add" or "commit," the hasattr check fails, and it triggers print_help(). This ensures the user isn't left staring at a blank screen.

The Resulting Object:
If the user runs: python script.py add photo.jpg

The args object will look like this internally:

Python

# args object
{
    'command': 'add',        # Created because of dest='command'
    'filename': 'photo.jpg', # Created by the add_parser
    'func': <function add_func>
}

Scenario,Resulting args object
With dest='command',"Namespace(command='add', filename='photo.jpg', func=<function...>)"
Without dest,"Namespace(filename='photo.jpg', func=<function...>)"

When you use add_parser.add_argument("paths", ...) instead of filename, the key inside the args object changes to match the name you gave the argument.

How the args Object Changes
If you run the command: python git.py add file1.txt file2.txt

The args object will now look like this
# args object
{
    'command': 'add',          # From dest='command' in add_subparsers
    'paths': ['file1.txt', 'file2.txt'],  # From add_argument("paths", nargs='+')
    'func': <function add_func>
}

Why the key name changed
The argparse library uses the first string you provide in add_argument as the variable name (the key) in the resulting object.

If you write add_argument("filename"), you get args.filename.

If you write add_argument("paths"), you get args.paths.

What does nargs='+' do?
This is a very "Git-like" design choice.

nargs='+' tells Python: "Expect one or more values and put them all into a list."

This is why args.paths becomes ['file1.txt', 'file2.txt'] instead of just a single string.

Yes. Every time you call .add_argument() on a subparser, you are telling Python: "When this specific sub-command is used, look for these extra details and add them as keys to the args object."

If the user runs commit, those paths keys won't exist in the args object, because they belong specifically to the add branch.

Would you like to see how to implement the SHA-1 hashing and zlib compression in Python to actually process those paths?