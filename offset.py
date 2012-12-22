"""https://gist.github.com/376572"""
from __future__ import division

from sys import argv
import os
import subprocess

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy import signal


def wavread(fname):
    fs, sig = wavfile.read(fname)
    nsig = sig / 2 ** 15
    enc = '?'
    return nsig, fs, enc


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
    corr = signal.fftconvolve(s1, s2[::-1], mode="same")
    print("done")

    delay = int(len(corr) / 2) - np.argmax(corr)

    offset = delay / fs

    print("offset is {offset}s".format(offset=offset))


def fft(fname):
    """Plot the fourier transform of a given wav file."""
    sig, fs, enc = wavread(fname)
    w = np.fft.fft(sig)
    freqs = np.fft.fftfreq(len(sig)) * fs

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(freqs, w)
    ax.set_xlim(0, 10000)
    ax.set_xlabel('Frequency (Hz)')
    ax.set_title('fft of a whistle')
    plt.show()
    # fig.savefig('whistle-fft.png')


def whistle_filter(wav, fs):
    """ Filter non whistle info out of wav stream with rate fs.

    from scikits.audiolab import wavread
    cam1, fs, enc = wavread('cam1.wav')
    fcam1 = whistle_filter(cam1, fs)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    Time = np.arange(len(cam1)) / fs
    ax.plot(Time, cam1, label='unfiltered')
    ax.plot(Time, fcam1, label='filtered')
    ax.set_xlabel('Time (s)')
    ax.legend()
    fig.savefig('filtered-audio.png')
    """
    nyq = fs / 2    # nyquist frequency
    b, a = signal.butter(3, [2775 / nyq, 2850 / nyq], btype='band')
    fwav = signal.lfilter(b, a, wav)

    return fwav


def whistle_offset(fname):
    """Find where the whistle occurs in file (a .wav)."""
    sig, fs, enc = wavread(fname)
    fsig = whistle_filter(sig, fs)
    time = np.where(fsig > 0.4)[0][0] / fs
    return time


if __name__ == '__main__':
    f1 = argv[1]
    # f2 = argv[2]
    # o1 = f1.split('.')[0] + '.wav'
    # o2 = f2.split('.')[0] + '.wav'

    # fft(argv[1])
    print whistle_offset(f1)
    # extract_audio()
    # convolution()
    # # clean up
    # os.remove(o1)
    # os.remove(o2)
