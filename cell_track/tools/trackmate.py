import glob
import os
import re
from xml.etree import ElementTree as ET

import pandas as pd

from cell_track.tools.box import get_box_center


class Track:
    """
    Class for handling a 'track' as defined in the trackmate XML document.
    Initialization of this class will parse the trackmate XML track.

    Because most attributes are extracted from an xml (text file) they are
    represented as str objects.

    Args:
         xml_track (ElementTree): root.findall('Model/AllTracks/Track')
            for each individual track
         xml_root (ElementTree): tree.getroot(), the root of the XML tree

    Attributes:
        id (str): The ID of the track
        num_spots (str): Number of spots in the track
        num_gaps (str): Number of gaps in the track
        total_displacement (str): Total displacement of the track
        index (str): The track index (different than track ID)
        mean_speed (str): Mean speed of the track
        median_speed (str): Median speed of the track
        total_dist_traveled (str): Total distance traveled (sum of edges)
        max_dist_traveled (str): Maximum distance traveled
        processivity (str): total displacement / total distance traveled
        x_loc (int): Center x location of the track
        y_loc (int): Center y location of the track
        include (bool): Did this pass the trackmate filtering?
        edges (list): List of IDs for the edges in the track
        spots_in_track (list): IDs of the spots in the track
        spot_objs (list): List of Spot objects, representing all spots
        lines (list): List of Line objects for each line in the track

    Examples:
        >>> tree = ET.parse(inxml)
        >>> root = tree.getroot()
        >>>
        >>> tracks = [Track(xml_track, root) for xml_track in root.findall('Model/AllTracks/Track')]
        >>> filt_tracks = [x for x in tracks if x.include]
        >>> edge_nest = [x.lines for x in tracks if x.include]
        >>> line_list = [item for sublist in edge_nest for item in sublist]

    """
    def __init__(self, xml_track, xml_root):
        include = [trackid.get('TRACK_ID') for trackid in xml_root.findall('Model/FilteredTracks/TrackID')]

        class Line:
            """
            Class for holding 'line' data. It holds the x and y corrdinates
            of where all the lines start and end. Mostly to make the code
            more readable.

            Args:
                spot_start (tuple): (x1, y1) of the line beginning
                spot_end (tuple): (x1, y1) of the line end

            Attributes:
                x1y1 (tuple): (x1, y1) of line beginning
                x2y2 (tuple): (x2, y2) of line ending
            """
            def __init__(self, spot_start, spot_end):
                self.x1y1 = spot_start
                self.x2y2 = spot_end

        class Spot:
            """
            Class for holding 'spot' data. Mostly exists to make the code
            more readable.

            Args:
                xml_data (ElementTree): root.findall('Model/AllSpots/')
                frame_num (int): Frame number

            Attributes:
                id (str): The ID of the spot
                frame (int): The frame number where the spot is found
                x (int): x position of the spot
                y (int): y position of the spot

            """
            def __init__(self, xml_data, frame_num):
                self.id = xml_data.get('ID')
                self.frame = int(round(float(frame_num)))
                self.x = int(round(float(xml_data.get('POSITION_X'))))
                self.y = int(round(float(xml_data.get('POSITION_Y'))))

        self.id = xml_track.get('TRACK_ID')
        self.num_spots = xml_track.get('NUMBER_SPOTS')
        self.num_gaps = xml_track.get('NUMBER_GAPS')
        self.total_displacement = xml_track.get('TRACK_DISPLACEMENT')
        self.index = xml_track.get('TRACK_INDEX')
        self.mean_speed = xml_track.get('TRACK_MEAN_SPEED')
        self.median_speed = xml_track.get('TRACK_MEDIAN_SPEED')
        self.total_dist_traveled = xml_track.get('TOTAL_DISTANCE_TRAVELED')
        self.max_dist_traveled = xml_track.get('MAX_DISTANCE_TRAVELED')
        self.processivity = xml_track.get('CONFINMENT_RATIO')
        self.x_loc = int(round(float(xml_track.get('TRACK_X_LOCATION'))))
        self.y_loc = int(round(float(xml_track.get('TRACK_Y_LOCATION'))))
        self.include = xml_track.get('TRACK_ID') in include
        self.edges = xml_track.findall('Edge')

        edge_source = []
        spot_list = []
        for edge in self.edges:
            id_pair = (edge.get('SPOT_SOURCE_ID'), edge.get('SPOT_TARGET_ID'))
            spot_list.append(edge.get('SPOT_SOURCE_ID'))
            spot_list.append(edge.get('SPOT_TARGET_ID'))
            edge_source.append(id_pair)

        self.spots_in_track = spot_list

        spot_obj_list = []
        for spot_xmlobj in xml_root.findall('Model/AllSpots/'):
            frame = spot_xmlobj.get('frame')
            for child in spot_xmlobj:
                if child.get('ID') in self.spots_in_track:
                    spot_obj_list.append(Spot(child, frame))

        self.spot_objs = spot_obj_list

        spot_dict = {spot.id: spot for spot in self.spot_objs}
        self.lines = []

        for pair in edge_source:
            start = (spot_dict[pair[0]].x, spot_dict[pair[0]].y)
            end = (spot_dict[pair[1]].x, spot_dict[pair[1]].y)
            self.lines.append(Line(start, end))


