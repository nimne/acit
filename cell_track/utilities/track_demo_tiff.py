# import keras
import keras

# import keras_retinanet
from keras_retinanet import models
from keras_retinanet.utils.image import preprocess_image, resize_image
from keras_retinanet.utils.visualization import draw_box, draw_caption
import sys
sys.path.append("../..")
from cell_track.tools.box import filter_boxes
from PIL import Image, ImageSequence
# import miscellaneous modules
import cv2
import os
import numpy as np
import time
import skvideo.io

from cell_track.tools import get_session

infile = 'demo_image/noninf_well1.tif'
import tensorflow as tf
tf.logging.set_verbosity(tf.logging.ERROR)


# use this environment flag to change which GPU to use
# os.environ["CUDA_VISIBLE_DEVICES"] = "1"

# set the modified tf session as backend in keras
keras.backend.tensorflow_backend.set_session(get_session())

# adjust this to point to your downloaded/trained model
# models can be downloaded here: https://github.com/fizyr/keras-retinanet/releases
model_path = os.path.join('..', 'trained_models', 'resnet50_csv_v1.0.h5')

# load retinanet model
model = models.load_model(model_path, backbone_name='resnet50')

# load label to names mapping for visualization purposes
labels_to_names = {0: 'cell'}

out_video = infile + '.mp4'
# out_csv = '../tracking_demo_image/out.csv'
PIL_image = Image.open(infile)
width, height = PIL_image.size
print('Converting ' + os.path.basename(infile))
writer = skvideo.io.FFmpegWriter(out_video, outputdict={
                                 '-vcodec': 'libx264',
                                 '-pix_fmt': 'yuv420p',
                                 '-r': '8',
                                 })
# load image
PIL_image = Image.open(infile)

# i is the frame, page is the PIL image object
for i, page in enumerate(ImageSequence.Iterator(PIL_image)):
    print("Image " + str(i))
    # this is the read BGR thing
    np_image = np.asarray(page.convert('RGB'))
    image = np_image[:, :, ::-1].copy()
    # copy to draw on
    draw = image.copy()
    draw = cv2.cvtColor(draw, cv2.COLOR_BGR2RGB)

    # preprocess image for network
    image = preprocess_image(image)
    image, scale = resize_image(image)

    # process image
    start = time.time()
    boxes, scores, labels = model.predict_on_batch(np.expand_dims(image, axis=0))
    print("processing time: ", time.time() - start)

    # correct for image scale
    boxes /= scale

    pre_passed_boxes = []
    pre_passed_scores = []
    for box, score, label in zip(boxes[0], scores[0], labels[0]):
        if score >= 0.2:
            pre_passed_boxes.append(box.tolist())
            pre_passed_scores.append(score.tolist())

    passed_boxes, passed_scores = filter_boxes(
        in_boxes=pre_passed_boxes, in_scores=pre_passed_scores,
        _passed_boxes=[], _passed_scores=[])  # These are necessary
    print("found " + str(len(passed_boxes)) + " cells in " +
          str(infile) + " frame " + str(i))
    for b, score in zip(passed_boxes, passed_scores):

        # b = box.astype(int)
        draw_box(draw, b, color=(0, 255, 0), thickness=1)

        caption = "{:.3f}".format(score)
        draw_caption(draw, b, caption)

    #cv2.imwrite('./tracking_demo_image/stack/out' + str(i) + '.png', draw)
    writer.writeFrame(draw)

writer.close()
