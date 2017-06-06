# coding: utf-8
import pandas as pd
import numpy as np
import sys
# Select examples where PII has been found (containing moustache {{)

args = sys.argv[1:]

def main(raw=args[0], classified=args[1], output=args[2]):
    '''
    Function to compare pre and post classified data to compile test cases
    for PII removal.

    Takes the following three arguments:
    raw: original survey results before classifiation
    classified: survey data after classifiaction and PII removal
    output: output of a new file facilitating comparison
    '''

    # Load pre-classified and raw datasets

    classified_df = pd.read_csv(classified)
    raw_df = pd.read_csv(raw)

    # Create mask for classified based on whether PII was identified

    classified_mask = np.column_stack([classified_df[col].str.contains(r"\{\{", na=False) for col in classified_df.select_dtypes(include=[object])])
    
    # Apply the mask to the classified data

    classified_masked = classified_df.loc[classified_mask.any(axis=1)]
    
    # Create a mask on raw based on respondent_ID
    
    raw_mask = raw_df.respondent_ID.isin(classified_df.respondent_ID)
    
    # Extract all comment columns

    comment_cols = [i for i in classified_df if 'comment' in i]
    comment_cols.append('respondent_ID')

    classified_filtered = classified_masked[comment_cols] 
    
    # Apply mask to raw

    raw_masked = raw_df.loc[raw_mask]
    raw_filtered = raw_masked[comment_cols]

    out = pd.merge(raw_filtered, classified_filtered, on='respondent_ID')

    out.to_csv(output, index=None)

if __name__ == '__main__':
    main()
