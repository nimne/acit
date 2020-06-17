import os
import numpy as np
import time
from cell_track.tools.trackmate import trackmateXML
from cell_track.tools.box import filter_boxes
from keras_retinanet.utils.image import preprocess_image, resize_image
import keras
from readlif.reader import LifFile

#Todo: Reduce code redundancy between the functions
def track_lif(lif_path: str, out_path: str , model: keras.models.Model) -> None:
    """
    Applies ML model (model object) to everything in the lif file.

    This will write a trackmate xml file via the method tm_xml.write_xml(),
    and save output tiff image stacks from the lif file.

    Args:
        lif_path (str): Path to the lif file
        out_path (str): Path to output directory
        model (str): A trained keras.models.Model object

    Returns: None
    """
    print("loading LIF")
    lif_data = LifFile(lif_path)
    print("Iterating over lif")
    for image in lif_data.get_iter_image():
        folder_path = "/".join(str(image.path).strip("/").split('/')[1:])
        path = folder_path + str(image.name)
        name = image.name

        if os.path.exists(os.path.join(out_path, path + '.tif.xml')) \
           or os.path.exists(os.path.join(out_path, path + '.tif.trackmate.xml')):
            print(str(path) + '.xml' + ' exists, skipping')
            continue

        make_dirs = os.path.join(out_path, image.path)
        if not os.path.exists(make_dirs):
            os.makedirs(make_dirs)

        print("Processing " + str(path))
        start = time.time()
        # initialize XML creation for this file
        tm_xml = trackmateXML()
        i = 1
        image_out = image.get_frame()  # Initialize the output image
        images_to_append = []
        for frame in image.get_iter_t():
            images_to_append.append(frame)
            np_image = np.asarray(frame.convert('RGB'))
            image_array = np_image[:, :, ::-1].copy()

            tm_xml.filename = name + '.tif'
            tm_xml.imagepath = os.path.join(out_path, image.path)
            if tm_xml.nframes < i:  # set nframes to the maximum i
                tm_xml.nframes = i
            tm_xml.frame = i
            # preprocess image for network
            image_array = preprocess_image(image_array)
            image_array, scale = resize_image(image_array)

            # process image
            boxes, scores, labels = model.predict_on_batch(np.expand_dims(image_array, axis=0))

            # correct for image scale
            boxes /= scale

            # filter the detection boxes
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
                  str(path) + " frame " + str(i))

            # tell the trackmate writer to add the passed_boxes to the final output xml
            tm_xml.add_frame_spots(passed_boxes, passed_scores)
            i += 1
        # write the image to trackmate, prepare for next image
        print("processing time: ", time.time() - start)
        tm_xml.write_xml()
        image_out.save(os.path.join(out_path, path + '.tif'),
                       format="tiff",
                       append_images=images_to_append[1:],
                       save_all=True,
                       compression='tiff_lzw')


def track_tiff_folder(tiff_folder: str, model: keras.models.Model) -> None:
    """
    Applies ML model (model object) to every tiff file in the directory.

    This will write a trackmate xml file via the method tm_xml.write_xml(),
    and save output tiff image stacks from the lif file.

    Args:
        lif_path (str): Path to the lif file
        out_path (str): Path to output directory
        model (keras.models.Model): A trained keras.models.Model object

    Returns: None
    """
    from PIL import Image, ImageSequence
    for file in os.listdir(tiff_folder):
        if file.endswith(".tif"):
            filepath = os.path.join(tiff_folder, file)
            if os.path.exists(os.path.join(tiff_folder, file + '.xml')):
                print(str(file) + '.xml' + ' exists, skipping')
            else:

                # load image
                PIL_image = Image.open(filepath)
                print("Processing " + str(filepath))
                start = time.time()
                # initialize XML creation for this file
                tm_xml = trackmateXML()
                # i is the frame, page is the PIL image object
                for i, page in enumerate(ImageSequence.Iterator(PIL_image)):
                    # this is the read BGR thing
                    np_image = np.asarray(page.convert('RGB'))
                    image = np_image[:, :, ::-1].copy()

                    tm_xml.filename = file
                    tm_xml.imagepath = tiff_folder
                    if tm_xml.nframes < i:  # set nframes to the maximum i
                        tm_xml.nframes = i
                    tm_xml.frame = i
                    # preprocess image for network
                    image = preprocess_image(image)
                    image, scale = resize_image(image)

                    # process image
                    boxes, scores, labels = model.predict_on_batch(np.expand_dims(image, axis=0))

                    # correct for image scale
                    boxes /= scale

                    # filter the detection boxes
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
                          str(file) + " frame " + str(i))

                    # tell the trackmate writer to add the passed_boxes to the final output xml
                    tm_xml.add_frame_spots(passed_boxes, passed_scores)

                # write the image to trackmate, prepare for next image
                print("processing time: ", time.time() - start)
                tm_xml.write_xml()

