# pyBullet
## An automatic task notifier
I wrote pyBullet while running very long builds at work. The goal of the project is to make it safe to work on other things while waiting on very long builds - without the risk of not noticing the build was complete. This is accomplished by using push notifications through Pushbullet.

### Requirements
1. Python 2.7 or Python 3.x  
2. [requests module](http://docs.python-requests.org/en/latest/)  
3. [Pushbullet](https://www.pushbullet.com/) account/app

### Installation
1. Clone this repo somewhere easy to access. I like to make a symlink in my path so I can call it from anywhere.
2. Enter your Pushbullet API key into the file `api.pub`, located in the same folder as `pyBullet.py`

### Usage
General usage is like so:  
`$ pyBullet.py -m "Build Complete" -t "ProductID" /path/to/pull/script, /path/to/build/script`  
There are three different arguments here, the first being the message to send in the notification, the second being the title of the notification, and the third being a comma separated list of commands to call. pyBullet will call all given commands, then send a notification based on the title and message given once all commands are complete.

There are also quite a few other flags and features, most notably the [save and recall](#save-and-recall) feature.

| Option | Description | Example |
| ------ | ----------- | ------- |
| -m | The message to use in the notification. Default: `pyBullet task complete.` | `-m "task complete"` |
| -t | The title to use in the notification. Default: `pyBullet` | `-t "Task Name"` |
| --save | Save this set of arguments with this name. Can later be recalled. | `--save task_name` |
| --recall | Recall a saved set of arguments with this name. Any args specified here will override the saved args. | `--recall task_name` |
| --list | Displays all saved command sets. | N/A |
| -b | If a task has a return code other than 0, do not execute the rest of the commands. Displays the failing command. | `Task 3 failed.` |
| -e | Send a notification for each task, appending the task number to the title. | `Task Name : Task 1` |
| -r | Add the return code to the message. | `Task Complete : Returned 0` |
| -s | Run the given commands in a shell. Allows the use of environment setup scripts, but could be dangerous. See [here](https://docs.python.org/2/library/subprocess.html#frequently-used-arguments). Makes the -e and -b flags have no effect. | N/A |
| -f | Turn on strict mode. If any command fails because it cannot be executed (not because of its return code), the exception will be raised instead of displaying a warning. | N/A |
| -w | Turn on SSL warnings. By default they are disabled. | N/A |
| -q | Quiet mode. Do not send any notifications. | N/A |

### Save and Recall
One of my most common tasks is pulling, then building the source for a very large project. The full command to do so looks like this (doing Windows development these days):  
```
pyBullet.py -s -r -t "ProductName Build" -m "Build Complete"
C:\Users\My.Name\Downloads\SetupScript\SetupScript.bat,
C:\ProductName\debug\src\commonscripts\build\InternalBuildSystem.py pull,
C:\ProductName\debug\src\commonscripts\build\InternalBuildSystem.py build
```

Nasty, right? No one wants to type all that every time. Admittedly, without using pyBullet, it's much easier, just a call to the setup script, pull, then build. However, if I was to add the --save flag to that command:  
```
pyBullet.py --save pull_and_build -s -r -t "ProductName Build" -m "Build Complete"
C:\Users\My.Name\Downloads\SetupScript\SetupScript.bat,
C:\ProductName\debug\src\commonscripts\build\InternalBuildSystem.py pull,
C:\ProductName\debug\src\commonscripts\build\InternalBuildSystem.py build
```

Now, after typing all of that only once I can run `pyBullet.py --recall pull_and_build` to run the exact same command with the exact same arguments.
