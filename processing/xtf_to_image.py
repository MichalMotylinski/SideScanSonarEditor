
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
import scipy
from scipy.interpolate import interp1d

MINv = 0
MAXv = 0
FILE = ""
def read_xtf(filepath, channel_num, decimation, auto_stretch, stretch, shift, compute_bac):
    global FILE, MINv, MAXv
    data = xtf_reader.XTFReader(filepath)

    first_pos = data.fileptr.tell()
    FILE = filepath.rsplit(os.sep, 1)[1].rsplit(".", 1)[0]
    print(FILE)
    # Read the first packet and get its size and time
    packet_size, time_first = data.get_packet_size()
    ping_count = (data.fileSize - first_pos) / packet_size

    # Read the last packet and get its size and time
    data.fileptr.seek(data.fileSize - packet_size, 0)
    max_samples_port, slant_range, time_last = data.get_duration(channel_num)
    data.fileptr.seek(first_pos, 0)

    print(max_samples_port, slant_range)
    max_samples_port = min(max_samples_port, math.ceil(slant_range))
    print(max_samples_port, slant_range)

    bac_dir = os.path.join(filepath.rsplit(os.sep, 1)[0], "BAC")
    port_means = [0]
    stbd_means = [0]
    if compute_bac:
        if not os.path.exists(bac_dir):
            os.mkdir(bac_dir)

        samples_port_sum = np.zeros(max_samples_port, dtype=np.int32)
        samples_port_count = np.zeros(max_samples_port, dtype=np.int32)
        samples_stbd_sum = np.zeros(max_samples_port, dtype=np.int32)
        samples_stbd_count = np.zeros(max_samples_port, dtype=np.int32)
       
        if os.path.exists(os.path.join(bac_dir, f"{filepath.rsplit(os.sep, 1)[1].rsplit('.', 1)[0]}_bac.json")):
            with open(os.path.join(bac_dir, f"{filepath.rsplit(os.sep, 1)[1].rsplit('.', 1)[0]}_bac.json"), "r") as json_file:
                bac_data = json.load(json_file)
                samples_port_avg, samples_stbd_avg = bac_data["port"], bac_data["starboard"]
        else:
            samples_port_avg, samples_stbd_avg, port_means, stbd_means = beam_correction.compute_beam_correction(filepath, 0, 1, samples_port_sum, samples_port_count, samples_stbd_sum, samples_stbd_count, decimation)
            bac_data = {"port": samples_port_avg.tolist(), "starboard": samples_stbd_avg.tolist()}
            with open(os.path.join(bac_dir, f"{filepath.rsplit(os.sep, 1)[1].rsplit('.', 1)[0]}_bac.json"), "w") as json_file:
                json.dump(bac_data, json_file)
    
    """packet_size, max_samples_port, max_samples_stbd, max_altitude, slant_range, ping_count, navigation = get_sample_range(filepath, 0, 1)
    max_samples_port = min(max_samples_port, slant_range)
    max_samples_stbd = min(max_samples_stbd, slant_range)

    segment_interval = 100
    bac_dir = os.path.join(filepath.rsplit(os.sep, 1)[0], "BAC")

    if compute_bac:
        if not os.path.exists(bac_dir):
            os.mkdir(bac_dir)

        #num_segments = int(max_altitude / segment_interval) + 1 # need to add extra for zero index
        max_samples_port = int(max_samples_port)
        max_samples_stbd = int(max_samples_stbd)
        
        samples_port_sum = np.zeros(max_samples_port, dtype=np.int32)
        samples_port_count = np.zeros(max_samples_port, dtype=np.int32)
        samples_port_sum_squared = np.zeros(max_samples_port, dtype=np.int32) #used for standard deviations
        samples_stbd_sum = np.zeros(max_samples_stbd, dtype=np.int32)
        samples_stbd_count = np.zeros(max_samples_stbd, dtype=np.int32)
        samples_stbd_sum_squared = np.zeros(max_samples_stbd, dtype=np.int32)
        
        #print("samples", max_altitude, samples_port_sum.shape, samples_port_sum)
        if not os.path.exists(bac_dir):
            os.mkdir(bac_dir)

        if os.path.exists(os.path.join(bac_dir, f"{filepath.rsplit(os.sep, 1)[1].rsplit('.', 1)[0]}_bac.json")):
            with open(os.path.join(bac_dir, f"{filepath.rsplit(os.sep, 1)[1].rsplit('.', 1)[0]}_bac.json"), "r") as json_file:
                bac_data = json.load(json_file)
                samples_port_avg, samples_stbd_avg = np.array(bac_data["port"]), np.array(bac_data["starboard"])
        else:
            samples_port_sum, samples_port_count, samples_port_sum_squared, samples_port_avg, samples_stbd_sum, samples_stbd_count, samples_stbd_sum_squared, samples_stbd_avg = beam_correction.compute_beam_correction(filepath, 0, 1, samples_port_sum, samples_port_count, samples_port_sum_squared, samples_stbd_sum, samples_stbd_count, samples_stbd_sum_squared, segment_interval)
            bac_data = {"port": samples_port_avg.tolist(), "starboard": samples_stbd_avg.tolist()}
            samples_port_avg = np.array(samples_port_avg)
            samples_stbd_avg = np.array(samples_stbd_avg)
            with open(os.path.join(bac_dir, f"{filepath.rsplit(os.sep, 1)[1].rsplit('.', 1)[0]}_bac.json"), "w") as json_file:
                json.dump(bac_data, json_file)"""

    # Sample interval in metres
    across_track_sample_interval = (slant_range / max_samples_port) * decimation
    print(across_track_sample_interval)
    mean_speed = compute_mean_speed(filepath)
    # To make the image somewhat isometric, we need to compute the alongtrack sample interval.  this is based on the ping times, number of pings and mean speed  where distance = speed * duration
    distance = mean_speed * (time_last - time_first)

    #distance = mean_speed * (navigation[-1].dateTime.timestamp() - navigation[0].dateTime.timestamp())
    along_track_sample_interval = (distance / ping_count)

    # Automatic calculation of stretch that needs to be applied to the data
    if auto_stretch:
        stretch = math.ceil(along_track_sample_interval / across_track_sample_interval)

    # Roughly calculate the size of channel data array with float64 dtype
    size_bytes = ((max_samples_port / decimation * ping_count * stretch) * 8)
    req_size = size_bytes * 2
    available_size = psutil.virtual_memory().available

    data_limit = 999536870912
    if available_size < data_limit:
        data_limit == available_size
    
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

        port_channel = np.array(ping.pingChannel[0].data[::decimation])
        port_channel = np.multiply(port_channel, math.pow(2, - ping.pingChannel[0].Weight))
        #port_arc = beam_correction.offtrack_response_to_ping(samples_port_avg, ping.pingChannel[0].SlantRange, ping.SensorPrimaryAltitude, int (ping.pingChannel[0].NumSamples / decimation), decimation)
        
        stbd_channel = np.array(ping.pingChannel[1].data[::decimation])
        stbd_channel = np.multiply(stbd_channel, math.pow(2, - ping.pingChannel[1].Weight))
        #stbd_arc = beam_correction.offtrack_response_to_ping(samples_stbd_avg, ping.pingChannel[1].SlantRange, ping.SensorPrimaryAltitude, int (ping.pingChannel[1].NumSamples / decimation), decimation)
        
        if compute_bac:
            #stbd_channel = port_channel.copy()
            
            # Angular correction
            #BS_mean_at_40 = beam_correction.get_value_at_40_degree(port_arc, ping.pingChannel[0].SlantRange, ping.SensorPrimaryAltitude)
            #port_channel = np.add(port_channel, BS_mean_at_40).tolist()
            
            #BS_mean_at_40 = beam_correction.get_value_at_40_degree(stbd_arc, ping.pingChannel[1].SlantRange, ping.SensorPrimaryAltitude)
            #stbd_channel = np.add(stbd_channel, BS_mean_at_40).tolist()
            
            #port_channel = np.add(port_channel, np.sqrt(port_arc[::-1])).tolist()
            #port_channel = np.add(port_channel, math.sqrt(BS_mean_at_40)).tolist()
            #stbd_channel = np.add(stbd_channel, math.sqrt(BS_mean_at_40)).tolist()
            '''offtrack_response = [0] * math.ceil(slant_range)
            samples_per_metre = math.ceil(len(port_channel) / slant_range)
            altitude_in_samples = math.floor(ping.SensorPrimaryAltitude * samples_per_metre)
            altitude_in_metres_squared = (altitude_in_samples / samples_per_metre) * (altitude_in_samples / samples_per_metre)
            for s in range(altitude_in_samples, len(port_channel), decimation):
                range_metres = s / samples_per_metre
                dx = int(math.sqrt((range_metres * range_metres) - altitude_in_metres_squared))
                offtrack_response[dx] = port_channel[s]
            #with open("Portchannel.json", "w") as f:
                #json.dump({"port": port_channel.tolist(), "off":offtrack_response}, f, indent=4)
            #print(port_channel.tolist(), offtrack_response)
            offtrack_response = offtrack_response[::-1]
            #print(offtrack_response)
            stbd_channel = port_channel
            port_mean = np.mean(port_channel[181:])'''

            """for s in range(altitude_in_samples, len(port_channel), decimation):
                range_metres = s / samples_per_metre
                dx = int(math.sqrt((range_metres * range_metres) - altitude_in_metres_squared))
                #port_channel[s] = port_channel[s] + offtrack_response[dx]
                #port_channel = [value + 0.5 * (port_mean - value) for value in port_channel]
                stbd_channel[s] = stbd_channel[s] + math.sqrt(offtrack_response[dx])"""
            #stbd_channel = np.add(stbd_channel, math.sqrt(BS_mean_at_40)).tolist()
            #port_channel = [value + 0.1 * (port_mean - value) for value in port_channel]
            #port_mean = np.mean(port_means)# + 25000
            #print(min(port_channel), max(port_channel), port_mean)
            #stbd_mean = np.mean(stbd_means)
            #stbd_channel = [value + 0.5 * abs(port_mean - value) if value < port_mean else value - 0.5 * abs(port_mean - value) for value in stbd_channel]
            #stbd_channel[181:1024]  = stbd_channel[181:1024] - 300
            #stbd_channel[1024:]  = stbd_channel[1024:] + 300
            #port_channel = [value + np.sqrt(abs(port_mean - value)) if value < port_mean else value - np.sqrt(abs(port_mean - value)) for value in port_channel]
            #port_channel = [value + 0.5 * abs(port_mean - value) if value < port_mean else value - 0.5 * abs(port_mean - value) for value in port_channel]
            #port_channel = [value + 0.9 * (port_mean - value) for value in port_channel]
            #port_channel = [value + (np.log(value) if abs(np.log(value)) != np.inf else 0 + np.sqrt(value)) if value < port_mean else value - (np.log(value) if abs(np.log(value)) != np.inf else 0 + np.sqrt(value)) for value in port_channel]
            #port_channel = port_channel.tolist()
            #port_channel = np.divide(np.add(port_channel, port_mean), np.std(port_channel)).tolist()
            #port_channel = np.add(port_channel, BS_mean_at_40).tolist()
            #port_channel = np.nan_to_num(port_channel, nan=0.0).tolist()
            #stbd_channel = [value + (np.log(value) if abs(np.log(value)) != np.inf else 0 + np.sqrt(value)) if value < port_mean else value - (np.log(value) if abs(np.log(value)) != np.inf else 0 + np.sqrt(value)) for value in stbd_channel]
            #BS_mean_at_40 = beam_correction.get_value_at_40_degree(stbd_arc, ping.pingChannel[1].SlantRange, ping.SensorPrimaryAltitude)
            #stbd_channel = np.divide(np.subtract(stbd_channel, np.mean(stbd_channel)), np.std(stbd_channel)).tolist()
            #stbd_channel = np.multiply(stbd_channel, port_arc_alt).tolist()
            #stbd_channel = [value + (np.log(value) * np.sqrt(value))+BS_mean_at_40 if value < stbd_mean else value - (np.log(value) * np.sqrt(value))+BS_mean_at_40 for value in stbd_channel]
            
            """offtrack_response = [0] * math.ceil(ping.pingChannel[1].SlantRange)
            samples_per_metre = math.ceil(len(stbd_channel) / ping.pingChannel[1].SlantRange)
            altitude_in_samples = math.floor(ping.SensorPrimaryAltitude * samples_per_metre)
            altitude_in_metres_squared = (altitude_in_samples / samples_per_metre) * (altitude_in_samples / samples_per_metre)

            # we do not need to process all records, just subsample on a per-degree basis
            for s in range(altitude_in_samples, len(stbd_channel), decimation):
                range_metres = s / samples_per_metre
                dx = int(math.sqrt((range_metres * range_metres) - altitude_in_metres_squared))
                offtrack_response[dx] = stbd_channel[s]
            epsilon = 1e-6 """
            #port_channel = [value + 0.5 * (port_mean - value) / (abs(port_mean - value) + epsilon)for value in port_channel]
            #port_channel[1024:] = np.add(port_channel[1024:], 4000).tolist()
            
            #stbd_channel = [value + 0.5 * abs(stbd_mean - value) if value < stbd_mean else value - 0.9 * abs(stbd_mean - value) for value in stbd_channel]
            
            #port_channel = np.add(port_channel, port_arc).tolist()
            #port_channel = np.add(port_channel, np.array(port_arc)).tolist()
            
            """if not (previous_stbd_range == int(ping.pingChannel[1].SlantRange)):
                previous_stbd_range = int(ping.pingChannel[1].SlantRange)
                stbd_arc = beam_correction.offtrack_response_to_ping(samples_stbd_avg, ping.pingChannel[1].SlantRange, ping.SensorPrimaryAltitude, int (ping.pingChannel[1].NumSamples / decimation), decimation)"""
            
            #BS_mean_at_40 = beam_correction.get_value_at_40_degree(stbd_arc, ping.pingChannel[1].SlantRange, ping.SensorPrimaryAltitude)
            #stbd_channel = np.add(stbd_channel, stbd_arc).tolist()

            #port_channel = port_channel.tolist()
            #stbd_channel = stbd_channel.tolist()
            #BS_mean_at_40 = beam_correction.get_value_at_40_degree(stbd_arc, ping.pingChannel[1].SlantRange, ping.SensorPrimaryAltitude)
            #stbd_channel = np.add(stbd_channel, BS_mean_at_40).tolist()
            #print(stbd_channel)
            #corrected_ping = slant_range_correction(stbd_channel, ping.SensorPrimaryAltitude, ping.pingChannel[1].SlantRange, int (ping.pingChannel[1].NumSamples / decimation))
            #corrected_pings.append(corrected_ping)
            #stbd_channel = corrected_ping
            #print("AFTER", stbd_channel)

            ##############################################
            # Good slant range correction!!!!
            ##############################################
            """samples_per_metre = int (ping.pingChannel[1].NumSamples / decimation) / ping.pingChannel[0].SlantRange
            altitude_in_samples = math.ceil(ping.SensorPrimaryAltitude * samples_per_metre)

            # Create the original bin positions (non-uniform)
            original_length = len(stbd_channel)
            original_bins = np.linspace(0, samples_per_metre, original_length)

            # Create the new bin positions after removing the water column
            new_bins = original_bins[altitude_in_samples:]

            # The side scan sonar data after removing the water column
            #stbd_channel = np.random.rand(len(stbd_channel) - altitude_in_samples)  # Example data, replace with actual data
            stbd_channel = stbd_channel[altitude_in_samples:]
            # Create an interpolation function
            interpolation_function = interp1d(new_bins, stbd_channel, kind='linear', fill_value="extrapolate")

            # Generate the new positions for interpolation
            interpolated_bins = np.linspace(new_bins[0], new_bins[-1], original_length)

            # Interpolate the data back to the original length
            stbd_channel = interpolation_function(interpolated_bins)"""
            ##############################################
            # Good slant range correction!!!!
            ##############################################

            #BS_mean_at_40 = beam_correction.get_value_at_40_degree(port_arc, ping.pingChannel[1].SlantRange, ping.SensorPrimaryAltitude)
            #stbd_channel = np.add(stbd_channel, BS_mean_at_40).tolist()
            #stbd_channel = np.divide(np.subtract(stbd_channel, np.mean(stbd_channel)), np.std(stbd_channel))
            #stbd_channel = np.add(stbd_channel, abs(np.min(stbd_channel)))
            #stbd_channel = np.pad(stbd_channel, (0, altitude_in_samples), 'constant', constant_values=(0, 0)).tolist()

        for _ in range(stretch):
            port_data.insert(0, port_channel[::-1])

        for _ in range(stretch):
            starboard_data.insert(0, stbd_channel)
    
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

