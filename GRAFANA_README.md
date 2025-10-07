# OpenProject DevLake Grafana Integration

This project provides comprehensive Grafana dashboards for visualizing OpenProject data through DevLake integration.

## 📊 Dashboard Overview

### Team Productivity Dashb#### Network Access
- Default configuration allows localhost access only
- For remote access, configure Grafana properly:
```ini
[server]
http_addr = 0.0.0.0
http_port = 3001
```*Active Team Members**: Real-time count of team members working on issues
- **Issues Completed**: 30-day completion metrics
- **Team Productivity by Assignee**: Individual performance tracking
- **Completion Rate Trends**: 7-day rolling completion rates
- **Issue Resolution Time**: Average time to resolve issues by assignee
- **Time Logging Analysis**: Hours logged by team members
- **Activity Heatmap**: Weekly activity patterns
- **Issue Aging**: Track how long issues remain open
- **Status Distribution**: Current issue status breakdown
- **Recent Activity**: Latest team actions and updates

### Sprint Progress Dashboard
- **Sprint Overview**: All sprints with completion metrics
- **Project Health**: Cross-project status tracking
- **Sprint Progress Table**: Detailed sprint breakdown with hours
- **Issue Priority Distribution**: Priority-based workload analysis
- **Weekly Progress**: Sprint completion trends over time
- **Velocity Tracking**: Sprint-over-sprint velocity analysis
- **Burndown Charts**: Sprint progress visualization
- **Team Capacity**: Resource allocation and utilization

### Issues Metrics & DORA Dashboard
- **Lead Time for Changes**: Average time from creation to completion
- **Deployment Frequency**: How often changes are deployed
- **Change Failure Rate**: Percentage of deployments causing issues
- **Mean Time to Recovery**: Time to recover from failures
- **Issue Metrics by Type**: Performance by issue categories
- **Resolution Time Distribution**: Statistical analysis of completion times
- **Time Logging by Project**: Project-wise time investment
- **Issue Age Distribution**: Aging analysis of open issues
- **Priority vs Resolution Time**: Priority impact on completion speed
- **Monthly Trends**: Historical performance patterns

## 🚀 Quick Start

### Prerequisites
- DevLake MySQL database running on `localhost:3307`
- Python 3.x with required packages
- Sudo privileges for Grafana installation

### 1. Install Grafana
```bash
# Run the automated installation script
./scripts/install_grafana.sh

# Manual installation (alternative)
# Ubuntu/Debian:
sudo apt-get install -y grafana

# CentOS/RHEL/Fedora:
sudo yum install -y grafana
```

### 2. Start Grafana Service
```bash
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

### 3. Access Grafana
- Open browser to: http://localhost:3001
- Default login: admin/admin
- **Change the password immediately!**

### 4. Setup Dashboards
```bash
# Install Python dependencies if needed
pip install requests pyyaml tabulate mysql-connector-python

# Run dashboard setup (replace YOUR_PASSWORD with your actual password)
python3 scripts/setup_grafana.py --url http://localhost:3001 --password YOUR_PASSWORD
```

### 5. Preview Dashboard Data
```bash
# Test all dashboard queries
python3 scripts/dashboard_preview.py --dashboard all

# Test specific dashboards
python3 scripts/dashboard_preview.py --dashboard team
python3 scripts/dashboard_preview.py --dashboard sprint
python3 scripts/dashboard_preview.py --dashboard dora
```

## 📁 File Structure

```
grafana/
├── datasource.yaml              # MySQL DevLake datasource configuration
└── dashboards/
    ├── team-productivity.json   # Team performance dashboard (11 panels)
    ├── sprint-progress.json     # Sprint and project tracking (8 panels)
    └── issues-metrics-dora.json # DORA metrics and analytics (10 panels)

scripts/
├── install_grafana.sh          # Automated Grafana installation
├── setup_grafana.py           # Dashboard and datasource setup
└── dashboard_preview.py       # Query testing and data preview
```

## 🔧 Configuration

### Database Connection
Edit `config.yaml` to configure your DevLake database:
```yaml
database:
  host: localhost
  port: 3307
  user: merico
  password: merico
  database: lake
