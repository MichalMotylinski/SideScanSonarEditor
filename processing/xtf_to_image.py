from datetime import datetime
import numpy as np
import math
import matplotlib as mpl
import pandas as pd
from PIL import Image
from processing import geodetic
import pyxtf
from scipy.interpolate import interp1d

def slant_range_correction(ping_data, slant_range, depth):
    """
    Apply slant range correction for a single ping of side-scan sonar data.
    
    Parameters:
    ping_data (numpy array): Array of return intensities for the ping.
    slant_range (float): Maximum slant range for this ping.
    depth (float): Water depth or sonar height above the seabed.
    
    Returns:
    corrected_ping_data (numpy array): Intensity values interpolated to horizontal distances.
    horizontal_ranges (numpy array): Corrected horizontal ranges for each return.
    """
    N = len(ping_data)
    
    # Compute slant range for each return
    slant_ranges = np.linspace(0, slant_range, N)
    
    # Compute horizontal ranges using slant range correction
    horizontal_ranges = np.sqrt(np.clip(np.square(slant_ranges) - np.square(depth), 0, None))
    
    # Interpolation: map the ping data from slant range to horizontal range
    interp_func = interp1d(horizontal_ranges, ping_data, bounds_error=False, fill_value=0)
    
    # Create a uniform grid in horizontal range
    uniform_horizontal_range = np.linspace(0, np.max(horizontal_ranges), N)
    
    # Interpolate the ping data to the new horizontal range grid
    corrected_ping_data = interp_func(uniform_horizontal_range)
    
    return corrected_ping_data

def calculate_distance(easting1, northing1, easting2, northing2):
    return math.sqrt((easting2 - easting1)**2 + (northing2 - northing1)**2)

