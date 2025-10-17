# 🚀 Pre-Push Checklist

**Complete this checklist before pushing to Git for your colleague**

---

## 📋 Repository Preparation

### 1. Security & Configuration

- [ ] **Remove sensitive credentials from config.yaml**
  ```bash
  # Edit config.yaml and replace with placeholders:
  # api_key: "YOUR_OPENPROJECT_API_KEY_HERE"
  # password: "YOUR_DATABASE_PASSWORD_HERE"
  ```

- [ ] **Create .gitignore if not exists**
  ```bash
  # Check if .gitignore exists
  ls -la .gitignore
  ```

- [ ] **Add sensitive files to .gitignore:**
  ```
  # Add these lines to .gitignore
  config.yaml
  *.log
  logs/
  __pycache__/
  *.pyc
  .env
  *.db
  backups/
  .DS_Store
  ```

- [ ] **Create config.yaml.example** for reference
  ```bash
  cp config.yaml config.yaml.example
  # Then edit config.yaml.example to remove real credentials
  ```

### 2. Documentation Check

- [ ] **README.md is updated** with link to GRAFANA_QUICKSTART.md
- [ ] **GRAFANA_QUICKSTART.md exists** and is complete
- [ ] **GRAFANA_SETUP_CHEATSHEET.md exists** for quick reference
- [ ] **All guides reference correct ports, paths, and commands**

### 3. File Structure Verification

```bash
# Run this to verify all necessary files exist
ls -la README.md
ls -la GRAFANA_QUICKSTART.md
ls -la GRAFANA_SETUP_CHEATSHEET.md
ls -la requirements.txt
ls -la config.yaml.example
ls -la scripts/install_grafana.sh
ls -la scripts/setup_grafana.py
ls -la scripts/dashboard_preview.py
ls -la grafana/datasource.yaml
ls -la grafana/dashboards/team-productivity.json
ls -la grafana/dashboards/sprint-progress.json
ls -la grafana/dashboards/issues-metrics-dora.json
```

### 4. Scripts are Executable

```bash
chmod +x scripts/*.sh
chmod +x setup.sh
chmod +x *.sh
```

### 5. Test Installation (Optional but Recommended)

```bash
# In a clean environment, test that installation works:
pip3 install -r requirements.txt
python3 test_connection.py
```

---

## 🔒 Security Checklist

### Critical: Before Pushing to Git

- [ ] **No API keys in code**
  ```bash
  # Search for potential secrets
  grep -r "api_key.*:" . --include="*.py" --include="*.yaml" --include="*.yml"
  grep -r "password.*:" . --include="*.py" --include="*.yaml" --include="*.yml"
  ```

- [ ] **No database passwords in plaintext**
  ```bash
  # Verify config.yaml has placeholders
  cat config.yaml | grep -i password
  cat config.yaml | grep -i api_key
  ```

- [ ] **No personal data in logs**
  ```bash
  # Remove or clean log files
  rm -rf logs/*.log
  ```

- [ ] **.gitignore is properly configured**
  ```bash
  cat .gitignore
  ```

---

## 📝 Documentation Tasks

### Update README.md

- [ ] Add prominent link to GRAFANA_QUICKSTART.md at the top
- [ ] Include prerequisite information
- [ ] Verify all commands are correct
- [ ] Add repository URL (once created)

### Create config.yaml.example

```yaml
# config.yaml.example
openproject:
  base_url: "https://your-openproject-instance.com"
  api_key: "YOUR_OPENPROJECT_API_KEY_HERE"
  connection_id: 1
  connection_name: "OpenProject Production"

database:
  host: "localhost"
  port: 3307
  database: "lake"
  user: "merico"
  password: "YOUR_DATABASE_PASSWORD_HERE"
  charset: "utf8mb4"

pipeline:
  batch_size: 100
  rate_limit_rpm: 60
  retry_attempts: 3
  timeout_seconds: 30
  max_pages_per_collection: 1000

collection:
  incremental_sync: true
  sync_interval_hours: 6
  full_sync_interval_days: 7
  projects: []

logging:
  level: "INFO"
  file: "logs/openproject_pipeline.log"
  max_bytes: 10485760
  backup_count: 5
```

