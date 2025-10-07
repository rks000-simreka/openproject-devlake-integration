#!/usr/bin/env python3
"""
Dashboard Preview - Test queries and show sample data for Grafana dashboards
"""

import mysql.connector
import yaml
import json
from pathlib import Path
from tabulate import tabulate
import argparse

def load_config():
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def get_db_connection(config):
    """Get database connection"""
    db_config = config['database']
    return mysql.connector.connect(
        host=db_config['host'],
        port=db_config['port'],
        database=db_config['database'],
        user=db_config['user'],
        password=db_config['password'],
        charset=db_config['charset']
    )

def run_query_preview(cursor, query_name, query, limit=5):
    """Run a query and show preview results"""
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        
        if results:
            # Get column names
            column_names = [desc[0] for desc in cursor.description]
            
            # Show limited results
            preview_results = results[:limit]
            table = tabulate(preview_results, headers=column_names, tablefmt="grid")
            
            print(f"\n📊 {query_name}")
            print("=" * 60)
            print(f"Total rows: {len(results)}")
            print(f"Showing first {min(limit, len(results))} rows:")
            print(table)
            
            # If there are aggregation results, show the single result
            if len(results) == 1 and len(column_names) == 1:
                print(f"\n💡 Result: {results[0][0]}")
                
        else:
            print(f"\n📊 {query_name}")
            print("=" * 60)
            print("⚠️  No data returned")
            
    except Exception as e:
        print(f"\n❌ Error in {query_name}: {e}")
        print(f"Query: {query}")

def preview_team_productivity():
    """Preview Team Productivity dashboard queries"""
    config = load_config()
    connection = get_db_connection(config)
    cursor = connection.cursor()
    
    print("🏃‍♂️ TEAM PRODUCTIVITY DASHBOARD PREVIEW")
    print("=" * 70)
    
    queries = {
        "Active Team Members": """
            SELECT COUNT(DISTINCT assignee_name) as active_members 
            FROM issues 
            WHERE assignee_name IS NOT NULL AND assignee_name != '' 
            AND id LIKE 'openproject:%' 
            AND updated_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """,
        
        "Issues Completed (30 Days)": """
            SELECT COUNT(*) as completed 
            FROM issues 
            WHERE status = 'DONE' AND id LIKE 'openproject:%' 
            AND resolution_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """,
        
        "Team Productivity by Assignee": """
            SELECT assignee_name, 
                   COUNT(CASE WHEN status = 'DONE' AND resolution_date >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 END) as completed,
                   COUNT(CASE WHEN status IN ('TODO', 'IN_PROGRESS') THEN 1 END) as active
            FROM issues 
            WHERE assignee_name IS NOT NULL AND assignee_name != '' AND id LIKE 'openproject:%' 
            GROUP BY assignee_name 
            HAVING (completed > 0 OR active > 0) 
            ORDER BY completed DESC, active DESC 
            LIMIT 10
        """,
        
        "Time Logging by Team Member (30 Days)": """
            SELECT a.full_name as author_name, ROUND(SUM(w.time_spent_minutes)/60, 1) as hours_logged 
            FROM issue_worklogs w 
            LEFT JOIN accounts a ON w.author_id = a.id
            WHERE w.id LIKE 'openproject:%' 
            AND w.logged_date >= DATE_SUB(NOW(), INTERVAL 30 DAY) 
            AND a.full_name IS NOT NULL AND a.full_name != '' 
            GROUP BY a.full_name 
            ORDER BY hours_logged DESC 
            LIMIT 10
        """
    }
    
    for query_name, query in queries.items():
        run_query_preview(cursor, query_name, query)
    
    cursor.close()
    connection.close()

def preview_sprint_progress():
    """Preview Sprint Progress dashboard queries"""
    config = load_config()
    connection = get_db_connection(config)
    cursor = connection.cursor()
    
    print("\n\n🏃‍♀️ SPRINT PROGRESS & PROJECTS DASHBOARD PREVIEW")
    print("=" * 70)
    
    queries = {
        "Project Health Overview": """
            SELECT b.name as 'Project', 
                   COUNT(i.id) as 'Total Issues', 
                   COUNT(CASE WHEN i.status = 'DONE' THEN 1 END) as 'Completed',
                   COUNT(CASE WHEN i.status IN ('TODO', 'IN_PROGRESS') THEN 1 END) as 'Active',
                   ROUND((COUNT(CASE WHEN i.status = 'DONE' THEN 1 END) * 100.0) / NULLIF(COUNT(i.id), 0), 1) as 'Completion %'
            FROM boards b 
            LEFT JOIN board_issues bi ON b.id = bi.board_id 
            LEFT JOIN issues i ON bi.issue_id = i.id 
            WHERE b.type = 'openproject' 
            GROUP BY b.id, b.name 
            ORDER BY 'Total Issues' DESC
        """,
        
        "Sprint Progress (Version-based)": """
            SELECT COALESCE(s.name, 'No Sprint') as 'Sprint/Version', 
                   COUNT(i.id) as 'Total Issues', 
                   COUNT(CASE WHEN i.status = 'DONE' THEN 1 END) as 'Completed',
                   ROUND((COUNT(CASE WHEN i.status = 'DONE' THEN 1 END) * 100.0) / NULLIF(COUNT(i.id), 0), 1) as 'Progress %'
            FROM issues i 
            LEFT JOIN sprint_issues si ON i.id = si.issue_id 
            LEFT JOIN sprints s ON si.sprint_id = s.id
            WHERE i.id LIKE 'openproject:%' 
            GROUP BY s.name 
            ORDER BY 'Progress %' DESC, 'Total Issues' DESC 
            LIMIT 10
        """,
        
        "Issue Priority Distribution": """
            SELECT priority, 
                   COUNT(CASE WHEN status IN ('TODO', 'IN_PROGRESS') THEN 1 END) as active_count,
                   COUNT(CASE WHEN status = 'DONE' THEN 1 END) as completed_count
            FROM issues 
            WHERE id LIKE 'openproject:%' AND priority IS NOT NULL AND priority != '' 
            GROUP BY priority 
            ORDER BY active_count DESC
        """
    }
    
    for query_name, query in queries.items():
        run_query_preview(cursor, query_name, query)
    
    cursor.close()
    connection.close()

