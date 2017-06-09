import unittest
from urllookup import *
import pandas as pd

class TestCleanUrls(unittest.TestCase):

    def setUp(self):
        
        # Load in test data

        self.urls = [
                '/',
                '/government/world/turkey',
                '/government/publications/crown-commercial-service-customer-update-september-2016/crown-commercial-service-update-september-2016',
                '/guidance/guidance-for-driving-examiners-carrying-out-driving-tests-dt1/05-candidates-with-an-impairment',
                '/search/this-is/a-search/url',
                '/help/this/is/a/help/url',
                '/contact/this/is/a/contact/url'
                ]

        self.urls = self.urls * 2

        # Convert to pandas series (as expected by the class)

        self.urls = pd.Series(self.urls, name='full_url')
        
        self.urlsclass = govukurls(self.urls)

#    def tearDown(self):
#
    
    def test_govukurls_class_init(self):

        self.assertTrue(len(self.urlsclass.dedupurls) < len(self.urls))
        self.assertTrue(len(self.urlsclass.dedupurls) == len(self.urls) / 2)

    def test_clean_url(self):
    
        self.assertTrue(clean_url(self.urls[0]) == {'full_url': '/', 'page': '/', 'org0': None, 'section0': 'site-nav', 'section1': 'site-nav'})
        self.assertTrue(clean_url(self.urls[1]) == {'full_url': '/government/world/turkey', 'page': '/government/world', 'org0': 'Foreign & Commonwealth Office'})
        self.assertTrue(clean_url(self.urls[2]) == {'full_url': '/government/publications/crown-commercial-service-customer-update-september-2016/crown-commercial-service-update-september-2016', 'page': '/government/publications/crown-commercial-service-customer-update-september-2016/crown-commercial-service-update-september-2016', 'org0': None})
        self.assertTrue(clean_url(self.urls[3]) == {'full_url': '/guidance/guidance-for-driving-examiners-carrying-out-driving-tests-dt1/05-candidates-with-an-impairment', 'page': '/guidance/guidance-for-driving-examiners-carrying-out-driving-tests-dt1/05-candidates-with-an-impairment', 'org0': None})
        self.assertTrue(clean_url(self.urls[4]) == {'full_url': '/search/this-is/a-search/url', 'page': '/search/this-is/a-search/url', 'org0': None, 'section0': 'site-nav', 'section1': 'site-nav'})
        self.assertTrue(clean_url(self.urls[5]) == {'full_url': '/help/this/is/a/help/url', 'page': '/help/this/is/a/help/url', 'org0': None, 'section0': 'site-nav', 'section1': 'site-nav'})
        self.assertTrue(clean_url(self.urls[6]) == {'full_url': '/contact/this/is/a/contact/url', 'page': '/contact/this/is/a/contact/url', 'org0': None, 'section0': 'contact', 'section1': 'contact'})

    # TODO: Expand clean and lookup tests

    def test_clean_method(self):

        self.urlsclass.clean()
        self.assertTrue(isinstance(self.urlsclass.cleanurls, list))
        self.assertTrue(isinstance(self.urlsclass.cleanurls[0], dict))

    def test_lookup_method(self):
        
        self.urlsclass.clean()
        self.urlsclass.lookup()
        self.assertTrue(isinstance(self.urlsclass.urlsdf, pd.core.frame.DataFrame))
        self.assertTrue(self.urlsclass.urlsdf.loc[3,'org0'] == 'Driver and Vehicle Standards Agency')  

