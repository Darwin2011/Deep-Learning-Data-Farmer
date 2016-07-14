#!/usr/bin/env python


import pandas


def reformat_dataframe(results_list, metric_order):
    df = pandas.DataFrame(results_list)
    cols = df.columns.tolist()
    cols = metric_order
    df = df[cols]
    return df

def generate_html(dataframe):
    return dataframe.to_html(index = False)

def generate_csv(dataframe):
    return dataframe.to_csv(index = False)

