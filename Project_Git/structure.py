import argparse

# 1. Create the main parser
parser = argparse.ArgumentParser(description='A program with sub-commands')

# 2. Add subparsers
subparsers = parser.add_subparsers(dest='command', help='Available commands')

# 3. Create a parser for the "add" command
add_parser = subparsers.add_parser('add', help='Add a file')
add_parser.add_argument('filename', type=str, help='The file to add')
# Associate a function with this sub-command
def add_func(args):
    print(f"Adding file: {args.filename}")
add_parser.set_defaults(func=add_func)

# 4. Create a parser for the "commit" command
commit_parser = subparsers.add_parser('commit', help='Commit changes')
commit_parser.add_argument('-m', '--message', type=str, required=True, help='A commit message')
# Associate a different function with this sub-command
def commit_func(args):
    print(f"Committing with message: {args.message}")
commit_parser.set_defaults(func=commit_func)

# 5. Parse arguments and call the associated function
args = parser.parse_args()
if hasattr(args, 'func'):
    # Call the function associated with the chosen subparser
    args.func(args)
else:
    # If no subparser was selected (e.g., just running the script with -h)
    parser.print_help()



# Step,Action,Mental State / Value of args
# 1. Entry,You run python script.py add photo.jpg.,"The shell passes ['add', 'photo.jpg'] to the script."
# 2. Routing,parser.parse_args() sees the word add.,"""Okay, I need to hand the rest of this input to the add_parser specialist."""
# 3. Validation,add_parser looks for filename.,It sees photo.jpg. It checks if it’s a string (Yes). It saves it.
# 4. Assembly,The args object is built.,"args now looks like: Namespace(command='add', filename='photo.jpg', func=add_func)"
# 5. The Hook,"if hasattr(args, 'func'):","The code checks: ""Did the sub-command we picked leave us a function to run?"" (Yes, it’s add_func)."
# 6. Execution,args.func(args),"The script calls add_func(args). Inside that function, args.filename resolves to 'photo.jpg'."

# Structure: Subparsers are added to an existing ArgumentParser instance using the add_subparsers() method. Each individual sub-command is then created by calling the add_parser() method on the object returned by add_subparsers().
# Positional Argument: The user specifies which subparser to use by providing its name as a positional argument on the command line. This name triggers the corresponding subparser to handle the subsequent arguments.



# Usage from the command line:
# python script_name.py add my_file.txt -> calls add_func
# python script_name.py commit -m "initial commit" -> calls commit_func
# python script_name.py --help -> shows help for the main program and lists sub-commands
# python script_name.py add --help -> shows help specifically for the add sub-command 