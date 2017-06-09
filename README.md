[![GitHub tag](https://img.shields.io/github/tag/ukgovdatascience/classifyintentspipe.svg)](https://github.com/ukgovdatascience/classifyintentspipe/releases)

# Using machine learning to classify user comments on gov.uk

This repo contains code used to automate the classification of responses to the user intent survey conducted on GOV.UK.

The project is described in the [blog post](https://gdsdata.blog.gov.uk/2016/12/20/using-machine-learning-to-classify-user-comments-on-gov-uk/)

## Requirements

Nominally this application requires the following:

* Python 3.6.1
* gnu make (required for using makefile)

I would recommend setting up an environment using anaconda or venv before proceeding. `pip install -r requirements.txt` can then be used to install the required packages.
The only out of the ordinary requirement is the [classifyintents](https://github.com/ukgovdatascience/classifyintents) package, developed to handle the cleaning of the data; this is installed with the above step.

## Instructions

### Adding new data

At present new smartsurvey data is added to the postgres database in batches.
These data are downloaded as flat files from SmartSurvey, and must be cleaned to fit the format expected by the database. This is currently done with an R script:

```r
Rscript reformat.R input.csv output.csv`
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
At present a [fork](https://github.com/ukgovdatascience/scrubadub) of this package is used, though in future it would be preferable for the changes made in the fork to be pushed back to the original repo.
The fork can be installed using `pip install git+git://github.com/ukgovdatascience/scrubadub.git`

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

TODO: update below

To execute, run `make` from the root directory.

To upgrade to the latest version of classifyintents run:

```make init``` from the root.

More instructions are provided in the [makefile](makefile).

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