def drawTrackmateVideo(infile, out_csv):
    """
    Takes a tif file, with a matching trackmate file, and makes a mp4 video
    of the tracked output. This will draw a spot ID, and a trail on the video.

    This will also write a csv file containing the x position, y position,
    spot frame, and track id. This can be used later to draw lines using

    Args:
        infile (str): .tif filename to convert
        out_csv (str): The csv file to write to. This is opened in append mode.

    Returns:
        None: This does not return any value, but will write a .mp4 file and
            .csv file.

    """
    import cv2
    import numpy as np
    import skvideo.io
    from PIL import Image, ImageSequence
    # infile = '../tracking_demo_image/Well1-Pos001.tif'
    inxml = infile + '.trackmate.xml'
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

    tree = ET.parse(inxml)
    root = tree.getroot()

    tracks = [Track(xml_track, root) for xml_track in root.findall('Model/AllTracks/Track')]

    filt_tracks = [x for x in tracks if x.include]
    edge_nest = [x.lines for x in tracks if x.include]
    line_list = [item for sublist in edge_nest for item in sublist]

    # i is the frame, page is the PIL image object
    for i, img in enumerate(ImageSequence.Iterator(PIL_image)):
        page = np.asarray(img.convert('RGB'))
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 0.5
        fontColor = (255, 100, 255)
        lineType = 1
        page = cv2.cvtColor(page, cv2.COLOR_BGR2RGB)
        for line in line_list:
            cv2.line(page, line.x1y1, line.x2y2, (255, 255, 255), 1)

        for track_obj in filt_tracks:
            for spot in track_obj.spot_objs:
                if spot.frame == i:
                    bottomLeftCornerOfText = (spot.x + 2, spot.y)
                    cv2.putText(page, track_obj.id,
                                bottomLeftCornerOfText,
                                font,
                                fontScale,
                                fontColor,
                                lineType)

        writer.writeFrame(page)

    writer.close()

    with open(out_csv, 'a') as f:
        for track in filt_tracks:
            for spot in track.spot_objs:
                f.write(str(spot.frame) + "," +
                        str(spot.x) + "," +
                        str(spot.y) + "," +
                        str(track.id) + "," +
                        str(os.path.basename(infile)) + "\n"
                        )


