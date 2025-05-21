# src/database/db_manager.py

import sqlite3
from datetime import datetime
from typing import Dict, List
import json

class DatabaseManager:
    def __init__(self, db_path: str = 'ci_insights.db'):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        """Get a database connection."""
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            
            # Pipeline runs table
            c.execute('''
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT UNIQUE,
                    workflow_name TEXT,
                    status TEXT,
                    conclusion TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    duration INTEGER,
                    repository TEXT,
                    branch TEXT,
                    commit_sha TEXT,
                    failure_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Test results table
            c.execute('''
                CREATE TABLE IF NOT EXISTS test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    test_name TEXT,
                    status TEXT,
                    duration REAL,
                    failure_message TEXT,
                    error_type TEXT,
                    stack_trace TEXT,
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES pipeline_runs(run_id)
                )
            ''')
            
            # Error patterns table
            c.execute('''
                CREATE TABLE IF NOT EXISTS error_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT,
                    error_type TEXT,
                    frequency INTEGER,
                    last_seen TIMESTAMP,
                    suggested_fix TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Analysis results table
            c.execute('''
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_type TEXT,
                    data JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()

    def store_pipeline_run(self, run_data: Dict):
        """Store pipeline run data."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT OR REPLACE INTO pipeline_runs (
                    run_id, workflow_name, status, conclusion,
                    started_at, completed_at, duration,
                    repository, branch, commit_sha, failure_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                run_data['run_id'],
                run_data['workflow_name'],
                run_data['status'],
                run_data['conclusion'],
                run_data['started_at'],
                run_data['completed_at'],
                run_data['duration'],
                run_data['repository'],
                run_data['branch'],
                run_data['commit_sha'],
                run_data.get('failure_reason')
            ))
            conn.commit()

    def store_test_result(self, test_data: Dict):
        """Store test result data."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO test_results (
                    run_id, test_name, status, duration,
                    failure_message, error_type, stack_trace, retry_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                test_data['run_id'],
                test_data['test_name'],
                test_data['status'],
                test_data['duration'],
                test_data.get('failure_message'),
                test_data.get('error_type'),
                test_data.get('stack_trace'),
                test_data.get('retry_count', 0)
            ))
            conn.commit()

    def store_error_pattern(self, pattern_data: Dict):
        """Store error pattern data."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT OR REPLACE INTO error_patterns (
                    pattern, error_type, frequency, last_seen, suggested_fix
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                pattern_data['pattern'],
                pattern_data['error_type'],
                pattern_data['frequency'],
                pattern_data['last_seen'],
                pattern_data['suggested_fix']
            ))
            conn.commit()

    def store_analysis_result(self, analysis_type: str, analysis_data: dict):
        """Store analysis results in the database."""
        with self.get_connection() as conn:
            c = conn.cursor()
            
            # First, drop the existing table if it exists
            c.execute('DROP TABLE IF EXISTS analysis_results')
            
            # Create the table with the correct schema
            c.execute('''
                CREATE TABLE analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_type TEXT NOT NULL,
                    failure_id TEXT,
                    analysis_data TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    workflow_name TEXT,
                    failure_reason TEXT
                )
            ''')
            conn.commit()
            
            # Now insert the data
            try:
                c.execute('''
                    INSERT INTO analysis_results 
                    (analysis_type, failure_id, analysis_data, timestamp, workflow_name, failure_reason)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    analysis_type,
                    analysis_data.get('failure_id'),
                    json.dumps(analysis_data),
                    analysis_data.get('timestamp', datetime.now().isoformat()),
                    analysis_data.get('workflow_name'),
                    analysis_data.get('failure_reason')
                ))
                conn.commit()
            except sqlite3.OperationalError as e:
                print(f"Error storing analysis result: {str(e)}")
                # If there's an error, try to recreate the table and insert again
                c.execute('DROP TABLE IF EXISTS analysis_results')
                c.execute('''
                    CREATE TABLE analysis_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        analysis_type TEXT NOT NULL,
                        failure_id TEXT,
                        analysis_data TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        workflow_name TEXT,
                        failure_reason TEXT
                    )
                ''')
                conn.commit()
                
                # Try the insert again
                c.execute('''
                    INSERT INTO analysis_results 
                    (analysis_type, failure_id, analysis_data, timestamp, workflow_name, failure_reason)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    analysis_type,
                    analysis_data.get('failure_id'),
                    json.dumps(analysis_data),
                    analysis_data.get('timestamp', datetime.now().isoformat()),
                    analysis_data.get('workflow_name'),
                    analysis_data.get('failure_reason')
                ))
                conn.commit()

    def dict_factory(self, cursor, row):
        """Convert database row to dictionary."""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d