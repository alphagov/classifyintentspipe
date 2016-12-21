
# coding: utf-8
# Automatically classify OK surveys from GOV.UK intents survey - TRAINING

# Import modules. Note the classify module does most of the work, and can be found at <https://github.com/ukgovdatascience/classifyintents>.

print('******************************')
print('***** Running trainer.py *****')
print('******************************')

from classifyintents import survey
import pandas as pd
import numpy as np
import sys, pickle
from sklearn.cross_validation import train_test_split
from sklearn.ensemble import AdaBoostClassifier, VotingClassifier
from sklearn.pipeline import make_pipeline, make_union
from sklearn.preprocessing import FunctionTransformer
from sklearn.metrics import confusion_matrix, classification_report

input = sys.argv[1]
model = sys.argv[2]

def main():

    # Instantiate instance of the survey class.

    intent = survey()
    intent.data = pickle.load(open(input,'rb'))
    print('Loading data from ', input)
    
    print(intent.data.code1.value_counts())

    print('Default behaviour is for one-versus-all using class "ok"')

    intent.trainer(['ok'])
    
    print('The following features are included in the model:')
    print(intent.cleaned.columns)
    # Train the machine learner
 
    # Load necessary packages. Note that `sklearn.cross_validation` is due to be deprecated in version 0.20 of `sklearn`. It will be necessary to update this code following that, if we want to stay up to date.

    # Create a training/test split on the data. Things that can be tweaked here are the test set proportion. An 80/20 training/test split seems pretty good.
    print(intent.cleaned.code1.value_counts())
    training_features, testing_features, training_classes, testing_classes = train_test_split(
        intent.cleaned.drop(['code1'], axis=1), 
        intent.cleaned['code1'],
        test_size=0.2,
        random_state=42)

    # Set up the pipeline using `AdaBoostClassifer`. Note that the choice of classifier came from using TPOT. However new tests should be done as new data becomes available.

    exported_pipeline = make_pipeline(
        AdaBoostClassifier(
        learning_rate = 0.1, 
        n_estimators = 500)
    )

    exported_pipeline.fit(training_features, training_classes)

    # Extract the results into a df to allow creation of a confusion matrix.
    results = exported_pipeline.predict(testing_features)

    results_df = pd.DataFrame(results,columns = ['adaboost_class'], index = testing_features.index)

    test_results = pd.concat([testing_features, testing_classes, results_df], axis = 1)

    print('Confusion matrix:')

    cm = confusion_matrix(
        test_results['code1'], 
        test_results['adaboost_class']
    )

    print(cm)

    print('Test set accuracy report:')

# Print the statistics for the test set accuracy. Note that this is the test set, hence n will seem smaller!

    print(
        classification_report(
        test_results['code1'], 
        test_results['adaboost_class']
          )
    )
    
    print('***** Saving model object you: ', model, ' *****')
    pickle.dump(exported_pipeline, open(model, 'wb')) 
    
if __name__ == '__main__':
        main()
