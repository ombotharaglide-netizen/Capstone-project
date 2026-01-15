"""Optional demo data seeding script for testing and demonstration purposes.

This script populates the database and vector store with realistic synthetic
DevOps log entries covering common failure scenarios.

Usage:
    python -m scripts.seed_demo_data

Note: This script is for demo/testing purposes only and should not be run
in production environments.
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal, init_db
from app.core.logging import get_logger, setup_logging
from app.services.log_parser import LogParser
from app.services.resolver import get_resolver

# Setup logging
setup_logging()
logger = get_logger(__name__)


# Demo log entries covering common DevOps failure scenarios
DEMO_LOGS = [
    # Database connection timeouts
    {
        "service_name": "api-service",
        "error_level": "ERROR",
        "error_message": "Database connection timeout after 30 seconds. Unable to establish connection to postgresql://db-prod:5432/app_db",
        "raw_log": "2024-01-15 14:23:45 ERROR [api-service] Database connection timeout after 30 seconds. Unable to establish connection to postgresql://db-prod:5432/app_db. Retry attempt 3/3 failed.",
        "log_metadata": {"environment": "production", "region": "us-east-1", "retry_count": 3},
    },
    {
        "service_name": "api-service",
        "error_level": "ERROR",
        "error_message": "Connection pool exhausted. All 50 connections are in use. Waiting for available connection...",
        "raw_log": "2024-01-15 14:25:12 ERROR [api-service] Connection pool exhausted. All 50 connections are in use. Waiting for available connection... Request ID: req-abc123",
        "log_metadata": {"environment": "production", "pool_size": 50, "active_connections": 50},
    },
    {
        "service_name": "worker-service",
        "error_level": "ERROR",
        "error_message": "Database query timeout: SELECT * FROM orders WHERE status = 'pending' exceeded 10 second limit",
        "raw_log": "2024-01-15 15:10:33 ERROR [worker-service] Database query timeout: SELECT * FROM orders WHERE status = 'pending' exceeded 10 second limit. Query cancelled.",
        "log_metadata": {"environment": "production", "query_timeout": 10, "table": "orders"},
    },
    # Authentication failures
    {
        "service_name": "auth-service",
        "error_level": "ERROR",
        "error_message": "Authentication failed: Invalid credentials for user admin@example.com. IP: 192.168.1.100",
        "raw_log": "2024-01-15 16:45:22 ERROR [auth-service] Authentication failed: Invalid credentials for user admin@example.com. IP: 192.168.1.100. Attempt 5/5",
        "log_metadata": {"environment": "production", "user": "admin@example.com", "ip_address": "192.168.1.100", "attempts": 5},
    },
    {
        "service_name": "auth-service",
        "error_level": "WARN",
        "error_message": "JWT token expired. Token issued at 2024-01-15T10:00:00Z, expired at 2024-01-15T11:00:00Z",
        "raw_log": "2024-01-15 11:05:15 WARN [auth-service] JWT token expired. Token issued at 2024-01-15T10:00:00Z, expired at 2024-01-15T11:00:00Z. User ID: user-12345",
        "log_metadata": {"environment": "production", "token_type": "JWT", "user_id": "user-12345"},
    },
    {
        "service_name": "api-gateway",
        "error_level": "ERROR",
        "error_message": "OAuth2 token validation failed: Invalid signature. Token rejected.",
        "raw_log": "2024-01-15 12:30:45 ERROR [api-gateway] OAuth2 token validation failed: Invalid signature. Token rejected. Request path: /api/v1/users",
        "log_metadata": {"environment": "production", "auth_type": "OAuth2", "request_path": "/api/v1/users"},
    },
    # Disk space exhaustion
    {
        "service_name": "storage-service",
        "error_level": "CRITICAL",
        "error_message": "Disk space exhausted. Available: 0 bytes (0%), Used: 500GB (100%). Mount point: /var/data",
        "raw_log": "2024-01-15 18:20:10 CRITICAL [storage-service] Disk space exhausted. Available: 0 bytes (0%), Used: 500GB (100%). Mount point: /var/data. Service may become unavailable.",
        "log_metadata": {"environment": "production", "mount_point": "/var/data", "total_space": "500GB", "used_space": "500GB"},
    },
    {
        "service_name": "log-aggregator",
        "error_level": "WARN",
        "error_message": "Low disk space warning: Only 5GB (1%) remaining on /var/logs. Consider log rotation or cleanup.",
        "raw_log": "2024-01-15 19:15:30 WARN [log-aggregator] Low disk space warning: Only 5GB (1%) remaining on /var/logs. Consider log rotation or cleanup. Current log size: 495GB",
        "log_metadata": {"environment": "production", "mount_point": "/var/logs", "available_space": "5GB", "usage_percent": 99},
    },
    {
        "service_name": "backup-service",
        "error_level": "ERROR",
        "error_message": "Backup failed: Insufficient disk space. Required: 100GB, Available: 10GB",
        "raw_log": "2024-01-15 20:00:00 ERROR [backup-service] Backup failed: Insufficient disk space. Required: 100GB, Available: 10GB. Backup job: daily-backup-2024-01-15",
        "log_metadata": {"environment": "production", "backup_job": "daily-backup-2024-01-15", "required_space": "100GB", "available_space": "10GB"},
    },
    # API gateway timeouts
    {
        "service_name": "api-gateway",
        "error_level": "ERROR",
        "error_message": "Upstream service timeout: api-service did not respond within 30 seconds. Request ID: req-xyz789",
        "raw_log": "2024-01-15 21:30:15 ERROR [api-gateway] Upstream service timeout: api-service did not respond within 30 seconds. Request ID: req-xyz789. Path: /api/v1/orders",
        "log_metadata": {"environment": "production", "upstream_service": "api-service", "timeout": 30, "request_path": "/api/v1/orders"},
    },
    {
        "service_name": "api-gateway",
        "error_level": "ERROR",
        "error_message": "Circuit breaker opened for payment-service after 5 consecutive failures. Requests will be rejected for 60 seconds.",
        "raw_log": "2024-01-15 22:15:45 ERROR [api-gateway] Circuit breaker opened for payment-service after 5 consecutive failures. Requests will be rejected for 60 seconds. Last error: Connection refused",
        "log_metadata": {"environment": "production", "upstream_service": "payment-service", "failure_count": 5, "circuit_breaker_state": "open"},
    },
    {
        "service_name": "load-balancer",
        "error_level": "WARN",
        "error_message": "High latency detected: Average response time 2.5s exceeds threshold of 1.0s for api-service",
        "raw_log": "2024-01-15 23:00:30 WARN [load-balancer] High latency detected: Average response time 2.5s exceeds threshold of 1.0s for api-service. Active connections: 150",
        "log_metadata": {"environment": "production", "service": "api-service", "avg_latency": "2.5s", "threshold": "1.0s", "active_connections": 150},
    },
    # Memory pressure warnings
    {
        "service_name": "api-service",
        "error_level": "WARN",
        "error_message": "High memory usage: 4.5GB / 5GB (90%). Consider scaling or optimizing memory usage.",
        "raw_log": "2024-01-16 00:30:20 WARN [api-service] High memory usage: 4.5GB / 5GB (90%). Consider scaling or optimizing memory usage. Heap size: 3.2GB",
        "log_metadata": {"environment": "production", "memory_used": "4.5GB", "memory_total": "5GB", "usage_percent": 90, "heap_size": "3.2GB"},
    },
    {
        "service_name": "worker-service",
        "error_level": "ERROR",
        "error_message": "Out of memory error: Unable to allocate 512MB for task processing. Process terminated.",
        "raw_log": "2024-01-16 01:15:55 ERROR [worker-service] Out of memory error: Unable to allocate 512MB for task processing. Process terminated. Task ID: task-456",
        "log_metadata": {"environment": "production", "task_id": "task-456", "requested_memory": "512MB", "available_memory": "100MB"},
    },
    {
        "service_name": "cache-service",
        "error_level": "WARN",
        "error_message": "Memory cache eviction rate high: 1000 evictions/second. Cache hit rate dropped to 60%",
        "raw_log": "2024-01-16 02:00:10 WARN [cache-service] Memory cache eviction rate high: 1000 evictions/second. Cache hit rate dropped to 60%. Cache size: 2GB / 2GB",
        "log_metadata": {"environment": "production", "eviction_rate": "1000/sec", "hit_rate": "60%", "cache_size": "2GB"},
    },
    # Additional common scenarios
    {
        "service_name": "scheduler-service",
        "error_level": "ERROR",
        "error_message": "Scheduled job failed: daily-report-generation. Error: FileNotFoundError: /reports/template.xlsx not found",
        "raw_log": "2024-01-16 03:00:00 ERROR [scheduler-service] Scheduled job failed: daily-report-generation. Error: FileNotFoundError: /reports/template.xlsx not found. Retry scheduled in 1 hour.",
        "log_metadata": {"environment": "production", "job_name": "daily-report-generation", "error_type": "FileNotFoundError"},
    },
    {
        "service_name": "notification-service",
        "error_level": "ERROR",
        "error_message": "Failed to send email notification: SMTP server unreachable. smtp.example.com:587 connection refused",
        "raw_log": "2024-01-16 04:30:45 ERROR [notification-service] Failed to send email notification: SMTP server unreachable. smtp.example.com:587 connection refused. Retry attempt 2/3",
        "log_metadata": {"environment": "production", "notification_type": "email", "smtp_server": "smtp.example.com:587", "retry_attempt": 2},
    },
    {
        "service_name": "api-service",
        "error_level": "ERROR",
        "error_message": "Rate limit exceeded: 1000 requests per minute limit reached. Client IP: 203.0.113.42",
        "raw_log": "2024-01-16 05:15:20 ERROR [api-service] Rate limit exceeded: 1000 requests per minute limit reached. Client IP: 203.0.113.42. Retry after: 60 seconds",
        "log_metadata": {"environment": "production", "rate_limit": "1000/min", "client_ip": "203.0.113.42", "retry_after": 60},
    },
]


def seed_demo_data() -> None:
    """Seed database and vector store with demo log entries."""
    logger.info("Starting demo data seeding...")
    logger.info(f"Will insert {len(DEMO_LOGS)} demo log entries")

    # Initialize database
    init_db()

    # Create database session
    db = SessionLocal()

    try:
        # Initialize services
        parser = LogParser()
        resolver = get_resolver()

        # Process each demo log
        for i, log_data in enumerate(DEMO_LOGS, 1):
            try:
                logger.info(f"Processing log {i}/{len(DEMO_LOGS)}: {log_data['service_name']} - {log_data['error_level']}")

                # Parse log (using structured format)
                from app.models.schemas import LogIngestionRequest

                request = LogIngestionRequest(
                    service_name=log_data["service_name"],
                    error_level=log_data["error_level"],
                    error_message=log_data["error_message"],
                    raw_log=log_data["raw_log"],
                    log_metadata=log_data.get("log_metadata"),
                )

                parsed = parser.parse_structured_log(request)

                # Store log with embedding
                log_entry = resolver.store_log_with_embedding(parsed, db, embedding_id=None)

                logger.info(f"✓ Successfully inserted log entry {log_entry.id}")

            except Exception as e:
                logger.error(f"✗ Failed to insert log {i}: {e}")
                db.rollback()
                continue

        # Commit all changes
        db.commit()
        logger.info(f"✓ Successfully seeded {len(DEMO_LOGS)} demo log entries")

        # Display summary
        from app.models.domain import LogEntry
        from app.services.vector_store import get_vector_store

        total_logs = db.query(LogEntry).count()
        vector_store = get_vector_store()
        total_embeddings = vector_store.count()

        logger.info("=" * 60)
        logger.info("Demo Data Seeding Summary:")
        logger.info(f"  Total log entries in database: {total_logs}")
        logger.info(f"  Total embeddings in vector store: {total_embeddings}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error during demo data seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        seed_demo_data()
        logger.info("Demo data seeding completed successfully!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Demo data seeding failed: {e}")
        sys.exit(1)
