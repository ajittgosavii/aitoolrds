"""
Utility functions for AI Database Migration Studio
"""
import pandas as pd
import json
import io
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amounts with proper formatting"""
    if currency == "USD":
        return f"${amount:,.2f}"
    return f"{amount:,.2f} {currency}"

def format_large_number(num: float, suffix: str = "") -> str:
    """Format large numbers with K, M, B suffixes"""
    if num >= 1e9:
        return f"{num/1e9:.1f}B{suffix}"
    elif num >= 1e6:
        return f"{num/1e6:.1f}M{suffix}"
    elif num >= 1e3:
        return f"{num/1e3:.1f}K{suffix}"
    else:
        return f"{num:.1f}{suffix}"

def calculate_roi(annual_savings: float, annual_cost: float) -> float:
    """Calculate Return on Investment percentage"""
    if annual_cost == 0:
        return 0
    return (annual_savings / annual_cost) * 100

def calculate_payback_period(total_investment: float, monthly_savings: float) -> float:
    """Calculate payback period in months"""
    if monthly_savings <= 0:
        return float('inf')
    return total_investment / monthly_savings

def generate_recommendation_score(
    cpu_efficiency: float, 
    ram_efficiency: float, 
    cost_efficiency: float,
    performance_score: float = 1.0
) -> int:
    """Generate recommendation score (0-100) based on multiple factors"""
    weights = {
        'cpu': 0.3,
        'ram': 0.25, 
        'cost': 0.3,
        'performance': 0.15
    }
    
    score = (
        cpu_efficiency * weights['cpu'] + 
        ram_efficiency * weights['ram'] + 
        cost_efficiency * weights['cost'] +
        performance_score * weights['performance']
    ) * 100
    
    return min(100, max(0, int(score)))

def validate_inputs(inputs: Dict) -> List[str]:
    """Validate user inputs and return list of errors"""
    errors = []
    
    # Required fields validation
    required_fields = {
        'cores': 'CPU Cores',
        'ram': 'RAM (GB)',
        'storage': 'Storage (GB)',
        'cpu_util': 'CPU Utilization',
        'ram_util': 'RAM Utilization'
    }
    
    for field, display_name in required_fields.items():
        if field not in inputs:
            errors.append(f"{display_name} is required")
        elif inputs[field] <= 0:
            errors.append(f"{display_name} must be greater than 0")
    
    # Range validations
    if inputs.get('cpu_util', 0) > 100:
        errors.append("CPU utilization cannot exceed 100%")
    
    if inputs.get('ram_util', 0) > 100:
        errors.append("RAM utilization cannot exceed 100%")
    
    if inputs.get('growth', 0) < 0:
        errors.append("Growth rate cannot be negative")
    
    if inputs.get('growth', 0) > 1000:
        errors.append("Growth rate seems unrealistic (>1000%)")
    
    # Logical validations
    if inputs.get('cores', 0) > 1000:
        errors.append("CPU cores count seems unrealistic (>1000)")
    
    if inputs.get('ram', 0) > 10000:
        errors.append("RAM amount seems unrealistic (>10TB)")
    
    if inputs.get('storage', 0) > 1000000:
        errors.append("Storage amount seems unrealistic (>1PB)")
    
    return errors

def get_instance_recommendations(vcpus: int, ram: int, engine: str) -> List[Dict[str, str]]:
    """Get instance type recommendations based on requirements"""
    recommendations = []
    
    # T3 instances for light workloads
    if vcpus <= 2 and ram <= 8:
        recommendations.append({
            "type": "db.t3.medium",
            "reason": "Cost-effective for variable workloads with CPU credits",
            "use_case": "Development and testing environments"
        })
    
    # M5 instances for balanced workloads
    if vcpus <= 8 and ram <= 32:
        recommendations.append({
            "type": "db.m5.xlarge", 
            "reason": "Balanced compute and memory for general workloads",
            "use_case": "Production applications with steady performance needs"
        })
    
    # R5 instances for memory-intensive workloads
    if ram >= 16:
        recommendations.append({
            "type": "db.r5.large",
            "reason": "Memory-optimized for demanding applications",
            "use_case": "Analytics and memory-intensive databases"
        })
    
    # Aurora Serverless for variable workloads
    if engine.startswith('aurora'):
        recommendations.append({
            "type": "Aurora Serverless",
            "reason": "Automatic scaling for variable workloads",
            "use_case": "Applications with intermittent or unpredictable usage"
        })
    
    # High-performance instances for large workloads
    if vcpus >= 16 or ram >= 64:
        recommendations.append({
            "type": "db.r5.4xlarge",
            "reason": "High-performance for enterprise workloads",
            "use_case": "Large-scale production databases"
        })
    
    return recommendations

def calculate_storage_costs(
    storage_gb: int, 
    storage_type: str = "gp3", 
    iops: int = 3000,
    throughput_mbps: int = 125
) -> Dict[str, float]:
    """Calculate detailed storage costs"""
    costs = {}
    
    if storage_type == "gp3":
        # GP3 base cost
        costs["base_storage"] = storage_gb * 0.08
        
        # Additional IOPS cost (free up to 3000)
        extra_iops = max(0, iops - 3000)
        costs["additional_iops"] = extra_iops * 0.005
        
        # Additional throughput cost (free up to 125 MB/s)
        extra_throughput = max(0, throughput_mbps - 125)
        costs["additional_throughput"] = extra_throughput * 0.04
        
    elif storage_type == "gp2":
        costs["base_storage"] = storage_gb * 0.10
        costs["additional_iops"] = 0  # Burstable
        costs["additional_throughput"] = 0
        
    elif storage_type == "io1":
        costs["base_storage"] = storage_gb * 0.125
        costs["additional_iops"] = iops * 0.065
        costs["additional_throughput"] = 0
        
    elif storage_type == "io2":
        costs["base_storage"] = storage_gb * 0.125
        costs["additional_iops"] = iops * 0.065
        costs["additional_throughput"] = 0
    
    costs["total"] = sum(costs.values())
    return costs

def generate_migration_timeline(
    complexity: str = "Medium",
    database_size_gb: int = 1000,
    num_databases: int = 1,
    has_custom_apps: bool = True
) -> Dict[str, Any]:
    """Generate realistic migration timeline based on complexity"""
    
    # Base timeline factors
    complexity_multipliers = {
        "Low": 0.7,
        "Medium": 1.0, 
        "High": 1.5,
        "Critical": 2.0
    }
    
    # Base phases in weeks
    base_timeline = {
        "Assessment & Planning": 2,
        "Environment Setup": 1,
        "Schema Migration": 2,
        "Data Migration": 3,
        "Application Testing": 4,
        "Performance Tuning": 2,
        "Go-Live & Support": 1
    }
    
    multiplier = complexity_multipliers.get(complexity, 1.0)
    
    # Adjust for database size (large databases take longer)
    if database_size_gb > 10000:  # >10TB
        multiplier *= 1.5
    elif database_size_gb > 1000:  # >1TB
        multiplier *= 1.2
    
    # Adjust for number of databases
    if num_databases > 5:
        multiplier *= 1.3
    elif num_databases > 1:
        multiplier *= 1.1
    
    # Adjust for custom applications
    if has_custom_apps:
        multiplier *= 1.2
    
    # Calculate adjusted timeline
    adjusted_timeline = {}
    total_weeks = 0
    
    for phase, weeks in base_timeline.items():
        adjusted_weeks = max(1, int(weeks * multiplier))
        adjusted_timeline[phase] = adjusted_weeks
        total_weeks += adjusted_weeks
    
    return {
        "phases": adjusted_timeline,
        "total_weeks": total_weeks,
        "complexity_factor": multiplier,
        "critical_path": ["Schema Migration", "Data Migration", "Application Testing"]
    }

def calculate_risk_score(
    database_size_gb: int,
    complexity: str,
    custom_applications: bool,
    compliance_requirements: List[str],
    downtime_tolerance_hours: float
) -> Dict[str, Any]:
    """Calculate comprehensive risk assessment"""
    
    risk_factors = {}
    
    # Size-based risk
    if database_size_gb > 10000:
        risk_factors["data_size"] = {"score": 8, "description": "Very large database migration"}
    elif database_size_gb > 1000:
        risk_factors["data_size"] = {"score": 5, "description": "Large database migration"}
    else:
        risk_factors["data_size"] = {"score": 2, "description": "Manageable database size"}
    
    # Complexity risk
    complexity_scores = {"Low": 2, "Medium": 5, "High": 7, "Critical": 9}
    risk_factors["complexity"] = {
        "score": complexity_scores.get(complexity, 5),
        "description": f"{complexity} complexity migration"
    }
    
    # Application risk
    if custom_applications:
        risk_factors["applications"] = {
            "score": 6,
            "description": "Custom applications require extensive testing"
        }
    else:
        risk_factors["applications"] = {
            "score": 2,
            "description": "Standard applications with known compatibility"
        }
    
    # Compliance risk
    compliance_score = min(8, len(compliance_requirements) * 2)
    risk_factors["compliance"] = {
        "score": compliance_score,
        "description": f"Multiple compliance requirements: {', '.join(compliance_requirements)}"
    }
    
    # Downtime risk
    if downtime_tolerance_hours < 1:
        risk_factors["downtime"] = {"score": 9, "description": "Minimal downtime tolerance"}
    elif downtime_tolerance_hours < 4:
        risk_factors["downtime"] = {"score": 6, "description": "Low downtime tolerance"}
    else:
        risk_factors["downtime"] = {"score": 3, "description": "Acceptable downtime window"}
    
    # Calculate overall risk
    total_score = sum(factor["score"] for factor in risk_factors.values())
    max_possible = len(risk_factors) * 10
    risk_percentage = (total_score / max_possible) * 100
    
    if risk_percentage < 30:
        risk_level = "Low"
        risk_color = "green"
    elif risk_percentage < 60:
        risk_level = "Medium" 
        risk_color = "orange"
    else:
        risk_level = "High"
        risk_color = "red"
    
    return {
        "overall_risk": risk_level,
        "risk_percentage": risk_percentage,
        "risk_color": risk_color,
        "risk_factors": risk_factors,
        "mitigation_recommendations": generate_risk_mitigations(risk_factors)
    }

def generate_risk_mitigations(risk_factors: Dict) -> List[str]:
    """Generate risk mitigation strategies based on identified risks"""
    mitigations = []
    
    for factor_name, factor_data in risk_factors.items():
        score = factor_data["score"]
        
        if factor_name == "data_size" and score >= 5:
            mitigations.append("Implement incremental data migration with minimal downtime")
            mitigations.append("Use AWS DMS for large-scale data replication")
        
        if factor_name == "complexity" and score >= 6:
            mitigations.append("Engage AWS Professional Services for complex migrations")
            mitigations.append("Conduct thorough proof-of-concept testing")
        
        if factor_name == "applications" and score >= 5:
            mitigations.append("Implement comprehensive application testing framework")
            mitigations.append("Plan for application code modifications and optimization")
        
        if factor_name == "compliance" and score >= 4:
            mitigations.append("Establish compliance validation checkpoints")
            mitigations.append("Implement automated compliance monitoring")
        
        if factor_name == "downtime" and score >= 6:
            mitigations.append("Design zero-downtime migration strategy")
            mitigations.append("Implement blue-green deployment approach")
    
    # Add general mitigations
    mitigations.extend([
        "Establish comprehensive rollback procedures",
        "Implement real-time monitoring and alerting",
        "Plan for gradual traffic migration",
        "Conduct load testing before go-live"
    ])
    
    return list(set(mitigations))  # Remove duplicates

def export_to_json(data: Dict, filename: str = None) -> str:
    """Export data to JSON string or file"""
    json_str = json.dumps(data, indent=2, default=str)
    
    if filename:
        with open(filename, 'w') as f:
            f.write(json_str)
        return f"Data exported to {filename}"
    else:
        return json_str

def export_to_csv(data: List[Dict], filename: str = None) -> str:
    """Export data to CSV string or file"""
    df = pd.DataFrame(data)
    
    if filename:
        df.to_csv(filename, index=False)
        return f"Data exported to {filename}"
    else:
        return df.to_csv(index=False)

def create_download_link(data: str, filename: str, mime_type: str = "text/plain") -> str:
    """Create a download link for data"""
    b64_data = base64.b64encode(data.encode()).decode()
    return f'<a href="data:{mime_type};base64,{b64_data}" download="{filename}">Download {filename}</a>'

def format_bytes(bytes_value: int) -> str:
    """Format bytes into human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} EB"

