#!/usr/bin/env python3
"""
OpenProject DevLake Integration - Complete Pipeline Orchestrator

This script orchestrates the complete data pipeline:
1. Data Collection (Collector)
2. Data Extraction (Extractor) 
3. Domain Conversion (Converter)

Usage:
    python3 run_pipeline.py [--full-sync] [--verbose] [--dry-run]
"""

import subprocess
import sys
import logging
import yaml
from pathlib import Path
from datetime import datetime
import argparse

def setup_logging(verbose=False):
    """Set up logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/pipeline.log')
        ]
    )
    return logging.getLogger(__name__)

def run_component(script_path, description, verbose=False, dry_run=False):
    """Run a pipeline component and return success status"""
    logger = logging.getLogger(__name__)
    
    if dry_run:
        logger.info(f"[DRY RUN] Would run: {description}")
        return True, 0, ""
    
    logger.info(f"Starting: {description}")
    start_time = datetime.now()
    
    cmd = [sys.executable, script_path]
    if verbose:
        cmd.append('--verbose')
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        duration = datetime.now() - start_time
        
        if result.returncode == 0:
            logger.info(f"✓ Completed: {description} (took {duration})")
            if verbose and result.stdout:
                logger.debug(f"Output: {result.stdout[-500:]}")  # Last 500 chars
            return True, result.returncode, result.stdout
        else:
            logger.error(f"❌ Failed: {description} (took {duration})")
            logger.error(f"Error: {result.stderr}")
            return False, result.returncode, result.stderr
            
    except Exception as e:
        duration = datetime.now() - start_time
        logger.error(f"❌ Exception in {description}: {e} (took {duration})")
        return False, -1, str(e)

def load_config():
    """Load pipeline configuration"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def main():
    parser = argparse.ArgumentParser(description='OpenProject DevLake Integration Pipeline')
    parser.add_argument('--full-sync', action='store_true', 
                       help='Force full sync (ignore incremental settings)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be executed without running')
    parser.add_argument('--skip-collection', action='store_true',
                       help='Skip data collection (use existing raw data)')
    parser.add_argument('--skip-extraction', action='store_true',
                       help='Skip data extraction (use existing tool data)')
    
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging(args.verbose)
    
    # Load configuration
    try:
        config = load_config()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1
    
    # Pipeline components
    components = []
    
    if not args.skip_collection:
        components.append({
            'script': 'collectors/openproject_collector.py',
            'description': 'Data Collection from OpenProject API',
            'required': True
        })
    
    if not args.skip_extraction:
        components.append({
            'script': 'extractors/openproject_extractor.py', 
            'description': 'Data Extraction to Tool Layer',
            'required': True
        })
    
    components.append({
        'script': 'converters/openproject_converter.py',
        'description': 'Domain Conversion to DevLake Schema',
        'required': True
    })
    
    # Print pipeline plan
    logger.info("=" * 60)
    logger.info("OpenProject DevLake Integration Pipeline")
    logger.info("=" * 60)
    logger.info(f"Mode: {'DRY RUN' if args.dry_run else 'EXECUTION'}")
    logger.info(f"Verbose: {args.verbose}")
    logger.info(f"Full Sync: {args.full_sync}")
    logger.info("")
    logger.info("Pipeline Components:")
    
    for i, component in enumerate(components, 1):
        status = "REQUIRED" if component['required'] else "OPTIONAL"
        logger.info(f"  {i}. {component['description']} [{status}]")
    
    logger.info("")
    
    if args.dry_run:
        logger.info("DRY RUN COMPLETE - No actual execution performed")
        return 0
    
    # Execute pipeline
    start_time = datetime.now()
    failed_components = []
    
    for i, component in enumerate(components, 1):
        logger.info(f"[{i}/{len(components)}] {component['description']}")
        
        success, return_code, output = run_component(
            component['script'],
            component['description'],
            args.verbose,
            args.dry_run
        )
        
        if not success:
            failed_components.append(component['description'])
            if component['required']:
                logger.error(f"Required component failed: {component['description']}")
                logger.error("Pipeline execution stopped due to failure")
                break
            else:
                logger.warning(f"Optional component failed: {component['description']}")
    
    # Pipeline summary
    total_duration = datetime.now() - start_time
    logger.info("")
    logger.info("=" * 60)
    logger.info("Pipeline Execution Summary")
    logger.info("=" * 60)
    logger.info(f"Total Duration: {total_duration}")
    logger.info(f"Components Executed: {len(components) - len(failed_components)}/{len(components)}")
    
    if failed_components:
        logger.error(f"Failed Components: {len(failed_components)}")
        for component in failed_components:
            logger.error(f"  ❌ {component}")
        return 1
    else:
        logger.info("✓ All components completed successfully")
        logger.info("")
        logger.info("Next Steps:")
        logger.info("  1. Verify data in DevLake domain tables")
        logger.info("  2. Set up Grafana dashboards for visualization")
        logger.info("  3. Configure automated scheduling (cron/systemd)")
        return 0

if __name__ == "__main__":
    sys.exit(main())