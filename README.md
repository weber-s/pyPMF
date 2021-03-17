[![Documentation Status](https://img.shields.io/badge/Documentation-API-green)](https://pypmf.readthedocs.io/)
[![PyPI version](https://badge.fury.io/py/pyPMF.svg)](https://badge.fury.io/py/pyPMF)


Positive Matrix Factorization in python
=======================================

Handle PMF output from various format in handy pandas DataFrame and do lot of stuf with
them.

Currently, only data from the EPA PMF5 is handle, from `xlsx` or sql database output.

History
-------

This project started because I needed to run several PMF for my PhD and also needed to run
some computation on these results.
The raw output of the EPA PMF5 software is a bit messy and hard to understand at a first
glance, and copy/pasting xlsx file is not my taste... So I ended developping this tools
for handling the tasks of maping the xlsx output to nice python objects, on which I can
easily run some computation.

Since I needed to plot the results afterward, I also added some plot utilities in this
package. It then has build in support for ploting :

 * chemical profile (both absolute and normalized)
 * species repartition among factor
 * timeserie contribution (*for all species* and profiles)
 * uncertainties plots (Bootstrap and DISP)
 * seasonal contribution
 * contribution of sources to polluted and normal days
 * And a lot more!


Examples
========

The [documentation](https://pypmf.readthedocs.io) has a lot of examples and figures, but here is a short summary:

```python
from pyPMF.PMF import PMF

pmf = PMF(site="GRE-fr", reader="xlsx", BDIR="./")

# Read various output
pmf.read.read_base_profiles()
pmf.read.read_base_contributions()
pmf.read.read_constrained_profiles()
pmf.read.read_constrained_contributions()
# ... or simply :
pmf.read.read_all()

# The pmf has now different attributes associated
pmf.profiles    # name of the different factors
pmf.species     # name of the different species
pmf.dfcontrib_c # contribution dataframe of factors
pmf.dfprofile_c # chemical profile of factors
# ... and lot more

# plot the results
pmf.plot.plot_stacked_profiles()


# or use some utilities
pmf.to_cubic_meter(specie="Cu") # Contribution timeserie of the different factors to the Cu
pmf.to_relative_mass()
# ... and lot more

```

