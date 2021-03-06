# Copyright (C) Duncan Macleod (2013)
#
# This file is part of GWpy.
#
# GWpy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GWpy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GWpy.  If not, see <http://www.gnu.org/licenses/>.

"""A collection of average power spectral density calculation routines

Average-spectrum calculation routines are available for the following methods

    - :func:`Bartlett <bartlett>`
    - :func:`Welch <welch>`
    - :func:`Median-mean <median_mean>`
    - :func:`Median <median>`

Each of these methods utilises an existing method provided by the
LIGO Algorithm Library, wrapped into python as part of the `lal.spectrum`
module.
"""

import numpy
from matplotlib import mlab
from scipy import signal

from astropy import units

from .core import Spectrum
from ..timeseries import window as tdwindow
from ..spectrogram import Spectrogram

from .. import version
__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"
__version__ = version.version

__all__ = ['bartlett', 'welch', 'median_mean', 'median', 'spectrogram']


def bartlett(timeseries, segmentlength, window=None):
    """Calculate the power spectral density of the given `TimeSeries`
    using the Bartlett average method.

    This method divides the data into chunks of length `segmentlength`,
    a periodogram calculated for each, and the bin-by-bin mean returned.

    Parameters
    ---------
    timeseries: `TimeSeries`
        input `TimeSeries` data
    segmentlength : `int`
        number of samples in each average

    Returns
    -------
    Spectrum
        Bartlett-averaged `Spectrum`
    """
    return welch(timeseries, segmentlength, segmentlength, window=window)


def welch(timeseries, segmentlength, overlap, window=None):
    """Calculate the power spectral density of the given `TimeSeries`
    using the Welch average method.

    For more details see :lalsuite:`XLALREAL8AverageSpectrumWelch`.

    Parameters
    ----------
    timeseries : `TimeSeries`
        input `TimeSeries` data
    method : `str`
        average method
    segmentlength : `int`
        number of samples in single average
    overlap : `int`
        number of samples between averages
    window : `timeseries.Window`, optional
        window function to apply to timeseries prior to FFT

    Returns
    -------
    Spectrum
        Welch-averaged `Spectrum`
    """
    try:
        return lal_psd(timeseries, 'welch', segmentlength, overlap,
                       window=window)
    except ImportError:
        return scipy_psd(timeseries, 'welch', segmentlength, overlap,
                         window=window)


def median_mean(timeseries, segmentlength, overlap, window=None):
    """Calculate the power spectral density of the given `TimeSeries`
    using the median-mean average method.

    For more details see :lalsuite:`XLALREAL8AverageSpectrumMedianMean`.

    Parameters
    ----------
    timeseries : `TimeSeries`
        input `TimeSeries` data
    segmentlength : `int`
        number of samples in single average
    overlap : `int`
        number of samples between averages
    window : `timeseries.Window`, optional
        window function to apply to timeseries prior to FFT

    Returns
    -------
    Spectrum
        median-mean-averaged `Spectrum`
    """
    return lal_psd(timeseries, 'medianmean', segmentlength, overlap,
                    window=window)


def median(timeseries, segmentlength, overlap, window=None):
    """Calculate the power spectral density of the given `TimeSeries`
    using the median-mean average method.

    For more details see :lalsuite:`XLALREAL8AverageSpectrumMean`.

    Parameters
    ----------
    timeseries : `TimeSeries`
        input `TimeSeries` data
    segmentlength : `int`
        number of samples in single average
    overlap : `int`
        number of samples between averages
    window : `timeseries.Window`, optional
        window function to apply to timeseries prior to FFT

    Returns
    -------
    Spectrum
        median-mean-averaged `Spectrum`
    """
    return lal_psd(timeseries, 'medianmean', segmentlength, overlap,
                    window=window)


def lal_psd(timeseries, method, segmentlength, overlap, window=None):
    """Internal wrapper to the `lal.spectrum.psd` function

    This function handles the conversion between GWpy `TimeSeries` and
    XLAL ``TimeSeries``, (e.g. :lalsuite:`XLALREAL8TimeSeries`).

    Parameters
    ----------
    timeseries : `TimeSeries`
        input `TimeSeries` data
    method : `str`
        average method
    segmentlength : `int`
        number of samples in single average
    overlap : `int`
        number of samples between averages
    window : `timeseries.Window`, optional
        window function to apply to timeseries prior to FFT

    Returns
    -------
    Spectrum
        average power `Spectrum`
    """
    try:
        from lal.spectrum import averagespectrum as lalspectrum
    except ImportError as e:
        raise ImportError('%s. Try using gwpy.spectrum.scipy_psd instead'
                          % str(e))
    if isinstance(segmentlength, units.Quantity):
        segmentlength = segmentlength.value
    if isinstance(overlap, units.Quantity):
        overlap = overlap.value
    lalts = timeseries.to_lal()
    lalwin = window is not None and window.to_lal() or None
    lalfs = lalspectrum._psd(method, lalts, segmentlength, overlap,
                             window=lalwin)
    spec = Spectrum.from_lal(lalfs)
    if timeseries.unit:
        spec.unit = timeseries.unit ** 2 / units.Hertz
    else:
        spec.unit = 1 / units.Hertz
    return spec

def scipy_psd(timeseries, method, segmentlength, overlap, window='hanning'):
    """Internal wrapper to the `lal.spectrum.psd` function

    This function handles the conversion between GWpy `TimeSeries` and
    XLAL ``TimeSeries``, (e.g. :lalsuite:`XLALREAL8TimeSeries`).

    Parameters
    ----------
    timeseries : `TimeSeries`
        input `TimeSeries` data
    method : `str`
        average method
    segmentlength : `int`
        number of samples in single average
    overlap : `int`
        number of samples between averages
    window : `timeseries.Window`, optional
        window function to apply to timeseries prior to FFT

    Returns
    -------
    Spectrum
        average power `Spectrum`
    """
    methods = ['welch', 'bartlett']
    if method.lower() not in methods:
        raise ValueError("'method' must be one of: '%s'" % "','".join(methods))
    if isinstance(segmentlength, units.Quantity):
        segmentlength = segmentlength.value
    if isinstance(overlap, units.Quantity):
        overlap = overlap.value
    f, psd_ = signal.welch(timeseries.data, fs=timeseries.sample_rate.value,
                           window=window, nperseg=segmentlength,
                           noverlap=(segmentlength-overlap))
    spec = psd_.view(Spectrum)
    spec.name = timeseries.name
    spec.epoch = timeseries.epoch
    spec.channel = timeseries.channel
    spec.f0 = f[0]
    spec.df = f[1]-f[0]
    if timeseries.unit:
        spec.unit = timeseries.unit ** 2 / units.Hertz
    else:
        spec.unit = 1 / units.Hertz
    return spec
