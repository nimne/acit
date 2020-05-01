#@String infilename
from fiji.plugin.trackmate.visualization.hyperstack import HyperStackDisplayer
from fiji.plugin.trackmate.io import TmXmlReader
from fiji.plugin.trackmate import Logger
from fiji.plugin.trackmate import Settings
from fiji.plugin.trackmate import SelectionModel
from fiji.plugin.trackmate.detection import ManualDetectorFactory
from fiji.plugin.trackmate.providers import DetectorProvider
from fiji.plugin.trackmate.providers import TrackerProvider
from fiji.plugin.trackmate.providers import SpotAnalyzerProvider
from fiji.plugin.trackmate.providers import EdgeAnalyzerProvider
from fiji.plugin.trackmate.providers import TrackAnalyzerProvider
from java.io import File
import fiji.plugin.trackmate.TrackMate as TrackMate
import fiji.plugin.trackmate.tracking.sparselap.SparseLAPTrackerFactory as SparseLAPTrackerFactory
import fiji.plugin.trackmate.tracking.LAPUtils as LAPUtils
import fiji.plugin.trackmate.features.FeatureFilter as FeatureFilter
import fiji.plugin.trackmate.features.track.TrackSpeedStatisticsAnalyzer as TrackSpeedStatisticsAnalyzer
import fiji.plugin.trackmate.features.track.TrackDurationAnalyzer as TrackDurationAnalyzer
import fiji.plugin.trackmate.features.track.TrackBranchingAnalyzer as TrackBranchingAnalyzer
import fiji.plugin.trackmate.features.track.TrackIndexAnalyzer as TrackIndexAnalyzer
import fiji.plugin.trackmate.Model as Model
import fiji.plugin.trackmate.LoadTrackMatePlugIn_ as LoadTrackMatePlugIn_
from fiji.plugin.trackmate.action import ExportTracksToXML
from fiji.plugin.trackmate.features.edges import EdgeTargetAnalyzer, EdgeTimeLocationAnalyzer, EdgeVelocityAnalyzer
import fiji.plugin.trackmate.action.CaptureOverlayAction as CaptureOverlayAction
import fiji.plugin.trackmate.action.ISBIChallengeExporter as ISBIChallengeExporter
import fiji.plugin.trackmate.visualization.TrackMateModelView as TrackMateModelView
import fiji.plugin.trackmate.io.TmXmlWriter as TmXmlWriter
from fiji.plugin.trackmate.features.edge import LinearTrackEdgeStatistics
from fiji.plugin.trackmate.features.track import LinearTrackDescriptor
import sys
import glob
import os

#----------------
# Setup variables
#----------------

