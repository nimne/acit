"""
Unit tests for the cell tracking to make sure that the results remain
consistent despite code changes.

Todo: Implement testing for LIF files directly?
"""
import unittest
import keras
from cell_track.tools.track_image import track_tiff_folder
from cell_track.tools import get_session, safe_load_model
import tempfile
from shutil import copy
import warnings
import os
from cell_track.tools.initialize import init


class TestBoxOutput(unittest.TestCase):
    def setUp(self) -> None:
        keras.backend.tensorflow_backend.set_session(get_session())

    def test_tracking(self):
        from xml.etree import ElementTree as ET
        from cell_track.tools.trackmate import Track
        with tempfile.TemporaryDirectory() as tmpdir:
            copy('tests/reference_files/Well1-Pos001-1.tif', tmpdir)
            # convert into inference model
            modelpath = "cell_track/trained_models/resnet50_csv_v1.0.h5"
            model = safe_load_model(modelpath)
            track_tiff_folder(tmpdir, model)

            # The order of the spots can not be assumed to be the same,
            # need to parse the XML and compare.
            ref_tree = ET.parse("tests/reference_files/Well1-Pos001-1.tif.xml")
            test_tree = ET.parse(os.path.join(tmpdir, "Well1-Pos001-1.tif.xml"))

            ref_root = ref_tree.getroot()
            test_root = test_tree.getroot()

            ref_tracks = [Track(xml_track, ref_root) for xml_track in ref_root.findall('Model/AllTracks/Track')]
            test_tracks = [Track(xml_track, test_root) for xml_track in test_root.findall('Model/AllTracks/Track')]

            self.assertEqual(len(ref_tracks), len(test_tracks))
            for i in range(len(ref_tracks)):
                self.assertEqual(len(ref_tracks[i].spots_in_track),
                                 len(test_tracks[i].spots_in_track))




if __name__ == "__main__":
    init()
    unittest.main()
