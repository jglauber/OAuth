import hashlib
import secrets
from dataclasses import dataclass, asdict, field
from datetime import datetime
from argon2 import PasswordHasher, exceptions
import json
import psycopg2
from psycopg2._psycopg import connection, cursor
from getpass import getpass
import gc
from typing import TypeAlias, Optional
con: TypeAlias = connection
cur: TypeAlias = cursor
type Connection = tuple[con,cur]

class PostgreSqlHelper:
    """
    A class to handle interactions with the PostgreSQL backend.

    ...

    Attributes
    ----------
    database_name : str
        The name of the PostgreSQL database.
    host : str
        The database host address.
    pgpass : bool
        When set to True, the program will search for a .pgpass file (linux) in the /home/username directory.
        The file should contain a string in the format:

        ``host:port:db_name:username:password``

        By default, this parameter is set to False which forces the user to authenitcate via the command line.
    client_keys : list
        A list of the default columns to include in the table that stores client id and client secret.
    
    Methods
    -------
    connect()
        Establishes a connection to the db and returns a Connection tuple with con connection and cur cursor classes
    close(con,cur)
        Closes the db connection
    create(cur, con, table_name, column, data = None)
        Creates a table in the db
    add(cur, con, table_name, data)
        Adds to a table in the db
    query(self, cur, query)
        Query the connected db     
    """

    def __init__(self, database_name: str = 'clientdb', host: str = '127.0.0.1', pgpass: bool = False):
        """
        Parameters
        ----------
        database_name : str
            The name of the PostgreSQL database. *Default* "clientdb"
        host : str
            The host IP address for the PostgreSQL server. *Default* "127.0.0.1"
        pgpass : bool
            An option to use a .pgpass file in the user's home directory instead \
            of typing a password in the terminal. *Default* "False"
        """

        self.database_name = database_name
        self.host = host
        self.pgpass = pgpass
        self.client_keys = ['grant_type varchar', 'client_id varchar', 'client_secret varchar', 'resource varchar']       

    def connect(self) -> Connection:
        """
        Establishes a connection with the PostgreSQL server and returns a Connection class tuple.

        Returns
        -------
        tuple
            A connection tuple with connection (con) and cursor (cur) classes
        """

        if self.pgpass:
            try:
                con = psycopg2.connect(f"dbname={self.database_name} user=auth_client host={self.host}")
                cur = con.cursor()
                return (con,cur)
            except Exception as e:
                print(e)       
        else:
            print("Please provide postgreSQL authentication.")
            user = input("user: ")
            pw = getpass("password: ")
            try:
                con = psycopg2.connect(f"dbname={self.database_name} user={user} password={pw} host={self.host}")

                # remove pw binding
                del pw

                # if reference count reaches 0, collect garbage to free memory
                gc.collect()

                cur = con.cursor()
                return (con, cur)
            except psycopg2.OperationalError as e:
                if ("password authentication failed" or
                    "no password supplied" in str(e)):
                    print("Invalid username or password. Please try again.")
                    return self.connect()
                else:    
                    print(e)
        
    
    def close(self, con: connection, cur: cursor) -> Optional[bool]:
        """
        Closes the PostgreSQL database connection.

        Parameters
        ----------
        con : connection
            The connection class.
        cur : cursor
            The cursor class.

        Returns
        -------
        literal[True] | None
            True if closing the connection was successful. Otherwise\
            returns None.
        """

        cur.close()
        con.close()
        return True

    def create(self, cur: cursor, con: connection, table_name: str, column: list, data: list = None):
        """
        Creates a new table in the PostgreSQL database.

        Parameters
        ----------
        cur : cursor
            The cursor class
        con : connection
            The connection class
        table_name : str
            The name of the table to create in the PostgreSQL database.
        column : list
            A list of columns along with their datatypes.
            
            *Example* "['grant_type varchar', 'client_id varchar',\
            'client_secret varchar', 'resource varchar']"
        data : list
            A list of values to store in the table. The list represents\
            a row of data where each value is a column.
        """

        try:
            cur.execute(f"CREATE TABLE {table_name} ({', '.join(column)});")
            if data is not None:
                if len(data)>0:
                    cur.execute(f"INSERT INTO {table_name} VALUES ({", ".join(list(map(lambda x: '%s', data)))});", data)
            con.commit()
        except psycopg2.errors.DuplicateTable:
            con.rollback()

    def add(self, cur: cursor, con: connection, table_name: str, data):
        """
        Adds data to a table.

        Parameters
        ----------
        cur : cursor
            The cursor class
        con : connection
            The connection class
        table_name : str
            The name of the table to create in the PostgreSQL database.
        data : list
            A list of values to store in the table. The list represents\
            a row of data where each value is a column.
        """

        try:
            if len(data)>0:
                cur.execute(f"INSERT INTO {table_name} VALUES ({", ".join(list(map(lambda x: '%s', data)))});", data)
                con.commit()
        except psycopg2.errors.InFailedSqlTransaction:
            con.rollback()

    def remove(self, cur: cursor, con: connection, table_name: str, client_id: str):
        """
        Removes a client from the database.

        Parameters
        ----------
        cur : cursor
            The cursor class
        con : connection
            The connection class
        table_name : str
            The name of the table to create in the PostgreSQL database.
        client_id : str
            The client id to remove from the database.
        """

        try:
            cur.execute(f"DELETE FROM {table_name} WHERE client_id = '{client_id}';")
            con.commit()
        except psycopg2.errors.InFailedSqlTransaction:
            con.rollback()
        
    def query(self, cur: cursor, query: str) -> list:
        """
        Perform a SQL query of the database.

        Parameters
        ----------
        cur : cursor
            The cursor class
        query : str
            The SQL query to perform. *Note* query string must end with a semicolon.
        
        Returns
        -------
        list
            a list of all matching values.
        """
        
        cur.execute(query)
        db_list = cur.fetchall()
        return db_list
    
    def edit(self, cur: cursor, con: connection, client_id: str, edit_list: list[tuple]):
        """
        Edit a client in the database.

        Parameters
        ----------
        cur : cursor
            The cursor class
        con : connection
            The connection class
        client_id : str
            The client id to remove from the database.
        edit_list : list
            A list of tuples specifying the column name and value with which to replace\
            the existing values.
        """
        
        columns = ", ".join([item[0] for item in edit_list])
        values = ", ".join([f"'{item[1]}'" for item in edit_list])
        try:
            cur.execute(f"""UPDATE stored_tokens
            SET ({columns}) = ROW({values})
            WHERE client_id = '{client_id}';""")

            con.commit()
        except psycopg2.errors.InFailedSqlTransaction:
            con.rollback()


