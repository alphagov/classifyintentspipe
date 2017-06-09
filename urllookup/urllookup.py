# coding: utf-8

import re, requests
import pandas as pd
from datetime import datetime

class govukurls(object):
    """
    Clean and handle GOV.UK urls.
    """

    def __init__(self, urls):
        """
        Check that x is a pd series.
        """

        self.urls = urls
        assert isinstance(self.urls, pd.core.series.Series)
        
        self.dedupurls = self.urls.drop_duplicates().dropna()

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

def clean_url(x, query='\/?browse'):
    """
    Clean the incoming URL according to rules.
    """

    assert isinstance(x, str)

    url = {
        'full_url' : None,
        'page' : None,
        'org0' : None,
        }

    url['full_url'] = x
    url['page'] = x

    # If FCO government/world/country page:
    # Strip back to /government/world and
    # set org to FCO
    
    if re.search('/government/world', x):

        url['org0'] = 'Foreign & Commonwealth Office'
        url['page'] = '/government/world'

    # If full_url starts with /guidance or /government:
    # and there is no org (i.e. not the above)
    # Set page to equal full_url                

    elif re.search('\/guidance|\/government', x):
        if 'org0' not in url:
            url['page'] = x  
    
    elif re.search('\/browse', x):
        url['page'] = reg_match(query, x, 1)
              
        # Set section to be /browse/--this-bit--/

        url['section0'] = reg_match(query, x, 2)
            
        # Otherwise:
        # Strip back to the top level
    
    elif ((x == '/') or re.search('^/search.*', x) or re.search('^/help.*', x)):
        url['section0'] = 'site-nav'
        url['section1'] = 'site-nav'

    elif re.search('^/contact.*', x):
        url['section0'] = 'contact'
        url['section1'] = 'contact'

    else:
        url['page'] = '/' + reg_match('.*', x, 0)
    
    # If none of the above apply, then simply return the Urls
    # object with the same page

    return url

def reg_match(r, x, i):

    """
    Helper function for dealing with urls beginning /browse/...
    or similar. Utilised in clean_url()
    """

    r = r + '/'
    
    # r = uncompiled regex query
    # x = string to search
    # i = index of captive group (0 = all)
    
    p = re.compile(r)
    s = p.search(x)
    
    if s:
        t = re.split('\/', x, maxsplit=3)
        if i == 0:
            found = t[1]
        if i == 1:
            found = '/' + t[1] + '/' + t[2]
        elif i == 2:
            found = t[2]
    else: 
        found = x
    return(found)

def api_lookup(x):
    
    '''
    Simple function to lookup a url on the GOV.UK content API
    Takes as an input the dictionary output by clean_url()
    '''

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
