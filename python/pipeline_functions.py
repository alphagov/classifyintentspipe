"""Functions and classes for running the feature_engineering script"""

import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
import scrubadub
import logging
import logging.config
import os
import pickle

# Extract raw data and join with majority vote.

logger = logging.getLogger('pipeline')

def save_pickle(obj, filename, description):
    '''
    Save an object to a pickle
    '''

    logger.info('Writing %s to %s', description, filename)

    # Remove file dump if exists
        
    if os.path.exists(filename):
        logger.warn('File %s already exists, deleting...', filename)
        try:
            os.remove(filename)
        except OSError:
            logger.error('Could not delete %s', filename)

    try:
        with open(filename, 'wb') as f:
            pickle.dump(obj, f)
            f.close()

        # Check that the new file was produced.

        assert os.path.isfile(filename), logger.error('%s was not produced', filename)

        logger.info('%s succesfully written to %s', description, filename)

    except AssertionError:

        logging.error('Failed to write to %s', filename)


def get_df(engine):
    """
    Extract the full raw dataset from postgres db
    """

    logger.debug('Starting query using %s', engine)

    df = pd.read_sql_query(
        (
            "select raw.respondent_id, start_date, end_date, full_url, "
            "cat_work_or_personal, comment_what_work, comment_why_you_came, "
            "cat_found_looking_for, cat_satisfaction, cat_anywhere_else_help, "
            "comment_where_for_help, comment_further_comments, concat_ws(', ', "
            "comment_why_you_came, comment_where_for_help, comment_further_comments)" 
            "as comment_combined, vote "
            "from raw left join (select respondent_id,"
            "vote from priority where coders is not null) p on "
            "(raw.respondent_id = p.respondent_id) "
            "left join (select code_id, code from codes) c on "
            "(p.vote = c.code_id)"
        ),
        con=engine
        )

    logger.debug('Extracted %s rows and %s features from database', df.shape[0], df.shape[1])
    
    return df

# Clear PII from data

def clean_if(string, remove_detectors=['name', 'url', 'vehicle']):
    """
    Clean a text string of PII using scrubadub
    """
    scrubber = scrubadub.Scrubber()
    
    for i in remove_detectors:
        scrubber.remove_detector(i)
    if isinstance(string, str):
        string = scrubber.clean(string)
    return(string)

# Identify comment columns, and apply clean_if to each

def clean_PII(df, comment_cols, *kwargs):
    """
    Run clean_if on a all columns containing comments.
    """

    logger.debug('Starting to remove PII from columns %s', comment_cols)

    df.loc[:,comment_cols] = df.loc[:, comment_cols].applymap(clean_if)

    logger.debug('Finished removing PII.')

    return df

class DataFrameSelector(BaseEstimator, TransformerMixin):
    '''
    Select pandas df columns and return the columns

    Note that this returns a truncated pandas dataframe, not an
    np.array. This is because there are a number of string and
    datetime manipulations that are easier on pandas objects
    than numpy arrays. Instead the DataFrame converter class
    is then used to convert into a DataFrame.
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
    * hour
    * Time taken to complete survey

    Needs to take start_data and end_date in the input list, but will
    drop end_date, using it only to generate time_delta.

    If none specified, then the delta will not be added.
    '''
    def __init__(self, start_date=None, end_date=None):
        self.end_date = end_date
        self.start_date = start_date
        logger.debug('self.start_date = %s', self.start_date)   
        logger.debug('self.end_date = %s', self.end_date)
    def fit(self, X, y=None):
        return self
    def transform(self, X):

        logger.debug('Running DateFeatureAdder.transform()')
        
        out = np.empty([X.shape[0], 0])
        
        X.is_copy = False # Squash slice warning from pandas
        X = X[['start_date','end_date']].apply(pd.to_datetime)
        
        out = np.c_[out, (X[self.start_date].astype(np.int64)/1e6)] # Unix time
        logger.debug('Converted %s to unixtime', self.start_date)
            
        out = np.c_[out, X[self.start_date].dt.weekday]
        logger.debug('Converted %s to weekday', self.start_date)
            
        out = np.c_[out, X[self.start_date].dt.dayofyear]
        logger.debug('Converted %s to dayofyear', self.start_date)
            
        out = np.c_[out, X[self.start_date].dt.day]
        logger.debug('Converted %s to day', self.start_date)
            
        out = np.c_[out, X[self.start_date].dt.week]
        logger.debug('Converted %s to week', self.start_date)
            
        out = np.c_[out, X[self.start_date].dt.month]
        logger.debug('Converted %s to month', self.start_date)
            
        out = np.c_[out, X[self.start_date].dt.hour]
        logger.debug('Converted %s to hour', self.start_date)

        if self.end_date:

            time2 = pd.to_datetime(X[self.end_date])
            logger.debug('time2 is %s', type(time2))
            time1 = pd.to_datetime(X[self.start_date])
            logger.debug('time1 is %s', type(time1))
            delta = np.absolute(time2 - time1)
            delta = delta.astype('int')
            delta = delta / 10e+8
            out = np.c_[out, delta]
        logger.debug('Calculated time delta by subtracting %s from %s', self.start_date, self.end_date)

        # Replace any nans with zero.
        # TODO: investigate what is causing the creation of these nans.
        # No nans are present in the pandas dataframe, so something in
        # this class creates them (six at last count).

        logger.debug('DateFeatureAdder outputs a %s', type(out))
        logger.debug('DateFeatureAdder outputs object of shape is %s', out.shape)
        logger.debug('DateFeatureAdder converting %s nans to zeros.', np.isnan(out).sum())
        out = np.nan_to_num(out)
        return out

