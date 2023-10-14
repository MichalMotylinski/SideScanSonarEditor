
import processing.xtf_reader as xtf_reader
import processing.beam_correction as beam_correction
import numpy as np
import math
import matplotlib as mpl
import time
import pandas as pd
from PIL import Image
import os
import psutil
import bisect
from processing import geodetic
from datetime import datetime
import json

def read_xtf(filepath, channel_num, decimation, auto_stretch, stretch, shift, compute_bac):
    data = xtf_reader.XTFReader(filepath)

    first_pos = data.fileptr.tell()

    # Read the first packet and get its size and time
    packet_size, time_first = data.get_packet_size()
    ping_count = (data.fileSize - first_pos) / packet_size

    # Read the last packet and get its size and time
    data.fileptr.seek(data.fileSize - packet_size, 0)
    max_samples_port, slant_range, time_last = data.get_duration(channel_num)
    data.fileptr.seek(first_pos, 0)

    bac_dir = os.path.join(filepath.rsplit("/", 1)[0], "BAC")
    if compute_bac:
        if not os.path.exists(bac_dir):
            os.mkdir(bac_dir)

        if os.path.exists(os.path.join(bac_dir, f"{filepath.rsplit('/', 1)[1].rsplit('.', 1)[0]}.json")):
            with open(os.path.join(bac_dir, f"{filepath.rsplit('/', 1)[1].rsplit('.', 1)[0]}.json"), "r") as json_file:
                data = json.load(json_file)
                samples_port_avg, samples_stbd_avg = data["port"], data["starboard"]
        else:
            samples_port_avg, samples_stbd_avg = beam_correction.compute_beam_correction(filepath, 0, 1, slant_range, ping_count)
            data = {"port": samples_port_avg.tolist(), "starboard": samples_stbd_avg.tolist()}
            with open(os.path.join(bac_dir, f"{filepath.rsplit('/', 1)[1].rsplit('.', 1)[0]}.json"), "w") as json_file:
                json.dump(data, json_file)


    # Sample interval in metres
    across_track_sample_interval = (slant_range / max_samples_port) * decimation
    
    mean_speed = compute_mean_speed(filepath)
    # To make the image somewhat isometric, we need to compute the alongtrack sample interval.  this is based on the ping times, number of pings and mean speed  where distance = speed * duration
    distance = mean_speed * (time_last - time_first)
    along_track_sample_interval = (distance / ping_count)

    # Automatic calculation of stretch that needs to be applied to the data
    if auto_stretch:
        stretch = math.ceil(along_track_sample_interval / across_track_sample_interval)

    # Roughly calculate the size of channel data array with float64 dtype
    size_bytes = ((max_samples_port / decimation * ping_count * stretch) * 8)
    req_size = size_bytes * 2
    available_size = psutil.virtual_memory().available

    data_limit = 536870912
    if available_size < data_limit:
        data_limit == available_size
    

    print("Size", req_size, data_limit)
    if req_size > data_limit:
        print("Not enough memory, splitting the data.")
        
        port_data = []
        starboard_data = []
        coords = []

        splits = math.ceil(req_size / data_limit)  
        pos = first_pos
        selected_split = 1
        
        pos = pos + math.floor(math.ceil(data.fileSize / splits) / packet_size) * packet_size * (selected_split - 1)
        stop_point = math.floor(math.ceil(data.fileSize / splits) / packet_size) * packet_size * selected_split + shift * packet_size
        while pos < stop_point:
            data.fileptr.seek(pos, 0)
            ping = data.readPacket()
            
            image_width = len(ping.pingChannel[0].data) * 2

            if ping == -999:
                continue

            coords.insert(0, {"x": ping.ShipXcoordinate, "y": ping.ShipYcoordinate, "gyro": ping.ShipGyro})
            
            pos = pos + packet_size
            
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

            if pos > math.floor(math.ceil(data.fileSize / splits) / packet_size) * packet_size * selected_split:
                print(pos)

        image_height = (data.fileSize - 1024) / packet_size

        return np.array(port_data), np.array(starboard_data), coords, splits, stretch, packet_size, image_height, image_width, across_track_sample_interval, along_track_sample_interval

    data = xtf_reader.XTFReader(filepath)
    port_data = []
    starboard_data = []
    coords = []

    while data.moreData():
        ping = data.readPacket()
        # this is not a ping so skip it
        if ping == -999:
            continue

        coords.insert(0, {"x": ping.ShipXcoordinate, "y": ping.ShipYcoordinate, "gyro": ping.ShipGyro})
        image_width = len(ping.pingChannel[0].data) * 2

        channel = np.array(ping.pingChannel[0].data[::decimation])
        channel = np.multiply(channel, math.pow(2, - ping.pingChannel[0].Weight))

        if compute_bac:
            samples_port_avg_at_40 = beam_correction.get_value_at_40_degree(samples_port_avg, ping.pingChannel[0].SlantRange, ping.SensorPrimaryAltitude)
            channel = np.add(channel, samples_port_avg_at_40)

        filtered_port_data = channel.tolist()
        
        for _ in range(stretch):
            port_data.insert(0, filtered_port_data[::-1])
        
        channel = np.array(ping.pingChannel[1].data[::decimation])
        channel = np.multiply(channel, math.pow(2, - ping.pingChannel[1].Weight))

        if compute_bac:
            samples_port_avg_at_40 = beam_correction.get_value_at_40_degree(samples_stbd_avg, ping.pingChannel[0].SlantRange, ping.SensorPrimaryAltitude)
            channel = np.add(channel, samples_port_avg_at_40)

        raw_starboard_data = channel.tolist()

        for _ in range(stretch):
            starboard_data.insert(0, raw_starboard_data)

    image_height = (data.fileSize - 1024) / packet_size

    return np.array(port_data), np.array(starboard_data), coords, 1, stretch, packet_size, image_height, image_width, across_track_sample_interval, along_track_sample_interval

