# 📊 Grafana Visualization Setup Guide

**Complete guide for colleagues to set up Grafana dashboards for OpenProject DevLake Integration**

---

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start (5 Minutes)](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Verification & Testing](#verification--testing)
5. [Troubleshooting](#troubleshooting)
6. [Dashboard Overview](#dashboard-overview)

---

## Prerequisites

Before starting, ensure you have:

### ✅ Required Services Running
- **DevLake MySQL Database** running on port `3307`
- **Data already collected** in the database (run the pipeline first if not done)

### ✅ System Requirements
- **Operating System**: Linux (Ubuntu/Debian/RHEL/CentOS/Fedora)
- **Sudo privileges** for installing Grafana
- **Python 3.8+** installed
- **Internet connection** for downloading Grafana

### ✅ Verify DevLake is Running

```bash
# Check if DevLake MySQL is running
docker ps | grep mysql

# You should see something like:
# devlake-docker-mysql-1   Up   0.0.0.0:3307->3306/tcp
```

### ✅ Verify Data Exists in Database

```bash
# Test database connection
mysql -h localhost -P 3307 -u merico -pmerico lake -e "SELECT COUNT(*) as issue_count FROM issues WHERE id LIKE 'openproject:%';"

# You should see a count > 0 if data collection was successful
```

---

## Quick Start

### Step 1: Clone/Download the Repository

```bash
# If you're cloning from Git
git clone <repository-url>
cd openproject-devlake-integration

# OR if you received a ZIP file
unzip openproject-devlake-integration.zip
cd openproject-devlake-integration
```

### Step 2: Install Python Dependencies

```bash
# Install required Python packages
pip3 install -r requirements.txt
```

### Step 3: Install Grafana

```bash
# Make the script executable
chmod +x scripts/install_grafana.sh

# Run the installation script
./scripts/install_grafana.sh
```

**What this script does:**
- ✅ Detects your Linux distribution
- ✅ Adds Grafana repository
- ✅ Installs Grafana
- ✅ Configures Grafana to run on port **3001**
- ✅ Starts Grafana service
- ✅ Enables auto-start on boot

**Expected Output:**
```
✅ Grafana is running successfully!
✅ Grafana Installation Complete!

🌐 Access Grafana:
   URL: http://localhost:3001
   Username: admin
   Password: admin
```

### Step 4: Access Grafana

1. Open your browser
2. Navigate to: **http://localhost:3001**
3. Login with:
   - **Username:** `admin`
   - **Password:** `admin`
4. **Change the password immediately** (Grafana will prompt you)

### Step 5: Setup Dashboards

```bash
# Run the automated setup script
# Replace YOUR_NEW_PASSWORD with the password you just set in Grafana
python3 scripts/setup_grafana.py --url http://localhost:3001 --password YOUR_NEW_PASSWORD
```

**What this script does:**
- ✅ Creates MySQL datasource connection to DevLake
- ✅ Creates "OpenProject" folder
- ✅ Imports 3 pre-built dashboards:
  - Team Productivity Dashboard
  - Sprint Progress & Projects Dashboard
  - Issues Metrics & DORA Dashboard

**Expected Output:**
```
✅ Grafana connection successful
✅ Datasource configured successfully
✅ Folder 'OpenProject' created
✅ Dashboard 'Team Productivity' created/updated
✅ Dashboard 'Sprint Progress & Projects' created/updated
✅ Dashboard 'Issues Metrics & DORA' created/updated
🎉 Grafana setup completed successfully!
```

### Step 6: View Your Dashboards

1. In Grafana, click **Dashboards** (4 squares icon) in the left sidebar
2. Navigate to the **OpenProject** folder
3. Click on any dashboard to view your data

**🎉 You're done! Your Grafana dashboards are ready.**

---

## Detailed Setup

### Option A: Automated Setup (Recommended)

Follow the [Quick Start](#quick-start) section above.

### Option B: Manual Setup (If Automated Fails)

If the automated scripts have issues, follow these manual steps:

#### 1. Install Grafana Manually

**For Ubuntu/Debian:**
```bash
sudo apt-get install -y software-properties-common wget
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt-get update
sudo apt-get install -y grafana
```

**For RHEL/CentOS/Fedora:**
```bash
sudo tee /etc/yum.repos.d/grafana.repo <<EOF
[grafana]
name=grafana
baseurl=https://rpm.grafana.com
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://rpm.grafana.com/gpg.key
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
EOF
sudo yum install -y grafana
```

#### 2. Configure Grafana Port

```bash
# Change port to 3001 to avoid conflicts
sudo sed -i 's/;http_port = 3000/http_port = 3001/' /etc/grafana/grafana.ini
sudo sed -i 's/#http_port = 3000/http_port = 3001/' /etc/grafana/grafana.ini
```

#### 3. Start Grafana Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

# Verify it's running
sudo systemctl status grafana-server
```

#### 4. Manual Dashboard Import

1. **Access Grafana:** http://localhost:3001 (admin/admin)

2. **Add MySQL Datasource:**
   - Click gear icon (⚙️) → **Data sources** → **Add data source**
   - Select **MySQL**
   - Configure:
     - **Name:** `DevLake MySQL`
     - **Host:** `localhost:3307`
     - **Database:** `lake`
     - **User:** `merico`
     - **Password:** `merico`
   - Click **Save & test**

3. **Create Folder:**
   - Click **+** → **Folder**
   - Name: `OpenProject`
   - Click **Create**

4. **Import Dashboards:**
   - Click **+** → **Import**
   - Click **Upload JSON file**
   - Select from: `grafana/dashboards/`
     - `team-productivity.json`
     - `sprint-progress.json`
     - `issues-metrics-dora.json`
   - For each import:
     - Set folder: **OpenProject**
     - Select datasource: **DevLake MySQL**
     - Click **Import**

---

## Verification & Testing

### 1. Verify Grafana Service

```bash
# Check if Grafana is running
sudo systemctl status grafana-server

# View live logs
sudo journalctl -u grafana-server -f
```

### 2. Test Datasource Connection

In Grafana:
1. Go to **Configuration** → **Data sources**
2. Click on **DevLake MySQL**
3. Scroll down and click **Save & test**
4. Should show: **"Database Connection OK"**

### 3. Preview Dashboard Data

```bash
# Test queries from all dashboards
python3 scripts/dashboard_preview.py --dashboard all

# Test specific dashboard
python3 scripts/dashboard_preview.py --dashboard team
python3 scripts/dashboard_preview.py --dashboard sprint
python3 scripts/dashboard_preview.py --dashboard dora
```

**Expected Output:**
```
📊 Team Productivity Dashboard Data Preview
===========================================

Active Team Members:
+------------------+
| active_members   |
+------------------+
| 20               |
+------------------+

Issues Completed (30 Days):
+-----------+
| completed |
+-----------+
| 1847      |
+-----------+

... (more data)
```

### 4. Check Dashboard Panels

In Grafana:
1. Open each dashboard
2. Verify all panels show data (not "No data")
3. Check time ranges are appropriate
4. Ensure graphs and charts render correctly

---

## Troubleshooting

### Problem: Grafana Won't Start

```bash
# Check service status
sudo systemctl status grafana-server

# View detailed logs
sudo journalctl -u grafana-server -xe

# Restart service
sudo systemctl restart grafana-server
```

### Problem: Can't Access Grafana UI

1. **Check if port 3001 is open:**
   ```bash
   sudo netstat -tulpn | grep 3001
   ```

2. **Check firewall:**
   ```bash
   sudo ufw status
   sudo ufw allow 3001/tcp  # If needed
   ```

3. **Try different browser or incognito mode**

### Problem: Database Connection Failed

1. **Verify MySQL is running:**
   ```bash
   docker ps | grep mysql
   ```

2. **Test connection manually:**
   ```bash
   mysql -h localhost -P 3307 -u merico -pmerico lake -e "SHOW TABLES;"
   ```

3. **Check datasource configuration in Grafana:**
   - Host should be: `localhost:3307`
   - Database: `lake`
   - User: `merico`
   - Password: `merico`

### Problem: Dashboards Show "No Data"

1. **Verify data exists:**
   ```bash
   mysql -h localhost -P 3307 -u merico -pmerico lake -e "
   SELECT COUNT(*) as total_issues FROM issues WHERE id LIKE 'openproject:%';
   SELECT COUNT(*) as total_boards FROM boards WHERE id LIKE 'openproject:%';
   SELECT COUNT(*) as total_accounts FROM accounts WHERE id LIKE 'openproject:%';
   "
   ```

2. **If counts are 0, run the data pipeline:**
   ```bash
   python3 run_pipeline.py --verbose
   ```

3. **Check time ranges in dashboard:**
   - Click time picker (top-right)
   - Try "Last 90 days" or "Last 6 months"

### Problem: Setup Script Authentication Failed

If `setup_grafana.py` fails with authentication error:

1. **Verify Grafana admin password:**
   ```bash
   # Reset admin password if needed
   sudo grafana-cli admin reset-admin-password newpassword
   ```

2. **Use manual import instead** (see [Option B: Manual Setup](#option-b-manual-setup-if-automated-fails))

### Problem: Permission Denied Errors

```bash
# Make scripts executable
chmod +x scripts/*.sh
chmod +x scripts/*.py

# Fix ownership if needed
sudo chown -R $USER:$USER .
```

---

## Dashboard Overview

### 📈 Team Productivity Dashboard

**Purpose:** Monitor team performance, activity, and productivity metrics

**Key Panels:**
- **Active Team Members:** Current team size
- **Issues Completed:** 30-day completion count
- **Completion Rate Trends:** 7-day rolling average
- **Team Productivity by Assignee:** Individual performance comparison
- **Issue Resolution Time:** Average days to resolve by person
- **Time Logging Analysis:** Hours logged per team member
- **Activity Heatmap:** Weekly patterns
- **Issue Aging:** How long issues stay open
- **Status Distribution:** Current workload breakdown
- **Recent Activity:** Latest updates

**Use Cases:**
- Daily standup metrics
- Sprint retrospectives
- Performance reviews
- Capacity planning

### 📊 Sprint Progress & Projects Dashboard

**Purpose:** Track sprint health, project status, and velocity

**Key Panels:**
- **Sprint Overview:** All active sprints
- **Project Health:** Cross-project completion rates
- **Sprint Progress Table:** Detailed breakdown with hours
- **Issue Priority Distribution:** Workload by priority
- **Weekly Progress:** Trend analysis
- **Velocity Tracking:** Sprint-over-sprint comparison
- **Burndown Charts:** Sprint progress visualization
- **Team Capacity:** Resource utilization

**Use Cases:**
- Sprint planning
- Project status reports
- Resource allocation
- Timeline estimation

### 🎯 Issues Metrics & DORA Dashboard

**Purpose:** Engineering excellence metrics and performance indicators

**Key Panels:**
- **Lead Time for Changes:** Average delivery time
- **Deployment Frequency:** Release cadence
- **Change Failure Rate:** Quality metrics
- **Mean Time to Recovery:** Incident response
- **Issue Metrics by Type:** Performance by category
- **Resolution Time Distribution:** Statistical analysis
- **Time Logging by Project:** Investment tracking
- **Issue Age Distribution:** Aging analysis
- **Priority vs Resolution:** Priority impact on speed
- **Monthly Trends:** Historical patterns

**Use Cases:**
- DevOps metrics
- Process improvement
- Quality assessment
- Executive reporting

---

## Configuration Details

### Grafana Configuration File
**Location:** `/etc/grafana/grafana.ini`

**Key Settings:**
```ini
[server]
http_port = 3001
domain = localhost

[security]
admin_user = admin
admin_password = <your-password>

[database]
type = sqlite3
path = grafana.db
```

### Datasource Configuration
**File:** `grafana/datasource.yaml`

```yaml
datasources:
  - name: DevLake MySQL
    type: mysql
    access: proxy
    url: localhost:3307
    database: lake
    user: merico
    jsonData:
      maxOpenConns: 10
      maxIdleConns: 2
      connMaxLifetime: 14400
```

### Dashboard Files
**Location:** `grafana/dashboards/`

- `team-productivity.json` - 11 visualization panels
- `sprint-progress.json` - 8 visualization panels
- `issues-metrics-dora.json` - 10 visualization panels

---

## Advanced Configuration

### Remote Access Setup

To access Grafana from other machines:

1. **Edit Grafana config:**
   ```bash
   sudo nano /etc/grafana/grafana.ini
   ```

2. **Change server settings:**
   ```ini
   [server]
   http_addr = 0.0.0.0
   http_port = 3001
   domain = your-server-ip
   ```

3. **Restart Grafana:**
   ```bash
   sudo systemctl restart grafana-server
   ```

4. **Open firewall:**
   ```bash
   sudo ufw allow 3001/tcp
   ```

### Enable HTTPS (Production)

```bash
# Generate SSL certificate (self-signed for testing)
sudo mkdir -p /etc/grafana/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/grafana/ssl/grafana.key \
  -out /etc/grafana/ssl/grafana.crt

# Configure Grafana
sudo nano /etc/grafana/grafana.ini
```

```ini
[server]
protocol = https
http_port = 3001
cert_file = /etc/grafana/ssl/grafana.crt
cert_key = /etc/grafana/ssl/grafana.key
```

### Custom Time Ranges

Edit dashboards to adjust default time ranges:
1. Open dashboard
2. Click **Dashboard settings** (gear icon)
3. Go to **Time options**
4. Set **Auto refresh** and **Time range**

---

## Maintenance

### Regular Tasks

**Daily:**
- Monitor dashboard performance
- Check for panel errors
- Verify data freshness

**Weekly:**
- Review dashboard usage
- Update time ranges if needed
- Check Grafana logs

**Monthly:**
- Update Grafana version
- Review and optimize slow queries
- Backup dashboard configurations

### Backup Dashboards

```bash
# Export all dashboards
mkdir -p backups
python3 -c "
import requests
import json
from datetime import datetime

session = requests.Session()
session.auth = ('admin', 'your-password')
base_url = 'http://localhost:3001'

# Get all dashboards
search = session.get(f'{base_url}/api/search?type=dash-db').json()

for dashboard in search:
    uid = dashboard['uid']
    db = session.get(f'{base_url}/api/dashboards/uid/{uid}').json()
    
    filename = f\"backups/{dashboard['title'].replace(' ', '-')}-{datetime.now().strftime('%Y%m%d')}.json\"
    with open(filename, 'w') as f:
        json.dump(db, f, indent=2)
    print(f'Backed up: {filename}')
"
```

### Update Grafana

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get upgrade grafana

# RHEL/CentOS/Fedora
sudo yum update grafana

# Restart service
sudo systemctl restart grafana-server
```

---

## FAQ

### Q: Which port does Grafana use?
**A:** Port **3001** (configured to avoid conflicts with other services)

### Q: What are the default credentials?
**A:** Username: `admin`, Password: `admin` (must change on first login)

### Q: How do I reset the admin password?
**A:** Run: `sudo grafana-cli admin reset-admin-password newpassword`

### Q: Can I access Grafana from another computer?
**A:** Yes, configure remote access (see [Advanced Configuration](#advanced-configuration))

### Q: How often does data refresh?
**A:** Dashboards auto-refresh every 5 minutes by default (configurable)

### Q: What if I see "No data" on panels?
**A:** 
1. Verify DevLake pipeline has collected data
2. Check time range settings
3. Test datasource connection

### Q: Can I customize the dashboards?
**A:** Yes! All dashboards are fully editable. Click edit (pencil icon) on any panel.

### Q: How do I add more dashboards?
**A:** Create new dashboards in Grafana UI or import additional JSON files

### Q: What if the setup script fails?
**A:** Follow the manual setup instructions in [Option B: Manual Setup](#option-b-manual-setup-if-automated-fails)

---

## Support & Resources

### Documentation
- **Grafana Docs:** https://grafana.com/docs/
- **DevLake Docs:** https://devlake.apache.org/
- **OpenProject API:** https://docs.openproject.org/api/

### Useful Commands

```bash
# Check Grafana status
sudo systemctl status grafana-server

# View Grafana logs
sudo journalctl -u grafana-server -f

# Restart Grafana
sudo systemctl restart grafana-server

# Test database connection
python3 test_connection.py

# Preview dashboard data
python3 scripts/dashboard_preview.py --dashboard all

# Check DevLake containers
docker ps

# View MySQL data
mysql -h localhost -P 3307 -u merico -pmerico lake
```

### Log Files
- **Grafana Server:** `sudo journalctl -u grafana-server`
- **Grafana Application:** `/var/log/grafana/grafana.log`
- **Setup Scripts:** Console output

---

## Success Checklist

Before considering setup complete, verify:

- [ ] Grafana is accessible at http://localhost:3001
- [ ] Admin password has been changed from default
- [ ] MySQL datasource shows "Database Connection OK"
- [ ] OpenProject folder exists with 3 dashboards
- [ ] Team Productivity dashboard shows data
- [ ] Sprint Progress dashboard shows data
- [ ] Issues Metrics & DORA dashboard shows data
- [ ] All panels render without errors
- [ ] Time ranges are appropriate for your data
- [ ] Auto-refresh is working (check panel updates)

---

## 🎉 Congratulations!

Your Grafana visualization environment is now set up and ready to provide insights into your OpenProject data!

**What's Next?**
1. Explore the dashboards
2. Customize visualizations for your team
3. Set up alerts for important metrics
4. Share dashboards with stakeholders
5. Schedule regular data pipeline runs to keep data fresh

**Need Help?**
- Check the [Troubleshooting](#troubleshooting) section
- Review [FAQ](#faq)
- Consult [Support & Resources](#support--resources)

---

**Last Updated:** October 2025  
**Version:** 1.0  
**Maintainer:** OpenProject DevLake Integration Team
