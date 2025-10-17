# 📊 Grafana Setup - Quick Reference Card

**One-page guide for setting up OpenProject Grafana dashboards**

---

## ⚡ 5-Minute Setup

### Prerequisites Check
```bash
# Verify DevLake MySQL is running
docker ps | grep mysql
# Should show port 3307
```

### Installation Steps

#### 1️⃣ Install Dependencies
```bash
pip3 install -r requirements.txt
```

#### 2️⃣ Install Grafana
```bash
chmod +x scripts/install_grafana.sh
./scripts/install_grafana.sh
```

#### 3️⃣ Access Grafana
- **URL:** http://localhost:3001
- **Login:** admin / admin
- **Action:** Change password when prompted

#### 4️⃣ Setup Dashboards
```bash
python3 scripts/setup_grafana.py --url http://localhost:3001 --password YOUR_NEW_PASSWORD
```

#### 5️⃣ View Dashboards
- Open Grafana → **Dashboards** → **OpenProject** folder
- You'll see 3 dashboards ready to use!

---

## 🔧 Quick Commands

```bash
# Check Grafana status
sudo systemctl status grafana-server

# View Grafana logs
sudo journalctl -u grafana-server -f

# Restart Grafana
sudo systemctl restart grafana-server

# Test dashboard data
python3 scripts/dashboard_preview.py --dashboard all

# Reset admin password
sudo grafana-cli admin reset-admin-password newpassword
```

---

## 🎯 What You Get

### 3 Pre-built Dashboards:

1. **Team Productivity** (11 panels)
   - Active team members
   - Issues completed
   - Completion trends
   - Time logging analysis

2. **Sprint Progress** (8 panels)
   - Sprint overview
   - Project health
   - Velocity tracking
   - Resource utilization

3. **Issues Metrics & DORA** (10 panels)
   - Lead time for changes
   - Deployment frequency
   - Resolution time distribution
   - Monthly trends

---

## 🚨 Common Issues

| Problem | Solution |
|---------|----------|
| Can't access Grafana | Check if service is running: `sudo systemctl status grafana-server` |
| "No data" in panels | Verify data exists: `mysql -h localhost -P 3307 -u merico -pmerico lake -e "SELECT COUNT(*) FROM issues;"` |
| Setup script fails | Use manual import (see GRAFANA_QUICKSTART.md, Option B) |
| Port 3001 in use | Change port in `/etc/grafana/grafana.ini` |

---

## 📁 Key Files

- **Setup Scripts:** `scripts/install_grafana.sh`, `scripts/setup_grafana.py`
- **Dashboard JSON:** `grafana/dashboards/*.json`
- **Datasource Config:** `grafana/datasource.yaml`
- **Full Guide:** `GRAFANA_QUICKSTART.md`

---

## 💡 Quick Tips

✅ **Default Port:** 3001 (not 3000)  
✅ **Database:** DevLake MySQL on localhost:3307  
✅ **Credentials:** merico/merico for database  
✅ **Auto-refresh:** Dashboards update every 5 minutes  
✅ **Time Range:** Adjust in top-right corner of each dashboard

---

## 📚 Need More Help?

- **Complete Guide:** Read `GRAFANA_QUICKSTART.md`
- **Troubleshooting:** See section in `GRAFANA_QUICKSTART.md`
- **Manual Setup:** Follow `MANUAL_SETUP_GUIDE.md`

---

## ✅ Success Checklist

- [ ] Grafana accessible at http://localhost:3001
- [ ] Password changed from default
- [ ] MySQL datasource connected
- [ ] 3 dashboards imported
- [ ] Panels showing data (not "No data")

**All checked?** 🎉 **You're ready to go!**

---

**For detailed instructions, see:** [GRAFANA_QUICKSTART.md](GRAFANA_QUICKSTART.md)
