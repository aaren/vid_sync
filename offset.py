"""https://gist.github.com/376572"""
from __future__ import division

from sys import argv
import os
import subprocess

import numpy as np
from scikits.audiolab import wavread
from scipy.signal import fftconvolve

f1 = argv[1]
f2 = argv[2]

o1 = f1.split('.')[0] + '.wav'
o2 = f2.split('.')[0] + '.wav'

def extract_audio():
    """Uses ffmpeg to strip audio from video as wav for two files
    called cam1.MOV and cam2.MOV.
    """
    tstart = str(0)
    duration = str(30)

    cmd1 = ["ffmpeg", "-i", f1,     # input is f1
            "-ss", tstart,          # start at tstart seconds
            "-t", duration,         # for duration seconds
            "-vn", "-ar", "44100",  # ignore video, audio rate is 44100
            "-f", "wav",            # output format wav
            o1]                     # output filename
    cmd2 = ["ffmpeg", "-i", f2,
            "-ss", tstart,
            "-t", duration,
            "-vn", "-ar", "44100",
            "-f", "wav",
            o2]
    print("extracting audio...")
    subprocess.call(cmd1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.call(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def convolution():
    """Find the offset by convolving the two audio streams."""
    print("reading...")
    s1, fs, enc = wavread(o1)
    s2, fs, enc = wavread(o2)
    print("done")

    print("computing fft convolution...")
    corr = fftconvolve(s1, s2[::-1], mode="same")
    print("done")

    delay = int(len(corr) / 2) - np.argmax(corr)

    offset = delay / fs

    print("offset is {offset}s".format(offset=offset))

if __name__ == '__main__':
    extract_audio()
    convolution()
    # clean up
    os.remove(o1)
    os.remove(o2)
