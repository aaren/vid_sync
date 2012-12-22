"""Video synchronisation using a whistle.

Break up synced videos into images.

Inputs: two videos in a format that ffmpeg understands.

These videos must each have audio and a whistle must be
blown in the course of filming. This is assumed to be
at 2800Hz, but this is easily changed,

Use on command line:
    python offset.py vid1.mov vid2.mov

Use as module:
    import offset
    cut_video_name_1, cut_video_name_2 = offset.main()

Requires ffmpeg.
"""

from __future__ import division

from sys import argv
import os
import subprocess

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy import signal


def wavread(fname):
    """Read in a wav file with scipy. Argument order ensures
    compatibility with wavread from scikits.audiolab.
    """
    fs, sig = wavfile.read(fname)
    nsig = sig / 2 ** 15
    enc = '?'
    return nsig, fs, enc


def extract_audio(f, verbose=None):
    """Uses ffmpeg to strip audio from video as wav from file f

    Writes the audio into output file f.wav and returns the name of
    the output file.
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
    if verbose:
        subprocess.call(cmd)
    elif not verbose:
        subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return o


def convolution(o1, o2):
    """Find the offset by convolving the two audio streams.
    https://gist.github.com/376572
    """
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


def whistle_offset(fname, thresh=0.4):
    """Find where the whistle occurs in file (a .wav)."""
    sig, fs, enc = wavread(fname)
    fsig = whistle_filter(sig, fs)
    time = np.where(fsig > thresh)[0][0] / fs
    return time


def cut_video(fname, tstart, verbose=None):
    """Cut the given video to start at tstart."""
    cutname = "cut-" + fname
    cmd = ["ffmpeg",
           "-ss", str(tstart),     # start at tstart seconds
           "-i", fname,            # input file *has to come after -ss!*
           "-vcodec", "copy",      # don't reencode
           cutname]         # output filename
    print("Cutting {video}".format(video=fname))
    if verbose:
        subprocess.call(cmd)
    elif not verbose:
        subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return cutname


def burst_video(fname, folder='.', framerate=5, verbose=None):
    """Take the given video and split into images at the given
    framerate, saving to the given folder.
    """
    if folder is not '.':
        try:
            os.makedirs(folder, mode=0755)
        except OSError:
            print "specified folder already exists. You need to remove it first."
            exit(0)
    out_format = '{folder}/img_%04d.jpg'.format(folder=folder)
    cmd = ["ffmpeg",
           "-i", fname,
           "-sameq",
           "-r", str(framerate),
           out_format]
    if verbose:
        subprocess.call(cmd)
    elif not verbose:
        subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main(f1=argv[1], f2=argv[2], pre=1, verbose=None):
    """two input files, f1, f2.

    pre is the amount of video to have before the whistle
    in seconds.

    Returns the names of the cut files.
    """
    o1 = extract_audio(f1)
    o2 = extract_audio(f2)
    t_cam1 = whistle_offset(o1) - pre
    t_cam2 = whistle_offset(o2) - pre
    os.remove(o1)
    os.remove(o2)
    outs = "Whistle at {time} in {f}"
    print outs.format(time=t_cam1, f=o1)
    print outs.format(time=t_cam2, f=o2)

    c1 = cut_video(f1, t_cam1, verbose)
    c2 = cut_video(f2, t_cam2, verbose)
    print "bursting images..."
    burst_video(c1, './cam1', verbose=verbose)
    burst_video(c2, './cam2', verbose=verbose)

    return c1, c2


if __name__ == '__main__':
    main()