### Add Quick Start Section to README

Add this near the top of README.md:

```markdown
## 🎯 For Your Colleague (Quick Start)

**Setting up Grafana dashboards only?**  
👉 **[Go to Grafana Quick Start Guide](GRAFANA_QUICKSTART.md)** 👈

This is a complete, standalone guide that takes ~5 minutes to set up Grafana visualization.
```

---

## 🧪 Pre-Push Testing

### Test These Scenarios

1. **Clone fresh copy and verify:**
   ```bash
   cd /tmp
   git clone <your-repo-url> test-clone
   cd test-clone
   ls -la  # Verify all files are present
   cat config.yaml  # Should not have real credentials
   ```

2. **Verify .gitignore works:**
   ```bash
   git status
   # Should not show logs/, __pycache__, etc.
   ```

3. **Test documentation links:**
   ```bash
   # Open README.md in browser/viewer
   # Click all internal links
   # Verify they work
   ```

---

## 🌐 Git Commands

### Initial Commit (if new repo)

```bash
# Initialize git (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: OpenProject DevLake Grafana Integration"

# Add remote
git remote add origin <your-repo-url>

# Push
git push -u origin main
```

### Update Existing Repo

```bash
# Check status
git status

# Add all changes
git add .

# Commit with descriptive message
git commit -m "Add comprehensive Grafana setup documentation

- Added GRAFANA_QUICKSTART.md with complete setup guide
- Added GRAFANA_SETUP_CHEATSHEET.md for quick reference
- Updated README.md with documentation links
- Created config.yaml.example for reference
- Removed sensitive credentials from tracked files"

# Push to remote
git push origin main
```

---

## 📧 Colleague Communication

### Email/Message Template

```
Hi [Colleague Name],

I've pushed the OpenProject DevLake Grafana integration to the repository.

**To set up Grafana dashboards (takes ~5 minutes):**

1. Clone the repository:
   git clone <repo-url>
   cd openproject-devlake-integration

2. Follow the Grafana Quick Start Guide:
   📚 Open GRAFANA_QUICKSTART.md
   
   Or use the one-page cheatsheet:
   📄 GRAFANA_SETUP_CHEATSHEET.md

**Prerequisites:**
- DevLake MySQL must be running on port 3307
- Pipeline data should be collected first (if not done)
- Sudo privileges for installing Grafana

**Quick Commands:**
```bash
# Install Grafana
./scripts/install_grafana.sh

# Setup dashboards
python3 scripts/setup_grafana.py --url http://localhost:3001 --password YOUR_PASSWORD
```

**Configuration:**
- Copy config.yaml.example to config.yaml
- Update with your credentials

Let me know if you have any questions!

Best regards,
[Your Name]
```

---

## ✅ Final Checklist Before Push

- [ ] All sensitive credentials removed
- [ ] .gitignore configured correctly
- [ ] config.yaml.example created
- [ ] All documentation files present
- [ ] Scripts are executable
- [ ] README.md updated with clear links
- [ ] Tested clone in fresh directory
- [ ] Git status shows only intended files
- [ ] Commit message is descriptive
- [ ] Colleague instructions prepared

---

## 🎯 Post-Push Tasks

After pushing to Git:

1. **Send colleague the repository URL**
2. **Share the email template above**
3. **Be available for questions during setup**
4. **Ask for feedback on documentation clarity**

---

## 📞 Support Preparation

Prepare to help your colleague with:

- **DevLake MySQL connection issues**
- **Grafana installation problems**
- **Dashboard import errors**
- **Data verification questions**

**Have ready:**
- Access to test environment
- Sample config.yaml with placeholders
- Screenshots of successful setup
- Links to external documentation

---

**Good luck with the push! 🚀**

Your colleague will have everything needed to get Grafana running quickly.