class trackmateXML:
    """
    Class for constructing, and writing the trackmate XML from the ML tracking tools.

    Note, this currently has a hard-coded frame duration of 300 seconds.
    Todo: Update the hardcoded frame duration.

    Args:
        None

    Attributes:
        spot_id (int): The ID of the spot being added. This will auto increment.
        frame (int): The frame being added.
        total_spots (int): Total number of spots added to the obejct.
        filename (str): The name of the output xml file
        content (str): The 'body' of the XMl file
        imagepath (str): The path to the tiff file that the trackmate XMl is
            associated with
        header (str): The trackmate header
        footer1 (str): First trackmate footer
        footer2 (str): Second trackmate footer
        footer3 (str): Third trackmate footer

    """
    def __init__(self):
        self.spot_id = 1
        self.frame = 0
        self.total_spots = 0
        self.nframes = 0
        self.filename = 'default.xml'
        self.content = ''
        self.imagepath = ''
        self.header = """<?xml version="1.0" encoding="UTF-8"?>
  <TrackMate version="3.8.0">
    <Model spatialunits="micron" timeunits="sec">
    <FeatureDeclarations>
      <SpotFeatures>
        <Feature feature="QUALITY" name="Quality" shortname="Quality" dimension="QUALITY" isint="false" />
        <Feature feature="POSITION_X" name="X" shortname="X" dimension="POSITION" isint="false" />
        <Feature feature="POSITION_Y" name="Y" shortname="Y" dimension="POSITION" isint="false" />
        <Feature feature="POSITION_Z" name="Z" shortname="Z" dimension="POSITION" isint="false" />
        <Feature feature="POSITION_T" name="T" shortname="T" dimension="TIME" isint="false" />
        <Feature feature="FRAME" name="Frame" shortname="Frame" dimension="NONE" isint="true" />
        <Feature feature="RADIUS" name="Radius" shortname="R" dimension="LENGTH" isint="false" />
        <Feature feature="VISIBILITY" name="Visibility" shortname="Visibility" dimension="NONE" isint="true" />
        <Feature feature="MANUAL_COLOR" name="Manual spot color" shortname="Spot color" dimension="NONE" isint="true" />
        <Feature feature="MEAN_INTENSITY" name="Mean intensity" shortname="Mean" dimension="INTENSITY" isint="false" />
        <Feature feature="MEDIAN_INTENSITY" name="Median intensity" shortname="Median" dimension="INTENSITY" isint="false" />
        <Feature feature="MIN_INTENSITY" name="Minimal intensity" shortname="Min" dimension="INTENSITY" isint="false" />
        <Feature feature="MAX_INTENSITY" name="Maximal intensity" shortname="Max" dimension="INTENSITY" isint="false" />
        <Feature feature="TOTAL_INTENSITY" name="Total intensity" shortname="Total int." dimension="INTENSITY" isint="false" />
        <Feature feature="STANDARD_DEVIATION" name="Standard deviation" shortname="Stdev." dimension="INTENSITY" isint="false" />
        <Feature feature="ESTIMATED_DIAMETER" name="Estimated diameter" shortname="Diam." dimension="LENGTH" isint="false" />
        <Feature feature="CONTRAST" name="Contrast" shortname="Constrast" dimension="NONE" isint="false" />
        <Feature feature="SNR" name="Signal/Noise ratio" shortname="SNR" dimension="NONE" isint="false" />
      </SpotFeatures>
      <EdgeFeatures>
        <Feature feature="SPOT_SOURCE_ID" name="Source spot ID" shortname="Source ID" dimension="NONE" isint="true" />
        <Feature feature="SPOT_TARGET_ID" name="Target spot ID" shortname="Target ID" dimension="NONE" isint="true" />
        <Feature feature="LINK_COST" name="Link cost" shortname="Cost" dimension="NONE" isint="false" />
        <Feature feature="EDGE_TIME" name="Time (mean)" shortname="T" dimension="TIME" isint="false" />
        <Feature feature="EDGE_X_LOCATION" name="X Location (mean)" shortname="X" dimension="POSITION" isint="false" />
        <Feature feature="EDGE_Y_LOCATION" name="Y Location (mean)" shortname="Y" dimension="POSITION" isint="false" />
        <Feature feature="EDGE_Z_LOCATION" name="Z Location (mean)" shortname="Z" dimension="POSITION" isint="false" />
        <Feature feature="VELOCITY" name="Velocity" shortname="V" dimension="VELOCITY" isint="false" />
        <Feature feature="DISPLACEMENT" name="Displacement" shortname="D" dimension="LENGTH" isint="false" />
        <Feature feature="MANUAL_COLOR" name="Manual edge color" shortname="Edge color" dimension="NONE" isint="true" />
      </EdgeFeatures>
      <TrackFeatures>
        <Feature feature="NUMBER_SPOTS" name="Number of spots in track" shortname="N spots" dimension="NONE" isint="true" />
        <Feature feature="NUMBER_GAPS" name="Number of gaps" shortname="Gaps" dimension="NONE" isint="true" />
        <Feature feature="LONGEST_GAP" name="Longest gap" shortname="Longest gap" dimension="NONE" isint="true" />
        <Feature feature="NUMBER_SPLITS" name="Number of split events" shortname="Splits" dimension="NONE" isint="true" />
        <Feature feature="NUMBER_MERGES" name="Number of merge events" shortname="Merges" dimension="NONE" isint="true" />
        <Feature feature="NUMBER_COMPLEX" name="Complex points" shortname="Complex" dimension="NONE" isint="true" />
        <Feature feature="TRACK_DURATION" name="Duration of track" shortname="Duration" dimension="TIME" isint="false" />
        <Feature feature="TRACK_START" name="Track start" shortname="T start" dimension="TIME" isint="false" />
        <Feature feature="TRACK_STOP" name="Track stop" shortname="T stop" dimension="TIME" isint="false" />
        <Feature feature="TRACK_DISPLACEMENT" name="Track displacement" shortname="Displacement" dimension="LENGTH" isint="false" />
        <Feature feature="TRACK_INDEX" name="Track index" shortname="Index" dimension="NONE" isint="true" />
        <Feature feature="TRACK_ID" name="Track ID" shortname="ID" dimension="NONE" isint="true" />
        <Feature feature="TRACK_X_LOCATION" name="X Location (mean)" shortname="X" dimension="POSITION" isint="false" />
        <Feature feature="TRACK_Y_LOCATION" name="Y Location (mean)" shortname="Y" dimension="POSITION" isint="false" />
        <Feature feature="TRACK_Z_LOCATION" name="Z Location (mean)" shortname="Z" dimension="POSITION" isint="false" />
        <Feature feature="TRACK_MEAN_SPEED" name="Mean velocity" shortname="Mean V" dimension="VELOCITY" isint="false" />
        <Feature feature="TRACK_MAX_SPEED" name="Maximal velocity" shortname="Max V" dimension="VELOCITY" isint="false" />
        <Feature feature="TRACK_MIN_SPEED" name="Minimal velocity" shortname="Min V" dimension="VELOCITY" isint="false" />
        <Feature feature="TRACK_MEDIAN_SPEED" name="Median velocity" shortname="Median V" dimension="VELOCITY" isint="false" />
        <Feature feature="TRACK_STD_SPEED" name="Velocity standard deviation" shortname="V std" dimension="VELOCITY" isint="false" />
        <Feature feature="TRACK_MEAN_QUALITY" name="Mean quality" shortname="Mean Q" dimension="QUALITY" isint="false" />
        <Feature feature="TRACK_MAX_QUALITY" name="Maximal quality" shortname="Max Q" dimension="QUALITY" isint="false" />
        <Feature feature="TRACK_MIN_QUALITY" name="Minimal quality" shortname="Min Q" dimension="QUALITY" isint="false" />
        <Feature feature="TRACK_MEDIAN_QUALITY" name="Median quality" shortname="Median Q" dimension="QUALITY" isint="false" />
        <Feature feature="TRACK_STD_QUALITY" name="Quality standard deviation" shortname="Q std" dimension="QUALITY" isint="false" />
      </TrackFeatures>
    </FeatureDeclarations>"""  # noqa
        self.footer1 = """</AllSpots>
        <AllTracks />
        <FilteredTracks />
      </Model>
      <Settings>"""
        self.footer3 = """<BasicSettings xstart="0" xend="1391" ystart="0" yend="1039" zstart="0" zend="0" tstart="0" tend="60" />
    <DetectorSettings DETECTOR_NAME="LOG_DETECTOR" TARGET_CHANNEL="1" RADIUS="20.0" THRESHOLD="0.2" DO_MEDIAN_FILTERING="true" DO_SUBPIXEL_LOCALIZATION="false" />
    <InitialSpotFilter feature="QUALITY" value="0.0" isabove="true" />
    <SpotFilterCollection />
    <TrackerSettings />
    <TrackFilterCollection />
    <AnalyzerCollection>
      <SpotAnalyzers>
        <Analyzer key="MANUAL_SPOT_COLOR_ANALYZER" />
        <Analyzer key="Spot descriptive statistics" />
        <Analyzer key="Spot radius estimator" />
        <Analyzer key="Spot contrast and SNR" />
      </SpotAnalyzers>
      <EdgeAnalyzers>
        <Analyzer key="Edge target" />
        <Analyzer key="Edge mean location" />
        <Analyzer key="Edge velocity" />
        <Analyzer key="MANUAL_EDGE_COLOR_ANALYZER" />
      </EdgeAnalyzers>
      <TrackAnalyzers>
        <Analyzer key="Branching analyzer" />
        <Analyzer key="Track duration" />
        <Analyzer key="Track index" />
        <Analyzer key="Track location" />
        <Analyzer key="Velocity" />
        <Analyzer key="TRACK_SPOT_QUALITY" />
      </TrackAnalyzers>
    </AnalyzerCollection>
  </Settings>
  <GUIState state="SpotFilter">
    <View key="HYPERSTACKDISPLAYER" />
  </GUIState>
</TrackMate>"""  # noqa

    def _add_spots(self, box, score):
        """
        Used to add one or more spots to the trackmate object. This is needs to be called
        from the add_frame_spots, and not called directly. (PRIVATE)

        Args:
            box (list): List of tuples in the form (x1, x2, y1, y2) of boxes to add.
            score (list): List of scores to accompany the boxes. THe score is stored
                in the 'QUALITY' attribute of the trackmate XML.

        Returns:
            None

        """
        spot_num = int(len(box))
        self.total_spots += spot_num
        centerx, centery = get_box_center(box)
        self.content += ('\t\t\t\t<Spot ID="' + str(self.spot_id) + '" '
                         'name="ID' + str(self.spot_id) + ''
                         '" QUALITY="' + str(score) + '" '
                         'POSITION_T="' + str(self.frame * 300) + '" '
                         'MAX_INTENSITY="100" FRAME="' + str(self.frame) + '" '
                         'MEDIAN_INTENSITY="60.0" VISIBILITY="1" '
                         'MEAN_INTENSITY="50" '
                         'TOTAL_INTENSITY="21000" '
                         'ESTIMATED_DIAMETER="20" RADIUS="10.0" '
                         'SNR="0.5" '
                         'POSITION_X="' + str(centerx) + '" '
                         'POSITION_Y="' + str(centery) + '" '
                         'STANDARD_DEVIATION="20" '
                         'CONTRAST="0.2" '
                         'MANUAL_COLOR="-10921639" MIN_INTENSITY="0.0" '
                         'POSITION_Z="0.0" />\n')
        self.spot_id += 1

    def add_frame_spots(self, box, scores):
        """
        This is the public method to add spots to the trackmate xml. This will
        add the required header to tell trackmate which frame the spots belong to.

        When adding spots to the trackmate XML object, it is necessary to set
        the 'frame' attribute of the object instance to the correct frame.

        _add_spots() does the heavy lifting here.

        Args:
            box (list): List of tuples in the form (x1, x2, y1, y2) of boxes to add.
            score (list): List of scores to accompany the boxes. THe score is stored
                in the 'QUALITY' attribute of the trackmate XML.

        Returns:

        """
        self.content += '\t\t\t<SpotsInFrame frame="' + str(self.frame) + '">\n'
        for spot, score in zip(box, scores):
            self._add_spots(spot, score)
        self.content += '\t\t\t</SpotsInFrame>\n'

    def write_xml(self):
        """
        This method writes the trackmate XML with all of the spot data.

        The location that it is written to is the 'imagepath' + 'filename' with
        .xml appended to the end.

        Returns:
            None
        """
        self.footer2 = ('\n\t\t<ImageData filename="' + str(self.filename) + '" '
                        'folder="./" width="1392" '
                        'height="1040" nslices="1" nframes="' + str(self.nframes) + '" '
                        'pixelwidth="1.843" pixelheight="1.843" voxeldepth="1.0" '
                        'timeinterval="300.0" />\n')
        self.header += '\n\t\t<AllSpots nspots="' + str(self.total_spots) + '">\n'
        with open(os.path.join(self.imagepath, self.filename + '.xml'), 'w') as f:
            f.write(self.header)
            f.write(self.content)
            f.write(self.footer1)
            f.write(self.footer2)
            f.write(self.footer3)


