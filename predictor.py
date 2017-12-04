# coding: utf-8
"""
Make predictions on intent surveys using a pre-trained model
"""

import pickle
import sys
import csv
import logging
import logging.config
from datetime import datetime
from os.path import basename, join, splitext
import pandas as pd
import numpy as np
import scrubadub
from classifyintents import survey

# Setup logging

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('classifypipe')
logger.info('Running predictor.py')

# Handle command line arguments

input_file = sys.argv[1]
model = sys.argv[2]

def clean_if(x):

    scrubber = scrubadub.Scrubber()
    scrubber.remove_detector('name')
    scrubber.remove_detector('url')
    if isinstance(x, str):
        x = scrubber.clean(x)
    return x


def main():

    # Instantiate an instance of the survey class.

    intent = survey()

    intent.load(input_file)


    # Clean the raw dataset. This creates a dataframe called `intent.data`.

    intent.clean_raw()

    # Apply cleaning rules to URLs and extract unique. These are stored in `intent.unique_pages`

    intent.clean_urls()

    # Now perform an API lookup on the cleaned URLS, and match them back into `intent.data`.
    # This is quite verbose!

    intent.api_lookup()

    # Remove obvious `none` cases where there is no free text.

    no_comments = ((intent.data['comment_further_comments'] == 'none') &
                   (intent.data['comment_where_for_help'] == 'none') &
                   (intent.data['comment_other_where_for_help'] == 'none') &
                   (intent.data['comment_why_you_came'] == 'none'))

    # Extract the respondent_id of the easily classified `nones`. These will be
    # used later for matching back in.

    easy_nones = intent.data.loc[no_comments, 'respondent_id'].astype(int)

    # Exclude easily classifed nones from intent.data, so we don't try to classify
    # on these, but create a copy first for later matching.

    intent.data_full = intent.data.copy()
    intent.data = intent.data.loc[~no_comments]

    # Now run the predictor class

    intent.predictor()

    # Import the saved model object from the training notebook

    exported_pipeline = pickle.load(open(model, 'rb'))

    # Run the prediction

    predicted_classes = exported_pipeline.predict(intent.cleaned)

    # Convert to a Series, name, and combine the respondent_id with the predicted code.
    # Then strip out those cases who are not coming out as OKs

    predicted_classes = pd.Series(
        predicted_classes,
        index=intent.cleaned.index,
        name='ada_code')

    predicted_classes = pd.concat(
        [intent.data['respondent_id'].astype('int'), predicted_classes],
        axis=1)

    predicted_classes = predicted_classes.loc[predicted_classes['ada_code'] == 1, 'respondent_id']

    # Combine the predicted OKs with the easily classified OKs.

    final_oks = pd.concat([easy_nones, predicted_classes], axis = 0)

    # Label the raw dataset with 'ok' and 'nones'

    intent.raw['target'] = ''
    intent.raw.loc[intent.raw['UserID'].isin(predicted_classes), 'target'] = 'ok'
    intent.raw.loc[intent.raw['UserID'].isin(easy_nones), 'target'] = 'none'

    print('Predicted classes:')
    print(intent.raw['target'].value_counts())

    # Standardise the column type for respondent ID, for merging

    intent.raw['UserID'] = intent.raw['UserID'].astype('int')
    intent.data['respondent_id'] = intent.data['respondent_id'].astype('int')

    # Run the pii_remover on all the free text fields

    comment_cols = [i for i in intent.raw.columns if 'comment' in i]
    intent.raw.loc[:,comment_cols] = intent.raw.loc[:, comment_cols].applymap(clean_if)

# Concatenate easy_nones with intent.data to ensure
    # Now merge the api lookup data into intent.raw

    urls = intent.data_full.loc[:, ['respondent_id', 'start_date',
        'end_date', 'full_url', 'page', 'section', 'org']]
    urls['respondent_id'] = urls['respondent_id'].astype('int')
    print(intent.raw.dtypes)
    print(urls.dtypes)

    output = intent.raw.merge(
        right=urls,
        how='left',
        left_on='UserID',
        right_on='respondent_id',
        indicator=True
     )

    print('Merge success:')
    print(output['_merge'].value_counts())

    # Remove the rather unhelpful US system dates, retaining only the clean ones.

    # No longer need to drop US dates as these do not exist!
    #output.drop(['respondent_id','start_date','end_date','full_url'],axis=1,inplace=True)

    # Save the file out

    output_file = join(
        'output_data/classified',
        splitext(basename(input_file))[0] + '_classified.csv'
    )

    url_file = join(
        'output_data/',
        splitext(basename(input_file))[0] + '_urls.csv'
        )

    print('***** Saving predictions to ', output_file, ' *****')

    output.to_csv(output_file, index=False)

    print('***** Saving url lookups to ', url_file, ' *****')

    urls1 = urls.loc[:, ['full_url', 'page', 'section', 'org']]
    urls1.drop_duplicates(inplace=True)

    # Convert all to string for regex to work!

    urls1 = urls1.applymap(str)
    urls1.replace(to_replace='^null$', value=np.nan, regex=True, inplace=True)
    urls1['lookup_date'] = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.now())

    # Use NONNUMERIC quotes to avoid issues with quotes in the csv itself

    urls1.to_csv(url_file, index=False, quoting=csv.QUOTE_NONNUMERIC)

if __name__ == '__main__':
    main()
