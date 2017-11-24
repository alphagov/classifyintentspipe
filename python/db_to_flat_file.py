"""Write a database dump to csv and remove PII"""
# coding: utf-8

import os
import sys
import urllookup
import pandas as pd
import scrubadub
import sqlalchemy as sa

if len(sys.argv) > 1:
    OUT = sys.argv[1]
else: 
    OUT = 'database_dump.csv'

def main():

    # Get database credentials from environment variables.

    DATABASE_URL = os.environ['DATABASE_URL']
    ENGINE = sa.create_engine(DATABASE_URL)


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
            con=ENGINE
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
    
    urls = urllookup.GovukUrls(df['full_url'])
    urls.clean()
    urls.lookup()
    urls.urlsdf.to_csv('urls_' + OUT, index=False, na_rep='')
    
    # Merge urls into dataframe

    df = pd.merge(df, urls.urlsdf)
    df.to_csv(OUT, index=False, na_rep='')
