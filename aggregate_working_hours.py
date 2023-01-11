#!/usr/bin/env python

import argparse
import datetime
import pathlib

import pandas as pandas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', '-d', type=pathlib.Path)

    args = parser.parse_args()

    all_data = get_all_data_from_directory(args.directory)
    print(all_data)

    dates = all_data.loc[:, "date_local"].unique()
    print(dates)

    min_max_local_dates = all_data.groupby("date_local").agg({"time_utc": ["min", "max"]})
    print(min_max_local_dates)


def get_all_data_from_directory(directory: pathlib.Path) -> pandas.DataFrame:
    dfs = [pandas.read_csv(filename, names=["time", "focus", "device"],
                           parse_dates=["time"])
           for
           filename in
           directory.glob("*.csv")]
    df = pandas.concat(dfs)
    df["time_utc"] = pandas.to_datetime(df["time"], utc=True)
    df["date_local"] = df["time"].map(lambda x: datetime.date(x.year, x.month, x.day))
    return df


if __name__ == "__main__":
    main()
