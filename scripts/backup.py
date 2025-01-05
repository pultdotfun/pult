#!/usr/bin/env python3
import os
import subprocess
from datetime import datetime
import boto3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self):
        self.backup_dir = "/backups"
        self.s3_bucket = os.getenv("BACKUP_BUCKET")
        self.db_name = os.getenv("POSTGRES_DB")
        self.db_user = os.getenv("POSTGRES_USER")
        
        # Initialize S3 client
        self.s3 = boto3.client('s3')
    
    def create_database_backup(self):
        """Create PostgreSQL database backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{self.backup_dir}/pult_db_{timestamp}.sql"
        
        try:
            subprocess.run([
                "pg_dump",
                "-U", self.db_user,
                "-d", self.db_name,
                "-f", backup_file
            ], check=True)
            
            logger.info(f"Database backup created: {backup_file}")
            return backup_file
        except Exception as e:
            logger.error(f"Database backup failed: {str(e)}")
            raise
    
    def upload_to_s3(self, file_path):
        """Upload backup to S3"""
        try:
            file_name = os.path.basename(file_path)
            self.s3.upload_file(
                file_path,
                self.s3_bucket,
                f"backups/{file_name}"
            )
            logger.info(f"Backup uploaded to S3: {file_name}")
        except Exception as e:
            logger.error(f"S3 upload failed: {str(e)}")
            raise
    
    def cleanup_old_backups(self, keep_days=7):
        """Clean up old backup files"""
        try:
            # Local cleanup
            subprocess.run([
                "find", self.backup_dir,
                "-type", "f",
                "-mtime", f"+{keep_days}",
                "-delete"
            ])
            
            # S3 cleanup
            response = self.s3.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix="backups/"
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Check if backup is older than keep_days
                    if (datetime.now() - obj['LastModified'].replace(tzinfo=None)).days > keep_days:
                        self.s3.delete_object(
                            Bucket=self.s3_bucket,
                            Key=obj['Key']
                        )
            
            logger.info("Old backups cleaned up")
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            raise

if __name__ == "__main__":
    backup_manager = BackupManager()
    
    try:
        # Create backup
        backup_file = backup_manager.create_database_backup()
        
        # Upload to S3
        backup_manager.upload_to_s3(backup_file)
        
        # Cleanup old backups
        backup_manager.cleanup_old_backups()
        
        logger.info("Backup process completed successfully")
    except Exception as e:
        logger.error(f"Backup process failed: {str(e)}")
        exit(1) 