
# OpenProject DevLake Integration - Setup Guide Part 3

## Domain Layer Conversion and Grafana Setup

### Step 8: Create Domain Layer Converter

Create `converters/openproject_converter.py`:
```python
#!/usr/bin/env python3
"""
OpenProject Domain Converter - Converts tool-layer data to DevLake domain tables
"""

import mysql.connector
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import yaml
import json

class OpenProjectConverter:
    """Converts tool-layer data to domain-layer tables"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.connection_id = self.config['openproject']['connection_id']
        self.db_config = self.config['database']

        # Transformation rules - customize these based on your OpenProject setup
        self.type_mappings = {
            'Feature': 'REQUIREMENT',
            'Bug': 'BUG', 
            'Support': 'REQUIREMENT',
            'Incident': 'INCIDENT',
            'Task': 'REQUIREMENT',
            'Epic': 'REQUIREMENT',
            'User Story': 'REQUIREMENT',
            'Defect': 'BUG',
            'Enhancement': 'REQUIREMENT',
            'Story': 'REQUIREMENT'
        }

        self.status_mappings = {
            'New': 'TODO',
            'Open': 'TODO',
            'In progress': 'DOING',
            'In Progress': 'DOING',
            'In development': 'DOING',
            'In Development': 'DOING',
            'In review': 'DOING',
            'In Review': 'DOING',
            'Testing': 'DOING',
            'On hold': 'TODO',
            'Blocked': 'TODO',
            'Closed': 'DONE',
            'Resolved': 'DONE',
            'Done': 'DONE',
            'Completed': 'DONE',
            'Rejected': 'DONE',
            'Cancelled': 'DONE'
        }

        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.{self.connection_id}")
        self.logger.setLevel(getattr(logging, self.config['logging']['level']))

        self.logger.info("OpenProject Converter initialized")

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _get_db_connection(self):
        """Get database connection"""
        return mysql.connector.connect(**self.db_config)

    def _ensure_domain_tables_exist(self):
        """Ensure DevLake domain tables exist (they should already exist in DevLake)"""

        connection = self._get_db_connection()
        cursor = connection.cursor()

        domain_table_ddl = {
            'issues': """
                CREATE TABLE IF NOT EXISTS issues (
                    id VARCHAR(255) PRIMARY KEY,
                    url VARCHAR(500),
                    issue_key VARCHAR(255),
                    title VARCHAR(500),
                    description LONGTEXT,
                    type VARCHAR(100),
                    original_type VARCHAR(100),
                    status VARCHAR(100),
                    original_status VARCHAR(100),
                    story_point DOUBLE,
                    priority VARCHAR(255),
                    urgency VARCHAR(255),
                    component VARCHAR(255),
                    severity VARCHAR(255),
                    parent_issue_id VARCHAR(255),
                    epic_key VARCHAR(255),
                    original_estimate_minutes INT,
                    time_spent_minutes INT,
                    time_remaining_minutes INT,
                    creator_id VARCHAR(255),
                    creator_name VARCHAR(255),
                    assignee_id VARCHAR(255), 
                    assignee_name VARCHAR(255),
                    created_date TIMESTAMP(3),
                    updated_date TIMESTAMP(3),
                    resolution_date TIMESTAMP(3),
                    lead_time_minutes INT,
                    original_project VARCHAR(255),
                    icon_url VARCHAR(255)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,

            'boards': """
                CREATE TABLE IF NOT EXISTS boards (
                    id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255),
                    description LONGTEXT,
                    url VARCHAR(500),
                    created_date TIMESTAMP(3),
                    type VARCHAR(100)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,

            'board_issues': """
                CREATE TABLE IF NOT EXISTS board_issues (
                    board_id VARCHAR(255),
                    issue_id VARCHAR(255),
                    PRIMARY KEY (board_id, issue_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,

            'issue_worklogs': """
                CREATE TABLE IF NOT EXISTS issue_worklogs (
                    id VARCHAR(255) PRIMARY KEY,
                    author_id VARCHAR(255),
                    author_name VARCHAR(255),
                    comment LONGTEXT,
                    time_spent_minutes INT,
                    logged_date TIMESTAMP(3),
                    started_date TIMESTAMP(3),
                    issue_id VARCHAR(255)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,

            'sprints': """
                CREATE TABLE IF NOT EXISTS sprints (
                    id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255),
                    url VARCHAR(500),
                    status VARCHAR(100),
                    started_date TIMESTAMP(3),
                    ended_date TIMESTAMP(3),
                    completed_date TIMESTAMP(3),
                    original_board_id VARCHAR(255)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,

            'sprint_issues': """
                CREATE TABLE IF NOT EXISTS sprint_issues (
                    sprint_id VARCHAR(255),
                    issue_id VARCHAR(255),
                    PRIMARY KEY (sprint_id, issue_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,

            'accounts': """
                CREATE TABLE IF NOT EXISTS accounts (
                    id VARCHAR(255) PRIMARY KEY,
                    full_name VARCHAR(255),
                    user_name VARCHAR(255),
                    email VARCHAR(255),
                    avatar_url VARCHAR(500),
                    organization VARCHAR(255),
                    created_date TIMESTAMP(3),
                    status INT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        }

        try:
            for table_name, ddl in domain_table_ddl.items():
                self.logger.debug(f"Ensuring {table_name} table exists")
                cursor.execute(ddl)

            connection.commit()
            self.logger.info("Domain tables verified/created")

        except Exception as e:
            self.logger.error(f"Failed to ensure domain tables: {e}")
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def convert_issues(self):
        """Convert work packages to domain issues table"""

        self.logger.info("Starting issues conversion")

        connection = self._get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            # Get tool work packages
            cursor.execute("""
                SELECT wp.*, p.identifier as project_identifier, s.is_closed as status_is_closed
                FROM _tool_openproject_work_packages wp
                LEFT JOIN _tool_openproject_projects p ON wp.connection_id = p.connection_id AND wp.project_id = p.id
                LEFT JOIN _tool_openproject_statuses s ON wp.connection_id = s.connection_id AND wp.status_id = s.id
                WHERE wp.connection_id = %s
            """, (self.connection_id,))

            work_packages = cursor.fetchall()
            self.logger.info(f"Found {len(work_packages)} work packages to convert")

            # Clear existing domain data for this connection
            cursor.execute("""
                DELETE FROM issues 
                WHERE id LIKE %s
            """, (f"openproject:WorkPackages:{self.connection_id}:%",))

            converted_count = 0

            for wp in work_packages:
                try:
                    domain_issue = self._convert_work_package_to_issue(wp)
                    if domain_issue:
                        self._insert_domain_issue(cursor, domain_issue)
                        converted_count += 1

                except Exception as e:
                    self.logger.error(f"Failed to convert work package {wp.get('id')}: {e}")
                    continue

            connection.commit()
            self.logger.info(f"Converted {converted_count} issues")

        except Exception as e:
            self.logger.error(f"Issues conversion failed: {e}")
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def _convert_work_package_to_issue(self, wp: Dict) -> Optional[Dict]:
        """Convert individual work package to domain issue"""

        try:
            # Generate domain ID
            domain_id = f"openproject:WorkPackages:{self.connection_id}:{wp['id']}"

            # Map type
            original_type = wp.get('type_name', '') or 'Task'
            mapped_type = self.type_mappings.get(original_type, 'REQUIREMENT')

            # Map status  
            original_status = wp.get('status_name', '') or 'New'
            mapped_status = self.status_mappings.get(original_status, 'TODO')

            # Use closed flag if available
            if wp.get('status_is_closed'):
                mapped_status = 'DONE'

            # Calculate lead time
            lead_time_minutes = None
            if wp.get('created_at') and wp.get('updated_at'):
                try:
                    created = wp['created_at']
                    updated = wp['updated_at']
                    if isinstance(created, datetime) and isinstance(updated, datetime):
                        lead_time_minutes = int((updated - created).total_seconds() / 60)
                except Exception as e:
                    self.logger.debug(f"Lead time calculation failed: {e}")

            # Convert hours to minutes
            estimated_minutes = None
            if wp.get('estimated_hours'):
                estimated_minutes = int(wp['estimated_hours'] * 60)

            spent_minutes = None
            if wp.get('spent_hours'):
                spent_minutes = int(wp['spent_hours'] * 60)

            # Calculate remaining time
            remaining_minutes = None
            if estimated_minutes and spent_minutes:
                remaining_minutes = max(0, estimated_minutes - spent_minutes)

            # Determine resolution date
            resolution_date = None
            if mapped_status == 'DONE':
                resolution_date = wp.get('updated_at')

            # Generate URL
            project_identifier = wp.get('project_identifier') or wp.get('project_id', '')
            base_url = self.config['openproject']['base_url']
            issue_url = f"{base_url}/work_packages/{wp['id']}"

            # Build domain issue
            issue = {
                'id': domain_id,
                'issue_key': str(wp['id']),
                'url': issue_url,
                'title': wp.get('subject', ''),
                'description': wp.get('description', ''),
                'type': mapped_type,
                'original_type': original_type,
                'status': mapped_status,
                'original_status': original_status,
                'story_point': None,  # OpenProject doesn't have story points by default
                'priority': wp.get('priority_name', ''),
                'urgency': None,
                'component': wp.get('category_name', ''),
                'severity': None,
                'parent_issue_id': f"openproject:WorkPackages:{self.connection_id}:{wp['parent_id']}" if wp.get('parent_id') else None,
                'epic_key': '',  # OpenProject doesn't have epics by default
                'original_estimate_minutes': estimated_minutes,
                'time_spent_minutes': spent_minutes,
                'time_remaining_minutes': remaining_minutes,
                'creator_id': f"openproject:Users:{self.connection_id}:{wp['author_id']}" if wp.get('author_id') else None,
                'creator_name': wp.get('author_name', ''),
                'assignee_id': f"openproject:Users:{self.connection_id}:{wp['assignee_id']}" if wp.get('assignee_id') else None,
                'assignee_name': wp.get('assignee_name', ''),
                'created_date': wp.get('created_at'),
                'updated_date': wp.get('updated_at'),
                'resolution_date': resolution_date,
                'lead_time_minutes': lead_time_minutes,
                'original_project': wp.get('project_name', ''),
                'icon_url': None
            }

            return issue

        except Exception as e:
            self.logger.error(f"Failed to convert work package to issue: {e}")
            return None

    def _insert_domain_issue(self, cursor, issue_data: Dict):
        """Insert issue into domain table"""

        query = """
            INSERT INTO issues (
                id, issue_key, url, title, description, type, original_type,
                status, original_status, story_point, priority, urgency,
                component, severity, parent_issue_id, epic_key,
                original_estimate_minutes, time_spent_minutes, time_remaining_minutes,
                creator_id, creator_name, assignee_id, assignee_name,
                created_date, updated_date, resolution_date, lead_time_minutes,
                original_project, icon_url
            ) VALUES (
                %(id)s, %(issue_key)s, %(url)s, %(title)s, %(description)s,
                %(type)s, %(original_type)s, %(status)s, %(original_status)s,
                %(story_point)s, %(priority)s, %(urgency)s, %(component)s,
                %(severity)s, %(parent_issue_id)s, %(epic_key)s,
                %(original_estimate_minutes)s, %(time_spent_minutes)s,
                %(time_remaining_minutes)s, %(creator_id)s, %(creator_name)s,
                %(assignee_id)s, %(assignee_name)s, %(created_date)s,
                %(updated_date)s, %(resolution_date)s, %(lead_time_minutes)s,
                %(original_project)s, %(icon_url)s
            )
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                description = VALUES(description),
                status = VALUES(status),
                original_status = VALUES(original_status),
                priority = VALUES(priority),
                component = VALUES(component),
                parent_issue_id = VALUES(parent_issue_id),
                original_estimate_minutes = VALUES(original_estimate_minutes),
                time_spent_minutes = VALUES(time_spent_minutes),
                time_remaining_minutes = VALUES(time_remaining_minutes),
                assignee_id = VALUES(assignee_id),
                assignee_name = VALUES(assignee_name),
                updated_date = VALUES(updated_date),
                resolution_date = VALUES(resolution_date),
                lead_time_minutes = VALUES(lead_time_minutes)
        """

        cursor.execute(query, issue_data)

    def convert_boards(self):
        """Convert projects to domain boards table"""

        self.logger.info("Starting boards conversion")

        connection = self._get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT * FROM _tool_openproject_projects 
                WHERE connection_id = %s
            """, (self.connection_id,))

            projects = cursor.fetchall()

            # Clear existing domain data
            cursor.execute("""
                DELETE FROM boards 
                WHERE id LIKE %s
            """, (f"openproject:Projects:{self.connection_id}:%",))

            base_url = self.config['openproject']['base_url']

            for project in projects:
                board_url = f"{base_url}/projects/{project.get('identifier', project.get('id'))}"

                board_data = {
                    'id': f"openproject:Projects:{self.connection_id}:{project['id']}",
                    'name': project.get('name', ''),
                    'description': project.get('description', ''),
                    'url': board_url,
                    'created_date': project.get('created_at'),
                    'type': 'openproject'
                }

                query = """
                    INSERT INTO boards (
                        id, name, description, url, created_date, type
                    ) VALUES (
                        %(id)s, %(name)s, %(description)s, %(url)s, 
                        %(created_date)s, %(type)s
                    )
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        description = VALUES(description),
                        url = VALUES(url),
                        created_date = VALUES(created_date)
                """

                cursor.execute(query, board_data)

            connection.commit()
            self.logger.info(f"Converted {len(projects)} boards")

        except Exception as e:
            self.logger.error(f"Boards conversion failed: {e}")
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def convert_board_issues(self):
        """Create board-issue relationships"""

        self.logger.info("Starting board-issues conversion")

        connection = self._get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT id, project_id FROM _tool_openproject_work_packages 
                WHERE connection_id = %s AND project_id IS NOT NULL
            """, (self.connection_id,))

            work_packages = cursor.fetchall()

            # Clear existing relationships
            cursor.execute("""
                DELETE FROM board_issues 
                WHERE board_id LIKE %s
            """, (f"openproject:Projects:{self.connection_id}:%",))

            for wp in work_packages:
                board_issue_data = {
                    'board_id': f"openproject:Projects:{self.connection_id}:{wp['project_id']}",
                    'issue_id': f"openproject:WorkPackages:{self.connection_id}:{wp['id']}"
                }

                query = """
                    INSERT INTO board_issues (board_id, issue_id) 
                    VALUES (%(board_id)s, %(issue_id)s)
                    ON DUPLICATE KEY UPDATE board_id = board_id
                """

                cursor.execute(query, board_issue_data)

            connection.commit()
            self.logger.info(f"Created {len(work_packages)} board-issue relationships")

        except Exception as e:
            self.logger.error(f"Board-issues conversion failed: {e}")
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def convert_worklogs(self):
        """Convert time entries to domain worklogs"""

        self.logger.info("Starting worklogs conversion")

        connection = self._get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT * FROM _tool_openproject_time_entries 
                WHERE connection_id = %s
            """, (self.connection_id,))

            time_entries = cursor.fetchall()

            # Clear existing worklogs
            cursor.execute("""
                DELETE FROM issue_worklogs 
                WHERE id LIKE %s
            """, (f"openproject:TimeEntries:{self.connection_id}:%",))

            for entry in time_entries:
                # Convert hours to minutes
                time_spent_minutes = None
                if entry.get('hours'):
                    time_spent_minutes = int(entry['hours'] * 60)

                worklog_data = {
                    'id': f"openproject:TimeEntries:{self.connection_id}:{entry['id']}",
                    'author_id': f"openproject:Users:{self.connection_id}:{entry['user_id']}" if entry.get('user_id') else None,
                    'author_name': entry.get('user_name', ''),
                    'comment': entry.get('comment', ''),
                    'time_spent_minutes': time_spent_minutes,
                    'logged_date': entry.get('created_at'),
                    'started_date': entry.get('spent_on'),
                    'issue_id': f"openproject:WorkPackages:{self.connection_id}:{entry['work_package_id']}" if entry.get('work_package_id') else None
                }

                query = """
                    INSERT INTO issue_worklogs (
                        id, author_id, author_name, comment, time_spent_minutes,
                        logged_date, started_date, issue_id
                    ) VALUES (
                        %(id)s, %(author_id)s, %(author_name)s, %(comment)s, %(time_spent_minutes)s,
                        %(logged_date)s, %(started_date)s, %(issue_id)s
                    )
                    ON DUPLICATE KEY UPDATE
                        author_name = VALUES(author_name),
                        comment = VALUES(comment),
                        time_spent_minutes = VALUES(time_spent_minutes),
                        logged_date = VALUES(logged_date),
                        started_date = VALUES(started_date)
                """

                cursor.execute(query, worklog_data)

            connection.commit()
            self.logger.info(f"Converted {len(time_entries)} worklogs")

        except Exception as e:
            self.logger.error(f"Worklogs conversion failed: {e}")
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def convert_sprints(self):
        """Convert versions to domain sprints table"""

        self.logger.info("Starting sprints conversion")

        connection = self._get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT * FROM _tool_openproject_versions 
                WHERE connection_id = %s
            """, (self.connection_id,))

            versions = cursor.fetchall()

            # Clear existing sprints
            cursor.execute("""
                DELETE FROM sprints 
                WHERE id LIKE %s
            """, (f"openproject:Versions:{self.connection_id}:%",))

            base_url = self.config['openproject']['base_url']

            for version in versions:
                # Map version status to sprint status
                status_mapping = {
                    'open': 'active',
                    'locked': 'closed',
                    'closed': 'closed'
                }

                sprint_status = status_mapping.get(version.get('status', '').lower(), 'active')

                sprint_url = f"{base_url}/versions/{version['id']}"

                sprint_data = {
                    'id': f"openproject:Versions:{self.connection_id}:{version['id']}",
                    'name': version.get('name', ''),
                    'url': sprint_url,
                    'status': sprint_status,
                    'started_date': version.get('created_at'),  # Use created as started
                    'ended_date': version.get('due_date'),
                    'completed_date': version.get('updated_at') if sprint_status == 'closed' else None,
                    'original_board_id': f"openproject:Projects:{self.connection_id}:{version['project_id']}" if version.get('project_id') else None
                }

                query = """
                    INSERT INTO sprints (
                        id, name, url, status, started_date, ended_date, 
                        completed_date, original_board_id
                    ) VALUES (
                        %(id)s, %(name)s, %(url)s, %(status)s, %(started_date)s,
                        %(ended_date)s, %(completed_date)s, %(original_board_id)s
                    )
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        url = VALUES(url),
                        status = VALUES(status),
                        started_date = VALUES(started_date),
                        ended_date = VALUES(ended_date),
                        completed_date = VALUES(completed_date),
                        original_board_id = VALUES(original_board_id)
                """

                cursor.execute(query, sprint_data)

            connection.commit()
            self.logger.info(f"Converted {len(versions)} sprints")

        except Exception as e:
            self.logger.error(f"Sprints conversion failed: {e}")
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def convert_sprint_issues(self):
        """Create sprint-issue relationships based on versions"""

        self.logger.info("Starting sprint-issues conversion")

        connection = self._get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT id, version_id FROM _tool_openproject_work_packages 
                WHERE connection_id = %s AND version_id IS NOT NULL
            """, (self.connection_id,))

            work_packages = cursor.fetchall()

            # Clear existing relationships
            cursor.execute("""
                DELETE FROM sprint_issues 
                WHERE sprint_id LIKE %s
            """, (f"openproject:Versions:{self.connection_id}:%",))

            for wp in work_packages:
                sprint_issue_data = {
                    'sprint_id': f"openproject:Versions:{self.connection_id}:{wp['version_id']}",
                    'issue_id': f"openproject:WorkPackages:{self.connection_id}:{wp['id']}"
                }

                query = """
                    INSERT INTO sprint_issues (sprint_id, issue_id) 
                    VALUES (%(sprint_id)s, %(issue_id)s)
                    ON DUPLICATE KEY UPDATE sprint_id = sprint_id
                """

                cursor.execute(query, sprint_issue_data)

            connection.commit()
            self.logger.info(f"Created {len(work_packages)} sprint-issue relationships")

        except Exception as e:
            self.logger.error(f"Sprint-issues conversion failed: {e}")
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def convert_accounts(self):
        """Convert users to domain accounts table"""

        self.logger.info("Starting accounts conversion")

        connection = self._get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT * FROM _tool_openproject_users 
                WHERE connection_id = %s
            """, (self.connection_id,))

            users = cursor.fetchall()

            # Clear existing accounts
            cursor.execute("""
                DELETE FROM accounts 
                WHERE id LIKE %s
            """, (f"openproject:Users:{self.connection_id}:%",))

            for user in users:
                # Map status to numeric
                status_mapping = {
                    'active': 1,
                    'registered': 1,
                    'locked': 0,
                    'inactive': 0
                }

                status_num = status_mapping.get(user.get('status', '').lower(), 1)

                # Construct full name
                full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                if not full_name:
                    full_name = user.get('name', user.get('login', ''))

                account_data = {
                    'id': f"openproject:Users:{self.connection_id}:{user['id']}",
                    'full_name': full_name,
                    'user_name': user.get('login', ''),
                    'email': user.get('mail', ''),
                    'avatar_url': user.get('avatar_url', ''),
                    'organization': None,  # OpenProject doesn't have organization field
                    'created_date': user.get('created_at'),
                    'status': status_num
                }

                query = """
                    INSERT INTO accounts (
                        id, full_name, user_name, email, avatar_url,
                        organization, created_date, status
                    ) VALUES (
                        %(id)s, %(full_name)s, %(user_name)s, %(email)s,
                        %(avatar_url)s, %(organization)s, %(created_date)s, %(status)s
                    )
                    ON DUPLICATE KEY UPDATE
                        full_name = VALUES(full_name),
                        user_name = VALUES(user_name),
                        email = VALUES(email),
                        avatar_url = VALUES(avatar_url),
                        status = VALUES(status)
                """

                cursor.execute(query, account_data)

            connection.commit()
            self.logger.info(f"Converted {len(users)} accounts")

        except Exception as e:
            self.logger.error(f"Accounts conversion failed: {e}")
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def run_conversion(self):
        """Run complete conversion process"""

        self.logger.info("Starting OpenProject data conversion")

        conversion_stats = {
            'issues': 0,
            'boards': 0,
            'board_issues': 0,
            'sprints': 0,
            'sprint_issues': 0,
            'worklogs': 0,
            'accounts': 0
        }

        try:
            # Ensure domain tables exist
            self._ensure_domain_tables_exist()

            # Convert core entities
            self.logger.info("=== Converting Core Entities ===")
            self.convert_boards()
            conversion_stats['boards'] = 1

            self.convert_accounts()
            conversion_stats['accounts'] = 1

            self.convert_sprints()
            conversion_stats['sprints'] = 1

            # Convert main entities
            self.logger.info("=== Converting Main Entities ===")
            self.convert_issues()
            conversion_stats['issues'] = 1

            self.convert_worklogs()
            conversion_stats['worklogs'] = 1

            # Convert relationships
            self.logger.info("=== Converting Relationships ===")
            self.convert_board_issues()
            conversion_stats['board_issues'] = 1

            self.convert_sprint_issues()
            conversion_stats['sprint_issues'] = 1

            self.logger.info("OpenProject data conversion completed successfully")
            return conversion_stats

        except Exception as e:
            self.logger.error(f"Data conversion failed: {e}")
            raise

# CLI interface for the converter
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='OpenProject Domain Converter')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    # Create converter
    converter = OpenProjectConverter(args.config)

    if args.verbose:
        converter.logger.setLevel(logging.DEBUG)

    # Run conversion
    try:
        stats = converter.run_conversion()
        print("Conversion completed successfully")
    except Exception as e:
        print(f"Conversion failed: {e}")
        exit(1)
```

