# src/utils/seed_data.py

from datetime import datetime, timedelta
import random
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import DatabaseManager

def seed_database():
    db = DatabaseManager()
    
    # Sample workflow names
    workflows = [
        "Build and Test",
        "Deploy to Staging",
        "Security Scan",
        "Integration Tests",
        "Performance Tests"
    ]
    
    # Sample test names
    tests = [
        "test_user_authentication",
        "test_payment_processing",
        "test_api_endpoints",
        "test_database_operations",
        "test_frontend_components"
    ]
    
    # Sample failure reasons
    failure_reasons = [
        "Dependency resolution failed",
        "Test timeout exceeded",
        "Memory limit exceeded",
        "Network connectivity issues",
        "Resource quota exceeded"
    ]
    
    # Sample error patterns
    error_patterns = [
        {
            "pattern": "Connection refused",
            "error_type": "NetworkError",
            "frequency": 5,
            "last_seen": datetime.now().isoformat(),
            "suggested_fix": "Check network connectivity and firewall settings"
        },
        {
            "pattern": "Out of memory",
            "error_type": "MemoryError",
            "frequency": 3,
            "last_seen": datetime.now().isoformat(),
            "suggested_fix": "Increase memory limit or optimize memory usage"
        },
        {
            "pattern": "Test timeout",
            "error_type": "TimeoutError",
            "frequency": 4,
            "last_seen": datetime.now().isoformat(),
            "suggested_fix": "Increase test timeout or optimize slow tests"
        }
    ]
    
    # Generate pipeline runs for the last 7 days
    for i in range(20):  # 20 pipeline runs
        # Random date within last 7 days
        start_time = datetime.now() - timedelta(days=random.randint(0, 7))
        duration = random.randint(300, 3600)  # 5-60 minutes
        end_time = start_time + timedelta(seconds=duration)
        
        # Randomly decide if this run failed
        is_failure = random.random() < 0.3  # 30% chance of failure
        
        pipeline_run = {
            'run_id': f'run_{i}',
            'workflow_name': random.choice(workflows),
            'status': 'completed',
            'conclusion': 'failure' if is_failure else 'success',
            'started_at': start_time.isoformat(),
            'completed_at': end_time.isoformat(),
            'duration': duration,
            'repository': 'example/ci-failure-insights',
            'branch': random.choice(['main', 'develop', 'feature/new-feature']),
            'commit_sha': f'commit_{random.randint(1000, 9999)}',
            'failure_reason': random.choice(failure_reasons) if is_failure else None
        }
        
        # Store pipeline run
        db.store_pipeline_run(pipeline_run)
        
        # Generate test results for this run
        num_tests = random.randint(5, 15)
        for j in range(num_tests):
            test_name = random.choice(tests)
            test_duration = random.uniform(0.1, 5.0)
            
            # If pipeline failed, some tests should fail
            if is_failure and random.random() < 0.4:  # 40% chance of test failure
                error_type = random.choice(['AssertionError', 'TimeoutError', 'ConnectionError'])
                failure_message = f"Test failed: {error_type}"
                stack_trace = f"Traceback (most recent call last):\n  File 'test_{test_name}.py', line 42, in test_{test_name}\n    assert result == expected"
            else:
                error_type = None
                failure_message = None
                stack_trace = None
            
            test_result = {
                'run_id': pipeline_run['run_id'],
                'test_name': test_name,
                'status': 'failed' if error_type else 'passed',
                'duration': test_duration,
                'failure_message': failure_message,
                'error_type': error_type,
                'stack_trace': stack_trace,
                'retry_count': random.randint(0, 2) if error_type else 0
            }
            
            # Store test result
            db.store_test_result(test_result)
    
    # Store error patterns
    for pattern in error_patterns:
        db.store_error_pattern(pattern)
    
    print("Database seeded successfully!")

if __name__ == "__main__":
    seed_database()