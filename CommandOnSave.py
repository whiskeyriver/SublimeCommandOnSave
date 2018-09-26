import os
import re
import sys
import shlex
import subprocess

import sublime
import sublime_plugin


_STATUS_KEY = "CommandOnSave"


class CommandOnSave(sublime_plugin.EventListener):
    def on_post_save_async(self, view):
        settings = sublime.load_settings("CommandOnSave.sublime-settings").get(
            "commands"
        )

        if settings is None:
            return

        filename = view.file_name()
        before_stat = None

        view.erase_status(_STATUS_KEY)
        for path, commands in settings.items():
            if filename.startswith(path):
                for command in commands:
                    if before_stat is None:
                        before_stat = os.stat(filename)
                    try:
                        output = self._exec(command, filename)
                    except subprocess.CalledProcessError as e:
                        print(e)
                        view.set_status(
                            _STATUS_KEY, "ERROR: Command failed: {e.output}".format(e=e)
                        )
                        print(
                            "CommandOnSave failed code {e.returncode}; output: {e.output}".format(
                                e=e
                            ),
                            file=sys.stderr,
                        )
                        # attempt to execute any other commands

        if before_stat is not None and not view.is_dirty():
            after_stat = os.stat(filename)
            if before_stat.st_mtime != after_stat.st_mtime:
                # it seems like the file changed: reload the view
                view.run_command("revert")

    def _exec(self, command: str, filename: str):
        """Perform the command execution.

        Args:
            command (str): The command string
            filename (str): The fully-qualified file name

        Returns:
            str: The command output

        Raises:
            subprocess.CalledProcessError
        """
        command_sub = re.sub(r"\b_file_\b", filename, command)
        command_args = shlex.split(command_sub)

        result = subprocess.check_output(command_args)
        return result
