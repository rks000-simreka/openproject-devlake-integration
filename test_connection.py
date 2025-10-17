#!/usr/bin/env python3
"""
Test connections for OpenProject and DevLake Database
"""

import yaml
import sys
import requests
import mysql.connector
from tabulate import tabulate

def load_config():
    """Load configuration from config.yaml"""
    try:
        with open('config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("❌ Error: config.yaml not found!")
        print("Please create config.yaml from config.yaml.example")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading config.yaml: {e}")
        sys.exit(1)

def test_openproject_connection(config):
    """Test connection to OpenProject API"""
    print("\n" + "="*60)
    print("Testing OpenProject API Connection")
    print("="*60)
    
    op_config = config.get('openproject', {})
    base_url = op_config.get('base_url')
    api_key = op_config.get('api_key')
    
    if not base_url or not api_key:
        print("❌ OpenProject configuration missing in config.yaml")
        return False
    
    print(f"URL: {base_url}")
    print(f"API Key: {'*' * (len(api_key) - 8) + api_key[-8:]}")
    
    try:
        # Test API connection
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{base_url}/api/v3/projects",
            headers=headers,
            timeout=10,
            params={'pageSize': 1}
        )
        
        if response.status_code == 200:
            data = response.json()
            total_projects = data.get('total', 0)
            print(f"\n✅ Connection successful!")
            print(f"📊 Found {total_projects} projects")
            return True
        else:
            print(f"\n❌ Connection failed!")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n❌ Connection timeout!")
        print("The OpenProject server is not responding.")
        return False
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection error!")
        print("Cannot reach the OpenProject server. Check the URL.")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def test_database_connection(config):
    """Test connection to DevLake MySQL database"""
    print("\n" + "="*60)
    print("Testing DevLake MySQL Database Connection")
    print("="*60)
    
    db_config = config.get('database', {})
    
    print(f"Host: {db_config.get('host')}:{db_config.get('port')}")
    print(f"Database: {db_config.get('database')}")
    print(f"User: {db_config.get('user')}")
    
    try:
        # Test database connection
        connection = mysql.connector.connect(
            host=db_config.get('host'),
            port=db_config.get('port'),
            database=db_config.get('database'),
            user=db_config.get('user'),
            password=db_config.get('password'),
            charset=db_config.get('charset', 'utf8mb4')
        )
        
        cursor = connection.cursor()
        
        # Test basic query
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"\n✅ Connection successful!")
        print(f"MySQL version: {version}")
        
        # Check for OpenProject data
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM issues WHERE id LIKE 'openproject:%') as issues,
                (SELECT COUNT(*) FROM boards WHERE id LIKE 'openproject:%') as boards,
                (SELECT COUNT(*) FROM accounts WHERE id LIKE 'openproject:%') as accounts
        """)
        
        counts = cursor.fetchone()
        
        print(f"\n📊 OpenProject Data in DevLake:")
        table_data = [
            ["Issues", counts[0]],
            ["Boards", counts[1]],
            ["Accounts", counts[2]]
        ]
        print(tabulate(table_data, headers=["Table", "Count"], tablefmt="grid"))
        
        if sum(counts) == 0:
            print("\n⚠️  No OpenProject data found in database.")
            print("Run the pipeline to collect data: python3 run_pipeline.py")
        
        cursor.close()
        connection.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"\n❌ Database connection failed!")
        print(f"Error: {e}")
        print("\nCommon issues:")
        print("  - Is MySQL/DevLake running? Check with: docker ps")
        print("  - Is the port correct? (default: 3307)")
        print("  - Are the credentials correct?")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def main():
    """Main test function"""
    print("\n" + "="*60)
    print("🔍 OpenProject DevLake Integration - Connection Test")
    print("="*60)
    
    # Load configuration
    config = load_config()
    
    # Test connections
    op_success = test_openproject_connection(config)
    db_success = test_database_connection(config)
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    results = [
        ["OpenProject API", "✅ OK" if op_success else "❌ Failed"],
        ["DevLake Database", "✅ OK" if db_success else "❌ Failed"]
    ]
    print(tabulate(results, headers=["Component", "Status"], tablefmt="grid"))
    
    if op_success and db_success:
        print("\n✅ All connections successful!")
        print("You can now run the pipeline: python3 run_pipeline.py")
        return 0
    else:
        print("\n❌ Some connections failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
