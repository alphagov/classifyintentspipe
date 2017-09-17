"""Create dataset for machine learning
"""
# coding: utf-8
import os
import pickle
import scrubadub
import sqlalchemy as sa
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import FeatureUnion
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelBinarizer
from pipeline_functions import DataFrameSelector, CommentFeatureAdder, \
        get_df, clean_PII, DateFeatureAdder
import logging
import logging.config

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('pipeline')

# Get database credentials from environment variables.

logger.info('Extracting data from %s:%s', os.environ['PGHOST'], os.environ['PGDB'])

ENGINE_STRING = "postgres://{}:{}@{}/{}".format(os.environ['PGUSER'], \
        os.environ['PGPASSWORD'], os.environ['PGHOST'], os.environ['PGDB'])
ENGINE = sa.create_engine(ENGINE_STRING)

# Extract raw data and join with majority vote.

df = get_df(engine=ENGINE)

logger.info('Database extraction complete')
logger.debug('Extracted %s rows and %s features from database', df.shape[0], df.shape[1])

df = clean_PII(df)

pkl_file = open('OFFICIAL_full_data.pkl', 'wb')
pickle.dump(df, pkl_file)
pkl_file.close()

# df column names have already been sanitized in a previous step (and in
# future will be loaded directly from the database, so it is not necessary
# to sanitize them here)

# For now drop url until better features can be added

X_id = df['respondent_id']
X = df.drop(['respondent_id','full_url','vote'], axis=1)

# One hot encoding on the ok variable

encoder = LabelBinarizer()
y = encoder.fit_transform(df['vote'])

# This creates a matrix of m * k where there are k classes.
# We then need to select a column to be the target, in this case

print('Running one hot encoding on target variable...')

#y = df_one_hot[:,4]

print('...done')

# Scale numeric features with the standard

scaler = StandardScaler()

# Create int features from date first...

date_features = [i for i in X.columns if 'date' in i]

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

comment_pipeline = Pipeline([
    ('selector', DataFrameSelector(comment_features)),
    ('str_length', CommentFeatureAdder()),
    ('minmax_scaler', MinMaxScaler())
    ])

full_pipeline = FeatureUnion(transformer_list=[
    ("date_pipeline", date_pipeline),
    ("comment_pipeline", comment_pipeline),
    ])

print('Running full_pipeline...')

transformed_dataset = full_pipeline.fit_transform(X)

#foo = full_pipeline.fit_transform(X)

print('...done')

# Save data out to pickle object

cleaned_data_file = open('cleaned_data.pkl', 'wb')
pickle.dump(transformed_dataset, cleaned_data_file)
pkl_file.close()
