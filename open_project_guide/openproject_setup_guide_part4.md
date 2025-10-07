
# OpenProject DevLake Integration - Setup Guide Part 4

## Grafana Configuration and Automation

### Step 10: Grafana Data Source Configuration

Create `grafana/datasource.yaml`:
```yaml
apiVersion: 1

datasources:
  - name: DevLake MySQL
    type: mysql
    access: proxy
    url: localhost:3306
    database: devlake
    user: grafana_user
    secureJsonData:
      password: grafana_password
    jsonData:
      maxOpenConns: 100
      maxIdleConns: 100
      maxIdleConnsAuto: true
      connMaxLifetime: 14400
      timezone: UTC
    isDefault: true
    editable: true
```

### Step 11: Create Grafana Dashboards

Create `grafana/dashboards/openproject-overview.json`:
```json
{
  "dashboard": {
    "id": null,
    "title": "OpenProject Overview Dashboard",
    "tags": ["openproject", "devlake"],
    "timezone": "browser",
    "refresh": "5m",
    "time": {
      "from": "now-30d",
      "to": "now"
    },
    "panels": [
      {
        "id": 1,
        "title": "Project Summary",
        "type": "stat",
        "targets": [
          {
            "expr": "",
            "format": "table",
            "rawSql": "SELECT COUNT(*) as total_projects FROM boards WHERE type = 'openproject'",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "custom": {
              "align": "center",
              "displayMode": "list"
            },
            "displayName": "Total Projects"
          }
        },
        "gridPos": {
          "h": 4,
          "w": 6,
          "x": 0,
          "y": 0
        }
      },
      {
        "id": 2,
        "title": "Active Issues",
        "type": "stat",
        "targets": [
          {
            "rawSql": "SELECT COUNT(*) as active_issues FROM issues WHERE status IN ('TODO', 'DOING') AND id LIKE 'openproject:%'",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "palette-classic"
            },
            "displayName": "Active Issues"
          }
        },
        "gridPos": {
          "h": 4,
          "w": 6,
          "x": 6,
          "y": 0
        }
      },
      {
        "id": 3,
        "title": "Completed Issues",
        "type": "stat", 
        "targets": [
          {
            "rawSql": "SELECT COUNT(*) as completed_issues FROM issues WHERE status = 'DONE' AND id LIKE 'openproject:%'",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "fixedColor": "green",
              "mode": "fixed"
            },
            "displayName": "Completed Issues"
          }
        },
        "gridPos": {
          "h": 4,
          "w": 6,
          "x": 12,
          "y": 0
        }
      },
      {
        "id": 4,
        "title": "Total Time Logged (Hours)",
        "type": "stat",
        "targets": [
          {
            "rawSql": "SELECT ROUND(SUM(time_spent_minutes)/60, 1) as total_hours FROM issue_worklogs WHERE id LIKE 'openproject:%'",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "fixedColor": "blue",
              "mode": "fixed"
            },
            "displayName": "Hours Logged"
          }
        },
        "gridPos": {
          "h": 4,
          "w": 6,
          "x": 18,
          "y": 0
        }
      },
      {
        "id": 5,
        "title": "Issues by Status",
        "type": "piechart",
        "targets": [
          {
            "rawSql": "SELECT status, COUNT(*) as count FROM issues WHERE id LIKE 'openproject:%' GROUP BY status ORDER BY count DESC",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "custom": {
              "hideFrom": {
                "legend": false,
                "tooltip": false,
                "vis": false
              }
            }
          }
        },
        "options": {
          "reduceOptions": {
            "values": false,
            "calcs": ["lastNotNull"],
            "fields": ""
          },
          "pieType": "pie",
          "tooltip": {
            "mode": "single"
          },
          "legend": {
            "displayMode": "table",
            "placement": "right",
            "values": ["value", "percent"]
          }
        },
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 4
        }
      },
      {
        "id": 6,
        "title": "Issues by Type",
        "type": "piechart",
        "targets": [
          {
            "rawSql": "SELECT type, COUNT(*) as count FROM issues WHERE id LIKE 'openproject:%' GROUP BY type ORDER BY count DESC",
            "refId": "A"
          }
        ],
        "options": {
          "reduceOptions": {
            "values": false,
            "calcs": ["lastNotNull"],
            "fields": ""
          },
          "pieType": "donut",
          "tooltip": {
            "mode": "single"
          },
          "legend": {
            "displayMode": "table",
            "placement": "right",
            "values": ["value", "percent"]
          }
        },
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 4
        }
      },
      {
        "id": 7,
        "title": "Issue Creation Trend",
        "type": "timeseries",
        "targets": [
          {
            "rawSql": "SELECT DATE(created_date) as time, COUNT(*) as count FROM issues WHERE id LIKE 'openproject:%' AND created_date >= DATE_SUB(NOW(), INTERVAL 30 DAY) GROUP BY DATE(created_date) ORDER BY time",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "palette-classic"
            },
            "custom": {
              "axisPlacement": "auto",
              "barAlignment": 0,
              "drawStyle": "line",
              "fillOpacity": 10,
              "gradientMode": "none",
              "hideFrom": {
                "legend": false,
                "tooltip": false,
                "vis": false
              },
              "lineInterpolation": "linear",
              "lineWidth": 2,
              "pointSize": 5,
              "scaleDistribution": {
                "type": "linear"
              },
              "showPoints": "auto",
              "spanNulls": false,
              "stacking": {
                "group": "A",
                "mode": "none"
              },
              "thresholdsStyle": {
                "mode": "off"
              }
            },
            "displayName": "Issues Created"
          }
        },
        "options": {
          "tooltip": {
            "mode": "single"
          },
          "legend": {
            "calcs": [],
            "displayMode": "list",
            "placement": "bottom"
          }
        },
        "gridPos": {
          "h": 8,
          "w": 24,
          "x": 0,
          "y": 12
        }
      },
      {
        "id": 8,
        "title": "Top Assignees by Active Issues",
        "type": "barchart",
        "targets": [
          {
            "rawSql": "SELECT assignee_name, COUNT(*) as active_count FROM issues WHERE status IN ('TODO', 'DOING') AND id LIKE 'openproject:%' AND assignee_name IS NOT NULL AND assignee_name != '' GROUP BY assignee_name ORDER BY active_count DESC LIMIT 10",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "palette-classic"
            },
            "custom": {
              "axisPlacement": "auto",
              "barAlignment": 0,
              "displayMode": "list",
              "orientation": "horizontal"
            },
            "displayName": "Active Issues"
          }
        },
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 20
        }
      },
      {
        "id": 9,
        "title": "Time Logging by User (Last 30 Days)",
        "type": "barchart",
        "targets": [
          {
            "rawSql": "SELECT author_name, ROUND(SUM(time_spent_minutes)/60, 1) as hours_logged FROM issue_worklogs WHERE id LIKE 'openproject:%' AND logged_date >= DATE_SUB(NOW(), INTERVAL 30 DAY) AND author_name IS NOT NULL AND author_name != '' GROUP BY author_name ORDER BY hours_logged DESC LIMIT 10",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "palette-classic"
            },
            "custom": {
              "axisPlacement": "auto",
              "barAlignment": 0,
              "displayMode": "list",
              "orientation": "horizontal"
            },
            "displayName": "Hours Logged",
            "unit": "h"
          }
        },
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 20
        }
      },
      {
        "id": 10,
        "title": "Project Activity Table",
        "type": "table",
        "targets": [
          {
            "rawSql": "SELECT b.name as project, COUNT(CASE WHEN i.status IN ('TODO', 'DOING') THEN 1 END) as active_issues, COUNT(CASE WHEN i.status = 'DONE' THEN 1 END) as completed_issues, ROUND(SUM(CASE WHEN w.logged_date >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN w.time_spent_minutes ELSE 0 END)/60, 1) as hours_this_week FROM boards b LEFT JOIN board_issues bi ON b.id = bi.board_id LEFT JOIN issues i ON bi.issue_id = i.id LEFT JOIN issue_worklogs w ON i.id = w.issue_id WHERE b.type = 'openproject' GROUP BY b.id, b.name ORDER BY active_issues DESC",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "custom": {
              "align": "auto",
              "displayMode": "auto"
            }
          },
          "overrides": [
            {
              "matcher": {
                "id": "byName",
                "options": "hours_this_week"
              },
              "properties": [
                {
                  "id": "unit",
                  "value": "h"
                }
              ]
            }
          ]
        },
        "options": {
          "showHeader": true,
          "sortBy": [
            {
              "desc": true,
              "displayName": "active_issues"
            }
          ]
        },
        "gridPos": {
          "h": 8,
          "w": 24,
          "x": 0,
          "y": 28
        }
      }
    ],
    "schemaVersion": 27,
    "version": 1,
    "links": []
  }
}
```

