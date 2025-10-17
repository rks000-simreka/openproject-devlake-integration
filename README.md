# OpenProject DevLake Integration

A complete data integration pipeline that collects, transforms, and loads OpenProject data into Apache DevLake for analytics and visualization.

---

## 🚀 **New User? Start Here!**

### 👥 **For Colleagues Setting Up Grafana:**
**→ [GETTING_STARTED.md](GETTING_STARTED.md) ← Click here to begin!**

This guide will walk you through setting up Grafana dashboards in ~10 minutes.

---

## 🎯 Overview

This integration enables you to:
- **Collect** work packages, projects, users, and time entries from OpenProject
- **Transform** data through tool-layer and domain-layer schemas  
- **Analyze** project metrics, team performance, and work patterns
- **Visualize** data in Grafana dashboards

## 📚 Documentation

- **[GRAFANA_QUICKSTART.md](GRAFANA_QUICKSTART.md)** - Complete Grafana setup guide for colleagues (START HERE for visualization)
- **[GRAFANA_README.md](GRAFANA_README.md)** - Detailed Grafana documentation and dashboard overview
- **[MANUAL_SETUP_GUIDE.md](MANUAL_SETUP_GUIDE.md)** - Manual dashboard import instructions
- **[open_project_guide/](open_project_guide/)** - OpenProject API setup guides

## 📊 Pipeline Architecture

```
OpenProject API → Raw Tables → Tool Tables → Domain Tables → Analytics
     ↓              ↓            ↓            ↓            ↓
  Collector     Extractor    Converter    DevLake      Grafana
```

### Data Flow
1. **Collection**: Fetch data from OpenProject API → `_raw_*` tables
2. **Extraction**: Parse JSON → structured `_tool_*` tables  
3. **Conversion**: Map to DevLake domain tables (`issues`, `boards`, etc.)
4. **Analysis**: Query domain tables for insights and dashboards

## 🚀 Quick Start

> **👥 For Colleagues:** If you only need to set up Grafana dashboards (visualization), skip to **[Grafana Setup Guide](GRAFANA_QUICKSTART.md)** - this is a complete standalone guide.

### Prerequisites
- Python 3.8+
- MySQL 8.0+ (DevLake database)
- OpenProject instance with API access
- Required Python packages: `mysql-connector-python`, `PyYAML`, `requests`

### Installation
```bash
# Clone or create the project directory
mkdir openproject-devlake-integration
cd openproject-devlake-integration

# Install dependencies
pip install -r requirements.txt

# Set up database schema
python3 database_setup.py

# Test connections
python3 test_connection.py
```

### Configuration
Edit `config.yaml`:
```yaml
openproject:
  base_url: "https://your-openproject.domain.com"
  api_key: "your-api-key"
  
database:
  host: "localhost"
  port: 3307
  database: "lake"
  user: "merico"
  password: "merico"
```

### Run Pipeline
```bash
# Complete pipeline (recommended)
python3 run_pipeline.py --verbose

# Individual components
python3 collectors/openproject_collector.py
python3 extractors/openproject_extractor.py  
python3 converters/openproject_converter.py
```

## 📁 Project Structure

```
openproject-devlake-integration/
├── collectors/
│   └── openproject_collector.py     # API data collection
├── extractors/
│   └── openproject_extractor.py     # JSON to tool tables
├── converters/
│   └── openproject_converter.py     # Tool to domain mapping
├── schema/
│   ├── 01_create_raw_tables.sql     # Raw data schema
│   └── 02_create_tool_tables.sql    # Tool layer schema
├── logs/                            # Pipeline execution logs
├── config.yaml                      # Configuration file
├── database_setup.py               # Database initialization
├── test_connection.py              # Connection testing
├── run_pipeline.py                 # Complete pipeline orchestrator
└── requirements.txt                # Python dependencies
```

## 🏗️ Database Schema

### Raw Layer (`_raw_*`)
- Stores unprocessed JSON responses from OpenProject API
- Tables: `_raw_openproject_api_work_packages`, `_raw_openproject_api_projects`, etc.

### Tool Layer (`_tool_*`)  
- Structured, OpenProject-specific tables
- Tables: `_tool_openproject_work_packages`, `_tool_openproject_projects`, etc.

### Domain Layer (DevLake Standard)
- Standardized schema for cross-tool analytics
- Tables: `issues`, `boards`, `accounts`, `issue_worklogs`, etc.

## 📈 Data Transformation Details

### Work Packages → Issues
| OpenProject Field | DevLake Field | Transformation |
|-------------------|---------------|----------------|
| `id` | `issue_key` | Direct mapping |
| `subject` | `title` | Direct mapping |
| `status.name` | `status` | Mapped to standard values |
| `type.name` | `type` | Mapped to REQUIREMENT/BUG/etc. |
| `priority.name` | `priority` | Direct mapping |
| `assignee` | `assignee_id/name` | User ID generation |

