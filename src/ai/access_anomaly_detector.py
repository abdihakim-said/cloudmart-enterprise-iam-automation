import boto3
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
import numpy as np

class IAMAccessAnomalyDetector:
    """ML-powered anomaly detection for IAM access patterns"""
    
    def __init__(self, region='us-east-1'):
        self.cloudtrail = boto3.client('cloudtrail', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.model = IsolationForest(contamination=0.1, random_state=42)
    
    def analyze_access_patterns(self, days_back=30) -> Dict:
        """Analyze IAM access patterns for anomalies"""
        
        # Get CloudTrail events
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)
        
        events = self._get_iam_events(start_time, end_time)
        df = pd.DataFrame(events)
        
        if df.empty:
            return {'anomalies': [], 'status': 'no_data'}
        
        # Feature engineering
        features = self._extract_features(df)
        
        # Train model and detect anomalies
        self.model.fit(features)
        anomaly_scores = self.model.decision_function(features)
        anomalies = self.model.predict(features)
        
        # Identify anomalous events
        anomalous_events = df[anomalies == -1].copy()
        anomalous_events['anomaly_score'] = anomaly_scores[anomalies == -1]
        
        return {
            'anomalies': anomalous_events.to_dict('records'),
            'total_events': len(df),
            'anomaly_count': len(anomalous_events),
            'status': 'completed'
        }
    
    def _get_iam_events(self, start_time, end_time) -> List[Dict]:
        """Fetch IAM-related CloudTrail events"""
        
        response = self.cloudtrail.lookup_events(
            LookupAttributes=[
                {
                    'AttributeKey': 'EventName',
                    'AttributeValue': 'AssumeRole'
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            MaxItems=1000
        )
        
        events = []
        for event in response['Events']:
            events.append({
                'event_time': event['EventTime'],
                'user_name': event.get('Username', 'unknown'),
                'source_ip': event.get('SourceIPAddress', ''),
                'user_agent': event.get('UserAgent', ''),
                'event_name': event['EventName'],
                'aws_region': event.get('AwsRegion', ''),
                'resources': len(event.get('Resources', []))
            })
        
        return events
    
    def _extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract features for anomaly detection"""
        
        # Time-based features
        df['hour'] = pd.to_datetime(df['event_time']).dt.hour
        df['day_of_week'] = pd.to_datetime(df['event_time']).dt.dayofweek
        
        # IP-based features
        df['ip_frequency'] = df.groupby('source_ip')['source_ip'].transform('count')
        df['is_internal_ip'] = df['source_ip'].str.startswith(('10.', '172.', '192.168.'))
        
        # User behavior features
        df['user_frequency'] = df.groupby('user_name')['user_name'].transform('count')
        df['unique_regions'] = df.groupby('user_name')['aws_region'].transform('nunique')
        
        features = df[[
            'hour', 'day_of_week', 'ip_frequency', 'is_internal_ip',
            'user_frequency', 'unique_regions', 'resources'
        ]].fillna(0)
        
        return features.values
    
    def send_alert(self, anomalies: List[Dict], topic_arn: str):
        """Send SNS alert for detected anomalies"""
        
        if not anomalies:
            return
        
        message = f"""
        IAM Access Anomalies Detected: {len(anomalies)} suspicious events
        
        Top Anomalies:
        """
        
        for anomaly in anomalies[:5]:
            message += f"""
        - User: {anomaly['user_name']}
        - IP: {anomaly['source_ip']}
        - Time: {anomaly['event_time']}
        - Score: {anomaly.get('anomaly_score', 'N/A')}
        """
        
        self.sns.publish(
            TopicArn=topic_arn,
            Subject="IAM Access Anomaly Alert",
            Message=message
        )