# Put here the path to the TrackMate file you want to load
def magic(file):
    # We have to feed a logger to the reader.
    logger = Logger.IJ_LOGGER

    #-------------------
    # Instantiate reader
    #-------------------

    reader = TmXmlReader(File(file))
    if not reader.isReadingOk():
        sys.exit(reader.getErrorMessage())
    #-----------------
    # Get a full model
    #-----------------

    # This will return a fully working model, with everything
    # stored in the file. Missing fields (e.g. tracks) will be
    # null or None in python
    model = reader.getModel()
    # model is a fiji.plugin.trackmate.Model

    #model = Model()
    #model.setSpots(model2.getSpots(), True)

    #----------------
    # Display results
    #----------------

    # We can now plainly display the model. It will be shown on an
    # empty image with default magnification.
    sm = SelectionModel(model)
    #displayer = HyperStackDisplayer(model, sm)
    #displayer.render()

    #---------------------------------------------
    # Get only part of the data stored in the file
    #---------------------------------------------

    # You might want to access only separate parts of the
    # model.

    spots = model.getSpots()
    # spots is a fiji.plugin.trackmate.SpotCollection

    logger.log(str(spots))

    # If you want to get the tracks, it is a bit trickier.
    # Internally, the tracks are stored as a huge mathematical
    # simple graph, which is what you retrieve from the file.
    # There are methods to rebuild the actual tracks, taking
    # into account for everything, but frankly, if you want to
    # do that it is simpler to go through the model:

    #---------------------------------------
    # Building a settings object from a file
    #---------------------------------------

    # Reading the Settings object is actually currently complicated. The
    # reader wants to initialize properly everything you saved in the file,
    # including the spot, edge, track analyzers, the filters, the detector,
    # the tracker, etc...
    # It can do that, but you must provide the reader with providers, that
    # are able to instantiate the correct TrackMate Java classes from
    # the XML data.

    # We start by creating an empty settings object
    settings = Settings()

    # Then we create all the providers, and point them to the target model:
    detectorProvider        = DetectorProvider()
    trackerProvider         = TrackerProvider()
    spotAnalyzerProvider    = SpotAnalyzerProvider()
    edgeAnalyzerProvider    = EdgeAnalyzerProvider()
    trackAnalyzerProvider   = TrackAnalyzerProvider()

    # Ouf! now we can flesh out our settings object:
    reader.readSettings(settings, detectorProvider, trackerProvider, spotAnalyzerProvider, edgeAnalyzerProvider, trackAnalyzerProvider)
    settings.detectorFactory = ManualDetectorFactory()


    # Configure tracker - We want to allow merges and fusions
    settings.initialSpotFilterValue = 0
    settings.trackerFactory = SparseLAPTrackerFactory()
    settings.trackerSettings = LAPUtils.getDefaultLAPSettingsMap()  # almost good enough
    settings.trackerSettings['ALLOW_TRACK_SPLITTING'] = True
    settings.trackerSettings['ALLOW_TRACK_MERGING'] = False
    settings.trackerSettings['LINKING_MAX_DISTANCE'] = 40.0
    settings.trackerSettings['ALLOW_GAP_CLOSING'] = True
    settings.trackerSettings['ALLOW_TRACK_SPLITTING'] = True
    settings.trackerSettings['GAP_CLOSING_MAX_DISTANCE'] = 30.0
    settings.trackerSettings['MAX_FRAME_GAP'] = 4

    # Configure track analyzers - Later on we want to filter out tracks
    # based on their displacement, so we need to state that we want
    # track displacement to be calculated. By default, out of the GUI,
    # not features are calculated.

    # The displacement feature is provided by the TrackDurationAnalyzer.

    settings.addTrackAnalyzer(TrackDurationAnalyzer())
    settings.addTrackAnalyzer(TrackBranchingAnalyzer())
    settings.addTrackAnalyzer(TrackIndexAnalyzer())
    settings.addTrackAnalyzer(TrackSpeedStatisticsAnalyzer())
    settings.addTrackAnalyzer(LinearTrackDescriptor())
    # Configure track filters - We want to get rid of the two immobile spots at
    # the bottom right of the image. Track displacement must be above 10 pixels.

    filter2 = FeatureFilter('NUMBER_SPOTS', 31, True)
    settings.addTrackFilter(filter2)
    #filter3 = FeatureFilter('NUMBER_GAPS', 2, False)
    #settings.addTrackFilter(filter3)
    filter4 = FeatureFilter('NUMBER_SPLITS', 0.5, False)
    settings.addTrackFilter(filter4)


    settings.addEdgeAnalyzer(EdgeTargetAnalyzer())
    settings.addEdgeAnalyzer(EdgeTimeLocationAnalyzer())
    settings.addEdgeAnalyzer(EdgeVelocityAnalyzer())
    settings.addEdgeAnalyzer(LinearTrackEdgeStatistics())

    #-------------------
    # Instantiate plugin
    #-------------------
    logger.log(str('\n\nSETTINGS:'))
    logger.log(unicode(settings))
    print("tracking")
    spots = model.getSpots()
    # spots is a fiji.plugin.trackmate.SpotCollection

    logger.log(str(spots))
    logger.log(str(spots.keySet()))


    # The settings object is also instantiated with the target image.
    # Note that the XML file only stores a link to the image.
    # If the link is not valid, the image will not be found.
    #imp = settings.imp
    #imp.show()

    # With this, we can overlay the model and the source image:

    trackmate = TrackMate(model, settings)

    #--------
    # Process
    #--------

    ok = trackmate.checkInput()
    if not ok:
        sys.exit(str(trackmate.getErrorMessage()))

    trackmate.execInitialSpotFiltering()
    trackmate.execSpotFiltering(True)
    trackmate.execTracking()
    trackmate.computeTrackFeatures(True)
    trackmate.execTrackFiltering(True)
    trackmate.computeEdgeFeatures(True)

    outfile = TmXmlWriter(File(str(file[:-4] + ".trackmate.xml")))
    outfile.appendSettings(settings)
    outfile.appendModel(model)
    outfile.writeToFile()

    ISBIChallengeExporter.exportToFile(model, settings, File(str(file[:-4] + ".ISBI.xml")))

rootdir = infilename
print(rootdir)
for dir, subFolders, files in os.walk(rootdir):
    for file in subFolders:
        print("Trackmate processing folder: " + dir)
        tiff_list = glob.glob(os.path.join(dir, file, '*.xml'), )
        for infile in tiff_list:
            if not (infile.endswith('trackmate.xml') or infile.endswith('ISBI.xml')):
                print("Processing file " + infile)
                magic(infile)
                if os.path.exists(infile):
                    os.remove(infile)
