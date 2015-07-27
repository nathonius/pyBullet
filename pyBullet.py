#!/usr/bin/env python
from __future__ import print_function
import requests
import json
import os.path as path
import argparse
import subprocess
import platform

class pyBullet:
    def __init__(self, api_key=None):
        if not api_key:
            self.header = {"Content-Type": "application/json"}
            self.url = "https://api.pushbullet.com/v2/pushes"
            config_path = path.join(path.dirname(path.abspath(__file__)), "api.pub")
            if not path.isfile(config_path):
                raise IOError("No api key specified and api.pub not found.")
            with open(config_path, 'r') as fp:
                self.api_key = fp.read().strip()
        else:
            self.api_key = api_key

    def push(self, title, body):
        jsonized_data = json.dumps({"title": title, "body": body, "type": "note"})
        response = requests.post(self.url, headers=self.header, auth=(self.api_key, ""), data=jsonized_data)
        print(response)

    def build_message(self, title, body, return_code, task_number, code=False, each=False):
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
    args = vars(args)
    default_message = "pyBullet task complete."
    default_title = "pyBullet"
    new_args = fakespace(data)
    for arg in args.keys():
        if arg is "message" and args["message"] != default_message:
            new_args.data[arg] = args[arg]
        elif arg is "title" and args["title"] != default_title:
            new_args.data[arg] = args[arg]
        elif args[arg] and arg != "message" and arg != "title":
            new_args.data[arg] = args[arg]
    return new_args


def main():
    # Set up arg parser and parse
    parser = argparse.ArgumentParser(description="Do something, then send a notification.")
    parser.add_argument('arguments', nargs='*', help="Things to do.")
    parser.add_argument('-m', '--message', dest='message', help="Message to send.", default="pyBullet task complete.")
    parser.add_argument('-t', '--title', dest='title', help="Title of the message.", default="pyBullet")
    parser.add_argument('--save', dest='save', help="Store this set of commands with this name.", default=None)
    parser.add_argument('--recall', dest='recall', help="Recall a set of commands with this name.", default=None)
    parser.add_argument('-b', '--break', dest='brk', help="Stop when one task returns something other than 0.", default=False, action="store_true")
    parser.add_argument('-e', '--each', dest='each', help="Send a notification for each task.", default=False, action="store_true")
    parser.add_argument('-r', '--return', dest='code', help="Send return codes with notifications.", default=False, action="store_true")
    parser.add_argument('-s', '--shell', dest='shell', help="Run the arguments in a shell. Dangerous.", default=False, action="store_true")
    parser.add_argument('-f', '--strict', dest='strict', help="Do not fail gracefully. Raise all errors.", default=False, action="store_true")
    parser.add_argument('-w', '--warn', dest='warn', help="Show SSL warnings.", default=False, action="store_true")
    parser.add_argument('-q', '--quiet', dest='silent', help="Send no notifications.", default=False, action="store_true")
    args = parser.parse_args()
    pb = pyBullet()

    # Save/recall args
    saved_args = None
    if args.recall:
        inpath = path.join(path.dirname(path.abspath(__file__)), str(args.recall)+".saved_args")
        if not path.isfile(inpath):
            print("Could not locate saved command set \""+str(args.recall)+"\".")
            return 1
        with open(inpath, 'r') as fp:
            saved_args = json.load(fp)
        args = make_fakespace(saved_args, args)

    elif args.save:
        out = json.dumps(vars(args))
        outpath = path.join(path.dirname(path.abspath(__file__)), str(args.save)+".saved_args")
        with open(outpath, 'w') as fp:
            fp.write(out)

    if not args.warn:
        requests.packages.urllib3.disable_warnings()

    # Join args into a single string, then split on commas. Join the args with the appropriate separator for the OS
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
            message = pb.build_message(args.title, args.message, ret, task_number, code=args.code, each=args.each)
            response = pb.push(message[0], message[1])
        # Stop if we are breaking
        if args.brk and ret != 0:
            broke = True
            break
        task_number += 1

    if not args.each and not args.silent:
        message = (args.title, args.message)
        if args.brk and broke:
            message = pb.build_message(args.title, args.message, ret, task_number, code=True, each=True)
        elif args.code:
            message = pb.build_message(args.title, args.message, ret, task_number, code=True)
        response = pb.push(message[0], message[1])

if __name__ == "__main__":
    main()