Create `grafana/dashboards/openproject-dora-metrics.json`:
```json
{
  "dashboard": {
    "id": null,
    "title": "OpenProject DORA Metrics",
    "description": "DORA (DevOps Research and Assessment) metrics for OpenProject",
    "tags": ["openproject", "dora", "devops"],
    "timezone": "browser",
    "refresh": "1d",
    "time": {
      "from": "now-90d",
      "to": "now"
    },
    "panels": [
      {
        "id": 1,
        "title": "Lead Time for Changes (Days)",
        "description": "Time from issue creation to completion",
        "type": "stat",
        "targets": [
          {
            "rawSql": "SELECT ROUND(AVG(lead_time_minutes)/1440, 1) as avg_lead_time_days FROM issues WHERE status = 'DONE' AND id LIKE 'openproject:%' AND resolution_date >= DATE_SUB(NOW(), INTERVAL 30 DAY) AND lead_time_minutes IS NOT NULL",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {
                  "color": "green",
                  "value": null
                },
                {
                  "color": "yellow", 
                  "value": 7
                },
                {
                  "color": "red",
                  "value": 30
                }
              ]
            },
            "unit": "d",
            "displayName": "Avg Lead Time"
          }
        },
        "gridPos": {
          "h": 4,
          "w": 6,
          "x": 0,
          "y": 0
        }
      },
      {
        "id": 2,
        "title": "Deployment Frequency",
        "description": "Issues completed per week",
        "type": "stat",
        "targets": [
          {
            "rawSql": "SELECT ROUND(COUNT(*)/4, 1) as issues_per_week FROM issues WHERE status = 'DONE' AND id LIKE 'openproject:%' AND resolution_date >= DATE_SUB(NOW(), INTERVAL 28 DAY)",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {
                  "color": "red",
                  "value": null
                },
                {
                  "color": "yellow",
                  "value": 1
                },
                {
                  "color": "green",
                  "value": 5
                }
              ]
            },
            "unit": "per week",
            "displayName": "Issues Completed"
          }
        },
        "gridPos": {
          "h": 4,
          "w": 6,
          "x": 6,
          "y": 0
        }
      },
      {
        "id": 3,
        "title": "Change Failure Rate",
        "description": "Percentage of bugs vs total completed issues",
        "type": "stat",
        "targets": [
          {
            "rawSql": "SELECT ROUND((SUM(CASE WHEN type = 'BUG' THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 1) as failure_rate FROM issues WHERE status = 'DONE' AND id LIKE 'openproject:%' AND resolution_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {
                  "color": "green",
                  "value": null
                },
                {
                  "color": "yellow",
                  "value": 10
                },
                {
                  "color": "red",
                  "value": 20
                }
              ]
            },
            "unit": "percent",
            "displayName": "Failure Rate"
          }
        },
        "gridPos": {
          "h": 4,
          "w": 6,
          "x": 12,
          "y": 0
        }
      },
      {
        "id": 4,
        "title": "Mean Time to Recovery",
        "description": "Average time to resolve bugs",
        "type": "stat",
        "targets": [
          {
            "rawSql": "SELECT ROUND(AVG(lead_time_minutes)/1440, 1) as avg_recovery_days FROM issues WHERE type = 'BUG' AND status = 'DONE' AND id LIKE 'openproject:%' AND resolution_date >= DATE_SUB(NOW(), INTERVAL 30 DAY) AND lead_time_minutes IS NOT NULL",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {
                  "color": "green",
                  "value": null
                },
                {
                  "color": "yellow",
                  "value": 1
                },
                {
                  "color": "red",
                  "value": 7
                }
              ]
            },
            "unit": "d",
            "displayName": "MTTR"
          }
        },
        "gridPos": {
          "h": 4,
          "w": 6,
          "x": 18,
          "y": 0
        }
      },
      {
        "id": 5,
        "title": "Lead Time Trend",
        "type": "timeseries",
        "targets": [
          {
            "rawSql": "SELECT DATE(resolution_date) as time, ROUND(AVG(lead_time_minutes)/1440, 1) as avg_lead_time_days FROM issues WHERE status = 'DONE' AND id LIKE 'openproject:%' AND resolution_date >= DATE_SUB(NOW(), INTERVAL 90 DAY) AND lead_time_minutes IS NOT NULL GROUP BY DATE(resolution_date) ORDER BY time",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "palette-classic"
            },
            "custom": {
              "axisPlacement": "auto",
              "drawStyle": "line",
              "fillOpacity": 20,
              "lineWidth": 2,
              "pointSize": 5
            },
            "unit": "d",
            "displayName": "Lead Time (Days)"
          }
        },
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 4
        }
      },
      {
        "id": 6,
        "title": "Weekly Completion Rate",
        "type": "timeseries",
        "targets": [
          {
            "rawSql": "SELECT DATE(DATE_SUB(resolution_date, INTERVAL WEEKDAY(resolution_date) DAY)) as week_start, COUNT(*) as completed_count FROM issues WHERE status = 'DONE' AND id LIKE 'openproject:%' AND resolution_date >= DATE_SUB(NOW(), INTERVAL 90 DAY) GROUP BY week_start ORDER BY week_start",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "palette-classic"
            },
            "custom": {
              "axisPlacement": "auto",
              "drawStyle": "bars",
              "fillOpacity": 80
            },
            "displayName": "Issues Completed"
          }
        },
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 4
        }
      },
      {
        "id": 7,
        "title": "Issue Type Distribution (Last 30 Days)",
        "type": "table",
        "targets": [
          {
            "rawSql": "SELECT type, COUNT(*) as total, SUM(CASE WHEN status = 'DONE' THEN 1 ELSE 0 END) as completed, ROUND(AVG(CASE WHEN status = 'DONE' AND lead_time_minutes IS NOT NULL THEN lead_time_minutes END)/1440, 1) as avg_lead_time_days FROM issues WHERE id LIKE 'openproject:%' AND created_date >= DATE_SUB(NOW(), INTERVAL 30 DAY) GROUP BY type ORDER BY total DESC",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "custom": {
              "align": "auto",
              "displayMode": "auto"
            }
          },
          "overrides": [
            {
              "matcher": {
                "id": "byName",
                "options": "avg_lead_time_days"
              },
              "properties": [
                {
                  "id": "unit",
                  "value": "d"
                }
              ]
            }
          ]
        },
        "gridPos": {
          "h": 6,
          "w": 24,
          "x": 0,
          "y": 12
        }
      }
    ],
    "schemaVersion": 27,
    "version": 1
  }
}
```

