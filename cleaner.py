
# coding: utf-8

# Automatically classify OK surveys from GOV.UK intents survey - TRAINING

# Import modules. Note the classify module does most of the work, and can be found at <https://github.com/ukgovdatascience/classifyintents>.

from classifyintents import survey
import pandas as pd
import numpy as np
import sys, pickle

print('******************************')
print('***** Running cleaner.py *****')
print('******************************')

# Handle command-line inputs

input = sys.argv[1]
output = sys.argv[2]

def main():

    # Instantiate instance of the survey class.

    intent = survey()

    # Load the input data    

    intent.load(input)

    # Clean the data, creating the input.data dataframe    

    intent.clean_raw()
    print(intent.data.code1.value_counts())   
    # Apply rules to clean the urls in the dataset

    intent.clean_urls()

    # Now perform a lookup of the unique urls against the GOV.UK content API, and merge back into intent.data

    intent.api_lookup()
    print(intent.data.code1.value_counts())
    # Remove obvious cases where the survey can be classed as none. Some argument for including this step into a class method.

    if 'code1' in intent.data.columns:

        print('Classifying obvious "none" cases')
#        print('Prior to classification, there are ', str(sum(intent.data.code1 == 'none')), ' "none" cases in the data')
    
        no_comments = (intent.data['comment_further_comments'] == 'none') & (intent.data['comment_where_for_help'] == 'none') & (intent.data['comment_other_where_for_help'] == 'none') & (intent.data['comment_why_you_came'] == 'none')
        easy_nones = intent.data.loc[no_comments,'respondent_ID'].astype(int)
        print(intent.data.code1.value_counts())   
#        print('After classification, there are ',  str(sum(intent.data.code1 == 'none')), ' "none" cases in the data')

    else:
        pass

    # Create one-versus-all (OVA) coding of the code variable. Note that you can pass this a list of n > 1, and it will merge these classes together and perform what is effectively n-versus-all
    
    print('The data contain the following classes (which will be combined into 2 or more with the survey.trainer() method)')
    print(intent.data.code1.value_counts())
    
    print('The following features are included in the model:')
    print(intent.data.columns)

    print('***** Saving cleaned dataset to ', output, ' *****')    

    pickle.dump(intent.data, open(output,'wb'))
    
if __name__ == '__main__':
        main()
