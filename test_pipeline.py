""" Test sklearn pipeline classes and functions
"""
# coding: utf-8

import pytest
import os
import pandas as pd
import numpy as np
import sqlalchemy as sa
from pipeline_functions import DataFrameConverter, DataFrameSelector, \
        CommentFeatureAdder, get_df, clean_PII, DateFeatureAdder, save_pickle
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import FeatureUnion
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelBinarizer

class TestPipelineFunctions(object):

    def setup_method(self):
           
        """
        Extract data from database 
        """
        
        ENGINE_STRING = "postgres://{}:{}@{}/{}".format(os.environ['PGUSER'], \
                os.environ['PGPASSWORD'], os.environ['PGHOST'], os.environ['PGDB'])
        ENGINE = sa.create_engine(ENGINE_STRING)

        self.df = pd.read_sql_query(
            (
                "select raw.respondent_id, start_date, end_date, full_url, "
                "cat_work_or_personal, comment_what_work, comment_why_you_came, "
                "cat_found_looking_for, cat_satisfaction, cat_anywhere_else_help, "
                "comment_where_for_help, comment_further_comments, vote "
                "from raw left join (select respondent_id,"
                "vote from priority where coders is not null) p on "
                "(raw.respondent_id = p.respondent_id) "
                "left join (select code_id, code from codes) c on "
                "(p.vote = c.code_id) limit 100"
            ),
            con = ENGINE
            )
               

#    def teardown_method(self):
#        """
#        Delete all the outputs created by the docker container
#        """
#
#        shutil.rmtree('tests/output')
#        shutil.rmtree('tests/experiments')
#
    def test_DataFrameSelector(self):
        """
        Test that DataFrameSelector returns columns as expected
        """
        
        features = ['respondent_id', 'start_date']

        test_pipeline = Pipeline([
            ('selector', DataFrameSelector(features))
            ])

        df = test_pipeline.fit_transform(self.df)

        assert len(df.columns) == len(features)
        assert set(df.columns) == set(features)
        assert isinstance(df, pd.core.frame.DataFrame) 

    def test_DataFrameConverter(self):
        """
        Test that DataFrameConverter returns an np.array
        """
        
        features = ['respondent_id', 'vote']

        test_pipeline = Pipeline([
            ('selector', DataFrameSelector(features)),
            ('converter', DataFrameConverter())
            ])

        df = test_pipeline.fit_transform(self.df)

        assert isinstance(df, np.ndarray)
        assert df.shape[1] == 2

    def test_DateFeatureAdder(self):
        """
        Test that DateFeatureAdder returns the requisite columns
        """
        
        features = ['start_date', 'end_date']

        test_pipeline = Pipeline([
            ('selector', DataFrameSelector(features)),
            ('date_features', DateFeatureAdder())
            ])

        df = test_pipeline.fit_transform(self.df)

        assert isinstance(df, np.ndarray)
        assert df.shape[1] == 8
        assert df.dtype == np.float64

    def test_CommentFeatureAdder(self):
        """
        Test that CommentFeatureAdder returns the requisite columns
        """
        
        features = ['comment_further_comments']

        test_pipeline = Pipeline([
            ('selector', DataFrameSelector(features)),
            ('comment_features', CommentFeatureAdder())
            ])

        df = test_pipeline.fit_transform(self.df)

        assert isinstance(df, np.ndarray)