### Step 12: Create Grafana Setup Script

Create `scripts/setup_grafana.py`:
```python
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

        logging.basicConfig(level=logging.INFO)
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

    def create_dashboard(self, dashboard_path: str):
        """Create dashboard from JSON file"""

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
                dashboard_config['dashboard']['version'] = existing_dashboard['version'] + 1

        # Create/update dashboard
        response = self.session.post(
            f"{self.grafana_url}/api/dashboards/db",
            json=dashboard_config
        )

        if response.status_code == 200:
            result = response.json()
            dashboard_url = f"{self.grafana_url}/d/{result['uid']}/{result['slug']}"
            self.logger.info(f"✅ Dashboard '{dashboard_title}' created/updated: {dashboard_url}")
            return True
        else:
            self.logger.error(f"❌ Failed to create dashboard '{dashboard_title}': {response.text}")
            return False

    def create_folder(self, folder_name: str):
        """Create folder for organizing dashboards"""

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

    def setup_complete_environment(self):
        """Setup complete Grafana environment for OpenProject"""

        self.logger.info("🚀 Setting up Grafana environment for OpenProject DevLake integration")

        success_count = 0
        total_steps = 4

        # Step 1: Test connection
        if self.test_connection():
            success_count += 1
        else:
            return False

        # Step 2: Create datasource
        if self.create_datasource('grafana/datasource.yaml'):
            success_count += 1

        # Step 3: Create folder
        folder_uid = self.create_folder('OpenProject')
        if folder_uid:
            success_count += 1

        # Step 4: Create dashboards
        dashboard_files = [
            'grafana/dashboards/openproject-overview.json',
            'grafana/dashboards/openproject-dora-metrics.json'
        ]

        dashboard_success = 0
        for dashboard_file in dashboard_files:
            if Path(dashboard_file).exists():
                if self.create_dashboard(dashboard_file):
                    dashboard_success += 1
            else:
                self.logger.warning(f"Dashboard file not found: {dashboard_file}")

        if dashboard_success > 0:
            success_count += 1

        # Summary
        self.logger.info("=" * 60)
        if success_count == total_steps:
            self.logger.info("🎉 Grafana setup completed successfully!")
            self.logger.info(f"📊 Access your dashboards at: {self.grafana_url}")
            return True
        else:
            self.logger.warning(f"⚠️  Setup partially completed ({success_count}/{total_steps} steps)")
            return False

def main():
    parser = argparse.ArgumentParser(description='Setup Grafana for OpenProject DevLake')
    parser.add_argument('--url', required=True, help='Grafana URL (e.g., http://localhost:3000)')
    parser.add_argument('--user', default='admin', help='Grafana admin username')
    parser.add_argument('--password', required=True, help='Grafana admin password')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    setup = GrafanaSetup(args.url, args.user, args.password)

    if setup.setup_complete_environment():
        print("✅ Grafana setup completed successfully")
        exit(0)
    else:
        print("❌ Grafana setup failed")
        exit(1)

if __name__ == "__main__":
    main()
```

