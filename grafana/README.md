# 📊 Grafana Configuration Files

This directory contains Grafana dashboard and datasource configurations for OpenProject DevLake integration.

---

## 📁 Directory Contents

```
grafana/
├── datasource.yaml           # MySQL datasource configuration
└── dashboards/
    ├── team-productivity.json      # Team performance metrics (11 panels)
    ├── sprint-progress.json        # Sprint & project tracking (8 panels)
    └── issues-metrics-dora.json    # DORA & engineering metrics (10 panels)
```

---

## 🔧 Files Overview

### datasource.yaml
**Purpose:** Configures MySQL connection to DevLake database

**Configuration:**
- **Host:** localhost:3307
- **Database:** lake
- **User:** merico
- **Password:** merico (should match your DevLake setup)

**Used by:** Automated setup script (`scripts/setup_grafana.py`)

### dashboards/team-productivity.json
**Dashboard:** Team Productivity

**Panels (11):**
1. Active Team Members - Current team size
2. Issues Completed (30 Days) - Recent completion count
3. Completion Rate Trends - 7-day rolling average
4. Team Productivity by Assignee - Individual comparison
5. Issue Resolution Time - Average days by person
6. Time Logging Analysis - Hours logged per member
7. Activity Heatmap - Weekly patterns
8. Issue Aging - Open issue duration
9. Status Distribution - Current workload
10. Priority Distribution - Work prioritization
11. Recent Activity Timeline - Latest updates

**Best for:** Daily standups, sprint retros, performance tracking

### dashboards/sprint-progress.json
**Dashboard:** Sprint Progress & Projects

**Panels (8):**
1. Sprint Overview - All active sprints
2. Project Health - Cross-project metrics
3. Sprint Progress Table - Detailed breakdown
4. Issue Priority Distribution - Workload analysis
5. Weekly Progress - Trend charts
6. Velocity Tracking - Sprint-over-sprint
7. Burndown Charts - Sprint progress
8. Team Capacity - Resource utilization

**Best for:** Sprint planning, status reports, resource allocation

### dashboards/issues-metrics-dora.json
**Dashboard:** Issues Metrics & DORA

**Panels (10):**
1. Lead Time for Changes - Average delivery time
2. Deployment Frequency - Release cadence
3. Change Failure Rate - Quality metrics
4. Mean Time to Recovery - Incident response
5. Issue Metrics by Type - Category performance
6. Resolution Time Distribution - Statistical analysis
7. Time Logging by Project - Investment tracking
8. Issue Age Distribution - Aging patterns
9. Priority vs Resolution Time - Priority impact
10. Monthly Trends - Historical patterns

**Best for:** DevOps metrics, process improvement, executive reporting

---

## 🚀 How to Use These Files

### Automated Import (Recommended)

Run the setup script:
```bash
python3 scripts/setup_grafana.py --url http://localhost:3001 --password YOUR_PASSWORD
```

This will automatically:
1. Create the MySQL datasource
2. Import all 3 dashboards
3. Configure everything properly

### Manual Import

1. **Add Datasource:**
   - Grafana → Configuration → Data sources → Add data source
   - Select MySQL
   - Copy settings from `datasource.yaml`
   - Save & test

2. **Import Dashboards:**
   - Grafana → + → Import
   - Upload each JSON file from `dashboards/`
   - Select datasource: "DevLake MySQL"
   - Click Import

---

## 🔧 Customization

### Modify Datasource

Edit `datasource.yaml` if you have different:
- Database host/port
- Database name
- User credentials
- Connection settings

### Modify Dashboards

**Option 1: Edit in Grafana UI**
- Open dashboard
- Click panel title → Edit
- Modify query, visualization, or settings
- Save dashboard
- Export JSON to update file

**Option 2: Edit JSON Directly**
- Open dashboard JSON file
- Modify queries, settings, or layout
- Re-import to Grafana

---

## 📊 Dashboard Queries

All dashboards query these DevLake tables:
- `issues` - Core issue data
- `accounts` - User/team information
- `boards` - Project structure
- `issue_worklogs` - Time tracking
- `sprint_issues` - Sprint relationships
- `sprints` - Sprint definitions

**Filter pattern:** `id LIKE 'openproject:%'`  
All queries filter for OpenProject-specific data.

---

## 🔍 Troubleshooting

### Datasource Connection Failed

1. Verify MySQL is running:
   ```bash
   docker ps | grep mysql
   ```

2. Test connection:
   ```bash
   mysql -h localhost -P 3307 -u merico -pmerico lake -e "SHOW TABLES;"
   ```

3. Check datasource settings in Grafana

### Dashboard Shows "No Data"

1. Verify data exists:
   ```bash
   mysql -h localhost -P 3307 -u merico -pmerico lake -e \
   "SELECT COUNT(*) FROM issues WHERE id LIKE 'openproject:%';"
   ```

2. Check time range in dashboard (top-right)

3. Edit panel and test query

### Import Errors

1. Ensure Grafana version compatibility (v8.0+)
2. Check JSON syntax is valid
3. Verify datasource name matches
4. Try manual import through UI

---

## 📈 Dashboard Maintenance

### Update Dashboards

1. Make changes in Grafana UI
2. Export dashboard JSON
3. Replace file in `dashboards/` directory
4. Commit to Git

### Backup Dashboards

```bash
# Export all dashboards
cd grafana/dashboards
for dashboard in *.json; do
    cp "$dashboard" "backup_$(date +%Y%m%d)_$dashboard"
done
```

### Version Control

Dashboard JSON files are tracked in Git:
- Commit changes with descriptive messages
- Review diffs before committing
- Tag major versions

---

## 🔐 Security Notes

### Datasource Configuration

The `datasource.yaml` contains database credentials:
- Use secure passwords in production
- Consider environment variables for passwords
- Restrict file permissions: `chmod 600 datasource.yaml`

### Dashboard Access

Configure Grafana permissions:
- Create teams for different access levels
- Set folder permissions appropriately
- Enable authentication (LDAP, OAuth, etc.)

---

## 📚 Additional Resources

- **Setup Guide:** [../GRAFANA_QUICKSTART.md](../GRAFANA_QUICKSTART.md)
- **Quick Reference:** [../GRAFANA_SETUP_CHEATSHEET.md](../GRAFANA_SETUP_CHEATSHEET.md)
- **Dashboard Docs:** [../GRAFANA_README.md](../GRAFANA_README.md)
- **Grafana Docs:** https://grafana.com/docs/
- **DevLake Schema:** https://devlake.apache.org/docs/DataModels/

---

## ✅ Quick Checks

Before using these files:

- [ ] DevLake MySQL is running on port 3307
- [ ] Database credentials match your setup
- [ ] Data exists in DevLake tables
- [ ] Grafana is installed and accessible
- [ ] You have Grafana admin credentials

All checked? Run the setup script and you're ready to go!

---

**Need help?** See the main documentation in the repository root.