def process_imagestack(well):
    """Processes a single image stack (xml file) and returns three lists,
    mean_speed, processivity, max_displacement.
    """
    tree = ET.parse(well)
    root = tree.getroot()
    try:
        scale = float(root.find('Settings/ImageData').get('pixelwidth'))
    except:
        scale = 1
    filteredTrackId = [track.get('TRACK_ID') for track in root.findall('Model/FilteredTracks/TrackID')]

    class track():
        def __init__(self, xml_track):
            self.id = xml_track.get('TRACK_ID')
            self.num_spots = xml_track.get('NUMBER_SPOTS')
            self.num_gaps = xml_track.get('NUMBER_GAPS')
            self.total_displacement = xml_track.get('TRACK_DISPLACEMENT')
            self.index = xml_track.get('TRACK_INDEX')
            self.mean_speed = float(xml_track.get('TRACK_MEAN_SPEED'))
            self.median_speed = xml_track.get('TRACK_MEDIAN_SPEED')
            self.total_dist_traveled = xml_track.get('TOTAL_DISTANCE_TRAVELED')
            self.max_dist_traveled = float(xml_track.get('MAX_DISTANCE_TRAVELED'))
            self.processivity = float(xml_track.get('CONFINMENT_RATIO'))
            #self.XML

    tracks = [track(xml_track) for xml_track in root.findall('Model/AllTracks/Track')]

    mean_speed = [track_data.mean_speed / scale for track_data in tracks
                  if track_data.id in filteredTrackId]
    processivity = [track_data.processivity / scale for track_data in tracks
                    if track_data.id in filteredTrackId]
    max_displacement = [track_data.max_dist_traveled / scale for track_data in tracks
                        if track_data.id in filteredTrackId]
    return mean_speed, processivity, max_displacement


