 🚀 When to Use Each Script:
setup.sh - Run FIRST (Initial Setup)

./setup.sh
Purpose: Verify prerequisites and prepare the environment
Use when: First time setting up the project

install_grafana.sh - For Grafana Only

./scripts/install_grafana.sh
Purpose: Install and configure Grafana for visualization
Use when: You want to set up dashboards

streamlit_app.py - For Streamlit Dashboard

streamlit run streamlit_app.py
Purpose: Run interactive web dashboard
Use when: You want real-time monitoring interface

 Complete Setup Flow:
# 1. Initial setup (run FIRST)
./setup.sh

# 2. Create database schema
python3 database_setup.py

# 3. Run the pipeline to collect data
python3 run_pipeline.py --verbose

# 4. Set up Grafana dashboards (optional)
./scripts/install_grafana.sh

# 5. Run Streamlit dashboard (optional)
streamlit run streamlit_app.py
