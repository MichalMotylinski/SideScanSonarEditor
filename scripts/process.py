
import pyXTF
import numpy as np
import math
import matplotlib as mpl
import time
import pickle
import pandas as pd
from PIL import Image
import bisect

def read_xtf(filepath, channel_num, decimation, auto_stretch, stretch):
    max_samples_port, max_slant_range, ping_count, mean_speed, navigation = get_sample_range(filepath, channel_num, True)
    across_track_sample_interval = (max_slant_range / max_samples_port) * decimation # sample interval in metres

    # to make the image somewhat isometric, we need to compute the alongtrack sample interval.  this is based on the ping times, number of pings and mean speed  where distance = speed * duration
    distance = mean_speed * (navigation[-1].dateTime.timestamp() - navigation[0].dateTime.timestamp())
    along_track_sample_interval = (distance / ping_count) 

    if auto_stretch:
        stretch = math.ceil(along_track_sample_interval / across_track_sample_interval)

    data = pyXTF.XTFReader(filepath)
    port_data = []
    starboard_data = []

    while data.moreData():
        ping = data.readPacket()
        # this is not a ping so skip it
        if ping == -999:
            continue

        channel = np.array(ping.pingChannel[0].data[::decimation])
        channel = np.multiply(channel, math.pow(2, - ping.pingChannel[0].Weight))
        filtered_port_data = channel.tolist()
        
        for i in range(stretch):
            port_data.insert(0, filtered_port_data[::-1])
        
        channel = np.array(ping.pingChannel[1].data[::decimation])
        channel = np.multiply(channel, math.pow(2, - ping.pingChannel[1].Weight))
        raw_starboard_data = channel.tolist()

        for i in range(stretch):
            starboard_data.insert(0, raw_starboard_data)
    
    return np.array(port_data), np.array(starboard_data)


def get_sample_range(filepath, channel_num, load_navigation):
    """iterate through the file to find the extents for range, time and samples.  These are all needed in subsequent processing """
    max_samples_port = 0
    max_range = 0
    ping_count = 0
    navigation = 0
    
    print("Gathering data limits...")
    #   open the XTF file for reading 
    data = pyXTF.XTFReader(filepath)
    if load_navigation:
        navigation = data.loadNavigation()
    
    mean_speed = 1
    start_time = time.time() # time the process

    while data.moreData():
        ping = data.readPacket()
        max_samples_port = max(ping.pingChannel[channel_num].NumSamples, max_samples_port)
        max_range = max(max_range, ping.pingChannel[channel_num].SlantRange)
        ping_count = ping_count + 1

    print("Get Sample Range Duration %.3fs" % (time.time() - start_time)) # print the processing time.
    return max_samples_port, max_range, ping_count, mean_speed, navigation


def find_min_max_clip_values(channel, clip):
    print ("Clipping data with an upper and lower percentage of:", clip)
    # compute a histogram of teh data so we can auto clip the outliers
    bins = np.arange(np.floor(channel.min()), np.ceil(channel.max()))
    hist, base = np.histogram(channel, bins=bins, density=1)    

    # instead of spreading across the entire data range, we can clip the outer n percent by using the cumsum.
    # from the cumsum of histogram density, we can figure out what cut off sample amplitude removes n % of data
    cumsum = np.cumsum(hist)
    
    minimum_bin_index = bisect.bisect(cumsum, clip / 100)
    maximum_bin_index = bisect.bisect(cumsum, (1 - clip / 100))

    return minimum_bin_index, maximum_bin_index

def convert_to_image(samples, invert, auto_min_max, channel_min=None, auto_scale=True, scale=None, color_scheme="greylog", cmap=None):
    gs_min = 0
    gs_max = 255
    
    #create numpy arrays so we can compute stats
    channel = np.array(samples)
    
    if auto_min_max:
        # compute the clips
        channel_min = channel.min()
        channel_max = channel.max()

        if channel_min > 0:
            channel_min = math.log(channel_min)
        else:
            channel_min = 0
        
        if channel_max > 0:
            channel_max = math.log(channel_max)
        else:
            channel_max = 0
    
    # this scales from the range of image values to the range of output grey levels
    if auto_scale:
        if (channel_max - channel_min) != 0:
            scale = (gs_max - gs_min) / (channel_max - channel_min)
    
    np.seterr(divide='ignore')

    if color_scheme == "greylog":
        channel = np.log(samples)

    channel = np.subtract(channel, channel_min)
    channel = np.multiply(channel, scale)

    if invert:
        channel = np.subtract(gs_max, channel)
    else:
        channel = np.add(gs_min, channel)

    if color_scheme == "color":
        if cmap is None:
            cmap = mpl.colors.ListedColormap({
                'black': (
                    (0.0, 0.0, 0.0),
                    (0.5, 0.0, 0.1),
                    (1.0, 1.0, 1.0),
                ),
                'white': (
                    (0.0, 0.0, 0.0),
                    (1.0, 0.0, 0.0),
                    (1.0, 1.0, 1.0),
                ),
                'yellow': (
                    (0.0, 0.0, 0.0),
                    (1.0, 0.0, 0.0),
                    (1.0, 1.0, 1.0),
                )})
        else:
            cmap = mpl.colors.ListedColormap(cmap)
        image = Image.fromarray(np.uint8(cmap(channel)*255))
    else:
        image = Image.fromarray(channel).convert('L')
    return image

def load_color_map(path):
    df = pd.read_csv(path, delim_whitespace=True)
    cmap = mpl.colors.ListedColormap({
        'black': (
            (0.0, 0.0, 0.0),
            (0.5, 0.0, 0.1),
            (1.0, 1.0, 1.0),
        ),
        'yellow': (
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
        )})
    return

def merge_images(image1, image2):
    """Merge two images into one, displayed side by side
    :param file1: path to first image file
    :param file2: path to second image file
    :return: the merged Image object
    """

    (width1, height1) = image1.size
    (width2, height2) = image2.size

    result_width = width1 + width2
    result_height = max(height1, height2)

    result = Image.new("RGBA", size=(result_width, result_height))
    result.paste(im=image1, box=(0, 0))
    result.paste(im=image2, box=(width1, 0))
    return result