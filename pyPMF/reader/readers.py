from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.colors as mcolors
import seaborn as sns
from py4pm.chemutilities import get_sourceColor, get_sourcesCategories, format_ions

XLSX_ENGINE = "xlrd"

class BaseReader(ABC):

    def __init__(self, site, pmf):
        self.site = site
        self.pmf = pmf

    @abstractmethod
    def read_base_profiles(self):
        """Read the "base" profiles result from the file: '_base.xlsx',
        sheet "Profiles", and add :

        - self.dfprofiles_b: constrained factors profile

        """
        pass

    @abstractmethod
    def read_constrained_profiles(self):
        """Read the "constrained" profiles result from the file: '_Constrained.xlsx',
        sheet "Profiles", and add :

        - self.dfprofiles_c: constrained factors profile

        """
        pass

    @abstractmethod
    def read_base_contributions(self):
        """Read the "base" contributions result from the file: '_base.xlsx',
        sheet "Contributions", and add :

        - self.dfcontrib_b: base factors contribution

        """
        pass

    @abstractmethod
    def read_constrained_contributions(self):
        """Read the "constrained" contributions result from the file: '_Constrained.xlsx',
        sheet "Contributions", and add :

        - self.dfcontrib_c: constrained factors contribution

        """
        pass

    @abstractmethod
    def read_base_bootstrap(self):
        """Read the "base" bootstrap result from the file: '_boot.xlsx'
        and add :

        - self.dfBS_profile_b: all mapped profile
        - self.dfbootstrap_mapping_b: table of mapped profiles

        """
        pass

    @abstractmethod
    def read_constrained_bootstrap(self):
        """Read the "base" bootstrap result from the file: '_Gcon_profile_boot.xlsx'
        and add :

        - self.dfBS_profile_c: all mapped profile
        - self.dfbootstrap_mapping_c: table of mapped profiles

        """
        pass

    @abstractmethod
    def read_base_uncertainties_summary(self):
        """Read the _BaseErrorEstimationSummary.xlsx file and add:

        - self.df_uncertainties_summary_b : uncertainties from BS, DISP and BS-DISP

        """
        pass

    @abstractmethod
    def read_constrained_uncertainties_summary(self):
        """Read the _ConstrainedErrorEstimationSummary.xlsx file and add :

        - self.df_uncertainties_summary_b : uncertainties from BS, DISP and BS-DISP

        """
        pass

    def read_metadata(self):
        """Get profiles, species and co

        It add a totalVariable (by default one of "PM10", "PM2.5", "PMrecons" or
        "PM10recons", "PM10rec"). Otherwise, try to guess (variable with "PM" on its
        name).
        """

        pmf = self.pmf

        if pmf.dfprofiles_b is None:
            read_base_profiles()

        pmf.profiles = pmf.dfprofiles_b.columns.tolist()
        pmf.nprofiles = len(pmf.profiles)
        pmf.species = pmf.dfprofiles_b.index.tolist()
        pmf.nspecies = len(pmf.species)

        TOTALVAR = ["PM10", "PM2.5", "PMrecons", "PM10rec", "PM10recons"]
        for x in TOTALVAR:
            if x in pmf.species:
                pmf.totalVar = x
        if pmf.totalVar is None:
            print("Warning: trying to guess total variable.")
            pmf.totalVar = [x for x in pmf.species if "PM" in x]
            if len(pmf.totalVar) >= 1:
                print("Warning: several possible total variable: {}".format(pmf.totalVar))
                print("Watning: taking the first one {}".format(pmf.totalVar[0]))
            pmf.totalVar = pmf.totalVar[0]
        print("Total variable set to: {}".format(pmf.totalVar))

    def read_all(self):
        """Read all possible data outputed by the PMF

        :returns: TODO

        """

        pmf = self.pmf
        for reader in ["read_base_profiles", "read_base_contributions",
                "read_base_bootstrap", "read_base_uncertainties_summary",
                "read_constrained_profiles", "read_constrained_contributions",
                "read_constrained_bootstrap", "read_constrained_uncertainties_summary"]:
            try:
                getattr(self, reader)()
            except FileNotFoundError:
                print("The file is not found for {}".format(reader))

