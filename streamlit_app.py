#!/usr/bin/env python3
"""
OpenProject DevLake Integration - Streamlit UI
Web interface for configuring sync policies and scheduling data collection
"""

import streamlit as st
import mysql.connector
import yaml
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import subprocess
import sys
import re
from typing import Dict, Optional, List

# Page configuration
st.set_page_config(
    page_title="OpenProject DevLake Sync",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)


class SyncPolicyManager:
    """Manages sync policies in MySQL database"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.db_config = config['database']
    
    def get_connection(self):
        """Create database connection"""
        return mysql.connector.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            charset=self.db_config['charset']
        )
    
    def get_current_policy(self) -> Optional[Dict]:
        """Get current sync policy from database"""
        with self.get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT * FROM sync_policies 
                    WHERE is_active = TRUE 
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """)
                return cursor.fetchone()
    
    def save_policy(self, policy: Dict) -> bool:
        """Save sync policy to database"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE sync_policies SET is_active = FALSE")
                    cursor.execute("""
                        INSERT INTO sync_policies (
                            time_range_start, time_range_end, sync_frequency, 
                            custom_cron, skip_failed_tasks, is_active,
                            created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, TRUE, NOW(), NOW())
                    """, (
                        policy['time_range_start'],
                        policy['time_range_end'],
                        policy['sync_frequency'],
                        policy.get('custom_cron'),
                        policy['skip_failed_tasks'],
                    ))
                conn.commit()
            return True
        except Exception as e:
            st.error(f"Error saving policy: {e}")
            return False

    def get_execution_history(self, limit: int = 10) -> pd.DataFrame:
        """Get recent execution history"""
        with self.get_connection() as conn:
            return pd.read_sql("""
                SELECT id, started_at, completed_at, status, records_collected,
                       error_message, TIMESTAMPDIFF(SECOND, started_at, completed_at) as duration_seconds
                FROM sync_execution_history 
                ORDER BY started_at DESC 
                LIMIT %s
            """, conn, params=(limit,))

    def get_table_counts(self, tables: List[str]) -> Dict[str, int]:
        """Get record counts for multiple tables efficiently"""
        counts = {}
        with self.get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) AS c FROM {table}")
                        row = cursor.fetchone()
                        counts[table] = int(row.get('c', 0)) if row else 0
                    except Exception:
                        counts[table] = 0
        counts['total'] = sum(counts.values())
        return counts
    
    def get_next_scheduled_runs(self) -> List[Dict]:
        """Calculate next 3 scheduled runs based on current policy"""
        policy = self.get_current_policy()
        if not policy:
            return []
        
        frequency = policy['sync_frequency']
        now = datetime.now()
        
        if frequency == 'manual':
            return [{'date': 'Manual', 'note': 'Run manually when needed'}]
        
        runs = []
        
        # Calculate initial next_run based on frequency
        if frequency == 'daily':
            next_run = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            delta = timedelta(days=1)
        elif frequency == 'weekly':
            days_until_monday = (7 - now.weekday()) % 7 or 7
            next_run = (now + timedelta(days=days_until_monday)).replace(hour=9, minute=0, second=0, microsecond=0)
            delta = timedelta(weeks=1)
        elif frequency == 'monthly':
            next_run = (now.replace(day=1) + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            delta = None  # Special handling for monthly
        else:
            return []
        
        # Generate 3 runs
        for i in range(3):
            days_diff = (next_run - now).days
            runs.append({
                'date': next_run.strftime('%Y-%m-%d %H:%M'),
                'note': f'in {days_diff} days' if days_diff > 0 else 'today'
            })
            next_run = (next_run + timedelta(days=32)).replace(day=1) if frequency == 'monthly' else next_run + delta
        
        return runs

    def update_execution_status(self, execution_id: int, status: str, 
                               records: int = 0, error: str = None):
        """Update execution history status"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE sync_execution_history 
                    SET completed_at = NOW(), status = %s, 
                        records_collected = %s, error_message = %s
                    WHERE id = %s
                """, (status, records, error, execution_id))
            conn.commit()


def load_config() -> Dict:
    """Load configuration from YAML file"""
    with open("config.yaml", 'r') as f:
        return yaml.safe_load(f)


def extract_metrics_from_output(output: str) -> tuple:
    """Extract metrics from pipeline output"""
    records_collected = 0
    duration = None
    
    # Try multiple patterns to find total records
    patterns = [
        r'Total domain records:\s*(\d+)',
        r'Total records:\s*(\d+)',
        r'Total records (extracted|collected):\s*(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            records_collected = int(match.groups()[-1])
            break
    
    # If still 0, sum individual components
    if records_collected == 0:
        for component in ['Issues', 'Boards', 'Worklogs', 'Accounts', 'Board Issues', 'Sprint Issues']:
            comp_match = re.search(f'{component}:\\s*(\\d+)', output, re.IGNORECASE)
            if comp_match:
                records_collected += int(comp_match.group(1))
    
    # Extract duration
    duration_match = re.search(r'Total Duration:\s*([0-9:\.]+)', output)
    if duration_match:
        duration = duration_match.group(1)
    
    return records_collected, duration


def run_pipeline_manually(policy_manager: SyncPolicyManager):
    """Trigger manual pipeline execution"""
    conn = policy_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sync_execution_history (started_at, status) VALUES (NOW(), 'running')")
    conn.commit()
    execution_id = cursor.lastrowid
    cursor.close()
    conn.close()
    
    with st.spinner("🔄 Running data collection pipeline..."):
        try:
            result = subprocess.run(
                [sys.executable, "run_pipeline.py", "--verbose"],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            output = (result.stdout or "") + "\n" + (result.stderr or "")
            records_collected, duration = extract_metrics_from_output(output)
            
            if result.returncode == 0:
                # Fallback to DB counts if parsing failed
                if records_collected == 0:
                    try:
                        counts = policy_manager.get_table_counts(['issues', 'boards', 'board_issues', 
                                                                 'issue_worklogs', 'accounts'])
                        records_collected = counts.get('total', 0)
                    except Exception:
                        pass
                
                policy_manager.update_execution_status(execution_id, 'success', records_collected)
                
                st.success("✅ Pipeline completed successfully!")
                if records_collected > 0:
                    st.info(f"📦 **Total records collected:** {records_collected:,}")
                if duration:
                    st.info(f"⏱️ **Execution time:** {duration}")
                st.info("💡 Check the 'Execution History' tab to see this run logged!")
            else:
                error_msg = result.stderr[:1000] if result.stderr else "Unknown error"
                policy_manager.update_execution_status(execution_id, 'failed', records_collected, error_msg)
                st.error("❌ Pipeline failed")
                st.text_area("Error Output", result.stderr, height=200)
                
        except subprocess.TimeoutExpired:
            policy_manager.update_execution_status(execution_id, 'failed', 0, 'Execution timeout (>10 minutes)')
            st.error("⏱️ Pipeline execution timed out (> 10 minutes)")
        except Exception as e:
            policy_manager.update_execution_status(execution_id, 'failed', 0, str(e)[:1000])
            st.error(f"❌ Error running pipeline: {e}")


def render_sidebar(policy_manager: SyncPolicyManager, config: Dict):
    """Render sidebar with quick stats and actions"""
    with st.sidebar:
        st.header("📊 Quick Stats")
        
        try:
            history = policy_manager.get_execution_history(limit=1)
            if not history.empty:
                last_run = history.iloc[0]
                status = str(last_run.get('status', 'unknown')).upper()
                records = int(last_run.get('records_collected', 0) or 0)
                
                if records == 0:
                    try:
                        counts = policy_manager.get_table_counts(['issues', 'boards', 'board_issues', 
                                                                 'issue_worklogs', 'accounts'])
                        records = counts.get('total', 0)
                    except Exception:
                        pass
                
                duration = int(last_run.get('duration_seconds', 0) or 0)
                st.metric("Last Run Status", status)
                st.metric("Records Collected", f"{records:,}")
                st.metric("Duration", f"{duration}s")
            else:
                st.info("No execution history yet")
        except Exception as e:
            st.warning(f"Could not load stats: {e}")
        
        st.markdown("---")
        st.header("🔌 Connection Status")
        
        # MySQL Connection
        try:
            test_conn = policy_manager.get_connection()
            test_conn.close()
            st.success("✅ MySQL Connected")
            st.caption(f"DB: {config['database']['database']}")
        except Exception as e:
            st.error("❌ MySQL Disconnected")
            st.caption(str(e)[:50])
        
        # OpenProject Connection
        op_config = config.get('openproject', {})
        base_url = op_config.get('base_url', '')
        api_key = op_config.get('api_key', '')
        
        if 'your-openproject-instance' in base_url or 'your-api-key' in api_key:
            st.warning("⚠️ OpenProject Not Configured")
        else:
            try:
                import requests
                import base64
                auth_b64 = base64.b64encode(f"apikey:{api_key}".encode()).decode()
                response = requests.get(f"{base_url}/api/v3/users/me", 
                                      headers={'Authorization': f'Basic {auth_b64}'}, 
                                      timeout=5)
                if response.status_code == 200:
                    st.success("✅ OpenProject Connected")
                else:
                    st.error(f"❌ Auth Failed ({response.status_code})")
            except Exception:
                st.error("❌ OpenProject Unreachable")
        
        st.markdown("---")
        st.header("🚀 Quick Actions")
        
        if st.button("▶️ Run Pipeline Now", type="primary", use_container_width=True):
            run_pipeline_manually(policy_manager)
        
        if st.button("🔄 Refresh Page", use_container_width=True):
            st.rerun()


def render_sync_policy_tab(policy_manager: SyncPolicyManager):
    """Render sync policy configuration tab"""
    st.header("Set Sync Policy")
    
    current_policy = policy_manager.get_current_policy()
    
    # Time Range Section
    st.subheader("📅 Time Range")
    col1, col2, col3, col4 = st.columns(4)
    
    time_presets = {
        'Last 30 days': 30,
        'Last 90 days': 90,
        'Last 6 months': 180,
        'Last Year': 365
    }
    
    for col, (label, days) in zip([col1, col2, col3, col4], time_presets.items()):
        with col:
            if st.button(label, use_container_width=True):
                st.session_state.time_preset = days
    
    if 'time_preset' not in st.session_state:
        st.session_state.time_preset = 180
    
    start_date = datetime.now() - timedelta(days=st.session_state.time_preset)
    
    col_start, col_end = st.columns(2)
    with col_start:
        start_date_input = st.date_input("Start Date", value=start_date.date())
    with col_end:
        st.text_input("End Date", value="Now", disabled=True)
    
    # Sync Frequency Section
    st.subheader("⏰ Sync Frequency")
    
    frequency_options = {
        "Manual": "manual",
        "Daily (at 00:00AM UTC)": "daily",
        "Weekly (on Monday at 09:00AM UTC)": "weekly",
        "Monthly (on first day at 00:00AM UTC)": "monthly",
        "Custom": "custom"
    }
    
    frequency = st.radio("Select frequency", list(frequency_options.keys()), index=2)
    frequency_value = frequency_options[frequency]
    
    custom_cron = None
    if frequency == "Custom":
        st.markdown("📖 [Learn cron syntax](https://crontab.guru/)")
        custom_cron = st.text_input("Cron Expression", placeholder="0 9 * * 1")
    
    # Show next scheduled runs
    if frequency_value != "manual":
        st.markdown("### 📅 Next Three Runs:")
        st.session_state.temp_policy = {
            'time_range_start': start_date_input,
            'time_range_end': datetime.now().date(),
            'sync_frequency': frequency_value,
            'custom_cron': custom_cron,
            'skip_failed_tasks': False
        }
        
        next_runs = policy_manager.get_next_scheduled_runs()
        for run in next_runs[:3]:
            st.text(f"{run['date']} ({run['note']})")
    
    # Running Policy
    st.subheader("🛡️ Running Policy")
    skip_failed = st.checkbox(
        "Skip failed tasks (Recommended for large data volumes)",
        value=current_policy['skip_failed_tasks'] if current_policy else True
    )
    
    # Save button
    st.markdown("---")
    col_cancel, col_save = st.columns([1, 1])
    
    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            st.rerun()
    
    with col_save:
        if st.button("💾 Save", type="primary", use_container_width=True):
            policy = {
                'time_range_start': start_date_input,
                'time_range_end': datetime.now().date(),
                'sync_frequency': frequency_value,
                'custom_cron': custom_cron,
                'skip_failed_tasks': skip_failed
            }
            
            if policy_manager.save_policy(policy):
                st.success("✅ Sync policy saved successfully!")
                st.balloons()
                st.info("ℹ️ Restart scheduler: `sudo systemctl restart devlake-scheduler`")


def render_execution_history_tab(policy_manager: SyncPolicyManager):
    """Render execution history tab"""
    st.header("📋 Execution History")
    
    try:
        history = policy_manager.get_execution_history(limit=50)
        
        if history.empty:
            st.info("No execution history yet. Run the pipeline to see results here.")
        else:
            history['started_at'] = pd.to_datetime(history['started_at'])
            history['completed_at'] = pd.to_datetime(history['completed_at'])
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Runs", len(history))
            with col2:
                st.metric("Successful", len(history[history['status'] == 'success']))
            with col3:
                st.metric("Failed", len(history[history['status'] == 'failed']))
            with col4:
                st.metric("Avg Duration", f"{history['duration_seconds'].mean():.0f}s")
            
            # Display table
            st.dataframe(
                history[['started_at', 'status', 'records_collected', 'duration_seconds', 'error_message']],
                use_container_width=True,
                hide_index=True
            )
    except Exception as e:
        st.error(f"❌ Error loading execution history: {e}")


def render_configuration_tab(policy_manager: SyncPolicyManager):
    """Render configuration/statistics tab"""
    st.markdown("### 📈 Database Statistics")
    
    try:
        tables = {
            'issues': 'Issues',
            'boards': 'Boards/Projects',
            'board_issues': 'Board Issues',
            'issue_worklogs': 'Worklogs',
            'accounts': 'Users/Accounts'
        }
        
        counts = policy_manager.get_table_counts(list(tables.keys()))
        
        # Display in columns
        cols = st.columns(5)
        for i, (table, label) in enumerate(tables.items()):
            with cols[i]:
                st.metric(label, f"{counts[table]:,}")
        
        if counts['total'] > 0:
            st.success(f"✅ Total records in database: **{counts['total']:,}**")
        else:
            st.info("No data in database yet. Configure OpenProject and run the pipeline.")
            
    except Exception as e:
        st.error(f"Could not load statistics: {e}")


def main():
    """Main Streamlit application"""
    
    try:
        config = load_config()
        policy_manager = SyncPolicyManager(config)
    except Exception as e:
        st.error(f"❌ Failed to load configuration: {e}")
        st.stop()
    
    st.title("🔄 OpenProject DevLake Sync Management")
    st.markdown("Configure data synchronization policies and schedule automated runs")
    
    render_sidebar(policy_manager, config)
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["⚙️ Sync Policy", "📋 Execution History", "🔧 Configuration"])
    
    with tab1:
        render_sync_policy_tab(policy_manager)
    
    with tab2:
        render_execution_history_tab(policy_manager)
    
    with tab3:
        render_configuration_tab(policy_manager)


if __name__ == "__main__":
    main()