@dataclass
class Client:
    """
    A class to handle creation and maintenance of authorized clients.

    ...

    Attributes
    ----------
    name : str
        The name of the authorized user.
    grant_type : str
        The type of grant to allow. *Default* client_credentials
    resource : str
        The resource on the server that the client is allowed to access.

    Methods
    -------
    generate()
        Creates a new client with client id and client secret.
    store(db, host, table_name)
        Stores the client id, grant type, resource, and a salted and hashed client secret.
        In addition, this function deletes the stored client information from the class.

    verify(client_id: str, client_secret: str, grant_type: str,\
        resource: str, db, host, table_name, pgpass=False)
        Compares the stored credentials against the user provided credentials and returns True
        if all parameters match
    """

    name: str = ''
    grant_type: str = 'client_credentials'
    resource: str = ''
    _date: str = datetime.now().strftime('%d%m%Y_%H:%M:%S')
    _client: dict = field(default_factory=dict)

    def __repr__(self):
        return str(asdict(self))
    
    def generate(self):
        """
        Create a new client consisting of a grant_type, client_id\
        client_secret, and resource.

        Returns
        -------
        dict
            a client dictionary.
        """
        
        if self.name != '':
            client = {
                'grant_type': self.grant_type,
                'client_id': hashlib.md5(str(self).encode()).hexdigest(),
                'client_secret': 'PRIVATE-' + secrets.token_urlsafe(32),
                'resource': self.resource
            }
            self._client = client
            return client
        else:
            print('Please provide the name of the authorized user.')
            return None
           
    def store(self, db: str, host: str, table_name: str):
        """
        Store the client information in the PostgreSQL database and\
        delete any references from memory.

        Parameters
        ----------
        db : str
            The name of the database.
        host : str
            The host IP address of the PostgreSQL server.
        table_name : str
            The name of the table in the database.
        """

        # connect to db clientdb
        sqlh = PostgreSqlHelper(db, host)
        con, cur = sqlh.connect()

        # hash and salt client secret.
        client_values = list(self._client.values())
        ph = PasswordHasher()
        client_values[2] = ph.hash(client_values[2])

        # store in database
        sqlh.add(cur,con,table_name,client_values)

        # close database
        sqlh.close(con, cur)
        print(f"""The below credentials have been created.
Please store client secret in a secure location
as it will not be available again.
              
{json.dumps(self._client, indent=0)}
        """)

        # remove any references to the client secret
        del self._client
        gc.collect()
    
    def verify(self, client_id: str, 
               client_secret: str,
               grant_type: str,
               resource: str,
               db: str, host: str, table_name: str, pgpass=False) -> bool:
        """
        Verify that the provided client id, client secret, grant type and resource\
        exactly match the database.

        Parameters
        ----------
        client_id : str
            The client id to verify.
        grant_type : str
            The type of grant provided to the user.
        resource : str
            The resource on the server that the client is allowed to access.
        db : str
            The name of the database.
        host : str
            The host IP address of the PostgreSQL server.
        table_name : str
            The name of the table in the database.
        pgpass : bool
            When set to True, the program will search for a .pgpass file (linux) in the /home/username directory.
            The file should contain a string in the format:

            ``host:port:db_name:username:password``

            By default, this parameter is set to False which forces the user to authenitcate via the command line.
        
        Returns
        -------
        literal[True] | None
            True if all provided parameters match the database and False if any one does not exactly match.
        """
        
        # connect to db clientdb
        sqlh = PostgreSqlHelper(db, host, pgpass)
        con, cur = sqlh.connect()
        hash_client_secret = sqlh.query(cur,f"""SELECT client_secret
                                        FROM {table_name}
                                        WHERE client_id = '{client_id}';""")
        stored_grant_type = sqlh.query(cur,f"""SELECT grant_type
                                FROM {table_name}
                                WHERE client_id = '{client_id}';""")
        stored_resource = sqlh.query(cur,f"""SELECT resource
                              FROM {table_name}
                              WHERE client_id = '{client_id}';""")
        sqlh.close(con,cur)

        grant_flag = False
        resource_flag = False
        secret_flag = False

        if hash_client_secret == [] or stored_grant_type == [] or stored_resource == []:
            return False

        if grant_type == stored_grant_type[0][0]:
            grant_flag = True

        if resource == stored_resource[0][0]:
            resource_flag = True

        ph = PasswordHasher()
        try:
            secret_flag = ph.verify(hash_client_secret[0][0],client_secret)
        except exceptions.VerifyMismatchError:
            secret_flag = False
        
        if resource_flag and secret_flag and grant_flag:
            return True
        else:
            return False
    
