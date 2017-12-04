[![GitHub tag](https://img.shields.io/github/tag/ukgovdatascience/classifyintentspipe.svg)](https://github.com/ukgovdatascience/classifyintentspipe/releases)

# Using machine learning to classify user comments on gov.uk

This repo contains code used to automate the classification of responses to the user intent survey conducted on GOV.UK.

The project is described in the [blog post](https://gdsdata.blog.gov.uk/2016/12/20/using-machine-learning-to-classify-user-comments-on-gov-uk/)

## Requirements

Nominally this application requires the following:

* Python 3.6.2

I would recommend setting up an environment using anaconda or venv before proceeding. `pip install -r requirements.txt` can then be used to install the required packages.
The only out of the ordinary requirement is the [classifyintents](https://github.com/ukgovdatascience/classifyintents) package, developed to handle the cleaning of the data; this is installed with the above step.

## Instructions

## What's actually here:

* create_training_set.py: Creates a training set from multiple disparately formatted data that have been manually classified to create a single authoritative training set.

* cleaner.py: Conducts initial cleaning of a dataset prior to modelling or predicting.

```
python cleaner.py <input file (csv)> <output file (pkl)>
```

* trainer.py: Trains model using data output as a pickle object by cleaner.py.

```
python trainer.py <cleaned data (pkl)> <model object (pkl)>
```

* predictor.py: Makes predictions on newly aquired data downloaded from surveymonkey, using the model trained by trainer.py.

```
python predictor.py <input data (csv)> <model object (pkl)>
```

### Folders

Note that for privacy reasons, no data are stored in this repository. `.gitkeep` files are used to retain the following directory structure:

* input_data
    * Contains raw downloads from survey monkey prior to being classified using predictor.py
* models
    * Pickle objects of the trained models are stored here.
* output_data
    * Cleaned data produced by cleaner.py are stored here.
    * Predicted data which has been classified using the predicted script.
* training_data
    * Pre-classified training data is stored here.

### Assessing PII removal performance

To assess the performance of PII removal run the script pii_test_cases.py:

```
python pii_test_cases.py <input_data/raw.csv> <output_data/classified/classified.csv> <output.csv>
```

This will take all the cases in which PII was identified, and combine these with the uncleansed examples to facilitate comparison.
From this comparison, new test cases can be created to improve the performance of the PII removal.

# Next steps

This work is due to be revisited in 2017.
