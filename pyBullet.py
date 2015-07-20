#!/usr/bin/env python3
import requests
import json
import os.path as path
import argparse
import subprocess


class pyBullet:
    def __init__(self, api_key=None):
        if not api_key:
            self.header = {"Content-Type": "application/json"}
            self.url = "https://api.pushbullet.com/v2/pushes"
            config_path = path.join(path.dirname(path.abspath(__file__)), "api.pub")
            if not path.isfile(config_path):
                raise FileNotFoundError("No api key specified and api.pub not found.")
            with open(config_path, 'r') as fp:
                self.api_key = fp.read().strip()
        else:
            self.api_key = api_key

    def push(self, title, body):
        jsonized_data = json.dumps({"title": title, "body": body, "type": "note"})
        response = requests.post(self.url, headers=self.header, auth=(self.api_key, ""), data=jsonized_data)
        print(response)


def main():
    parser = argparse.ArgumentParser(description="Do something, then send a notification.")
    parser.add_argument('arguments', nargs='*', help="Things to do.")
    parser.add_argument('-m', '--message', dest='multiple', help="Message to send.")
    parser.add_argument('-t', '--title', dest='title', help="Title of the message.")
    args = "".join(parser.parse_args().arguments)
    args = args.replace(" ", "")
    cmds = filter(bool, args.split(','))
    for cmd in cmds:
        out = subprocess.call(cmd, shell=True)
    pb = pyBullet()
    pb.push("Done!", "I did some things.")

if __name__ == "__main__":
    main()