def read_xtf(filepath, params):#decimation, auto_stretch, stretch):
    (file_header, packets) = pyxtf.xtf_read(filepath)
    ping = packets[pyxtf.XTFHeaderType.sonar]
    
    geographicals = False
    speeds = []
    prev_x_coordinate = None
    prev_y_coordinate = None
    prev_datetime = None
    time_first = 0
    time_last = 0

    port_channel = pyxtf.concatenate_channel(packets[pyxtf.XTFHeaderType.sonar], file_header=file_header, channel=0, weighted=True).astype(np.float64)
    stbd_channel = pyxtf.concatenate_channel(packets[pyxtf.XTFHeaderType.sonar], file_header=file_header, channel=1, weighted=True).astype(np.float64)
    
    coords = []
    for i in range(len(ping)):
        across_track_sample_interval = (ping[i].ping_chan_headers[0].SlantRange / ping[i].ping_chan_headers[0].NumSamples)
        coords.insert(0, {"x": ping[i].ShipXcoordinate, "y": ping[i].ShipYcoordinate, "gyro": ping[i].ShipGyro, "across_interval": across_track_sample_interval, "slant_range":ping[i].ping_chan_headers[0].SlantRange, "num_samples": ping[i].ping_chan_headers[0].NumSamples, "altitude": ping[i].SensorPrimaryAltitude})
        
        current_x_coordinate, current_y_coordinate= ping[i].SensorXcoordinate, ping[i].SensorYcoordinate
        current_datetime = datetime(ping[i].Year, ping[i].Month, ping[i].Day, ping[i].Hour, ping[i].Minute, ping[i].Second, ping[i].HSeconds * 10000).timestamp()
        
        if i == 0:
            time_first = current_datetime
            previous_x = ping[i].ShipXcoordinate
            previous_y = ping[i].ShipYcoordinate
        
        distance = calculate_distance(previous_x, previous_y, ping[i].ShipXcoordinate, ping[i].ShipYcoordinate)

        if i == 0 and (ping[i].SensorXcoordinate <= 180) & (ping[i].SensorYcoordinate <= 90): 
            geographicals = True
        if i % 2 == 0:
            prev_x_coordinate, prev_y_coordinate = ping[i].SensorXcoordinate, ping[i].SensorYcoordinate
            prev_datetime = datetime(ping[i].Year, ping[i].Month, ping[i].Day, ping[i].Hour, ping[i].Minute, ping[i].Second, ping[i].HSeconds * 10000).timestamp()
        else:
            if geographicals:
                s, _, _ = geodetic.calculateRangeBearingFromGeographicals(prev_x_coordinate, prev_y_coordinate, current_x_coordinate, current_y_coordinate)
                # now we have the range, comput the speed in metres/second. where speed = distance/time
                speeds.append(s / (current_datetime - prev_datetime))
            else:
                s, _ = geodetic.calculateRangeBearingFromGridPosition(prev_x_coordinate, prev_y_coordinate, current_x_coordinate, current_y_coordinate)
                # now we have the range, comput the speed in metres/second. where speed = distance/time
                speeds.append(s / (current_datetime - prev_datetime))
    
    mean_speed = float(np.mean(speeds))
    ping_count = i
    time_last = current_datetime

    # Get full spatial size of the data before stretching and decimation
    params["full_image_height"] = port_channel.shape[0]
    params["full_image_width"] = port_channel.shape[1] + stbd_channel.shape[1]

    # Sample interval in metres
    params["across_track_sample_interval"] *= params["decimation"] 
    
    # To make the image somewhat isometric, we need to compute the alongtrack sample interval.  this is based on the ping times, number of pings and mean speed  where distance = speed * duration
    distance = mean_speed * (time_last - time_first)
    
    #distance = mean_speed * (navigation[-1].dateTime.timestamp() - navigation[0].dateTime.timestamp())
    params["along_track_sample_interval"] = (distance / ping_count)

    if params["slant_range_correct"]:
        port_channel = np.fliplr(port_channel)
        for i, _ in enumerate(port_channel):
            port_channel[i] = slant_range_correction(port_channel[i], coords[i]["slant_range"], coords[i]["altitude"])
            stbd_channel[i] = slant_range_correction(stbd_channel[i], coords[i]["slant_range"], coords[i]["altitude"])
        port_channel = np.fliplr(port_channel)

    # Automatic calculation of stretch that needs to be applied to the data
    if params["auto_stretch"]:
        params["stretch"] = math.ceil(params["along_track_sample_interval"] / params["across_track_sample_interval"])

    port_channel = np.repeat(port_channel, params["stretch"], axis=0)[:, ::params["decimation"]]
    stbd_channel = np.repeat(stbd_channel, params["stretch"], axis=0)[:, ::params["decimation"]]

    params["coords"] = coords

    return port_channel, stbd_channel, params

def convert_to_image(channel, params):
    gs_min = 0
    gs_max = 255 
    channel_max = params["channel_max"]
    channel_min = params["channel_min"]

    upper_limit = 2 ** 14
    channel.clip(0, upper_limit-1, out=channel)
    if params["auto_min"]:
        # compute the clips
        channel_min = channel.min()

        if channel_min > 0:
            channel_min = math.log10(channel_min)
        else:
            channel_min = 0

    if params["auto_max"]:
        channel_max = channel.max()
        
        if channel_max > 0:
            channel_max = math.log10(channel_max)
        else:
            channel_max = 0

    params["channel_min"] = channel_min
    params["channel_max"] = channel_max

    # this scales from the range of image values to the range of output grey levels
    if (channel_max - channel_min) != 0:
        scale = (gs_max - gs_min) / (channel_max - channel_min)
    
    if params["color_scheme"] == "greylog":
        channel = np.log10(channel + 0.00001, dtype=np.float32)
    
    channel = np.subtract(channel, channel_min)
    channel = np.multiply(channel, scale)

    if params["invert"]:
        channel = np.subtract(gs_max, channel)
    else:
        channel = np.add(gs_min, channel)
    
    if params["color_scheme"] == "color":
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
    return image, params

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