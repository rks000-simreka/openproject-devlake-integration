#!/usr/bin/env python3
"""
OpenProject Data Collector - Fetches raw data from OpenProject API
"""

import requests
import json
import mysql.connector
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time
import logging
import logging.handlers
import base64
from pathlib import Path
import yaml

class OpenProjectCollector:
    """Collects raw data from OpenProject API and stores in raw tables"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()

        # OpenProject configuration
        op_config = self.config['openproject']
        self.base_url = op_config['base_url'].rstrip('/')
        self.api_key = op_config['api_key']
        self.connection_id = op_config['connection_id']

        # Pipeline configuration
        pipeline_config = self.config['pipeline']
        self.batch_size = pipeline_config['batch_size']
        self.rate_limit_rpm = pipeline_config['rate_limit_rpm']
        self.retry_attempts = pipeline_config['retry_attempts']
        self.timeout = pipeline_config['timeout_seconds']
        
        # Safety limit to prevent infinite loops
        self.max_pages = pipeline_config.get('max_pages_per_collection', 1000)

        # Database configuration
        self.db_config = self.config['database']

        # Setup authentication headers
        self.headers = {
            'Authorization': f'Basic {self._encode_auth()}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'DevLake-OpenProject-Collector/1.0'
        }

        # Rate limiting
        self.last_request_time = 0
        self.request_count = 0
        self.request_window_start = time.time()

        self.logger.info("OpenProject Collector initialized")

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_config = self.config['logging']

        # Create logger
        logger = logging.getLogger(f"{__name__}.{self.config['openproject']['connection_id']}")
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

    def _encode_auth(self) -> str:
        """Encode API key for basic auth"""
        auth_string = f"apikey:{self.api_key}"
        return base64.b64encode(auth_string.encode()).decode()

    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()

        # Reset window if 60 seconds have passed
        if current_time - self.request_window_start >= 60:
            self.request_count = 0
            self.request_window_start = current_time

        # Check if we're at the limit
        if self.request_count >= self.rate_limit_rpm:
            sleep_time = 60 - (current_time - self.request_window_start)
            if sleep_time > 0:
                self.logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self.request_count = 0
                self.request_window_start = time.time()

        # Minimum delay between requests
        time_since_last = current_time - self.last_request_time
        min_interval = 60.0 / self.rate_limit_rpm

        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()
        self.request_count += 1

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make API request with error handling and rate limiting"""

        self._rate_limit()
        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.retry_attempts):
            try:
                self.logger.debug(f"Making request to {url} (attempt {attempt + 1})")

                response = requests.get(
                    url, 
                    headers=self.headers, 
                    params=params, 
                    timeout=self.timeout
                )

                # Log rate limit info if available
                if 'X-RateLimit-Remaining' in response.headers:
                    remaining = response.headers['X-RateLimit-Remaining']
                    self.logger.debug(f"Rate limit remaining: {remaining}")

                response.raise_for_status()

                return {
                    'success': True,
                    'data': response.json(),
                    'url': url,
                    'params': params or {},
                    'status_code': response.status_code,
                    'headers': dict(response.headers)
                }

            except requests.exceptions.Timeout:
                self.logger.warning(f"Request timeout for {url} (attempt {attempt + 1})")
                if attempt < self.retry_attempts - 1:
                    time.sleep(2 ** attempt)
                    continue

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                elif e.response.status_code in [500, 502, 503, 504]:
                    self.logger.warning(f"Server error {e.response.status_code} for {url} (attempt {attempt + 1})")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(2 ** attempt)
                        continue
                else:
                    self.logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
                    break

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request failed for {url} (attempt {attempt + 1}): {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(2 ** attempt)
                    continue

        return {
            'success': False,
            'error': f"Failed after {self.retry_attempts} attempts",
            'url': url,
            'params': params or {}
        }

    def _get_db_connection(self):
        """Get database connection"""
        return mysql.connector.connect(**self.db_config)

    def _store_raw_data(self, table_name: str, data: Dict, additional_fields: Optional[Dict] = None):
        """Store raw API response in database"""

        connection = self._get_db_connection()
        cursor = connection.cursor()

        try:
            record = {
                'connection_id': self.connection_id,
                'params': json.dumps(data.get('params', {})),
                'url': data.get('url'),
                'input': json.dumps(additional_fields or {}),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }

            if data.get('success'):
                record['data'] = json.dumps(data.get('data', {}))
            else:
                record['data'] = None
                self.logger.warning(f"Storing failed request for {table_name}: {data.get('error')}")

            if additional_fields:
                record.update(additional_fields)

            columns = list(record.keys())
            placeholders = [f"%({col})s" for col in columns]

            query = f"""
                INSERT INTO {table_name} 
                ({', '.join(columns)}) 
                VALUES ({', '.join(placeholders)})
            """

            cursor.execute(query, record)
            connection.commit()

            self.logger.debug(f"Stored raw data in {table_name}: {data.get('url')}")

        except mysql.connector.Error as e:
            self.logger.error(f"Failed to store raw data in {table_name}: {e}")
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def collect_work_packages(self, project_id: Optional[int] = None, incremental: bool = True):
        """Collect work packages data"""

        self.logger.info(f"Starting work packages collection for project {project_id or 'all'}")

        params = {
            'pageSize': self.batch_size,
            'offset': 1
        }

        # Add project filter if specified
        if project_id:
            params['filters'] = json.dumps([{
                "project": {
                    "operator": "=", 
                    "values": [str(project_id)]
                }
            }])

        # For incremental sync, we'll use a simpler approach
        if incremental:
            last_sync = self._get_last_sync_time('_raw_openproject_api_work_packages')
            if last_sync:
                # Use a more compatible date format
                date_str = last_sync.strftime('%Y-%m-%dT%H:%M:%SZ')
                self.logger.info(f"Incremental sync from {date_str}")
                # Note: Some OpenProject versions don't support updatedAt filter
                # We'll collect all and filter later if needed

        page = 1
        total_collected = 0

        while page <= self.max_pages:
            params['offset'] = page

            self.logger.info(f"Collecting work packages page {page}")

            response = self._make_request('/api/v3/work_packages', params)

            self._store_raw_data(
                '_raw_openproject_api_work_packages',
                response,
                {'project_id': project_id}
            )

            if not response.get('success'):
                self.logger.error("Failed to collect work packages")
                break

            data = response.get('data', {})
            elements = data.get('_embedded', {}).get('elements', [])

            if not elements:
                self.logger.info("No more work packages to collect")
                break

            total_collected += len(elements)
            self.logger.info(f"Collected {len(elements)} work packages (total: {total_collected})")

            # Check if we've collected all available records
            total = data.get('total', 0)
            if total_collected >= total:
                self.logger.info(f"Collected all {total} work packages")
                break

            # Increment page for next iteration
            page += 1
            
        if page > self.max_pages:
            self.logger.warning(f"Reached maximum page limit ({self.max_pages}) for work packages collection")

        self.logger.info(f"Work packages collection completed. Total: {total_collected}")
        return total_collected

    def _get_last_sync_time(self, table_name: str) -> Optional[datetime]:
        """Get the last sync time from raw table"""

        connection = self._get_db_connection()
        cursor = connection.cursor()

        try:
            query = f"""
                SELECT MAX(created_at) as last_sync
                FROM {table_name}
                WHERE connection_id = %s AND data IS NOT NULL
            """

            cursor.execute(query, (self.connection_id,))
            result = cursor.fetchone()

            if result and result[0]:
                return result[0]
            return None

        except mysql.connector.Error as e:
            self.logger.error(f"Failed to get last sync time from {table_name}: {e}")
            return None
        finally:
            cursor.close()
            connection.close()

    def collect_projects(self):
        """Collect projects data"""

        self.logger.info("Starting projects collection")

        params = {
            'pageSize': self.batch_size,
            'offset': 1
        }

        page = 1
        total_collected = 0

        while True:
            params['offset'] = page

            self.logger.info(f"Collecting projects page {page}")

            response = self._make_request('/api/v3/projects', params)

            self._store_raw_data('_raw_openproject_api_projects', response)

            if not response.get('success'):
                self.logger.error("Failed to collect projects")
                break

            data = response.get('data', {})
            elements = data.get('_embedded', {}).get('elements', [])

            if not elements:
                break

            total_collected += len(elements)
            self.logger.info(f"Collected {len(elements)} projects (total: {total_collected})")

            total = data.get('total', 0)
            if total_collected >= total:
                break

            page += 1

        self.logger.info(f"Projects collection completed. Total: {total_collected}")
        return total_collected

    def collect_users(self):
        """Collect users data"""

        self.logger.info("Starting users collection")

        params = {
            'pageSize': self.batch_size,
            'offset': 1
        }

        page = 1
        total_collected = 0

        while page <= self.max_pages:
            params['offset'] = page

            self.logger.info(f"Collecting users page {page}")

            response = self._make_request('/api/v3/users', params)

            self._store_raw_data('_raw_openproject_api_users', response)

            if not response.get('success'):
                self.logger.error("Failed to collect users")
                break

            data = response.get('data', {})
            elements = data.get('_embedded', {}).get('elements', [])

            if not elements:
                self.logger.info("No more users to collect")
                break

            total_collected += len(elements)
            self.logger.info(f"Collected {len(elements)} users (total: {total_collected})")

            # Check if we've collected all available records
            total = data.get('total', 0)
            if total_collected >= total:
                self.logger.info(f"Collected all {total} users")
                break

            # Increment page for next iteration
            page += 1
            
        if page > self.max_pages:
            self.logger.warning(f"Reached maximum page limit ({self.max_pages}) for users collection")

        self.logger.info(f"Users collection completed. Total: {total_collected}")
        return total_collected

    def collect_time_entries(self, work_package_id: Optional[int] = None, incremental: bool = True):
        """Collect time entries data"""

        self.logger.info(f"Starting time entries collection for work package {work_package_id or 'all'}")

        params = {
            'pageSize': self.batch_size,
            'offset': 1
        }

        # Add work package filter if specified
        if work_package_id:
            params['filters'] = json.dumps([{
                "workPackage": {
                    "operator": "=",
                    "values": [str(work_package_id)]
                }
            }])

        # For incremental sync, we'll use a simpler approach
        if incremental:
            last_sync = self._get_last_sync_time('_raw_openproject_api_time_entries')
            if last_sync:
                date_str = last_sync.strftime('%Y-%m-%dT%H:%M:%SZ')
                self.logger.info(f"Incremental sync from {date_str}")
                # Note: Some OpenProject versions don't support updatedAt filter for time entries

        page = 1
        total_collected = 0

        while page <= self.max_pages:
            params['offset'] = page

            self.logger.info(f"Collecting time entries page {page}")

            response = self._make_request('/api/v3/time_entries', params)

            self._store_raw_data(
                '_raw_openproject_api_time_entries',
                response,
                {'work_package_id': work_package_id}
            )

            if not response.get('success'):
                self.logger.error("Failed to collect time entries")
                break

            data = response.get('data', {})
            elements = data.get('_embedded', {}).get('elements', [])

            if not elements:
                self.logger.info("No more time entries to collect")
                break

            total_collected += len(elements)
            self.logger.info(f"Collected {len(elements)} time entries (total: {total_collected})")

            # Check if we've collected all available records
            total = data.get('total', 0)
            if total_collected >= total:
                self.logger.info(f"Collected all {total} time entries")
                break

            # Increment page for next iteration
            page += 1
            
        if page > self.max_pages:
            self.logger.warning(f"Reached maximum page limit ({self.max_pages}) for time entries collection")

        self.logger.info(f"Time entries collection completed. Total: {total_collected}")
        return total_collected

    def collect_metadata(self):
        """Collect metadata (statuses, types, priorities, activities)"""

        metadata_endpoints = [
            ('/api/v3/statuses', '_raw_openproject_api_statuses'),
            ('/api/v3/types', '_raw_openproject_api_types'),
            ('/api/v3/priorities', '_raw_openproject_api_priorities'),
            # Note: activities endpoint might not exist in all OpenProject versions
            # We'll try it but won't fail if it doesn't exist
        ]

        total_collected = 0

        for endpoint, table in metadata_endpoints:
            self.logger.info(f"Collecting metadata from {endpoint}")

            response = self._make_request(endpoint)
            self._store_raw_data(table, response)

            if response.get('success'):
                data = response.get('data', {})
                elements = data.get('_embedded', {}).get('elements', [])
                count = len(elements)
                total_collected += count
                self.logger.info(f"Collected {count} items from {endpoint}")
            else:
                self.logger.warning(f"Failed to collect from {endpoint} (this might be expected)")

        # Try to collect activities separately - different OpenProject versions have different endpoints
        activities_endpoints = [
            '/api/v3/time_entries/activities',
            '/api/v3/activities'
        ]
        
        for endpoint in activities_endpoints:
            self.logger.info(f"Trying activities endpoint: {endpoint}")
            response = self._make_request(endpoint)
            
            if response.get('success'):
                self._store_raw_data('_raw_openproject_api_activities', response)
                data = response.get('data', {})
                elements = data.get('_embedded', {}).get('elements', [])
                count = len(elements)
                total_collected += count
                self.logger.info(f"Successfully collected {count} activities from {endpoint}")
                break
            else:
                self.logger.debug(f"Activities endpoint {endpoint} not available")
        else:
            self.logger.warning("No activities endpoint found - this is not critical")

        return total_collected

    def collect_versions(self, project_id: Optional[int] = None):
        """Collect versions (sprint equivalent) data"""

        self.logger.info(f"Starting versions collection for project {project_id or 'all'}")

        if project_id:
            endpoint = f'/api/v3/projects/{project_id}/versions'
        else:
            endpoint = '/api/v3/versions'

        params = {
            'pageSize': self.batch_size,
            'offset': 1
        }

        page = 1
        total_collected = 0

        while page <= self.max_pages:
            params['offset'] = page

            self.logger.info(f"Collecting versions page {page}")

            response = self._make_request(endpoint, params)

            self._store_raw_data(
                '_raw_openproject_api_versions',
                response,
                {'project_id': project_id}
            )

            if not response.get('success'):
                self.logger.error("Failed to collect versions")
                break

            data = response.get('data', {})
            elements = data.get('_embedded', {}).get('elements', [])

            if not elements:
                self.logger.info("No more versions to collect")
                break

            total_collected += len(elements)
            self.logger.info(f"Collected {len(elements)} versions (total: {total_collected})")

            # Check if we've collected all available records
            total = data.get('total', 0)
            if total_collected >= total:
                self.logger.info(f"Collected all {total} versions")
                break

            # Increment page for next iteration
            page += 1
            
        if page > self.max_pages:
            self.logger.warning(f"Reached maximum page limit ({self.max_pages}) for versions collection")

        self.logger.info(f"Versions collection completed. Total: {total_collected}")
        return total_collected

    def run_collection(self, project_ids: Optional[List[int]] = None, incremental: bool = True):
        """Run complete data collection process"""

        self.logger.info("Starting OpenProject data collection")

        collection_stats = {
            'projects': 0,
            'users': 0,
            'work_packages': 0,
            'time_entries': 0,
            'versions': 0,
            'metadata': 0
        }

        try:
            self.logger.info("=== Collecting Metadata ===")
            collection_stats['metadata'] = self.collect_metadata()

            self.logger.info("=== Collecting Core Entities ===")
            collection_stats['projects'] = self.collect_projects()
            collection_stats['users'] = self.collect_users()

            if project_ids:
                for project_id in project_ids:
                    self.logger.info(f"=== Collecting Data for Project {project_id} ===")
                    collection_stats['work_packages'] += self.collect_work_packages(project_id, incremental)
                    collection_stats['time_entries'] += self.collect_time_entries(None, incremental)
                    collection_stats['versions'] += self.collect_versions(project_id)
            else:
                self.logger.info("=== Collecting All Project Data ===")
                collection_stats['work_packages'] = self.collect_work_packages(None, incremental)
                collection_stats['time_entries'] = self.collect_time_entries(None, incremental)
                collection_stats['versions'] = self.collect_versions()

            self.logger.info("=== Collection Statistics ===")
            for entity, count in collection_stats.items():
                self.logger.info(f"{entity.title()}: {count}")

            total_records = sum(collection_stats.values())
            self.logger.info(f"Total records collected: {total_records}")

            self.logger.info("OpenProject data collection completed successfully")
            return collection_stats

        except Exception as e:
            self.logger.error(f"Data collection failed: {e}")
            raise

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='OpenProject Data Collector')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--projects', nargs='+', type=int, help='Specific project IDs to collect')
    parser.add_argument('--full', action='store_true', help='Force full sync (not incremental)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--test', action='store_true', help='Test mode: collect only first page of each entity')

    args = parser.parse_args()

    collector = OpenProjectCollector(args.config)

    if args.verbose:
        collector.logger.setLevel(logging.DEBUG)

    if args.test:
        collector.max_pages = 1  # Limit to 1 page for testing
        collector.logger.info("Test mode enabled: collecting only first page of each entity")

    try:
        incremental = not args.full
        stats = collector.run_collection(args.projects, incremental)
        print("\n" + "=" * 50)
        print("Collection Summary")
        print("=" * 50)
        for entity, count in stats.items():
            print(f"{entity.title()}: {count}")
        print(f"\nTotal records: {sum(stats.values())}")
        print("=" * 50)
    except Exception as e:
        print(f"\n✗ Collection failed: {e}")
        exit(1)