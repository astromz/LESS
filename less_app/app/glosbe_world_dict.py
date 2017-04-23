# -*- coding: utf-8 -*-
"""


Created on Tue Sep 22 17:19:09 2015
@author: mxz20
"""

from __future__ import print_function

def query_world_dict(origin='eng',dest='zho',phrase='consideration'):
    import json, requests
    from iso639 import languages

    if dest in ['jp','japan','japanese','jpn']: dest_code='jpn'
    elif dest in ['zh','chinese','china', 'zho']: dest_code='zho'
    elif dest in ['fr', 'france','french','frances','fra']: 
        dest_code='fra'
    else:
        dest=dest.lower()
        dest=dest.title()
        dest_code = languages.get(name=dest).part3


    url = 'https://glosbe.com/gapi/translate?'

    params = {
        'from':origin,
        'dest':dest_code,
        'phrase':phrase,
        'format':'json',  # format='xml'  for sentences
        'pretty':'true'
    }
    
    resp = requests.get(url=url, params=params)
    data = json.loads(resp.text)

    try:
        if data['result'] == 'ok':
            word = data['phrase']
            dictionary = ['{}. {}'.format(i+1,entry['phrase']['text']) for i, entry in enumerate(data['tuc']) if 'phrase' in entry]
            # English meaning
            meaning=['{}'.format(entry['meanings'][0]['text']) for i, entry in enumerate(data['tuc']) if 'meanings' in entry]
            meaning=set(meaning)
        dictionary = '; '.join(dictionary)
        return {'word':word, 'definition':dictionary, 'meaning':meaning}

    except:
        if data['result'] =='error':
            print(data['message'])
        return None
        
    

