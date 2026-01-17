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