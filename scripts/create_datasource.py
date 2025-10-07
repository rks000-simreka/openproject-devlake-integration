#!/usr/bin/env python3
"""
Simple Grafana datasource creator - creates just the MySQL datasource
"""

import requests
import json
import yaml

def create_datasource():
    # Load database config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    db_config = config['database']
    
    # Grafana API details
    grafana_url = "http://localhost:3001"
    
    print("🔧 Creating DevLake MySQL Datasource in Grafana")
    print("=" * 50)
    
    # Get admin credentials
    username = input("Grafana username (default: admin): ") or "admin"
    password = input("Grafana password: ")
    
    if not password:
        print("❌ Password required!")
        return False
    
    # Create datasource payload
    datasource = {
        "name": "DevLake MySQL",
        "type": "mysql",
        "url": f"{db_config['host']}:{db_config['port']}",
        "database": db_config['database'],
        "user": db_config['user'],
        "secureJsonData": {
            "password": db_config['password']
        },
        "jsonData": {
            "maxOpenConns": 100,
            "maxIdleConns": 100,
            "connMaxLifetime": 14400
        },
        "access": "proxy",
        "isDefault": True
    }
    
    try:
        # Create datasource
        response = requests.post(
            f"{grafana_url}/api/datasources",
            auth=(username, password),
            headers={'Content-Type': 'application/json'},
            data=json.dumps(datasource)
        )
        
        if response.status_code in [200, 409]:  # 409 = already exists
            print("✅ Datasource created successfully!")
            print(f"📊 Database: {db_config['database']} on {db_config['host']}:{db_config['port']}")
            print(f"👤 User: {db_config['user']}")
            
            # Test the datasource
            print("\n🔍 Testing datasource...")
            test_response = requests.get(
                f"{grafana_url}/api/datasources/name/DevLake%20MySQL",
                auth=(username, password)
            )
            
            if test_response.status_code == 200:
                datasource_id = test_response.json()['id']
                print(f"✅ Datasource test successful! ID: {datasource_id}")
                
                print("\n🎯 Next Steps:")
                print("1. Go to http://localhost:3001")
                print("2. Navigate to Dashboards → Import")
                print("3. Upload these JSON files:")
                print("   - grafana/dashboards/team-productivity.json")
                print("   - grafana/dashboards/sprint-progress.json") 
                print("   - grafana/dashboards/issues-metrics-dora.json")
                print("4. Select 'DevLake MySQL' as the datasource for each")
                
                return True
            else:
                print(f"⚠️ Datasource created but test failed: {test_response.text}")
                return False
                
        else:
            print(f"❌ Failed to create datasource: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = create_datasource()
    if success:
        print("\n🚀 Ready to import dashboards!")
    else:
        print("\n❌ Setup failed. Check the manual guide: MANUAL_SETUP_GUIDE.md")