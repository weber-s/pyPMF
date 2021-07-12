import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.colors as mcolors
import seaborn as sns

from .utils import get_sourceColor, add_season

def _pretty_specie(text):
    map_species = {
        "Cl-": "Cl$^-$",
        "Na+": "Na$^+$",
        "K+": "K$^+$",
        "NO3-": "NO$_3^-$",
        "NH4+": "NH$_4^+$",
        "SO42-": "SO$_4^{2-}$",
        "Mg2+": "Mg$^{2+}$",
        "Ca2+": "Ca$^{2+}$",
        "nss-SO42-": "nss-SO$_4^{2-}$",
        "OP_DTT_m3": "OP$^{DTT}_v$",
        "OP_AA_m3": "OP$^{AA}_v$",
        "OP_DTT_µg": "OP$^{DTT}_m$",
        "OP_AA_µg": "OP$^{AA}_m$",
        "PM_µg/m3": "PM mass",
    }
    if text in map_species.keys():
        return map_species[text]
    else:
        return text

def pretty_specie(text):
    if isinstance(text, list):
        mapped = [_pretty_specie(x) for x in text]
    elif isinstance(text, str):
        mapped = _pretty_specie(text)
    else:
        raise KeyError(
            "`text` must be a {x,y}ticklabels, a list of string or string"
        )
    return mapped

