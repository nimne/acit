"""
Standalone script to run all parts of the cell tracking and output useful data.
"""
import sys
import os
from cell_track.tools.initialize import init
import cell_track

init()

local_path = os.path.dirname(cell_track.__file__)
model_path = os.path.join(local_path, 'trained_models/resnet50_csv_v1.0.h5')

def show_exception_and_exit(exc_type, exc_value, tb):
    """Capture exceptions and print them to the console before exiting."""
    import traceback
    traceback.print_exception(exc_type, exc_value, tb)
    input("Press key to exit.")
    sys.exit(-1)

sys.excepthook = show_exception_and_exit

def get_args():
    """Setup the command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(description='Split lif files and track them with retinanet.')
    parser.add_argument('--gpu',
                        help='Id of the GPU to use '
                             '(as reported by nvidia-smi).')
    parser.add_argument('--track', help='Track this file using trackmate.'
                                        'Requires ImageJ or FiJi in $PATH'
                                        ' with TrackMate and \'Track analysis\''
                                        ' plugin. Needed for --make_video',
                        action="store_true")
    parser.add_argument('--make_csv', help='Makes a CSV file from trackmate '
                                           'results. Requires --track',
                        action="store_true")
    parser.add_argument('--make_video',
                        help='Makes a video from the tiff files, and '
                             'compiles csv results from xml. Requires ffmpeg. '
                             '--track is required',
                        action="store_true")
    required = parser.add_argument_group('Required')
    required.add_argument('--lif_folder', '-l',
                          help='The tiff folder to process',
                          required=True)
    required.add_argument('--model', '-m', help='Directory of the model,'
                                                ' defaults to the model included'
                                                ' with the module',
                          default=model_path)
    required.add_argument('--out_folder', '-o', help='The output directory '
                                                     'containing TIFF stacks '
                                                     'and XML files',
                          required=True)
    return parser.parse_args()


if len(sys.argv) < 2:
    import PySimpleGUI as sg
    layout = [
        [sg.Text('Options:')],
        [sg.Checkbox('Track cells with trackmate', default=True, key="track"), ],
        [sg.Checkbox('Make csv files for all wells', default=True, key="csv"), ],
        [sg.Checkbox('Make mp4 videos with tracking data', default=True, key="video"), ],
        [sg.Text('Model:'), sg.InputText(model_path, key="model"), sg.FileBrowse()],
        [sg.Text('LIF folder:'), sg.InputText('Folder containing LIF files', key="lif"), sg.FolderBrowse()],
        [sg.Text('Output folder:'), sg.InputText('Output folder', key='output'), sg.FolderBrowse()],
        [sg.Submit(), sg.Cancel()]
    ]

    window = sg.Window('Track cell motility').Layout(layout)
    button, gui_val = window.Read()

    enable_gpu = False
    enable_track = gui_val['track']
    make_csv = gui_val['csv']
    make_video = gui_val['video']
    model_path = gui_val['model']
    lif_folder = gui_val['lif']
    out_folder = gui_val['output']


else:
    args = get_args()
    enable_gpu = args.gpu
    out_folder = args.out_folder
    model_path = args.model
    enable_track = args.track
    make_csv = args.make_csv
    make_video = args.make_video
    lif_folder = args.lif_folder

# Yes.. this is against PEP8, but this prevents taking time to load
# tensorflow if all we're doing is looking at the arguments.
import tensorflow as tf  # noqa
tf.logging.set_verbosity(tf.logging.ERROR)
import keras  # noqa
import os  # noqa
import glob  # noqa
from cell_track.tools import get_session, safe_load_model  # noqa
from cell_track.tools.track_image import track_lif  # noqa


lif_list = glob.glob(os.path.join(lif_folder, '*.lif'))
if len(lif_list) > 1:
    raise ValueError("No LIF files to process.")

def getOutLifPath(lif_path):
    """Create the path for the output files"""
    outfilename = os.path.basename(lif_path)
    outdirname = os.path.splitext(outfilename)[0]
    return os.path.join(out_folder, outdirname)

# Use GPU if available / enabled
if enable_gpu:
    os.environ['CUDA_VISIBLE_DEVICES'] = enable_gpu

keras.backend.tensorflow_backend.set_session(get_session())

# convert into inference model
print('Loading model')
model = safe_load_model(model_path)

# ML/track on the files
for liffile in lif_list:
    outpath = getOutLifPath(liffile)
    track_lif(liffile, outpath, model)

# Run tracking through ImageJ
if enable_track:
    import subprocess
    import shutil

    imagej_bins = ['ImageJ-linux64',
                   'ImageJ-macosx',
                   'ImageJ',
                   'ImageJ-win64.exe',
                   str(os.environ.get('IJ_BIN_PATH'))]
    imagej_path = None
    for bin in imagej_bins:
        which_path = shutil.which(bin)
        if which_path is not None:
            imagej_path = bin
            break

    if imagej_path is None:
        raise RuntimeError("Can't find ImageJ exec. Link / Add 'ImageJ' to the $PATH")

    for liffile in lif_list:
        outpath = getOutLifPath(liffile)
        if sys.platform.startswith('win'):
            os.system(imagej_path + ' --ij2 --headless --console --run "./ImageJ/TrackmateHeadlessPyWin.py" "infilename=\'' + outpath + '\'"')
        else:
            subprocess.run([imagej_path, '--headless', './ImageJ/TrackmateHeadlessPy.py', outpath])

# Make summary CSV files for each lif?
if make_csv:
    from cell_track.tools.trackmate import process_xml_folder
    for liffile in lif_list:
        outpath = getOutLifPath(liffile)

        for dir, subFolders, files in os.walk(outpath):
            for subdir in subFolders:
                print("Making CSVs in folder: " + subdir)
                process_xml_folder(os.path.join(outpath, subdir))


if make_video:
    if not enable_track:
        raise RuntimeError('--make_video requires --track')
    from cell_track.tools.trackmate import drawTrackmateVideo

    print('Making video, compiling csv files.')

    for liffile in lif_list:
        outpath = getOutLifPath(liffile)

        for dir, subFolders, files in os.walk(outpath):
            for subdir in subFolders:
                print("Processing folder: " + subdir)
                tiff_list = glob.glob(os.path.join(dir, subdir, '*.tif'), )
                for file in tiff_list:
                    drawTrackmateVideo(file, os.path.join(outpath, subdir, 'alldata.csv'))
