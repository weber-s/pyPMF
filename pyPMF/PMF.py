import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.colors as mcolors
import seaborn as sns

from .reader import readers
from .plotter import plotter
from .utils import get_sourcesCategories, add_season

class PMF(object):

    """PMF output of the US EPA PMF5.0 software in handy format (pandas DataFrame).
    Several utilities and plots are also available.
    """

    def __init__(self, site, reader=None, savedir="./", BDIR=None, SQL_connection=None,
            SQL_table_names=None, SQL_program=None):
        """PMF object from output of EPAPMF5.

        Parameters
        ----------

        site : str, the name of the site (prefix of each files if outputed in xlsx)
        reader : str, 'xlsx' or 'sql'
            Format of the saved output of the PMF
            
            - xlsx : saved as xlsx output. Need to specify also BDIR
            - sql : name of the SQL database. Need to specify also SQL_connection,
                  SQL_program and SQL_table_names

        savedir : str, default current path
            Path to directory to save the figures

        BDIR : str, the directory where the xlsx files live, if outputed in xlsx
        SQL_connection : SQL connection to a existing database
        SQL_program : str, optional
            If the database contains a "Program" column, specify the program wanted
        SQL_table_names : dict, mapping of PMF output and table name in the SQL database

        """
        self._site = site

        if reader == "xlsx":
            self.read = readers.XlsxReader(BDIR=BDIR, site=site, pmf=self)
        elif reader == "sql":
            self.read = readers.SqlReader(
                    site=site,
                    pmf=self,
                    SQL_program=SQL_program, SQL_connection=SQL_connection, SQL_table_names=SQL_table_names
                    )

        self.plot = plotter.Plotter(pmf=self, savedir=savedir)

        self.profiles = None
        self.nprofiles = None
        self.species = None
        self.nspecies = None
        self.totalVar = None
        self.dfprofiles_b = None
        self.dfcontrib_b = None
        self.dfprofiles_c = None
        self.dfcontrib_c = None
        self.dfBS_profile_b = None
        self.dfBS_profile_c = None
        self.dfbootstrap_mapping_b = None
        self.dfbootstrap_mapping_c = None
        self.df_disp_swap_b = None
        self.df_disp_swap_c = None
        self.df_uncertainties_summary_b = None
        self.df_uncertainties_summary_c = None

    def to_cubic_meter(self, specie=None, constrained=True, profiles=None):
        """Convert the contribution in cubic meter for the given specie

        Parameters
        ----------

        constrained : Boolean, default True
        specie : str, the specie, default totalVar
        profiles : list of profile, default all profiles

        Return
        ------

        df : pd.DataFrame

        """
        if specie is None:
            specie = self.totalVar

        if profiles is None:
            profiles = self.profiles

        if constrained:
            df = self.dfcontrib_c
            dfprofiles = self.dfprofiles_c
        else:
            df = self.dfcontrib_b
            dfprofiles = self.dfprofiles_b

        contrib = pd.DataFrame(index=df.index, columns=profiles)

        for profile in profiles:
            contrib[profile] = df[profile] * dfprofiles.loc[specie, profile]

        return contrib

    def to_relative_mass(self, constrained=True, species=None, profiles=None):
        """Compute the factor profile relative mass (i.e. each species divided
        by the totalVar mass)

        Parameters
        ----------

        constrained : Boolean, default True
        species : list of str, default all species
        profiles : list of str, default all profiles

        Return
        ------
        
        df : pd.DataFrame

        """
        if constrained:
            df = self.dfprofiles_c
        else:
            df = self.dfprofiles_b

        if profiles is None:
            profiles = self.profiles

        if species is None:
            species = self.species

        d = df[profiles] / df.loc[self.totalVar, profiles]

        return d

    def get_total_specie_sum(self, constrained=True):
        """
        Return the total specie sum profiles in %

        Parameters
        ----------

        constrained : boolean, default True
            use the constrained run or not

        Returns
        -------

        df : pd.DataFrame
            The normalized species sum per profiles
        """
        if constrained:
            df = self.dfprofiles_c.copy()
        else:
            df = self.dfprofiles_b.copy()

        # df = (self.dfprofiles_c.T / self.dfprofiles_c.sum(axis=1)).T * 100
        df = (df.T / df.sum(axis=1)).T * 100
        return df

    def get_seasonal_contribution(self, specie=None, annual=True,
                                  normalize=True, constrained=True):
        """
        Get a dataframe of seasonal contribution

        Parameters
        ----------

        specie : str, default to total variable
        annual : Boolean, default True, add annual contribution
        normalize : Boolean, default True, normalize to 100%
        constrained : Boolean, default True

        Return
        ------

        df : pd.DataFrame
            seasonal contribution
        """

        if constrained:
            if self.dfprofiles_c is None:
                self.read.read_constrained_profiles()
            if self.dfcontrib_c is None:
                self.read.read_constrained_contributions()
            dfprofiles = self.dfprofiles_c
            dfcontrib = self.dfcontrib_c
        else:
            if self.dfprofiles_b is None:
                self.read.read_base_profiles()
            if self.dfcontrib_b is None:
                self.read.read_base_contributions()
            dfprofiles = self.dfprofiles_b
            dfcontrib = self.dfcontrib_b

        if specie is None:
            if self.totalVar is None:
                self.read.read_metadata()
            specie = self.totalVar


        dfcontribSeason = (dfprofiles.loc[specie] * dfcontrib).sort_index(axis=1)
        ordered_season = ["Winter", "Spring", "Summer", "Fall"]
        if annual:
            ordered_season.append("Annual")

        dfcontribSeason = add_season(dfcontribSeason, month=False)\
                .infer_objects()
        dfcontribSeason = dfcontribSeason.groupby("season")

        if normalize:
            df = (dfcontribSeason.sum().T / dfcontribSeason.sum().sum(axis=1))
            df = df.T
        else:
            df = dfcontribSeason.mean()

        if annual:
            df.loc["Annual", :] = df.mean()

        df = df.reindex(ordered_season)

        return df

    def replace_totalVar(self, newTotalVar):
        """replace the total var to all dataframe

        Parameters
        ----------

        newTotalVar : str
        """
        DF = [
            self.dfprofiles_b,
            self.dfprofiles_c,
            self.dfBS_profile_b,
            self.dfBS_profile_c,
            self.df_uncertainties_summary_b,
            self.df_uncertainties_summary_c,
        ]
        for df in DF:
            if df is None:
                continue
            df.rename({self.totalVar: newTotalVar}, inplace=True, axis=0)

        self.species = [newTotalVar if x == self.totalVar else x for x in self.species]
        self.totalVar = newTotalVar

    def rename_profile_to_profile_category(self):
        """Rename the factor profile name to match the category

        See pyPMF.utils.get_sourcesCategories
        """
        DF = [
            self.dfprofiles_b,
            self.dfprofiles_c,
            self.dfcontrib_b,
            self.dfcontrib_c,
            self.dfBS_profile_b,
            self.dfBS_profile_c,
            self.df_uncertainties_summary_b,
            self.df_uncertainties_summary_c,
        ]
        for df in DF:
            if df is None:
                continue
            possible_sources = {
                p: get_sourcesCategories([p])[0]
                for p in self.profiles
            }
            df.rename(possible_sources, inplace=True, axis=1)
            df.rename(possible_sources, inplace=True, axis=0)

        self.profiles = [possible_sources[p] for p in self.profiles]
        
    def rename_profile(self, mapper):
        """Rename a factor profile

        Parameters
        ----------

        mapper : dict
            Key of the dictionnary are the old name, and value the desired name
        """
        DF = [
            self.dfprofiles_b,
            self.dfprofiles_c,
            self.dfcontrib_b,
            self.dfcontrib_c,
            self.dfBS_profile_b,
            self.dfBS_profile_c,
            self.df_uncertainties_summary_b,
            self.df_uncertainties_summary_c,
        ]
        for df in DF:
            if df is None:
                continue
            df.rename(mapper, inplace=True, axis=1)
            df.rename(mapper, inplace=True, axis=0)

        new_profiles = []
        for p in self.profiles:
            if p in mapper.keys():
                new_profiles.append(mapper[p])
            else:
                new_profiles.append(p)
        self.profiles = new_profiles

    def recompute_new_species(self, specie):
        """Recompute a specie given the other species. For instance, recompute OC
        from OC* and a list of organic species.

        It modify inplace both dfprofile_b and dfprofile_c, and update
        self.species.

        Parameters
        ----------

        specie : str in ["OC",]

        """
        knownSpecies = ["OC"]
        if specie not in knownSpecies:
            return

        equivC = {
            'Oxalate': 0.27,
            'Arabitol': 0.40,
            'Mannitol': 0.40,
            'Sorbitol': 0.40,
            'Polyols': 0.40,
            'Levoglucosan': 0.44,
            'Mannosan': 0.44,
            'Galactosan': 0.44,
            'MSA': 0.12,
            'Glucose': 0.44,
            'Cellulose': 0.44,
            'Maleic': 0.41,
            'Succinic': 0.41,
            'Citraconic': 0.46,
            'Glutaric': 0.45,
            'Oxoheptanedioic': 0.48,
            'MethylSuccinic': 0.53,
            'Adipic': 0.49,
            'Methylglutaric': 0.49,
            '3-MBTCA': 0.47,
            'Phtalic': 0.58,
            'Pinic': 0.58,
            'Suberic': 0.55,
            'Azelaic': 0.57,
            'Sebacic': 0.59,
        }

        if specie == "OC":
            if specie not in self.species:
                self.species.append(specie)
            OCb = self.dfprofiles_b.loc["OC*"].copy()
            OCc = self.dfprofiles_c.loc["OC*"].copy()
            for sp in equivC.keys():
                if sp in self.species:
                    OCb += (self.dfprofiles_b.loc[sp] * equivC[sp]).infer_objects()
                    OCc += (self.dfprofiles_c.loc[sp] * equivC[sp]).infer_objects()
            self.dfprofiles_b.loc[specie] = OCb.infer_objects()
            self.dfprofiles_c.loc[specie] = OCc.infer_objects()


    def print_uncertainties_summary(self, constrained=True, profiles=None,
            species=None):
        """Get the uncertainties given by BS, BS-DISP and DISP for the given profiles and
        species

        Parameters
        ----------

        constrained : boolean, True
            Use the constrained run (False for the base run)
        profiles : list of str
            list of profiles, default all profiles
        species : list of str
            list of species, default all species

        Return
        ------

        df : pd.DataFrame
            BS, DISP and BS-DISP ranges
        """

        if constrained:
            if self.df_uncertainties_summary_c is None:
                self.read.read_constrained_uncertainties_summary()
            df = self.df_uncertainties_summary_c
        else:
            if self.df_uncertainties_summary_b is None:
                self.read.read_base_uncertainties_summary()
            df = self.df_uncertainties_summary_b

        if profiles is None:
            if self.profiles is None:
                self.read.read_metadata()
            profiles = self.profiles

        if species is None:
            if self.species is None:
                self.read.read_metadata()
            species = self.species

        return df.T.loc[:, (profiles, species)]

