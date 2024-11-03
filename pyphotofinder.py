#!/usr/bin/python3

#
# Find files from src_dir not present in dst_dir and move them to synched_dir
# python .\pyphotofinder.py E:\SyncPhonePhotos\PhotosPixel4a\ d:\Photos\ E:\SyncPhonePhotos\synched\
#

import os
import re
import shutil
import sys
import time

if len(sys.argv) < 4:
    print(f"Usage: {sys.argv[0]} src_directory dst_directory synched_directory")
src_dir = sys.argv[1]
dst_dir = sys.argv[2]
sync_dir = sys.argv[3]

dst_photos = {}

print("PyPhotoFinder")

# Parse reference tree
parsed_dirs = 0
dup_names = 0
start_time = time.time()
for root, dirs, files in os.walk(dst_dir, topdown=False):
    print(root)
    parsed_dirs += 1
    for name in files:
        if name.lower().endswith(".jpg"):
            path = os.path.join(root, name)
            size = os.stat(path).st_size
            if name in dst_photos.keys():
                dst_photos[name].append((path, size))
                dup_names += 1
            else:
                dst_photos[name] = [(path, size)]
end_time= time.time()

print(f"Indexed {len(dst_photos)} photos from {dst_dir} in {end_time - start_time:.1f} seconds")
print(f"{parsed_dirs} directories parsed")
print(f"{dup_names} duplicated names found")

# Parse import tree
files_checked = 0
files_present = 0
files_missing = 0
img_re = re.compile("[A-Z]+_(\d\d\d\d)(\d\d)\d\d_\d\d\d\d\d\d[\d]*.*\.\w\w\w")

start_time = time.time()
for root, dirs, files in os.walk(src_dir, topdown=False):
    print(root)
    for name in files:
        files_checked += 1
        #if name.lower().endswith(".jpg"):
        if name.lower()[-4:] in (".jpg", ".mp4"):
            path = os.path.join(root, name)
            size = os.stat(path).st_size
            found = False
            if name in dst_photos.keys():
                for photo in dst_photos[name]:
                    if photo[1] == size:
                        found = True
                        files_present += 1
                        # Move file to synched_dir
                        shutil.move(path, os.path.join(sync_dir, name))
                        break
            if not found:
                files_missing += 1
                # Move file to missing dir
                match = img_re.match(name)
                if (match):
                    year = match.group(1)
                    month = match.group(2)
                    sync_subdir = os.path.join(sync_dir, "missing", year + "-" + month)
                    os.makedirs(sync_subdir, exist_ok=True)
                    shutil.move(path, os.path.join(sync_subdir, name))
                else:
                    shutil.move(path, os.path.join(sync_dir, "missing", name))
        else:
            print(name)
end_time= time.time()

print(f"Checked {files_checked} photos in {end_time - start_time:.1f} seconds")
print(f"{files_present} files matched")
print(f"{files_missing} files missing from {dst_dir}")
