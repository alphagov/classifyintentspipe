""" Test sklearn pipeline classes and functions
"""
# coding: utf-8

import pytest
import os
import pandas as pd
import numpy as np
import sqlalchemy as sa
from pipeline_functions import DataFrameConverter, DataFrameSelector, \
        CommentFeatureAdder, DateFeatureAdder, save_pickle, \
        capsratio, exclratio, strlen, strlen_binned
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import FeatureUnion
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelBinarizer
from unittest import TestCase
#from psycopg2 import OperationalError, ProgrammingError

class TestPipelineFunctions(object):

    def setup_method(self):
           
        """
        Extract data from database 

        If the database is not available (e.g. when testing on travis)
        """
        

        try:

            ENGINE = sa.create_engine(os.environ['DATABASE_URL'])
            ENGINE.connect()
            ENGINE.execute('select * from raw limit 10;')

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
 
        # This is inelegant, but psycopg2 errors do not seem to be caught here
        # desite my better efforts.

        except:
            
            print('Unable to access postgres database. Loading from local file')
            self.df = pd.read_csv('python/tests/test_data.csv')
            pass


#    def teardown_method(self):
#        """
#        Delete all the outputs created by the docker container
#        """
#
#        shutil.rmtree('tests/output')
#        shutil.rmtree('tests/experiments')

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
        
        features = ['respondent_id', 'start_date']

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
            ('date_features', DateFeatureAdder('start_date', 'end_date'))
            ])

        df = test_pipeline.fit_transform(self.df)

        assert isinstance(df, np.ndarray)
        assert df.shape[1] == 8
        assert df.dtype == np.float64

    def test_CommentFeatureAdder(self):
        """
        Test that CommentFeatureAdder returns the requisite columns
        """
        
        features = ['comment_further_comments','comment_what_work']

        test_pipeline = Pipeline([
            ('selector', DataFrameSelector(features)),
            ('comment_features', CommentFeatureAdder())
            ])

        df = test_pipeline.fit_transform(self.df)

        assert isinstance(df, np.ndarray)
        assert df.shape[1] == 8

    def test_capsratio(self):
        """
        Test that capsratio() works as expected
        """
        
        assert capsratio('') == 0
        assert capsratio('The') == 0.3333
        assert capsratio(None) == 0

    def test_exclratio(self):
        """
        Test that exclratio() works as expected
        """

        assert exclratio('') == 0
        assert exclratio('Ag!') == 0.3333
        assert exclratio(None) == 0

    def test_strlen(self):
        """
        Test that strlen() works as expected
        """

        test_strings = pd.Series([None, 'a', 'ab', 'abc', 'abcd'])

        assert set(strlen(test_strings)) == set([0, 1, 2, 3, 4])
        assert strlen('') == 0

        #test_strings1 = pd.Series([np.nan, None])
        #case = TestCase()
        #case.assertCountEqual(strlen(test_strings1), [0, 0])
    
    def test_strlen_binned(self):
        """
        Test that strlen_binned() works as expected
        """

        test_strings = pd.Series([None, 'a', 'ab', 'abc', 'abcd'])
        string_length = strlen(test_strings)
        string_length_binned = strlen_binned(string_length, ratio=2,
                cutoff=1.5)
        case = TestCase()
        case.assertCountEqual(string_length_binned, [0., 1., 1., 2., 2.])
