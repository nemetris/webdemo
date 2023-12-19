# coding=utf-8
#===================================================================================================
#                                                                                    © nemetris GmbH
# Filename   cherrypy_demo.py
#
# Author     Thomas Rukwid
#
# Date       22.05.2023
#
#
# Notes:
# ------
# You need to add CherryPy to your Python installation:
# https://docs.cherrypy.dev/en/latest/install.html
#
# Database sample derived from:
# https://docs.cherrypy.dev/en/latest/tutorials.html#tutorial-9-data-is-all-my-life
#
# Importent:
# Unfortunately, SQLite in Python forbids us to share a connection between threads.
# Since CherryPy is a multi-threaded server, this would be an issue.
# This is the reason why we open and close a connection to the database on each call.
# This is clearly not really production friendly, and it is probably advisable to either
# use a more capable database engine or a higher level library, such as SQLAlchemy,
# to better support your application’s needs.
#
# nemetris has implemented his own higher level library to solve this issue.
# In productive environments we use PostgreSQL or Oracle as a database. SQLite is just something
# for fast mockups and tests.
#
# Check w2ui.com for the grid widget and how to use it.
# https://w2ui.com/web/docs/1.5/grid
#===================================================================================================
import cherrypy
import sys
import os
import json
import collections
import sqlite3

#===================================================================================================
# gobal database definition
#===================================================================================================
current_dir = os.path.dirname( os.path.abspath( __file__ ) )
DB_STRING   = os.path.join( current_dir, 'demo.db' )