def calculate_network_transfer_time(
    data_size_gb: int, 
    bandwidth_mbps: int = 1000,
    efficiency_factor: float = 0.8
) -> Dict[str, float]:
    """Calculate estimated data transfer time"""
    
    # Convert GB to Mb (Gigabytes to Megabits)
    data_size_mb = data_size_gb * 8 * 1024
    
    # Calculate transfer time with efficiency factor
    theoretical_time_hours = data_size_mb / (bandwidth_mbps * 60)
    actual_time_hours = theoretical_time_hours / efficiency_factor
    
    return {
        "theoretical_hours": theoretical_time_hours,
        "estimated_hours": actual_time_hours,
        "estimated_days": actual_time_hours / 24,
        "bandwidth_mbps": bandwidth_mbps,
        "efficiency_factor": efficiency_factor
    }

def generate_cost_breakdown_chart_data(cost_breakdown: Dict[str, float]) -> Dict:
    """Generate data for cost breakdown charts"""
    
    # Filter out zero costs
    filtered_costs = {k: v for k, v in cost_breakdown.items() if v > 0}
    
    return {
        "labels": list(filtered_costs.keys()),
        "values": list(filtered_costs.values()),
        "colors": [
            "#6366F1", "#8B5CF6", "#10B981", "#F59E0B", 
            "#EF4444", "#06B6D4", "#84CC16", "#F97316"
        ][:len(filtered_costs)]
    }