class XlsxReader(BaseReader):
    """
    Accessor class for the PMF class with all reader methods.
    """

    def __init__(self, BDIR, site, pmf):
        super().__init__(site=site, pmf=pmf)

        self.BDIR = BDIR
        self.basename = BDIR + self.site


    def _split_df_by_nan(self, df):
        """Internet method the read the bootstrap file format:
        1 block of N lines (1 per factor) for each species, separated by an empty line.

        Parameter
        ---------

        df : pd.DataFrame
            The bootstrap data from the xlsx files. The header should be already removed.

        Return
        ------

        pd.DataFrame, formatted by factor and species

        """
        pmf = self.pmf
        d = {}
        dftmp = df.dropna()
        for i, sp in enumerate(pmf.species):
            d[sp] = dftmp.iloc[pmf.nprofiles*i:pmf.nprofiles*(i+1), :]
            d[sp].index = pmf.profiles
            d[sp].index.name = "profile"
            d[sp].columns = ["Boot{}".format(i) for i in range(len(d[sp].columns))]
        return d


    def read_base_profiles(self):
        """Read the "base" profiles result from the file: '_base.xlsx',
        sheet "Profiles", and add :

        - self.dfprofiles_b: constrained factors profile

        """
        pmf = self.pmf

        dfbase = pd.read_excel(
                self.basename+"_base.xlsx",
                sheet_name=['Profiles'],
                header=None,
                engine=XLSX_ENGINE
                )["Profiles"]

        idx = dfbase.iloc[:, 0].str.contains("Factor Profiles").fillna(False)
        idx = idx[idx].index.tolist()

        dfbase = dfbase.iloc[idx[0]:idx[1], 1:]
        dfbase.dropna(axis=0, how="all", inplace=True)
        factor_names = list(dfbase.iloc[0, 1:])
        dfbase.columns = ["specie"] + factor_names
        dfbase = dfbase\
                .drop(dfbase.index[0])\
                .set_index("specie")

        # check correct number of column
        idx = dfbase.columns.isna().argmax()
        if idx > 0:
            dfbase = dfbase.iloc[:, :idx]
            dfbase.dropna(how="all", inplace=True)
        # avoid 10**-12 possible concentration...
        dfbase = dfbase.infer_objects()
        dfbase[dfbase < 10e-6] = 0

        pmf.dfprofiles_b = dfbase

        super().read_metadata()

    def read_constrained_profiles(self):
        """Read the "constrained" profiles result from the file: '_Constrained.xlsx',
        sheet "Profiles", and add :

        - self.dfprofiles_c: constrained factors profile

        """
        pmf = self.pmf

        if pmf.profiles is None:
            read_base_profiles()

        dfcons = pd.read_excel(
                    self.basename+"_Constrained.xlsx",
                    sheet_name=['Profiles'],
                    header=None,
                    engine=XLSX_ENGINE
                )["Profiles"]

        idx = dfcons.iloc[:, 0].str.contains("Factor Profiles").fillna(False)
        idx = idx[idx].index.tolist()

        dfcons = dfcons.iloc[idx[0]:idx[1], 1:]
        dfcons.dropna(axis=0, how="all", inplace=True)

        # check correct number of column
        idx = dfcons.columns.isna().argmax()
        if idx > 0:
            dfcons = dfcons.iloc[:, :idx]
            dfcons.dropna(how="all", inplace=True)
        nancolumns = dfcons.isna().all()
        if nancolumns.any():
            dfcons = dfcons.loc[:, :nancolumns.idxmax()]
            dfcons.dropna(axis=1, how="all", inplace=True)

        dfcons.columns = ["specie"] + pmf.profiles
        dfcons = dfcons.set_index("specie")
        dfcons = dfcons[dfcons.index.notnull()]
        # avoid 10**-12 possible concentration...
        dfcons = dfcons.infer_objects()
        dfcons[dfcons < 10e-6] = 0

        pmf.dfprofiles_c = dfcons

    def read_base_contributions(self):
        """Read the "base" contributions result from the file: '_base.xlsx',
        sheet "Contributions", and add :

        - self.dfcontrib_b: base factors contribution

        """
        pmf = self.pmf

        if pmf.profiles is None:
            read_base_profiles()

        dfcontrib = pd.read_excel(
            self.basename+"_base.xlsx",
            sheet_name=['Contributions'],
            parse_dates=[1],
            header=None,
            engine=XLSX_ENGINE
        )["Contributions"]

        try:
            idx = dfcontrib.iloc[:, 0].str.contains("Factor Contributions").fillna(False)
            idx = idx[idx].index.tolist()
            if len(idx) > 1:
                dfcontrib = dfcontrib.iloc[idx[0]:idx[1], :]
            else:
                dfcontrib = dfcontrib.iloc[idx[0]+1:, :]
        except AttributeError:
            print("WARNING: no total PM reconstructed in the file")

        dfcontrib.dropna(axis=1, how="all", inplace=True)
        dfcontrib.dropna(how="all", inplace=True)
        dfcontrib.drop(columns=dfcontrib.columns[0], inplace=True)
        dfcontrib.columns = ["Date"] + pmf.profiles
        dfcontrib.set_index("Date", inplace=True)
        dfcontrib = dfcontrib[dfcontrib.index.notnull()]

        dfcontrib.replace({-999: np.nan}, inplace=True)

        pmf.dfcontrib_b = dfcontrib

    def read_constrained_contributions(self):
        """Read the "constrained" contributions result from the file: '_Constrained.xlsx',
        sheet "Contributions", and add :

        - self.dfcontrib_c: constrained factors contribution

        """
        pmf = self.pmf

        if pmf.profiles is None:
            read_base_profiles()

        dfcontrib = pd.read_excel(
            self.basename+"_Constrained.xlsx",
            sheet_name=['Contributions'],
            parse_dates=[1],
            header=None,
            engine=XLSX_ENGINE
        )["Contributions"]

        idx = dfcontrib.iloc[:, 0].str.contains("Factor Contributions").fillna(False)
        idx = idx[idx].index.tolist()

        if len(idx) > 1:
            dfcontrib = dfcontrib.iloc[idx[0]+1:idx[1], 1:]
        else:
            dfcontrib = dfcontrib.iloc[idx[0]+1:, 1:]

        nancolumns = dfcontrib.isna().all()
        if nancolumns.any():
            dfcontrib = dfcontrib.loc[:, :nancolumns.idxmax()]
        dfcontrib.dropna(axis=0, how="all", inplace=True)
        dfcontrib.dropna(axis=1, how="all", inplace=True)
        dfcontrib.columns = ["Date"] + pmf.profiles
        dfcontrib.replace({-999: np.nan}, inplace=True)
        dfcontrib.set_index("Date", inplace=True)
        dfcontrib = dfcontrib[dfcontrib.index.notnull()]

        pmf.dfcontrib_c = dfcontrib.infer_objects()

    def read_base_bootstrap(self):
        """Read the "base" bootstrap result from the file: '_boot.xlsx'
        and add :

        - self.dfBS_profile_b: all mapped profile
        - self.dfbootstrap_mapping_b: table of mapped profiles

        """
        pmf = self.pmf

        if pmf.profiles is None:
            read_base_profiles()

        dfprofile_boot = pd.read_excel(
            self.basename+"_boot.xlsx",
            sheet_name=['Profiles'],
            header=None,
            engine=XLSX_ENGINE
        )["Profiles"]

        dfbootstrap_mapping_b = dfprofile_boot.iloc[2:2+pmf.nprofiles, 0:pmf.nprofiles+2]
        dfbootstrap_mapping_b.columns = ["mapped"] + pmf.profiles + ["unmapped"]
        dfbootstrap_mapping_b.set_index("mapped", inplace=True)
        dfbootstrap_mapping_b.index = ["BF-"+f for f in pmf.profiles]

        idx = dfprofile_boot.iloc[:, 0].str.contains("Columns are:").fillna(False)
        idx = idx[idx].index.tolist()

        # 13 is the first column for BS result
        dfprofile_boot = dfprofile_boot.iloc[idx[0]+1:, 13:]
        df = self._split_df_by_nan(dfprofile_boot)

        df = pd.concat(df)
        df.index.names = ["specie", "profile"]
        # handle nonconvergente BS
        nBSconverged = dfbootstrap_mapping_b.sum(axis=1)[0]
        nBSnotconverged = len(df.columns)-1-nBSconverged
        if nBSnotconverged > 0:
            print("Warging: trying to exclude non-convergente BS")
            idxStrange = (df.loc[pmf.totalVar]>100)
            colStrange = df[idxStrange]\
                    .dropna(axis=1, how="all")\
                    .dropna(how="all")\
                    .columns
            print("BS eliminated:")
            print(df[colStrange])
            df = df.drop(colStrange, axis=1)

        # handle BS without totalVariable
        if pmf.totalVar:
            lowmass = (df.loc[pmf.totalVar, :] < 10**-3)
            if lowmass.any().any():
                print("Warning: BS with totalVar < 10**-3 encountered ({})".format(lowmass.any().sum()))
                df = df.loc[:, ~lowmass.any()]

        pmf.dfBS_profile_b = df
        pmf.dfbootstrap_mapping_b = dfbootstrap_mapping_b

    def read_constrained_bootstrap(self):
        """Read the "base" bootstrap result from the file: '_Gcon_profile_boot.xlsx'
        and add :

        - self.dfBS_profile_c: all mapped profile
        - self.dfbootstrap_mapping_c: table of mapped profiles

        """
        pmf = self.pmf

        if pmf.profiles is None:
            read_base_profiles()

        dfprofile_boot = pd.read_excel(
            self.basename+"_Gcon_profile_boot.xlsx",
            sheet_name=['Profiles'],
            header=None,
            engine=XLSX_ENGINE
        )["Profiles"]

        dfbootstrap_mapping_c = dfprofile_boot.iloc[2:2+pmf.nprofiles, 0:pmf.nprofiles+2]
        dfbootstrap_mapping_c.columns = ["mapped"] + pmf.profiles + ["unmapped"]
        dfbootstrap_mapping_c.set_index("mapped", inplace=True)
        dfbootstrap_mapping_c.index = ["BF-"+f for f in pmf.profiles]

        idx = dfprofile_boot.iloc[:, 0].str.contains("Columns are:").fillna(False)
        idx = idx[idx].index.tolist()
        # 13 is the first column for BS result
        dfprofile_boot = dfprofile_boot.iloc[idx[0]+1:, 13:]
        df = self._split_df_by_nan(dfprofile_boot)

        df = pd.concat(df)
        df.index.names = ["specie", "profile"]
        # handle nonconvergente BS
        nBSconverged = dfbootstrap_mapping_c.sum(axis=1)[0]
        nBSnotconverged = len(df.columns)-1-nBSconverged
        if nBSnotconverged > 0:
            print("Warging: trying to exclude non-convergente BS")
            idxStrange = (df.loc[pmf.totalVar]>100)
            colStrange = df[idxStrange]\
                    .dropna(axis=1, how="all")\
                    .dropna(how="all")\
                    .columns
            print("BS eliminated: ", colStrange)
            df = df.drop(colStrange, axis=1)

        # handle BS without totalVariable
        if pmf.totalVar:
            lowmass = (df.loc[pmf.totalVar, :] < 10**-3)
            if lowmass.any().any():
                print("Warning: BS with totalVar < 10**-3 encountered ({})".format(lowmass.any().sum()))
                df = df.loc[:, ~lowmass.any()]

        pmf.dfBS_profile_c = df
        pmf.dfbootstrap_mapping_c = dfbootstrap_mapping_c

    def read_base_uncertainties_summary(self):
        """Read the _BaseErrorEstimationSummary.xlsx file and add:

        - self.df_uncertainties_summary_b : uncertainties from BS, DISP and BS-DISP

        """
        pmf = self.pmf

        if pmf.profiles is None:
            read_base_profiles()

        if pmf.species is None:
            read_base_profiles()

        rawdf = pd.read_excel(
            self.basename+"_BaseErrorEstimationSummary.xlsx",
            sheet_name=["Error Estimation Summary"],
            header=None,
            engine=XLSX_ENGINE
            )["Error Estimation Summary"]
        rawdf = rawdf.dropna(axis=0, how="all").reset_index().drop("index", axis=1)


        # ==== DISP swap
        idx = rawdf.iloc[:, 1].str.contains("Swaps").fillna(False)
        if idx.sum() > 0:
            df = pd.DataFrame()
            df = rawdf.loc[idx, :]\
                    .dropna(axis=1)\
                    .iloc[:, 1:]\
                    .reset_index(drop=True)
            df.columns = pmf.profiles
            df.index = ["swap count"]

            pmf.df_disp_swap_b = df

        # ==== uncertainties summary
        # get only the correct rows
        idx = rawdf.iloc[:, 0].str.contains("Concentrations for").astype(bool)
        idx = rawdf.loc[idx]\
                .iloc[:, 0]\
                .dropna()\
                .index
        df = pd.DataFrame()
        df = rawdf.loc[idx[0]+1:idx[-1]+1+pmf.nspecies, :]
        idx = df.iloc[:, 0].str.contains("Specie|Concentration").astype(bool)
        df = df.drop(idx[idx].index)
        df = df.dropna(axis=0, how='all')
        df["profile"] = pd.np.repeat(pmf.profiles, len(pmf.species)).tolist()

        df.columns = ["specie", "Base run", 
                "BS 5th", "BS 25th", "BS median", "BS 75th", "BS 95th", "tmp1",
                "BS-DISP 5th", "BS-DISP average", "BS-DISP 95th", "tmp2",
                "DISP Min", "DISP average", "DISP Max",
                "profile"
                ]
        df["specie"] = pmf.species * len(pmf.profiles)
        df.set_index(["profile", "specie"], inplace=True)
        df.drop(["tmp1", "tmp2"], axis=1, inplace=True)

        pmf.df_uncertainties_summary_b = df.infer_objects()

    def read_constrained_uncertainties_summary(self):
        """Read the _ConstrainedErrorEstimationSummary.xlsx file and add :

        - self.df_uncertainties_summary_b : uncertainties from BS, DISP and BS-DISP

        """
        pmf = self.pmf

        if pmf.profiles is None:
            read_base_profiles()

        if pmf.species is None:
            read_base_profiles()

        rawdf = pd.read_excel(
            self.basename+"_ConstrainedErrorEstimationSummary.xlsx",
            sheet_name=["Constrained Error Est. Summary"],
            header=None,
            engine=XLSX_ENGINE
            )["Constrained Error Est. Summary"]
        rawdf = rawdf.dropna(axis=0, how="all").reset_index().drop("index", axis=1)

        # ==== DISP swap
        idx = rawdf.iloc[:, 1].str.contains("Swaps").fillna(False)
        if idx.sum() > 0:
            df = pd.DataFrame()
            df = rawdf.loc[idx, :]\
                    .dropna(axis=1)\
                    .iloc[:, 1:]\
                    .reset_index(drop=True)
            df.columns = pmf.profiles
            df.index = ["swap count"]

            pmf.df_disp_swap_c = df

        # ==== uncertainties summary
        # get only the correct rows
        idx = rawdf.iloc[:, 0].str.contains("Concentrations for").astype(bool)
        idx = rawdf.loc[idx]\
                .iloc[:, 0]\
                .dropna()\
                .index
        df = pd.DataFrame()
        df = rawdf.loc[idx[0]+1:idx[-1]+1+pmf.nspecies, :]
        idx = df.iloc[:, 0].str.contains("Specie|Concentration").astype(bool)
        df = df.drop(idx[idx].index)
        df = df.dropna(axis=0, how='all')
        df["profile"] = np.repeat(pmf.profiles, len(pmf.species)).tolist()

        df.columns = ["specie", "Constrained base run",
                "BS 5th", "BS median", "BS 95th", "tmp1",
                "BS-DISP 5th", "BS-DISP average", "BS-DISP 95th", "tmp2",
                "DISP Min", "DISP average", "DISP Max",
                "profile"
                ]
        df["specie"] = pmf.species * len(pmf.profiles)
        df.set_index(["profile", "specie"], inplace=True)
        df.drop(["tmp1", "tmp2"], axis=1, inplace=True)

        pmf.df_uncertainties_summary_c = df.infer_objects()