```

### Grafana Settings
The datasource configuration in `grafana/datasource.yaml` connects to:
- **Host**: localhost:3307
- **Database**: lake
- **User**: merico
- **Password**: merico

## 📈 Dashboard Features

### Team Productivity Dashboard
- **Real-time Metrics**: Live data from DevLake
- **Time Tracking**: Detailed work hour analysis
- **Performance Trends**: Historical productivity patterns
- **Individual Insights**: Per-team-member analytics

### Sprint Progress Dashboard  
- **Sprint Health**: Overall sprint completion status
- **Project Overview**: Cross-project visibility
- **Resource Planning**: Team capacity and allocation
- **Progress Tracking**: Burndown and velocity charts

### DORA Metrics Dashboard
- **Lead Time**: Creation to completion analysis
- **Deployment Frequency**: Release cadence tracking
- **Failure Rate**: Quality and reliability metrics
- **Recovery Time**: Incident response performance

## 🛠️ Troubleshooting

### Common Issues

#### Grafana Connection Errors
```bash
# Check Grafana status
sudo systemctl status grafana-server

# View Grafana logs
sudo journalctl -u grafana-server -f

# Restart Grafana
sudo systemctl restart grafana-server
```

#### Database Connection Issues
```bash
# Test DevLake connection
python3 test_connection.py

# Check MySQL service
sudo systemctl status mysql

# Verify database access
mysql -h localhost -P 3307 -u merico -p lake
```

#### Dashboard Query Errors
```bash
# Test specific dashboard queries
python3 scripts/dashboard_preview.py --dashboard team

# Check database schema
python3 -c "
import mysql.connector, yaml
config = yaml.safe_load(open('config.yaml'))
conn = mysql.connector.connect(**config['database'])
cursor = conn.cursor()
cursor.execute('SHOW TABLES')
print('Available tables:', cursor.fetchall())
"
```

### Performance Optimization

#### Large Dataset Handling
- Dashboard queries include `LIMIT` clauses for performance
- Time-based filtering reduces data load
- Indexes on DevLake tables improve query speed

#### Memory Usage
- Grafana default memory limits may need adjustment for large datasets
- Configure in `/etc/grafana/grafana.ini`:
```ini
[server]
# Increase memory limits if needed
max_connections = 100
```

## 🔐 Security Considerations

### Default Passwords
- **CRITICAL**: Change Grafana admin password immediately
- Use strong passwords for database connections
- Consider enabling HTTPS for production use

### Network Access
- Default configuration allows localhost access only
- For remote access, configure Grafana properly:
```ini
[server]
http_addr = 0.0.0.0
http_port = 3000
```

### Database Permissions
- DevLake user should have read-only access for dashboards
- Consider creating dedicated Grafana database user:
```sql
CREATE USER 'grafana'@'localhost' IDENTIFIED BY 'secure_password';
GRANT SELECT ON lake.* TO 'grafana'@'localhost';
```

## 📊 Data Sources

### DevLake Schema Tables
The dashboards query these main DevLake tables:
- `issues` - Core issue data with status, assignee, timing
- `accounts` - User/team member information  
- `boards` - Project/board structure
- `issue_worklogs` - Time logging and work tracking
- `sprint_issues` - Sprint assignment relationships
- `sprints` - Sprint/version definitions

### Query Patterns
- **Time Windows**: Most queries use 30-day windows for recent data
- **Filtering**: OpenProject-specific filtering with `'openproject:%'` patterns
- **Aggregation**: Grouped by assignee, project, sprint for meaningful insights
- **Performance**: Optimized with proper joins and indexes

## 🤝 Contributing

### Adding New Dashboards
1. Create dashboard JSON in `grafana/dashboards/`
2. Add queries to `scripts/dashboard_preview.py` for testing
3. Update `scripts/setup_grafana.py` to include new dashboard
4. Test thoroughly with preview script
5. Document new panels in this README

### Query Development
1. Test queries in `dashboard_preview.py` first
2. Use proper DevLake schema field names
3. Include appropriate time filters and limits
4. Follow existing query patterns for consistency

## 📞 Support

### Getting Help
- Check the troubleshooting section above
- Verify DevLake database connectivity
- Ensure Grafana service is running properly
- Test dashboard queries individually

### Logs and Debugging  
- **Grafana logs**: `sudo journalctl -u grafana-server -f`
- **Setup script logs**: Check console output with `--verbose` flag
- **Database queries**: Use dashboard preview script for testing
- **DevLake logs**: Check DevLake service logs if data issues occur

---

## 🎯 Summary

This Grafana integration provides comprehensive visualization for OpenProject DevLake data with:

✅ **29+ Visualization Panels** across 3 specialized dashboards  
✅ **Automated Setup Scripts** for easy deployment  
✅ **DORA Metrics** for engineering performance tracking  
✅ **Team Productivity** insights and analytics  
✅ **Sprint Progress** monitoring and planning  
✅ **Query Testing Framework** for reliability  
✅ **Comprehensive Documentation** for setup and troubleshooting  

**Ready to visualize your OpenProject data!** 🚀