# -*- coding: utf-8 -*-
"""


Created on Wed Sep 23 08:58:42 2015
@author: mxz20
"""

from __future__ import print_function
import pymysql as mdb
from nltk.corpus import wordnet
from app.glosbe_world_dict import query_world_dict


def query_dict(word, lang='English', diagnose_on=False,create_db_if_not_exist=False):
    '''To query dictionary of a given word from given language.
    For English, first query from wordnet & Webster dictionary from MySQL database, 
        then query nltk.wordnet.
    For other languages, use the glosbe API wrapped in glosbe_dict.
    
    Output -- word definition in one string
    '''
    
    lang=lang.lower()
    dict_name = lang+'_dict'
    
    # Connect to the database
    db = mdb.connect(user="root", host="localhost", db="dictionaries",  
                     charset='utf8',port=3307)
                         
    if lang=='english':
        # Query wordnet first since it's modern
        synsets = wordnet.synsets(word)
        if len(synsets) >0:
            definitions=[synset.definition() for synset in synsets]
            definition = ['{}. {}'.format(i+1, defi) for i,defi in enumerate(definitions)]
            definition = ';  '.join(definition) 
            
            definition_for_sql = definition.replace("'", "''")
            definition_for_sql = definition_for_sql.replace('"', '""')
            
            try:
                with db: #update to MySQL
                    cur = db.cursor()
                    #Check if entry already exists
                    cmd = '''SELECT word, definition FROM english_dict WHERE word='{}' ;'''.format(word)
                    cur.execute(cmd)  
                    query_results = cur.fetchone()       
                    if query_results==None:                                        
                        cmd = '''INSERT INTO english_dict VALUES ('{0}','{1}','Webster');'''.format(word,definition_for_sql)
                        cur.execute(cmd)
                        if diagnose_on:
                            print('Word={} successfully uploaded to MySQL database dictionaris into table {}'.format(word, lang+"_dict"))
            except:
                print('Problem uploading dictionary to MySQL')
                db.close()
                
        else: 
            # Query webster's dictionary 1913 version, which is already in MySQL 
            try:                   
                with db:
                    cur = db.cursor()
                    cmd = '''SELECT word, definition FROM english_dict WHERE word='{}' ;'''.format(word)
                    cur.execute(cmd)  
                    query_results = cur.fetchone()            
                    
                if query_results!=None: 
                    definition = query_results[1]
                else:
                    if diagnose_on:
                        print('query_dictionary: No entry found for {}'.format(word))
                    return None
            except:    
                print('Issue in MySQL query: \n cmd={}'.format(cmd))
                db.close()
                return None

    #---------------------------------------------                
    else: # Use globse's API for other languages
        # First check if exists in MySQL
        try:
            with db: #update to MySQL
                cur = db.cursor()
                # First check if entry exists
                cmd = '''SELECT word, definition FROM {0} WHERE word='{1}' ;'''.format(dict_name,word)
                cur.execute(cmd)  
                query_results = cur.fetchone() 
        except: 
            query_results=None
            pass
        
            
        if query_results!=None: 
            definition=query_results[1]
        else:  # either the search failed or word does not exsit
            # Now query glosbe_dict
            query=query_world_dict(origin='eng',dest=lang, phrase=word)
            if query==None:
                print('IP is Banned!!!')
                return None
            else:
                definition = query['definition']
            
            if definition=='': # no definition found for word
                if diagnose_on:
                    print('No definition found in glosbe')
                return None
            else:
                if diagnose_on:
                    print('Queried word: {} from globse_dict. Definition= {} '.format(word, definition) )
        
                # Upload to MySQL since it's not in there yet -- previsously determined
                if create_db_if_not_exist:
                    try: # check if database exsits
                        with db: #update to MySQL
                            cur = db.cursor()
                            cmd = '''select count(*) from {};'''.format(dict_name)
                            cur.execute(cmd)
                            query_results=cur.fetchall()
                    except: # table not exists, create
                        try:
                            with db: #update to MySQL
                                cur = db.cursor()
                                cmd='''create table if not exists {} (word varchar(50), definition text, source varchar(30)) DEFAULT CHARACTER set utf8 DEFAULT COLLATE utf8_general_ci ;'''.format(dict_name)
                                if diagnose_on:
                                    print('Successfully created table {}'.format(dict_name))
                                cur.execute(cmd)
                        except:
                            print('Problem with creating MySQL table {} '.format(dict_name))
                            return None
                    finally: # table exsits, upload data                   
                        try:
                            with db: #update to MySQL
                                cur = db.cursor()
                                cmd = '''INSERT INTO {2} VALUES ('{0}','{1}','glosbe');'''.format(word,definition, dict_name)    
                                #print(cmd)
                                cur.execute(cmd)
                                if diagnose_on:
                                    print('word={} successfully uploaded to MySQL database dictionaris into table {}'.format(word, dict_name))
            
                        except:
                            print('Problem uploading dictionary table {} to MySQL'.format(dict_name))
                            return None
                else:
                    try:
                        with db: #update to MySQL
                            cur = db.cursor()
                            cmd = '''INSERT INTO {2} VALUES ('{0}','{1}','glosbe');'''.format(word,definition, dict_name)    
                            #print(cmd)
                            cur.execute(cmd)
                            if diagnose_on:
                                print('word={} successfully uploaded to MySQL database dictionaris into table {}'.format(word, dict_name))
                    except:
                        print('Problem uploading dictionary table {} to MySQL'.format(dict_name))
                        return None
     
    db.close()            
    return definition
