#!python3
"""
A Pushbullet wrapper for Python. Sends a push notification when the given
commands finish. Can be used to automate and notify long tasks, like building a
large project.

@authors Nathan Smith
"""
from __future__ import print_function
import json
import os
import sys
import inspect
import argparse
import subprocess
import platform
import requests

DEFAULT_TITLE = "pyBullet"
DEFAULT_MESSAGE = "Task complete."


# TODO: Move pyBullet into separate file
class pyBullet:
    def __init__(self, api_key=None):
        if not api_key:
            self.header = {"Content-Type": "application/json"}
            self.url = "https://api.pushbullet.com/v2/pushes"
            config_path = os.path.join(get_script_dir(), "api.pub")
            if not os.path.isfile(config_path):
                raise IOError("No api key specified and api.pub not found.")
            with open(config_path, 'r') as fp:
                self.api_key = fp.read().strip()
        else:
            self.api_key = api_key

    def push(self, title, body):
        jsonized_data = json.dumps({
            "title": title,
            "body": body,
            "type": "note"
            })
        requests.post(self.url, headers=self.header, auth=(self.api_key, ""),
                      data=jsonized_data)

    def build_message(self, title, body, return_code, task_number, code=False,
                      each=False):
        # TODO: Handle case where both code and each are True
        if code:
            body = body + " : Returned " + str(return_code)
        if each:
            title = title + " : Task " + str(task_number)
        return (title, body)


class fakespace:
    def __init__(self, data):
        self.data = data

    def __getattr__(self, name, default=None):
        if name in self.data.keys():
            return self.data[name]
        else:
            raise AttributeError("fakespace has no attribute "+name)


def make_fakespace(data, args):
    # TODO: Integrate this function into the fakespace class
    args = vars(args)
    new_args = fakespace(data)
    for arg in args.keys():
        if arg is "message" and args["message"] != DEFAULT_MESSAGE:
            new_args.data[arg] = args[arg]
        elif arg is "title" and args["title"] != DEFAULT_TITLE:
            new_args.data[arg] = args[arg]
        elif args[arg] and arg != "message" and arg != "title":
            new_args.data[arg] = args[arg]
    return new_args


def get_script_dir(follow_symlinks=True):
    """Finds the directory where the script resides."""
    # TODO: Select a better directory to store saved args where the user has permissions
    if getattr(sys, 'frozen', False):
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)


def init_parser():
    """Sets up and returns the argparse object."""
    # TODO: Standardize arg order for add_arguement functions.
    parser = argparse.ArgumentParser(
        description="Do something, then send a notification.")
    parser.add_argument('arguments', nargs='*', help="Things to do.")
    parser.add_argument('-m', '--message', dest='message',
                        help="Message to send.", default=DEFAULT_MESSAGE)
    parser.add_argument('-t', '--title', dest='title',
                        help="Title of the message.", default=DEFAULT_TITLE)
    parser.add_argument('--save', dest='save', default=None,
                        help="Store this set of commands with this name.")
    parser.add_argument('--recall', dest='recall', default=None,
                        help="Recall a set of commands with this name.")
    parser.add_argument('--list', dest='list', default=False,
                        action="store_true",
                        help="Show a list of all saved command sets.")
    parser.add_argument('-b', '--break', dest='brk', default=False,
                        action="store_true",
                        help="Stop when a task returns not 0.")
    parser.add_argument('-e', '--each', dest='each', default=False,
                        action="store_true",
                        help="Send a notification for each task.")
    parser.add_argument('-r', '--return', dest='code', default=False,
                        action="store_true",
                        help="Send return codes with notifications.")
    parser.add_argument('-s', '--shell', dest='shell', default=False,
                        action="store_true",
                        help="Run the arguments in a shell. Dangerous.")
    parser.add_argument('-f', '--strict', dest='strict', default=False,
                        action="store_true",
                        help="Do not fail gracefully. Raise all errors.")
    parser.add_argument('-w', '--warn', dest='warn', help="Show SSL warnings.",
                        default=False, action="store_true")
    parser.add_argument('-q', '--quiet', dest='silent', default=False,
                        action="store_true", help="Send no notifications.")
    return parser


def main():
    # Set up arg parser and parse
    parser = init_parser()
    args = parser.parse_args()
    pb = pyBullet()

    # TODO: Simplify main by moving as much as possible out into functions
    # List saved command sets
    if args.list:
        saved = []
        for root, dirs, files in os.walk(get_script_dir()):
            for name in files:
                if name.endswith(".saved_args"):
                    saved.append(name)
        if len(saved) == 0:
            print("No saved command sets found.")
        else:
            print("Saved command sets: ", end='')
            first = True
            for name in saved:
                set_name = name[:name.find('.saved_args')]
                if first:
                    print(set_name, end='')
                else:
                    print(', '+set_name, end='')
                first = False

    # Save/recall args
    saved_args = None
    if args.recall:
        inpath = os.path.join(get_script_dir(), str(args.recall)+".saved_args")
        if not os.path.isfile(inpath):
            saved_set = str(args.recall)
            print("Could not locate saved command set \""+saved_set+"\".")
            return 1
        with open(inpath, 'r') as fp:
            saved_args = json.load(fp)
        args = make_fakespace(saved_args, args)

    elif args.save:
        out = json.dumps(vars(args))
        outpath = os.path.join(get_script_dir(), str(args.save)+".saved_args")
        with open(outpath, 'w') as fp:
            fp.write(out)

    if not args.warn:
        requests.packages.urllib3.disable_warnings()

    # Join args into a single string, then split on commas. Join the args with
    # the appropriate separator for the OS
    cmd_args = " ".join(args.arguments)
    cmds = filter(bool, cmd_args.split(','))

    # If we are running this in a shell
    if args.shell:
        if platform.system() is "Windows":
            cmds = "&".join(cmds)
        else:
            cmds = ";".join(cmds)
        cmds = [cmds]

    # Run the commands
    task_number = 1
    ret = 1
    broke = False
    for cmd in cmds:
        try:
            ret = subprocess.call(cmd.strip(), shell=args.shell)
        except:
            print("Task "+str(task_number)+" failed.\n\t"+cmd)
            # Raise the error in strict mode
            if args.strict:
                raise
        # Send notification if notifying for each task
        if args.each and not args.silent:
            message = pb.build_message(args.title, args.message, ret,
                                       task_number, code=args.code,
                                       each=args.each)
            pb.push(message[0], message[1])
        # Stop if we are breaking
        if args.brk and ret != 0:
            broke = True
            break
        task_number += 1

    if not args.each and not args.silent:
        message = (args.title, args.message)
        if args.brk and broke:
            message = pb.build_message(args.title, args.message, ret,
                                       task_number, code=True, each=True)
        elif args.code:
            message = pb.build_message(args.title, args.message, ret,
                                       task_number, code=True)
        pb.push(message[0], message[1])

if __name__ == "__main__":
    main()
