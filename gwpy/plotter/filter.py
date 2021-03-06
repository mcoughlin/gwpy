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

"""Definition of a BodePlot
"""

from math import pi
import numpy
from scipy import signal

from matplotlib import ticker as mticker

from .core import Plot

from ..version import version as __version__
__author__ = "Duncan Macleod <duncan.macleod@ligo.org>"
__all__ = ['BodePlot']


class BodePlot(Plot):
    """An extension of the :class:`~gwpy.plotter.core.Plot` class for
    visualising filters using the Bode representation

    Parameters
    ----------
    *filters : :class:`~scipy.signal.lti`, `tuple`
        any number of linear time-invariant filters to
        display on the plot. If filters are given as tuples, they will
        be interpreted according to the number of elements:

            - 2: (numerator, denominator)
            - 3: (zeros, poles, gain)
            - 4: (A, B, C, D)

    frequencies : `numpy.ndarray`, optional
        list of frequencies (in Hertz) at which to plot
    sample_rate : `float`, optional
        sample_rate (in Hertz) for time-domain filter
    logx : `bool`, optional, default: False
        display frequency on a log-scale
    **kwargs
        other keyword arguments as applicable for the
        :class:`~gwpy.plotter.core.Plot`
    """
    def __init__(self, *filters, **kwargs):
        """Initialise a new TimeSeriesPlot
        """
        frequencies = kwargs.pop('frequencies', None)
        sample_rate = kwargs.pop('sample_rate', None)
        logx = kwargs.pop('logx', None)

        # generate figure
        super(BodePlot, self).__init__(**kwargs)

        # delete the axes, and create two more
        self.add_subplot(2, 1, 1, projection='spectrum')
        self.add_subplot(2, 1, 2, projection='spectrum', sharex=self.maxes)

        # auto set log and frequencies
        if logx is not False and frequencies is None and sample_rate:
            logx = True
            N = 512
            nyq = numpy.float64(sample_rate) / 2.0
            frequencies = numpy.logspace(numpy.log10(nyq / N),
                                         numpy.log10(nyq), N)

        # add filters
        for filter_ in filters:
            self.add_filter(filter_, frequencies=frequencies,
                            sample_rate=sample_rate)

        # set labels
        self.maxes.set_ylabel('Magnitude [dB]')
        self.paxes.set_xlabel('Frequency [Hz]')
        self.paxes.set_ylabel('Phase [deg]')

        # set log-scale
        if logx:
            self.maxes.set_xscale('log')
            self.paxes.set_xscale('log')
            self.maxes.relim()
            self.paxes.relim()
            self.maxes.autoscale_view(scalex=False)
            self.paxes.autoscale_view(scalex=False)

        # set xlim
        if frequencies is not None:
            self.maxes.set_xlim(frequencies.min(), frequencies.max())

        # set ylim
        self.paxes.yaxis.set_major_locator(mticker.MultipleLocator(base=90))
        self.paxes.set_ylim(0, 360)

    @property
    def maxes(self):
        """:class:`~matplotlib.axes.Axes` for the Bode magnitude
        """
        return self.axes[0]

    @property
    def paxes(self):
        """:class:`~matplotlib.axes.Axes` for the Bode phase
        """
        return self.axes[1]

    def add_filter(self, filter_, frequencies=None, sample_rate=None,
                   **kwargs):
        """Add a linear time-invariant filter to this BodePlot
        """
        if frequencies is None:
            w = None
        else:
            w = frequencies * 2 * pi / numpy.float64(sample_rate)
        if not isinstance(filter_, signal.lti):
            filter_ = signal.lti(*filter_)
        w, h = signal.freqz(filter_.num, filter_.den, w)
        if sample_rate:
            w *= numpy.float64(sample_rate) / (2.0 * pi)
        mag = 20.0 * numpy.log10(numpy.absolute(h))
        phase = numpy.degrees(numpy.unwrap(numpy.angle(h))) % 360
        lm = self.maxes.plot(w, mag, **kwargs)
        lp = self.paxes.plot(w, phase, **kwargs)
        return (lm, lp)