def validate_api_key(api_key: str) -> bool:
    """Validate Claude API key format"""
    if not api_key:
        return False
    
    # Claude API keys start with 'sk-ant-'
    if not api_key.startswith('sk-ant-'):
        return False
    
    # Basic length check
    if len(api_key) < 20:
        return False
    
    return True

def get_optimization_recommendations(
    current_config: Dict,
    recommended_config: Dict,
    cost_analysis: Dict
) -> List[Dict[str, str]]:
    """Generate optimization recommendations based on analysis"""
    
    recommendations = []
    
    # Instance optimization
    if recommended_config.get('vcpus', 0) < current_config.get('cores', 0):
        savings = (current_config['cores'] - recommended_config['vcpus']) * 50  # Rough estimate
        recommendations.append({
            "category": "Compute Optimization",
            "recommendation": f"Right-size from {current_config['cores']} to {recommended_config['vcpus']} vCPUs",
            "impact": f"Save ~${savings}/month",
            "effort": "Low"
        })
    
    # Storage optimization
    if cost_analysis.get('storage_type') == 'gp2':
        recommendations.append({
            "category": "Storage Optimization", 
            "recommendation": "Migrate to GP3 storage for better price/performance",
            "impact": "20% storage cost reduction",
            "effort": "Low"
        })
    
    # Reserved Instance recommendation
    recommendations.append({
        "category": "Cost Optimization",
        "recommendation": "Consider 1-year Reserved Instances for stable workloads",
        "impact": "30-40% cost reduction",
        "effort": "Low"
    })
    
    # Auto Scaling recommendation
    recommendations.append({
        "category": "Performance Optimization",
        "recommendation": "Implement auto-scaling for read replicas",
        "impact": "Better performance during peak loads",
        "effort": "Medium"
    })
    
    return recommendations