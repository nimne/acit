"""
This tiny script is used to convert the alp annotations in the training
set to a csv that is useful for training.

Like this whole python module, this script only identifies a single kind of thing (cells).

Essentially, this converts the output from ALP's labeling tool into the
expected csv format. For the csv, the file needs to have the columns:
    img_file,x1,y1,x2,y2,class_name
where x1, y1, x2, y2 define the squares.

Note that these need to be in pixel positions, while ImageJ will
normally stay with micrometers if available.

It is highly recommended to add a bunch of images lacking cells in the training set.

This script assumes a few things. First, the directory structure must match this:
    training/
    ├── convert_alp_annotations.py
    ├── keras_train.py
    ├── train/
        ├── category.csv
        ├── no_cells/
        └── cells/

It is expected that the ALP annotations are in the 'no_cells' and 'cells' folders.
See the readme and documentation for more information about how to run the training.

"""

import os
import fnmatch

def um_to_px(number):
    scale = 1 # Edit this number for the um to px conversion
    return float(float(number) * scale) # For the example data, the value is 0.5426

# Clear the 'imagej_alp_train.csv' file
with open('imagej_alp_train.csv', 'w'):
    pass

for file in os.listdir('./train/no_cells/'):
    if fnmatch.fnmatch(file, '*.tif'):
        with open('imagej_alp_train.csv', 'a') as outfile:
            outfile.write('./train/no_cells/'
                          + str(file) + ',,,,,\n')


def one_cat_alp(directory, category, outfname):
    for fname in os.listdir(directory):
        if fnmatch.fnmatch(fname, '*.txt'):
            print(f'Converting {fname}')
            basename = str(fname[:-4])
            with open(directory + fname, 'r') as f:
                for line in f:
                    line_list = line.split(' ')
                    out_line = str(directory + str(basename + '.tif')
                                   + ',' +
                                   str(int(round(um_to_px(line_list[4]))))
                                   + ',' +
                                   str(int(round(um_to_px(line_list[5]))))
                                   + ',' +
                                   str(int(round(um_to_px(line_list[6]))))
                                   + ',' +
                                   str(int(round(um_to_px(line_list[7]))))
                                   + ',' + category +
                                   '\n')
                    with open(outfname, 'a') as writefile:
                        writefile.write(out_line)


one_cat_alp(directory='./train/cells/',
            category='cell',
            outfname='imagej_alp_train.csv')

