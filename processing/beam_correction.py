import processing.xtf_reader as xtf_reader
import numpy as np
import math

def compute_beam_correction(filename, channel_a, channel_b, slant_range, ping_count):
    """
    Compute the beam correction table using the sonar ping data for the file. We are using slant range to define maximum number of samples in the table.
    """
    samples_port_sum = np.zeros(math.ceil(slant_range), dtype=np.int32)
    samples_stbd_sum = np.zeros(math.ceil(slant_range), dtype=np.int32)
    
    data = xtf_reader.XTFReader(filename)
    while data.moreData():
        ping = data.readPacket()
        
        # CHANNEL A : convert the port channel into an array of samples on a per angle basis
        channel = np.array(ping.pingChannel[channel_a].data)
        channel = np.multiply(channel, math.pow(2, -ping.pingChannel[channel_a].Weight))
        angular_response = ping_to_offtrack_response(channel, ping.pingChannel[channel_a].SlantRange, ping.SensorPrimaryAltitude)
        samples_port_sum = np.add(samples_port_sum, angular_response)

        # CHANNEL B : convert the starboard channel into an array of samples on a per angle basis
        channel = np.array(ping.pingChannel[channel_b].data)
        channel = np.multiply(channel, math.pow(2, -ping.pingChannel[channel_b].Weight))
        angular_response = ping_to_offtrack_response(channel, ping.pingChannel[channel_b].SlantRange, ping.SensorPrimaryAltitude)
        samples_stbd_sum = np.add(samples_stbd_sum, angular_response)

    samples_port_avg = np.divide(samples_port_sum, ping_count)
    samples_stbd_avg = np.divide(samples_stbd_sum, ping_count)                   
    return samples_port_avg, samples_stbd_avg

def get_value_at_40_degree(ping, slant_range, altitude):
    """
    Given a 1D ping array, return the sample at the 40 degree angle from nadir.
    """
    samples_per_metre = len(ping) / slant_range
    altitude_in_samples = math.floor(altitude * samples_per_metre)
    val = int(altitude_in_samples / math.cos(math.radians(40)))
    return ping[val]   

def ping_to_offtrack_response(ping, slant_range,  altitude):
    """
    Compute an instantaneous OFFSET (dX) based response using a single ping of information.
    """
    offtrack_response = [0] * math.ceil(slant_range)
    samples_per_metre = len(ping) / slant_range
    altitude_in_samples = math.floor(altitude * samples_per_metre)
    altitude_in_metres_squared = (altitude_in_samples / samples_per_metre) * (altitude_in_samples / samples_per_metre)

    # we do not need to process all records, just subsample on a per-degree basis
    for s in range(altitude_in_samples, len(ping)):
        range_metres = s / samples_per_metre
        dx = int (math.sqrt((range_metres * range_metres) - altitude_in_metres_squared))
        offtrack_response[dx] = ping[s]
    return offtrack_response