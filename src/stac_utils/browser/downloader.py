import glob
import os
import time
from collections import defaultdict
from typing import Iterator


class Downloader:
    """Iterator that looks for files in a directory and waits for one
    to finish downloading.

    Later calls will not return files that have already been given.

    Useful for Selenium where it's the only way to check
    whether a file finished downloading or not.

    """

    def __init__(self, directory: str, polling: float = 10.0, pattern: str = None):
        self.directory = directory
        self.returned_files = set()
        self.polling = polling
        self.pattern = pattern

    def clear(self):
        self.returned_files.clear()

    def check_for_new_files(self, pattern: str = None) -> Iterator[str]:
        print("Checking for new files")
        pattern = pattern if pattern is not None else self.pattern
        last_size = defaultdict(int)
        finished = set()
        while True:
            time.sleep(self.polling)
            directory_files = glob.glob(os.path.join(self.directory, pattern))

            if not directory_files:
                """No files so let's wait"""
                continue

            downloaded = [
                file for file in directory_files if file not in self.returned_files
            ]
            if not downloaded:
                """If there are files and we've already returned them all,
                stop iterating
                """
                break

            for download in downloaded:
                """Check each file, compare file size to last time it was checked
                and if it's been static, assume it's finished.
                """
                size = os.path.getsize(download)
                if (last_size[download] > 0) and (size == last_size[download]):
                    finished.add(download)
                elif size > 0:
                    last_size[download] = size

            for filename in finished:
                """Start spitting out finished files"""
                print(f"{filename} is complete")
                self.returned_files.add(filename)
                yield filename