def process_well_list(well_string, xml_file_list):
    """Takes a well name (well_string) and an xml_file_list (all XML file paths) returns
    three pandas dataframes"""
    print("Processing " + str(well_string))
    match_well = [i for i in xml_file_list if str(well_string + '-') in i]
    mean_speed, processivity, max_displacement = [], [], []
    for well in match_well:
        speed, process, disp = process_imagestack(well)
        mean_speed.extend(speed)
        processivity.extend(process)
        max_displacement.extend(disp)
    speed_um = pd.to_numeric(pd.Series(mean_speed))
    processivity_um = pd.to_numeric(pd.Series(processivity))
    max_displacement_um = pd.to_numeric(pd.Series(max_displacement))
    return speed_um, processivity_um, max_displacement_um


def process_xml_folder(folder):
    print("Processing folder " + str(folder))
    xml_file_list = glob.glob(os.path.join(folder, '*trackmate.xml'), )

    well_search = re.compile('(Well[0-9]*)')
    well_list = list(set([well_search.search(well).group(0) for well in xml_file_list]))
    speed_dict, processivity_dict, max_displacement_dict = {}, {}, {}

    for well in well_list:
        speed, processivity, max_displacement = process_well_list(well, xml_file_list)
        well_num = int(well[4:])
        speed_dict[well_num] = speed
        processivity_dict[well_num] = processivity
        max_displacement_dict[well_num] = max_displacement

    speed_df = pd.DataFrame(speed_dict)
    processivity_df = pd.DataFrame(processivity_dict)
    max_displacement_df = pd.DataFrame(max_displacement_dict)

    speed_df.to_csv(os.path.join(folder, 'All_wells_speed.csv'), index=False)
    processivity_df.to_csv(os.path.join(folder, 'All_wells_processivity.csv'), index=False)
    max_displacement_df.to_csv(os.path.join(folder, 'All_wells_max_displacement.csv'), index=False)