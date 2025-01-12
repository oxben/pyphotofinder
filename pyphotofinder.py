#!/usr/bin/python3

#
# Find files from src_dir not present in dst_dir and move them to synched_dir
# python .\pyphotofinder.py E:\SyncPhonePhotos\PhotosPixel4a\ D:\Photos\ E:\SyncPhonePhotos\synched\
#

import os
import re
import shutil
import subprocess
import sys
import time

# Android Debug Bridge path
ADB_PATH = r"C:\Apps\android-platform-tools-2407"

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
    finder = PyPhotoFinder(src_dir, dst_dir, sync_dir)
    #finder.parse_reference_tree()
    #finder.parse_import_tree()

    android_photos = list_android_photos()
    banner("Android Photos: " + str(len(android_photos)))
    print(android_photos[0])


#-------------------------------------------------------------------------------

def banner(str):
    print("-------------------------------------------------------------------")
    print(str)
    print("-------------------------------------------------------------------")


#-------------------------------------------------------------------------------

class PyPhotoFinder:

    def __init__(self, src_dir, dst_dir, sync_dir):
        self._src_dir = src_dir
        self._dst_dir = dst_dir
        self._sync_dir = sync_dir
        self._dst_photos = {}

    def pull_android_photos_to_src_dir():
        '''
        Pull photos from the Android device to the source directory on the PC
        '''
        # List all Android photos
        # For each photo check if it is already present in the synched directory
        # Pull photo if it is absent from the synched directory
        pass

    def parse_reference_tree(self):
        '''
        Parse reference tree which is also the destination directory where the photos should be stored
        at the end.
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

def add_adb_to_path():
    '''Add the directory containing adb.exe to the PATH'''
    original_path = os.environ['PATH']
    if not ADB_PATH in original_path:
        os.environ['PATH'] = ADB_PATH + ";" + original_path  # Temporarily modify PATH


def list_android_photos(remote_path='/sdcard/DCIM/Camera'):
    '''List all photos contained under the specified directory on an Android device'''
    add_adb_to_path()
    # Use adb to list all image files (jpg, png, etc.) in the specified directory and its subdirectories
    command = ['adb', 'shell', 'find', remote_path, '-type', 'f', '-name', '*.jpg', '-o', '-name', '*.mp4']
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print("ERROR: " + result.stderr)
        return []

    return result.stdout.splitlines()  # Return as a list of file paths


def copy_file_from_android(src, dst):
    '''Copy the specified src file from the Android device to the dst directory'''
    add_adb_to_path()
    # Use adb to pull the specified file from the Android device
    command = ['adb', 'pull', src, dst]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print("ERROR: " + result.stderr)

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    sys.exit(main())
