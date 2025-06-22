#!/usr/bin/env python3

# Health monitoring and alerting script for the trading platform
# Can be run as a standalone script or integrated into monitoring systems

import requests
import time
import json
import logging
import sys
from datetime import datetime
from typing import Dict, List, Any
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class HealthMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.services = config.get('services', {})
        self.thresholds = config.get('thresholds', {})
        self.alerts = config.get('alerts', {})
        
    def check_service_health(self, service_name: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
        # Check health of a specific service
        try:
            url = service_config['health_url']
            timeout = service_config.get('timeout', 10)
            
            start_time = time.time()
            response = requests.get(url, timeout=timeout)
            response_time = (time.time() - start_time) * 1000
            
            health_data = {
                'service': service_name,
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time_ms': round(response_time, 2),
                'status_code': response.status_code,
                'timestamp': datetime.now().isoformat()
            }
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    health_data['details'] = response_data
                    
                    # Check response time threshold
                    max_response_time = self.thresholds.get('max_response_time_ms', 5000)
                    if response_time > max_response_time:
                        health_data['status'] = 'degraded'
                        health_data['warning'] = f'Response time {response_time:.2f}ms exceeds threshold {max_response_time}ms'
                        
                except json.JSONDecodeError:
                    health_data['warning'] = 'Invalid JSON response'
                    health_data['status'] = 'degraded'
            else:
                health_data['error'] = f'HTTP {response.status_code}: {response.text[:200]}'
                
            return health_data
            
        except requests.exceptions.Timeout:
            return {
                'service': service_name,
                'status': 'unhealthy',
                'error': 'Request timeout',
                'timestamp': datetime.now().isoformat()
            }
        except requests.exceptions.ConnectionError:
            return {
                'service': service_name,
                'status': 'unhealthy',
                'error': 'Connection error - service may be down',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'service': service_name,
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def check_docker_health(self) -> Dict[str, Any]:
        # Check Docker container health status
        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                containers = []
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            containers.append({
                                'name': parts[0],
                                'status': parts[1],
                                'ports': parts[2] if len(parts) > 2 else ''
                            })
                
                return {
                    'status': 'healthy',
                    'containers': containers,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': result.stderr,
                    'timestamp': datetime.now().isoformat()
                }
                
        except subprocess.TimeoutExpired:
            return {
                'status': 'unhealthy',
                'error': 'Docker command timeout',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def send_alert(self, message: str, severity: str = 'warning'):
        # Send alert notification
        timestamp = datetime.now().isoformat()
        alert_data = {
            'timestamp': timestamp,
            'severity': severity,
            'message': message,
            'service': 'trading-platform-monitor'
        }
        
        logger.warning(f"ALERT [{severity.upper()}]: {message}")
        
        # Write to alerts file
        alerts_file = self.alerts.get('log_file', '/var/log/trading-platform-alerts.log')
        try:
            with open(alerts_file, 'a') as f:
                f.write(json.dumps(alert_data) + '\n')
        except Exception as e:
            logger.error(f"Failed to write alert to file: {e}")
        
        # Send webhook if configured
        webhook_url = self.alerts.get('webhook_url')
        if webhook_url:
            try:
                requests.post(webhook_url, json=alert_data, timeout=5)
                logger.info(f"Alert sent to webhook: {webhook_url}")
            except Exception as e:
                logger.error(f"Failed to send webhook alert: {e}")
    
    def run_health_check(self) -> Dict[str, Any]:
        # Run complete health check cycle
        logger.info("Starting health check cycle")
        
        overall_health = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'services': {},
            'docker': {},
            'issues': []
        }
        
        # Check each service
        for service_name, service_config in self.services.items():
            health = self.check_service_health(service_name, service_config)
            overall_health['services'][service_name] = health
            
            if health['status'] != 'healthy':
                overall_health['overall_status'] = 'degraded'
                issue = f"{service_name}: {health.get('error', health.get('warning', 'Unknown issue'))}"
                overall_health['issues'].append(issue)
                
                # Send alert for unhealthy services
                if health['status'] == 'unhealthy':
                    self.send_alert(f"Service {service_name} is unhealthy: {health.get('error', 'Unknown error')}", 'critical')
        
        # Check Docker containers
        docker_health = self.check_docker_health()
        overall_health['docker'] = docker_health
        
        if docker_health['status'] != 'healthy':
            overall_health['overall_status'] = 'degraded'
            overall_health['issues'].append(f"Docker: {docker_health.get('error', 'Unknown issue')}")
            self.send_alert(f"Docker health check failed: {docker_health.get('error', 'Unknown error')}", 'critical')
        
        logger.info(f"Health check completed - Overall status: {overall_health['overall_status']}")
        
        if overall_health['issues']:
            logger.warning(f"Issues found: {', '.join(overall_health['issues'])}")
        
        return overall_health
    
    def monitor_loop(self, interval_seconds: int = 60):
        # Run continuous monitoring loop
        logger.info(f"Starting health monitor loop with {interval_seconds}s interval")
        
        while True:
            try:
                self.run_health_check()
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                logger.info("Health monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(interval_seconds)

def main():
    # Main function for standalone execution
    config = {
        'services': {
            'trading-api': {
                'health_url': 'http://localhost:8000/health',
                'timeout': 10
            },
            'trading-ui': {
                'health_url': 'http://localhost:3000',
                'timeout': 10
            }
        },
        'thresholds': {
            'max_response_time_ms': 5000
        },
        'alerts': {
            'log_file': '/var/log/trading-platform-alerts.log',
            'webhook_url': None
        }
    }
    
    monitor = HealthMonitor(config)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        monitor.monitor_loop()
    else:
        # Single health check
        result = monitor.run_health_check()
        print(json.dumps(result, indent=2))
        
        # Exit with error code if unhealthy
        if result['overall_status'] != 'healthy':
            sys.exit(1)

if __name__ == '__main__':
    main()