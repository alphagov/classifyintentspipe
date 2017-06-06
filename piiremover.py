from re import sub, compile

ni = '[a-zA-Z]{2}(?:\s*\d\s*){6}[a-zA-Z]?'
phone = '(((\+44\s?\d{4}|\(?0\d{4}\)?)\s?\d{3}\s?\d{3})|((\+44\s?\d{3}|\(?0\d{3}\)?)\s?\d{3}\s?\d{4})|((\+44\s?\d{2}|\(?0\d{2}\)?)\s?\d{4}\s?\d{4}))(\s?\#(\d{4}|\d{3}))?'
vrp = '((?:[a-zA-Z]{2}\s?[0-9]{2}\s?[a-zA-Z]{3})|(?:[a-zA-Z]{3}\s?\d{4}))'
passport = '[0-9]{9,10}GBR[0-9]{7}[U,M,F]{1}[0-9]{7}'
date = '((?:\d{1,2})(?:rd|nd|th)?([\/\.\-\ ])((?:[0-9]{1,2})|(?:\D{3})|(?:January|February|March|April|May|June|July|August|September|October|November|December))(?:[\/\.\-\ ])\d{2,4})'
email = '([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'

def pii_remover(
        x, 
        ni = ni,
        phone = phone,
        vrp = vrp,
        passport = passport,
        date = date,
        email = email
        ):

    '''
    Find most common forms of PII and replace with [PII Removed]
    Order is important in terms of what is searched for first.
    Matches can conflict, but any remaining nmatched digits are
    replaced with X.

    Sources:

    Passport: http://regexlib.com/REDetails.aspx?regexp_id=2390
    Email: https://emailregex.com/
    
    Note: NHS and short passport numbers will be caught by credit cards regex
    '''
    
    if isinstance(x, str):

        if passport:
            x = sub(passport, '{{ PASSPORT NUMBER }}', x)
        
        if phone:
            x = sub(phone, '{{ PHONE NUMBER }}', x)

        if ni:
            x = sub(ni, '{{ NI NUMBER }}', x)

        if date:
            x = sub(date, '{{ DATE }}', x)
        
        if vrp:
            x = sub(vrp, '{{ VEHICLE REGISTRATION PLATE }}', x)

        if email:
            x = sub(email, '{{ EMAIL }}', x)

    return x
