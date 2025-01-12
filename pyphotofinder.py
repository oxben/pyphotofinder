#!/usr/bin/python3

"""
Script to synchronize photos from two directories or from an Android device
and a directory.

Find files from src_dir not present in dst_dir and move them to synched_dir
python .\pyphotofinder.py E:\SyncPhonePhotos\PhotosPixel4a\ D:\Photos\ E:\SyncPhonePhotos\synched\

Android Debug Bridge is used to retrieve the files from the Android device:
- Doc: https://developer.android.com/tools/adb?hl=en
Shell commands supported by ADB mainly comes from Toybox:
- http://landley.net/toybox/status.html

Default photo filename on Pixel phones: PXL_20240423_084532187.jpg (len: 26)

Author: oxben@free.fr
"""

from itertools import islice
import os
import re
import shutil
import subprocess
import sys
import time


# Android Debug Bridge path
ADB_PATH = r"C:\Apps\android-platform-tools-2407"

# Android default camera photos path
ANDROID_DCIM_PATH = "/sdcard/DCIM/Camera"

# Debug mode
DEBUG=True


#-------------------------------------------------------------------------------

def main():
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} src_directory dst_directory synched_directory")
        print("")
        print("Example:")
        print("  python .\pyphotofinder.py E:\SyncPhonePhotos\PhotosPixel4a\ D:\Photos\ E:\SyncPhonePhotos\synched\ ")
        return 1

    src_dir = sys.argv[1]
    dst_dir = sys.argv[2]
    sync_dir = sys.argv[3]

    banner("PyPhotoFinder")
    android = AndroidDevice(debug=DEBUG)
    finder = PyPhotoFinder(src_dir, dst_dir, sync_dir, android, debug=DEBUG)
    finder.parse_reference_tree()
    finder.list_android_photos()
    finder.find_missing_android_photos()
    #finder.parse_import_tree()

    # android_photos = android.list_photos()
    # banner(f"Android Photos: {len(android_photos)}")
    # print(f"{android_photos[0]}\n{android_photos[1]}")

    # android_photos = android.stat_photos()
    # banner(f"Android Photos and Sizes: {len(android_photos)}")
    # print(f"{android_photos[0]}\n{android_photos[1]}")


#-------------------------------------------------------------------------------

def banner(str):
    print("-------------------------------------------------------------------")
    print(str)
    print("-------------------------------------------------------------------")


#-------------------------------------------------------------------------------

