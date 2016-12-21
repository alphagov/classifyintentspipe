# Classifyintentspipe
#
# This makefile completes all the steps required to train and implement
# a machine learning model on the GOV.UK intents survey data. There are 
# four steps:
#
#   1: Combine training data together:
#   At present manual classification of the survey responses is 
#   done in google sheets. These classes need to be combined with
#   the raw data before they can be used for training. This step
#   is completed by scripts/create_training_set.py. This is hard
#   coded, as teh step will be removed in future version.
#
#   2: Clean the data:
#   This step makes use of the classifyintents package to handle all the
#   cleaning and feature engineering producing  output_data/cleaned.pkl
#
#   3: Train the model:
#   This makes use of the trainer() method in the classifyintents 
#   package to prepare the data, then trains the model using sklearn,
#   saving the model to models/adaboost_test.pkl, and printing model
#   accuracy and some statistics to the console.
#
#   4: Make a prediction:
#   Taking new data (input_data/new_data.csv) this step applies the
#   model, saving a file to output_data/new_data_classified.csv, incorporating
#   some of the new features generated in step 2.

all : init clean train predict
combine : training_data/manually_classified_training_data.csv
clean : output_data/cleaned/cleaned.pkl 
train : models/adaboost_test.pkl
predict : output_data/classified/october.csv 

training_data/manually_classified_training_data.csv: scripts/create_training_set.py
	python scripts/create_training_set.py 

output_data/cleaned/cleaned.pkl : cleaner.py
	python cleaner.py training_data/training_data.csv output_data/cleaned/cleaned.pkl

models/adaboost_test.pkl : trainer.py clean
	python trainer.py output_data/cleaned/cleaned.pkl models/adaboost_test.pkl

output_data/classified/october.csv : predictor.py
	python predictor.py input_data/new_data.csv models/adaboost_model.pkl

.PHONY: init

init :
	pip install -r requirements.txt --upgrade