### Step 9: Create Pipeline Orchestrator

Create `pipeline.py`:
```python
#!/usr/bin/env python3
"""
OpenProject DevLake Pipeline - Complete data pipeline orchestrator
"""

import sys
import os
from pathlib import Path
import argparse
import yaml
import logging
from datetime import datetime
import time

# Add project modules to path
sys.path.append(str(Path(__file__).parent))

from collectors.openproject_collector import OpenProjectCollector
from extractors.openproject_extractor import OpenProjectExtractor  
from converters.openproject_converter import OpenProjectConverter

class OpenProjectPipeline:
    """Orchestrates the complete OpenProject data pipeline"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.connection_id = self.config['openproject']['connection_id']

        # Initialize components
        self.collector = OpenProjectCollector(config_path)
        self.extractor = OpenProjectExtractor(config_path)
        self.converter = OpenProjectConverter(config_path)

        # Setup logging
        self.logger = self._setup_logging()

        self.logger.info("OpenProject Pipeline initialized")

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_config = self.config['logging']

        logger = logging.getLogger(f"OpenProjectPipeline.{self.connection_id}")
        logger.setLevel(getattr(logging, log_config['level']))

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # File handler
        fh = logging.handlers.RotatingFileHandler(
            log_config['file'],
            maxBytes=log_config['max_bytes'],
            backupCount=log_config['backup_count']
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        return logger

    def run_full_pipeline(self, project_ids: list = None, incremental: bool = True, 
                         skip_collection: bool = False, skip_extraction: bool = False,
                         skip_conversion: bool = False):
        """Run the complete data pipeline"""

        start_time = datetime.now()
        self.logger.info("=" * 60)
        self.logger.info("Starting OpenProject data pipeline")
        self.logger.info(f"Connection ID: {self.connection_id}")
        self.logger.info(f"Incremental sync: {incremental}")
        self.logger.info(f"Project IDs: {project_ids or 'All'}")
        self.logger.info("=" * 60)

        pipeline_stats = {
            'collection': {},
            'extraction': {},
            'conversion': {},
            'duration_seconds': 0,
            'success': False
        }

        try:
            # Stage 1: Data Collection
            if not skip_collection:
                self.logger.info("🔄 STAGE 1: DATA COLLECTION")
                self.logger.info("-" * 40)
                stage_start = time.time()

                collection_config = self.config.get('collection', {})
                target_projects = project_ids or collection_config.get('projects', [])

                pipeline_stats['collection'] = self.collector.run_collection(
                    project_ids=target_projects,
                    incremental=incremental
                )

                stage_duration = time.time() - stage_start
                self.logger.info(f"✅ Collection completed in {stage_duration:.2f} seconds")
                self.logger.info("")
            else:
                self.logger.info("⏭️  STAGE 1: SKIPPED - Data Collection")
                self.logger.info("")

            # Stage 2: Data Extraction
            if not skip_extraction:
                self.logger.info("🔄 STAGE 2: DATA EXTRACTION")
                self.logger.info("-" * 40)
                stage_start = time.time()

                pipeline_stats['extraction'] = self.extractor.run_extraction()

                stage_duration = time.time() - stage_start
                self.logger.info(f"✅ Extraction completed in {stage_duration:.2f} seconds")
                self.logger.info("")
            else:
                self.logger.info("⏭️  STAGE 2: SKIPPED - Data Extraction")
                self.logger.info("")

            # Stage 3: Domain Conversion
            if not skip_conversion:
                self.logger.info("🔄 STAGE 3: DOMAIN CONVERSION")
                self.logger.info("-" * 40)
                stage_start = time.time()

                pipeline_stats['conversion'] = self.converter.run_conversion()

                stage_duration = time.time() - stage_start
                self.logger.info(f"✅ Conversion completed in {stage_duration:.2f} seconds")
                self.logger.info("")
            else:
                self.logger.info("⏭️  STAGE 3: SKIPPED - Domain Conversion")
                self.logger.info("")

            # Calculate total duration
            total_duration = (datetime.now() - start_time).total_seconds()
            pipeline_stats['duration_seconds'] = total_duration
            pipeline_stats['success'] = True

            # Final summary
            self.logger.info("=" * 60)
            self.logger.info("🎉 PIPELINE COMPLETED SUCCESSFULLY")
            self.logger.info("-" * 40)
            self.logger.info(f"Total duration: {total_duration:.2f} seconds")

            if pipeline_stats['collection']:
                collection_total = sum(pipeline_stats['collection'].values())
                self.logger.info(f"Collection: {collection_total} records")

            self.logger.info("Extraction: Completed")
            self.logger.info("Conversion: Completed")
            self.logger.info("=" * 60)

            return pipeline_stats

        except Exception as e:
            total_duration = (datetime.now() - start_time).total_seconds()
            pipeline_stats['duration_seconds'] = total_duration
            pipeline_stats['success'] = False

            self.logger.error("=" * 60)
            self.logger.error("❌ PIPELINE FAILED")
            self.logger.error("-" * 40)
            self.logger.error(f"Error: {e}")
            self.logger.error(f"Duration before failure: {total_duration:.2f} seconds")
            self.logger.error("=" * 60)

            raise

    def run_collection_only(self, project_ids: list = None, incremental: bool = True):
        """Run only the data collection stage"""
        return self.run_full_pipeline(
            project_ids=project_ids,
            incremental=incremental,
            skip_extraction=True,
            skip_conversion=True
        )

    def run_extraction_only(self):
        """Run only the data extraction stage"""
        return self.run_full_pipeline(
            skip_collection=True,
            skip_conversion=True
        )

    def run_conversion_only(self):
        """Run only the domain conversion stage"""
        return self.run_full_pipeline(
            skip_collection=True,
            skip_extraction=True
        )

def main():
    """Main CLI interface"""

    parser = argparse.ArgumentParser(
        description='OpenProject DevLake Data Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline with incremental sync
  python pipeline.py --incremental

  # Run full pipeline with full sync for specific projects
  python pipeline.py --projects 1 2 3 --full

  # Run only collection stage
  python pipeline.py --collection-only --projects 1

  # Run only extraction and conversion (after collection)
  python pipeline.py --skip-collection

  # Run with verbose logging
  python pipeline.py --verbose --incremental
        """
    )

    parser.add_argument('--config', default='config.yaml',
                       help='Configuration file path (default: config.yaml)')

    parser.add_argument('--projects', nargs='+', type=int,
                       help='Specific project IDs to sync (default: all configured projects)')

    parser.add_argument('--incremental', action='store_true',
                       help='Run incremental sync (only new/updated data)')

    parser.add_argument('--full', action='store_true', 
                       help='Force full sync (all data)')

    parser.add_argument('--collection-only', action='store_true',
                       help='Run only data collection stage')

    parser.add_argument('--extraction-only', action='store_true',
                       help='Run only data extraction stage')

    parser.add_argument('--conversion-only', action='store_true',
                       help='Run only domain conversion stage')

    parser.add_argument('--skip-collection', action='store_true',
                       help='Skip data collection stage')

    parser.add_argument('--skip-extraction', action='store_true',
                       help='Skip data extraction stage')

    parser.add_argument('--skip-conversion', action='store_true',
                       help='Skip domain conversion stage')

    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')

    args = parser.parse_args()

    # Validate arguments
    if args.incremental and args.full:
        print("Error: Cannot specify both --incremental and --full")
        sys.exit(1)

    exclusive_stages = [args.collection_only, args.extraction_only, args.conversion_only]
    if sum(exclusive_stages) > 1:
        print("Error: Cannot specify multiple stage-only options")
        sys.exit(1)

    # Set defaults
    incremental = args.incremental or not args.full

    try:
        # Create pipeline
        pipeline = OpenProjectPipeline(args.config)

        # Set verbose logging if requested
        if args.verbose:
            pipeline.logger.setLevel(logging.DEBUG)
            pipeline.collector.logger.setLevel(logging.DEBUG)
            pipeline.extractor.logger.setLevel(logging.DEBUG)
            pipeline.converter.logger.setLevel(logging.DEBUG)

        # Run appropriate pipeline stage(s)
        if args.collection_only:
            stats = pipeline.run_collection_only(args.projects, incremental)
        elif args.extraction_only:
            stats = pipeline.run_extraction_only()
        elif args.conversion_only:
            stats = pipeline.run_conversion_only()
        else:
            stats = pipeline.run_full_pipeline(
                project_ids=args.projects,
                incremental=incremental,
                skip_collection=args.skip_collection,
                skip_extraction=args.skip_extraction,
                skip_conversion=args.skip_conversion
            )

        # Print final summary
        if stats['success']:
            print(f"\n✅ Pipeline completed successfully in {stats['duration_seconds']:.2f} seconds")
            sys.exit(0)
        else:
            print(f"\n❌ Pipeline failed after {stats['duration_seconds']:.2f} seconds")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏹️  Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

This completes the core pipeline implementation. Next, I'll create the Grafana configuration and automation scripts.
