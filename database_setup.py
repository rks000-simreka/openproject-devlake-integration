#!/usr/bin/env python3
"""
Database setup script for OpenProject DevLake integration
Creates all necessary raw and tool tables in the DevLake database
"""

import mysql.connector
import os
import yaml
from pathlib import Path
import logging
import sys

def load_config():
    """Load configuration from config.yaml"""
    config_path = Path("config.yaml")
    if not config_path.exists():
        raise FileNotFoundError("config.yaml not found")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/database_setup.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def create_database_connection(config):
    """Create database connection"""
    db_config = config['database']
    
    try:
        connection = mysql.connector.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            charset=db_config['charset'],
            autocommit=False
        )
        return connection
    except mysql.connector.Error as e:
        raise Exception(f"Database connection failed: {e}")

def execute_sql_file(connection, sql_file_path, logger):
    """Execute SQL commands from file"""
    
    if not Path(sql_file_path).exists():
        raise FileNotFoundError(f"SQL file not found: {sql_file_path}")
    
    with open(sql_file_path, 'r') as f:
        sql_content = f.read()
    
    # Split by semicolon and execute each statement
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    cursor = connection.cursor()
    
    try:
        for i, statement in enumerate(statements):
            if statement:
                # Show first 100 chars of statement
                preview = statement[:100].replace('\n', ' ')
                logger.info(f"Executing statement {i+1}/{len(statements)}: {preview}...")
                cursor.execute(statement)
        
        connection.commit()
        logger.info(f"✓ Successfully executed {sql_file_path}")
        
    except mysql.connector.Error as e:
        connection.rollback()
        logger.error(f"✗ Error executing {sql_file_path}: {e}")
        raise
    finally:
        cursor.close()

def verify_tables(connection, logger):
    """Verify that all tables were created successfully"""
    
    expected_raw_tables = [
        '_raw_openproject_api_work_packages',
        '_raw_openproject_api_projects',
        '_raw_openproject_api_users',
        '_raw_openproject_api_time_entries',
        '_raw_openproject_api_statuses',
        '_raw_openproject_api_types',
        '_raw_openproject_api_priorities',
        '_raw_openproject_api_versions',
        '_raw_openproject_api_activities'
    ]
    
    expected_tool_tables = [
        '_tool_openproject_work_packages',
        '_tool_openproject_projects',
        '_tool_openproject_users',
        '_tool_openproject_time_entries',
        '_tool_openproject_statuses',
        '_tool_openproject_types',
        '_tool_openproject_priorities',
        '_tool_openproject_versions',
        '_tool_openproject_activities'
    ]
    
    cursor = connection.cursor()
    
    # Check raw tables
    logger.info("\n" + "=" * 50)
    logger.info("Verifying Raw Tables...")
    logger.info("=" * 50)
    
    raw_count = 0
    for table in expected_raw_tables:
        cursor.execute(f"SHOW TABLES LIKE '{table}'")
        if cursor.fetchone():
            logger.info(f"✓ {table} exists")
            raw_count += 1
        else:
            logger.error(f"✗ {table} missing")
    
    # Check tool tables
    logger.info("\n" + "=" * 50)
    logger.info("Verifying Tool Tables...")
    logger.info("=" * 50)
    
    tool_count = 0
    for table in expected_tool_tables:
        cursor.execute(f"SHOW TABLES LIKE '{table}'")
        if cursor.fetchone():
            logger.info(f"✓ {table} exists")
            tool_count += 1
        else:
            logger.error(f"✗ {table} missing")
    
    cursor.close()
    
    logger.info("\n" + "=" * 50)
    logger.info("Verification Summary")
    logger.info("=" * 50)
    logger.info(f"Raw Tables: {raw_count}/{len(expected_raw_tables)}")
    logger.info(f"Tool Tables: {tool_count}/{len(expected_tool_tables)}")
    logger.info(f"Total: {raw_count + tool_count}/{len(expected_raw_tables) + len(expected_tool_tables)}")
    
    return (raw_count + tool_count) == (len(expected_raw_tables) + len(expected_tool_tables))

def main():
    """Main database setup function"""
    
    print("\n" + "=" * 50)
    print("OpenProject DevLake - Database Schema Setup")
    print("=" * 50 + "\n")
    
    logger = setup_logging()
    logger.info("Starting database setup...")
    
    connection = None
    
    try:
        # Load configuration
        config = load_config()
        logger.info("✓ Configuration loaded successfully")
        
        # Create database connection
        connection = create_database_connection(config)
        logger.info("✓ Database connection established")
        
        # Check if schema files exist
        schema_files = [
            "schema/01_create_raw_tables.sql",
            "schema/02_create_tool_tables.sql"
        ]
        
        for sql_file in schema_files:
            if not Path(sql_file).exists():
                logger.error(f"✗ Schema file not found: {sql_file}")
                logger.error("\nPlease ensure the SQL files are in the schema/ directory:")
                logger.error("  - schema/01_create_raw_tables.sql")
                logger.error("  - schema/02_create_tool_tables.sql")
                sys.exit(1)
        
        # Execute schema files
        logger.info("\n" + "=" * 50)
        logger.info("Creating Database Tables")
        logger.info("=" * 50 + "\n")
        
        for sql_file in schema_files:
            logger.info(f"Processing: {sql_file}")
            execute_sql_file(connection, sql_file, logger)
        
        # Verify tables
        logger.info("\n" + "=" * 50)
        logger.info("Verifying Table Creation")
        logger.info("=" * 50)
        
        success = verify_tables(connection, logger)
        
        if success:
            print("\n" + "=" * 50)
            print("✓ Database Setup Completed Successfully!")
            print("=" * 50)
            print("\nAll tables have been created in the database.")
            print("\nNext steps:")
            print("  1. Run initial data collection:")
            print("     python3 collectors/openproject_collector.py --verbose")
            print("\n  2. Check collected data:")
            print("     mysql -h 127.0.0.1 -P 3307 -u merico -pmerico lake")
            print("\n  3. View logs:")
            print("     tail -f logs/openproject_pipeline.log")
            sys.exit(0)
        else:
            logger.error("\n✗ Some tables were not created successfully")
            logger.error("Please check the errors above and try again")
            sys.exit(1)
        
    except FileNotFoundError as e:
        logger.error(f"✗ File not found: {e}")
        sys.exit(1)
    except mysql.connector.Error as e:
        logger.error(f"✗ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"✗ Database setup failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        if connection and connection.is_connected():
            connection.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()