class PyPhotoFinder:

    IDX_NAME = 0
    IDX_SIZE = 1

    def __init__(self, src_dir, dst_dir, sync_dir, android_device, debug=False):
        self._src_dir = src_dir
        self._dst_dir = dst_dir
        self._sync_dir = sync_dir
        self._dst_photos = {}  # Dict key: basename value: (fullname, size)
        self._android_device = android_device
        self._android_photos = [] # List of tuples (fullname, size)
        self._debug = debug


    def list_android_photos(self):
        '''
        List all photos from the Android device and get their size
        '''
        banner("List Android photos")
        self._android_photos = self._android_device.stat_photos(ANDROID_DCIM_PATH)
        print(f"Android photos: {len(self._android_photos)}")
        print("\n".join(map(str, self._android_photos[:4])))


    def pull_android_photos_to_src_dir():
        '''
        Pull photos from the Android device to the source directory on the PC
        '''
        # List all Android photos
        # For each photo check if it is already present in the synched directory
        # Pull photo if it is absent from the synched directory
        pass


    def find_missing_android_photos(self):
        '''
        List photos that are present on the Android device but not in the destination directory
        '''
        banner("Find missing Android photos")

        print("\n".join(map(str, islice(self._dst_photos.items(), 4))))

        start_time = time.time()
        missing_photos = {}
        diff_size_photos = {}
        for photo in self._android_photos:
            basename = os.path.basename(photo[self.IDX_NAME])
            size = int(photo[self.IDX_SIZE])
            if basename in self._dst_photos:
                found = False
                for dst_photo in self._dst_photos[basename]:
                    if dst_photo[self.IDX_SIZE] == size:
                        found = True
                if not found:
                    diff_size_photos[basename] = photo
            else:
                missing_photos[basename] = photo
        end_time = time.time()

        if self._debug:
            print(f"Elapsed time: {end_time - start_time:.3f} seconds")
        print(f"Missing photos: {len(missing_photos)}")
        print(f"Photos with non-matching size: {len(diff_size_photos)}")

        return missing_photos


    def parse_reference_tree(self):
        '''
        Parse reference tree which is also the destination directory where the photos should be
        stored at the end.
        '''
        banner("Parse reference directory")
        parsed_dirs = 0
        dup_names = 0
        start_time = time.time()
        for root, dirs, files in os.walk(self._dst_dir, topdown=False):
            print(root)
            parsed_dirs += 1
            for name in files:
                if name.lower()[-4:] in (".jpg", ".mp4"):
                    path = os.path.join(root, name)
                    size = os.stat(path).st_size
                    if name in self._dst_photos.keys():
                        self._dst_photos[name].append((path, size))
                        dup_names += 1
                    else:
                        self._dst_photos[name] = [(path, size)]
        end_time= time.time()

        print(f"Indexed {len(self._dst_photos)} photos from {self._dst_dir} in {end_time - start_time:.1f} seconds")
        print(f"{parsed_dirs} directories parsed")
        print(f"{dup_names} duplicated names found")


    def parse_import_tree(self):
        '''
        Parse import tree, the directory that contains the photos to synchronized
        '''
        banner("Synchronize files")
        files_checked = 0
        files_present = 0
        files_missing = 0
        # Regex for extracting date (year, month) from photos filename
        img_re = re.compile("[A-Z]+_(\d\d\d\d)(\d\d)\d\d_\d\d\d\d\d\d[\d]*.*\.\w\w\w")

        # Go through the source tree
        start_time = time.time()
        for root, dirs, files in os.walk(self._src_dir, topdown=False):
            print(root)
            for name in files:
                files_checked += 1
                # For each jpg or mp4 files in the tree, check if a file with the same name and size
                # exists in the reference directory
                if name.lower()[-4:] in (".jpg", ".mp4"):
                    path = os.path.join(root, name)
                    size = os.stat(path).st_size
                    found = False
                    if name in self._dst_photos.keys():
                        for photo in self._dst_photos[name]:
                            if photo[1] == size:
                                found = True
                                files_present += 1
                                # Move file to synched_dir
                                shutil.move(path, os.path.join(self._sync_dir, name))
                                break
                    if not found:
                        # The file is not present in the reference directory
                        files_missing += 1
                        # Move file to 'missing/YEAR/MONTH/' subdir in synched_dir if date can be extracted
                        # Move to 'missing/' subdir otherwise
                        match = img_re.match(name)
                        if (match):
                            year = match.group(1)
                            month = match.group(2)
                            sync_subdir = os.path.join(self._sync_dir, "missing", year + "-" + month)
                            os.makedirs(sync_subdir, exist_ok=True)
                            shutil.move(path, os.path.join(sync_subdir, name))
                        else:
                            shutil.move(path, os.path.join(self._sync_dir, "missing", name))
                else:
                    print(name)
        end_time = time.time()

        print(f"Checked {files_checked} photos in {end_time - start_time:.1f} seconds")
        print(f"{files_present} files matched")
        print(f"{files_missing} files missing from {self._dst_dir}")


#-------------------------------------------------------------------------------

class AndroidDevice:
    '''
    Class used to execute command on Android device
    '''

    def __init__(self, debug=False):
        '''Constructor'''
        self._debug = debug
        self.add_adb_to_path()


    def add_adb_to_path(self):
        '''Add the directory containing adb.exe to the PATH'''
        original_path = os.environ['PATH']
        if not ADB_PATH in original_path:
            os.environ['PATH'] = ADB_PATH + ";" + original_path  # Temporarily modify PATH


    def execute_shell_command(self, command_line):
        '''
        Execute Android shell command via ADB.
        Shell command passed in must not contains spaces in the argument values (eg. in paths)
        Return stdout content when command succeeds, None otherwise
        '''
        if self._debug:
            banner(f"Executing command: {command_line}")
        command = ['adb', 'shell'] + command_line.split(' ')
        print(command)

        start_time = time.time()
        result = subprocess.run(command, capture_output=True, text=True)
        end_time = time.time()

        if result.returncode != 0:
            print("ERROR: " + result.stderr)
            return None
        if self._debug:
            print(f"Elapsed time: {end_time - start_time:.3f} seconds")
        return result.stdout


    def list_photos(self, remote_path='/sdcard/DCIM/Camera'):
        '''
        List all photos (jpg and mp4) in the specified directory and its subdirectories
        of an Android device
        '''
        result = self.execute_shell_command(f"find {remote_path} -type f -name *.jpg -o -name *.mp4")
        if not result:
            print("ERROR: Failed to list photos")
            return []

        return result.splitlines()  # Return as a list of file paths


    def stat_photos(self, remote_path='/sdcard/DCIM/Camera'):
        '''
        Use stat command to list all photos contained under the specified directory
        of an Android device and get their size
        '''
        result = self.execute_shell_command(f"stat -c %n@%s {remote_path}/*.jpg {remote_path}/*.mp4")
        if not result:
            print("ERROR: Failed to stat photos")
            return []
        files_and_sizes = [tuple(line.split('@')) for line in result.splitlines()]
        return files_and_sizes  # Return as a list of tuples (filename, size_in_bytes)


    def copy_file_from_device(self, src, dst):
        '''Copy the specified src file from the Android device to the dst directory'''
        command = ['adb', 'pull', src, dst]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print("ERROR: " + result.stderr)

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    sys.exit(main())
