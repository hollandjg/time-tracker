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
    # print(all_data)

    dates = all_data.loc[:, "date_local"].unique()
    # print(dates)

    analysis_periods = pandas.date_range(all_data.loc[:, "date_local"].min(),
                                         all_data.loc[:, "date_local"].max() + pandas.DateOffset(
                                             days=1),
                                         freq="5min", name="time_utc").to_series()

    # print(analysis_periods)

    analysis_durations = analysis_periods.diff()

    analysis_df = pandas.DataFrame(index=analysis_periods, data={"duration": analysis_durations})

    all_data_with_index = all_data.set_index("time_utc").sort_index()

    combined_data = pandas.merge_asof(analysis_df,
                                      all_data_with_index,
                                      left_index=True,
                                      right_index=True)

    print(combined_data.groupby(["date_local", "focus"]).agg({"duration": "sum"}))


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
