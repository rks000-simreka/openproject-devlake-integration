# 🎯 Getting Started - Your Colleague's Guide

**Welcome! This guide will help you set up Grafana dashboards for OpenProject DevLake data visualization.**

---

## 📖 Which Guide Should You Use?

### 🚀 Option 1: Quick Start (Recommended)
**→ Read: [GRAFANA_QUICKSTART.md](GRAFANA_QUICKSTART.md)**

**Best for:** First-time setup, complete instructions
- Full step-by-step guide
- Troubleshooting section
- FAQ and support resources
- ~15 minute read, 5-10 minute setup

### ⚡ Option 2: Cheat Sheet
**→ Read: [GRAFANA_SETUP_CHEATSHEET.md](GRAFANA_SETUP_CHEATSHEET.md)**

**Best for:** Quick reference, experienced users
- One-page summary
- Essential commands only
- Quick troubleshooting
- ~2 minute read

### 📚 Option 3: Detailed Documentation
**→ Read: [GRAFANA_README.md](GRAFANA_README.md)**

**Best for:** Understanding dashboards, advanced configuration
- Dashboard panel details
- Query explanations
- Advanced settings
- Reference documentation

---

## ✅ Before You Start

### 1. Check Prerequisites

```bash
# Is DevLake MySQL running?
docker ps | grep mysql
# Expected: Should show devlake-docker-mysql on port 3307

# Does data exist in the database?
mysql -h localhost -P 3307 -u merico -pmerico lake -e "SELECT COUNT(*) FROM issues WHERE id LIKE 'openproject:%';"
# Expected: Count should be > 0
```

### 2. Prepare Configuration

```bash
# Copy the example config
cp config.yaml.example config.yaml

# Edit with your credentials
nano config.yaml
# or
vim config.yaml
```

**What to update in config.yaml:**
- `base_url`: Your OpenProject instance URL
- `api_key`: Your OpenProject API token
- `password`: Your database password (usually "merico")

---

## 🚀 Quick Setup (3 Commands)

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Install and start Grafana
./scripts/install_grafana.sh

# 3. Setup dashboards (after changing Grafana password)
python3 scripts/setup_grafana.py --url http://localhost:3001 --password YOUR_NEW_PASSWORD
```

**Done!** Open http://localhost:3001 and view your dashboards.

---

## 📊 What You'll Get

After setup, you'll have **3 powerful dashboards**:

### 1. Team Productivity Dashboard
**Use for:** Daily standups, sprint retrospectives
- 📈 Team member activity tracking
- ⏱️ Time logging analysis  
- 📊 Completion rate trends
- 🎯 Individual performance metrics

### 2. Sprint Progress & Projects
**Use for:** Sprint planning, project status reports
- 📋 Sprint overview and health
- 🏗️ Project completion rates
- 📊 Velocity tracking
- 👥 Team capacity planning

### 3. Issues Metrics & DORA
**Use for:** Engineering excellence, executive reporting
- ⚡ Lead time for changes
- 🚀 Deployment frequency
- 🐛 Change failure rate
- 🔧 Mean time to recovery

---

## 🆘 Need Help?

### Common Issues & Quick Fixes

| Problem | Quick Fix |
|---------|-----------|
| **Can't access Grafana** | `sudo systemctl restart grafana-server` |
| **Panels show "No data"** | Check time range (try "Last 90 days") |
| **Setup script fails** | See manual setup in GRAFANA_QUICKSTART.md |
| **Database connection error** | Verify: `mysql -h localhost -P 3307 -u merico -pmerico` |

### Get Detailed Help

1. **Troubleshooting:** See GRAFANA_QUICKSTART.md → Troubleshooting section
2. **FAQ:** See GRAFANA_QUICKSTART.md → FAQ section
3. **Manual Setup:** See MANUAL_SETUP_GUIDE.md

---

## 📁 Repository Structure

```
openproject-devlake-integration/
│
├── 📚 Documentation (START HERE)
│   ├── GETTING_STARTED.md          ← You are here!
│   ├── GRAFANA_QUICKSTART.md       ← Complete setup guide
│   ├── GRAFANA_SETUP_CHEATSHEET.md ← One-page reference
│   ├── GRAFANA_README.md           ← Detailed dashboard docs
│   └── MANUAL_SETUP_GUIDE.md       ← Manual import instructions
│
├── 🔧 Configuration
│   ├── config.yaml.example         ← Copy to config.yaml
│   └── requirements.txt            ← Python dependencies
│
├── 📊 Grafana Files
│   ├── grafana/
│   │   ├── datasource.yaml         ← MySQL connection config
│   │   └── dashboards/             ← Dashboard JSON files
│   │       ├── team-productivity.json
│   │       ├── sprint-progress.json
│   │       └── issues-metrics-dora.json
│
└── 🛠️ Scripts
    ├── scripts/
    │   ├── install_grafana.sh      ← Grafana installation
    │   ├── setup_grafana.py        ← Dashboard setup
    │   └── dashboard_preview.py    ← Test queries
    │
    └── Other pipeline files...
