#! /usr/bin/env python
#
# getspectrumandpeaksplot.py
#
# Copyright (c) 2018 by Micron Optics, Inc.  All Rights Reserved
#
"""This example will plot a spectrum and the corresponding peaks.  This
requires numpy, scilab, and matplotlib packages.
"""

import matplotlib

matplotlib.use("tkagg")

import hyperion
import matplotlib.pyplot as plt
import nest_asyncio
from scipy.interpolate import interp1d

nest_asyncio.apply()

channels = [3, 4]
h1 = hyperion.Hyperion("10.0.0.55")


for channel in channels:
    peaks = h1.peaks[channel]

    spectra = h1.spectra
    spectrum = spectra[channel]
    wavelengths = spectra.wavelengths

    # We will interpolate the peak data so that the indicators appear on the
    # plot in line with the spectrum.
    interpSpectrum = interp1d(wavelengths, spectrum)

    plt.plot(wavelengths, spectrum, peaks, interpSpectrum(peaks), "o")
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Amplitude (dBm)")
    plt.show()
