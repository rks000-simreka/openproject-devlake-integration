
# OpenProject DevLake Integration - Complete Setup Guide

## Table of Contents
1. [Environment Setup](#environment-setup)
2. [Database Configuration](#database-configuration)
3. [OpenProject Data Pipeline](#openproject-data-pipeline)
4. [Grafana Configuration](#grafana-configuration)
5. [Running the Pipeline](#running-the-pipeline)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)

## Prerequisites

- DevLake MySQL database (existing or new installation)
- OpenProject instance with API access
- Python 3.8+ environment
- Grafana instance
- MySQL client access

## Environment Setup

### Step 1: Install Required Python Packages

Create a `requirements.txt` file:

```text
mysql-connector-python==8.2.0
requests==2.31.0
python-dotenv==1.0.0
pandas==2.1.0
schedule==1.2.0
click==8.1.0
pyyaml==6.0.1
logging-config==1.0.3
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### Step 2: Create Configuration File

Create `config.yaml`:
```yaml
# OpenProject Configuration
openproject:
  base_url: "https://your-openproject.com"
  api_key: "your-api-key-here"
  connection_id: 1
  connection_name: "OpenProject Production"

# Database Configuration  
database:
  host: "localhost"
  port: 3306
  database: "devlake"
  user: "devlake"
  password: "your-password"
  charset: "utf8mb4"

# Pipeline Configuration
pipeline:
  batch_size: 100
  rate_limit_rpm: 60
  retry_attempts: 3
  timeout_seconds: 30

# Data Collection Settings
collection:
  incremental_sync: true
  sync_interval_hours: 6
  full_sync_interval_days: 7
  projects:
    - 1  # Specific project IDs to sync (empty for all)
    - 2

# Logging Configuration
logging:
  level: "INFO"
  file: "openproject_pipeline.log"
  max_bytes: 10485760  # 10MB
  backup_count: 5
```

### Step 3: Environment Variables

Create `.env` file:
```bash
# OpenProject Configuration
OPENPROJECT_BASE_URL=https://your-openproject.com
OPENPROJECT_API_KEY=your-api-key-here

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_DATABASE=devlake
DB_USER=devlake
DB_PASSWORD=your-password

# Pipeline Settings
CONNECTION_ID=1
BATCH_SIZE=100
RATE_LIMIT_RPM=60
```

## Database Configuration

### Step 4: Create Database Schema

Create `schema/01_create_raw_tables.sql`:
```sql
-- Raw layer tables for OpenProject data storage

-- Work packages raw data
CREATE TABLE IF NOT EXISTS _raw_openproject_api_work_packages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    connection_id INT NOT NULL,
    params JSON,
    data JSON,
    url VARCHAR(512),
    input JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    project_id INT,
    INDEX idx_connection_project (connection_id, project_id),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Projects raw data
CREATE TABLE IF NOT EXISTS _raw_openproject_api_projects (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    connection_id INT NOT NULL,
    params JSON,
    data JSON,
    url VARCHAR(512),
    input JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_connection (connection_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Users raw data
CREATE TABLE IF NOT EXISTS _raw_openproject_api_users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    connection_id INT NOT NULL,
    params JSON,
    data JSON,
    url VARCHAR(512),
    input JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_connection (connection_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Time entries raw data
CREATE TABLE IF NOT EXISTS _raw_openproject_api_time_entries (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    connection_id INT NOT NULL,
    params JSON,
    data JSON,
    url VARCHAR(512),
    input JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    work_package_id INT,
    INDEX idx_connection_wp (connection_id, work_package_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Statuses raw data
CREATE TABLE IF NOT EXISTS _raw_openproject_api_statuses (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    connection_id INT NOT NULL,
    params JSON,
    data JSON,
    url VARCHAR(512),
    input JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_connection (connection_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Types raw data
CREATE TABLE IF NOT EXISTS _raw_openproject_api_types (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    connection_id INT NOT NULL,
    params JSON,
    data JSON,
    url VARCHAR(512),
    input JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_connection (connection_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Priorities raw data
CREATE TABLE IF NOT EXISTS _raw_openproject_api_priorities (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    connection_id INT NOT NULL,
    params JSON,
    data JSON,
    url VARCHAR(512),
    input JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_connection (connection_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Versions raw data
CREATE TABLE IF NOT EXISTS _raw_openproject_api_versions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    connection_id INT NOT NULL,
    params JSON,
    data JSON,
    url VARCHAR(512),
    input JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    project_id INT,
    INDEX idx_connection_project (connection_id, project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Activities raw data
CREATE TABLE IF NOT EXISTS _raw_openproject_api_activities (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    connection_id INT NOT NULL,
    params JSON,
    data JSON,
    url VARCHAR(512),
    input JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_connection (connection_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

Create `schema/02_create_tool_tables.sql`:
```sql
-- Tool layer tables for OpenProject structured data

-- Work packages tool data
CREATE TABLE IF NOT EXISTS _tool_openproject_work_packages (
    connection_id INT NOT NULL,
    id INT NOT NULL,
    subject VARCHAR(512),
    description LONGTEXT,
    start_date DATE,
    due_date DATE,
    estimated_hours DECIMAL(10,2),
    spent_hours DECIMAL(10,2),
    percentage_done INT DEFAULT 0,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    project_id INT,
    project_identifier VARCHAR(100),
    project_name VARCHAR(255),
    type_id INT,
    type_name VARCHAR(100),
    status_id INT,
    status_name VARCHAR(100),
    status_is_closed BOOLEAN DEFAULT FALSE,
    priority_id INT,
    priority_name VARCHAR(100),
    assignee_id INT,
    assignee_name VARCHAR(255),
    assignee_login VARCHAR(100),
    responsible_id INT,
    responsible_name VARCHAR(255),
    responsible_login VARCHAR(100),
    author_id INT,
    author_name VARCHAR(255),
    author_login VARCHAR(100),
    parent_id INT,
    version_id INT,
    version_name VARCHAR(255),
    category_id INT,
    category_name VARCHAR(255),
    custom_fields JSON,
    all_fields JSON,
    PRIMARY KEY (connection_id, id),
    INDEX idx_project (connection_id, project_id),
    INDEX idx_assignee (connection_id, assignee_id),
    INDEX idx_status (connection_id, status_id),
    INDEX idx_type (connection_id, type_id),
    INDEX idx_created (created_at),
    INDEX idx_updated (updated_at),
    INDEX idx_due_date (due_date),
    INDEX idx_parent (connection_id, parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Projects tool data
CREATE TABLE IF NOT EXISTS _tool_openproject_projects (
    connection_id INT NOT NULL,
    id INT NOT NULL,
    identifier VARCHAR(100),
    name VARCHAR(255),
    description LONGTEXT,
    homepage VARCHAR(512),
    status VARCHAR(50),
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    parent_id INT,
    PRIMARY KEY (connection_id, id),
    INDEX idx_identifier (identifier),
    INDEX idx_status (status),
    INDEX idx_parent (connection_id, parent_id),
    UNIQUE KEY unique_identifier (connection_id, identifier)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Users tool data
CREATE TABLE IF NOT EXISTS _tool_openproject_users (
    connection_id INT NOT NULL,
    id INT NOT NULL,
    login VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    name VARCHAR(255),
    mail VARCHAR(255),
    admin BOOLEAN DEFAULT FALSE,
    status VARCHAR(50),
    language VARCHAR(10),
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    last_login_on TIMESTAMP NULL,
    avatar_url VARCHAR(512),
    PRIMARY KEY (connection_id, id),
    INDEX idx_login (login),
    INDEX idx_status (status),
    INDEX idx_email (mail),
    UNIQUE KEY unique_login (connection_id, login)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Time entries tool data
CREATE TABLE IF NOT EXISTS _tool_openproject_time_entries (
    connection_id INT NOT NULL,
    id INT NOT NULL,
    work_package_id INT,
    user_id INT,
    user_login VARCHAR(100),
    user_name VARCHAR(255),
    activity_id INT,
    activity_name VARCHAR(100),
    hours DECIMAL(10,2),
    comment TEXT,
    spent_on DATE,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    PRIMARY KEY (connection_id, id),
    INDEX idx_work_package (connection_id, work_package_id),
    INDEX idx_user (connection_id, user_id),
    INDEX idx_spent_on (spent_on),
    INDEX idx_activity (activity_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Statuses tool data
CREATE TABLE IF NOT EXISTS _tool_openproject_statuses (
    connection_id INT NOT NULL,
    id INT NOT NULL,
    name VARCHAR(100),
    position INT,
    is_default BOOLEAN DEFAULT FALSE,
    is_closed BOOLEAN DEFAULT FALSE,
    is_readonly BOOLEAN DEFAULT FALSE,
    default_done_ratio INT,
    PRIMARY KEY (connection_id, id),
    INDEX idx_position (position),
    INDEX idx_is_closed (is_closed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Types tool data
CREATE TABLE IF NOT EXISTS _tool_openproject_types (
    connection_id INT NOT NULL,
    id INT NOT NULL,
    name VARCHAR(100),
    position INT,
    is_default BOOLEAN DEFAULT FALSE,
    is_in_roadmap BOOLEAN DEFAULT FALSE,
    is_milestone BOOLEAN DEFAULT FALSE,
    color VARCHAR(20),
    PRIMARY KEY (connection_id, id),
    INDEX idx_position (position),
    INDEX idx_milestone (is_milestone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Priorities tool data
CREATE TABLE IF NOT EXISTS _tool_openproject_priorities (
    connection_id INT NOT NULL,
    id INT NOT NULL,
    name VARCHAR(100),
    position INT,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (connection_id, id),
    INDEX idx_position (position),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Versions tool data  
CREATE TABLE IF NOT EXISTS _tool_openproject_versions (
    connection_id INT NOT NULL,
    id INT NOT NULL,
    project_id INT,
    name VARCHAR(255),
    description LONGTEXT,
    status VARCHAR(50),
    due_date DATE,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    wiki_page_title VARCHAR(255),
    PRIMARY KEY (connection_id, id),
    INDEX idx_project (connection_id, project_id),
    INDEX idx_status (status),
    INDEX idx_due_date (due_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Activities tool data
CREATE TABLE IF NOT EXISTS _tool_openproject_activities (
    connection_id INT NOT NULL,
    id INT NOT NULL,
    name VARCHAR(100),
    position INT,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (connection_id, id),
    INDEX idx_position (position),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Step 5: Setup Database Connection

Create `database_setup.py`:
```python
#!/usr/bin/env python3
"""
Database setup script for OpenProject DevLake integration
"""

import mysql.connector
import os
import yaml
from pathlib import Path
import logging

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
            logging.FileHandler('database_setup.log'),
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
        for statement in statements:
            if statement:
                logger.info(f"Executing: {statement[:100]}...")
                cursor.execute(statement)

        connection.commit()
        logger.info(f"Successfully executed {sql_file_path}")

    except mysql.connector.Error as e:
        connection.rollback()
        logger.error(f"Error executing {sql_file_path}: {e}")
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
    logger.info("Verifying raw tables...")
    for table in expected_raw_tables:
        cursor.execute(f"SHOW TABLES LIKE '{table}'")
        if cursor.fetchone():
            logger.info(f"✓ {table} exists")
        else:
            logger.error(f"✗ {table} missing")

    # Check tool tables
    logger.info("Verifying tool tables...")
    for table in expected_tool_tables:
        cursor.execute(f"SHOW TABLES LIKE '{table}'")
        if cursor.fetchone():
            logger.info(f"✓ {table} exists")
        else:
            logger.error(f"✗ {table} missing")

    cursor.close()

def main():
    """Main database setup function"""

    logger = setup_logging()
    logger.info("Starting database setup...")

    try:
        # Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully")

        # Create database connection
        connection = create_database_connection(config)
        logger.info("Database connection established")

        # Execute schema files
        schema_files = [
            "schema/01_create_raw_tables.sql",
            "schema/02_create_tool_tables.sql"
        ]

        for sql_file in schema_files:
            execute_sql_file(connection, sql_file, logger)

        # Verify tables
        verify_tables(connection, logger)

        logger.info("Database setup completed successfully!")

    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()
```

## OpenProject Data Pipeline

### Step 6: Create Data Collection Module

Create `collectors/openproject_collector.py`:
```python
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

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
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
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limited
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                elif e.response.status_code in [500, 502, 503, 504]:  # Server errors
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

    def _store_raw_data(self, table_name: str, data: Dict, additional_fields: Dict = None):
        """Store raw API response in database"""

        connection = self._get_db_connection()
        cursor = connection.cursor()

        try:
            # Prepare data for insertion
            record = {
                'connection_id': self.connection_id,
                'params': json.dumps(data.get('params', {})),
                'url': data.get('url'),
                'input': json.dumps(additional_fields or {}),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }

            # Add successful data or None for failed requests
            if data.get('success'):
                record['data'] = json.dumps(data.get('data', {}))
            else:
                record['data'] = None
                self.logger.warning(f"Storing failed request for {table_name}: {data.get('error')}")

            # Add any additional fields
            if additional_fields:
                record.update(additional_fields)

            # Build INSERT query dynamically
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

        # Build filters
        filters = []
        if project_id:
            filters.append({
                "project": {
                    "operator": "=",
                    "values": [str(project_id)]
                }
            })

        # Incremental sync - only get updated work packages
        if incremental:
            # Get last sync time from database
            last_sync = self._get_last_sync_time('_raw_openproject_api_work_packages')
            if last_sync:
                filters.append({
                    "updatedAt": {
                        "operator": ">=",
                        "values": [last_sync.isoformat()]
                    }
                })
                self.logger.info(f"Incremental sync from {last_sync}")

        params = {
            'pageSize': self.batch_size,
            'offset': 1
        }

        if filters:
            params['filters'] = json.dumps(filters)

        page = 1
        total_collected = 0

        while True:
            params['offset'] = page

            self.logger.info(f"Collecting work packages page {page}")

            response = self._make_request('/api/v3/work_packages', params)

            # Store raw response
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

            # Check if there are more pages
            total = data.get('total', 0)
            if total_collected >= total:
                break

            page += 1

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

            # Store raw response
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

            # Check if there are more pages
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

        while True:
            params['offset'] = page

            response = self._make_request('/api/v3/users', params)

            # Store raw response
            self._store_raw_data('_raw_openproject_api_users', response)

            if not response.get('success'):
                self.logger.error("Failed to collect users")
                break

            data = response.get('data', {})
            elements = data.get('_embedded', {}).get('elements', [])

            if not elements:
                break

            total_collected += len(elements)
            page += 1

        self.logger.info(f"Users collection completed. Total: {total_collected}")
        return total_collected

    def collect_time_entries(self, work_package_id: Optional[int] = None, incremental: bool = True):
        """Collect time entries data"""

        self.logger.info(f"Starting time entries collection for work package {work_package_id or 'all'}")

        # Build filters
        filters = []
        if work_package_id:
            filters.append({
                "workPackage": {
                    "operator": "=",
                    "values": [str(work_package_id)]
                }
            })

        # Incremental sync
        if incremental:
            last_sync = self._get_last_sync_time('_raw_openproject_api_time_entries')
            if last_sync:
                filters.append({
                    "updatedAt": {
                        "operator": ">=", 
                        "values": [last_sync.isoformat()]
                    }
                })

        params = {
            'pageSize': self.batch_size,
            'offset': 1
        }

        if filters:
            params['filters'] = json.dumps(filters)

        page = 1
        total_collected = 0

        while True:
            params['offset'] = page

            response = self._make_request('/api/v3/time_entries', params)

            # Store raw response
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
                break

            total_collected += len(elements)
            page += 1

        self.logger.info(f"Time entries collection completed. Total: {total_collected}")
        return total_collected

    def collect_metadata(self):
        """Collect metadata (statuses, types, priorities, activities)"""

        metadata_endpoints = [
            ('/api/v3/statuses', '_raw_openproject_api_statuses'),
            ('/api/v3/types', '_raw_openproject_api_types'),
            ('/api/v3/priorities', '_raw_openproject_api_priorities'),
            ('/api/v3/time_entries/activities', '_raw_openproject_api_activities')
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
                self.logger.error(f"Failed to collect from {endpoint}")

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

        while True:
            params['offset'] = page

            response = self._make_request(endpoint, params)

            # Store raw response
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
                break

            total_collected += len(elements)
            page += 1

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
            # Collect metadata first (always full sync for metadata)
            self.logger.info("=== Collecting Metadata ===")
            collection_stats['metadata'] = self.collect_metadata()

            # Collect core entities
            self.logger.info("=== Collecting Core Entities ===")
            collection_stats['projects'] = self.collect_projects()
            collection_stats['users'] = self.collect_users()

            # Collect project-specific data
            if project_ids:
                for project_id in project_ids:
                    self.logger.info(f"=== Collecting Data for Project {project_id} ===")
                    collection_stats['work_packages'] += self.collect_work_packages(project_id, incremental)
                    collection_stats['time_entries'] += self.collect_time_entries(None, incremental)
                    collection_stats['versions'] += self.collect_versions(project_id)
            else:
                # Collect all data
                self.logger.info("=== Collecting All Project Data ===")
                collection_stats['work_packages'] = self.collect_work_packages(None, incremental)
                collection_stats['time_entries'] = self.collect_time_entries(None, incremental)
                collection_stats['versions'] = self.collect_versions()

            # Log final statistics
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

# CLI interface for the collector
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='OpenProject Data Collector')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--projects', nargs='+', type=int, help='Specific project IDs to collect')
    parser.add_argument('--full', action='store_true', help='Force full sync (not incremental)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    # Create collector
    collector = OpenProjectCollector(args.config)

    if args.verbose:
        collector.logger.setLevel(logging.DEBUG)

    # Run collection
    try:
        incremental = not args.full
        stats = collector.run_collection(args.projects, incremental)
        print(f"Collection completed. Total records: {sum(stats.values())}")
    except Exception as e:
        print(f"Collection failed: {e}")
        exit(1)
```

This is the first part of the complete setup guide. Would you like me to continue with the remaining components (Extractor, Converter, Grafana configuration, and automation scripts)?
