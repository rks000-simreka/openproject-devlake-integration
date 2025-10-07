#!/usr/bin/env python3
"""
OpenProject Domain Converter - Converts tool-layer data to DevLake domain tables
"""

import mysql.connector
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import logging.handlers
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
            'Story': 'REQUIREMENT',
            'Summary task': 'REQUIREMENT',
            'Phase': 'REQUIREMENT',
            'Milestone': 'REQUIREMENT'
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
        self.logger = self._setup_logging()
        self.logger.info("OpenProject Converter initialized")

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_config = self.config['logging']

        logger = logging.getLogger(f"{__name__}.{self.connection_id}")
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

    def _get_db_connection(self):
        """Get database connection"""
        return mysql.connector.connect(**self.db_config)

    def _ensure_domain_tables_exist(self):
        """Check that DevLake domain tables exist (they should already exist in DevLake)"""
        
        connection = self._get_db_connection()
        cursor = connection.cursor()
        
        required_tables = ['issues', 'boards', 'board_issues', 'issue_worklogs', 'accounts']
        
        try:
            for table in required_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table} LIMIT 1")
                cursor.fetchone()  # Consume the result
                self.logger.debug(f"✓ {table} table exists")
            
            self.logger.info("All required domain tables exist")
            
        except Exception as e:
            self.logger.error(f"Domain table check failed: {e}")
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
                LEFT JOIN _tool_openproject_projects p ON wp.project_id = p.id AND wp.connection_id = p.connection_id
                LEFT JOIN _tool_openproject_statuses s ON wp.status_id = s.id AND wp.connection_id = s.connection_id
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
                    issue_data = self._convert_work_package_to_issue(wp)
                    if issue_data:
                        self._insert_domain_issue(cursor, issue_data)
                        converted_count += 1
                        
                        if converted_count % 100 == 0:
                            self.logger.info(f"Converted {converted_count} issues...")
                            
                except Exception as e:
                    self.logger.error(f"Failed to convert work package {wp.get('id')}: {e}")
                    continue

            connection.commit()
            self.logger.info(f"Converted {converted_count} issues")
            return converted_count

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
                        delta = updated - created
                        lead_time_minutes = int(delta.total_seconds() / 60)
                except:
                    pass

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
                'issue_key': f"WP-{wp['id']}",
                'url': issue_url,
                'title': wp.get('subject', ''),
                'description': wp.get('description', ''),
                'type': mapped_type,
                'original_type': original_type,
                'status': mapped_status,
                'original_status': original_status,
                'story_point': estimated_minutes,
                'resolution_date': resolution_date,
                'created_date': wp.get('created_at'),
                'updated_date': wp.get('updated_at'),
                'lead_time_minutes': lead_time_minutes,
                'parent_issue_id': f"openproject:WorkPackages:{self.connection_id}:{wp['parent_id']}" if wp.get('parent_id') else None,
                'priority': wp.get('priority_name', ''),

                'creator_id': f"openproject:Users:{self.connection_id}:{wp['author_id']}" if wp.get('author_id') else None,
                'creator_name': wp.get('author_name', ''),
                'assignee_id': f"openproject:Users:{self.connection_id}:{wp['assignee_id']}" if wp.get('assignee_id') else None,
                'assignee_name': wp.get('assignee_name', ''),
                'severity': wp.get('priority_name', ''),
                'component': wp.get('category_name', ''),
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
                status, original_status, story_point, resolution_date,
                created_date, updated_date, lead_time_minutes, parent_issue_id,
                priority, creator_id, creator_name,
                assignee_id, assignee_name, severity, component,
                original_project, icon_url
            ) VALUES (
                %(id)s, %(issue_key)s, %(url)s, %(title)s, %(description)s,
                %(type)s, %(original_type)s, %(status)s, %(original_status)s,
                %(story_point)s, %(resolution_date)s, %(created_date)s,
                %(updated_date)s, %(lead_time_minutes)s, %(parent_issue_id)s,
                %(priority)s, %(creator_id)s, %(creator_name)s,
                %(assignee_id)s, %(assignee_name)s, %(severity)s, %(component)s,
                %(original_project)s, %(icon_url)s
            )
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                description = VALUES(description),
                type = VALUES(type),
                status = VALUES(status),
                story_point = VALUES(story_point),
                resolution_date = VALUES(resolution_date),
                updated_date = VALUES(updated_date),
                assignee_id = VALUES(assignee_id),
                assignee_name = VALUES(assignee_name),
                priority = VALUES(priority),
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
                    INSERT INTO boards (id, name, description, url, created_date, type)
                    VALUES (%(id)s, %(name)s, %(description)s, %(url)s, %(created_date)s, %(type)s)
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        description = VALUES(description),
                        url = VALUES(url),
                        created_date = VALUES(created_date)
                """

                cursor.execute(query, board_data)

            connection.commit()
            self.logger.info(f"Converted {len(projects)} boards")
            return len(projects)

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
                    ON DUPLICATE KEY UPDATE
                        board_id = VALUES(board_id)
                """

                cursor.execute(query, board_issue_data)

            connection.commit()
            self.logger.info(f"Created {len(work_packages)} board-issue relationships")
            return len(work_packages)

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

            # Clear existing domain data
            cursor.execute("""
                DELETE FROM issue_worklogs 
                WHERE id LIKE %s
            """, (f"openproject:TimeEntries:{self.connection_id}:%",))

            for te in time_entries:
                # Convert hours to minutes
                time_spent_minutes = None
                if te.get('hours'):
                    time_spent_minutes = int(te['hours'] * 60)

                worklog_data = {
                    'id': f"openproject:TimeEntries:{self.connection_id}:{te['id']}",
                    'author_id': f"openproject:Users:{self.connection_id}:{te['user_id']}" if te.get('user_id') else None,
                    'comment': te.get('comment', ''),
                    'time_spent_minutes': time_spent_minutes,
                    'logged_date': te.get('created_at'),
                    'started_date': te.get('spent_on'),
                    'issue_id': f"openproject:WorkPackages:{self.connection_id}:{te['work_package_id']}" if te.get('work_package_id') else None
                }

                query = """
                    INSERT INTO issue_worklogs (
                        id, author_id, comment, time_spent_minutes, 
                        logged_date, started_date, issue_id
                    ) VALUES (
                        %(id)s, %(author_id)s, %(comment)s, %(time_spent_minutes)s,
                        %(logged_date)s, %(started_date)s, %(issue_id)s
                    )
                    ON DUPLICATE KEY UPDATE
                        comment = VALUES(comment),
                        time_spent_minutes = VALUES(time_spent_minutes),
                        logged_date = VALUES(logged_date),
                        started_date = VALUES(started_date)
                """

                cursor.execute(query, worklog_data)

            connection.commit()
            self.logger.info(f"Converted {len(time_entries)} worklogs")
            return len(time_entries)

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
                SELECT v.*, p.identifier as project_identifier 
                FROM _tool_openproject_versions v
                LEFT JOIN _tool_openproject_projects p ON v.project_id = p.id AND v.connection_id = p.connection_id
                WHERE v.connection_id = %s
            """, (self.connection_id,))

            versions = cursor.fetchall()

            # Clear existing domain data
            cursor.execute("""
                DELETE FROM sprints 
                WHERE id LIKE %s
            """, (f"openproject:Versions:{self.connection_id}:%",))

            base_url = self.config['openproject']['base_url']

            for version in versions:
                # Generate sprint URL
                project_identifier = version.get('project_identifier', version.get('project_id', ''))
                sprint_url = f"{base_url}/projects/{project_identifier}/versions/{version['id']}"

                # Map status
                status_map = {
                    'open': 'active',
                    'locked': 'closed',
                    'closed': 'closed'
                }
                status = status_map.get(version.get('status', '').lower(), 'active')

                sprint_data = {
                    'id': f"openproject:Versions:{self.connection_id}:{version['id']}",
                    'name': version.get('name', ''),
                    'url': sprint_url,
                    'status': status,
                    'started_date': version.get('created_at'),
                    'ended_date': version.get('due_date'),
                    'completed_date': version.get('updated_at') if status == 'closed' else None,
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
                        ended_date = VALUES(ended_date),
                        completed_date = VALUES(completed_date)
                """

                cursor.execute(query, sprint_data)

            connection.commit()
            self.logger.info(f"Converted {len(versions)} sprints")
            return len(versions)

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
                    ON DUPLICATE KEY UPDATE
                        sprint_id = VALUES(sprint_id)
                """

                cursor.execute(query, sprint_issue_data)

            connection.commit()
            self.logger.info(f"Created {len(work_packages)} sprint-issue relationships")
            return len(work_packages)

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

            # Clear existing domain data
            cursor.execute("""
                DELETE FROM accounts 
                WHERE id LIKE %s
            """, (f"openproject:Users:{self.connection_id}:%",))

            for user in users:
                # Determine status
                status = 1  # Active
                if user.get('status') and user['status'].lower() in ['locked', 'closed', 'inactive']:
                    status = 0  # Inactive

                account_data = {
                    'id': f"openproject:Users:{self.connection_id}:{user['id']}",
                    'email': user.get('mail', ''),
                    'full_name': user.get('name', ''),
                    'user_name': user.get('login', ''),
                    'avatar_url': user.get('avatar', ''),
                    'status': status
                }

                query = """
                    INSERT INTO accounts (
                        id, email, full_name, user_name, avatar_url, status
                    ) VALUES (
                        %(id)s, %(email)s, %(full_name)s, %(user_name)s, 
                        %(avatar_url)s, %(status)s
                    )
                    ON DUPLICATE KEY UPDATE
                        email = VALUES(email),
                        full_name = VALUES(full_name),
                        user_name = VALUES(user_name),
                        avatar_url = VALUES(avatar_url),
                        status = VALUES(status)
                """

                cursor.execute(query, account_data)

            connection.commit()
            self.logger.info(f"Converted {len(users)} accounts")
            return len(users)

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
            'worklogs': 0,
            'sprints': 0,
            'sprint_issues': 0,
            'accounts': 0
        }

        try:
            # Check domain tables exist
            self.logger.info("=== Checking Domain Tables ===")
            self._ensure_domain_tables_exist()

            # Convert core entities
            self.logger.info("=== Converting Core Domain Entities ===")
            conversion_stats['accounts'] = self.convert_accounts()
            conversion_stats['boards'] = self.convert_boards()
            conversion_stats['issues'] = self.convert_issues()
            conversion_stats['worklogs'] = self.convert_worklogs()

            # Convert relationships
            self.logger.info("=== Converting Relationships ===")
            conversion_stats['board_issues'] = self.convert_board_issues()

            # Convert sprints (if versions exist)
            try:
                conversion_stats['sprints'] = self.convert_sprints()
                conversion_stats['sprint_issues'] = self.convert_sprint_issues()
            except Exception as e:
                self.logger.warning(f"Sprint conversion failed (versions might not exist): {e}")

            self.logger.info("=== Conversion Statistics ===")
            for entity, count in conversion_stats.items():
                self.logger.info(f"{entity.title().replace('_', ' ')}: {count}")

            total_converted = sum(conversion_stats.values())
            self.logger.info(f"Total domain records: {total_converted}")

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
        print("\n" + "=" * 50)
        print("Conversion Summary")
        print("=" * 50)
        for entity, count in stats.items():
            print(f"{entity.title().replace('_', ' ')}: {count}")
        print(f"\nTotal domain records: {sum(stats.values())}")
        print("=" * 50)
    except Exception as e:
        print(f"\n✗ Conversion failed: {e}")
        exit(1)