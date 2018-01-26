[![GitHub tag](https://img.shields.io/github/tag/alphagov/classifyintentspipe.svg)](https://github.com/alphagov/classifyintentspipe/releases)

# Using machine learning to classify user comments on gov.uk

This repo contains code used to automate the classification of responses to the user intent survey conducted on GOV.UK.

The project is described in the [blog post](https://gdsdata.blog.gov.uk/2016/12/20/using-machine-learning-to-classify-user-comments-on-gov-uk/)

## Requirements

Nominally this application requires the following:

* Python 3.6.1
* gnu make (required for using makefile)
* [nbstripout](https://github.com/kynan/nbstripout)

I would recommend setting up an environment using anaconda or venv before proceeding. `pip install -r requirements.txt` can then be used to install the required packages.
The only out of the ordinary requirement is the [classifyintents](https://github.com/alphagov/classifyintents) package, developed to handle the cleaning of the data; this is installed with the above step.

### nbstripout installation

[nbstripout](https://github.com/kynan/nbstripout) is a tool which removes the saved data from within jupyter notebooks. Whilst the stateful nature of notebooks is useful, they are also a pain if you are dealing with potentially sensitive data. Note that nbstripout will stop the data from being seen by git, and thus impossible to push it. It won't actually remove the outputs on your local machine.

See the instruction [here](https://github.com/kynan/nbstripout) for how to install. You should install it as a git filter using `npstripout --install`. 

### xgboost installation

If you face problems installing the python `xgboost` package. The following workaround will allow it to be install in a specified virtual environment:

```
git clone git@github.com:dmlc/xgboost.git

cd xgboost

./build.sh

# Start appropriate virtualenv (if using virtualenv wrapper)

workon my_env

cd python-package

pip install -e .
```

## Instructions

### Selecting training examples

Selecting training examples is complicated by the following factors:

* When looking at the database, most sruveys in the OK class have already been classified by the model.
* It is therefore important to select only the surveys which have since been cooberated by a human classifier. For the OK class, this is considered enough as they are fairly unambiguous.
* For the other classes, the intention is to only use training examples which have been classied. 

An explanation of how the current training set has been built is explained in <R/notebooks/create_training_set.Rmd>.

### Adding new data

At present new smartsurvey data is added to the postgres database in batches.
These data are downloaded as flat files from SmartSurvey, and must be cleaned to fit the format expected by the database. This is currently done with an R script:

```bash
Rscript R/data_preparation.R input.csv output.csv

```

Data can then be imported into the postgres data base by creating a temporary table as. `respondent_id` is a primary key on raw, so no duplicates are allowed. duplicate rows from temp_raw must be dropped before the two tables can be joined.

```sql
create temp table temp_raw as select * from raw where false;
\copy temp_raw from '<file>' delimiter ',' csv;

insert into raw (select * from temp_raw where respondent_id not in (select respondent_id from raw))
```

### Url lookup

Data from smartsurvey contain just a url slug (`full_url`) of the gov.uk page on which the survey was triggered.
Additional features are developed from this slug by looking up the url on the GOV.UK content API. This returns a number of features based on the various organisations and sections to which the slug belongs.

For example: a lookup of `/government/publications/unique_pupil_numbers` will return the following new features:

|org0|org1|org2|org3|section0|section1|section2|section3|section4|section5|section6|
|---|---|---|---|---|---|---|---|---|---|---|
|Department for Education|||||||||||

In this instance, none of the fields are filled in with the exception of `org0`. This is relatively normal. These extremely sparse features are not likely to be useful at present, but may become more useful in future as more data is recorded in these fields. It may be prudent to reduce the number of sections and orgs used until then.

There is a problem with this general approach in that machinery of government (MOG) changes, and site restructuring can lead to changes in metadata held on a particular url. We want to capture the data as it was when the survey was completed, which means that we must cache the original lookup on the content API. Future visitors may find that a page now belongs to a new department, or a new section, and so this data must also be captured.

The solution is to lookup the url metadata from the content API when it is added to the database. A check is then made to see whether any changes have occured since the last lookup, and if they have, then any duplicate rows are dropped. If changes have occured, these are stored in the database with a new `lookup_date`. This check can be achieved in SQL with:

```sql
delete from urls
where url_id in (
    select url_id from (
        select url_id, row_number() 
        over (partition by full_url, org0, org1, org2, org3, 
            section0, section1, section2, section3, section4, section5, section6 
            order by url_id) as rnum
        from urls) t
    where t.rnum > 1);
```

When using metadata to create features from the url table, the entry in the url table with the `lookup_date` closest to the survey `start_date` should be used. This can be done with the following query:

```sql

with fulljoin as (
    select * from raw 
    left join urls 
    on (raw.full_url=urls.full_url) 
) 

select * from fulljoin
where url_id in (
    select url_id from (
        select url_id, start_date, lookup_date, row_number()
        over (partition by respondent_id, full_url 
            order by lookup_date - start_date) as rnum
        from urls) t
    where t.rnum < 2);

```

The url lookup itself is handled by the urlookup/ module in the following way:

```python
# Assuming a pandas dataframe df with a column full_url containing the url slug...

from urllookup import *
import sqlalchemy as sa

engine = sa.create_engine('postgres://username:password@host/db')
df = pd.read_sql_table('raw', con=engine)

# Instantiate the class

foo = govukurls(df['full_url'])

# The deduplicated urls can then be called with foo.dedupurls

# Apply cleaning rules to foo.dedupurls creating foo.cleanurls

foo.clean()

# Lookup the urls using the gov.uk content API to foo.clean

foo.lookup()

# This creates a pandas dataframe called foo.urlsdf which can be merged into the dataframe in python using:

pd.merge(df, foo.urldf)

```

### Removing Personal Identifying Information (PII)

#### scrubadud

PII is removed from the free text of the surveys by using the [scrubadub](https://github.com/datascopeanalytics/scrubadub) package.
At present a [fork](https://github.com/alphagov/scrubadub) of this package is used, though in future it would be preferable for the changes made in the fork to be pushed back to the original repo.
The fork can be installed using `pip install git+git://github.com/alphagov/scrubadub.git`

PII can be removed with the following:

```python

# Set up a custom scrubber. Names, urls, and vehicle detection has proven to
# be too severe under most circumstances, so these are not used. The name 
# scrubAber has a hard time differentiating between names and other proper 
# nouns. Urls are useful in the survey free text, and do not represent PII, 
# whilst vehicle registration plates are somewhat difficult to identify 
# because of their form.

def clean_if(x):

    scrubber = scrubadub.Scrubber()
    scrubber.remove_detector('name')
    scrubber.remove_detector('url')
    scrubber.remove_detector('vehicle')
    if isinstance(x, str):
        x = scrubber.clean(x)
    return(x)

# Identify comment columns, and apply clean_if to each

comment_cols = [i for i in df.columns if 'comment' in i] 

# Apply the scrubber over all comment columns.

df.loc[:,comment_cols] = df.loc[:,comment_cols].applymap(clean_if)

```

#### Assessing PII removal performance

To assess the performance of PII removal run the script pii_test_cases.py:

```
python pii_test_cases.py <input_data/raw.csv> <output_data/classified/classified.csv> <output.csv>
```

This will take all the cases in which PII was identified, and combine these with the uncleansed examples to facilitate comparison.
From this comparison, new test cases can be created to improve the performance of the PII removal.