class HelloWorld(object):
    #===============================================================================================
    # main index page --> http://localhost:4444
    #===============================================================================================
    @cherrypy.expose
    def index(self):
        html_content = """<H1>Hallo Welt!</H1>
                          <H2>weitere Seiten:</H2>
                           <ul>
                              <li><a href="/mypage">/mypage</a></li>
                              <li><a href="/formular">/formular</a></li>
                              <li><a href="/database">/database</a></li>
                              <li><a href="/jquery_ui_sample">/jquery UI Sample</a></li>
                              <li><a href="/ajax_sample">/AJAX Sample</a></li>
                          </ul>
                       """
        return html_content

    #===============================================================================================
    # /maypage --> http://localhost:4444/mypage
    #===============================================================================================
    @cherrypy.expose(alias="second_page")
    def mypage(self):
        return "My Page"

    #===============================================================================================
    # /formular --> http://localhost:4444/formular
    #===============================================================================================
    @cherrypy.expose
    def formular(self):
        with open( "formular.html", encoding='utf-8' ) as f:
            html = f.read()
        return html

    @cherrypy.expose
    def submit_form(self, **kwargs):
        print("form submit ...")
        print( kwargs )
        return f"form received ... {kwargs}"

    #===============================================================================================
    # /database --> http://localhost:4444/database
    #===============================================================================================
    @cherrypy.expose
    def database(self):
        with open( "database.html", encoding='utf-8' ) as f:
            html = f.read()
        return html

    #===============================================================================================
    # /jquery-ui_sample --> http://localhost:4444/jquery-ui_sample
    #===============================================================================================
    @cherrypy.expose
    def jquery_ui_sample(self):
        with open( "jquery-ui_sample.html", encoding='utf-8' ) as f:
            html = f.read()
        return html

    #===============================================================================================
    # /ajax_sample --> http://localhost:4444/ajax_sample
    #===============================================================================================
    @cherrypy.expose
    def ajax_sample(self):
        with open( "ajax_sample.html", encoding='utf-8' ) as f:
            html = f.read()
        return html


    @cherrypy.expose
    def get_table_data( self, **kwargs ):
        print("*** get_table_data ***")
        #===========================================================================================
        # w2ui gives us already a lot of parameters ... check the print
        # we just ignore them in our sample
        #===========================================================================================
        for arg, value in kwargs.items():
            print( "*****************************************************************************" )
            print( "Parameter: {0}, Value:{1}".format(arg, value) )
            print( "*****************************************************************************" )

        # hard coded in this simplified version of get_table_data
        table_name = "test"

        with sqlite3.connect(DB_STRING) as conn:
            curs = conn.cursor()
            #=======================================================================================
            # get the maximum of possible rows
            #=======================================================================================
            curs.execute( "select count(*) from {0}".format( table_name ) )
            data = curs.fetchone()
            total_rows = data[0]
            #=======================================================================================
            # get the requested results ...
            #=======================================================================================
            curs.execute(  "select rowid, {0}.* from {0}".format( table_name ) )
            #=======================================================================================
            # get all fields from the select ...
            #=======================================================================================
            columns = [column[0] for column in curs.description]
            data = curs.fetchall()
            records = []
            for i, row in enumerate(data):
                #===================================================================================
                # we need here an ordered dict so that we keep the column order of our selection ...
                # note that a dict is not ordered and the the result would be randomly ordered!
                #===================================================================================
                record = collections.OrderedDict( zip(columns, row) )
                #===================================================================================
                # we need to add the record ID for the w2ui grid to the result
                # ... we use here the sqlite rowid as an unique identifier since this will help us
                # with all other operations like delete or update a record ...
                #===================================================================================
                record["recid"] = row[0] #rowid
                records.append(record)
            #=======================================================================================
            # build the final w2ui grid structure
            #=======================================================================================
            result = {
                         "status":  "success",
                         "total":   total_rows,
                         "records": records
                     }
            return  json.dumps( result )

    @cherrypy.expose
    def get_table_data_all( self, **kwargs ):
        '''
        Data selection function for our grid.

        This function is called from the w2ui.grid in an ajax call. See http://w2ui.com/web/docs/grid
        for more details.
        '''
        #===========================================================================================
        # log all parameters
        #===========================================================================================
        for arg, value in kwargs.items():
            print( "Parameter: {0}, Value:{1}".format(arg, value) )
        kwargs = json.loads(kwargs["request"])
        #===========================================================================================
        # get the table name
        #===========================================================================================
        table_name = kwargs.get( 'table_name' )

        with sqlite3.connect(DB_STRING) as conn:
            curs = conn.cursor()
            #===========================================================================================
            # check if we do have some search filters --> WHERE clause for our select statement
            #===========================================================================================
            i = 0
            where_clause = ""
            for search in  kwargs.get( 'search', '' ):
                current_field    = search.get( 'field' )
                current_operator = search.get( 'operator' )
                current_value    = search.get( "value" )
                search_logic     = kwargs.get( 'searchLogic' )
                print( "Search operation: field( {0} ) - operator ( {1} ) - search logic ( {2} )".format( current_field, current_operator, search_logic ) )
                #=======================================================================================
                # get type of field ...
                # we need this so that we can create a correct SQL statement
                #=======================================================================================
                curs.execute( 'SELECT typeof({0}) FROM {1} LIMIT 1'.format( current_field, table_name ) )
                data = curs.fetchone()
                field_type = data[0].upper()
                print( "Search operation: field type( {0} ) ".format( field_type ) )
                #=======================================================================================
                # kind of operation depending on the field type...
                #=======================================================================================
                #=======================================================================================
                # text field operations ....
                #=======================================================================================
                if( field_type in ("TEXT", "BLOB") ):
                    #===================================================================================
                    # =
                    #===================================================================================
                    if( current_operator == "is" ):
                        sql_operation = " {0} = '{1}'".format( current_field, current_value )
                    #===================================================================================
                    # like abc%
                    #===================================================================================
                    elif( current_operator == "begins" ):
                        sql_operation = " {0} like '{1}%'".format( current_field, current_value )
                    #===================================================================================
                    # like %abc%
                    #===================================================================================
                    elif( current_operator == "contains" ):
                        sql_operation = " {0} like '%{1}%'".format( current_field, current_value )
                    #===================================================================================
                    # like %abc
                    #===================================================================================
                    elif( current_operator == "ends" ):
                        sql_operation = " {0} like '%{1}'".format( current_field, current_value )
                    #===================================================================================
                    # error
                    #===================================================================================
                    else:
                        message = "Fatal Error: Unknown search operator: {0} (TEXT, BLOB)".format( current_operator )
                        logger.critical( message )
                        result = {
                                    "status"  : "error",
                                    "message" : message
                                }
                        return  json.dumps(result)
                #=======================================================================================
                # numbers ...
                #=======================================================================================
                elif( field_type in ("INTEGER", "FLOAT", "REAL") ):
                    break
                    # not implemented yet

                #=======================================================================================
                # build where clause ...
                #=======================================================================================
                if( i == 0 ):
                    where_clause = ( "where " + sql_operation )
                else:
                    where_clause = ( where_clause + ' ' + search_logic + sql_operation )
                i += 1
            #===========================================================================================
            # check if we do have a sorting in the request --> ORDER BY for our select statement
            #===========================================================================================
            i = 0
            order_by = ""

            # not implemented yet

            #===========================================================================================
            # get the maximum of possible rows
            #===========================================================================================
            print("TTTTTTTTTTTTTTTTTTTTTTTTT")
            print( "select count(*) from {0} {1} {2}".format( table_name, where_clause, order_by ) )
            print("TTTTTTTTTTTTTTTTTTTTTTTTT")
            curs.execute( "select count(*) from {0} {1} {2}".format( table_name,
                                                                    where_clause,
                                                                    order_by ) )
            data = curs.fetchone()
            total_rows = data[0]
            #===========================================================================================
            # get the requested results ...
            #===========================================================================================
            curs.execute( "select rowid, {0}.* from {0} {1} {2} limit {3} offset {4}".format( table_name,
                                                                                            where_clause,
                                                                                            order_by,
                                                                                            kwargs.get('limit'),
                                                                                            kwargs.get('offset') ) )
            #===========================================================================================
            # get all fields from the select ...
            #===========================================================================================
            columns = [column[0] for column in curs.description]
            data = curs.fetchall()
            records = []
            for i, row in enumerate(data):
                #=======================================================================================
                # we need here an ordered dict so that we keep the column order of our selection ...
                # note that a dict is not ordered and the the result would be random ..
                #=======================================================================================
                record = collections.OrderedDict( zip(columns, row) )
                #=======================================================================================
                # we need to add the record ID for the w2ui grid to the result
                # ... we use here the sqlite rowid as an unique identifier since this will help us
                # with all other operations like delete or update a record ...
                #=======================================================================================
                record["recid"] = row[0] #rowid
                records.append(record)
            #===========================================================================================
            # build the final w2ui grid structure
            #===========================================================================================
            result = {
                        "status": "success",
                        "total": total_rows,
                        "records": records
                    }
            return  json.dumps( result )

    @cherrypy.expose
    def delete_table_data( self, **kwargs ):
        print("*** delete_table_data ***")
        #===========================================================================================
        # w2ui gives us already a lot of parameters ... check the print
        # we just ignore them in our sample
        #===========================================================================================
        for arg, value in kwargs.items():
            print( "*****************************************************************************" )
            print( "Parameter: {0}, Value:{1}".format(arg, value) )
            print( "*****************************************************************************" )

        #TODO implement the record deletion here like this:
        # kwargs = json.loads(kwargs["request"])
        # recids = kwargs.get("recid")
        # print( f"recids: {recids}" )
        # with sqlite3.connect(DB_STRING) as conn:
        #     curs = conn.cursor()
        #     for recid in recids:
        #         curs.execute(f"delete from test where rowid = {recid}")
        #     curs.execute("commit")
        # result = { "status": "success" }
        # return  json.dumps( result )

        print( "deletion is not implemented yet!!!!" )
        result = {
                    "status":  "error",
                    "message": "deletion is not implemented yet"
                 }
        return  json.dumps( result )


    @cherrypy.expose
    def save_table_data( self, **kwargs ):
        print("*** save_table_data ***")

        for arg, value in kwargs.items():
            print( "*****************************************************************************" )
            print( "Parameter: {0}, Value:{1}".format(arg, value) )
            print( "*****************************************************************************" )

        return dict( status="success" )

    @cherrypy.expose
    def string_reverse( self, string_to_reverse ):
        print( "*****************************************************************************" )
        print( "*** string_reverse ***" )
        print( "*****************************************************************************" )
        print( " String to reverse: {}".format( string_to_reverse ) )
        if ( string_to_reverse.strip() == "" ):
            print("bin hier ...")
            result_string = string_to_reverse[::-1]
            result = {
                        "status":  "bad",
                        "result":  "Error: empty string!"
                     }
        else:
            result_string = string_to_reverse[::-1]
            result = {
                        "status":  "good",
                        "result":  result_string
                     }
        print( " Result           : {}".format( result_string ) )
        print( "*****************************************************************************" )
        return  json.dumps( result )