class Plotter():
    """
    Lot's of plot in this class for a PMF object!
    """
    def __init__(self, pmf, savedir):
        self.pmf = pmf
        self.savedir = savedir

    def _save_plot(self, formats=["png"], name="plot", DIR=""):
        """Save plot in a given format.
        
        Parameters
        ----------

        formats : list of str, format of the figure (see plt.savefig)
        name : string, default "plot". File name.
        DIR : string, default "". Directory for saving.
        """
        for fmt in formats:
            plt.savefig("{DIR}{name}.{fmt}".format(DIR=DIR,
                                                   name=name.replace("/", "-"), fmt=fmt))

    def _plot_per_microgramm(self, df=None, constrained=True, profile=None, species=None,
                             new_figure=False, **kwargs):
        """Internal method
        """
        pmf = self.pmf

        if new_figure:
            plt.figure(figsize=(12, 4))
            ax = plt.gca()
        elif "ax" in kwargs:
            ax = kwargs["ax"]

        if constrained:
            dfprofiles = pmf.dfprofiles_c
        else:
            dfprofiles = pmf.dfprofiles_b

        if df is not None:
            d = df.xs(profile, level="Profile") \
                    / (df.xs(profile, level="Profile").loc[pmf.totalVar])
            d = d.reindex(species).unstack().reset_index()
        else:
            d = None

        dref = dfprofiles[profile] / dfprofiles.loc[pmf.totalVar, profile]
        dref = dref.reset_index()

        if df is not None:
            sns.boxplot(data=d.replace({0: np.nan}), x="Specie", y=0,
                        color="grey", ax=ax)
        sns.stripplot(data=dref.replace({0: np.nan}), x="Specie", y=profile,
                      ax=ax, jitter=False, color="red")
        ax.set_yscale('log')
        ax.set_xticklabels(
            pretty_specie([t.get_text() for t in ax.get_xticklabels()]),
            rotation=90
        )
        ax.set_ylim((10e-6, 3))
        ax.set_ylabel("µg/µg")
        ax.set_xlabel("")
        ax.set_title(profile)

        #Create custom artists
        refArtist = plt.Line2D((0, 1),(0, 0), color='red', marker='o', linestyle='')
        BSArtist = plt.Rectangle((0, 0), 0, 0, color="grey")
        handles = [refArtist, BSArtist]
        labels = ["Ref. run", "BS"]
        ax.legend(handles=handles, labels=labels, loc="upper left", bbox_to_anchor=(1., 1.), frameon=False)

    def _plot_totalspeciesum(self, df=None, constrained=True, profile=None,
                             species=None, sumsp=None, new_figure=False,
                             **kwargs):
        """TODO: Docstring for _plot_totalspeciesum.

        Parameters
        ----------

        df : TODO
        constrained : Boolean, either to use the constrained run or the base run
        profile : TODO
        species : TODO
        sumsp : dataframe with the sum of each species
        new_figure : TODO

        """
        pmf = self.pmf

        if new_figure:
            plt.figure(figsize=(12, 4))
            ax = plt.gca()
        elif "ax" in kwargs:
            ax = kwargs["ax"]

        if constrained:
            dfprofiles = pmf.dfprofiles_c
        else:
            dfprofiles = pmf.dfprofiles_b

        if sumsp is None and df is not None:
            sumsp = pd.DataFrame(columns=species, index=['sum'])
            for sp in species:
                sumsp[sp] = df.loc[(sp, slice(None)), :].mean(axis=1).sum()

        if df is not None:
            d = df.xs(profile, level="Profile").divide(sumsp.iloc[0], axis=0) * 100
            d.index.names = ["Specie"]
            d = d.reindex(species).unstack().reset_index()

        dref = dfprofiles[profile].divide(dfprofiles.sum(axis=1)) * 100
        dref = dref.reset_index()

        if df is not None:
            sns.barplot(data=d, x="Specie", y=0, color="grey", ci="sd", ax=ax, label="BS (sd)")

        sns.stripplot(data=dref, x="Specie", y=0, color="red", jitter=False,
                      ax=ax, label="Ref. run")
        ax.set_xticklabels(
            pretty_specie([t.get_text() for t in ax.get_xticklabels()]),
            rotation=90
        )
        ax.set_ylim((0, 100))
        ax.set_ylabel("% of total specie sum")
        ax.set_xlabel("")
        ax.set_title(profile)

        h, l = ax.get_legend_handles_labels()
        h = h[-2:]
        l = l[-2:]
        ax.legend(handles=h, labels=l, loc="upper left", bbox_to_anchor=(1., 1.), frameon=False)

    def _plot_contrib(self, constrained=True, dfBS=None, dfDISP=None, dfcontrib=None,
                      profile=None, specie=None, BS=True, DISP=True,
                      BSDISP=False, new_figure=False, **kwargs):
        """TODO: Docstring for _plot_contrib.

        Parameters
        ----------

        dfBS  : pd.DataFrame
        dfDISP : TODO
        dfcontrib : TODO
        profile : TODO
        specie : TODO
        BS : TODO
        DISP : TODO
        BSDISP : TODO
        new_figure : TODO

        """
        pmf = self.pmf
        
        if new_figure:
            plt.figure(figsize=(12, 4))
            ax = plt.gca()
        elif "ax" in kwargs:
            ax = kwargs["ax"]

        if constrained:
            dfprofiles = pmf.dfprofiles_c
        else:
            dfprofiles = pmf.dfprofiles_b

        fill_kwarg = dict(
            alpha=0.5,
            edgecolor="black",
            linewidth=0,
        )
        with sns.axes_style("ticks"):
            if BS:
                d = pd.DataFrame(
                    columns=dfBS.columns,
                    index=dfcontrib.index
                )
                for BS in dfBS.columns:
                    d[BS] = dfcontrib[profile] * dfBS.xs(profile, level="Profile").loc[specie][BS]
                mstd = d.std(axis=1)
                ma = d.mean(axis=1)
                plt.fill_between(
                    ma.index, ma-mstd, ma+mstd,
                    label="BS (sd)", **fill_kwarg
                )
                # d.mean(axis=1).plot(marker="*")
            if DISP:
                d = pd.DataFrame(
                    columns=dfDISP.columns,
                    index=dfcontrib.index
                )
                for DISP in ["DISP Min", "DISP Max"]:
                    d[DISP] = dfcontrib[profile] * dfDISP.xs(profile, level="Profile").loc[specie][DISP]
                plt.fill_between(
                    d.index, d["DISP Min"], d["DISP Max"],
                    label="DISP (min-max)", **fill_kwarg
                )
            plt.plot(
                dfcontrib.index, dfcontrib[profile] * dfprofiles.loc[specie, profile],
                color="#888a85", marker="*", label="Ref. run"
            )
            ax.set_ylabel("Contribution to {} ($µg.m^{{-3}}$)".format(specie))
            ax.set_xlabel("")
            ax.set_title(profile)
            ax.legend(loc="upper left", bbox_to_anchor=(1., 1.), frameon=False)

    def _plot_profile(self, constrained=True, dfcontrib=None, dfBS=None, dfDISP=None, profile=None,
                      specie=None, BS=False, DISP=False, BSDISP=False):
        """TODO: Docstring for _plot_profile.

        constrained : Boolean, either to use the constrained run or the base one
        dfcontrib : TODO
        profile : TODO
        specie : TODO
        BS : TODO
        DISP : TODO
        BSDISP : TODO

        """
        pmf = self.pmf

        gs_profile = GridSpec(nrows=2, ncols=1, top=0.95, bottom=0.41, hspace=0.15)
        gs_contrib = GridSpec(nrows=3, ncols=1)

        fig = plt.figure(figsize=(12, 12))
        ax1 = fig.add_subplot(gs_profile[0])
        ax2 = fig.add_subplot(gs_profile[1], sharex=ax1)
        ax3 = fig.add_subplot(gs_contrib[2])

        self._plot_per_microgramm(
            df=dfBS, constrained=constrained, profile=profile, species=pmf.species,
            new_figure=False, ax=ax1
        )

        self._plot_totalspeciesum(
            df=dfBS, constrained=constrained, profile=profile, species=pmf.species,
            new_figure=False, ax=ax2
        )

        self._plot_contrib(
            constrained=constrained,
            dfcontrib=dfcontrib,
            dfBS=dfBS, dfDISP=dfDISP,
            BS=BS, DISP=DISP,
            profile=profile, specie=specie,
            new_figure=False, ax=ax3
        )

        # axes[0].xaxis.tick_top()

        for ax in fig.axes:
            ax.set_title("")

        # ax1.set_xticklabels("")
        plt.setp(ax1.get_xticklabels(), visible=False)

        fig.suptitle(profile)

        fig.subplots_adjust(
            top=0.95,
            bottom=0.05,
            left=0.125,
            right=0.865,
            hspace=0.40,
            wspace=0.015
        )

    def _plot_ts_stackedbarplot(self, df, ax):
        idx = df.index
        c = get_sourceColor()

        # Date index
        x = df.index

        # Width
        # Set it to 1.5 when no overlapping, 1 otherwise.
        width = np.ones(len(x))*1.5
        deltal = x[1:]-x[:-1]
        deltal = deltal.append(pd.TimedeltaIndex([10,], 'D'))
        deltar = pd.TimedeltaIndex([3], 'D')
        deltar = deltar.append(x[1:]-x[:-1])
        width[deltal < np.timedelta64(2, 'D')] = 1
        width[deltar < np.timedelta64(2, 'D')] = 1

        # Stacked bar plot
        count = 0
        default_colors = iter(mcolors.TABLEAU_COLORS.values())
        for i in range(df.shape[1]):
            bottom=df.iloc[:,0:count].sum(axis=1)
            count += 1
            try:
                color = c[df.columns[i]]
            except:
                color = next(default_colors)
            ax.bar(x, df[df.columns[i]],
                   bottom=bottom,
                   label=df.columns[i],
                   width=width,
                   color=color)

        ax.set_ylim(bottom=0)

    def _get_polluted_days_mean(self, specie=None, constrained=True, threshold=None):
        """Get the mean contribution of the sources for the given specie for polluted and
        non-polluted days define by the threshold

        Parameters
        ----------

        specie : str
        constrained : boolean
        threshold : int

        Returns
        -------

        df : pd.DataFrame
            Mean contribution by profile for the 2 categories
        """

        if specie is None:
            specie = self.pmf.totalVar


        df = self.pmf.to_cubic_meter(specie=specie, constrained=constrained)
        df["polluted"] = df.sum(axis=1) > threshold
        n_polluted = df["polluted"].sum()
        n_not_polluted = df["polluted"].count() - n_polluted

        df["polluted"].replace(
                {
                    True: "> {} µg/m³\n(n={})".format(threshold, n_polluted),
                    False: "≤ {} µg/m³\n(n={})".format(threshold, n_not_polluted)
                },
                inplace=True
        )

        df = df.melt(id_vars=["polluted"], var_name=["Profile"], value_name=specie)\
            .groupby(["polluted", "Profile"])\
            .mean()\
            .reset_index()\
            .pivot(index=["polluted"], columns=["Profile"])

        df.columns = df.columns.get_level_values("Profile")

        return df

    def plot_per_microgramm(self, df=None, constrained=True, profiles=None, species=None,
                            plot_save=False, savedir=None):
        """Plot profiles in concentration unique (µg/m3).

        Parameters
        ----------

        df : DataFrame with multiindex [species, profile] and an arbitrary
           number of column.  Default to dfBS_profile_c.
        constrained : Boolean, either to use the constrained run or the base run
        profiles : list of str, profile to plot (one figure per profile)
        species : list of str, specie to plot (x-axis)
        plot_save : boolean, default False. Save the graph in savedir.
        savedir : string, directory to save the plot.
        """
        pmf = self.pmf

        if df is None:
            if constrained:
                if pmf.dfBS_profile_c is None:
                    pmf.read.read_constrained_bootstrap()
                df = pmf.dfBS_profile_c
                if pmf.dfprofiles_c is None:
                    pmf.read.read_constrained_profiles()
            else:
                if pmf.dfBS_profile_b is None:
                    pmf.read.read_base_bootstrap()
                df = pmf.dfBS_profile_b
                if pmf.dfprofiles_b is None:
                    pmf.read.read_base_profiles()
        elif not(isinstance(df, pd.DataFrame)):
            raise TypeError("df should be a pandas DataFrame.")
        

        if profiles is None:
            if pmf.profiles is None:
                pmf.read.read_metadata()
            profiles = pmf.profiles
        elif not(isinstance(profiles, list)):
            raise TypeError("profiles should be a list.")

        if species is None:
            if pmf.species is None:
                pmf.read.read_metadata()
            species = pmf.species
        elif not(isinstance(species, list)):
            raise TypeError("species should be a list.")

        if savedir is None:
            savedir = self.savedir

        for p in profiles:
            self._plot_per_microgramm(df=df, constrained=constrained, profile=p, species=species,
                                      new_figure=True)
            plt.subplots_adjust(left=0.1, right=0.9, bottom=0.3, top=0.9)
            if plot_save: self._save_plot(DIR=savedir, name=p+"_profile_perµg")

    def plot_totalspeciesum(self, df=None, profiles=None, species=None, constrained=True,
                            plot_save=False, savedir=None, **kwargs):
        """Plot profiles in percentage of total specie sum (%).

        Parameters
        ----------

        df : DataFrame with multiindex [species, profile] and an arbitrary
           number of column.  Default to dfBS_profile_c.
        profiles : list, profile to plot (one figure per profile)
        species : list, specie to plot (x-axis)
        plot_save : boolean, default False. Save the graph in savedir.
        savedir : string, directory to save the plot.
        """
        pmf = self.pmf

        if df is None:
            if constrained:
                if pmf.dfBS_profile_c is None:
                    pmf.read.read_constrained_bootstrap()
                df = pmf.dfBS_profile_c
                if pmf.dfprofiles_c is None:
                    pmf.read.read_constrained_profiles()
            else:
                if pmf.dfBS_profile_b is None:
                    pmf.read.read_base_bootstrap()
                df = pmf.dfBS_profile_b
                if pmf.dfprofiles_b is None:
                    pmf.read.read_base_profiles()

        if profiles is None:
            if pmf.profiles is None:
                pmf.read.read_metadata()
            profiles = pmf.profiles

        if species is None:
            if pmf.species is None:
                pmf.read.read_metadata()
            species = pmf.species

        if savedir is None:
            savedir = self.savedir

        new_figure = kwargs.pop("new_figure", True)

        sumsp = pd.DataFrame(columns=species, index=['sum'])
        for sp in species:
            sumsp[sp] = df.loc[(sp, slice(None)),:].mean(axis=1).sum()
        for p in profiles:
            self._plot_totalspeciesum(df=df, profile=p, species=species,
                                      sumsp=sumsp, new_figure=new_figure,
                                      **kwargs)
            plt.subplots_adjust(left=0.1, right=0.9, bottom=0.3, top=0.9)
            if plot_save:
                self._save_plot(DIR=savedir, name=p+"_profile")

    def plot_contrib(self, dfBS=None, dfDISP=None, dfcontrib=None, profiles=None,
                     specie=None, constrained=True, plot_save=False, savedir=None,
                     BS=True, DISP=True, BSDISP=False, new_figure=True, **kwargs):
        """Plot temporal contribution in µg/m3.

        Parameters
        ----------

        df : pd.DataFrame, default self.dfBS_profile_c
            DataFrame with multiindex [species, profile] and an arbitrary number
            of column.
        dfcontrib : pd.DataFrame, default self.dfcontrib_c
            Profile as column and specie as index.
        profiles : list of string, default self.profiles
            profile to plot (one figure per profile)
        specie : string, default totalVar.
            specie to plot (y-axis)
        plot_save : boolean, default False
            Save the graph in savedir.
        savedir : string
            directory to save the plot
        """
        pmf = self.pmf

        if (dfBS is None) and (BS):
            if constrained:
                if pmf.dfBS_profile_c is None:
                    pmf.read.read_constrained_bootstrap()
                dfBS = pmf.dfBS_profile_c
            else:
                if pmf.dfBS_profile_b is None:
                    pmf.read.read_base_bootstrap()
                dfBS = pmf.dfBS_profile_b

        if (dfDISP is None) and (DISP):
            if constrained:
                if pmf.df_uncertainties_summary_c is None:
                    pmf.read.read_constrained_uncertainties_summary()
                dfDISP = pmf.df_uncertainties_summary_c[["DISP Min", "DISP Max"]]
            else:
                if pmf.df_uncertainties_summary_b is None:
                    pmf.read.read_base_uncertainties_summary()
                dfDISP = pmf.df_uncertainties_summary_b[["DISP Min", "DISP Max"]]

        if dfcontrib is None:
            if constrained:
                if pmf.dfcontrib_c is None:
                    pmf.read.read_constrained_contributions()
                dfcontrib = pmf.dfcontrib_c
            else:
                if pmf.dfcontrib_b is None:
                    pmf.read.read_base_contributions()
                dfcontrib = pmf.dfcontrib_b

        if profiles is None:
            if pmf.profiles is None:
                pmf.read.read_metadata()
            profiles = pmf.profiles

        # if pmf.dfprofiles_c is None:
        #     pmf.read.read_constrained_profiles()

        if specie is None:
            if pmf.totalVar is None:
                pmf.read.read_metadata()
            specie = pmf.totalVar
        elif not isinstance(specie, str):
            raise ValueError(
                "`specie` should be a string, got {}.".format(specie)
            )

        if savedir is None:
            savedir = self.savedir

        for p in profiles:
            self._plot_contrib(dfBS=dfBS, dfDISP=dfDISP,
                               dfcontrib=dfcontrib, constrained=constrained,
                               profile=p, specie=specie, BS=BS, DISP=DISP,
                               BSDISP=BSDISP, new_figure=new_figure,
                               **kwargs)
            plt.subplots_adjust(left=0.1, right=0.85, bottom=0.1, top=0.9)
            if plot_save:
                self._save_plot(DIR=savedir, name=p+"_contribution")

    def plot_all_profiles(self, constrained=True, profiles=None, specie=None,
                          BS=True, DISP=True, BSDISP=False, plot_save=False,
                          savedir=None):
        """TODO: Docstring for plot_all_profiles.

        Parameters
        ----------

        constrained : Boolean, default True
            Either to use the constrained run or the base one
        profiles : list of string
            Profiles to plot
        species : ?
        {BS, DISP, BSDISP} : boolean, default True, True, False
            Use them as error estimation
        plot_save : boolean, default False
            Either or not saving the plot
        savedir : str
            Path to save the plot

        """
        pmf = self.pmf

        if profiles is None:
            if pmf.profiles is None:
                pmf.read.read_metadata()
            profiles = pmf.profiles

        if BS:
            if constrained:
                if pmf.dfBS_profile_c is None:
                    pmf.read.read_constrained_bootstrap()
                dfBS = pmf.dfBS_profile_c
            else:
                if pmf.dfBS_profile_b is None:
                    pmf.read.read_base_bootstrap()
                dfBS = pmf.dfBS_profile_b
        else:
            dfBS = None

        if DISP:
            if constrained:
                if pmf.df_uncertainties_summary_c is None:
                    pmf.read.read_constrained_uncertainties_summary()
                dfDISP = pmf.df_uncertainties_summary_c[["DISP Min", "DISP Max"]]
            else:
                if pmf.df_uncertainties_summary_b is None:
                    pmf.read.read_base_uncertainties_summary()
                dfDISP = pmf.df_uncertainties_summary_b[["DISP Min", "DISP Max"]]
        else:
            dfDISP = None

        if constrained:
            if pmf.dfcontrib_c is None:
                pmf.read.read_constrained_contributions()
            dfcontrib = pmf.dfcontrib_c
        else:
            if pmf.dfcontrib_b is None:
                pmf.read.read_base_contributions()
            dfcontrib = pmf.dfcontrib_b

        if constrained:
            if pmf.dfprofiles_c is None:
                pmf.read.read_constrained_profiles()
        else:
            if pmf.dfprofiles_b is None:
                pmf.read.read_base_profiles()

        if specie is None:
            if pmf.totalVar is None:
                pmf.read.read_metadata()
            specie = pmf.totalVar

        if savedir is None:
            savedir = self.savedir

        for p in profiles:
            self._plot_profile(
                constrained=constrained, dfcontrib=dfcontrib, dfBS=dfBS, dfDISP=dfDISP, profile=p,
                specie=specie, BS=BS, DISP=DISP, BSDISP=BSDISP
            )
            if plot_save:
                self._save_plot(
                    DIR=savedir,
                    name=pmf._site+"_"+p+"_contribution_and_profiles"
                )

    def plot_stacked_contribution(self, constrained=True, order=None, plot_kwargs=None):
        """Plot a stacked plot for the contribution

        Parameters
        ----------

        constrained : TODO
        order : TODO
        plot_kwargs : TODO

        """
        pmf = self.pmf

        df = pmf.to_cubic_meter(constrained=constrained)
        if order:
            if isinstance(order, list):
                df = df.reindex(order, axis=1)
            else:
                df = df.reindex(sorted(df.columns), axis=1)
        labels = df.columns

        y = np.vstack(df.values).T
        colors = [
            get_sourceColor(c) for c in labels #get_sourcesCategories(labels)
        ]
        
        fig, ax = plt.subplots(figsize=(14, 4))
        ax.stackplot(df.index, y, colors=colors, labels=labels)
        ax.set_ylabel(pmf.totalVar + " (µg m⁻³)")
        ax.set_ylim(0, ax.get_ylim()[1])
        ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1., 1.))
        plt.subplots_adjust(
            top=0.961,
            bottom=0.081,
            left=0.042,
            right=0.87,
            hspace=0.2,
            wspace=0.2
        )

    def plot_seasonal_contribution(self, constrained=True, dfcontrib=None, dfprofiles=None, profiles=None,
            specie=None, plot_save=False, savedir=None, annual=True,
            normalize=True, ax=None, barplot_kwarg={}):
        """Plot the relative contribution of the profiles.

        Parameters
        ----------

        dfcontrib : DataFrame with contribution as column and date as index.
        dfprofiles : DataFrame with profile as column and specie as index.
        profiles : list, profile to plot (one figure per profile)
        specie : string, default totalVar. specie to plot
        plot_save : boolean, default False. Save the graph in savedir.
        savedir : string, directory to save the plot.
        annual : plot annual contribution
        normalize : plot relative contribution or absolute contribution.

        Return
        ------

        df : DataFrame

        """
        pmf = self.pmf

        if dfcontrib is None:
            if constrained:
                if pmf.dfcontrib_c is None:
                    pmf.read.read_constrained_contributions()
                dfcontrib = pmf.dfcontrib_c
            else:
                if pmf.dfcontrib_b is None:
                    pmf.read.read_base_contributions()
                dfcontrib = pmf.dfcontrib_b

        if dfprofiles is None:
            if constrained:
                if pmf.dfprofiles_c is None:
                    pmf.read.read_constrained_profiles()
                dfprofiles = pmf.dfprofiles_c
            else:
                if pmf.dfprofiles_b is None:
                    pmf.read.read_base_profiles()
                dfprofiles = pmf.dfprofiles_b

        if profiles is None:
            if pmf.profiles is None:
                pmf.read.read_metadata()
            profiles = pmf.profiles

        if specie is None:
            if pmf.totalVar is None:
                pmf.read.read_metadata()
            specie = pmf.totalVar

        if savedir is None:
            savedir = self.savedir

        if ax is None:
            f, ax = plt.subplots(nrows=1, ncols=1, figsize=(7.5, 4.7))

        df = pmf.get_seasonal_contribution(specie=specie, normalize=normalize,
                                            annual=annual,
                                           constrained=constrained)

        colors = [get_sourceColor(c) for c in df.columns]

        df.index = [l.replace("_", " ") for l in df.index]
        axes = df.plot.bar(
            stacked=True,
            rot=0,
            color=colors,
            ax=ax,
            **barplot_kwarg
        )

        ax.set_ylabel("Normalized contribution" if normalize else "$µg.m^{-3}$")
        if normalize:
            ax.set_ylim([0, 1])
            ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
        ax.legend("", frameon=False)
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], loc='center left',
                  bbox_to_anchor=(1, 0.5), frameon=False)
        ax.set_xlabel("")
        ax.set_title(specie)
        plt.subplots_adjust(top=0.90, bottom=0.10, left=0.15, right=0.72)
        
        if plot_save:
            title = "_seasonal_contribution_{}".format(
                    "normalized" if normalize else "absolute"
                    )
            self._save_plot(DIR=savedir, name=pmf._site+title)
        
        return (df)

    def plot_stacked_profiles(self, constrained=True):
        """plot the repartition of the species among the profiles, normalized to
        100%

        Parameters
        ----------
        constrained : boolean, default True
            use the constrained run or not

        Returns
        -------
        ax : the axe
        """
        pmf = self.pmf

        df = pmf.get_total_specie_sum(constrained=constrained)

        df = df.sort_index(axis=1)

        colors = [get_sourceColor(c) for c in df.columns]

        fig, ax = plt.subplots(1, 1, figsize=(12, 4))
        df.plot(kind="bar", stacked=True, color=colors, ax=ax)

        xticklabels = [t.get_text() for t in ax.get_xticklabels()]
        ax.set_xticklabels(pretty_specie(xticklabels), rotation=90)
        ax.set_xlabel("")

        ax.yaxis.set_major_formatter(mticker.PercentFormatter())
        ax.set_ylabel("Normalized contribution (%)")
        ax.set_ylim(0, 100)

        h, l = ax.get_legend_handles_labels()
        h = reversed(h)
        l = reversed(l)
        ax.legend(h, l, loc="upper left", bbox_to_anchor=(1, 1), frameon=False)
        fig.subplots_adjust(bottom=0.275, top=0.96, left=0.09, right=0.83)

        return ax

    def plot_polluted_contribution(self, constrained=True, threshold=None, specie=None,
            normalize=True):
        """Plot a barplot splited by polluted/non-polluted days defined by the threshold
        given.

        Parameters
        ----------
        constrained : boolean, default True
            use the constrained run or not
        threshold : int, default 50
            Threshold in µg/m³ to define a polluted days
        specie : str, default to total variable
            specie to use
        normalize : boolean, default True
            normalized the graph

        """
        if specie is None:
            specie = self.pmf.totalVar

        df = self._get_polluted_days_mean(
                constrained=constrained,
                specie=specie,
                threshold=threshold
            )

        if normalize:
            df = (df.T / df.sum(axis=1)).T

        colors = get_sourceColor()[df.columns].loc["color"].to_dict()

        fig, ax = plt.subplots(1, 1, figsize=(5, 4))

        df.plot(
                kind="bar",
                stacked=True,
                color=colors,
                ax=ax
                )

        ax.legend(
                loc="center left",
                bbox_to_anchor=(1.05, 0.5),
                frameon=False
                )

        fig.subplots_adjust(right=0.6)


        if normalize:
            ax.set_ylim([0, 1])
            ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))

        plt.setp(ax.get_xticklabels(), rotation=0)
        ax.set_xlabel("")

        fig.suptitle("{}\nContribution of the sources for {}".format(self.pmf._site, specie))

    def plot_samples_sources_contribution(self, constrained=True, specie=None):
        """Plot bar plot of the contribution per sample (timeserie)
        """

        pmf = self.pmf

        if specie is None:
            specie = self.pmf.totalVar

        df = pmf.to_cubic_meter(specie=specie)

        fig, ax = plt.subplots()

        self._plot_ts_stackedbarplot(df, ax=ax)

        # legend stuff
        f = plt.gcf()
        h, l = ax.get_legend_handles_labels()
        f.legend(h, l, loc=7, frameon=False)

        plt.subplots_adjust(top=0.90, bottom=0.10, left=0.10, right=0.85)
