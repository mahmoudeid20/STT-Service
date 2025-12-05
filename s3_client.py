"""
S3 Client Module
Handles AWS S3 operations for audio files
"""
import os
import logging
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class S3Client:
    def __init__(self, bucket_name, region_name='us-east-1'):
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.s3_client = None
        self.initialize_client()
    
    def initialize_client(self):
        """Initialize S3 client"""
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=self.region_name,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            logger.info("S3 client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise
    
    def upload_file(self, file_path, object_name=None, metadata=None):
        """
        Upload file to S3
        
        Args:
            file_path: Path to local file
            object_name: S3 object name (key)
            metadata: Optional metadata dict
        
        Returns:
            S3 URL of uploaded file
        """
        if object_name is None:
            object_name = os.path.basename(file_path)
        
        try:
            extra_args = {
                'ContentType': self._get_content_type(file_path)
            }
            
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                object_name,
                ExtraArgs=extra_args
            )
            
            s3_url = f"s3://{self.bucket_name}/{object_name}"
            logger.info(f"File uploaded to S3: {s3_url}")
            return s3_url
            
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            raise
    
    def download_file(self, object_name, local_path):
        """
        Download file from S3
        
        Args:
            object_name: S3 object name (key)
            local_path: Local path to save file
        """
        try:
            self.s3_client.download_file(
                self.bucket_name,
                object_name,
                local_path
            )
            logger.info(f"File downloaded from S3: {object_name}")
            return local_path
            
        except ClientError as e:
            logger.error(f"Error downloading file from S3: {str(e)}")
            raise
    
    def delete_file(self, object_name):
        """
        Delete file from S3
        
        Args:
            object_name: S3 object name (key)
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            logger.info(f"File deleted from S3: {object_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {str(e)}")
            return False
    
    def generate_presigned_url(self, object_name, expiration=3600):
        """
        Generate presigned URL for temporary access
        
        Args:
            object_name: S3 object name (key)
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Presigned URL string
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_name
                },
                ExpiresIn=expiration
            )
            return url
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return None
    
    def list_files(self, prefix='', max_keys=1000):
        """
        List files in S3 bucket
        
        Args:
            prefix: Filter by prefix
            max_keys: Maximum number of keys to return
        
        Returns:
            List of file information dicts
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'etag': obj['ETag']
                    })
            
            return files
            
        except ClientError as e:
            logger.error(f"Error listing files in S3: {str(e)}")
            return []
    
    def file_exists(self, object_name):
        """
        Check if file exists in S3
        
        Args:
            object_name: S3 object name (key)
        
        Returns:
            Boolean
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            return True
        except ClientError:
            return False
    
    def get_file_metadata(self, object_name):
        """
        Get file metadata from S3
        
        Args:
            object_name: S3 object name (key)
        
        Returns:
            Metadata dict
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified').isoformat(),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            logger.error(f"Error getting file metadata: {str(e)}")
            return None
    
    def copy_file(self, source_key, dest_key):
        """
        Copy file within S3
        
        Args:
            source_key: Source object key
            dest_key: Destination object key
        """
        try:
            copy_source = {
                'Bucket': self.bucket_name,
                'Key': source_key
            }
            
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=dest_key
            )
            
            logger.info(f"File copied in S3: {source_key} -> {dest_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error copying file in S3: {str(e)}")
            return False
    
    def _get_content_type(self, file_path):
        """Determine content type based on file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.flac': 'audio/flac',
            '.ogg': 'audio/ogg',
            '.m4a': 'audio/m4a',
            '.json': 'application/json',
            '.txt': 'text/plain'
        }
        return content_types.get(ext, 'application/octet-stream')
