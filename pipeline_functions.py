"""Functions and classes for running the sklearn_pipeline script"""

import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
import scrubadub
import logging
import logging.config

# Extract raw data and join with majority vote.

def get_df(engine):
    """
    Extract the full raw dataset from postgres db
    """

    logger = logging.getLogger('pipeline')
    logger.critical("sdhfhahfk")

    df = pd.read_sql_query(
        (
            "select raw.respondent_id, start_date, end_date, full_url, "
            "cat_work_or_personal, comment_what_work, comment_why_you_came, "
            "cat_found_looking_for, cat_satisfaction, cat_anywhere_else_help, "
            "comment_where_for_help, comment_further_comments, vote "
            "from raw left join (select respondent_id,"
            "vote from priority where coders is not null) p on "
            "(raw.respondent_id = p.respondent_id) "
            "left join (select code_id, code from codes) c on "
            "(p.vote = c.code_id) limit 100"
        ),
        con=engine
        )

    return df

# Clear PII from data

def clean_if(string):
    """
    Clean a text string of PII using scrubadub
    """

    scrubber = scrubadub.Scrubber()
    scrubber.remove_detector('name')
    scrubber.remove_detector('url')
    scrubber.remove_detector('vehicle')
    if isinstance(string, str):
        string = scrubber.clean(string)
    return(string)

# Identify comment columns, and apply clean_if to each

def clean_PII(df):
    """
    Run clean_if on a all columns containing comments.
    """
    comment_cols = [i for i in df.columns if 'comment' in i]

    print('Removing PII...')

    df.loc[:,comment_cols] = df.loc[:, comment_cols].applymap(clean_if)

    print('...done')

    return df

class DataFrameSelector(BaseEstimator, TransformerMixin):
    '''
    Select pandas df columns and return the columns

    Note that this returns a truncated pandas dataframe, not an
    np.array. This is because there are a number of string and
    datetime manipulations that are easier on pandas objects.
    '''
    def __init__(self, attribute_names):
        self.attribute_names = attribute_names
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        return X[self.attribute_names]

# Once datetime transformations have been made, we can convert the
# pd.dataframes into an np.array.

class DataFrameConverter(BaseEstimator, TransformerMixin):
    '''
    Convert pandas dataframes into numpy arrays
    '''
    def __init__(self):
        pass
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        return X.values

class DateFeatureAdder(BaseEstimator, TransformerMixin):
    '''
    Generate features from datetime columns

    Adds the following extra features onto the input dataset:
    * unix time
    * week day
    * day of year
    * day
    * week
    * month
    * year
    * Time taken to complete survey
    '''
    def __init__(self):
        pass
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        out = np.empty([X.shape[0], 0])
        X.is_copy = False # Squash slice warning from pandas
        X_cols = list(X)
        for i in X_cols:
            X[i] = pd.to_datetime(X[i])

            # Generate various features based on date and recast
            # the actual date into a unix time object.

            out = np.c_[out, (X[i].astype(np.int64)/1e6)] # Unix time
            out = np.c_[out, X[i].dt.weekday]
            out = np.c_[out, X[i].dt.dayofyear]
            out = np.c_[out, X[i].dt.day]
            out = np.c_[out, X[i].dt.week]
            out = np.c_[out, X[i].dt.month]
            out = np.c_[out, X[i].dt.year]

            # This is a bit inelegant, because it assumes that there are
            # only two date features, if the number of date features
            # changes, this will need to be changed.

            time1 = pd.to_datetime(X[X_cols[0]])
            for j in X_cols[1:]:
                time2 = pd.to_datetime(X[j])
                delta = np.absolute(time2 - time1)
                delta = delta.astype('int')
                delta = delta / 10e+8
                out = np.c_[out, delta]

            # Replace any nans with zero.
            # TODO: investigate what is causing the creation of these nans.
            # No nans are present in the pandas dataframe, so something in
            # this class creates them (six at last count).

            print('DateFeatureAdder converting', np.isnan(out).sum(), 'nans to zeros.')
            out = np.nan_to_num(out)
            return out

class CommentFeatureAdder(BaseEstimator, TransformerMixin):
    '''
    Add simple features derived from comment fields

    Adds the following features:
    * Character count
    TODO:
    - Count of capital letters as a ratio of character count
    - Count of exclamations as a ratio of character count
    '''

    def __init__(self):
        pass
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        #out = np.empty([X.shape[0],0])
        #X.is_copy=False # Squash slice warning from pandas
        # TODO: Need to iterate through the rows and columns here
        X_cols = list(X)
        for i in X_cols:

            X[i] = X[i].str.strip()
            X[i] = X[i].str.lower()
            X[i] = [len(i) for i in X[i]]
            # Character Count
            #out = np.c_[out, [len(i) for i in X[i]]
            # Caps ratio
            #out = np.c_[out, sum([i.isupper() for i in x])/len(x)]
            # Exclamation ratio
            #out = np.c_[out, sum([i == '!' for i in x]) / len(x)]
        return X
