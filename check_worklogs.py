#!/usr/bin/env python3

import mysql.connector
import yaml
from pathlib import Path

def load_config():
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def check_worklogs_schema():
    config = load_config()
    
    # Connect to database
    db_config = config['database']
    connection = mysql.connector.connect(
        host=db_config['host'],
        port=db_config['port'],
        database=db_config['database'],
        user=db_config['user'],
        password=db_config['password'],
        charset=db_config['charset']
    )
    
    cursor = connection.cursor()
    
    print("=== Issue Worklogs Table Structure ===")
    cursor.execute("DESCRIBE issue_worklogs")
    columns = cursor.fetchall()
    
    for column in columns:
        field, type_info, null, key, default, extra = column
        print(f"  {field}: {type_info}")
    
    print("\n=== Sample Worklog Data ===")
    cursor.execute("SELECT * FROM issue_worklogs LIMIT 2")
    rows = cursor.fetchall()
    
    if rows:
        # Get column names
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'issue_worklogs'", (db_config['database'],))
        column_names = [row[0] for row in cursor.fetchall()]
        print(f"Columns: {column_names}")
        
        for i, row in enumerate(rows, 1):
            print(f"Row {i}: {dict(zip(column_names, row))}")
    else:
        print("No data found")
    
    cursor.close()
    connection.close()

if __name__ == "__main__":
    check_worklogs_schema()