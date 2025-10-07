#!/usr/bin/env python3
"""
Grafana setup script for OpenProject DevLake integration
"""

import requests
import json
import yaml
import logging
import argparse
from pathlib import Path
import time
import sys

class GrafanaSetup:
    """Setup Grafana for OpenProject DevLake integration"""

    def __init__(self, grafana_url: str, admin_user: str, admin_password: str):
        self.grafana_url = grafana_url.rstrip('/')
        self.admin_user = admin_user
        self.admin_password = admin_password

        self.session = requests.Session()
        self.session.auth = (admin_user, admin_password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def test_connection(self):
        """Test connection to Grafana"""
        try:
            response = self.session.get(f"{self.grafana_url}/api/health")
            response.raise_for_status()
            self.logger.info("✅ Grafana connection successful")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to Grafana: {e}")
            return False

    def create_datasource(self, datasource_config_path: str):
        """Create MySQL datasource for DevLake"""
        try:
            with open(datasource_config_path, 'r') as f:
                config = yaml.safe_load(f)

            datasource = config['datasources'][0]

            # Check if datasource already exists
            response = self.session.get(f"{self.grafana_url}/api/datasources/name/{datasource['name']}")

            if response.status_code == 200:
                self.logger.info(f"Datasource '{datasource['name']}' already exists, updating...")
                datasource_id = response.json()['id']
                response = self.session.put(
                    f"{self.grafana_url}/api/datasources/{datasource_id}",
                    json=datasource
                )
            else:
                self.logger.info(f"Creating datasource '{datasource['name']}'...")
                response = self.session.post(
                    f"{self.grafana_url}/api/datasources",
                    json=datasource
                )

            if response.status_code in [200, 201]:
                self.logger.info("✅ Datasource configured successfully")
                return True
            else:
                self.logger.error(f"❌ Failed to configure datasource: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Error configuring datasource: {e}")
            return False

    def create_dashboard(self, dashboard_path: str):
        """Create dashboard from JSON file"""
        try:
            with open(dashboard_path, 'r') as f:
                dashboard_config = json.load(f)

            dashboard_title = dashboard_config['dashboard']['title']

            # Check if dashboard already exists
            search_response = self.session.get(
                f"{self.grafana_url}/api/search",
                params={'query': dashboard_title}
            )

            if search_response.status_code == 200:
                existing_dashboards = search_response.json()
                existing_dashboard = next(
                    (d for d in existing_dashboards if d['title'] == dashboard_title),
                    None
                )

                if existing_dashboard:
                    self.logger.info(f"Dashboard '{dashboard_title}' already exists, updating...")
                    dashboard_config['dashboard']['id'] = existing_dashboard['id']
                    dashboard_config['dashboard']['version'] = existing_dashboard.get('version', 1) + 1

            # Create/update dashboard
            response = self.session.post(
                f"{self.grafana_url}/api/dashboards/db",
                json=dashboard_config
            )

            if response.status_code == 200:
                result = response.json()
                dashboard_url = f"{self.grafana_url}/d/{result['uid']}/{result['slug']}"
                self.logger.info(f"✅ Dashboard '{dashboard_title}' created/updated")
                self.logger.info(f"   URL: {dashboard_url}")
                return True
            else:
                self.logger.error(f"❌ Failed to create dashboard '{dashboard_title}': {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Error creating dashboard {dashboard_path}: {e}")
            return False

    def create_folder(self, folder_name: str):
        """Create folder for organizing dashboards"""
        try:
            # Check if folder already exists
            response = self.session.get(f"{self.grafana_url}/api/folders")

            if response.status_code == 200:
                existing_folders = response.json()
                existing_folder = next(
                    (f for f in existing_folders if f['title'] == folder_name),
                    None
                )

                if existing_folder:
                    self.logger.info(f"Folder '{folder_name}' already exists")
                    return existing_folder['uid']

            # Create folder
            folder_data = {
                'title': folder_name,
                'uid': folder_name.lower().replace(' ', '-')
            }

            response = self.session.post(
                f"{self.grafana_url}/api/folders",
                json=folder_data
            )

            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"✅ Folder '{folder_name}' created")
                return result['uid']
            else:
                self.logger.error(f"❌ Failed to create folder '{folder_name}': {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"❌ Error creating folder: {e}")
            return None

    def setup_complete_environment(self):
        """Setup complete Grafana environment for OpenProject"""
        self.logger.info("🚀 Setting up Grafana environment for OpenProject DevLake integration")
        self.logger.info("=" * 70)

        success_count = 0
        total_steps = 4

        # Step 1: Test connection
        if self.test_connection():
            success_count += 1
        else:
            return False

        # Step 2: Create datasource
        datasource_path = Path(__file__).parent.parent / 'grafana' / 'datasource.yaml'
        if datasource_path.exists():
            if self.create_datasource(str(datasource_path)):
                success_count += 1
        else:
            self.logger.error(f"❌ Datasource config not found: {datasource_path}")

        # Step 3: Create folder
        folder_uid = self.create_folder('OpenProject')
        if folder_uid:
            success_count += 1

        # Step 4: Create dashboards
        dashboard_dir = Path(__file__).parent.parent / 'grafana' / 'dashboards'
        dashboard_files = list(dashboard_dir.glob('*.json'))

        if not dashboard_files:
            self.logger.warning("❌ No dashboard files found")
        else:
            dashboard_success = 0
            for dashboard_file in dashboard_files:
                if self.create_dashboard(str(dashboard_file)):
                    dashboard_success += 1
                time.sleep(1)  # Small delay between dashboard creation

            if dashboard_success > 0:
                success_count += 1
                self.logger.info(f"✅ Created/updated {dashboard_success} dashboards")

        # Summary
        self.logger.info("=" * 70)
        if success_count == total_steps:
            self.logger.info("🎉 Grafana setup completed successfully!")
            self.logger.info("")
            self.logger.info("📊 Access your dashboards at:")
            self.logger.info(f"   {self.grafana_url}/dashboards")
            self.logger.info("")
            self.logger.info("Available Dashboards:")
            self.logger.info("   • Team Productivity Dashboard")
            self.logger.info("   • Sprint Progress & Projects")
            self.logger.info("   • Issues Metrics & DORA")
            return True
        else:
            self.logger.warning(f"⚠️  Setup partially completed ({success_count}/{total_steps} steps)")
            return False

def main():
    parser = argparse.ArgumentParser(description='Setup Grafana for OpenProject DevLake')
    parser.add_argument('--url', required=True, help='Grafana URL (e.g., http://localhost:3001)')
    parser.add_argument('--user', default='admin', help='Grafana admin username (default: admin)')
    parser.add_argument('--password', required=True, help='Grafana admin password')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    setup = GrafanaSetup(args.url, args.user, args.password)

    print("🚀 OpenProject DevLake Grafana Setup")
    print("=" * 50)

    if setup.setup_complete_environment():
        print("\n✅ Grafana setup completed successfully!")
        print("\n🎯 Next Steps:")
        print("1. Open Grafana in your browser")
        print("2. Navigate to Dashboards to view your OpenProject analytics")
        print("3. Customize dashboards as needed for your team")
        sys.exit(0)
    else:
        print("\n❌ Grafana setup failed!")
        print("\nTroubleshooting:")
        print("1. Verify Grafana is running and accessible")
        print("2. Check admin credentials")
        print("3. Ensure MySQL datasource is reachable from Grafana")
        sys.exit(1)

if __name__ == "__main__":
    main()