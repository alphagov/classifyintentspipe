"""Create dataset for machine learning
"""
# coding: utf-8
import os
import pickle
import scrubadub
import pickle
import logging
import logging.config
import numpy as np
import sqlalchemy as sa
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import FeatureUnion
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelBinarizer
from pipeline_functions import DataFrameSelector, CommentFeatureAdder, \
        get_df, clean_PII, DateFeatureAdder, save_pickle
logging.config.fileConfig('logging.conf')
logger = logging.getLogger('pipeline')

# Get database credentials from environment variables.

ENGINE = sa.create_engine(os.environ['DATABASE_URL'])

logger.info('Extracting data from %s', ENGINE)

# Extract raw data and join with majority vote.

df = get_df(engine=ENGINE)

nrow = df.shape[0]

df = df.dropna(subset=['vote'])
df = df.loc[df.vote != 0, :]

logger.debug('Dropped %s of %s rows where there is no target (vote) or no comment (none)', nrow - df.shape[0], nrow)

logger.info('Database extraction complete')

#save_pickle(df, 'OFFICIAL_database_dump_dirty.pkl', 'Raw data extarcted from db')

df = clean_PII(df)

# Save PII cleaned data to pickle

save_pickle(df, '../data/OFFICIAL_db_dump_PII_removed.pkl', 'PII cleaned data')

# df column names have already been sanitized in a previous step (and in
# future will be loaded directly from the database, so it is not necessary
# to sanitize them here)

# Save index in

X_id = df['respondent_id']

# For now drop url until better url features can be added

drop_columns = ['respondent_id', 'full_url', 'vote']
logger.debug('Dropping columns %s', drop_columns)

X = df.drop(drop_columns, axis=1)

# One hot encoding on the ok variable

logger.debug('Encoding vote with one-hotencoding')

encoder = LabelBinarizer()
y_all = encoder.fit_transform(df['vote'])

# This creates a matrix of m * k where there are k classes.
# We then need to select a column to be the target, in this case

y_class = [i for i, x in enumerate(np.sum(y_all, axis=0)) if x == len(df.vote[df.vote==12])]

# Check that y_class codes for the ok (12) variable

logger.debug('Selecting class %s as target variable', y_class)

targets = y_all[:,y_class]

assert sum(targets) == len(df.vote[df.vote==12])

# Scale numeric features with the standard

scaler = StandardScaler()

# Create int features from date first...

date_features = [i for i in X.columns if 'date' in i]

logger.debug('Generating date features on %s', date_features)

date_pipeline = Pipeline([
    ('selector', DataFrameSelector(date_features)),
    ('date_features', DateFeatureAdder()),
    ('minmax_scaler', MinMaxScaler())
    ])

# At present, there are no numeric features, so exclude.

#numeric_features = list(X.select_dtypes(include=[int]))

#num_pipeline = Pipeline([
#    ('selector', DataFrameSelector(numeric_features)),
#    ('converter', DataFrameConverter()),
#    ('minmax_scaler', MinMaxScaler())
#    ])

comment_features = [i for i in X.columns if 'comment' in i]

logger.debug('Generating comment features on %s', comment_features)

comment_pipeline = Pipeline([
    ('selector', DataFrameSelector(comment_features)),
    ('str_length', CommentFeatureAdder()),
    ('minmax_scaler', MinMaxScaler())
    ])

full_pipeline = FeatureUnion(transformer_list=[
    ("date_pipeline", date_pipeline),
    ("comment_pipeline", comment_pipeline),
    ])

logger.debug('Running .fit_transform on full_pipeline')

transformed_dataset = full_pipeline.fit_transform(X)

logger.info('Transformed dataset shape is %s ', transformed_dataset.shape)

#foo = full_pipeline.fit_transform(X)

# Save data out to pickle object

save_pickle(transformed_dataset, '../data/transformed_data.pkl', 'Transformed data')
save_pickle(targets, '../data/targets.pkl', 'Targets')
