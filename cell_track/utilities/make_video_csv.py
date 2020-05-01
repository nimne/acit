from cell_track.tools.trackmate import drawTrackmateVideo
import os
import argparse
import glob

# Parallelize over folders..:
# parallel 'python make_video_csv.py -f {}' ::: /path/to/dir/*


def getArgs():
    parser = argparse.ArgumentParser(description='Draw videos and cumulative csv.')
    required = parser.add_argument_group('Required')
    required.add_argument('--folder', '-f', help='The tiff folder to process, need trakmate XML files',
                          required=True)
    return parser.parse_args()


args = getArgs()

file_list = glob.glob(os.path.join(args.folder, '*.tif'))

print('Making videos and compiling data')
if os.path.exists(os.path.join(args.folder, 'alldata.csv')):
    os.remove(os.path.join(args.folder, 'alldata.csv'))

for file in file_list:
    drawTrackmateVideo(file, os.path.join(args.folder, 'alldata.csv'))