class CommentFeatureAdder(BaseEstimator, TransformerMixin):
    '''
    Add simple features derived from comment fields

    Adds the following features:
    * Character count
    * Ratio of capital to lower case letters
    '''

    def __init__(self):
        pass
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        out = np.empty([X.shape[0],0])

        # Expecting a pandas dataframe here
        assert isinstance(X, pd.core.frame.DataFrame)

        X.is_copy=False # Squash slice warning from pandas
        X_cols = list(X)

        # Iterate through the columns, and create features which are appended
        # the np.ndarray out.

        for i in X_cols:

            # Operates on the individual series

            X[i] = X[i].str.strip()
            # Don't make lower case!!
            #X[i] = X[i].str.lower()
            
            logger.debug('Calculating string length on %s', i)
            string_length = strlen(X[i])
            
            logger.debug('Creating categorical var on %s', i)
            string_length_binned = strlen_binned(string_length)
            logger.debug('Created bins %s', pd.Series(string_length_binned).value_counts())
            out = np.c_[out, string_length, string_length_binned]
            
            # Caps ratio
            logger.debug('Calculating capsratio on %s', i)
            out = np.c_[out, [capsratio(j) for j in X[i]]]
            
            # Exclamation ratio
            out = np.c_[out, [exclratio(j) for j in X[i]]]
            logger.debug('Calculated exclsratio on %s', i)
        
        logger.debug('CommentFeatureAdder outputs object of %s', type(out))
        logger.debug('CommentFeatureAdder outputs object of shape %s', out.shape)
        logger.debug('CommentFeatureAdder converting %s nans to zeros.', np.isnan(out).sum())
        out = np.nan_to_num(out)
        assert out.shape == (X.shape[0], X.shape[1] * 4), 'CommentFeatureAdder returned wrong shape'
        return out


def strlen(x):
    '''
    Note that this will fail if passed np.nan rather than None
    for missing values.
    '''
    x[x.isnull()] = None
    out = [np.round(len(i), 4) if i is not None else 0 for i in x]
    return out

def capsratio(x):

    if isinstance(x, str) and (len(x) > 0):
        out = sum([i.isupper() for i in x]) / len(x)
        out = np.round(out, 4)
    else:
        out = 0
    return out

def exclratio(x):

    if isinstance(x, str) and (len(x) > 0):
        out = sum([j == '!' for j in x]) / len(x)
        out = np.round(out, 4)
    else:
        out = 0
    return out

def strlen_binned(string_length, ratio=0.1, cutoff=2.0):

    string_length_binned = np.ceil(np.array(string_length) / ratio)
    topbin = string_length_binned.max()
    string_length_binned[string_length_binned >= cutoff] = topbin

    return string_length_binned