### Type Mappings
- **Task** → REQUIREMENT
- **Bug** → BUG  
- **Feature** → REQUIREMENT
- **User Story** → REQUIREMENT

### Status Mappings
- **New/Open** → TODO
- **In Progress** → IN_PROGRESS  
- **Resolved/Closed** → DONE
- **On Hold** → TODO

## 🔧 Configuration Options

### Pipeline Settings
```yaml
pipeline:
  batch_size: 100                    # Records per batch
  rate_limit_rpm: 60                # API requests per minute
  retry_attempts: 3                 # Failed request retries
  max_pages_per_collection: 1000    # Safety limit for pagination
```

### Collection Settings  
```yaml
collection:
  incremental_sync: true            # Only collect new/changed data
  sync_interval_hours: 6           # How often to run incremental sync
  full_sync_interval_days: 7       # How often to run full sync
  projects: []                     # Specific project IDs (empty = all)
```

## 📊 Analytics & Queries

### Sample Queries

**Work Package Distribution by Status:**
```sql
SELECT status, COUNT(*) as count 
FROM issues 
WHERE original_project IS NOT NULL
GROUP BY status;
```

**Team Productivity (Time Logged):**
```sql
SELECT 
  assignee_name,
  COUNT(*) as issues_assigned,
  SUM(time_spent_minutes)/60 as hours_logged
FROM issues 
WHERE assignee_name IS NOT NULL
GROUP BY assignee_name
ORDER BY hours_logged DESC;
```

**Project Health Metrics:**
```sql
SELECT 
  original_project,
  COUNT(*) as total_issues,
  SUM(CASE WHEN status = 'DONE' THEN 1 ELSE 0 END) as completed,
  AVG(lead_time_minutes)/60 as avg_lead_time_hours
FROM issues
GROUP BY original_project;
```

## 🔍 Monitoring & Troubleshooting

### Logs
- **Pipeline Log**: `logs/pipeline.log`
- **Database Setup**: `logs/database_setup.log` 
- **Component Logs**: Each component logs to `logs/openproject_pipeline.log`

### Common Issues

**API Rate Limiting:**
```bash
# Reduce rate limit in config.yaml
rate_limit_rpm: 30  # Default is 60
```

**Memory Issues with Large Datasets:**
```bash
# Reduce batch size
batch_size: 50  # Default is 100
```

**Connection Timeouts:**
```bash
# Increase timeout
timeout_seconds: 60  # Default is 30
```

### Data Validation
```bash
# Check collection results
python3 -c "
import mysql.connector
# Connect and check record counts
"

# Verify domain conversion
SELECT 
  (SELECT COUNT(*) FROM _tool_openproject_work_packages) as tool_records,
  (SELECT COUNT(*) FROM issues) as domain_records;
```

## 🚀 Production Deployment

### Automated Scheduling
```bash
# Add to crontab for daily sync
0 2 * * * /usr/bin/python3 /path/to/run_pipeline.py >> /var/log/openproject-sync.log 2>&1
```

### Performance Optimization
- **Database Indexing**: Ensure proper indexes on frequently queried columns
- **Incremental Sync**: Enable for large datasets
- **Connection Pooling**: Consider for high-frequency runs

### Security
- Store API keys in environment variables or secure key management
- Use database connection pooling
- Implement proper logging rotation

## 📋 Pipeline Results

### Current Integration Status ✅

**Data Collection:**
- ✅ 2,235 raw records collected from OpenProject API
- ✅ Work packages, projects, users, time entries

**Data Extraction:**  
- ✅ 2,222 tool-layer records extracted and structured
- ✅ JSON parsing and normalization completed

**Domain Conversion:**
- ✅ 4,426 domain records created across all tables
- ✅ 2,068 issues (work packages)
- ✅ 11 boards (projects) 
- ✅ 71 accounts (users)
- ✅ 41 issue worklogs (time entries)
- ✅ 2,068 board-issue relationships
- ✅ 167 sprint-issue relationships

## 🛠️ Development

### Adding New Data Types
1. Update collector to fetch additional API endpoints
2. Create corresponding tool tables in schema
3. Add extraction logic in extractor  
4. Implement domain mapping in converter

### Custom Transformations
- Modify mapping functions in `converters/openproject_converter.py`
- Add custom business logic for your organization's needs
- Update domain table schemas if required

## 📚 Resources

- [Apache DevLake Documentation](https://devlake.apache.org/)
- [OpenProject API Documentation](https://docs.openproject.org/api/)
- [MySQL Connector/Python](https://dev.mysql.com/doc/connector-python/en/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with your OpenProject instance
5. Submit a pull request with detailed description

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Success!** 🎉 Your OpenProject data is now flowing into DevLake and ready for analytics!