#===================================================================================================
# helper function to setup our little test database
#===================================================================================================
def setup_database():
    '''
    creates a table in our demo database
    '''
    print("*** setup_database ***")

    with sqlite3.connect(DB_STRING) as conn:
        curs = conn.cursor()

        statement = '''CREATE TABLE IF NOT EXISTS test( fname  TEXT  not null,
                                                        lname  TEXT  not null,
                                                        email  TEXT  not null,
                                                        UNIQUE( fname, lname ) )'''
        curs.execute( statement )

        people = [ ("Thomas", "Rukwid", "thomas.rukwid@nemetris.com"),
                   ("Max", "Muster", "max.muster@gmail.com"),
                   ("John", "Doe", "john.doe@gmail.com"),
                   ("Jane", "Doe", "jane.doe@gmail.com") ]
        curs.executemany( 'INSERT OR IGNORE INTO test VALUES(?,?,?)', people )

        curs.execute( "SELECT * FROM test" )
        names = curs.fetchall()
        print("List of content in our test table")
        for name in names:
            print(name)


#===================================================================================================
# helper function to clean up the database at the program end
#===================================================================================================
def cleanup_database():
    '''
    Destroy the test table from the database on server shutdown.
    '''
    print("*** cleanup_database ***")

    with sqlite3.connect(DB_STRING) as conn:
        curs = conn.cursor()
        statement = '''DROP TABLE test'''
        curs.execute( statement )

