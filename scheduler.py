#!/usr/bin/env python3
"""
Scheduler for OpenProject DevLake Integration Pipeline
Runs data collection, extraction, and conversion on a schedule
"""

import schedule
import time
import logging
import subprocess
import sys
from datetime import datetime
import yaml

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from config.yaml"""
    try:
        with open('config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config.yaml: {e}")
        return None

def run_pipeline():
    """Run the complete OpenProject DevLake pipeline"""
    logger.info("="*60)
    logger.info(f"Starting scheduled pipeline run at {datetime.now()}")
    logger.info("="*60)
    
    try:
        # Run the complete pipeline
        result = subprocess.run(
            ['python3', 'run_pipeline.py', '--verbose'],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode == 0:
            logger.info("✅ Pipeline completed successfully!")
            logger.info(f"Output: {result.stdout}")
        else:
            logger.error(f"❌ Pipeline failed with return code {result.returncode}")
            logger.error(f"Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Pipeline timed out after 1 hour")
    except Exception as e:
        logger.error(f"❌ Pipeline execution failed: {e}")
    
    logger.info(f"Pipeline run completed at {datetime.now()}")
    logger.info("="*60)

def run_collector_only():
    """Run only the data collector"""
    logger.info(f"Running collector at {datetime.now()}")
    try:
        result = subprocess.run(
            ['python3', 'collectors/openproject_collector.py'],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes timeout
        )
        if result.returncode == 0:
            logger.info("✅ Collector completed successfully")
        else:
            logger.error(f"❌ Collector failed: {result.stderr}")
    except Exception as e:
        logger.error(f"❌ Collector execution failed: {e}")

def main():
    """Main scheduler function"""
    logger.info("🚀 OpenProject DevLake Scheduler Started")
    logger.info("="*60)
    
    # Load configuration
    config = load_config()
    if not config:
        logger.error("Failed to load configuration. Exiting...")
        sys.exit(1)
    
    # Get schedule settings from config
    collection_settings = config.get('collection', {})
    sync_interval_hours = collection_settings.get('sync_interval_hours', 6)
    
    logger.info(f"Configuration loaded:")
    logger.info(f"  - Sync interval: {sync_interval_hours} hours")
    logger.info(f"  - Incremental sync: {collection_settings.get('incremental_sync', True)}")
    logger.info("="*60)
    
    # Schedule tasks
    # Run full pipeline every N hours (from config)
    schedule.every(sync_interval_hours).hours.do(run_pipeline)
    
    # Optional: Run quick collector-only checks more frequently
    # schedule.every(1).hours.do(run_collector_only)
    
    # Optional: Daily full sync at specific time
    # schedule.every().day.at("02:00").do(run_pipeline)
    
    logger.info("📅 Scheduled Tasks:")
    logger.info(f"  - Full pipeline: Every {sync_interval_hours} hours")
    logger.info("="*60)
    
    # Run once immediately on startup
    logger.info("Running initial pipeline execution...")
    run_pipeline()
    
    # Main scheduler loop
    logger.info("Entering scheduler loop. Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("\n👋 Scheduler stopped by user")
    except Exception as e:
        logger.error(f"❌ Scheduler error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