def remove(db: str, host: str, table_name: str, client_id: str) -> Optional[bool]:
    """
    A function to remove a client from the database.

    Parameters
    ----------
    db : str
        The name of the database.
    host : str
        The host IP address of the PostgreSQL server.
    table_name : str
        The name of the table in the database.
    client_id : str
        The client to remove from the database.

    Returns
    -------
    literal[True] | None
        True if successful.
    """

    sqlh = PostgreSqlHelper(db, host)
    con, cur = sqlh.connect()
    sqlh.remove(cur, con, table_name, client_id)
    sqlh.close(con,cur)
    return True


def create_table(db: str, host: str, table_name: str) -> Optional[bool]:
    """
    A function to create a table in a database.

    Parameters
    ----------
    db : str
        The name of the database.
    host : str
        The host IP address of the PostgreSQL server.
    table_name : str
        The name of the table in the database.

    Returns
    -------
    literal[True] | None
        True if successful.
    """

    sqlh = PostgreSqlHelper(db, host)
    con, cur = sqlh.connect()
    sqlh.create(cur,con,table_name,sqlh.client_keys)
    sqlh.close(con,cur)
    return True

def edit_client(db: str, host: str, client_id: str, grant_type: str = None,
                resource: str = None, new_client_secret: bool = False) -> bool:
    """
    A function to edit a client in the database.

    Parameters
    ----------
    db : str
        The name of the PostgreSQL database.
    host : str
        The IP address of the database.
    client_id : str
        The client id associated with the client that will be edited.
    grant_type : str
        The type of credential grant.
    resource : str
        The name of the protected resource.
    new_client_secret : bool
        If True, this will create a new client secret for the client id.

    Returns
    -------
    literal[True] | None
        True if successful.

    """

    if grant_type is None and resource is None and not new_client_secret:
        return False
    else:
        edit_list = []
        print_list = []
        if grant_type is not None:
            edit_list.append(('grant_type',grant_type))
            print_list.append(('grant_type',grant_type))
        if resource is not None:
            edit_list.append(('resource',resource))
            print_list.append(('resource',resource))
        if new_client_secret:
            client_secret = 'PRIVATE-' + secrets.token_urlsafe(32)
            ph = PasswordHasher()
            client_secret_hash = ph.hash(client_secret)
            edit_list.append(('client_secret',client_secret_hash))
            print_list.append(('client_secret',client_secret)) 

        sqlh = PostgreSqlHelper(db,host)
        con, cur = sqlh.connect()
        sqlh.edit(cur, con, client_id, edit_list)

        print(f"The following items were updated for client_id {client_id}:")
        [print(f'\t{": ".join(item)}') for item in print_list]
        del print_list
        if 'client_secret' in locals():
            del client_secret
        gc.collect()
        return True


    
    

    