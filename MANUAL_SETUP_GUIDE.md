📊 Manual Grafana Dashboard Setup Guide
===========================================

Since the automated script is having authentication issues, here's how to set up the dashboards manually through the Grafana web interface:

## Step 1: Access Grafana
🌐 Open your browser and go to: http://localhost:3001
🔐 Login with: admin / admin

## Step 2: Add MySQL Datasource

1. **Navigate to Datasources:**
   - Click the gear icon (⚙️) in the left sidebar
   - Click "Data sources"
   - Click "Add data source"

2. **Configure MySQL Datasource:**
   - Select "MySQL" from the list
   - Fill in these details:
   
   ```
   Name: DevLake MySQL
   Host: localhost:3307
   Database: lake
   User: merico
   Password: merico
   ```

3. **Test Connection:**
   - Scroll down and click "Save & test"
   - You should see a green "Database Connection OK" message

## Step 3: Create Dashboard Folder

1. **Create Folder:**
   - Click the "+" icon in the left sidebar
   - Click "Folder"
   - Name: "OpenProject"
   - Click "Create"

## Step 4: Import Dashboards

### Method A: Import JSON Files (Recommended)

1. **For each dashboard:**
   - Click "+" → "Import"
   - Click "Upload JSON file"
   - Select one of these files from your project:
     - `grafana/dashboards/team-productivity.json`
     - `grafana/dashboards/sprint-progress.json`
     - `grafana/dashboards/issues-metrics-dora.json`

2. **Configure Import:**
   - Set folder to "OpenProject"
   - Select datasource: "DevLake MySQL"
   - Click "Import"

3. **Repeat for all 3 dashboards**

### Method B: Manual Dashboard Creation

If JSON import doesn't work, here are the key queries for manual setup:

#### Team Productivity Dashboard Queries:

**Active Team Members:**
```sql
SELECT COUNT(DISTINCT assignee_id) as active_members 
FROM issues 
WHERE assignee_id IS NOT NULL 
AND status IN ('TODO', 'IN_PROGRESS') 
AND id LIKE 'openproject:%'
```

**Issues Completed (30 Days):**
```sql
SELECT COUNT(*) as completed 
FROM issues 
WHERE status = 'DONE' 
AND resolution_date >= DATE_SUB(NOW(), INTERVAL 30 DAY) 
AND id LIKE 'openproject:%'
```

**Team Productivity by Assignee:**
```sql
SELECT 
    a.full_name as assignee_name,
    COUNT(CASE WHEN i.status = 'DONE' THEN 1 END) as completed,
    COUNT(CASE WHEN i.status IN ('TODO', 'IN_PROGRESS') THEN 1 END) as active
FROM issues i
JOIN accounts a ON i.assignee_id = a.id
WHERE i.id LIKE 'openproject:%'
GROUP BY i.assignee_id, a.full_name
ORDER BY completed DESC
LIMIT 10
```

#### Sprint Progress Dashboard Queries:

**Project Health Overview:**
```sql
SELECT 
    b.name as 'Project',
    COUNT(i.id) as 'Total Issues',
    COUNT(CASE WHEN i.status = 'DONE' THEN 1 END) as 'Completed',
    COUNT(CASE WHEN i.status IN ('TODO', 'IN_PROGRESS') THEN 1 END) as 'Active',
    ROUND((COUNT(CASE WHEN i.status = 'DONE' THEN 1 END) * 100.0) / NULLIF(COUNT(i.id), 0), 1) as 'Completion %'
FROM issues i
LEFT JOIN boards b ON i.original_project = b.id
WHERE i.id LIKE 'openproject:%'
GROUP BY b.name
ORDER BY 'Completion %' DESC, 'Total Issues' DESC
LIMIT 15
```

#### DORA Metrics Dashboard Queries:

**Lead Time for Changes:**
```sql
SELECT 
    ROUND(AVG(DATEDIFF(resolution_date, created_date)), 1) as avg_lead_time_days
FROM issues 
WHERE status = 'DONE' 
AND resolution_date IS NOT NULL 
AND created_date IS NOT NULL 
AND id LIKE 'openproject:%'
```

**Issue Metrics by Type:**
```sql
SELECT 
    type as 'Issue Type',
    COUNT(*) as 'Total',
    COUNT(CASE WHEN status = 'DONE' THEN 1 END) as 'Completed',
    ROUND((COUNT(CASE WHEN status = 'DONE' THEN 1 END) * 100.0) / COUNT(*), 1) as 'Completion %',
    ROUND(AVG(CASE WHEN status = 'DONE' AND resolution_date IS NOT NULL 
              THEN DATEDIFF(resolution_date, created_date) END), 1) as 'Avg Lead Time (Days)'
FROM issues 
WHERE id LIKE 'openproject:%'
GROUP BY type
ORDER BY 'Total' DESC
```

## Step 5: Verify Data

After importing/creating the dashboards:

1. **Check Data Appears:**
   - Navigate to each dashboard
   - Verify panels show data (not "No data")
   - Check time ranges are appropriate

2. **Test Queries:**
   - If panels show "No data", edit the panel
   - Go to the Query tab
   - Click "Run Query" to test

## Step 6: Customize (Optional)

- Adjust time ranges (top-right corner)
- Modify panel titles and descriptions
- Add alerts if needed
- Set refresh intervals

## Troubleshooting

**No Data Issues:**
- Verify MySQL datasource connection
- Check DevLake database has data: `SELECT COUNT(*) FROM issues WHERE id LIKE 'openproject:%'`
- Ensure time ranges include your data

**Connection Issues:**
- Verify DevLake MySQL is running on localhost:3307
- Test database connection: `mysql -h localhost -P 3307 -u merico -p lake`

**Query Errors:**
- Check table names match your DevLake schema
- Verify field names (use DESCRIBE tables if needed)

## Expected Results

Once set up correctly, you should see:
- **Team Dashboard**: ~20 active members, 1800+ completed issues
- **Sprint Dashboard**: Project breakdown and progress metrics  
- **DORA Dashboard**: ~1.4 days average lead time, completion trends

---

🎯 **Success!** Your Grafana dashboards should now display comprehensive OpenProject analytics!