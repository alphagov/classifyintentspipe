# coding: utf-8

from sklearn.linear_model import LogisticRegression

from sklearn.utils.validation import column_or_1d

targets = column_or_1d(targets)

log_reg = LogisticRegression()
log_reg.fit(transformed_dataset, targets)

predictions = log_reg.predict(transformed_dataset)

from sklearn.metrics import f1_score

f1 = f1_score(targets, predictions)

from sklearn.metrics import classification_report
class_report = classification_report(targets, predictions)


from sklearn.model_selection import cross_val_score
scores = cross_val_score(log_reg, transformed_dataset, targets,
        scoring="f1", cv=20)

print(scores)
