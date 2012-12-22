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


def extract_audio(f):
    """Uses ffmpeg to strip audio from video as wav for two files
    called cam1.MOV and cam2.MOV.

    Returns the name of the output file.
    """
    o = f.split('.')[-2] + '.wav'
    tstart = str(0)
    # duration = str(30)

    cmd = ["ffmpeg",
           "-ss", tstart,          # start at tstart seconds
           # "-t", duration,         # for duration seconds
           "-i", f,                # input is f1
           "-vn", "-ar", "44100",  # ignore video, audio rate is 44100
           "-f", "wav",            # output format wav
           o]                      # output filename
    print("extracting audio...")
    subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return o


def convolution(o1, o2):
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


def cut_video(fname, tstart):
    """Cut the given video to start at tstart."""
    cmd = ["ffmpeg",
           "-ss", str(tstart),     # start at tstart seconds
           "-i", fname,            # input file *has to come after -ss!*
           "-vcodec", "copy",      # don't reencode
           "cut-" + fname]         # output filename
    print("Cutting {video}".format(video=fname))
    subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main():
    f1 = argv[1]
    f2 = argv[2]
    o1 = extract_audio(f1)
    o2 = extract_audio(f2)
    t_cam1 = whistle_offset(o1) - 1
    t_cam2 = whistle_offset(o2) - 1
    outs = "Whistle at {time} in {f}"
    print outs.format(time=t_cam1, f=o1)
    print outs.format(time=t_cam2, f=o2)

    cut_video(f1, t_cam1)
    cut_video(f2, t_cam2)

    # cleanup
    os.remove(o1)
    os.remove(o2)


if __name__ == '__main__':
    main()
