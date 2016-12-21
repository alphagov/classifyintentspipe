# coding: utf-8

# Create a training set from multiple disparately formatted, but classified data
# This was used to generate the first dataset used for training teh first model.

# Import modules. Note the classify module does most of the work, and can be found at <https://github.com/ukgovdatascience/classifyintents>.

print('******************************************')
print('***** Running create_training_set.py *****')
print('******************************************')

from classifyintents import survey
import pandas as pd
import numpy as np
import sys, pickle

# Instantiate instance of the survey class.

intent = survey()

# Load the raw data into the survey object. Note that this is the raw file downloaded from survey monkey, into which we will match the classifications that have already been completed.

intent.load('training_data/training_data_2016-10-27.csv')

# Clean the raw dataset. This creates a dataframe called `intent.raw`.

# Match in classifications from data that have already been classified using Respondent_ID. Load 

preclassified_03 = pd.read_csv('training_data/manually_classified/manually_classified_2016-03.csv')
preclassified_04 = pd.read_csv('training_data/manually_classified/manually_classified_2016-04.csv')
preclassified_06 = pd.read_csv('training_data/manually_classified/manually_classified_2016-06.csv')

# Extract the relevant columns ready to be matched into `intent.raw`

class03 = preclassified_03.loc[:,['RespondentID','code1']]
class04 = preclassified_04.loc[:,['Respondent ID','CODE']]
class06 = preclassified_06.loc[:,['RespondentID','CODE']]

# Rename columns to match the data in `intent.raw` before matching.

class_columns = ['RespondentID','code1']

class03.columns = class_columns
class04.columns = class_columns
class06.columns = class_columns

# Drop NAs on class06, and combine these together 

class06.dropna(how='any',inplace=True)

classes_combined = pd.concat([class03,class04,class06], axis = 0)

# Tidy the codes

classes_combined['code1'] = classes_combined['code1'].str.replace('\_','-')

# Drop `org` and `section` before merging the unclassified data with the classifications.

intent.raw = pd.merge(intent.raw, classes_combined, how='outer', on='RespondentID')

intent.raw.to_csv('training_data/manually_classified_training_data.csv')

print('Data combined. Check value counts of the classifications.')

print(intent.raw.code1.value_counts())

print('***** Classified training data output to training_data/manually_classified_training_data.csv *****')
