#!/usr/bin/env python3
"""
OpenProject Data Extractor - Transforms raw data into tool-layer tables
"""

import json
import mysql.connector
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import logging.handlers
import re
import yaml

class OpenProjectExtractor:
    """Extracts raw OpenProject API data into tool-layer tables"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.connection_id = self.config['openproject']['connection_id']
        self.db_config = self.config['database']

        # Setup logging
        self.logger = self._setup_logging()
        self.logger.info("OpenProject Extractor initialized")

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

    def _parse_duration(self, duration_str: Optional[str]) -> Optional[float]:
        """Parse ISO 8601 duration (PT8H30M) to hours"""
        if not duration_str:
            return None

        # Parse ISO 8601 duration format PT#H#M#S
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?'
        match = re.match(pattern, duration_str)

        if not match:
            # Try simple format like "8:30" or "8.5"
            try:
                if ':' in duration_str:
                    parts = duration_str.split(':')
                    hours = float(parts[0])
                    minutes = float(parts[1]) if len(parts) > 1 else 0
                    return hours + (minutes / 60)
                else:
                    return float(duration_str)
            except ValueError:
                return None

        hours = float(match.group(1)) if match.group(1) else 0
        minutes = float(match.group(2)) if match.group(2) else 0
        seconds = float(match.group(3)) if match.group(3) else 0

        return hours + (minutes / 60) + (seconds / 3600)

    def _extract_link_info(self, link_data: Dict) -> tuple:
        """Extract ID and title from _links data"""
        if not link_data:
            return None, None

        href = link_data.get('href', '')
        title = link_data.get('title', '')

        # Extract ID from href
        link_id = None
        if href:
            # Extract ID from URL like /api/v3/users/5
            parts = href.split('/')
            if parts:
                try:
                    link_id = int(parts[-1])
                except (ValueError, IndexError):
                    pass

        return link_id, title

    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object"""
        if not datetime_str:
            return None

        try:
            # Handle ISO format with timezone
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str[:-1] + '+00:00'

            # Parse with timezone
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse date string to YYYY-MM-DD format"""
        if not date_str:
            return None

        try:
            # If it's already in YYYY-MM-DD format
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                return date_str

            # Parse full datetime and extract date
            dt = self._parse_datetime(date_str)
            return dt.date().isoformat() if dt else None
        except:
            return None

    def extract_work_packages(self):
        """Extract work packages from raw data"""

        self.logger.info("Starting work packages extraction")

        connection = self._get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            # Clear existing tool data for this connection
            cursor.execute("""
                DELETE FROM _tool_openproject_work_packages 
                WHERE connection_id = %s
            """, (self.connection_id,))

            # Get count of raw records first
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM _raw_openproject_api_work_packages 
                WHERE connection_id = %s AND data IS NOT NULL
            """, (self.connection_id,))
            
            total_records = cursor.fetchone()['total']
            self.logger.info(f"Found {total_records} raw work package records to process")

            # Process in smaller batches to avoid memory issues
            batch_size = 50
            offset = 0
            extracted_count = 0
            processed_wp_ids = set()

            while offset < total_records:
                # Get batch of raw work packages data
                cursor.execute("""
                    SELECT id, data, created_at, project_id
                    FROM _raw_openproject_api_work_packages 
                    WHERE connection_id = %s AND data IS NOT NULL
                    LIMIT %s OFFSET %s
                """, (self.connection_id, batch_size, offset))

                raw_records = cursor.fetchall()
                
                if not raw_records:
                    break
                
                self.logger.info(f"Processing batch {offset//batch_size + 1}: {len(raw_records)} records")

                for raw_record in raw_records:
                    try:
                        data = json.loads(raw_record['data'])
                        elements = data.get('_embedded', {}).get('elements', [])

                        for element in elements:
                            wp_id = element.get('id')
                            if not wp_id or wp_id in processed_wp_ids:
                                continue

                            wp_data = self._extract_work_package_data(element)
                            if wp_data:
                                self._insert_work_package(cursor, wp_data)
                                processed_wp_ids.add(wp_id)
                                extracted_count += 1
                                
                                # Log progress every 100 work packages
                                if extracted_count % 100 == 0:
                                    self.logger.info(f"Processed {extracted_count} work packages...")

                    except (json.JSONDecodeError, KeyError) as e:
                        self.logger.error(f"Failed to process raw record: {e}")
                        continue

                # Commit batch
                connection.commit()
                offset += batch_size

            self.logger.info(f"Extracted {extracted_count} unique work packages")
            return extracted_count

        except Exception as e:
            self.logger.error(f"Work package extraction failed: {e}")
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def _extract_work_package_data(self, wp_data: Dict) -> Optional[Dict]:
        """Extract individual work package data"""

        try:
            # Basic fields
            wp = {
                'connection_id': self.connection_id,
                'id': wp_data.get('id'),
                'subject': wp_data.get('subject', ''),
                'start_date': self._parse_date(wp_data.get('startDate')),
                'due_date': self._parse_date(wp_data.get('dueDate')),
                'created_at': self._parse_datetime(wp_data.get('createdAt')),
                'updated_at': self._parse_datetime(wp_data.get('updatedAt'))
            }

            # Description handling
            description = wp_data.get('description')
            if description and isinstance(description, dict):
                wp['description'] = description.get('raw', '')
            else:
                wp['description'] = description or ''

            # Duration fields
            wp['estimated_hours'] = self._parse_duration(
                wp_data.get('estimatedTime')
            )
            wp['spent_hours'] = self._parse_duration(
                wp_data.get('spentTime')
            )

            # Extract linked data
            links = wp_data.get('_links', {})

            # Project info
            project_id, project_title = self._extract_link_info(
                links.get('project')
            )
            wp['project_id'] = project_id
            wp['project_name'] = project_title

            # Extract project identifier from href if available
            project_link = links.get('project', {})
            if project_link.get('href'):
                # Try to get identifier from the project data
                wp['project_identifier'] = None  # Will be filled later if needed

            # Type info
            type_id, type_title = self._extract_link_info(
                links.get('type')
            )
            wp['type_id'] = type_id
            wp['type_name'] = type_title

            # Status info
            status_id, status_title = self._extract_link_info(
                links.get('status')
            )
            wp['status_id'] = status_id
            wp['status_name'] = status_title
            wp['status_is_closed'] = False  # Will be updated during status extraction

            # Priority info
            priority_id, priority_title = self._extract_link_info(
                links.get('priority')
            )
            wp['priority_id'] = priority_id
            wp['priority_name'] = priority_title

            # Assignee info
            assignee_id, assignee_title = self._extract_link_info(
                links.get('assignee')
            )
            wp['assignee_id'] = assignee_id
            wp['assignee_name'] = assignee_title
            wp['assignee_login'] = None  # Will be filled from user data

            # Responsible info
            responsible_id, responsible_title = self._extract_link_info(
                links.get('responsible')
            )
            wp['responsible_id'] = responsible_id
            wp['responsible_name'] = responsible_title
            wp['responsible_login'] = None  # Will be filled from user data

            # Author info
            author_id, author_title = self._extract_link_info(
                links.get('author')
            )
            wp['author_id'] = author_id
            wp['author_name'] = author_title
            wp['author_login'] = None  # Will be filled from user data

            # Parent info
            parent_id, _ = self._extract_link_info(
                links.get('parent')
            )
            wp['parent_id'] = parent_id

            # Version info (sprint equivalent)
            version_id, version_title = self._extract_link_info(
                links.get('version')
            )
            wp['version_id'] = version_id
            wp['version_name'] = version_title

            # Category info
            category_id, category_title = self._extract_link_info(
                links.get('category')
            )
            wp['category_id'] = category_id
            wp['category_name'] = category_title

            # Extract custom fields
            custom_fields = {}
            for key, value in wp_data.items():
                if key.startswith('customField'):
                    custom_fields[key] = value

            wp['custom_fields'] = json.dumps(custom_fields) if custom_fields else None

            # Store all fields as JSON for reference
            wp['all_fields'] = json.dumps(wp_data)

            return wp

        except Exception as e:
            self.logger.error(f"Failed to extract work package data: {e}")
            return None

    def _insert_work_package(self, cursor, wp_data: Dict):
        """Insert work package into tool table"""

        query = """
            INSERT INTO _tool_openproject_work_packages (
                connection_id, id, subject, description, start_date, due_date,
                created_at, updated_at, estimated_hours, spent_hours,
                project_id, project_name, project_identifier,
                type_id, type_name, status_id, status_name, status_is_closed,
                priority_id, priority_name, assignee_id, assignee_name, assignee_login,
                responsible_id, responsible_name, responsible_login,
                author_id, author_name, author_login, parent_id,
                version_id, version_name, category_id, category_name,
                custom_fields, all_fields
            ) VALUES (
                %(connection_id)s, %(id)s, %(subject)s, %(description)s, 
                %(start_date)s, %(due_date)s, %(created_at)s, %(updated_at)s,
                %(estimated_hours)s, %(spent_hours)s, %(project_id)s, %(project_name)s,
                %(project_identifier)s, %(type_id)s, %(type_name)s, %(status_id)s,
                %(status_name)s, %(status_is_closed)s, %(priority_id)s, %(priority_name)s,
                %(assignee_id)s, %(assignee_name)s, %(assignee_login)s,
                %(responsible_id)s, %(responsible_name)s, %(responsible_login)s,
                %(author_id)s, %(author_name)s, %(author_login)s, %(parent_id)s,
                %(version_id)s, %(version_name)s,
                %(category_id)s, %(category_name)s, %(custom_fields)s, %(all_fields)s
            )
            ON DUPLICATE KEY UPDATE
                subject = VALUES(subject),
                description = VALUES(description),
                start_date = VALUES(start_date),
                due_date = VALUES(due_date),
                updated_at = VALUES(updated_at),
                estimated_hours = VALUES(estimated_hours),
                spent_hours = VALUES(spent_hours),
                project_name = VALUES(project_name),
                project_identifier = VALUES(project_identifier),
                type_name = VALUES(type_name),
                status_name = VALUES(status_name),
                status_is_closed = VALUES(status_is_closed),
                priority_name = VALUES(priority_name),
                assignee_name = VALUES(assignee_name),
                assignee_login = VALUES(assignee_login),
                responsible_name = VALUES(responsible_name),
                responsible_login = VALUES(responsible_login),
                author_name = VALUES(author_name),
                author_login = VALUES(author_login),
                version_name = VALUES(version_name),
                category_name = VALUES(category_name),
                custom_fields = VALUES(custom_fields),
                all_fields = VALUES(all_fields)
        """

        cursor.execute(query, wp_data)

    def extract_projects(self):
        """Extract projects from raw data"""

        self.logger.info("Starting projects extraction")

        connection = self._get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT data FROM _raw_openproject_api_projects 
                WHERE connection_id = %s AND data IS NOT NULL
                ORDER BY created_at DESC LIMIT 1
            """, (self.connection_id,))

            raw_record = cursor.fetchone()
            if not raw_record:
                self.logger.warning("No raw project data found")
                return 0

            data = json.loads(raw_record['data'])
            elements = data.get('_embedded', {}).get('elements', [])

            # Clear existing data
            cursor.execute("""
                DELETE FROM _tool_openproject_projects 
                WHERE connection_id = %s
            """, (self.connection_id,))

            for element in elements:
                # Extract parent project info
                parent_id = None
                parent_name = None
                parent_link = element.get('_links', {}).get('parent')
                if parent_link:
                    parent_id, parent_name = self._extract_link_info(parent_link)

                # Handle description which might be an object
                description = element.get('description', '')
                if isinstance(description, dict):
                    description = description.get('raw', '') or description.get('html', '') or str(description)
                elif description is None:
                    description = ''
                
                project_data = {
                    'connection_id': self.connection_id,
                    'id': element.get('id'),
                    'identifier': element.get('identifier', ''),
                    'name': element.get('name', ''),
                    'description': str(description),
                    'status': element.get('status', ''),
                    'is_public': bool(element.get('public', False)),
                    'parent_id': parent_id,
                    'parent_name': parent_name or '',
                    'created_at': self._parse_datetime(element.get('createdAt')),
                    'updated_at': self._parse_datetime(element.get('updatedAt')),
                    'all_fields': json.dumps(element) if element else None
                }

                query = """
                    INSERT INTO _tool_openproject_projects (
                        connection_id, id, identifier, name, description, status,
                        is_public, parent_id, parent_name, created_at, updated_at, all_fields
                    ) VALUES (
                        %(connection_id)s, %(id)s, %(identifier)s, %(name)s, %(description)s,
                        %(status)s, %(is_public)s, %(parent_id)s, %(parent_name)s,
                        %(created_at)s, %(updated_at)s, %(all_fields)s
                    )
                    ON DUPLICATE KEY UPDATE
                        identifier = VALUES(identifier),
                        name = VALUES(name),
                        description = VALUES(description),
                        status = VALUES(status),
                        is_public = VALUES(is_public),
                        parent_name = VALUES(parent_name),
                        updated_at = VALUES(updated_at),
                        all_fields = VALUES(all_fields)
                """

                cursor.execute(query, project_data)

            connection.commit()
            self.logger.info(f"Extracted {len(elements)} projects")
            return len(elements)

        except Exception as e:
            self.logger.error(f"Project extraction failed: {e}")
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def extract_users(self):
        """Extract users from raw data"""

        self.logger.info("Starting users extraction")

        connection = self._get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT data FROM _raw_openproject_api_users 
                WHERE connection_id = %s AND data IS NOT NULL
                ORDER BY created_at DESC LIMIT 1
            """, (self.connection_id,))

            raw_record = cursor.fetchone()
            if not raw_record:
                self.logger.warning("No raw user data found")
                return 0

            data = json.loads(raw_record['data'])
            elements = data.get('_embedded', {}).get('elements', [])

            # Clear existing data
            cursor.execute("""
                DELETE FROM _tool_openproject_users 
                WHERE connection_id = %s
            """, (self.connection_id,))

            for element in elements:
                user_data = {
                    'connection_id': self.connection_id,
                    'id': element.get('id'),
                    'login': element.get('login', ''),
                    'first_name': element.get('firstName', ''),
                    'last_name': element.get('lastName', ''),
                    'name': element.get('name', ''),
                    'mail': element.get('email', ''),
                    'admin': element.get('admin', False),
                    'avatar': element.get('avatar'),
                    'status': element.get('status'),
                    'language': element.get('language'),
                    'identity_url': element.get('identityUrl'),
                    'created_at': self._parse_datetime(element.get('createdAt')),
                    'updated_at': self._parse_datetime(element.get('updatedAt')),
                    'all_fields': json.dumps(element)
                }

                query = """
                    INSERT INTO _tool_openproject_users (
                        connection_id, id, login, first_name, last_name, name, mail,
                        admin, avatar, status, language, identity_url,
                        created_at, updated_at, all_fields
                    ) VALUES (
                        %(connection_id)s, %(id)s, %(login)s, %(first_name)s, %(last_name)s,
                        %(name)s, %(mail)s, %(admin)s, %(avatar)s, %(status)s,
                        %(language)s, %(identity_url)s, %(created_at)s, %(updated_at)s, %(all_fields)s
                    )
                    ON DUPLICATE KEY UPDATE
                        login = VALUES(login),
                        first_name = VALUES(first_name),
                        last_name = VALUES(last_name),
                        name = VALUES(name),
                        mail = VALUES(mail),
                        admin = VALUES(admin),
                        avatar = VALUES(avatar),
                        status = VALUES(status),
                        language = VALUES(language),
                        identity_url = VALUES(identity_url),
                        updated_at = VALUES(updated_at),
                        all_fields = VALUES(all_fields)
                """

                cursor.execute(query, user_data)

            connection.commit()
            self.logger.info(f"Extracted {len(elements)} users")
            return len(elements)

        except Exception as e:
            self.logger.error(f"User extraction failed: {e}")
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def extract_time_entries(self):
        """Extract time entries from raw data"""

        self.logger.info("Starting time entries extraction")

        connection = self._get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT data FROM _raw_openproject_api_time_entries 
                WHERE connection_id = %s AND data IS NOT NULL
                ORDER BY created_at DESC
            """, (self.connection_id,))

            raw_records = cursor.fetchall()

            # Clear existing data
            cursor.execute("""
                DELETE FROM _tool_openproject_time_entries 
                WHERE connection_id = %s
            """, (self.connection_id,))

            extracted_count = 0
            processed_te_ids = set()

            for raw_record in raw_records:
                try:
                    data = json.loads(raw_record['data'])
                    elements = data.get('_embedded', {}).get('elements', [])

                    for element in elements:
                        te_id = element.get('id')
                        if not te_id or te_id in processed_te_ids:
                            continue

                        # Extract linked data
                        links = element.get('_links', {})
                        
                        # Work package info
                        wp_id, wp_title = self._extract_link_info(links.get('workPackage'))
                        
                        # User info
                        user_id, user_name = self._extract_link_info(links.get('user'))
                        
                        # Activity info
                        activity_id, activity_name = self._extract_link_info(links.get('activity'))
                        
                        # Project info
                        project_id, project_name = self._extract_link_info(links.get('project'))

                        time_entry_data = {
                            'connection_id': self.connection_id,
                            'id': te_id,
                            'hours': self._parse_duration(element.get('hours')),
                            'comment': str(element.get('comment', '')),
                            'spent_on': self._parse_date(element.get('spentOn')),
                            'work_package_id': wp_id,
                            'work_package_title': str(wp_title or ''),
                            'user_id': user_id,
                            'user_name': str(user_name or ''),
                            'activity_id': activity_id,
                            'activity_name': str(activity_name or ''),
                            'project_id': project_id,
                            'project_name': str(project_name or ''),
                            'created_at': self._parse_datetime(element.get('createdAt')),
                            'updated_at': self._parse_datetime(element.get('updatedAt')),
                            'all_fields': json.dumps(element) if element else None
                        }

                        query = """
                            INSERT INTO _tool_openproject_time_entries (
                                connection_id, id, hours, comment, spent_on,
                                work_package_id, work_package_title, user_id, user_name,
                                activity_id, activity_name, project_id, project_name,
                                created_at, updated_at, all_fields
                            ) VALUES (
                                %(connection_id)s, %(id)s, %(hours)s, %(comment)s, %(spent_on)s,
                                %(work_package_id)s, %(work_package_title)s, %(user_id)s, %(user_name)s,
                                %(activity_id)s, %(activity_name)s, %(project_id)s, %(project_name)s,
                                %(created_at)s, %(updated_at)s, %(all_fields)s
                            )
                            ON DUPLICATE KEY UPDATE
                                hours = VALUES(hours),
                                comment = VALUES(comment),
                                spent_on = VALUES(spent_on),
                                work_package_title = VALUES(work_package_title),
                                user_name = VALUES(user_name),
                                activity_name = VALUES(activity_name),
                                project_name = VALUES(project_name),
                                updated_at = VALUES(updated_at),
                                all_fields = VALUES(all_fields)
                        """

                        cursor.execute(query, time_entry_data)
                        processed_te_ids.add(te_id)
                        extracted_count += 1

                except (json.JSONDecodeError, KeyError) as e:
                    self.logger.error(f"Failed to process raw time entry record: {e}")
                    continue

            connection.commit()
            self.logger.info(f"Extracted {extracted_count} unique time entries")
            return extracted_count

        except Exception as e:
            self.logger.error(f"Time entries extraction failed: {e}")
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def extract_metadata(self):
        """Extract metadata (statuses, types, priorities, activities)"""

        self.logger.info("Starting metadata extraction")

        # Extract each metadata type
        metadata_extractions = [
            ('_raw_openproject_api_statuses', '_tool_openproject_statuses', self._extract_statuses),
            ('_raw_openproject_api_types', '_tool_openproject_types', self._extract_types),
            ('_raw_openproject_api_priorities', '_tool_openproject_priorities', self._extract_priorities),
            ('_raw_openproject_api_activities', '_tool_openproject_activities', self._extract_activities)
        ]

        total_extracted = 0

        for raw_table, tool_table, extract_func in metadata_extractions:
            try:
                count = extract_func(raw_table, tool_table)
                total_extracted += count
                self.logger.info(f"Extracted {count} items from {raw_table}")
            except Exception as e:
                self.logger.error(f"Failed to extract from {raw_table}: {e}")

        self.logger.info(f"Metadata extraction completed. Total: {total_extracted}")
        return total_extracted

    def _extract_statuses(self, raw_table: str, tool_table: str) -> int:
        """Extract statuses metadata"""

        connection = self._get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute(f"""
                SELECT data FROM {raw_table}
                WHERE connection_id = %s AND data IS NOT NULL
                ORDER BY created_at DESC LIMIT 1
            """, (self.connection_id,))

            raw_record = cursor.fetchone()
            if not raw_record:
                return 0

            data = json.loads(raw_record['data'])
            elements = data.get('_embedded', {}).get('elements', [])

            # Clear existing data
            cursor.execute(f"DELETE FROM {tool_table} WHERE connection_id = %s", (self.connection_id,))

            for element in elements:
                status_data = {
                    'connection_id': self.connection_id,
                    'id': element.get('id'),
                    'name': element.get('name', ''),
                    'is_closed': element.get('isClosed', False),
                    'is_default': element.get('isDefault', False),
                    'position': element.get('position'),
                    'default_done_ratio': element.get('defaultDoneRatio'),
                    'color': element.get('color'),
                    'all_fields': json.dumps(element)
                }

                query = f"""
                    INSERT INTO {tool_table} (
                        connection_id, id, name, is_closed, is_default, position,
                        default_done_ratio, color, all_fields
                    ) VALUES (
                        %(connection_id)s, %(id)s, %(name)s, %(is_closed)s, %(is_default)s,
                        %(position)s, %(default_done_ratio)s, %(color)s, %(all_fields)s
                    )
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        is_closed = VALUES(is_closed),
                        is_default = VALUES(is_default),
                        position = VALUES(position),
                        default_done_ratio = VALUES(default_done_ratio),
                        color = VALUES(color),
                        all_fields = VALUES(all_fields)
                """

                cursor.execute(query, status_data)

            connection.commit()
            return len(elements)

        finally:
            cursor.close()
            connection.close()

    def _extract_types(self, raw_table: str, tool_table: str) -> int:
        """Extract types metadata"""

        connection = self._get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute(f"""
                SELECT data FROM {raw_table}
                WHERE connection_id = %s AND data IS NOT NULL
                ORDER BY created_at DESC LIMIT 1
            """, (self.connection_id,))

            raw_record = cursor.fetchone()
            if not raw_record:
                return 0

            data = json.loads(raw_record['data'])
            elements = data.get('_embedded', {}).get('elements', [])

            # Clear existing data
            cursor.execute(f"DELETE FROM {tool_table} WHERE connection_id = %s", (self.connection_id,))

            for element in elements:
                type_data = {
                    'connection_id': self.connection_id,
                    'id': element.get('id'),
                    'name': element.get('name', ''),
                    'color': element.get('color'),
                    'position': element.get('position'),
                    'is_default': element.get('isDefault', False),
                    'is_milestone': element.get('isMilestone', False),
                    'all_fields': json.dumps(element)
                }

                query = f"""
                    INSERT INTO {tool_table} (
                        connection_id, id, name, color, position, is_default, is_milestone, all_fields
                    ) VALUES (
                        %(connection_id)s, %(id)s, %(name)s, %(color)s, %(position)s,
                        %(is_default)s, %(is_milestone)s, %(all_fields)s
                    )
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        color = VALUES(color),
                        position = VALUES(position),
                        is_default = VALUES(is_default),
                        is_milestone = VALUES(is_milestone),
                        all_fields = VALUES(all_fields)
                """

                cursor.execute(query, type_data)

            connection.commit()
            return len(elements)

        finally:
            cursor.close()
            connection.close()

    def _extract_priorities(self, raw_table: str, tool_table: str) -> int:
        """Extract priorities metadata"""

        connection = self._get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute(f"""
                SELECT data FROM {raw_table}
                WHERE connection_id = %s AND data IS NOT NULL
                ORDER BY created_at DESC LIMIT 1
            """, (self.connection_id,))

            raw_record = cursor.fetchone()
            if not raw_record:
                return 0

            data = json.loads(raw_record['data'])
            elements = data.get('_embedded', {}).get('elements', [])

            # Clear existing data
            cursor.execute(f"DELETE FROM {tool_table} WHERE connection_id = %s", (self.connection_id,))

            for element in elements:
                priority_data = {
                    'connection_id': self.connection_id,
                    'id': element.get('id'),
                    'name': element.get('name', ''),
                    'position': element.get('position'),
                    'color': element.get('color'),
                    'is_default': element.get('isDefault', False),
                    'is_active': element.get('isActive', True),
                    'all_fields': json.dumps(element)
                }

                query = f"""
                    INSERT INTO {tool_table} (
                        connection_id, id, name, position, color, is_default, is_active, all_fields
                    ) VALUES (
                        %(connection_id)s, %(id)s, %(name)s, %(position)s, %(color)s,
                        %(is_default)s, %(is_active)s, %(all_fields)s
                    )
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        position = VALUES(position),
                        color = VALUES(color),
                        is_default = VALUES(is_default),
                        is_active = VALUES(is_active),
                        all_fields = VALUES(all_fields)
                """

                cursor.execute(query, priority_data)

            connection.commit()
            return len(elements)

        finally:
            cursor.close()
            connection.close()

    def _extract_activities(self, raw_table: str, tool_table: str) -> int:
        """Extract activities metadata"""

        connection = self._get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute(f"""
                SELECT data FROM {raw_table}
                WHERE connection_id = %s AND data IS NOT NULL
                ORDER BY created_at DESC LIMIT 1
            """, (self.connection_id,))

            raw_record = cursor.fetchone()
            if not raw_record:
                return 0

            data = json.loads(raw_record['data'])
            elements = data.get('_embedded', {}).get('elements', [])

            # Clear existing data
            cursor.execute(f"DELETE FROM {tool_table} WHERE connection_id = %s", (self.connection_id,))

            for element in elements:
                activity_data = {
                    'connection_id': self.connection_id,
                    'id': element.get('id'),
                    'name': element.get('name', ''),
                    'position': element.get('position'),
                    'is_default': element.get('isDefault', False),
                    'is_active': element.get('isActive', True),
                    'all_fields': json.dumps(element)
                }

                query = f"""
                    INSERT INTO {tool_table} (
                        connection_id, id, name, position, is_default, is_active, all_fields
                    ) VALUES (
                        %(connection_id)s, %(id)s, %(name)s, %(position)s,
                        %(is_default)s, %(is_active)s, %(all_fields)s
                    )
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        position = VALUES(position),
                        is_default = VALUES(is_default),
                        is_active = VALUES(is_active),
                        all_fields = VALUES(all_fields)
                """

                cursor.execute(query, activity_data)

            connection.commit()
            return len(elements)

        finally:
            cursor.close()
            connection.close()

    def update_references(self):
        """Update reference fields like user logins, project identifiers, status flags"""

        self.logger.info("Updating reference fields")

        connection = self._get_db_connection()
        cursor = connection.cursor()

        try:
            # Update user logins in work packages
            cursor.execute("""
                UPDATE _tool_openproject_work_packages wp
                JOIN _tool_openproject_users u ON wp.assignee_id = u.id AND wp.connection_id = u.connection_id
                SET wp.assignee_login = u.login
                WHERE wp.connection_id = %s AND wp.assignee_id IS NOT NULL
            """, (self.connection_id,))

            cursor.execute("""
                UPDATE _tool_openproject_work_packages wp
                JOIN _tool_openproject_users u ON wp.responsible_id = u.id AND wp.connection_id = u.connection_id
                SET wp.responsible_login = u.login
                WHERE wp.connection_id = %s AND wp.responsible_id IS NOT NULL
            """, (self.connection_id,))

            cursor.execute("""
                UPDATE _tool_openproject_work_packages wp
                JOIN _tool_openproject_users u ON wp.author_id = u.id AND wp.connection_id = u.connection_id
                SET wp.author_login = u.login
                WHERE wp.connection_id = %s AND wp.author_id IS NOT NULL
            """, (self.connection_id,))

            # Update project identifiers in work packages
            cursor.execute("""
                UPDATE _tool_openproject_work_packages wp
                JOIN _tool_openproject_projects p ON wp.project_id = p.id AND wp.connection_id = p.connection_id
                SET wp.project_identifier = p.identifier
                WHERE wp.connection_id = %s AND wp.project_id IS NOT NULL
            """, (self.connection_id,))

            # Update status closed flags in work packages
            cursor.execute("""
                UPDATE _tool_openproject_work_packages wp
                JOIN _tool_openproject_statuses s ON wp.status_id = s.id AND wp.connection_id = s.connection_id
                SET wp.status_is_closed = s.is_closed
                WHERE wp.connection_id = %s AND wp.status_id IS NOT NULL
            """, (self.connection_id,))

            connection.commit()
            self.logger.info("Reference fields updated successfully")

        except Exception as e:
            self.logger.error(f"Failed to update reference fields: {e}")
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def run_extraction(self):
        """Run complete extraction process"""

        self.logger.info("Starting OpenProject data extraction")

        extraction_stats = {
            'projects': 0,
            'users': 0,
            'work_packages': 0,
            'time_entries': 0,
            'metadata': 0
        }

        try:
            # Extract metadata first
            self.logger.info("=== Extracting Metadata ===")
            extraction_stats['metadata'] = self.extract_metadata()

            # Extract core entities
            self.logger.info("=== Extracting Core Entities ===")
            extraction_stats['projects'] = self.extract_projects()
            extraction_stats['users'] = self.extract_users()
            extraction_stats['work_packages'] = self.extract_work_packages()
            extraction_stats['time_entries'] = self.extract_time_entries()

            # Update reference fields
            self.logger.info("=== Updating References ===")
            self.update_references()

            self.logger.info("=== Extraction Statistics ===")
            for entity, count in extraction_stats.items():
                self.logger.info(f"{entity.title()}: {count}")

            total_records = sum(extraction_stats.values())
            self.logger.info(f"Total records extracted: {total_records}")

            self.logger.info("OpenProject data extraction completed successfully")
            return extraction_stats

        except Exception as e:
            self.logger.error(f"Data extraction failed: {e}")
            raise

# CLI interface for the extractor
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='OpenProject Data Extractor')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    # Create extractor
    extractor = OpenProjectExtractor(args.config)

    if args.verbose:
        extractor.logger.setLevel(logging.DEBUG)

    # Run extraction
    try:
        stats = extractor.run_extraction()
        print("\n" + "=" * 50)
        print("Extraction Summary")
        print("=" * 50)
        for entity, count in stats.items():
            print(f"{entity.title()}: {count}")
        print(f"\nTotal records: {sum(stats.values())}")
        print("=" * 50)
    except Exception as e:
        print(f"\n✗ Extraction failed: {e}")
        exit(1)