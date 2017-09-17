"""Look up gov.uk url metadata using the content api

The department which owns the page on which the survey was triggered
along with other features is used as a feature in the machine learning
models. This information is extracted from a call to the GOV.UK
content api.

There are also a number of rules which we apply to the urls before they
are sent for lookup. This is because there is incomplete tagging of
of content in the content api, hence we can fill some fields
automatically before we run a api lookup.
"""
# coding: utf-8

from datetime import datetime
import re
import requests
import pandas as pd

class GovukUrls(object):
    """
    Clean and handle GOV.UK urls.
    """

    def __init__(self, urls):
        """
        Check that urls is a pd series.
        """

        self.urls = urls
        assert isinstance(self.urls, pd.core.series.Series)

        self.dedupurls = self.urls.drop_duplicates().dropna()

        # Instantiate list to be populated by clean method

        self.cleanurls = []
        self.urlsdf = pd.DataFrame()

    def clean(self):
        """
        Clean all urls in pandas series.
        """

        self.cleanurls = [clean_url(i) for i in self.dedupurls]

    def lookup(self):
        """
        Look up urls on GOV.UK content API
        """

        urldicts = [api_lookup(i) for i in self.cleanurls]
        self.urlsdf = pd.DataFrame.from_dict(urldicts)

def clean_url(url, query='\/?browse'):
    """
    Clean the incoming URL according to rules.
    """

    assert isinstance(url, str)

    url_dict = {
        'full_url' : None,
        'page' : None,
        'org0' : None,
        }

    url_dict['full_url'] = url
    url_dict['page'] = url

    # If FCO government/world/country page:
    # Strip back to /government/world and
    # set org to FCO

    if re.search('/government/world', url):

        url_dict['org0'] = 'Foreign & Commonwealth Office'
        url_dict['page'] = '/government/world'

    # If full_url starts with /guidance or /government:
    # and there is no org (i.e. not the above)
    # Set page to equal full_url.

    elif re.search(r'\/guidance|\/government', url):
        if 'org0' not in url:
            url_dict['page'] = url

    elif re.search(r'\/browse', url):
        url_dict['page'] = reg_match(query, url, 1)

        # Set section to be /browse/--this-bit--/

        url_dict['section0'] = reg_match(query, url, 2)

        # Otherwise:
        # Strip back to the top level

    elif (url == '/') or re.search('^/search.*', url) or re.search('^/help.*', url):
        url_dict['section0'] = 'site-nav'
        url_dict['section1'] = 'site-nav'

    elif re.search(r'^/contact.*', url):
        url_dict['section0'] = 'contact'
        url_dict['section1'] = 'contact'

    else:
        url_dict['page'] = '/' + reg_match(r'.*', url, 0)

    # If none of the above apply, then simply return the Urls
    # object with the same page

    return url_dict

def reg_match(regex, string, i):
    """
    Helper function for dealing with urls beginning /browse/...
    or similar. Utilised in clean_url()
    """

    regex = regex + '/'

    # r = uncompiled regex query
    # x = string to search
    # i = index of captive group (0 = all)

    p = re.compile(regex)
    s = p.search(string)

    if s:
        t = re.split(r'\/', string, maxsplit=3)
        if i == 0:
            found = t[1]
        if i == 1:
            found = '/' + t[1] + '/' + t[2]
        elif i == 2:
            found = t[2]
    else:
        found = string
    return found

def api_lookup(x):
    """
    Simple function to lookup a url on the GOV.UK content API
    Takes as an input the dictionary output by clean_url()
    """

    url = "https://www.gov.uk/api/search.json?filter_link[]=%s&fields=organisations&fields=mainstream_browse_pages" % x['page']
    
    #print('Looking up ' + url)
    
    try:
       
        # read JSON result into r
        r = requests.get(url)
        results = r.json()['results'][0]

        # Extract list of section and org data

        if 'organisations' in results:
            orgs = results['organisations']

        # Iterate through and populate the dictionary with org and section

            for i, j in enumerate(orgs):
                x['org' + str(i)] = j['title']

        if 'mainstream_browse_pages' in results:
            sections = results['mainstream_browse_pages']
        
            for i, j in enumerate(sections):
                x['section' + str(i)] = j
        
        x['lookup_date'] = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.now())
        x['status'] = r.status_code
        
        print("Looked up " + url + " returned status: " + str(x['status']))

    except Exception as e:
        print(e)
        print('Error looking up ' + url)
        print('Returning url dict without api lookup')
    
    return x
