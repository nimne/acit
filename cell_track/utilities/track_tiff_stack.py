import keras
from keras_retinanet import models
import argparse
import tensorflow as tf
import os

from cell_track.tools.track_image import track_tiff_folder
from cell_track.tools import get_session, safe_load_model
# Requires:
# tensorflow
# keras
# keras_retinanet
# numpy

parser = argparse.ArgumentParser(description='Simple training script for training a RetinaNet network.')
parser.add_argument('--gpu', help='Id of the GPU to use (as reported by nvidia-smi).')

required = parser.add_argument_group('Required')
required.add_argument('--tiff_folder', '-t', help='The tiff folder to process',
                      required=True)
required.add_argument('--model', '-m', help='Directory of the model', required=True)
args = parser.parse_args()

tiff_folder = args.tiff_folder
modelpath = args.model



if args.gpu:
    os.environ['CUDA_VISIBLE_DEVICES'] = args.gpu

keras.backend.tensorflow_backend.set_session(get_session())

# convert into inference model
model = safe_load_model(modelpath)


track_tiff_folder(tiff_folder, model)
