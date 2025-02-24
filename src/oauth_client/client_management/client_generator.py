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
from typing import TypeAlias


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
            host:port:db_name:username:password
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
    def __init__(self, database_name: str, host: str, pgpass: bool = False):
        self.database_name = database_name
        self.host = host
        self.pgpass = pgpass
        self.client_keys = ['grant_type varchar', 'client_id varchar', 'client_secret varchar', 'resource varchar']       

    con: TypeAlias = connection
    cur: TypeAlias = cursor
    type Connection = tuple[con,cur]

    def connect(self) -> Connection:
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
        
    
    def close(self, con: connection, cur: cursor) -> True:
        cur.close()
        con.close()
        return True

    def create(self, cur: cursor, con: connection, table_name: str, column: list, data: list = None):
        try:
            cur.execute(f"CREATE TABLE {table_name} ({', '.join(column)});")
            if data is not None:
                if len(data)>0:
                    cur.execute(f"INSERT INTO {table_name} VALUES ({", ".join(list(map(lambda x: '%s', data)))});", data)
            con.commit()
        except psycopg2.errors.DuplicateTable:
            con.rollback()

    def add(self, cur: cursor, con: connection, table_name: str, data):
        try:
            if len(data)>0:
                cur.execute(f"INSERT INTO {table_name} VALUES ({", ".join(list(map(lambda x: '%s', data)))});", data)
                con.commit()
        except psycopg2.errors.InFailedSqlTransaction:
            con.rollback()

    def remove(self, cur: cursor, con: connection, table_name: str, client_id: str):
        try:
            cur.execute(f"DELETE FROM {table_name} WHERE client_id = '{client_id}';")
            con.commit()
        except psycopg2.errors.InFailedSqlTransaction:
            con.rollback()
        
    def query(self, cur, query) -> list:
        cur.execute(query)
        db_list = cur.fetchall()
        return db_list
    
    def edit(self, cur: cursor, con: connection, client_id: str, edit_list: list):
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
    name: str = ''
    grant_type: str = ''
    resource: str = ''
    _date: str = datetime.now().strftime('%d%m%Y_%H:%M:%S')
    _client: dict = field(default_factory=dict)

    def __repr__(self):
        return str(asdict(self))
    
    def generate(self):
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
           
    def store(self, db, host, table_name):
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
    
    def verify(self, client_id: str, 
               client_secret: str,
               grant_type: str,
               resource: str,
               db, host, table_name, pgpass=False) -> bool:
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
    
def remove(db: str, host: str, table_name: str, client_id: str):
    sqlh = PostgreSqlHelper(db, host)
    con, cur = sqlh.connect()
    sqlh.remove(cur, con, table_name, client_id)
    sqlh.close(con,cur)
    return True


def create_table(db: str, host: str, table_name: str):
    sqlh = PostgreSqlHelper(db, host)
    con, cur = sqlh.connect()
    sqlh.create(cur,con,table_name,sqlh.client_keys)
    sqlh.close(con,cur)
    return True

def edit_client(db: str, host: str, client_id: str, grant_type: str = None, resource: str = None, new_client_secret: bool = False):
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


    
    

    