#!/usr/bin/env python

import argparse
import datetime
import pathlib
from enum import Enum

import pandas as pandas
import matplotlib.pyplot as plt


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

    df = pandas.merge_asof(analysis_df,
                           all_data_with_index,
                           left_index=True,
                           right_index=True)

    df_contracted_working_hours = get_contracted_working_hours()

    # Aggregation by week
    aggregated_contracted_hours = (df_contracted_working_hours
                                   .groupby(["year", "week"]).agg({"contracted": "sum"})
                                   )
    aggregated_worked_hours = (df
                               .loc[df["focus"] == "Work"]
                               .groupby(["focus", "year", "week"]).agg({"duration": "sum"})
                               / pandas.Timedelta(hours=1))

    aggregated_data = aggregated_worked_hours.merge(aggregated_contracted_hours, left_index=True,
                                                    right_index=True, how="outer")

    print(aggregated_data.applymap('{:,.1f}'.format))

    # Aggregation and cumulative sum over the year
    aggregated_worked_hours_by_day = (df
                                      .loc[df["focus"] == "Work"]
                                      .groupby(["date_local"]).agg({"duration": "sum"})
                                      )
    aggregated_data_by_day = aggregated_worked_hours_by_day.merge(df_contracted_working_hours,
                                                                  left_index=True,
                                                                  right_index=True, how="outer")
    dates_up_to_today = aggregated_data_by_day.index <= pandas.to_datetime('today')

    aggregated_data_by_day["worked"] = aggregated_data_by_day["duration"].fillna(
        pandas.Timedelta(0)) / pandas.Timedelta(hours=1)
    cumulative_aggregate_by_day = (aggregated_data_by_day[["contracted", "worked"]]
                                   .loc[dates_up_to_today]
                                   .cumsum()
                                   )

    cumulative_aggregate_by_day["surplus"] = cumulative_aggregate_by_day["worked"] - \
                                             cumulative_aggregate_by_day["contracted"]

    fig, (ax1, ax2) = plt.subplots(2, sharex=True, height_ratios=[3, 1])
    cumulative_aggregate_by_day[["contracted", "worked"]].plot(ylabel="hours", ax=ax1)
    cumulative_aggregate_by_day[["surplus"]].plot(ylabel="hours", ax=ax2)

    ax2.axhline(y=0, c='gray', linewidth=0.5)
    for ax in (ax1, ax2):
        ax.grid(True)

    fig.show()


def get_all_data_from_directory(directory: pathlib.Path) -> pandas.DataFrame:
    dfs = [pandas.read_csv(filename, names=["time", "focus", "device"],
                           parse_dates=["time"])
           for
           filename in
           directory.glob("*.csv")]
    df = pandas.concat(dfs)

    return df


def get_contracted_working_hours(working_hours_per_week=37.5, working_days_per_week=5):
    index = pandas.date_range("2023-01-01", periods=365, freq="D")
    df_non_work_days = pandas.DataFrame(index=index)
    series = index.to_series()

    NonWorkDays = Enum("NonWorkDays", ["WEEKEND", "VACATION", "HOLIDAY",
                                       "EMPLOYEE_APPRECIATION_DAY", "ANNUAL_LEAVE"])

    series_iso_dates = series.dt.isocalendar()
    df_non_work_days[NonWorkDays.WEEKEND] = series_iso_dates["day"] >= 6

    # Vacations (dates inclusive)
    vacations = [("christmas vacation 2022/2023", ("2022-12-23", "2023-01-08")),
                 ("christmas vacation 2023/2024", ("2023-12-27", "2024-01-05")), ]
    for label, (start_date, end_date) in vacations:
        df_non_work_days[(NonWorkDays.VACATION, label)] = (series >= start_date) & (
                series <= end_date)

    # Holidays (single dates)
    holidays = [
        ("New Year's Day", "2023-01-02"),
        ("Martin Luther King, Jr. Day", "2023-01-16"),
        ("Memorial Day", "2023-05-29"),
        ("Day After Memorial Day", "2023-05-30"),
        ("Juneteenth", "2023-06-19"),
        ("Independence Day", "2023-07-04"),
        ("Labor Day", "2023-09-04"),
        ("Indigenous Peoples Day", "2023-10-09"),
        ("Thanksgiving Day", "2023-11-23"),
        ("Day after Thanksgiving", "2023-11-24"),
        ("Christmas Eve", "2023-12-26"),
        ("Christmas Day", "2023-12-25"),
        ("New Year's Day", "2024-01-01"),
    ]
    for label, date in holidays:
        df_non_work_days[(NonWorkDays.HOLIDAY, label)] = (series == date)

    employee_appreciation_days = ["2023-02-20", "2023-08-11", "2024-02-19", "2024-08-09"]
    df_non_work_days[NonWorkDays.EMPLOYEE_APPRECIATION_DAY] = series.isin(
        employee_appreciation_days)

    annual_leave = [("leave", ("2023-01-27", "2023-01-27")),
                    ("sick day", ("2023-02-08", "2023-02-08")), ]
    for label, (start_date, end_date) in annual_leave:
        df_non_work_days[(NonWorkDays.ANNUAL_LEAVE, label)] = (series >= start_date) & (
                series <= end_date)

    working_days = ~df_non_work_days.any(axis="columns")

    working_hours_per_day = working_hours_per_week / working_days_per_week
    contracted_working_hours = pandas.DataFrame(
        index=index, data={"contracted": working_days * working_hours_per_day})
    contracted_working_hours[['year', 'week', 'day']] = series_iso_dates

    return contracted_working_hours


def add_derived_columns(df):
    df["time_utc"] = pandas.to_datetime(df["time"], utc=True)
    df["date_local"] = df["time"].map(lambda x: datetime.date(x.year, x.month, x.day))
    df[['year', 'week', 'day']] = df["time_utc"].dt.isocalendar()


if __name__ == "__main__":
    main()
