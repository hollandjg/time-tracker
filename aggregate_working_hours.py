#!/usr/bin/env python

import argparse
import datetime
import pathlib

import pandas as pandas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', '-d', type=pathlib.Path)
    parser.add_argument('--live', '-l', action='store_true')

    args = parser.parse_args()

    all_data = get_all_data_from_directory(args.directory)

    if args.live:
        # We include an additional datapoint which is "now" and has no status
        all_data = pandas.concat(
            [all_data,
             pandas.DataFrame([(pandas.Timestamp.now("utc"), "", __name__)],
                              columns=["time", "focus", "device"])]
        )

    add_derived_columns(all_data)

    period_length = pandas.Timedelta(pandas.offsets.Minute(5))
    analysis_periods = pandas.date_range(all_data.loc[:, "date_local"].min(),
                                         all_data.loc[:, "date_local"].max() +
                                         pandas.DateOffset(days=1),
                                         freq=period_length, name="time_utc").to_series()

    analysis_df = pandas.DataFrame(index=analysis_periods, data={"duration": period_length})

    all_data_with_index = all_data.set_index("time_utc").sort_index()

    combined_data = pandas.merge_asof(analysis_df,
                                      all_data_with_index,
                                      left_index=True,
                                      right_index=True)

    print(combined_data.groupby(["date_local", "focus"]).agg({"duration": "sum"}))

    print(
        (
                combined_data.groupby(["focus", "year", "week"]).agg({"duration": "sum"}) /
                pandas.Timedelta(hours=1)
        )["duration"].map('{:,.1f}'.format)
    )

    print(combined_data
          .loc[combined_data["focus"] == "Work"]
          .pivot_table(values="duration", columns=["focus"], index=["year", "week"], aggfunc=sum))


def get_all_data_from_directory(directory: pathlib.Path) -> pandas.DataFrame:
    dfs = [pandas.read_csv(filename, names=["time", "focus", "device"],
                           parse_dates=["time"])
           for
           filename in
           directory.glob("*.csv")]
    df = pandas.concat(dfs)

    return df


def add_derived_columns(df):
    df["time_utc"] = pandas.to_datetime(df["time"], utc=True)
    df["date_local"] = df["time"].map(lambda x: datetime.date(x.year, x.month, x.day))
    df[['year', 'week', 'day']] = df["time_utc"].dt.isocalendar()


if __name__ == "__main__":
    main()