#===================================================================================================
# create cherrypy app configuration ...
#===================================================================================================
#theme = "overcast"
#theme = "ui-darkness"
theme = "sunny"
#theme = "humanity"
current_dir = os.path.dirname( os.path.abspath(__file__) )
app_conf = {
            #=======================================================================================
            # jquery
            #=======================================================================================
            '/jquery.js':
            { 'tools.staticfile.on'         : True,
              'tools.staticfile.filename'   : os.path.join( current_dir, "public", "jquery", "jquery-3.6.0.min.js" )
            },
            #=======================================================================================
            # jquery UI
            #=======================================================================================
            '/jquery-ui.js':
            { 'tools.staticfile.on'         : True,
              'tools.staticfile.filename'   : os.path.join( current_dir, "public", "jquery-ui-1.12.1", "jquery-ui.min.js" )
            },
            '/jquery-ui.css':
            { 'tools.staticfile.on'         : True,
              'tools.staticfile.filename'   : os.path.join( current_dir, "public","jquery-ui-themes-1.12.1", "themes", theme, "jquery-ui.min.css" )
            },
            '/jquery-ui-theme.css':
            { 'tools.staticfile.on'         : True,
              'tools.staticfile.filename'   : os.path.join( current_dir, "public", "jquery-ui-themes-1.12.1", "themes", theme, "theme.css" )
            },
            # needed for the jquery ui images!
            '/images' :
            { 'tools.staticdir.on'          : True,
            'tools.staticdir.dir'           : os.path.join( current_dir, "public", "jquery-ui-themes-1.12.1", "themes", theme, "images" )
            },
            #=======================================================================================
            # W2UI
            #=======================================================================================
            '/w2ui.js':
            { 'tools.staticfile.on'         : True,
              'tools.staticfile.filename'   : os.path.join( current_dir, "public", "w2ui", "w2ui-1.5.js" )
            },
            '/w2ui.css':
            { 'tools.staticfile.on'         : True,
              'tools.staticfile.filename'   : os.path.join( current_dir, "public", "w2ui", "w2ui-1.5.css" )
            },
        }

#===================================================================================================
# set port to 4444
#===================================================================================================
cherrypy.config.update( { 'server.socket_port'  : 4444 } )

#===================================================================================================
# use compression for some MIME types ...
#===================================================================================================
cherrypy.config.update( { 'tools.gzip.on'         : True,
                          'tools.gzip.mime_types' : ['text/html', 'text/plain', 'text/css', 'text/javascript',
                                                     'image/jpeg', 'image/png', 'image/x-icon', 'image/gif',
                                                     'application/javascript', 'application/json'] } )
#===================================================================================================
# set cache settings
#===================================================================================================
cache_config = {
    'tools.caching.on'               : False,
    'tools.caching.delay '           : 0,
    'response.headers.Pragma'        : 'no-cache',
    'response.headers.Cache-Control' : 'private, max-age=0, no-store, no-cache, must-revalidate, post-check=0, pre-check=0',
    'response.headers.Expires'       : 'Thu, 01 Dec 1994 16:00:00 GMT',
}
cherrypy.config.update( cache_config )

cherrypy.engine.subscribe('start', setup_database)
cherrypy.engine.subscribe('stop', cleanup_database)
#===================================================================================================
# start Web-Server ...
#===================================================================================================
cherrypy.quickstart( HelloWorld(), config=app_conf )