'''def get_sample_range(filepath, channel_num, load_navigation):
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
    return max_samples_port, max_range, ping_count, mean_speed, navigation'''


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
    print(channel_min, channel_max, scale)
    np.seterr(divide='ignore')
    if color_scheme == "greylog":
        channel = np.log(samples)

    channel = np.subtract(channel, channel_min)
    channel = np.multiply(channel, scale)

    if invert:
        channel = np.subtract(gs_max, channel)
    else:
        channel = np.add(gs_min, channel)
    
    #channel = [value + (np.log(value) if abs(np.log(value)) != np.inf else 0 + np.sqrt(value)) if value < mean else value - (np.log(value) if abs(np.log(value)) != np.inf else 0 + np.sqrt(value)) for value in channel]
    #channel = [int(value + 0.9 * (mean - value)) for value in channel]
            
    """print(channel)
    channel = np.array(channel[:, 100:])
    hist, bins = np.histogram(channel.flatten(), bins=256, range=[0,256])

    # Normalize histogram
    hist_norm = hist / sum(hist)

    # Compute cumulative distribution function (CDF)
    cdf = hist_norm.cumsum()

    # Equalization mapping
    equalization_map = (cdf * 255).astype('uint8')
    print("ASDSD")
    # Apply mapping
    channel = equalization_map[np.uint8(channel)]
    print(channel)"""

    """data = channel
    # Define a 3x3 averaging filter to compute the local mean
    filter_3x3 = np.ones((3, 3)) / 9

    # Apply the filter to compute the local mean
    local_mean = scipy.ndimage.convolve(data, filter_3x3)

    # Define a function to get the central value of a 3x3 window
    def get_central_value(data, i, j):
        return data[i, j]

    # Compute the difference between the local mean and the central value
    difference = np.zeros_like(data)
    for i in range(1, data.shape[0] - 1):
        for j in range(1, data.shape[1] - 1):
            central_value = get_central_value(data, i, j)
            difference[i, j] = abs(local_mean[i, j] - central_value)
    """
    """print("A")
    for i in range(1, channel.shape[0]):
        means = []
        for j in range(1, channel.shape[1]):
            center = channel[i, j]
            filter = channel[i-1:i+2, j-1:j+2]
            #print(i, i-1, i+1, j, j-1, j+1, center, filter)
            means.append(np.mean(filter))
            if np.mean(filter) > np.mean(means):
                channel[i, j-1] = 255
                print(i,j)
                break
    print("B")"""
    """print("Original Data:\n", data)
    print("Local Mean:\n", local_mean)
    print("Difference:\n", difference, difference.shape)

    # Find the indices of the maximum difference
    max_diff_indices = np.unravel_index(np.argmax(difference, axis=None), difference.shape)
    print("Max Difference Indices:", max_diff_indices)
    print("Max Difference Value:", difference[max_diff_indices], difference.shape, data.shape)
    """
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
    global FILE
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
    print(f"{FILE}_add_response_at_40_angle.png")
    #result.save(f"{FILE}_add_log_and_sqrt.png")
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