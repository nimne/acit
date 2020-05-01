import unittest
import keras
from keras_retinanet import models
from cell_track.tools.track_image import track_tiff_folder
from cell_track.tools import get_session, safe_load_model
import tempfile
from shutil import copy
import warnings
import os
keras.backend.tensorflow_backend.set_session(get_session())

modelpath = "./cell_track/trained_models/resnet50_csv_v1.0.h5"
model = safe_load_model(modelpath)

track_tiff_folder("reference_files/", model)
