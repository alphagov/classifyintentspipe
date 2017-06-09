# coding: utf-8

import pandas as pd
import scrubadub
import sqlalchemy
import os
import sys
import re
import requests
from datetime import datetime
import urllookup

if len(sys.argv) > 1:
    out = sys.argv[1]
else: 
    out = 'database_dump.csv'


def main():

    engine_string = (f"postgres://{os.environ['PGUSER']}:"
            f"{os.environ['PGPASSWORD']}@{os.environ['PGHOST']}")

    engine = sqlalchemy.create_engine(engine_string)

    # Extract raw data and join with majority vote
    
    print('Extracting data from database...')

    df = pd.read_sql_query(
                (
                "select * from raw left join (select respondent_id,"
                "vote from priority where coders is not null) p on "
                "(raw.respondent_id = p.respondent_id) "
                "left join (select code_id, code from codes) c on "
                "(p.vote = c.code_id)"
                ),
                con=engine
                )

    print('...done')

    # Clear PII from data

    def clean_if(x):

        scrubber = scrubadub.Scrubber()
        scrubber.remove_detector('name')
        scrubber.remove_detector('url')
        scrubber.remove_detector('vehicle')
        if isinstance(x, str):
            x = scrubber.clean(x)
        return(x)

    # Identify comment columns, and apply clean_if to each

    comment_cols = [i for i in df.columns if 'comment' in i] 
    
    print('Removing PII...')

    df.loc[:,comment_cols] = df.loc[:,comment_cols].applymap(clean_if)

    print('...done')

    return df


if __name__ == "__main__":

    df = main()

    # Extract and lookup the urls using content API
    
    urls = urllookup.govukurls(df['full_url'])
    urls.clean()
    urls.lookup()
    urls.urlsdf.to_csv('urls_' + out, index=False, na_rep='')
    
    # Merge urls into dataframe

    df = pd.merge(df, urls.urlsdf)
    df.to_csv(out, index=False, na_rep='')