### Step 13: Create Automation Scripts

Create `scripts/scheduler.py`:
```python
#!/usr/bin/env python3
"""
Scheduler for OpenProject DevLake data pipeline
"""

import schedule
import time
import subprocess
import logging
import yaml
import signal
import sys
from datetime import datetime
from pathlib import Path

class PipelineScheduler:
    """Scheduler for automated pipeline execution"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.running = True

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scheduler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info("Pipeline Scheduler initialized")

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def run_incremental_sync(self):
        """Run incremental data sync"""
        self.logger.info("🔄 Starting incremental sync")

        try:
            result = subprocess.run([
                'python', 'pipeline.py', 
                '--incremental',
                '--config', 'config.yaml'
            ], capture_output=True, text=True, timeout=3600)  # 1 hour timeout

            if result.returncode == 0:
                self.logger.info("✅ Incremental sync completed successfully")
            else:
                self.logger.error(f"❌ Incremental sync failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            self.logger.error("❌ Incremental sync timed out")
        except Exception as e:
            self.logger.error(f"❌ Incremental sync error: {e}")

    def run_full_sync(self):
        """Run full data sync"""
        self.logger.info("🔄 Starting full sync")

        try:
            result = subprocess.run([
                'python', 'pipeline.py',
                '--full',
                '--config', 'config.yaml'
            ], capture_output=True, text=True, timeout=7200)  # 2 hour timeout

            if result.returncode == 0:
                self.logger.info("✅ Full sync completed successfully")
            else:
                self.logger.error(f"❌ Full sync failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            self.logger.error("❌ Full sync timed out")
        except Exception as e:
            self.logger.error(f"❌ Full sync error: {e}")

    def setup_schedules(self):
        """Setup scheduled tasks based on configuration"""

        collection_config = self.config.get('collection', {})

        # Incremental sync schedule
        sync_interval_hours = collection_config.get('sync_interval_hours', 6)
        schedule.every(sync_interval_hours).hours.do(self.run_incremental_sync)
        self.logger.info(f"📅 Scheduled incremental sync every {sync_interval_hours} hours")

        # Full sync schedule  
        full_sync_interval_days = collection_config.get('full_sync_interval_days', 7)
        schedule.every(full_sync_interval_days).days.at("02:00").do(self.run_full_sync)
        self.logger.info(f"📅 Scheduled full sync every {full_sync_interval_days} days at 02:00")

        # Health check
        schedule.every(1).hours.do(self._health_check)
        self.logger.info("📅 Scheduled health check every hour")

    def _health_check(self):
        """Perform health check"""
        self.logger.info("💓 Pipeline scheduler health check - OK")

    def run(self):
        """Run the scheduler"""

        self.logger.info("🚀 Starting Pipeline Scheduler")
        self.setup_schedules()

        # Run initial incremental sync
        self.logger.info("Running initial incremental sync...")
        self.run_incremental_sync()

        # Main scheduler loop
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(60)

        self.logger.info("📊 Pipeline Scheduler stopped")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='OpenProject Pipeline Scheduler')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')

    args = parser.parse_args()

    scheduler = PipelineScheduler(args.config)

    if args.daemon:
        # For production daemon mode, you might want to use python-daemon
        # For now, just run normally
        pass

    try:
        scheduler.run()
    except KeyboardInterrupt:
        print("\nScheduler stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

Create `scripts/health_check.py`:
```python
#!/usr/bin/env python3
"""
Health check script for OpenProject DevLake integration
"""