```

---

## 🎓 Learning Path

### For Quick Setup
1. Read this file (2 min)
2. Read GRAFANA_SETUP_CHEATSHEET.md (2 min)
3. Run the 3 commands above (5-10 min)
4. ✅ Done!

### For Understanding
1. Read GRAFANA_QUICKSTART.md (15 min)
2. Complete setup (5-10 min)
3. Read GRAFANA_README.md for dashboard details
4. Explore and customize dashboards

### For Advanced Usage
1. Complete basic setup first
2. Read "Advanced Configuration" in GRAFANA_QUICKSTART.md
3. Customize dashboards in Grafana UI
4. Create additional dashboards as needed

---

## 🔐 Security Notes

### Important: Configuration File

The `config.yaml` file contains sensitive credentials and is **not** tracked in Git.

**To set up:**
```bash
# Copy the example
cp config.yaml.example config.yaml

# Edit with your credentials
nano config.yaml
```

**Never commit** the actual `config.yaml` to Git!

### Grafana Default Password

**IMPORTANT:** Change the default Grafana password (`admin/admin`) immediately after first login!

---

## 📞 Support Resources

### Documentation Files
- **[GRAFANA_QUICKSTART.md](GRAFANA_QUICKSTART.md)** - Complete setup guide
- **[GRAFANA_SETUP_CHEATSHEET.md](GRAFANA_SETUP_CHEATSHEET.md)** - Quick reference
- **[GRAFANA_README.md](GRAFANA_README.md)** - Dashboard documentation
- **[README.md](README.md)** - Full project overview

### Useful Commands
```bash
# Test database connection
python3 test_connection.py

# Preview dashboard data
python3 scripts/dashboard_preview.py --dashboard all

# Check Grafana status
sudo systemctl status grafana-server

# View Grafana logs
sudo journalctl -u grafana-server -f

# Reset Grafana admin password
sudo grafana-cli admin reset-admin-password newpassword
```

### External Resources
- **Grafana Docs:** https://grafana.com/docs/
- **DevLake Docs:** https://devlake.apache.org/
- **OpenProject API:** https://docs.openproject.org/api/

---

## ✅ Success Checklist

After setup, verify:

- [ ] Grafana accessible at http://localhost:3001
- [ ] Logged in with changed password
- [ ] MySQL datasource shows "Connection OK"
- [ ] OpenProject folder exists with 3 dashboards
- [ ] Team Productivity dashboard shows data
- [ ] Sprint Progress dashboard shows data  
- [ ] Issues Metrics & DORA dashboard shows data
- [ ] All panels render without errors
- [ ] Time ranges show your data period

**All checked?** 🎉 **Congratulations! You're all set!**

---

## 🎯 Next Steps

After successful setup:

1. **Explore Dashboards**
   - Navigate through each dashboard
   - Understand the metrics
   - Adjust time ranges as needed

2. **Customize for Your Team**
   - Edit panels to match your needs
   - Add team-specific metrics
   - Set up alerts (optional)

3. **Share with Team**
   - Create dashboard links
   - Set up recurring reports
   - Schedule demo sessions

4. **Maintain Data Freshness**
   - Schedule regular pipeline runs
   - Monitor data collection
   - Keep Grafana updated

---

## 💬 Feedback Welcome!

If you find any issues with the setup or documentation:
- Note down what was unclear
- Suggest improvements
- Report any bugs or errors
- Share what worked well

Your feedback helps improve this project for others!

---

## 🌟 Quick Start Summary

**The absolute fastest way to get started:**

```bash
# 1. Clone and navigate
git clone <repo-url>
cd openproject-devlake-integration

# 2. Setup config
cp config.yaml.example config.yaml
nano config.yaml  # Add your credentials

# 3. Install everything
pip3 install -r requirements.txt
./scripts/install_grafana.sh

# 4. Open Grafana and change password
# Visit: http://localhost:3001
# Login: admin/admin → Change password

# 5. Setup dashboards
python3 scripts/setup_grafana.py --url http://localhost:3001 --password YOUR_NEW_PASSWORD

# 6. View dashboards!
# Grafana → Dashboards → OpenProject folder
```

**Total time:** ~10 minutes

---

**Ready to start?** 

→ **Go to [GRAFANA_QUICKSTART.md](GRAFANA_QUICKSTART.md)** for detailed instructions!

Good luck! 🚀