def preview_dora_metrics():
    """Preview DORA Metrics dashboard queries"""
    config = load_config()
    connection = get_db_connection(config)
    cursor = connection.cursor()
    
    print("\n\n📈 ISSUES METRICS & DORA DASHBOARD PREVIEW")
    print("=" * 70)
    
    queries = {
        "Lead Time for Changes (Days)": """
            SELECT ROUND(AVG(lead_time_minutes)/1440, 1) as avg_lead_time_days 
            FROM issues 
            WHERE status = 'DONE' AND id LIKE 'openproject:%' 
            AND resolution_date >= DATE_SUB(NOW(), INTERVAL 30 DAY) 
            AND lead_time_minutes IS NOT NULL
        """,
        
        "Change Failure Rate": """
            SELECT ROUND((SUM(CASE WHEN type = 'BUG' THEN 1 ELSE 0 END) * 100.0) / NULLIF(COUNT(*), 0), 1) as failure_rate 
            FROM issues 
            WHERE status = 'DONE' AND id LIKE 'openproject:%' 
            AND resolution_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """,
        
        "Issue Metrics by Type": """
            SELECT type as 'Issue Type', 
                   COUNT(*) as 'Total', 
                   COUNT(CASE WHEN status = 'DONE' THEN 1 END) as 'Completed',
                   ROUND((COUNT(CASE WHEN status = 'DONE' THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 1) as 'Completion %',
                   ROUND(AVG(CASE WHEN status = 'DONE' AND lead_time_minutes IS NOT NULL THEN lead_time_minutes END)/1440, 1) as 'Avg Lead Time (Days)'
            FROM issues 
            WHERE id LIKE 'openproject:%' 
            GROUP BY type 
            ORDER BY 'Total' DESC
        """,
        
        "Time Logging Analysis by Project": """
            SELECT i.original_project as 'Project', 
                   COUNT(w.id) as 'Worklogs', 
                   ROUND(SUM(w.time_spent_minutes)/60, 1) as 'Total Hours',
                   COUNT(DISTINCT w.author_id) as 'Contributors'
            FROM issues i 
            LEFT JOIN issue_worklogs w ON i.id = w.issue_id 
            WHERE i.id LIKE 'openproject:%' AND w.id IS NOT NULL 
            GROUP BY i.original_project 
            ORDER BY 'Total Hours' DESC
        """
    }
    
    for query_name, query in queries.items():
        run_query_preview(cursor, query_name, query)
    
    cursor.close()
    connection.close()

def show_data_summary():
    """Show overall data summary"""
    config = load_config()
    connection = get_db_connection(config)
    cursor = connection.cursor()
    
    print("📊 DATA SUMMARY")
    print("=" * 50)
    
    # Get data counts
    tables_to_check = [
        ('Issues (Total)', 'issues', "WHERE id LIKE 'openproject:%'"),
        ('Issues (Active)', 'issues', "WHERE id LIKE 'openproject:%' AND status IN ('TODO', 'IN_PROGRESS')"),
        ('Issues (Completed)', 'issues', "WHERE id LIKE 'openproject:%' AND status = 'DONE'"),
        ('Boards/Projects', 'boards', "WHERE type = 'openproject'"),
        ('Worklogs', 'issue_worklogs', "WHERE id LIKE 'openproject:%'"),
        ('Accounts/Users', 'accounts', "WHERE id LIKE 'openproject:%'"),
    ]
    
    summary_data = []
    for label, table, where_clause in tables_to_check:
        try:
            query = f"SELECT COUNT(*) FROM {table} {where_clause}"
            cursor.execute(query)
            count = cursor.fetchone()[0]
            summary_data.append([label, f"{count:,}"])
        except Exception as e:
            summary_data.append([label, f"Error: {e}"])
    
    print(tabulate(summary_data, headers=['Data Type', 'Count'], tablefmt='grid'))
    
    cursor.close()
    connection.close()

def main():
    parser = argparse.ArgumentParser(description='Preview Grafana dashboard data')
    parser.add_argument('--dashboard', choices=['team', 'sprint', 'dora', 'all'], 
                       default='all', help='Which dashboard to preview')
    parser.add_argument('--summary', action='store_true', 
                       help='Show data summary only')
    
    args = parser.parse_args()
    
    try:
        if args.summary:
            show_data_summary()
            return
            
        if args.dashboard in ['team', 'all']:
            preview_team_productivity()
            
        if args.dashboard in ['sprint', 'all']:
            preview_sprint_progress()
            
        if args.dashboard in ['dora', 'all']:
            preview_dora_metrics()
            
        print("\n" + "=" * 70)
        print("🎯 PREVIEW COMPLETE")
        print("=" * 70)
        print("✅ All queries executed successfully!")
        print("\n🚀 Next Steps:")
        print("1. Run the Grafana setup script to create dashboards")
        print("2. Customize queries and visualizations as needed")
        print("3. Set up alerts and monitoring")
        
    except Exception as e:
        print(f"\n❌ Error during preview: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())