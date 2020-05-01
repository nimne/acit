import os
from pathlib import Path
import gzip
from urllib.request import urlopen
import hashlib
import sys
import requests
import cell_track


def download(url, filename):
    # From https://sumit-ghosh.com/articles/python-download-progress-bar/
    with open(filename, 'wb') as f:
        response = requests.get(url, stream=True)
        total = response.headers.get('content-length')

        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            for data in response.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                downloaded += len(data)
                f.write(data)
                done = int(50*downloaded/total)
                sys.stdout.write('\r[{}{}]'.format('█' * done, '.' * (50-done)))
                sys.stdout.flush()
    sys.stdout.write('\n')


def init(traindata=False):
    """Function to download the trained model and training data.

    The trained model and training data are quite large, and it's
    not realistic to host them on github. This function downloads them
    from a server with less expensive bandwidth.

    Returns:
        bool: True for files exist.
    """

    import cell_track

    local_path = os.path.dirname(cell_track.__file__)
    model_path = os.path.join(local_path, 'trained_models/resnet50_csv_v1.0.h5')
    model_dir = os.path.join(local_path, 'trained_models/')
    Path(model_dir).mkdir(parents=True, exist_ok=True)

    p = Path(os.path.abspath(os.path.dirname(__file__)))
    if os.path.exists(model_path):
        return True
    else:
        print("Looks like the inference model isn't downloaded, downloading to: \n"
              + str(model_path))
        print("This file is large (~149 mb), please be patient")
        # 1. Download
        # 2. md5sum (if wrong, delete, raise value error
        download('https://cdn.nimne.com/acit/resnet50_csv_v1.0.h5', str(model_path))

        with open(model_path, 'rb') as f_check:
            dl_model_md5 = hashlib.md5(f_check.read()).hexdigest()

        if not dl_model_md5 == "47fdbca809e6bd767b123e8aa0299a1b":
            os.remove(model_path)
            raise ValueError("md5 mismatch between downloaded model and expected. "
                             "Please try again. If this fails, raise a github issue.")

        elif not os.path.exists(model_path):
            raise ValueError("Failed to download inference model, please "
                             "retry in a few minutes. If this fails, raise "
                             "an issue on GitHub")
        else:
            return True




    p = Path(os.path.abspath(os.path.dirname(__file__)))
    training_data = p / ".." / "utilities" / "training" / "train" / "cells" / "1.tiff"
    cells_dir = p / ".." / "utilities" / "training" / "train" / "cells"
    no_cells_dir = p / ".." / "utilities" / "training" / "train" / "no_cells"
    if os.path.exists(training_data):
        return True
    elif traindata:
        print("Looks like the training data isn't downlaoded, downloading..")
        # 1. Download the list of filenames + md5s (check md5)
        # 2. Download the files (check md5s along the way)
        # 3. If there is an error.. delete everything and raise value error

        if not os.path.exists(training_data):
            raise ValueError("Failed to download training data, please "
                             "retry in a few minutes. If this fails, raise "
                             "an issue on GitHub")