import mysql.connector
import requests
import yaml
import json
import logging
from datetime import datetime, timedelta
import argparse

class HealthChecker:
    """Health check for OpenProject DevLake integration"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.checks = {
            'database': False,
            'openproject_api': False,
            'data_freshness': False,
            'grafana': False
        }

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def check_database(self):
        """Check MySQL database connectivity and basic structure"""

        try:
            connection = mysql.connector.connect(**self.config['database'])
            cursor = connection.cursor()

            # Check if key tables exist
            required_tables = [
                '_raw_openproject_api_work_packages',
                '_tool_openproject_work_packages', 
                'issues',
                'boards'
            ]

            for table in required_tables:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if not cursor.fetchone():
                    raise Exception(f"Required table {table} not found")

            # Check data counts
            cursor.execute("SELECT COUNT(*) FROM issues WHERE id LIKE 'openproject:%'")
            issue_count = cursor.fetchone()[0]

            cursor.close()
            connection.close()

            self.checks['database'] = True
            self.logger.info(f"✅ Database OK ({issue_count} OpenProject issues)")
            return True

        except Exception as e:
            self.logger.error(f"❌ Database check failed: {e}")
            return False

    def check_openproject_api(self):
        """Check OpenProject API connectivity"""

        try:
            op_config = self.config['openproject']
            url = f"{op_config['base_url']}/api/v3/users/me"

            import base64
            auth_string = f"apikey:{op_config['api_key']}"
            auth_header = base64.b64encode(auth_string.encode()).decode()

            headers = {
                'Authorization': f'Basic {auth_header}',
                'Accept': 'application/json'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            user_data = response.json()

            self.checks['openproject_api'] = True
            self.logger.info(f"✅ OpenProject API OK (User: {user_data.get('name', 'Unknown')})")
            return True

        except Exception as e:
            self.logger.error(f"❌ OpenProject API check failed: {e}")
            return False

    def check_data_freshness(self):
        """Check if data is fresh (updated recently)"""

        try:
            connection = mysql.connector.connect(**self.config['database'])
            cursor = connection.cursor()

            # Check last raw data collection
            cursor.execute("""
                SELECT MAX(created_at) as last_collection
                FROM _raw_openproject_api_work_packages
                WHERE connection_id = %s
            """, (self.config['openproject']['connection_id'],))

            result = cursor.fetchone()
            last_collection = result[0] if result else None

            if last_collection:
                time_diff = datetime.now() - last_collection
                hours_old = time_diff.total_seconds() / 3600

                # Data should be fresher than configured sync interval + 2 hours buffer
                max_age_hours = self.config.get('collection', {}).get('sync_interval_hours', 6) + 2

                if hours_old <= max_age_hours:
                    self.checks['data_freshness'] = True
                    self.logger.info(f"✅ Data freshness OK ({hours_old:.1f} hours old)")
                    success = True
                else:
                    self.logger.warning(f"⚠️  Data is stale ({hours_old:.1f} hours old)")
                    success = False
            else:
                self.logger.error("❌ No data found")
                success = False

            cursor.close()
            connection.close()
            return success

        except Exception as e:
            self.logger.error(f"❌ Data freshness check failed: {e}")
            return False

    def check_grafana(self):
        """Check Grafana connectivity (if configured)"""

        grafana_config = self.config.get('grafana', {})

        if not grafana_config:
            self.logger.info("ℹ️  Grafana not configured, skipping check")
            self.checks['grafana'] = True
            return True

        try:
            url = f"{grafana_config['url']}/api/health"

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            self.checks['grafana'] = True
            self.logger.info("✅ Grafana OK")
            return True

        except Exception as e:
            self.logger.error(f"❌ Grafana check failed: {e}")
            return False

    def run_all_checks(self):
        """Run all health checks"""

        self.logger.info("🏥 Running health checks...")
        self.logger.info("=" * 50)

        # Run checks
        self.check_database()
        self.check_openproject_api()
        self.check_data_freshness()
        self.check_grafana()

        # Summary
        passed = sum(self.checks.values())
        total = len(self.checks)

        self.logger.info("=" * 50)
        self.logger.info(f"📊 Health Check Summary: {passed}/{total} checks passed")

        for check, status in self.checks.items():
            status_icon = "✅" if status else "❌"
            self.logger.info(f"{status_icon} {check}")

        overall_healthy = passed == total

        if overall_healthy:
            self.logger.info("🎉 System is healthy!")
        else:
            self.logger.warning("⚠️  System has issues that need attention")

        return overall_healthy, self.checks

    def get_system_info(self):
        """Get system information"""

        try:
            connection = mysql.connector.connect(**self.config['database'])
            cursor = connection.cursor()

            # Get data counts
            stats = {}

            tables_to_check = [
                ('Raw Work Packages', '_raw_openproject_api_work_packages'),
                ('Tool Work Packages', '_tool_openproject_work_packages'),
                ('Domain Issues', 'issues', "WHERE id LIKE 'openproject:%'"),
                ('Domain Boards', 'boards', "WHERE type = 'openproject'"),
                ('Domain Worklogs', 'issue_worklogs', "WHERE id LIKE 'openproject:%'")
            ]

            for label, table, *where_clause in tables_to_check:
                where = where_clause[0] if where_clause else ""
                query = f"SELECT COUNT(*) FROM {table} {where}"
                cursor.execute(query)
                stats[label] = cursor.fetchone()[0]

            cursor.close()
            connection.close()

            self.logger.info("📈 System Statistics:")
            for label, count in stats.items():
                self.logger.info(f"  {label}: {count:,}")

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {}

def main():
    parser = argparse.ArgumentParser(description='OpenProject DevLake Health Check')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--stats', action='store_true', help='Show system statistics')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    checker = HealthChecker(args.config)

    # Run health checks
    healthy, results = checker.run_all_checks()

    # Show statistics if requested
    if args.stats:
        print()
        checker.get_system_info()

    # Exit with appropriate code
    exit(0 if healthy else 1)

if __name__ == "__main__":
    main()
```

### Step 14: Create Deployment Guide

Create `DEPLOYMENT.md`:
```markdown
# OpenProject DevLake Integration - Deployment Guide

## Quick Start

### 1. Setup Environment
```bash
# Clone or create project directory
mkdir openproject-devlake
cd openproject-devlake

# Install Python dependencies
pip install -r requirements.txt

# Copy configuration template
cp config.yaml.template config.yaml
```

### 2. Configure Settings
Edit `config.yaml` with your settings:
- OpenProject URL and API key
- MySQL database connection
- Collection preferences

### 3. Setup Database
```bash
# Create schema
python database_setup.py

# Verify tables created
python scripts/health_check.py --stats
```

### 4. Run Initial Collection
```bash
# Full sync for initial data
python pipeline.py --full --verbose

# Check results
python scripts/health_check.py
```

### 5. Setup Grafana (Optional)
```bash
# Configure Grafana datasource and dashboards
python scripts/setup_grafana.py --url http://localhost:3000 --password admin
```

### 6. Setup Automation
```bash
# Start scheduler for regular syncs
python scripts/scheduler.py --config config.yaml
```

## Production Deployment

### Prerequisites
- MySQL 8.0+ (or compatible DevLake database)
- Python 3.8+
- OpenProject instance with API access
- Grafana (optional, for dashboards)

### Installation Steps

1. **Prepare Environment**
   ```bash
   # Create dedicated user
   sudo useradd -m -s /bin/bash openproject-devlake
   sudo su - openproject-devlake

   # Setup Python virtual environment
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Database**
   ```bash
   # Setup MySQL user and database
   mysql -u root -p
   CREATE DATABASE devlake CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'devlake'@'localhost' IDENTIFIED BY 'secure_password';
   GRANT ALL PRIVILEGES ON devlake.* TO 'devlake'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **Setup Configuration**
   ```bash
   # Create production config
   cp config.yaml.template config.yaml
   # Edit with production settings

   # Setup environment file
   cp .env.template .env
   # Add sensitive credentials
   ```

4. **Initialize Database Schema**
   ```bash
   python database_setup.py
   ```

5. **Test Pipeline**
   ```bash
   # Run health check
   python scripts/health_check.py

   # Test with limited data
   python pipeline.py --projects 1 --incremental --verbose
   ```

6. **Setup Systemd Service**

   Create `/etc/systemd/system/openproject-devlake.service`:
   ```ini
   [Unit]
   Description=OpenProject DevLake Pipeline Scheduler
   After=network.target mysql.service

   [Service]
   Type=simple
   User=openproject-devlake
   Group=openproject-devlake
   WorkingDirectory=/home/openproject-devlake/openproject-devlake
   Environment=PATH=/home/openproject-devlake/openproject-devlake/venv/bin
   ExecStart=/home/openproject-devlake/openproject-devlake/venv/bin/python scripts/scheduler.py --config config.yaml
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable openproject-devlake
   sudo systemctl start openproject-devlake
   sudo systemctl status openproject-devlake
   ```

7. **Setup Log Rotation**

   Create `/etc/logrotate.d/openproject-devlake`:
   ```
   /home/openproject-devlake/openproject-devlake/*.log {
       daily
       rotate 30
       compress
       delaycompress
       missingok
       notifempty
       create 644 openproject-devlake openproject-devlake
   }
   ```

### Monitoring and Maintenance

1. **Health Monitoring**
   ```bash
   # Setup cron job for health checks
   crontab -e

   # Add line:
   */15 * * * * /home/openproject-devlake/openproject-devlake/venv/bin/python /home/openproject-devlake/openproject-devlake/scripts/health_check.py --config /home/openproject-devlake/openproject-devlake/config.yaml
   ```

2. **Log Monitoring**
   ```bash
   # View pipeline logs
   tail -f openproject_pipeline.log

   # View scheduler logs  
   tail -f scheduler.log

   # Check service logs
   sudo journalctl -u openproject-devlake -f
   ```

3. **Performance Tuning**
   - Adjust `batch_size` in config for large datasets
   - Tune `rate_limit_rpm` based on OpenProject limits
   - Configure MySQL performance settings
   - Monitor disk space for log files

### Backup and Recovery

1. **Database Backup**
   ```bash
   # Backup DevLake data
   mysqldump -u devlake -p devlake > devlake_backup_$(date +%Y%m%d).sql
   ```

2. **Configuration Backup**
   ```bash
   # Backup configuration
   tar -czf config_backup_$(date +%Y%m%d).tar.gz config.yaml .env
   ```

3. **Recovery**
   ```bash
   # Restore database
   mysql -u devlake -p devlake < devlake_backup_20241006.sql

   # Restore configuration
   tar -xzf config_backup_20241006.tar.gz
   ```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check MySQL service status
   - Verify credentials in config.yaml
   - Test connection manually

2. **OpenProject API Authentication Failed**
   - Verify API key is correct and active
   - Check OpenProject user permissions
   - Test API endpoint manually

3. **Pipeline Hangs or Times Out**
   - Check network connectivity
   - Reduce batch_size in config
   - Increase timeout values

4. **Grafana Dashboards Show No Data**
   - Verify datasource configuration
   - Check domain table data exists
   - Verify MySQL user permissions for Grafana

5. **Scheduler Not Running**
   - Check systemd service status
   - Review scheduler logs
   - Verify Python virtual environment

### Debug Commands

```bash
# Test individual components
python collectors/openproject_collector.py --config config.yaml --verbose
python extractors/openproject_extractor.py --config config.yaml --verbose  
python converters/openproject_converter.py --config config.yaml --verbose

# Test specific stages
python pipeline.py --collection-only --projects 1 --verbose
python pipeline.py --extraction-only --verbose
python pipeline.py --conversion-only --verbose

# Health checks
python scripts/health_check.py --verbose --stats

# Database inspection
mysql -u devlake -p devlake
SELECT COUNT(*) FROM issues WHERE id LIKE 'openproject:%';
SELECT COUNT(*) FROM _raw_openproject_api_work_packages;
```

This completes the comprehensive deployment guide for production environments.
```

## Summary

This complete setup guide provides:

✅ **18 Database Tables** - Complete schema for raw, tool, and domain layers
✅ **Production-Ready Pipeline** - Collector, Extractor, Converter with error handling
✅ **Grafana Integration** - Pre-built dashboards and DORA metrics
✅ **Automation Scripts** - Scheduler, health checks, and monitoring
✅ **Deployment Guide** - Production setup with systemd services
✅ **CLI Tools** - Complete command-line interface for all operations

The implementation creates a DevLake-compatible OpenProject integration that provides the same level of analytics available for JIRA data sources.