class SqlReader(BaseReader):
    """
    Accessor class for the PMF class with all reader methods.
    """

    def __init__(self, site, pmf, SQL_connection, SQL_table_names=None, SQL_program=None):
        super().__init__(site=site, pmf=pmf)

        self.con = SQL_connection
        
        # TODO: check if all table are set
        if SQL_table_names is None:
            SQL_table_names = {
                    "dfcontrib_b": "PMF_dfcontrib_b",
                    "dfcontrib_c": "PMF_dfcontrib_c",
                    "dfprofiles_b": "PMF_dfprofiles_b",
                    "dfprofiles_c": "PMF_dfprofiles_c",
                    "dfBS_profile_b": "PMF_dfBS_profile_b",
                    "dfBS_profile_c": "PMF_dfBS_profile_c",
                    "df_uncertainties_summary_b": "PMF_df_uncertainties_summary_b",
                    "df_uncertainties_summary_c": "PMF_df_uncertainties_summary_c",
                    "dfbootstrap_mapping_b": "PMF_dfbootstrap_mapping_b",
                    "dfbootstrap_mapping_c": "PMF_dfbootstrap_mapping_c",
                    "df_disp_swap_b": "PMF_df_disp_swap_b",
                    "df_disp_swap_c": "PMF_df_disp_swap_c"
                    }

        self.SQL_table_names = SQL_table_names
        self.SQL_program = SQL_program

    def _read_table(self, table, read_sql_kws={}):
        query = """
                SELECT * FROM {table} WHERE
                Station IS '{site}'
                """.format(
                        table=self.SQL_table_names[table],
                        site=self.site,
                        )
        if self.SQL_program:
            query += " AND Program IS '{program}'".format(program=self.SQL_program)

        df = pd.read_sql(query, con=self.con, **read_sql_kws)

        return df

    def read_base_profiles(self):
        """Read the "base" profiles result from database and add :

        - self.dfprofiles_b: base factors profile

        """
        df = self._read_table(table="dfprofiles_b")

        df = df.dropna(axis=1, how='all')
        df = df.set_index(["Specie"]).drop(["index", "Program", "Station"], axis=1)

        self.pmf.dfprofiles_b = df

        super().read_metadata()

    def read_constrained_profiles(self):
        """Read the "constrained" profiles result database and add :

        - self.dfprofiles_c: constrained factors profile

        """
        df = self._read_table(table="dfprofiles_c")

        df = df.dropna(axis=1, how='all')
        df = df.set_index(["Specie"]).drop(["index", "Program", "Station"], axis=1)

        self.pmf.dfprofiles_c = df


    def read_base_contributions(self):
        """Read the "base" contributions result from the file: '_base.xlsx',
        sheet "Contributions", and add :

        - self.dfcontrib_b: base factors contribution

        """
        df = self._read_table(table="dfcontrib_b", read_sql_kws=dict(parse_dates="Date"))
        df = df.dropna(axis=1, how='all')
        df = df.set_index(["Date"]).drop(["index", "Program", "Station"], axis=1)

        self.pmf.dfcontrib_b = df

    def read_constrained_contributions(self):
        """Read the "constrained" contributions result from the file: '_Constrained.xlsx',
        sheet "Contributions", and add :

        - self.dfcontrib_c: constrained factors contribution

        """
        df = self._read_table(table="dfcontrib_c", read_sql_kws=dict(parse_dates="Date"))
        df = df.dropna(axis=1, how='all')
        df = df.set_index(["Date"]).drop(["index", "Program", "Station"], axis=1)

        self.pmf.dfcontrib_c = df

    def read_base_bootstrap(self):
        """Read the "base" bootstrap result from the file: '_boot.xlsx'
        and add :

        - self.dfBS_profile_b: all mapped profile
        - self.dfbootstrap_mapping_b: table of mapped profiles

        """
        pass

    def read_constrained_bootstrap(self):
        """Read the "base" bootstrap result from the file: '_Gcon_profile_boot.xlsx'
        and add :

        - self.dfBS_profile_c: all mapped profile
        - self.dfbootstrap_mapping_c: table of mapped profiles

        """
        pass

    def read_base_uncertainties_summary(self):
        """Read the _BaseErrorEstimationSummary.xlsx file and add:

        - self.df_uncertainties_summary_b : uncertainties from BS, DISP and BS-DISP

        """
        pass

    def read_constrained_uncertainties_summary(self):
        """Read the _ConstrainedErrorEstimationSummary.xlsx file and add :

        - self.df_uncertainties_summary_b : uncertainties from BS, DISP and BS-DISP

        """
        pass
