"""
Kafka Integration Module for STT Service
Handles Kafka producer and consumer operations
"""
import json
import logging
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import time

logger = logging.getLogger(__name__)

class KafkaHandler:
    def __init__(self, bootstrap_servers):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.consumer = None
        self.initialize_producer()
    
    def initialize_producer(self):
        """Initialize Kafka producer with retry logic"""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    acks='all',
                    retries=3,
                    max_in_flight_requests_per_connection=1,
                    compression_type='gzip'
                )
                logger.info("Kafka producer initialized successfully")
                return
            except KafkaError as e:
                retry_count += 1
                logger.warning(f"Failed to initialize Kafka producer (attempt {retry_count}/{max_retries}): {str(e)}")
                time.sleep(5)
        
        logger.error("Failed to initialize Kafka producer after all retries")
    
    def publish_transcription(self, message):
        """
        Publish transcription event to Kafka
        Topic: audio-transcribed
        """
        try:
            if not self.producer:
                self.initialize_producer()
            
            future = self.producer.send(
                'audio-transcribed',
                key=message.get('user_id'),
                value=message
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Message published to topic {record_metadata.topic} "
                f"partition {record_metadata.partition} "
                f"offset {record_metadata.offset}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error publishing to Kafka: {str(e)}")
            return False
    
    def publish_error(self, error_message):
        """Publish error event to error topic"""
        try:
            if not self.producer:
                self.initialize_producer()
            
            self.producer.send(
                'stt-errors',
                value=error_message
            )
            logger.info("Error message published to Kafka")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing error to Kafka: {str(e)}")
            return False
    
    def start_consumer(self, callback):
        """
        Start Kafka consumer
        Listens to: audio-upload, audio-processing-request
        """
        try:
            self.consumer = KafkaConsumer(
                'audio-upload',
                'audio-processing-request',
                bootstrap_servers=self.bootstrap_servers,
                group_id='stt-service-group',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                max_poll_records=10
            )
            
            logger.info("Kafka consumer started, listening for messages...")
            
            for message in self.consumer:
                try:
                    logger.info(f"Received message from topic {message.topic}")
                    callback(message.value)
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    self.publish_error({
                        'service': 'stt-service',
                        'error': str(e),
                        'message': message.value
                    })
                    
        except Exception as e:
            logger.error(f"Kafka consumer error: {str(e)}")
    
    def check_connection(self):
        """Check Kafka connection status"""
        try:
            if self.producer:
                # Try to get cluster metadata
                self.producer.bootstrap_connected()
                return True
            return False
        except:
            return False
    
    def close(self):
        """Close Kafka connections"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
        if self.consumer:
            self.consumer.close()
        logger.info("Kafka connections closed")