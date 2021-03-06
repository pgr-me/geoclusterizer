# standard library imports
import datetime
import getpass
import os
from pathlib import Path
from string import Template
import time

# third-party imports
from doit.tools import config_changed, create_folder, run_once
from loguru import logger
import pandas as pd
import requests

# local imports
from settings import (
    DIRS,
    RAW_DIR,
    INTERIM_DIR,
    PROCESSED_DIR,
    MODELS_DIR,
    LOG_PATH,
    ROOT_DIR,
    ACS_SPAN,
    ACS_YEAR,
    RAW_ACS_DATA_DIR,
    RAW_SHAPEFILES_DIR,
    LOOKUPS_SRC,
    RANDOM_STATE,
    CE_CUTOFF,
    N_HIDDEN,
    N_SAMPLES,
    N_TRIALS,
    MAX_COMPONENTS
)
from src.acs import ACS

logger.add(LOG_PATH)


@logger.catch
def task_makedirs():
    """Make directories if they don't exist
    To run, cd into root dir and type `doit makedirs`.
    """
    for dir_ in DIRS:
        yield dict(name=dir_, actions=[(create_folder, [dir_])], uptodate=[run_once])


@logger.catch
def task_get_tiger_files():
    """Download and save TIGER shapefiles.
    To run, cd into root dir and type `doit get_tiger_files`.
    """

    def get_zips(url, dst):
        r = requests.get(url)
        with open(dst, "wb") as f:
            f.write(r.content)
        return True

    fips = """1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 44, 45, 46, 47, 48, 49, 50, 51, 53, 54, 55, 56, 60, 66, 69, 72, 78"""
    fips = [x.strip().zfill(2) for x in fips.split(",") if len(x) > 0]
    url_template = Template(
        "https://www2.census.gov/geo/tiger/TIGER${year}/TRACT/tl_${year}_${fip}_tract.zip"
    )
    for fip in fips:
        url = url_template.substitute(year=ACS_YEAR, fip=fip)
        fn = url.split("/")[-1]
        dst = RAW_SHAPEFILES_DIR / fn
        yield dict(
            name=dst.stem,
            actions=[(get_zips, [url, dst])],
            uptodate=[True],
            targets=[dst],
            clean=True,
        )


@logger.catch
def task_download_acs():
    """Download American Community Survey (ACS) data.
    This underlying code is from
    https://gist.githubusercontent.com/erikbern/89c5f44bd1354854a8954fa2df04453d/raw/efd7b7c31d781a5cae9849be60ab86967bf7d2ed/american_community_survey_example.py
    Author of that underlying code is Erik Bernhardsson | erikbern | https://gist.github.com/erikbern
    To run, cd into root dir and type `doit download_acs`.
    """
    acs = ACS(
        ACS_YEAR, ACS_SPAN, RAW_ACS_DATA_DIR, INTERIM_DIR, LOOKUPS_SRC, overwrite=False
    )
    return dict(
        actions=[acs.get_acs_metadata, acs.get_acs_data],
        task_dep=["makedirs"],
        verbosity=2,
        clean=True,
    )


@logger.catch
def task_parse_acs():
    """Parse downloaded ACS data.
    To run, cd into root dir and type `doit parse_acs`.
    """
    # TODO: Refactor so that parse_acs.py uses pydoit dependency manaagement framework
    cmd = "python parse_acs.py"
    # file_dep = f"{ACS_YEAR}_{ACS_SPAN}y_lookup.txt"
    return dict(actions=[cmd], verbosity=2, clean=True)


@logger.catch
def task_scale_and_impute_data():
    """Scale and impute missing data"""
    i = INTERIM_DIR / "acs__preprocessed_tables.pkl"  # input_src, aka `i`
    m = MODELS_DIR / "scaler_imputer.pkl"  # models_dst, aka `m`
    o = PROCESSED_DIR / "scaled_imputed_data.pkl"  # output_dst, aka `o`
    r = RANDOM_STATE  # random_state, aka `r`
    cmd = f"python scale_impute.py -i {i} -m {m} -o {o} -r {r}"
    return dict(actions=[cmd], file_dep=[i], targets=[o], verbosity=2, clean=True)


@logger.catch
def task_select_n_components():
    """Select number of components to use for dimensionality reduction"""
    cmd = f"python select_n_components.py"
    c = CE_CUTOFF
    d = N_HIDDEN
    i = PROCESSED_DIR / "scaled_imputed_data.pkl"
    n = N_SAMPLES
    o = PROCESSED_DIR / "selected_n_components.json"
    t = N_TRIALS
    cmd = f"python select_n_components.py -c {c} -d {d} -i {i} -n {n} -o {o} -t {t}"
    return dict(actions=[cmd], file_dep=[i], targets=[o], verbosity=2, clean=True)


# TODO: #4 Add report generation task that creates a report of model summary statistics


def task_cluster():
    """Train set of Gaussian Mixture models, select best one, and cluster tracts"""
    src = PROCESSED_DIR / "scaled_imputed_data.pkl"
    orig_src = INTERIM_DIR / "acs__preprocessed_tables.pkl"
    corex_obj_src = PROCESSED_DIR / "selected_n_components.pkl"
    gm_dst = MODELS_DIR / "gaussian_mixture.pkl"
    ce_dst = MODELS_DIR / "corex.pkl"
    labeled_dst = PROCESSED_DIR / "labeled.pkl"
    labeled_orig_dst = PROCESSED_DIR / "labeled_orig.pkl"
    cmd = f"python cluster.py"
    return dict(
        actions=[cmd],
        file_dep=[src, orig_src, corex_obj_src],
        targets=[gm_dst, ce_dst, labeled_dst, labeled_orig_dst],
        verbosity=2,
        clean=True,
    )