def load_selected_split(filepath, decimation, stretch, shift, packet_size, splits, selected_split):
    start = time.perf_counter()
    data = xtf_reader.XTFReader(filepath)
    end = time.perf_counter()
    print("Load data", end-start)
    port_data = []
    starboard_data = []
    coords = []

    pos = 1024
    
    start = time.perf_counter()
    if selected_split == 1:
        pos = pos + math.floor(math.ceil(data.fileSize / splits) / packet_size) * packet_size * (selected_split - 1)
    else:
        if math.floor(math.ceil(data.fileSize / splits) / packet_size) * packet_size * (selected_split - 1) - shift * packet_size > pos:
            pos = pos + math.floor(math.ceil(data.fileSize / splits) / packet_size) * packet_size * (selected_split - 1) - shift * packet_size
 
    stop_point = data.fileSize
    print("filesize", data.fileSize)
    if math.floor(math.ceil(data.fileSize / splits) / packet_size) * packet_size * selected_split + shift * packet_size < data.fileSize:
        stop_point = math.floor(math.ceil(data.fileSize / splits) / packet_size) * packet_size * selected_split + shift * packet_size
        stop_point = stop_point + 1024
    if selected_split == splits:
        stop_point = data.fileSize
    
    while pos < stop_point:
        #while pos < math.floor(math.ceil(data.fileSize / splits) / packet_size) * packet_size * selected_split:
        data.fileptr.seek(pos, 0)
        ping = data.readPacket()

        if ping == -999:
            continue

        coords.insert(0, {"x": ping.ShipXcoordinate, "y": ping.ShipYcoordinate, "gyro": ping.ShipGyro})

        image_width = len(ping.pingChannel[0].data) * 2

        pos = pos + packet_size
        
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
    
    end = time.perf_counter()
    print("Calc data", end-start)
    image_height = (data.fileSize -1024) / packet_size
    return np.array(port_data), np.array(starboard_data), coords, splits, stretch, image_height, image_width


def get_sample_range(filepath, channel_num, load_navigation):
    """iterate through the file to find the extents for range, time and samples.  These are all needed in subsequent processing """
    max_samples_port = 0
    max_range = 0
    ping_count = 0
    navigation = 0
    
    start_time = time.time() # time the process
    print("Gathering data limits...")
    #   open the XTF file for reading 
    data = xtf_reader.XTFReader(filepath)
    if load_navigation:
        navigation = data.loadNavigation()
    
    mean_speed = 1

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

    channel_max = 1
    
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

def compute_mean_speed(filename):
    i = 0
    geographicals = False
    speeds = []
    prev_x_coordinate = None
    prev_y_coordinate = None
    prev_datetime = None

    data = xtf_reader.XTFReader(filename)
    while data.moreData():
        ping = data.readPacket()

        # Check if data is in geographicals
        if i == 0 and (ping.SensorXcoordinate <= 180) & (ping.SensorYcoordinate <= 90): 
            geographicals = True

        if i % 2 == 0:
            prev_x_coordinate, prev_y_coordinate = ping.SensorXcoordinate, ping.SensorYcoordinate
            prev_datetime = datetime(ping.Year, ping.Month, ping.Day, ping.Hour, ping.Minute, ping.Second, ping.HSeconds * 10000).timestamp()
        else:
            current_x_coordinate, current_y_coordinate= ping.SensorXcoordinate, ping.SensorYcoordinate
            current_datetime = datetime(ping.Year, ping.Month, ping.Day, ping.Hour, ping.Minute, ping.Second, ping.HSeconds * 10000).timestamp()

            if geographicals:
                range, _, _ = geodetic.calculateRangeBearingFromGeographicals(prev_x_coordinate, prev_y_coordinate, current_x_coordinate, current_y_coordinate)
                # now we have the range, comput the speed in metres/second. where speed = distance/time
                speeds.append(range / (current_datetime - prev_datetime))
            else:
                range, _ = geodetic.calculateRangeBearingFromGridPosition(prev_x_coordinate, prev_y_coordinate, current_x_coordinate, current_y_coordinate)
                # now we have the range, comput the speed in metres/second. where speed = distance/time
                speeds.append(range / (current_datetime - prev_datetime))
        mean_speed = float(np.mean(speeds))
        i += 1
    return mean_speed