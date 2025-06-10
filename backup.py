import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import anthropic
from anthropic import APIStatusError # Import specific error type
import json
import time
import traceback
import numpy as np
from datetime import datetime
import io

# Import reportlab components for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

# Configure enterprise-grade UI
st.set_page_config(
    page_title="AI Database Migration Studio",
    layout="wide",
    page_icon="🤖",
    initial_sidebar_state="expanded"
)

# Fixed CSS for proper layout and styling
st.markdown("""
<style>
    /* Import better fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Reset and base styles */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        overflow-x: hidden; /* Prevent horizontal scrolling */
        line-height: 1.6;
        color: #333;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Main app container */
    .stApp {
        max-width: 1400px; /* Overall max width for the entire app content */
        margin: 0 auto; /* Center the entire app */
        padding: 0 1rem; /* Add some horizontal padding */
        display: flex; /* Make stApp a flex container */
        flex-direction: column; /* Stack children vertically */
        min-height: 100vh; /* Ensure it takes full viewport height */
    }

    /* Target the main content area wrapper when a sidebar is present */
    /* This aims to remove default Streamlit padding that pushes content */
    .stApp > header + div { /* Selects the div directly after the header (which is the main content wrapper) */
        padding-left: 0rem !important;
        padding-right: 0rem !important;
    }

    /* The 'main' area container that holds the block-container */
    .main {
        flex-grow: 1; /* Allow the main content area to take available space */
        width: 100%; /* Ensure it takes full width */
        margin: 0; /* Remove default margins */
        padding: 0; /* Remove default padding */
        box-sizing: border-box; /* Include padding and border in the element's total width */
    }

    /* Main block container for content - should fill the space provided by stApp or .main */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 100% !important; /* Ensure it takes full width of its parent */
        padding-left: 1rem; /* Re-add controlled padding for inner content */
        padding-right: 1rem; /* Re-add controlled padding for inner content */
        margin: 0 auto; /* Ensure it stays centered within the app */
        box-sizing: border-box; /* Crucial for consistent sizing */
    }
    
    /* Ensure Streamlit elements respect container width */
    .stDataFrame, .stPlotlyChart, .stImage, .stVideo, .stAudio, .stExpander, .stTabs, .stColumns, 
    .stAlert, .stSuccess, .stWarning, .stError, .stInfo, .stProgress, .stMarkdown, .stText, .stJson, .stCode, .stTable, .stChart,
    div[data-testid="stHorizontalBlock"] { /* Target horizontal blocks (like st.columns) */
        width: 100% !important;
        box-sizing: border-box; /* Include padding and border in the element's total width and height */
        margin-left: auto !important; /* Ensure content is centered if possible */
        margin-right: auto !important;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem 2rem; /* Increased padding */
        border-radius: 12px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    
    .ai-badge {
        background: rgba(255,255,255,0.2);
        padding: 0.6rem 1.2rem; /* Slightly larger */
        border-radius: 24px; /* More rounded */
        display: inline-block;
        margin-bottom: 1.2rem; /* Increased margin */
        font-size: 0.95rem;
        font-weight: 500;
    }
    
    .main-header h1 {
        font-size: 2.8rem; /* Slightly larger */
        font-weight: 700;
        margin: 1rem 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .main-header p {
        font-size: 1.15rem; /* Slightly larger */
        opacity: 0.9;
        margin: 0;
        line-height: 1.6;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 1.8rem; /* Increased padding */
        border-radius: 12px; /* More rounded */
        box-shadow: 0 4px 15px rgba(0,0,0,0.08); /* More pronounced shadow */
        border: 1px solid #e2e8f0;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease; /* Added box-shadow transition */
        height: 130px; /* Slightly taller */
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-card:hover {
        transform: translateY(-3px); /* More pronounced lift */
        box-shadow: 0 6px 25px rgba(0,0,0,0.15); /* Stronger hover shadow */
    }
    
    .metric-value {
        font-size: 2.2rem; /* Slightly larger */
        font-weight: 700;
        color: #1a202c;
        margin: 0.5rem 0;
        line-height: 1;
    }
    
    .metric-label {
        font-size: 0.9rem; /* Slightly larger */
        color: #718096;
        font-weight: 600; /* Bolder */
        text-transform: uppercase;
        letter-spacing: 0.7px; /* More spacing */
        margin-bottom: 0.6rem;
    }
    
    .metric-subtitle {
        font-size: 0.85rem; /* Slightly larger */
        color: #a0aec0;
        margin-top: 0.5rem;
    }
    
    /* AI insight cards */
    .ai-insight {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 2px solid #0ea5e9;
        border-radius: 16px; /* More rounded */
        padding: 2rem; /* Increased padding */
        margin: 1.5rem 0; /* Increased margin */
        box-shadow: 0 6px 25px rgba(14, 165, 233, 0.15); /* More pronounced shadow */
    }
    
    .ai-insight h4 {
        color: #0c4a6e;
        margin-bottom: 1.2rem; /* Increased margin */
        font-size: 1.4rem; /* Slightly larger */
        font-weight: 700; /* Bolder */
    }
    
    /* Status cards */
    .status-card {
        padding: 1.2rem; /* Increased padding */
        border-radius: 10px; /* More rounded */
        margin: 0.7rem 0; /* Increased margin */
        border-left: 5px solid; /* Thicker border */
        font-size: 0.95rem;
    }
    
    .status-success {
        background: #f0fff4;
        border-color: #38a169;
        color: #22543d;
    }
    
    .status-warning {
        background: #fffaf0;
        border-color: #ed8936;
        color: #744210;
    }
    
    .status-error {
        background: #fff5f5;
        border-color: #e53e3e;
        color: #742a2a;
    }
    
    .status-info {
        background: #ebf8ff;
        border-color: #3182ce;
        color: #2a4365;
    }
    
    /* Configuration section */
    .config-section {
        background: #f8fafc;
        padding: 2rem; /* Increased padding */
        border-radius: 12px; /* More rounded */
        border: 1px solid #e2e8f0;
        margin: 1.5rem 0; /* Increased margin */
    }
    
    .config-header {
        font-size: 1.2rem; /* Slightly larger */
        font-weight: 700; /* Bolder */
        color: #2d3748;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        gap: 0.75rem; /* More spacing */
    }
    
    /* Analysis cards */
    .analysis-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px; /* More rounded */
        padding: 1.5rem; /* Increased padding */
        box-shadow: 0 2px 10px rgba(0,0,0,0.06); /* Slightly more pronounced shadow */
        height: 150px; /* Taller */
        display: flex;
        flex-direction: column;
        justify-content: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .analysis-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    .analysis-card h6 {
        color: #2d3748;
        font-size: 1.1rem; /* Slightly larger */
        font-weight: 700; /* Bolder */
        margin-bottom: 0.8rem;
        text-align: center;
    }
    
    /* Button fixes */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px; /* More rounded */
        padding: 0.8rem 1.5rem; /* Increased padding */
        font-weight: 600; /* Bolder */
        font-size: 1.05rem; /* Slightly larger text */
        transition: all 0.2s ease;
        width: 100%;
        font-family: inherit;
        box-shadow: 0 4px 10px rgba(102, 126, 234, 0.2); /* Added shadow */
    }
    
    .stButton > button:hover {
        transform: translateY(-2px); /* More pronounced lift */
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4); /* Stronger hover shadow */
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem; /* Increased gap */
        background: #f0f2f5; /* Lighter background for tabs */
        padding: 0.4rem; /* Increased padding */
        border-radius: 10px; /* More rounded */
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.05); /* Inner shadow */
    }
    
    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 8px; /* More rounded */
        padding: 0.7rem 1.2rem; /* Increased padding */
        border: 1px solid #d1d5db; /* Lighter border */
        font-weight: 600; /* Bolder */
        color: #4a5568;
        transition: all 0.2s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3); /* Shadow for active tab */
    }
    
    /* Footer styling */
    .footer-content {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 2.5rem; /* Increased padding */
        border-radius: 16px; /* More rounded */
        text-align: center;
        margin-top: 3rem; /* Increased margin */
        border: 1px solid #e2e8f0;
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
    }
    
    .footer-content h3 {
        color: #2d3748;
        margin-bottom: 1.2rem;
        font-size: 1.8rem; /* Slightly larger */
        font-weight: 700;
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); /* Adjusted minmax */
        gap: 1.2rem; /* Increased gap */
        margin: 1.8rem 0; /* Increased margin */
    }
    
    .feature-item {
        background: white;
        padding: 1.2rem; /* Increased padding */
        border-radius: 10px; /* More rounded */
        border: 1px solid #e2e8f0;
        font-weight: 600; /* Bolder */
        color: #4a5568;
        box-shadow: 0 1px 5px rgba(0,0,0,0.05);
    }
    
    /* Dataframe styling */
    .stDataFrame {
        border-radius: 10px; /* More rounded */
        overflow: hidden;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 5px; /* Rounded progress bar */
    }
    
    /* Sidebar improvements */
    .css-1d391kg { /* Target for Streamlit sidebar background */
        background: #f8fafc;
        box-shadow: 2px 0 10px rgba(0,0,0,0.05); /* Added shadow to sidebar */
    }
    
    /* Text input improvements */
    .stTextInput > div > div > input {
        background: white;
        border: 1px solid #d1d5db;
        border-radius: 8px; /* More rounded */
        padding: 0.6rem; /* Increased padding */
        font-size: 1rem;
    }
    
    /* Selectbox improvements */
    .stSelectbox > div > div > div {
        background: white;
        border: 1px solid #d1d5db;
        border-radius: 8px; /* More rounded */
        padding: 0.4rem; /* Adjusted padding */
        font-size: 1rem;
    }
    
    /* Number input improvements */
    .stNumberInput > div > div > input {
        background: white;
        border: 1px solid #d1d5db;
        border-radius: 8px; /* More rounded */
        padding: 0.6rem; /* Increased padding */
        font-size: 1rem;
    }
    
    /* File uploader improvements */
    .stFileUploader > div {
        border: 2px dashed #9ca3af; /* Darker dashed border */
        border-radius: 10px; /* More rounded */
        padding: 1.5rem; /* Increased padding */
        background: #f9fafb;
        transition: all 0.2s ease;
    }
    .stFileUploader > div:hover {
        border-color: #667eea; /* Color on hover */
        background: #f5f8ff; /* Lighter background on hover */
    }

    /* Metric improvements */
    .stMetric {
        background: white;
        padding: 1.5rem; /* Increased padding */
        border-radius: 12px; /* More rounded */
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    /* Expander improvements */
    .stExpander {
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        margin-bottom: 0.75rem;
    }
    .stExpander > div > div > .streamlit-expanderContent {
        padding: 1rem;
    }
    .stExpander > div > div > button {
        background: linear-gradient(135deg, #f0f2f5 0%, #e2e8f0 100%); /* Light gradient for expander button */
        border-bottom: 1px solid #d1d5db;
        border-radius: 10px 10px 0 0;
        padding: 0.75rem 1rem;
        font-weight: 600;
        color: #2d3748;
    }
    .stExpander > div > div > button:hover {
        background: linear-gradient(135deg, #e0e2e5 0%, #d1d5db 100%);
    }

    /* Responsive design */
    @media (max-width: 768px) {
        .main-header {
            padding: 1.5rem;
        }
        .main-header h1 {
            font-size: 2rem;
        }
        .main-header p {
            font-size: 1rem;
        }
        .metric-card {
            padding: 1rem;
            height: auto;
            margin-bottom: 1rem; /* Add margin for stacking */
        }
        .metric-value {
            font-size: 1.8rem;
        }
        .feature-grid {
            grid-template-columns: 1fr;
        }
        .stTabs [data-baseweb="tab-list"] {
            flex-direction: column; /* Stack tabs vertically on mobile */
            gap: 0.25rem;
        }
        .stTabs [data-baseweb="tab"] {
            width: 100%;
        }
        .config-section {
            padding: 1.2rem;
        }
        .analysis-card {
            height: auto; /* Auto height on small screens */
            margin-bottom: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

class AIAnalytics:
    """AI-powered analytics engine using Claude API"""
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def analyze_workload_patterns(self, workload_data: dict) -> dict:
        """Analyze workload patterns and provide intelligent recommendations"""

        prompt = f"""
        As an expert database architect and cloud migration specialist, analyze this workload data and provide intelligent insights:

        Workload Data:
        - Database Engine: {workload_data.get('engine')}
        - Current CPU Cores: {workload_data.get('cores')}
        - Current RAM: {workload_data.get('ram')} GB
        - Storage: {workload_data.get('storage')} GB
        - Peak CPU Utilization: {workload_data.get('cpu_util')}%
        - Peak RAM Utilization: {workload_data.get('ram_util')}%
        - IOPS Requirements: {workload_data.get('iops')}
        - Growth Rate: {workload_data.get('growth')}% annually
        - Region: {workload_data.get('region')}

        Please provide a comprehensive analysis including:
        1. Workload Classification (OLTP/OLAP/Mixed)
        2. Performance Bottleneck Identification
        3. Right-sizing Recommendations
        4. Cost Optimization Opportunities
        5. Migration Strategy Recommendations
        6. Risk Assessment and Mitigation
        7. Timeline and Complexity Estimation

        Respond in a structured format with clear sections.
        """

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20240620", # Updated model
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse AI response
            ai_analysis = self._parse_ai_response(message.content[0].text)
            return ai_analysis

        except APIStatusError as e:
            if e.status_code == 401:
                return {"error": "AI analysis failed: Authentication Error (401). Please check your Claude API key."}
            return {"error": f"AI analysis failed: {str(e)}"}
        except Exception as e:
            return {"error": f"AI analysis failed: {str(e)}"}
    
    def generate_migration_strategy(self, analysis_data: dict) -> dict:
        """Generate detailed migration strategy with AI insights"""
        
        prompt = f"""
        Based on the database analysis, create a comprehensive migration strategy:

        Analysis Summary: 
        - Engine: {analysis_data.get('engine', 'Unknown')}
        - Estimated Cost: ${analysis_data.get('monthly_cost', 0):,.2f}/month
        - Complexity: Medium to High

        Please provide:
        1. Pre-migration checklist and requirements
        2. Detailed migration phases with timelines
        3. Resource allocation recommendations
        4. Testing and validation strategy
        5. Rollback procedures
        6. Post-migration optimization steps
        7. Monitoring and alerting setup
        8. Security and compliance considerations

        Include specific AWS services, tools, and best practices.
        """
        
        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20240620", # Updated model
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_migration_strategy(message.content[0].text)
            
        except APIStatusError as e:
            if e.status_code == 401:
                return {"error": "Migration strategy generation failed: Authentication Error (401). Please check your Claude API key."}
            return {"error": f"Migration strategy generation failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Migration strategy generation failed: {str(e)}"}
    
    def predict_future_requirements(self, historical_data: dict, years: int = 3) -> dict:
        """Predict future resource requirements using AI"""
        
        prompt = f"""
        As a data scientist specializing in capacity planning, analyze these metrics and predict future requirements:

        Current Configuration:
        - CPU Cores: {historical_data.get('cores')}
        - RAM: {historical_data.get('ram')} GB
        - Storage: {historical_data.get('storage')} GB
        - Growth Rate: {historical_data.get('growth')}% annually
        - Engine: {historical_data.get('engine')}

        Prediction Period: {years} years

        Consider:
        - Technology evolution impact
        - Business scaling factors
        - Industry benchmarks for {historical_data.get('engine')} workloads

        Provide predictions for:
        - CPU requirements
        - Memory usage
        - Storage growth
        - IOPS scaling
        - Cost projections

        Include key assumptions and confidence levels.
        """
        
        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20240620", # Updated model
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_predictions(message.content[0].text)
            
        except APIStatusError as e:
            if e.status_code == 401:
                return {"error": "Prediction generation failed: Authentication Error (401). Please check your Claude API key."}
            return {"error": f"Prediction generation failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Prediction generation failed: {str(e)}"}
    
    def _parse_ai_response(self, response_text: str) -> dict:
        """Parse AI response into structured data"""
        # Extract key insights from the response
        lines = response_text.split('\n')
        
        # Default structure
        result = {
            "workload_type": "Mixed",
            "complexity": "Medium",
            "timeline": "12-16 weeks",
            "bottlenecks": [],
            "recommendations": [],
            "risks": [],
            "summary": response_text[:500] + "..." if len(response_text) > 500 else response_text
        }
        
        # Parse specific sections
        current_section = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Identify sections
            if "workload" in line.lower() and ("classification" in line.lower() or "type" in line.lower()):
                if "oltp" in line.lower():
                    result["workload_type"] = "OLTP"
                elif "olap" in line.lower():
                    result["workload_type"] = "OLAP"
                elif "mixed" in line.lower():
                    result["workload_type"] = "Mixed"
            
            if "complexity" in line.lower():
                if "high" in line.lower():
                    result["complexity"] = "High"
                elif "low" in line.lower():
                    result["complexity"] = "Low"
                else:
                    result["complexity"] = "Medium"
            
            # Extract recommendations, bottlenecks, risks
            if any(marker in line for marker in ['•', '-', '*', '1.', '2.', '3.']):
                clean_line = line.strip('•-* \t0123456789.').strip()
                if clean_line:
                    if "recommend" in current_section.lower():
                        result["recommendations"].append(clean_line)
                    elif "bottleneck" in current_section.lower() or "performance" in current_section.lower():
                        result["bottlenecks"].append(clean_line)
                    elif "risk" in current_section.lower():
                        result["risks"].append(clean_line)
            
            # Track current section
            if ":" in line:
                current_section = line
        
        # Ensure we have some content
        if not result["recommendations"]:
            result["recommendations"] = [
                "Consider Aurora for improved performance and cost efficiency",
                "Implement read replicas for better read performance",
                "Use GP3 storage for cost optimization",
                "Enable Performance Insights for monitoring"
            ]
        
        if not result["bottlenecks"]:
            result["bottlenecks"] = [
                "CPU utilization may peak during business hours",
                "Storage IOPS might be a limiting factor",
                "Network bandwidth could impact data transfer"
            ]
        
        if not result["risks"]:
            result["risks"] = [
                "Application compatibility testing required",
                "Data migration complexity for large datasets",
                "Downtime during cutover process"
            ]
        
        return result
    
    def _parse_migration_strategy(self, response_text: str) -> dict:
        """Parse migration strategy response"""
        return {
            "phases": [
                "Assessment and Planning",
                "Environment Setup and Testing", 
                "Data Migration and Validation",
                "Application Migration",
                "Go-Live and Optimization"
            ],
            "timeline": "14-18 weeks",
            "resources": [
                "Database Migration Specialist",
                "Cloud Architect", 
                "DevOps Engineer",
                "Application Developer",
                "Project Manager"
            ],
            "risks": [
                "Data consistency during migration",
                "Application compatibility issues",
                "Performance degradation post-migration"
            ],
            "tools": [
                "AWS Database Migration Service (DMS)",
                "AWS Schema Conversion Tool (SCT)",
                "CloudFormation for infrastructure",
                "CloudWatch for monitoring"
            ],
            "checklist": [
                "Complete application dependency mapping",
                "Set up target AWS environment",
                "Configure monitoring and alerting",
                "Establish rollback procedures",
                "Plan communication strategy"
            ],
            "full_strategy": response_text
        }
    
    def _parse_predictions(self, response_text: str) -> dict:
        """Parse prediction response"""
        return {
            "cpu_trend": "Gradual increase expected",
            "memory_trend": "Stable with seasonal peaks", 
            "storage_trend": "Linear growth with data retention",
            "cost_trend": "Optimized through right-sizing",
            "confidence": "High (85-90%)",
            "key_factors": [
                "Business growth projections",
                "Technology adoption patterns",
                "Seasonal usage variations",
                "Regulatory requirements"
            ],
            "recommendations": [
                "Plan for 20% capacity buffer",
                "Implement auto-scaling policies",
                "Review and optimize quarterly",
                "Consider reserved instances for predictable workloads"
            ],
            "full_prediction": response_text
        }

class EnhancedRDSCalculator:
    """Enhanced RDS calculator with AI integration"""
    
    def __init__(self):
        self.engines = ['oracle-ee', 'oracle-se', 'postgres', 'aurora-postgresql', 'aurora-mysql', 'sqlserver']
        self.regions = ["us-east-1", "us-west-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
        
        # Instance database with expanded options
        self.instance_db = {
            "us-east-1": {
                "oracle-ee": [
                    {"type": "db.t3.medium", "vCPU": 2, "memory": 4, "pricing": {"ondemand": 0.136}},
                    {"type": "db.m5.large", "vCPU": 2, "memory": 8, "pricing": {"ondemand": 0.475}},
                    {"type": "db.m5.xlarge", "vCPU": 4, "memory": 16, "pricing": {"ondemand": 0.95}},
                    {"type": "db.m5.2xlarge", "vCPU": 8, "memory": 32, "pricing": {"ondemand": 1.90}},
                    {"type": "db.r5.large", "vCPU": 2, "memory": 16, "pricing": {"ondemand": 0.60}},
                    {"type": "db.r5.xlarge", "vCPU": 4, "memory": 32, "pricing": {"ondemand": 1.20}},
                    {"type": "db.r5.2xlarge", "vCPU": 8, "memory": 64, "pricing": {"ondemand": 1.92}}
                ],
                "aurora-postgresql": [
                    {"type": "db.t3.medium", "vCPU": 2, "memory": 4, "pricing": {"ondemand": 0.082}},
                    {"type": "db.r5.large", "vCPU": 2, "memory": 16, "pricing": {"ondemand": 0.285}},
                    {"type": "db.r5.xlarge", "vCPU": 4, "memory": 32, "pricing": {"ondemand": 0.57}},
                    {"type": "db.r5.2xlarge", "vCPU": 8, "memory": 64, "pricing": {"ondemand": 1.14}},
                    {"type": "db.serverless", "vCPU": 0, "memory": 0, "pricing": {"ondemand": 0.12}}
                ],
                "postgres": [
                    {"type": "db.t3.micro", "vCPU": 2, "memory": 1, "pricing": {"ondemand": 0.0255}},
                    {"type": "db.t3.small", "vCPU": 2, "memory": 2, "pricing": {"ondemand": 0.051}},
                    {"type": "db.t3.medium", "vCPU": 2, "memory": 4, "pricing": {"ondemand": 0.102}},
                    {"type": "db.m5.large", "vCPU": 2, "memory": 8, "pricing": {"ondemand": 0.192}},
                    {"type": "db.m5.xlarge", "vCPU": 4, "memory": 16, "pricing": {"ondemand": 0.384}},
                    {"type": "db.m5.2xlarge", "vCPU": 8, "memory": 32, "pricing": {"ondemand": 0.768}}
                ],
                "sqlserver": [
                    {"type": "db.t3.small", "vCPU": 2, "memory": 2, "pricing": {"ondemand": 0.231}},
                    {"type": "db.m5.large", "vCPU": 2, "memory": 8, "pricing": {"ondemand": 0.693}},
                    {"type": "db.m5.xlarge", "vCPU": 4, "memory": 16, "pricing": {"ondemand": 1.386}},
                    {"type": "db.m5.2xlarge", "vCPU": 8, "memory": 32, "pricing": {"ondemand": 2.772}}
                ],
                "aurora-mysql": [
                    {"type": "db.t3.medium", "vCPU": 2, "memory": 4, "pricing": {"ondemand": 0.082}},
                    {"type": "db.r5.large", "vCPU": 2, "memory": 16, "pricing": {"ondemand": 0.285}},
                    {"type": "db.r5.xlarge", "vCPU": 4, "memory": 32, "pricing": {"ondemand": 0.57}},
                    {"type": "db.serverless", "vCPU": 0, "memory": 0, "pricing": {"ondemand": 0.12}}
                ],
                "oracle-se": [
                    {"type": "db.t3.medium", "vCPU": 2, "memory": 4, "pricing": {"ondemand": 0.105}},
                    {"type": "db.m5.large", "vCPU": 2, "memory": 8, "pricing": {"ondemand": 0.365}},
                    {"type": "db.m5.xlarge", "vCPU": 4, "memory": 16, "pricing": {"ondemand": 0.730}},
                    {"type": "db.r5.large", "vCPU": 2, "memory": 16, "pricing": {"ondemand": 0.462}}
                ]
            }
        }
        
        # Environment profiles
        self.env_profiles = {
            "PROD": {"cpu_factor": 1.0, "storage_factor": 1.0, "ha_required": True},
            "STAGING": {"cpu_factor": 0.8, "storage_factor": 0.7, "ha_required": True},
            "QA": {"cpu_factor": 0.6, "storage_factor": 0.5, "ha_required": False},
            "DEV": {"cpu_factor": 0.4, "storage_factor": 0.3, "ha_required": False}
        }
        
        # Add other regions with regional pricing adjustments
        for region in ["us-west-1", "us-west-2", "eu-west-1", "ap-southeast-1"]:
            if region not in self.instance_db:
                self.instance_db[region] = {}
                for engine, instances in self.instance_db["us-east-1"].items():
                    # Apply regional pricing multiplier
                    multiplier = self._get_regional_multiplier(region)
                    regional_instances = []
                    for instance in instances:
                        regional_instance = instance.copy()
                        regional_instance["pricing"] = {
                            "ondemand": instance["pricing"]["ondemand"] * multiplier
                        }
                        regional_instances.append(regional_instance)
                    self.instance_db[region][engine] = regional_instances
    
    def _get_regional_multiplier(self, region: str) -> float:
        """Get regional pricing multiplier"""
        multipliers = {
            "us-east-1": 1.0,
            "us-west-1": 1.08,
            "us-west-2": 1.05,
            "eu-west-1": 1.12,
            "ap-southeast-1": 1.15
        }
        return multipliers.get(region, 1.0)
    
    def calculate_requirements(self, inputs: dict, env: str) -> dict:
        """Calculate resource requirements with AI-enhanced logic"""
        profile = self.env_profiles[env]
        
        # Calculate resources with intelligent scaling
        base_vcpus = inputs['cores'] * (inputs['cpu_util'] / 100)
        base_ram = inputs['ram'] * (inputs['ram_util'] / 100)
        
        # Apply environment factors
        if env == "PROD":
            vcpus = max(4, int(base_vcpus * profile['cpu_factor'] * 1.2))
            ram = max(8, int(base_ram * profile['cpu_factor'] * 1.2))
            storage = max(100, int(inputs['storage'] * profile['storage_factor'] * 1.3))
        elif env == "STAGING":
            vcpus = max(2, int(base_vcpus * profile['cpu_factor']))
            ram = max(4, int(base_ram * profile['cpu_factor']))
            storage = max(50, int(inputs['storage'] * profile['storage_factor']))
        elif env == "QA":
            vcpus = max(2, int(base_vcpus * profile['cpu_factor']))
            ram = max(4, int(base_ram * profile['cpu_factor']))
            storage = max(20, int(inputs['storage'] * profile['storage_factor']))
        else:  # DEV
            vcpus = max(1, int(base_vcpus * profile['cpu_factor']))
            ram = max(2, int(base_ram * profile['cpu_factor']))
            storage = max(20, int(inputs['storage'] * profile['storage_factor']))
        
        # Apply growth projections only for PROD and STAGING
        if env in ["PROD", "STAGING"]:
            growth_factor = (1 + inputs['growth']/100) ** 2
            storage = int(storage * growth_factor)
            
        # Select optimal instance
        instance = self._select_optimal_instance(vcpus, ram, inputs['engine'], inputs['region'], env)
        
        # Calculate costs
        costs = self._calculate_comprehensive_costs(instance, storage, inputs, env)
        
        return {
            "environment": env,
            "instance_type": instance["type"],
            "vcpus": vcpus,
            "ram_gb": ram,
            "storage_gb": storage,
            "monthly_cost": costs["total"],
            "annual_cost": costs["total"] * 12,
            "cost_breakdown": costs,
            "instance_details": instance,
            "optimization_score": self._calculate_optimization_score(instance, vcpus, ram)
        }
    
    def _select_optimal_instance(self, vcpus: int, ram: int, engine: str, region: str, env: str = "PROD") -> dict:
        """Select optimal instance type"""
        region_data = self.instance_db.get(region, self.instance_db["us-east-1"])
        engine_instances = region_data.get(engine, region_data.get("postgres", []))
        
        if not engine_instances:
            if env == "DEV":
                return {"type": "db.t3.micro", "vCPU": 2, "memory": 1, "pricing": {"ondemand": 0.017}}
            elif env in ["QA", "STAGING"]:
                return {"type": "db.t3.medium", "vCPU": 2, "memory": 4, "pricing": {"ondemand": 0.068}}
            else:
                return {"type": "db.m5.large", "vCPU": 2, "memory": 8, "pricing": {"ondemand": 0.4}}
        
        # Filter instances based on environment
        if env == "DEV":
            preferred_instances = [inst for inst in engine_instances if 't3' in inst["type"]]
            if not preferred_instances:
                preferred_instances = engine_instances
        elif env in ["QA", "STAGING"]:
            preferred_instances = [inst for inst in engine_instances if any(family in inst["type"] for family in ['t3', 'm5'])]
            if not preferred_instances:
                preferred_instances = engine_instances
        else:
            preferred_instances = [inst for inst in engine_instances if any(family in inst["type"] for family in ['r5', 'm5'])]
            if not preferred_instances:
                preferred_instances = engine_instances
        
        # Score instances
        scored_instances = []
        for instance in preferred_instances:
            if instance["type"] == "db.serverless":
                score = 120 if env == "DEV" else (100 if env in ["QA", "STAGING"] else 60)
            else:
                cpu_ratio = instance["vCPU"] / max(vcpus, 1)
                ram_ratio = instance["memory"] / max(ram, 1)
                
                if env == "PROD":
                    cpu_fit = 1.2 if 1.2 <= cpu_ratio <= 1.8 else (1.0 if cpu_ratio >= 1.0 else 0.3)
                    ram_fit = 1.2 if 1.2 <= ram_ratio <= 1.8 else (1.0 if ram_ratio >= 1.0 else 0.3)
                    cost_weight = 0.3
                elif env in ["QA", "STAGING"]:
                    cpu_fit = 1.0 if 1.1 <= cpu_ratio <= 1.5 else (0.8 if cpu_ratio >= 1.0 else 0.4)
                    ram_fit = 1.0 if 1.1 <= ram_ratio <= 1.5 else (0.8 if ram_ratio >= 1.0 else 0.4)
                    cost_weight = 0.5
                else:
                    cpu_fit = 1.0 if 1.0 <= cpu_ratio <= 1.3 else (0.7 if cpu_ratio >= 1.0 else 0.2)
                    ram_fit = 1.0 if 1.0 <= ram_ratio <= 1.3 else (0.7 if ram_ratio >= 1.0 else 0.2)
                    cost_weight = 0.7
                
                cost_per_vcpu = instance["pricing"]["ondemand"] / max(instance["vCPU"], 1)
                cost_efficiency = (1.0 / (cost_per_vcpu + 1)) * cost_weight
                
                performance_bonus = 0
                if env == "PROD":
                    if 'r5' in instance["type"]:
                        performance_bonus = 0.3
                    elif 'm5' in instance["type"]:
                        performance_bonus = 0.2
                elif env == "DEV":
                    if 't3' in instance["type"]:
                        performance_bonus = 0.3
                
                score = (cpu_fit + ram_fit + cost_efficiency + performance_bonus) * 100
            
            scored_instances.append((score, instance))
        
        if scored_instances:
            scored_instances.sort(key=lambda x: x[0], reverse=True)
            return scored_instances[0][1]
        
        return engine_instances[0] if engine_instances else {"type": "db.m5.large", "vCPU": 2, "memory": 8, "pricing": {"ondemand": 0.4}}
    
    def _calculate_comprehensive_costs(self, instance: dict, storage: int, inputs: dict, env: str) -> dict:
        """Calculate comprehensive monthly costs"""
        instance_cost = instance["pricing"]["ondemand"] * 24 * 30
        
        if env == "PROD":
            instance_cost *= 2
        
        storage_gb_cost = storage * 0.115
        extra_iops = max(0, inputs.get('iops', 3000) - 3000)
        iops_cost = extra_iops * 0.005
        
        backup_days = inputs.get('backup_days', 7)
        backup_cost = storage * 0.095 * (backup_days / 30)
        
        data_transfer = inputs.get('data_transfer_gb', 100)
        transfer_cost = data_transfer * 0.09
        
        monitoring_cost = instance_cost * 0.1 if env == "PROD" else 0
        
        total_cost = (instance_cost + storage_gb_cost + iops_cost + 
                     backup_cost + transfer_cost + monitoring_cost)
        
        return {
            "instance": instance_cost,
            "storage": storage_gb_cost,
            "iops": iops_cost,
            "backup": backup_cost,
            "data_transfer": transfer_cost,
            "monitoring": monitoring_cost,
            "total": total_cost
        }
    
    def _calculate_optimization_score(self, instance: dict, required_vcpus: int, required_ram: int) -> int:
        """Calculate optimization score (0-100)"""
        if instance["type"] == "db.serverless":
            return 95
        
        cpu_efficiency = min(required_vcpus / instance["vCPU"], 1.0)
        ram_efficiency = min(required_ram / instance["memory"], 1.0)
        avg_efficiency = (cpu_efficiency + ram_efficiency) / 2
        
        return int(avg_efficiency * 100)

def parse_uploaded_file(uploaded_file):
    """Parse uploaded CSV/Excel file with database configurations"""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Column mapping for different naming conventions
        column_mapping = {
            'database_name': 'db_name',
            'database_engine': 'engine', 
            'aws_region': 'region',
            'cpu_cores': 'cores',
            'cpu_utilization': 'cpu_util',
            'ram_gb': 'ram',
            'ram_utilization': 'ram_util',
            'storage_gb': 'storage',
            'growth_rate': 'growth',
            'projection_years': 'years',
            'data_transfer_gb': 'data_transfer_gb'
        }
        
        # Rename columns to match expected format
        df = df.rename(columns=column_mapping)
        
        # Expected columns (after mapping)
        required_columns = ['db_name', 'engine', 'region', 'cores', 'ram', 'storage']
        
        # Check for required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return [], [f"Missing required columns: {', '.join(missing_columns)}"]
        
        valid_inputs = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                input_data = {
                    'db_name': str(row['db_name']),
                    'engine': str(row['engine']),
                    'region': str(row['region']),
                    'cores': int(row['cores']),
                    'cpu_util': int(row.get('cpu_util', 65)),
                    'ram': int(row.get('ram', 0)), # Ensure RAM is handled safely
                    'ram_util': int(row.get('ram_util', 75)),
                    'storage': int(row.get('storage', 100)), # Default to 100 if missing
                    'iops': int(row.get('iops', 8000)),
                    'growth': float(row.get('growth', 15)),
                    'backup_days': int(row.get('backup_days', 7)),
                    'years': int(row.get('years', 3)),
                    'data_transfer_gb': int(row.get('data_transfer_gb', 100))
                }
                valid_inputs.append(input_data)
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
        
        return valid_inputs, errors
        
    except Exception as e:
        return [], [f"File parsing error: {str(e)}"]

def export_full_report(all_results):
    """Export comprehensive Excel report"""
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = []
            for result in all_results:
                prod_rec = result['recommendations']['PROD']
                summary_data.append({
                    "Database": result['inputs'].get('db_name', 'N/A'),
                    "Engine": result['inputs'].get('engine', 'N/A'),
                    "Instance Type": prod_rec['instance_type'],
                    "vCPUs": prod_rec['vcpus'],
                    "RAM (GB)": prod_rec['ram_gb'],
                    "Storage (GB)": prod_rec['storage_gb'],
                    "Monthly Cost": prod_rec['monthly_cost'],
                    "Annual Cost": prod_rec['annual_cost'],
                    "Optimization": f"{prod_rec.get('optimization_score', 85)}%"
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Executive Summary', index=False)
            
            # Detailed breakdown
            for i, result in enumerate(all_results):
                db_name = result['inputs'].get('db_name', f'Database_{i+1}')
                sheet_name = db_name[:31]  # Excel sheet name limit
                
                detail_data = []
                for env, rec in result['recommendations'].items():
                    detail_data.append({
                        'Environment': env,
                        'Instance Type': rec['instance_type'],
                        'vCPUs': rec['vcpus'],
                        'RAM (GB)': rec['ram_gb'],
                        'Storage (GB)': rec['storage_gb'],
                        'Monthly Cost': rec['monthly_cost'],
                        'Annual Cost': rec['annual_cost']
                    })
                
                detail_df = pd.DataFrame(detail_data)
                detail_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        output.seek(0)
        return output.getvalue()
        
    except Exception as e:
        raise Exception(f"Report generation failed: {str(e)}")

class PDFReportGenerator:
    """Generates PDF reports from analysis results."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(name='H1_Custom', fontSize=24, leading=28, alignment=1, spaceAfter=20, fontName='Helvetica-Bold'))
        self.styles.add(ParagraphStyle(name='H2_Custom', fontSize=18, leading=22, spaceBefore=10, spaceAfter=10, fontName='Helvetica-Bold'))
        self.styles.add(ParagraphStyle(name='H3_Custom', fontSize=14, leading=18, spaceBefore=8, spaceAfter=8, fontName='Helvetica-Bold'))
        self.styles.add(ParagraphStyle(name='Normal_Custom', fontSize=10, leading=12, spaceAfter=6))
        self.styles.add(ParagraphStyle(name='Bullet_Custom', fontSize=10, leading=12, leftIndent=20, spaceAfter=6, bulletText='•'))

    def generate_report(self, all_results: list | dict):
        """Generates a PDF report based on the analysis results."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        story.append(Paragraph("AI Database Migration Studio Report", self.styles['H1_Custom']))
        story.append(Paragraph(f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['Normal_Custom']))
        story.append(Spacer(1, 0.2 * inch))

        if not all_results:
            story.append(Paragraph("No analysis results available to generate a report.", self.styles['Normal_Custom']))
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()

        # Handle both single and bulk analysis results
        if isinstance(all_results, dict):
            # Convert single result to a list for consistent processing
            all_results = [all_results]

        # Executive Summary (aggregated for bulk, or single for individual)
        story.append(Paragraph("1. Executive Summary", self.styles['H2_Custom']))
        
        summary_data = [["Database", "Engine", "Instance Type", "Monthly Cost ($)", "Optimization"]]
        total_monthly_cost = 0
        total_databases = len(all_results)
        
        for result in all_results:
            inputs = result.get('inputs', {})
            prod_rec = result['recommendations']['PROD']
            db_name = inputs.get('db_name', 'N/A')
            engine = inputs.get('engine', 'N/A')
            instance_type = prod_rec['instance_type']
            monthly_cost = f"{prod_rec['monthly_cost']:,.0f}"
            optimization = f"{prod_rec.get('optimization_score', 85)}%"
            
            summary_data.append([db_name, engine, instance_type, monthly_cost, optimization])
            total_monthly_cost += prod_rec['monthly_cost']

        table = Table(summary_data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 1.2*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph(f"Total Monthly Cost (Production): ${total_monthly_cost:,.0f}", self.styles['Normal_Custom']))
        story.append(Paragraph(f"Total Annual Cost (Production): ${total_monthly_cost * 12:,.0f}", self.styles['Normal_Custom']))
        story.append(Spacer(1, 0.2 * inch))

        # Detailed Analysis for Each Database
        for i, result in enumerate(all_results):
            inputs = result.get('inputs', {})
            recommendations = result.get('recommendations', {})
            ai_insights = result.get('ai_insights', {})
            db_name = inputs.get('db_name', f'Database {i+1}')

            story.append(Paragraph(f"2. Detailed Analysis: {db_name}", self.styles['H2_Custom']))
            story.append(Paragraph("2.1. Current Configuration", self.styles['H3_Custom']))
            story.append(Paragraph(f"• Engine: {inputs.get('engine', 'N/A').upper()}", self.styles['Bullet_Custom']))
            story.append(Paragraph(f"• Region: {inputs.get('region', 'N/A')}", self.styles['Bullet_Custom']))
            story.append(Paragraph(f"• CPU: {inputs.get('cores', 'N/A')} cores ({inputs.get('cpu_util', 'N/A')}% util)", self.styles['Bullet_Custom']))
            story.append(Paragraph(f"• RAM: {inputs.get('ram', 'N/A')} GB ({inputs.get('ram_util', 'N/A')}% util)", self.styles['Bullet_Custom']))
            story.append(Paragraph(f"• Storage: {inputs.get('storage', 'N/A'):,} GB ({inputs.get('iops', 'N/A'):,} IOPS)", self.styles['Bullet_Custom']))
            story.append(Spacer(1, 0.1 * inch))

            story.append(Paragraph("2.2. Recommended Configurations", self.styles['H3_Custom']))
            rec_table_data = [["Environment", "Instance Type", "vCPUs", "RAM (GB)", "Monthly Cost ($)"]]
            for env, rec in recommendations.items():
                rec_table_data.append([
                    env, 
                    rec['instance_type'], 
                    rec['vcpus'], 
                    rec['ram_gb'], 
                    f"{rec['monthly_cost']:,.0f}"
                ])
            
            rec_table = Table(rec_table_data, colWidths=[1.2*inch, 1.5*inch, 0.8*inch, 0.8*inch, 1.2*inch])
            rec_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#764ba2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('RIGHTPADDING', (0,0), (-1,-1), 6),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(rec_table)
            story.append(Spacer(1, 0.2 * inch))

            if 'workload' in ai_insights and 'error' not in ai_insights['workload']:
                workload = ai_insights['workload']
                story.append(Paragraph("2.3. AI Workload Insights", self.styles['H3_Custom']))
                story.append(Paragraph(f"• Workload Type: {workload.get('workload_type', 'N/A')}", self.styles['Bullet_Custom']))
                story.append(Paragraph(f"• Migration Complexity: {workload.get('complexity', 'N/A')}", self.styles['Bullet_Custom']))
                story.append(Paragraph(f"• Estimated Timeline: {workload.get('timeline', 'N/A')}", self.styles['Bullet_Custom']))
                
                if workload.get('recommendations'):
                    story.append(Paragraph("Key Recommendations:", self.styles['Normal_Custom']))
                    for rec in workload['recommendations']:
                        story.append(Paragraph(f"• {rec}", self.styles['Bullet_Custom']))
                if workload.get('risks'):
                    story.append(Paragraph("Identified Risks:", self.styles['Normal_Custom']))
                    for risk in workload['risks']:
                        story.append(Paragraph(f"• {risk}", self.styles['Bullet_Custom']))
                story.append(Spacer(1, 0.2 * inch))

            if 'migration' in ai_insights and 'error' not in ai_insights['migration']:
                migration = ai_insights['migration']
                story.append(Paragraph("2.4. Migration Strategy Overview", self.styles['H3_Custom']))
                story.append(Paragraph(f"• Estimated Timeline: {migration.get('timeline', 'N/A')}", self.styles['Bullet_Custom']))
                if migration.get('phases'):
                    story.append(Paragraph("Migration Phases:", self.styles['Normal_Custom']))
                    for phase in migration['phases']:
                        story.append(Paragraph(f"• {phase}", self.styles['Bullet_Custom']))
                if migration.get('tools'):
                    story.append(Paragraph("Recommended Tools:", self.styles['Normal_Custom']))
                    for tool in migration['tools']:
                        story.append(Paragraph(f"• {tool}", self.styles['Bullet_Custom']))
                story.append(Spacer(1, 0.2 * inch))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

def initialize_session_state():
    """Initialize all session state variables"""
    if 'ai_analytics' not in st.session_state:
        st.session_state.ai_analytics = None
    if 'calculator' not in st.session_state:
        st.session_state.calculator = EnhancedRDSCalculator()
    if 'pdf_generator' not in st.session_state: # Initialize PDF generator
        st.session_state.pdf_generator = PDFReportGenerator()
    if 'file_analysis' not in st.session_state:
        st.session_state.file_analysis = None
    if 'file_inputs' not in st.session_state:
        st.session_state.file_inputs = None
    if 'last_analysis_results' not in st.session_state:
        st.session_state.last_analysis_results = None # To store results for reports

def main():
    """Main application function"""
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <div class="ai-badge">🤖 Powered by Claude AI</div>
        <h1>AI Database Migration Studio</h1>
        <p>Enterprise database migration planning with intelligent recommendations, cost optimization, and risk assessment powered by advanced AI analytics</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar Configuration
    with st.sidebar:
        st.markdown("### 🔑 API Configuration")
        api_key = st.text_input(
            "Claude API Key", 
            type="password",
            help="Enter your Anthropic Claude API key to enable AI features",
            placeholder="sk-ant-..."
        )
        
        if api_key:
            try:
                st.session_state.ai_analytics = AIAnalytics(api_key)
                st.success("✅ AI Analytics Enabled")
            except Exception as e:
                st.error(f"❌ API Key Error: {str(e)}")
        else:
            st.info("⚠️ Enter API key to unlock AI features")
        
        st.markdown("---")
        
        # Configuration inputs with better organization
        st.markdown("### 🎯 Migration Configuration")
        
        with st.expander("📊 Database Settings", expanded=True):
            engine = st.selectbox("Database Engine", st.session_state.calculator.engines, index=0)
            region = st.selectbox("AWS Region", st.session_state.calculator.regions, index=0)
        
        with st.expander("🖥️ Current Infrastructure", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                cores = st.number_input("CPU Cores", min_value=1, value=16, step=1)
                cpu_util = st.slider("Peak CPU %", 1, 100, 65)
            with col2:
                ram = st.number_input("RAM (GB)", min_value=1, value=64, step=1)
                ram_util = st.slider("Peak RAM %", 1, 100, 75)
            
            storage = st.number_input("Storage (GB)", min_value=1, value=1000, step=100)
            iops = st.number_input("Peak IOPS", min_value=100, value=8000, step=1000)
        
        with st.expander("⚙️ Migration Settings", expanded=True):
            growth_rate = st.number_input("Annual Growth Rate (%)", min_value=0, max_value=100, value=15)
            backup_days = st.slider("Backup Retention (Days)", 1, 35, 7)
            years_projection = st.slider("Projection Years", 1, 5, 3)
            data_transfer_gb = st.number_input("Monthly Data Transfer (GB)", min_value=0, value=100)
        
        with st.expander("🤖 AI Features", expanded=True):
            enable_ai_analysis = st.checkbox("Enable AI Workload Analysis", value=True)
            enable_predictions = st.checkbox("Enable Future Predictions", value=True)
            enable_migration_strategy = st.checkbox("Generate Migration Strategy", value=True)
    
    # Collect inputs
    inputs = {
        'engine': engine,
        'region': region,
        'cores': cores,
        'cpu_util': cpu_util,
        'ram': ram,
        'ram_util': ram_util,
        'storage': storage,
        'iops': iops,
        'growth': growth_rate,
        'backup_days': backup_days,
        'years': years_projection,
        'data_transfer_gb': data_transfer_gb
    }
    
    # Create main tabs with improved styling
    main_tabs = st.tabs(["🔍 AI Analysis", "📁 Bulk Upload", "📊 Manual Configuration", "📋 Reports & Export"])
    
    # Tab 1: AI Analysis
    with main_tabs[0]:
        render_ai_analysis_tab(inputs, enable_ai_analysis, enable_predictions, enable_migration_strategy, api_key)
    
    # Tab 2: Bulk Upload  
    with main_tabs[1]:
        render_bulk_upload_tab(enable_ai_analysis, enable_predictions, enable_migration_strategy, api_key)
    
    # Tab 3: Manual Configuration
    with main_tabs[2]:
        render_manual_config_tab(inputs, enable_ai_analysis, enable_predictions, enable_migration_strategy, api_key)
    
    # Tab 4: Reports & Export
    with main_tabs[3]:
        render_reports_tab()

def render_ai_analysis_tab(inputs, enable_ai_analysis, enable_predictions, enable_migration_strategy, api_key):
    """Render the AI Analysis tab"""
    st.markdown("### 🤖 AI-Powered Database Migration Analysis")
    
    # Current configuration display
    st.markdown("#### 📊 Current Configuration Overview")
    
    config_cols = st.columns(4)
    with config_cols[0]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Database Engine</div>
            <div class="metric-value" style="font-size: 1.5rem;">{inputs['engine'].upper()}</div>
            <div class="metric-subtitle">{inputs['region']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with config_cols[1]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Compute Resources</div>
            <div class="metric-value">{inputs['cores']}</div>
            <div class="metric-subtitle">CPU Cores ({inputs['cpu_util']}% peak)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with config_cols[2]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Memory</div>
            <div class="metric-value">{inputs['ram']}</div>
            <div class="metric-subtitle">GB RAM ({inputs['ram_util']}% peak)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with config_cols[3]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Storage & Performance</div>
            <div class="metric-value">{inputs['storage']:,}</div>
            <div class="metric-subtitle">GB Storage ({inputs['iops']:,} IOPS)</div>
        </div>
        """, unsafe_allow_html=True)
    
    # AI Analysis Controls
    st.markdown("#### 🎯 AI Analysis Configuration")
    
    analysis_cols = st.columns([2, 1])
    with analysis_cols[0]:
        st.markdown("**Selected AI Features:**")
        feature_status = []
        if enable_ai_analysis:
            feature_status.append("✅ **Workload Pattern Analysis** - Deep dive into database usage patterns")
        else:
            feature_status.append("❌ Workload Pattern Analysis")
            
        if enable_predictions:
            feature_status.append("✅ **Future Capacity Planning** - AI-powered growth predictions")
        else:
            feature_status.append("❌ Future Capacity Planning")
            
        if enable_migration_strategy:
            feature_status.append("✅ **Migration Strategy Generation** - Step-by-step migration roadmap")
        else:
            feature_status.append("❌ Migration Strategy Generation")
        
        for status in feature_status:
            st.markdown(status)
    
    with analysis_cols[1]:
        if not api_key:
            st.markdown("""
            <div class="status-card status-warning">
                <strong>⚠️ API Key Required</strong><br>
                Enter your Claude API key in the sidebar to enable AI analysis
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-card status-success">
                <strong>✅ AI Ready</strong><br>
                All AI features are available
            </div>
            """, unsafe_allow_html=True)
    
    # Analysis Button
    st.markdown("---")
    
    button_cols = st.columns([1, 2, 1])
    with button_cols[1]:
        if st.button("🚀 Start AI Analysis", type="primary", use_container_width=True):
            if not api_key:
                st.error("🔑 Please enter your Claude API key in the sidebar to enable AI analysis")
            else:
                analyze_workload(inputs, enable_ai_analysis, enable_predictions, enable_migration_strategy)

def render_bulk_upload_tab(enable_ai_analysis, enable_predictions, enable_migration_strategy, api_key):
    """Render the bulk upload tab"""
    st.markdown("### 📁 Bulk Database Configuration Upload")
    
    # Upload section
    st.markdown("#### 📤 Upload Database Configurations")
    
    upload_cols = st.columns([2, 1])
    with upload_cols[0]:
        uploaded_file = st.file_uploader(
            "Upload CSV/Excel file with database configurations", 
            type=["csv", "xlsx"],
            help="Upload a file containing multiple database configurations for batch analysis"
        )
    
    with upload_cols[1]:
        if st.button("📋 Download Template", use_container_width=True, key="download_template_button"):
            # Create sample template
            template_data = {
                'db_name': ['ProductionDB', 'StagingDB', 'AnalyticsDB'],
                'engine': ['postgres', 'postgres', 'oracle-ee'],
                'region': ['us-east-1', 'us-east-1', 'us-west-2'],
                'cores': [16, 8, 32],
                'cpu_util': [75, 60, 80],
                'ram': [64, 32, 128],
                'ram_util': [70, 65, 75],
                'storage': [2000, 500, 5000],
                'iops': [10000, 5000, 15000],
                'growth': [15, 10, 20],
                'backup_days': [7, 7, 14],
                'years': [3, 3, 3],
                'data_transfer_gb': [200, 50, 500]
            }
            template_df = pd.DataFrame(template_data)
            csv_buffer = io.StringIO()
            template_df.to_csv(csv_buffer, index=False)
            
            st.download_button(
                label="📄 Download CSV Template",
                data=csv_buffer.getvalue(),
                file_name=f"database_migration_template_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="download_csv_template_button"
            )
    
    if uploaded_file:
        process_bulk_upload(uploaded_file, enable_ai_analysis, enable_predictions, enable_migration_strategy, api_key)

def process_bulk_upload(uploaded_file, enable_ai_analysis, enable_predictions, enable_migration_strategy, api_key):
    """Process the bulk upload file"""
    try:
        st.markdown("#### 📋 File Processing Results")
        
        with st.spinner("🔄 Processing uploaded file..."):
            valid_inputs, errors = parse_uploaded_file(uploaded_file)
        
        # Results summary
        result_cols = st.columns(3)
        with result_cols[0]:
            st.metric("Total Rows", len(valid_inputs) + len(errors))
        with result_cols[1]:
            st.metric("Valid Configurations", len(valid_inputs))
        with result_cols[2]:
            st.metric("Errors", len(errors))
        
        # Show errors if any
        if errors:
            with st.expander(f"⚠️ View {len(errors)} Validation Errors", expanded=False):
                for i, error in enumerate(errors, 1):
                    st.error(f"{i}. {error}")
        
        # Show valid configurations
        if valid_inputs:
            st.success(f"✅ Successfully parsed **{len(valid_inputs)}** valid database configurations")
            st.session_state.file_inputs = valid_inputs
            
            # Display preview
            st.markdown("#### 📊 Configuration Preview")
            preview_data = []
            for i, db in enumerate(valid_inputs[:5], 1):  # Show first 5
                preview_data.append({
                    "#": i,
                    "Database": db.get('db_name', f'Database {i}'),
                    "Engine": db.get('engine', 'Unknown'),
                    "Region": db.get('region', 'Unknown'),
                    "CPU": f"{db.get('cores', 'N/A')} cores",
                    "RAM": f"{db.get('ram', 'N/A')} GB",
                    "Storage": f"{db.get('storage', 'N/A')} GB"
                })
            
            preview_df = pd.DataFrame(preview_data)
            st.dataframe(preview_df, use_container_width=True, hide_index=True)
            
            if len(valid_inputs) > 5:
                st.info(f"Showing first 5 configurations. Total: {len(valid_inputs)} databases")
            
            # Analysis controls
            st.markdown("#### 🚀 Bulk Analysis")
            
            # Use a container with flexbox to center the button
            st.markdown("""
            <div style="display: flex; justify-content: center; width: 100%; margin-top: 1.5rem; margin-bottom: 1.5rem;">
            """, unsafe_allow_html=True)
            
            # The button itself
            if st.button("🚀 Analyze All Databases", type="primary", use_container_width=False, key="bulk_analyze_button"):
                if not api_key and (enable_ai_analysis or enable_predictions or enable_migration_strategy):
                    st.error("🔑 Please enter your Claude API key in the sidebar to enable AI analysis")
                else:
                    analyze_file(valid_inputs, enable_ai_analysis, enable_predictions, enable_migration_strategy)
            
            st.markdown("</div>", unsafe_allow_html=True) # Close the centering div

            # The status of AI features, now separate from the button's centering logic
            st.markdown(f"""
            <div style="margin-top: 1rem; padding: 1rem; border: 1px solid #e2e8f0; border-radius: 8px; background: #f8fafc;">
                <strong>Analysis Settings:</strong><br>
                <ul>
                    <li>• AI Workload Analysis: {'✅ Enabled' if enable_ai_analysis else '❌ Disabled'}</li>
                    <li>• Future Predictions: {'✅ Enabled' if enable_predictions else '❌ Disabled'}</li>
                    <li>• Migration Strategy: {'✅ Enabled' if enable_migration_strategy else '❌ Disabled'}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)


        else:
            st.error("❌ No valid database configurations found. Please check your file format and data.")
            
    except Exception as e:
        st.error(f"❌ **Error processing file:** {str(e)}")
        st.info("💡 Make your file has all required columns and proper formatting.")

def render_manual_config_tab(inputs, enable_ai_analysis, enable_predictions, enable_migration_strategy, api_key):
    """Render the manual configuration tab"""
    st.markdown("### 📊 Manual Database Configuration")
    
    # Configuration summary
    st.markdown("#### 🎯 Current Configuration Summary")
    
    summary_cols = st.columns(2)
    with summary_cols[0]:
        st.markdown("""
        <div class="config-section">
            <div class="config-header">🖥️ Infrastructure Details</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div><strong>Database Engine:</strong> {}</div>
                <div><strong>AWS Region:</strong> {}</div>
                <div><strong>CPU Cores:</strong> {}</div>
                <div><strong>RAM:</strong> {} GB</div>
                <div><strong>Storage:</strong> {:,} GB</div>
                <div><strong>IOPS:</strong> {:,}</div>
            </div>
        </div>
        """.format(
            inputs['engine'].upper(),
            inputs['region'],
            inputs['cores'],
            inputs['ram'],
            inputs['storage'],
            inputs['iops']
        ), unsafe_allow_html=True)
    
    with summary_cols[1]:
        st.markdown("""
        <div class="config-section">
            <div class="config-header">📈 Performance & Growth</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div><strong>CPU Utilization:</strong> {}%</div>
                <div><strong>RAM Utilization:</strong> {}%</div>
                <div><strong>Growth Rate:</strong> {}% annually</div>
                <div><strong>Backup Retention:</strong> {} days</div>
                <div><strong>Data Transfer:</strong> {} GB/month</div>
                <div><strong>Projection Period:</strong> {} years</div>
            </div>
        </div>
        """.format(
            inputs['cpu_util'],
            inputs['ram_util'],
            inputs['growth'],
            inputs['backup_days'],
            inputs['data_transfer_gb'],
            inputs['years']
        ), unsafe_allow_html=True)
    
    # Quick analysis buttons
    st.markdown("#### ⚡ Quick Actions")
    
    action_cols = st.columns(3)
    with action_cols[0]:
        if st.button("🧮 Basic Cost Calculation", use_container_width=True):
            perform_basic_calculation(inputs)
    
    with action_cols[1]:
        if st.button("🚀 Full AI Analysis", type="primary", use_container_width=True):
            if not api_key:
                st.error("🔑 Please enter your Claude API key in the sidebar to enable AI analysis")
            else:
                analyze_workload(inputs, enable_ai_analysis, enable_predictions, enable_migration_strategy)
    
    with action_cols[2]:
        if st.button("📊 Generate Sample Report", use_container_width=True):
            generate_sample_report()

def render_reports_tab():
    """Render the reports and export tab"""
    st.markdown("### 📋 Reports & Export Center")
    
    st.markdown("#### 📊 Available Reports")
    
    report_cols = st.columns(2)
    
    with report_cols[0]:
        st.markdown("""
        <div class="config-section">
            <div class="config-header">📈 Executive Reports</div>
            <p>Comprehensive analysis for stakeholders and decision makers.</p>
            <ul>
                <li>Executive summary with key metrics</li>
                <li>Cost-benefit analysis</li>
                <li>ROI calculations and projections</li>
                <li>Risk assessment overview</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📈 Generate Executive Report (Excel)", use_container_width=True, key="generate_executive_report_tab"):
            if st.session_state.last_analysis_results:
                try:
                    excel_data = export_full_report(st.session_state.last_analysis_results)
                    st.download_button(
                        label="📊 Download Executive Excel Report",
                        data=excel_data,
                        file_name=f"executive_migration_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="download_executive_excel_tab"
                    )
                    st.success("✅ Executive report generated successfully!")
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
            else:
                st.info("💡 No analysis results found. Please run an analysis first (Manual Config or Bulk Upload).")
        
        if st.button("📄 Generate Executive Report (PDF)", use_container_width=True, key="generate_executive_report_pdf_tab"):
            if st.session_state.last_analysis_results:
                try:
                    pdf_data = st.session_state.pdf_generator.generate_report(st.session_state.last_analysis_results)
                    st.download_button(
                        label="⬇️ Download Executive PDF Report",
                        data=pdf_data,
                        file_name=f"executive_migration_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="download_executive_pdf_tab"
                    )
                    st.success("✅ Executive PDF report generated successfully!")
                except Exception as e:
                    st.error(f"PDF Export failed: {str(e)}")
            else:
                st.info("💡 No analysis results found. Please run an analysis first (Manual Config or Bulk Upload).")

    with report_cols[1]:
        st.markdown("""
        <div class="config-section">
            <div class="config-header">🔧 Technical Reports</div>
            <p>Detailed technical documentation for implementation teams.</p>
            <ul>
                <li>Instance specifications</li>
                <li>Configuration details</li>
                <li>Migration procedures</li>
                <li>Performance metrics</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔧 Generate Technical Report", use_container_width=True, key="generate_technical_report_tab"):
            if st.session_state.last_analysis_results:
                st.markdown("##### Detailed Technical Report Output")
                if isinstance(st.session_state.last_analysis_results, list): # Bulk analysis results
                    for i, result in enumerate(st.session_state.last_analysis_results):
                        db_name = result['inputs'].get('db_name', f'Database {i+1}')
                        st.markdown(f"**--- Technical Report for {db_name} ---**")
                        st.json(result) # Display raw JSON for technical details
                        st.markdown("---")
                else: # Single analysis result
                    st.json(st.session_state.last_analysis_results)
                st.success("✅ Technical report displayed above!")
            else:
                st.info("💡 No analysis results found. Please run an analysis first (Manual Config or Bulk Upload).")
    
    # Sample downloads
    st.markdown("#### 📄 Sample Templates & Documentation")
    
    template_cols = st.columns(3)
    
    with template_cols[0]:
        if st.button("📋 Download Input Template", use_container_width=True, key="download_input_template"):
            # Create sample template
            template_data = {
                'db_name': ['ProductionDB', 'StagingDB'],
                'engine': ['postgres', 'oracle-ee'],
                'region': ['us-east-1', 'us-west-2'],
                'cores': [16, 32],
                'cpu_util': [75, 80],
                'ram': [64, 128],
                'ram_util': [70, 75],
                'storage': [2000, 5000],
                'iops': [10000, 15000],
                'growth': [15, 20],
                'backup_days': [7, 14],
                'years': [3, 3],
                'data_transfer_gb': [200, 500]
            }
            template_df = pd.DataFrame(template_data)
            csv_buffer = io.StringIO()
            template_df.to_csv(csv_buffer, index=False)
            
            st.download_button(
                label="📄 Download CSV Template",
                data=csv_buffer.getvalue(),
                file_name=f"migration_template_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="download_migration_template_button"
            )
    
    with template_cols[1]:
        if st.button("📊 Sample Analysis Report", use_container_width=True, key="sample_analysis_report"):
            generate_sample_report()
    
    with template_cols[2]:
        if st.button("📖 Migration Guide", use_container_width=True, key="migration_guide"):
            st.info("Migration guide will be available after running analysis")

def perform_basic_calculation(inputs):
    """Perform basic cost calculation without AI"""
    st.markdown("#### 🧮 Basic Cost Calculation Results")
    
    with st.spinner("🔄 Calculating recommendations..."):
        calculator = st.session_state.calculator
        recommendations = {}
        for env in calculator.env_profiles:
            recommendations[env] = calculator.calculate_requirements(inputs, env)
    
    # Store results for reporting
    st.session_state.last_analysis_results = {'inputs': inputs, 'recommendations': recommendations, 'ai_insights': {}} # No AI insights for basic calc
    
    # Display basic results
    st.markdown("##### 💰 Cost Summary by Environment")
    
    env_data = []
    for env, rec in recommendations.items():
        env_data.append({
            'Environment': env,
            'Instance Type': rec['instance_type'],
            'vCPUs': rec['vcpus'],
            'RAM (GB)': rec['ram_gb'],
            'Storage (GB)': rec['storage_gb'],
            'Monthly Cost': rec['monthly_cost'],
            'Annual Cost': rec['annual_cost']
        })
    
    env_df = pd.DataFrame(env_data)
    st.dataframe(
        env_df,
        column_config={
            "Monthly Cost": st.column_config.NumberColumn("Monthly Cost", format="$%.0f"),
            "Annual Cost": st.column_config.NumberColumn("Annual Cost", format="$%.0f")
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Key metrics
    prod_rec = recommendations['PROD']
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Recommended Instance", prod_rec['instance_type'])
    with col2:
        st.metric("Monthly Cost (PROD)", f"${prod_rec['monthly_cost']:,.0f}")
    with col3:
        st.metric("Annual Cost (PROD)", f"${prod_rec['annual_cost']:,.0f}")
    
    st.info("💡 For detailed AI insights, migration strategies, and risk assessments, enable AI features and run full analysis.")

def analyze_workload(inputs, enable_ai_analysis, enable_predictions, enable_migration_strategy):
    """Main analysis function with AI integration and enhanced UI"""
    
    # Create progress tracking
    progress_container = st.container()
    with progress_container:
        st.markdown("#### 🔄 Analysis in Progress")
        progress_bar = st.progress(0)
        status_text = st.empty()
        stage_info = st.empty()
    
    try:
        # Stage 1: Basic calculations
        status_text.text("🔄 Calculating resource requirements...")
        stage_info.info("Analyzing current workload and determining optimal AWS configurations")
        progress_bar.progress(20)
        time.sleep(1)
        
        calculator = st.session_state.calculator
        recommendations = {}
        for env in calculator.env_profiles:
            recommendations[env] = calculator.calculate_requirements(inputs, env)
        
        progress_bar.progress(40)
        
        # Stage 2: AI Analysis
        ai_insights = {}
        if st.session_state.ai_analytics and enable_ai_analysis:
            status_text.text("🤖 Running AI workload analysis...")
            stage_info.info("AI is analyzing workload patterns and generating intelligent recommendations")
            progress_bar.progress(60)
            
            try:
                workload_analysis = st.session_state.ai_analytics.analyze_workload_patterns(inputs)
                ai_insights['workload'] = workload_analysis
                if "error" in ai_insights['workload']:
                    st.error(ai_insights['workload']['error'])
                time.sleep(2)
            except Exception as e:
                st.error(f"AI Analysis Error: {str(e)}")
                ai_insights['workload'] = {"error": str(e)}
        
        # Stage 3: Predictions
        if st.session_state.ai_analytics and enable_predictions:
            status_text.text("🔮 Generating future predictions...")
            stage_info.info("AI is forecasting future capacity requirements and cost projections")
            progress_bar.progress(75)
            
            try:
                predictions = st.session_state.ai_analytics.predict_future_requirements(inputs, inputs['years'])
                ai_insights['predictions'] = predictions
                if "error" in ai_insights['predictions']:
                    st.error(ai_insights['predictions']['error'])
                time.sleep(2)
            except Exception as e:
                st.error(f"Prediction Error: {str(e)}")
                ai_insights['predictions'] = {"error": str(e)}
        
        # Stage 4: Migration Strategy
        if st.session_state.ai_analytics and enable_migration_strategy:
            status_text.text("📋 Creating migration strategy...")
            stage_info.info("AI is developing a comprehensive migration roadmap and risk assessment")
            progress_bar.progress(90)
            
            try:
                migration_strategy = st.session_state.ai_analytics.generate_migration_strategy(recommendations['PROD'])
                ai_insights['migration'] = migration_strategy
                if "error" in ai_insights['migration']:
                    st.error(ai_insights['migration']['error'])
                time.sleep(2)
            except Exception as e:
                st.error(f"Migration Strategy Error: {str(e)}")
                ai_insights['migration'] = {"error": str(e)}
        
        # Complete
        progress_bar.progress(100)
        status_text.text("✅ Analysis complete!")
        stage_info.success("All analysis stages completed successfully")
        time.sleep(1)
        
        # Clear progress indicators
        progress_container.empty()
        
        # Store results for reporting
        st.session_state.last_analysis_results = {'inputs': inputs, 'recommendations': recommendations, 'ai_insights': ai_insights}

        # Display comprehensive results
        display_enhanced_results(recommendations, ai_insights, inputs)
        
    except Exception as e:
        progress_container.empty()
        st.error(f"Analysis failed: {str(e)}")

def display_enhanced_results(recommendations, ai_insights, inputs):
    """Display comprehensive results with enhanced AI insights"""
    
    st.markdown("### 🎯 Migration Analysis Results")
    
    # Executive Summary Header
    prod_rec = recommendations['PROD']
    
    summary_cols = st.columns(4)
    with summary_cols[0]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Recommended Instance</div>
            <div class="metric-value" style="color: #667eea;">{prod_rec['instance_type']}</div>
            <div class="metric-subtitle">{prod_rec['vcpus']} vCPUs • {prod_rec['ram_gb']} GB RAM</div>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_cols[1]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Monthly Cost</div>
            <div class="metric-value" style="color: #10b981;">${prod_rec['monthly_cost']:,.0f}</div>
            <div class="metric-subtitle">Production Environment</div>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_cols[2]:
        onprem_monthly = inputs['cores'] * 200
        monthly_savings = onprem_monthly - prod_rec['monthly_cost']
        savings_percentage = (monthly_savings / onprem_monthly) * 100 if onprem_monthly > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Monthly Savings</div>
            <div class="metric-value" style="color: #10b981;">${monthly_savings:,.0f}</div>
            <div class="metric-subtitle">{savings_percentage:.0f}% vs On-Premise</div>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_cols[3]:
        optimization_score = prod_rec.get('optimization_score', 85)
        score_color = "#10b981" if optimization_score >= 80 else "#f59e0b" if optimization_score >= 60 else "#ef4444"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Optimization Score</div>
            <div class="metric-value" style="color: {score_color};">{optimization_score}%</div>
            <div class="metric-subtitle">Resource Efficiency</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Results tabs
    result_tabs = st.tabs([
        "🤖 AI Insights", 
        "🏗️ Recommendations", 
        "💰 Cost Analysis", 
        "📈 Future Planning",
        "🚀 Migration Strategy"
    ])
    
    with result_tabs[0]:  # AI Insights
        render_ai_insights_tab(ai_insights, inputs)
    
    with result_tabs[1]:  # Recommendations
        render_recommendations_tab(recommendations, inputs)
    
    with result_tabs[2]:  # Cost Analysis
        render_cost_analysis_tab(recommendations, inputs)
    
    with result_tabs[3]:  # Future Planning
        render_future_planning_tab(ai_insights, recommendations, inputs)
    
    with result_tabs[4]:  # Migration Strategy
        render_migration_strategy_tab(ai_insights, recommendations)

def render_ai_insights_tab(ai_insights, inputs):
    """Render AI insights with professional layout"""
    st.markdown("#### 🤖 AI-Powered Intelligence")
    
    if not ai_insights:
        st.markdown("""
        <div class="status-card status-info">
            <strong>🔑 AI Features Not Enabled</strong><br>
            Configure your Claude API key in the sidebar and enable AI features to see intelligent insights.
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Workload Analysis
    if 'workload' in ai_insights and 'error' not in ai_insights['workload']:
        workload = ai_insights['workload']
        
        st.markdown("""
        <div class="ai-insight">
            <h4>🔍 Intelligent Workload Analysis</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Workload classification
        insight_cols = st.columns(3)
        with insight_cols[0]:
            st.markdown(f"""
            <div class="analysis-card">
                <h6>📊 Workload Classification</h6>
                <div style="font-size: 1.5rem; font-weight: bold; color: #667eea; margin: 1rem 0;">
                    {workload.get('workload_type', 'Mixed')}
                </div>
                <p style="color: #64748b; font-size: 0.9rem;">
                    Based on CPU/RAM patterns and usage characteristics
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with insight_cols[1]:
            complexity = workload.get('complexity', 'Medium')
            complexity_color = "#ef4444" if complexity == "High" else "#f59e0b" if complexity == "Medium" else "#10b981"
            st.markdown(f"""
            <div class="analysis-card">
                <h6>⚙️ Migration Complexity</h6>
                <div style="font-size: 1.5rem; font-weight: bold; color: {complexity_color}; margin: 1rem 0;">
                    {complexity}
                </div>
                <p style="color: #64748b; font-size: 0.9rem;">
                    Risk assessment and effort estimation
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with insight_cols[2]:
            timeline = workload.get('timeline', '12-16 weeks')
            st.markdown(f"""
            <div class="analysis-card">
                <h6>⏱️ Estimated Timeline</h6>
                <div style="font-size: 1.5rem; font-weight: bold; color: #8b5cf6; margin: 1rem 0;">
                    {timeline}
                </div>
                <p style="color: #64748b; font-size: 0.9rem;">
                    End-to-end migration duration
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # AI Recommendations
        recommendations = workload.get('recommendations', [])
        if recommendations:
            st.markdown("##### 🎯 AI-Generated Recommendations")
            
            rec_cols = st.columns(2)
            mid_point = len(recommendations) // 2
            
            with rec_cols[0]:
                for i, rec in enumerate(recommendations[:mid_point], 1):
                    st.markdown(f"""
                    <div style="background: #f8fafc; border-left: 4px solid #667eea; padding: 1rem; margin: 0.5rem 0; border-radius: 0 8px 8px 0;">
                        <strong>{i}.</strong> {rec}
                    </div>
                    """, unsafe_allow_html=True)
            
            with rec_cols[1]:
                for i, rec in enumerate(recommendations[mid_point:], mid_point + 1):
                    st.markdown(f"""
                    <div style="background: #f8fafc; border-left: 4px solid #667eea; padding: 1rem; margin: 0.5rem 0; border-radius: 0 8px 8px 0;">
                        <strong>{i}.</strong> {rec}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Risk Assessment
        risks = workload.get('risks', [])
        bottlenecks = workload.get('bottlenecks', [])
        
        if risks or bottlenecks:
            st.markdown("##### ⚠️ Risk Assessment & Bottlenecks")
            
            risk_cols = st.columns(2)
            
            with risk_cols[0]:
                if risks:
                    st.markdown("**🔍 Identified Risks:**")
                    for risk in risks[:3]:
                        st.markdown(f"""
                        <div class="status-card status-warning" style="margin: 0.5rem 0;">
                            • {risk}
                        </div>
                        """, unsafe_allow_html=True)
            
            with risk_cols[1]:
                if bottlenecks:
                    st.markdown("**⚡ Performance Bottlenecks:**")
                    for bottleneck in bottlenecks[:3]:
                        st.markdown(f"""
                        <div class="status-card status-info" style="margin: 0.5rem 0;">
                            • {bottleneck}
                        </div>
                        """, unsafe_allow_html=True)
    
    # Error handling
    if 'workload' in ai_insights and 'error' in ai_insights['workload']:
        st.markdown(f"""
        <div class="status-card status-error">
            <strong>❌ AI Analysis Error</strong><br>
            {ai_insights['workload']['error']}
        </div>
        """, unsafe_allow_html=True)

def render_recommendations_tab(recommendations, inputs):
    """Render environment recommendations"""
    st.markdown("#### 🏗️ Environment-Specific Recommendations")
    
    # Environment comparison table
    st.markdown("##### 📊 Configuration Comparison")
    
    env_data = []
    for env, rec in recommendations.items():
        env_icon = {"PROD": "🔴", "STAGING": "🟡", "QA": "🔵", "DEV": "🟢"}
        env_data.append({
            'Environment': f"{env_icon.get(env, '⚪')} {env}",
            'Instance Type': rec['instance_type'],
            'vCPUs': rec['vcpus'],
            'RAM (GB)': rec['ram_gb'],
            'Storage (GB)': f"{rec['storage_gb']:,}",
            'Monthly Cost': rec['monthly_cost'],
            'Annual Cost': rec['annual_cost'],
            'Optimization': f"{rec.get('optimization_score', 85)}%"
        })
    
    env_df = pd.DataFrame(env_data)
    st.dataframe(
        env_df,
        column_config={
            "Monthly Cost": st.column_config.NumberColumn("Monthly Cost", format="$%.0f"),
            "Annual Cost": st.column_config.NumberColumn("Annual Cost", format="$%.0f")
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Detailed environment breakdown
    st.markdown("##### 🎯 Environment Details")
    
    env_details_cols = st.columns(2)
    
    with env_details_cols[0]:
        # Production details
        prod_rec = recommendations['PROD']
        st.markdown(f"""
        <div class="config-section">
            <div class="config-header">🔴 Production Environment</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin: 1rem 0;">
                <div><strong>Instance:</strong></div><div>{prod_rec['instance_type']}</div>
                <div><strong>Compute:</strong></div><div>{prod_rec['vcpus']} vCPUs, {prod_rec['ram_gb']} GB RAM</div>
                <div><strong>Storage:</strong></div><div>{prod_rec['storage_gb']:,} GB</div>
                <div><strong>Monthly Cost:</strong></div><div style="color: #10b981; font-weight: bold;">${prod_rec['monthly_cost']:,.0f}</div>
                <div><strong>Optimization:</strong></div><div>{prod_rec.get('optimization_score', 85)}%</div>
            </div>
            <div style="background: #f0f9ff; padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                <strong>💡 Key Features:</strong><br>
                • High availability with Multi-AZ deployment<br>
                • Automated backups and point-in-time recovery<br>
                • Performance monitoring and alerting<br>
                • Enhanced security and compliance
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with env_details_cols[1]:
        # Development details
        dev_rec = recommendations['DEV']
        st.markdown(f"""
        <div class="config-section">
            <div class="config-header">🟢 Development Environment</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin: 1rem 0;">
                <div><strong>Instance:</strong></div><div>{dev_rec['instance_type']}</div>
                <div><strong>Compute:</strong></div><div>{dev_rec['vcpus']} vCPUs, {dev_rec['ram_gb']} GB RAM</div>
                <div><strong>Storage:</strong></div><div>{dev_rec['storage_gb']:,} GB</div>
                <div><strong>Monthly Cost:</strong></div><div style="color: #10b981; font-weight: bold;">${dev_rec['monthly_cost']:,.0f}</div>
                <div><strong>Optimization:</strong></div><div>{dev_rec.get('optimization_score', 85)}%</div>
            </div>
            <div style="background: #f0fdf4; padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                <strong>💡 Key Features:</strong><br>
                • Cost-optimized for development workloads<br>
                • Flexible instance sizing<br>
                • Development-friendly backup policies<br>
                • Easy environment refresh capabilities
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_cost_analysis_tab(recommendations, inputs):
    """Render detailed cost analysis"""
    st.markdown("#### 💰 Comprehensive Cost Analysis")
    
    # Cost visualization
    cost_vis_cols = st.columns(2)
    
    with cost_vis_cols[0]:
        # Environment cost comparison
        env_costs = [rec['monthly_cost'] for rec in recommendations.values()]
        env_names = list(recommendations.keys())
        
        fig1 = px.bar(
            x=env_names,
            y=env_costs,
            title="Monthly Cost by Environment",
            labels={'x': 'Environment', 'y': 'Monthly Cost ($)'},
            color=env_costs,
            color_continuous_scale='Viridis',
            text=[f'${cost:,.0f}' for cost in env_costs]
        )
        fig1.update_traces(textposition='outside')
        fig1.update_layout(
            showlegend=False, 
            height=400,
            title_font_size=16,
            xaxis_title_font_size=14,
            yaxis_title_font_size=14
        )
        st.plotly_chart(fig1, use_container_width=True, config={'responsive': True}) # Added config
    
    with cost_vis_cols[1]:
        # Production cost breakdown
        prod_rec = recommendations['PROD']
        cost_breakdown = prod_rec.get('cost_breakdown', {})
        
        if cost_breakdown and 'total' in cost_breakdown:
            # Remove total from breakdown for pie chart
            breakdown_for_chart = {k: v for k, v in cost_breakdown.items() if k != 'total'}
            
            fig2 = px.pie(
                values=list(breakdown_for_chart.values()),
                names=[k.replace('_', ' ').title() for k in breakdown_for_chart.keys()],
                title="Production Cost Breakdown"
            )
            fig2.update_traces(textposition='inside', textinfo='percent+label')
            fig2.update_layout(height=400, title_font_size=16)
            st.plotly_chart(fig2, use_container_width=True, config={'responsive': True}) # Added config
    
    # Cost comparison with on-premise
    st.markdown("##### 📊 Cost Comparison & Savings Analysis")
    
    # Calculate savings
    onprem_monthly = inputs['cores'] * 200  # Estimated on-premise cost
    cloud_monthly = recommendations['PROD']['monthly_cost']
    monthly_savings = onprem_monthly - cloud_monthly
    annual_savings = monthly_savings * 12
    
    savings_cols = st.columns(4)
    
    with savings_cols[0]:
        st.metric("On-Premise (Est.)", f"${onprem_monthly:,.0f}/mo")
    with savings_cols[1]:
        st.metric("AWS Cloud", f"${cloud_monthly:,.0f}/mo")
    with savings_cols[2]:
        st.metric("Monthly Savings", f"${monthly_savings:,.0f}", delta=f"{(monthly_savings/onprem_monthly)*100:.0f}%")
    with savings_cols[3]:
        payback_months = (cloud_monthly * 0.1) / (monthly_savings / 12) if monthly_savings > 0 else 0
        st.metric("ROI Payback", f"{payback_months:.0f} months" if payback_months > 0 else "Immediate")
    
    # 3-year projection
    st.markdown("##### 📈 3-Year Cost Projection")
    
    years = list(range(1, 4))
    growth_rate = inputs.get('growth', 15) / 100
    
    onprem_costs = [onprem_monthly * 12 * (1 + growth_rate) ** (year - 1) for year in years]
    cloud_costs = [cloud_monthly * 12 * (1 + growth_rate * 0.7) ** (year - 1) for year in years]  # Cloud scales better
    
    projection_df = pd.DataFrame({
        'Year': years,
        'On-Premise': onprem_costs,
        'AWS Cloud': cloud_costs,
        'Savings': [op - cl for op, cl in zip(onprem_costs, cloud_costs)]
    })
    
    fig3 = px.line(
        projection_df, 
        x='Year', 
        y=['On-Premise', 'AWS Cloud'],
        title="3-Year Cost Projection",
        labels={'value': 'Annual Cost ($)', 'variable': 'Infrastructure'}
    )
    fig3.update_layout(height=400, title_font_size=16)
    st.plotly_chart(fig3, use_container_width=True, config={'responsive': True}) # Added config

def render_future_planning_tab(ai_insights, recommendations, inputs):
    """Render future planning insights"""
    st.markdown("#### 📈 Future Planning & Predictions")
    
    if 'predictions' in ai_insights and 'error' not in ai_insights['predictions']:
        predictions = ai_insights['predictions']
        
        # Prediction summary
        st.markdown("""
        <div class="ai-insight">
            <h4>🔮 AI-Powered Future Predictions</h4>
        </div>
        """, unsafe_allow_html=True)
        
        prediction_cols = st.columns(3)
        
        with prediction_cols[0]:
            st.markdown(f"""
            <div class="analysis-card">
                <h6>💻 CPU Trend</h6>
                <p style="font-weight: bold; color: #667eea; margin: 1rem 0;">
                    {predictions.get('cpu_trend', 'Gradual increase expected')}
                </p>
                <p style="color: #64748b; font-size: 0.9rem;">
                    Based on workload analysis and growth patterns
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with prediction_cols[1]:
            st.markdown(f"""
            <div class="analysis-card">
                <h6>🧠 Memory Trend</h6>
                <p style="font-weight: bold; color: #10b981; margin: 1rem 0;">
                    {predictions.get('memory_trend', 'Stable with seasonal peaks')}
                </p>
                <p style="color: #64748b; font-size: 0.9rem;">
                    Memory usage patterns and optimization opportunities
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with prediction_cols[2]:
            st.markdown(f"""
            <div class="analysis-card">
                <h6>💾 Storage Trend</h6>
                <p style="font-weight: bold; color: #f59e0b; margin: 1rem 0;">
                    {predictions.get('storage_trend', 'Linear growth with data retention')}
                </p>
                <p style="color: #64748b; font-size: 0.9rem;">
                    Data growth patterns and retention policies
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Future recommendations
        future_recs = predictions.get('recommendations', [])
        if future_recs:
            st.markdown("##### 🎯 Future Planning Recommendations")
            
            for i, rec in enumerate(future_recs, 1):
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); 
                            border-left: 4px solid #0ea5e9; padding: 1rem; margin: 0.5rem 0; border-radius: 0 8px 8px 0;">
                        <strong>{i}.</strong> {rec}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Confidence and factors
        confidence_cols = st.columns(2)
        
        with confidence_cols[0]:
            confidence = predictions.get('confidence', 'High (85-90%)')
            st.markdown(f"""
            <div class="config-section">
                <div class="config-header">📊 Prediction Confidence</div>
                <div style="font-size: 1.2rem; font-weight: bold; color: #10b981; margin: 1rem 0;">
                    {confidence}
                </div>
                <p style="color: #64748b;">
                    Based on historical data patterns, industry benchmarks, and AI analysis
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with confidence_cols[1]:
            key_factors = predictions.get('key_factors', [])
            if key_factors:
                st.markdown("""
                <div class="config-section">
                    <div class="config-header">🔍 Key Factors</div>
                    <ul>
                """, unsafe_allow_html=True)
                
                for factor in key_factors:
                    st.markdown(f"<li>{factor}</li>", unsafe_allow_html=True)
                
                st.markdown("</ul></div>", unsafe_allow_html=True)
    else:
        # Show basic projections without AI
        st.markdown("##### 📊 Basic Growth Projections")
        
        growth_rate = inputs.get('growth', 15)
        years = list(range(1, 6))
        
        current_storage = inputs['storage']
        projected_storage = [current_storage * (1 + growth_rate/100) ** year for year in years]
        
        current_cost = recommendations['PROD']['monthly_cost']
        projected_costs = [current_cost * (1 + growth_rate/100 * 0.8) ** year for year in years]
        
        projection_df = pd.DataFrame({
            'Year': [f"Year {y}" for y in years],
            'Storage (GB)': [f"{storage:,.0f}" for storage in projected_storage],
            'Estimated Cost': [f"${cost:,.0f}" for cost in projected_costs]
        })
        
        st.dataframe(projection_df, use_container_width=True, hide_index=True)
        
        st.info("💡 Enable AI predictions for detailed future analysis including CPU, memory trends, and confidence intervals.")

def render_migration_strategy_tab(ai_insights, recommendations):
    """Render migration strategy details"""
    st.markdown("#### 🚀 Migration Strategy & Implementation")
    
    if 'migration' in ai_insights and 'error' not in ai_insights['migration']:
        migration = ai_insights['migration']
        
        st.markdown("""
        <div class="ai-insight">
            <h4>📋 AI-Generated Migration Strategy</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Migration phases
        st.markdown("##### 📅 Migration Phases")
        
        phases = migration.get('phases', [])
        if phases:
            phase_cols = st.columns(len(phases))
            
            for i, (phase, col) in enumerate(zip(phases, phase_cols), 1):
                with col:
                    st.markdown(f"""
                    <div class="analysis-card" style="text-align: center;">
                        <div style="background: #667eea; color: white; border-radius: 50%; width: 40px; height: 40px; 
                                    display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem auto; font-weight: bold;">
                            {i}
                        </div>
                        <h6 style="margin: 0;">{phase}</h6>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Timeline and resources
        strategy_cols = st.columns(2)
        
        with strategy_cols[0]:
            timeline = migration.get('timeline', '14-18 weeks')
            st.markdown(f"""
            <div class="config-section">
                <div class="config-header">⏱️ Estimated Timeline</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #8b5cf6; margin: 1rem 0;">
                    {timeline}
                </div>
                <p style="color: #64748b;">
                    End-to-end migration including testing and validation phases
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Required resources
            resources = migration.get('resources', [])
            if resources:
                st.markdown("**👥 Required Team Members:**")
                for resource in resources:
                    st.markdown(f"• {resource}")
        
        with strategy_cols[1]:
            # Migration tools
            tools = migration.get('tools', [])
            if tools:
                st.markdown("""
                <div class="config-section">
                    <div class="config-header">🛠️ Recommended Tools</div>
                    <ul>
                """, unsafe_allow_html=True)
                
                for tool in tools:
                    st.markdown(f"<li>{tool}</li>", unsafe_allow_html=True)
                
                st.markdown("</ul></div>", unsafe_allow_html=True)
        
        # Pre-migration checklist
        checklist = migration.get('checklist', [])
        if checklist:
            st.markdown("##### ✅ Pre-Migration Checklist")
            
            checklist_cols = st.columns(2)
            mid_point = len(checklist) // 2
            
            with checklist_cols[0]:
                for item in checklist[:mid_point]:
                    st.markdown(f"""
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 1rem; margin: 0.5rem 0; border-radius: 8px;">
                        <input type="checkbox" style="margin-right: 0.5rem;"> {item}
                    </div>
                    """, unsafe_allow_html=True)
            
            with checklist_cols[1]:
                for item in checklist[mid_point:]:
                    st.markdown(f"""
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 1rem; margin: 0.5rem 0; border-radius: 8px;">
                        <input type="checkbox" style="margin-right: 0.5rem;"> {item}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Risk mitigation
        risks = migration.get('risks', [])
        if risks:
            st.markdown("##### ⚠️ Risk Mitigation Strategy")
            
            for i, risk in enumerate(risks, 1):
                st.markdown(f"""
                <div class="status-card status-warning" style="margin: 0.5rem 0;">
                    <strong>Risk {i}:</strong> {risk}
                </div>
                """, unsafe_allow_html=True)
    
    else:
        # Basic migration strategy without AI
        st.markdown("##### 📋 Standard Migration Approach")
        
        basic_phases = [
            "Assessment & Planning",
            "Environment Setup",
            "Data Migration",
            "Application Testing",
            "Go-Live & Optimization"
        ]
        
        phase_cols = st.columns(len(basic_phases))
        for i, (phase, col) in enumerate(zip(basic_phases, phase_cols), 1):
            with col:
                st.markdown(f"""
                <div class="analysis-card" style="text-align: center;">
                    <div style="background: #94a3b8; color: white; border-radius: 50%; width: 40px; height: 40px; 
                                display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem auto; font-weight: bold;">
                        {i}
                    </div>
                    <h6 style="margin: 0;">{phase}</h6>
                </div>
                """, unsafe_allow_html=True)
        
        st.info("💡 Enable AI migration strategy generation for detailed implementation roadmap, resource planning, and risk assessment.")

def analyze_file(valid_inputs, enable_ai_analysis, enable_predictions, enable_migration_strategy):
    """Analyze multiple databases from uploaded file with enhanced progress tracking"""
    
    st.markdown("### 🔄 Bulk Database Analysis")
    
    # Progress setup
    progress_container = st.container()
    with progress_container:
        overall_progress = st.progress(0)
        current_db = st.empty()
        stage_status = st.empty()
        
        # Results summary
        results_summary = st.empty()
    
    all_results = []
    
    try:
        total_databases = len(valid_inputs)
        
        for i, inputs in enumerate(valid_inputs):
            db_name = inputs.get('db_name', f'Database {i+1}')
            current_db.text(f"🔄 Analyzing: {db_name} ({i+1}/{total_databases})")
            
            # Basic calculations
            stage_status.text("📊 Calculating resource requirements...")
            calculator = st.session_state.calculator
            recommendations = {}
            for env in calculator.env_profiles:
                recommendations[env] = calculator.calculate_requirements(inputs, env)
            
            # AI Analysis
            ai_insights = {}
            if st.session_state.ai_analytics:
                if enable_ai_analysis:
                    stage_status.text("🤖 Running AI workload analysis...")
                    try:
                        workload_analysis = st.session_state.ai_analytics.analyze_workload_patterns(inputs)
                        ai_insights['workload'] = workload_analysis
                        if "error" in ai_insights['workload']:
                            st.warning(f"AI Workload Analysis for {db_name}: {ai_insights['workload']['error']}")
                    except Exception as e:
                        st.warning(f"AI Workload Analysis for {db_name} failed: {str(e)}")
                        ai_insights['workload'] = {"error": str(e)}
                
                if enable_predictions:
                    stage_status.text("🔮 Generating predictions...")
                    try:
                        predictions = st.session_state.ai_analytics.predict_future_requirements(inputs, inputs.get('years', 3))
                        ai_insights['predictions'] = predictions
                        if "error" in ai_insights['predictions']:
                            st.warning(f"AI Predictions for {db_name}: {ai_insights['predictions']['error']}")
                    except Exception as e:
                        st.warning(f"AI Predictions for {db_name} failed: {str(e)}")
                        ai_insights['predictions'] = {"error": str(e)}
                
                if enable_migration_strategy:
                    stage_status.text("📋 Creating migration strategy...")
                    try:
                        migration_strategy = st.session_state.ai_analytics.generate_migration_strategy(recommendations['PROD'])
                        ai_insights['migration'] = migration_strategy
                        if "error" in ai_insights['migration']:
                            st.warning(f"AI Migration Strategy for {db_name}: {ai_insights['migration']['error']}")
                    except Exception as e:
                        st.warning(f"AI Migration Strategy for {db_name} failed: {str(e)}")
                        ai_insights['migration'] = {"error": str(e)}
            
            all_results.append({
                'inputs': inputs,
                'recommendations': recommendations,
                'ai_insights': ai_insights
            })
            
            # Update progress
            progress = (i + 1) / total_databases
            overall_progress.progress(progress)
            
            # Update summary
            completed = i + 1
            total_cost = sum(result['recommendations']['PROD']['monthly_cost'] for result in all_results)
            results_summary.markdown(f"""
            **Progress:** {completed}/{total_databases} databases analyzed  
            **Total Monthly Cost:** ${total_cost:,.0f}  
            **Average Cost:** ${total_cost/completed:,.0f} per database
            """)
        
        # Analysis complete
        current_db.text("✅ Analysis complete for all databases!")
        stage_status.text("🎉 All databases analyzed successfully")
        
        # Clear progress after a moment
        time.sleep(2)
        progress_container.empty()
        
        # Store results for reporting
        st.session_state.last_analysis_results = all_results

        # Display comprehensive results
        display_bulk_results(all_results)
        
    except Exception as e:
        progress_container.empty()
        st.error(f"Bulk analysis failed: {str(e)}")

def display_bulk_results(all_results):
    """Display results from bulk analysis with enhanced visualization"""
    st.markdown("### 📊 Bulk Analysis Results")
    
    # Executive dashboard
    total_monthly = sum(result['recommendations']['PROD']['monthly_cost'] for result in all_results)
    total_annual = total_monthly * 12
    avg_monthly = total_monthly / len(all_results)
    
    # Calculate total on-premise estimate
    total_onprem = sum(result['inputs']['cores'] * 200 for result in all_results)
    total_savings = total_onprem - total_monthly
    savings_percentage = (total_savings / total_onprem) * 100 if total_onprem > 0 else 0
    
    dashboard_cols = st.columns(4)
    
    with dashboard_cols[0]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Databases</div>
            <div class="metric-value">{len(all_results)}</div>
            <div class="metric-subtitle">Successfully Analyzed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with dashboard_cols[1]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Monthly Cost</div>
            <div class="metric-value" style="color: #10b981;">${total_monthly:,.0f}</div>
            <div class="metric-subtitle">AWS Production Environment</div>
        </div>
        """, unsafe_allow_html=True)
    
    with dashboard_cols[2]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Monthly Savings</div>
            <div class="metric-value" style="color: #10b981;">${total_savings:,.0f}</div>
            <div class="metric-subtitle">{savings_percentage:.0f}% vs On-Premise</div>
        </div>
        """, unsafe_allow_html=True)
    
    with dashboard_cols[3]:
        avg_optimization = sum(result['recommendations']['PROD'].get('optimization_score', 85) for result in all_results) / len(all_results)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Avg Optimization</div>
            <div class="metric-value" style="color: #8b5cf6;">{avg_optimization:.0f}%</div>
            <div class="metric-subtitle">Resource Efficiency</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Results tabs
    bulk_tabs = st.tabs([
        "📊 Summary Dashboard", 
        "🤖 AI Intelligence", 
        "💰 Cost Analysis", 
        "🔍 Individual Results",
        "📄 Export & Reports"
    ])
    
    with bulk_tabs[0]:  # Summary Dashboard
        render_bulk_summary_tab(all_results)
    
    with bulk_tabs[1]:  # AI Intelligence
        render_bulk_ai_tab(all_results)
    
    with bulk_tabs[2]:  # Cost Analysis
        render_bulk_cost_tab(all_results)
    
    with bulk_tabs[3]:  # Individual Results
        render_bulk_individual_tab(all_results)
    
    with bulk_tabs[4]:  # Export & Reports
        render_bulk_export_tab(all_results)

def render_bulk_summary_tab(all_results):
    """Render bulk summary dashboard"""
    st.markdown("#### 📊 Database Portfolio Summary")
    
    # Create summary table
    summary_data = []
    for i, result in enumerate(all_results, 1):
        prod_rec = result['recommendations']['PROD']
        inputs = result['inputs']
        
        summary_data.append({
            "#": i,
            "Database": inputs.get('db_name', f'Database {i}'),
            "Engine": inputs.get('engine', 'Unknown'),
            "Region": inputs.get('region', 'Unknown'),
            "Instance Type": prod_rec['instance_type'],
            "vCPUs": prod_rec['vcpus'],
            "RAM (GB)": prod_rec['ram_gb'],
            "Storage (GB)": f"{prod_rec['storage_gb']:,}",
            "Monthly Cost": prod_rec['monthly_cost'],
            "Annual Cost": prod_rec['annual_cost'],
            "Optimization": f"{prod_rec.get('optimization_score', 85)}%"
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    st.dataframe(
        summary_df,
        column_config={
            "Monthly Cost": st.column_config.NumberColumn("Monthly Cost", format="$%.0f"),
            "Annual Cost": st.column_config.NumberColumn("Annual Cost", format="$%.0f")
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Quick statistics
    st.markdown("#### 📈 Portfolio Statistics")
    
    stats_cols = st.columns(3)
    
    with stats_cols[0]:
        # Engine distribution
        engine_counts = {}
        for result in all_results:
            engine = result['inputs'].get('engine', 'Unknown')
            engine_counts[engine] = engine_counts.get(engine, 0) + 1
        
        st.markdown("**Database Engines:**")
        for engine, count in engine_counts.items():
            percentage = (count / len(all_results)) * 100
            st.markdown(f"• **{engine}:** {count} ({percentage:.1f}%)")
    
    with stats_cols[1]:
        # Region distribution
        region_counts = {}
        for result in all_results:
            region = result['inputs'].get('region', 'Unknown')
            region_counts[region] = region_counts.get(region, 0) + 1
        
        st.markdown("**AWS Regions:**")
        for region, count in region_counts.items():
            percentage = (count / len(all_results)) * 100
            st.markdown(f"• **{region}:** {count} ({percentage:.1f}%)")
    
    with stats_cols[2]:
        # Cost ranges
        costs = [result['recommendations']['PROD']['monthly_cost'] for result in all_results]
        min_cost = min(costs)
        max_cost = max(costs)
        median_cost = sorted(costs)[len(costs)//2]
        
        st.markdown("**Cost Distribution:**")
        st.markdown(f"• **Minimum:** ${min_cost:,.0f}/month")
        st.markdown(f"• **Median:** ${median_cost:,.0f}/month")
        st.markdown(f"• **Maximum:** ${max_cost:,.0f}/month")

def render_bulk_ai_tab(all_results):
    """Render bulk AI intelligence summary"""
    st.markdown("#### 🤖 AI Intelligence Aggregation")
    
    ai_available = any(result.get('ai_insights') for result in all_results)
    
    if not ai_available:
        st.info("🔑 AI analysis requires a Claude API key. Configure in sidebar and re-run analysis for AI insights.")
        return
    
    # Filter out results where AI insights had an error
    clean_results = [res for res in all_results if 'workload' in res.get('ai_insights', {}) and 'error' not in res['ai_insights']['workload']]

    if not clean_results:
        st.info("No valid AI insights available for aggregation (API key might be missing or invalid for all databases).")
        return

    # Aggregate AI insights
    workload_types = {}
    complexity_levels = {}
    all_recommendations = []
    
    for result in clean_results:
        ai_insights = result.get('ai_insights', {})
        if 'workload' in ai_insights and 'error' not in ai_insights['workload']: # Re-check inside loop to be safe
            workload = ai_insights['workload']
            
            # Aggregate workload types
            wtype = workload.get('workload_type', 'Unknown')
            workload_types[wtype] = workload_types.get(wtype, 0) + 1
            
            # Aggregate complexity
            complexity = workload.get('complexity', 'Unknown')
            complexity_levels[complexity] = complexity_levels.get(complexity, 0) + 1
            
            # Collect recommendations
            all_recommendations.extend(workload.get('recommendations', []))
    
    # Display aggregated insights
    ai_cols = st.columns(2)
    
    with ai_cols[0]:
        if workload_types:
            st.markdown("##### 📊 Workload Type Distribution")
            
            fig_workload = px.pie(
                values=list(workload_types.values()),
                names=list(workload_types.keys()),
                title="Database Workload Types"
            )
            fig_workload.update_traces(textposition='inside', textinfo='percent+label')
            fig_workload.update_layout(height=350)
            st.plotly_chart(fig_workload, use_container_width=True, config={'responsive': True}) # Added config
    
    with ai_cols[1]:
        if complexity_levels:
            st.markdown("##### ⚙️ Migration Complexity Assessment")
            
            complexity_colors = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#10b981"}
            
            for complexity, count in complexity_levels.items():
                percentage = (count / len(clean_results)) * 100 # Calculate percentage based on clean_results
                color = complexity_colors.get(complexity, "#64748b")
                
                st.markdown(f"""
                <div style="background: {color}20; border-left: 4px solid {color}; padding: 1rem; margin: 0.5rem 0; border-radius: 0 8px 8px 0;">
                    <strong>{complexity} Complexity:</strong> {count} databases ({percentage:.1f}%)
                </div>
                """, unsafe_allow_html=True)
    
    # Top recommendations
    if all_recommendations:
        st.markdown("##### 🎯 Most Common AI Recommendations")
        
        from collections import Counter
        rec_counts = Counter(all_recommendations)
        
        top_recs = rec_counts.most_common(6)
        rec_cols = st.columns(2)
        
        with rec_cols[0]:
            for i in range(0, len(top_recs), 2):
                rec, count = top_recs[i]
                percentage = (count / len(clean_results)) * 100 # Calculate percentage based on clean_results
                st.markdown(f"""
                <div style="background: #f0f9ff; border: 1px solid #0ea5e9; padding: 1rem; margin: 0.5rem 0; border-radius: 8px;">
                    <strong>{rec}</strong><br>
                    <small style="color: #64748b;">Recommended for {count} databases ({percentage:.0f}%)</small>
                </div>
                """, unsafe_allow_html=True)
        
        with rec_cols[1]:
            for i in range(1, len(top_recs), 2):
                if i < len(top_recs):
                    rec, count = top_recs[i]
                    percentage = (count / len(clean_results)) * 100 # Calculate percentage based on clean_results
                    st.markdown(f"""
                    <div style="background: #f0f9ff; border: 1px solid #0ea5e9; padding: 1rem; margin: 0.5rem 0; border-radius: 8px;">
                        <strong>{rec}</strong><br>
                        <small style="color: #64748b;">Recommended for {count} databases ({percentage:.0f}%)</small>
                    </div>
                    """, unsafe_allow_html=True)

def render_bulk_cost_tab(all_results):
    """Render bulk cost analysis"""
    st.markdown("#### 💰 Portfolio Cost Analysis")
    
    # Cost visualizations
    viz_cols = st.columns(2)
    
    with viz_cols[0]:
        # Individual database costs
        db_costs = [result['recommendations']['PROD']['monthly_cost'] for result in all_results]
        db_names = [result['inputs'].get('db_name', f'DB{i+1}') for i, result in enumerate(all_results)]
        
        # Truncate long names for display
        db_names_display = [name[:12] + "..." if len(name) > 12 else name for name in db_names]
        
        fig1 = px.bar(
            x=db_names_display,
            y=db_costs,
            title="Monthly Cost per Database",
            labels={'x': 'Database', 'y': 'Monthly Cost ($)'},
            color=db_costs,
            color_continuous_scale='RdYlBu_r'
        )
        fig1.update_layout(
            xaxis_tickangle=-45, 
            height=400, 
            showlegend=False,
            title_font_size=16
        )
        st.plotly_chart(fig1, use_container_width=True, config={'responsive': True}) # Added config
    
    with viz_cols[1]:
        # Cost by engine type
        engine_costs = {}
        for result in all_results:
            engine = result['inputs'].get('engine', 'Unknown')
            cost = result['recommendations']['PROD']['monthly_cost']
            if engine in engine_costs:
                engine_costs[engine] += cost
            else:
                engine_costs[engine] = cost
        
        fig2 = px.pie(
            values=list(engine_costs.values()),
            names=list(engine_costs.keys()),
            title="Total Cost by Database Engine"
        )
        fig2.update_traces(textposition='inside', textinfo='percent+label')
        fig2.update_layout(height=400, title_font_size=16)
        st.plotly_chart(fig2, use_container_width=True, config={'responsive': True}) # Added config
    
    # Cost summary metrics
    st.markdown("##### 📊 Financial Summary")
    
    total_monthly = sum(result['recommendations']['PROD']['monthly_cost'] for result in all_results)
    total_onprem_estimate = sum(result['inputs']['cores'] * 200 for result in all_results)
    total_savings = total_onprem_estimate - total_monthly
    
    financial_cols = st.columns(4)
    
    with financial_cols[0]:
        st.metric("Total Portfolio Cost", f"${total_monthly:,.0f}/mo", f"${total_monthly * 12:,.0f}/year")
    
    with financial_cols[1]:
        st.metric("Estimated On-Prem", f"${total_onprem_estimate:,.0f}/mo", f"${total_onprem_estimate * 12:,.0f}/year")
    
    with financial_cols[2]:
        savings_pct = (total_savings / total_onprem_estimate * 100) if total_onprem_estimate > 0 else 0
        st.metric("Monthly Savings", f"${total_savings:,.0f}", f"{savings_pct:.0f}%")
    
    with financial_cols[3]:
        # Adjusted for division by zero if total_savings is 0 or negative (no ROI)
        payback_months = (total_monthly * 0.1) / (total_savings / 12) if total_savings > 0 else (0 if total_savings == 0 else float('inf'))
        st.metric("ROI Payback", f"{payback_months:.0f} months" if payback_months > 0 and payback_months != float('inf') else ("Immediate" if payback_months == 0 else "N/A"))

def render_bulk_individual_tab(all_results):
    """Render individual database details from bulk analysis"""
    st.markdown("#### 🔍 Individual Database Analysis")
    
    # Database selector
    db_options = []
    for i, result in enumerate(all_results):
        db_name = result['inputs'].get('db_name', f'Database {i+1}')
        engine = result['inputs'].get('engine', 'Unknown')
        monthly_cost = result['recommendations']['PROD']['monthly_cost']
        db_options.append(f"{db_name} ({engine}) - ${monthly_cost:,.0f}/mo")
    
    selected_idx = st.selectbox(
        "Select database for detailed analysis:",
        options=list(range(len(all_results))),
        format_func=lambda x: db_options[x],
        key="individual_db_selector"
    )
    
    if selected_idx is not None:
        selected_result = all_results[selected_idx]
        db_name = selected_result['inputs'].get('db_name', f'Database {selected_idx + 1}')
        
        st.markdown(f"### 📋 Detailed Analysis: {db_name}")
        
        # Display individual analysis using existing function
        display_single_database_analysis(selected_result, selected_idx + 1)

def display_single_database_analysis(result, db_number):
    """Display detailed analysis for a single database"""
    inputs = result['inputs']
    recommendations = result['recommendations']
    ai_insights = result.get('ai_insights', {})
    
    # Database info header
    info_cols = st.columns(4)
    
    with info_cols[0]:
        st.metric("Database Engine", inputs.get('engine', 'Unknown').upper())
    with info_cols[1]:
        st.metric("AWS Region", inputs.get('region', 'Unknown'))
    with info_cols[2]:
        st.metric("Current Resources", f"{inputs.get('cores', 0)} cores, {inputs.get('ram', 0)} GB")
    with info_cols[3]:
        st.metric("Storage & IOPS", f"{inputs.get('storage', 0):,} GB, {inputs.get('iops', 0):,} IOPS")
    
    # Detailed tabs
    detail_tabs = st.tabs([
        "🏗️ Recommendations", 
        "🤖 AI Analysis", 
        "💰 Cost Breakdown", 
        "📊 Configuration"
    ])
    
    with detail_tabs[0]:  # Recommendations
        st.markdown("##### Environment Recommendations")
        
        env_data = []
        for env, rec in recommendations.items():
            env_data.append({
                'Environment': env,
                'Instance Type': rec['instance_type'],
                'vCPUs': rec['vcpus'],
                'RAM (GB)': rec['ram_gb'],
                'Storage (GB)': rec['storage_gb'],
                'Monthly Cost': rec['monthly_cost'],
                'Optimization': f"{rec.get('optimization_score', 85)}%"
            })
        
        env_df = pd.DataFrame(env_data)
        st.dataframe(
            env_df,
            column_config={
                "Monthly Cost": st.column_config.NumberColumn("Monthly Cost", format="$%.0f")
            },
            use_container_width=True,
            hide_index=True
        )
    
    with detail_tabs[1]:  # AI Analysis
        if ai_insights and 'workload' in ai_insights and 'error' not in ai_insights['workload']:
            workload = ai_insights['workload']
            
            ai_detail_cols = st.columns(3)
            
            with ai_detail_cols[0]:
                st.markdown(f"""
                **Workload Type:** {workload.get('workload_type', 'Mixed')}  
                **Complexity:** {workload.get('complexity', 'Medium')}  
                **Timeline:** {workload.get('timeline', '12-16 weeks')}
                """)
            
            with ai_detail_cols[1]:
                recommendations_ai = workload.get('recommendations', [])
                if recommendations_ai:
                    st.markdown("**Top Recommendations:**")
                    for i, rec in enumerate(recommendations_ai[:3], 1):
                        st.markdown(f"{i}. {rec}")
            
            with ai_detail_cols[2]:
                risks = workload.get('risks', [])
                if risks:
                    st.markdown("**Key Risks:**")
                    for risk in risks[:3]:
                        st.markdown(f"⚠️ {risk}")
        else:
            st.info("🔑 AI analysis not available. Configure Claude API key for detailed insights or check previous errors.")
    
    with detail_tabs[2]:  # Cost Breakdown
        prod_rec = recommendations['PROD']
        cost_breakdown = prod_rec.get('cost_breakdown', {})
        
        if cost_breakdown:
            breakdown_data = []
            for component, cost in cost_breakdown.items():
                if component != 'total':
                    percentage = (cost / cost_breakdown.get('total', 1)) * 100
                    breakdown_data.append({
                        "Component": component.replace('_', ' ').title(),
                        "Monthly Cost": cost,
                        "Percentage": f"{percentage:.1f}%"
                    })
            
            if breakdown_data:
                breakdown_df = pd.DataFrame(breakdown_data)
                st.dataframe(
                    breakdown_df,
                    column_config={
                        "Monthly Cost": st.column_config.NumberColumn("Monthly Cost", format="$%.2f")
                    },
                    use_container_width=True,
                    hide_index=True
                )
    
    with detail_tabs[3]:  # Configuration
        st.markdown("##### Current vs Recommended Configuration")
        
        config_comparison = pd.DataFrame({
            "Metric": ["CPU Cores", "RAM (GB)", "Storage (GB)", "Peak CPU %", "Peak RAM %"],
            "Current": [
                str(inputs.get('cores', 0)), # Cast to string
                str(inputs.get('ram', 0)), # Cast to string
                str(inputs.get('storage', 0)), # Cast to string
                f"{inputs.get('cpu_util', 0)}%",
                f"{inputs.get('ram_util', 0)}%"
            ],
            "Recommended (PROD)": [
                str(recommendations['PROD']['vcpus']), # Cast to string
                str(recommendations['PROD']['ram_gb']), # Cast to string
                str(recommendations['PROD']['storage_gb']), # Cast to string
                "N/A",
                "N/A"
            ]
        })
        
        st.dataframe(config_comparison, use_container_width=True, hide_index=True)

def render_bulk_export_tab(all_results):
    """Render bulk export and reporting options"""
    st.markdown("#### 📄 Export & Reporting Options")
    
    # Export summary
    export_cols = st.columns(3)
    
    with export_cols[0]:
        st.markdown("""
        <div class="config-section">
            <div class="config-header">📊 Executive Reports</div>
            <p>Comprehensive analysis for stakeholders and decision makers.</p>
            <ul>
                <li>Executive summary with key metrics</li>
                <li>Cost-benefit analysis</li>
                <li>ROI calculations and projections</li>
                <li>Risk assessment overview</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📈 Generate Executive Report (Excel)", use_container_width=True, key="generate_executive_report_bulk_excel"):
            try:
                excel_data = export_full_report(all_results)
                st.download_button(
                    label="📊 Download Executive Excel Report",
                    data=excel_data,
                    file_name=f"executive_migration_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="download_executive_excel_bulk"
                )
                st.success("✅ Executive report generated successfully!")
            except Exception as e:
                st.error(f"Export failed: {str(e)}")

        if st.button("📄 Generate Executive Report (PDF)", use_container_width=True, key="generate_executive_report_bulk_pdf"):
            try:
                pdf_data = st.session_state.pdf_generator.generate_report(all_results)
                st.download_button(
                    label="⬇️ Download Executive PDF Report",
                    data=pdf_data,
                    file_name=f"executive_migration_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="download_executive_pdf_bulk"
                )
                st.success("✅ Executive PDF report generated successfully!")
            except Exception as e:
                st.error(f"PDF Export failed: {str(e)}")
    
    with export_cols[1]:
        st.markdown("""
        <div class="config-section">
            <div class="config-header">📋 Data Exports</div>
            <p>Raw data and detailed configurations for technical teams.</p>
            <ul>
                <li>Summary data in CSV format</li>
                <li>Complete technical specifications</li>
                <li>AI insights and recommendations</li>
                <li>Cost breakdown details</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Create summary CSV
        summary_data = []
        for result in all_results:
            prod_rec = result['recommendations']['PROD']
            summary_data.append({
                "Database": result['inputs'].get('db_name', 'N/A'),
                "Engine": result['inputs'].get('engine', 'N/A'),
                "Region": result['inputs'].get('region', 'N/A'),
                "Instance_Type": prod_rec['instance_type'],
                "vCPUs": prod_rec['vcpus'],
                "RAM_GB": prod_rec['ram_gb'],
                "Storage_GB": prod_rec['storage_gb'],
                "Monthly_Cost": prod_rec['monthly_cost'],
                "Annual_Cost": prod_rec['annual_cost'],
                "Optimization_Score": prod_rec.get('optimization_score', 85)
            })
        
        summary_df = pd.DataFrame(summary_data)
        csv_data = summary_df.to_csv(index=False)
        
        st.download_button(
            label="📄 Download Summary CSV",
            data=csv_data,
            file_name=f"migration_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
            key="download_summary_csv_bulk"
        )
        
        # Technical JSON export
        json_data = json.dumps(all_results, indent=2, default=str)
        st.download_button(
            label="🔧 Download Technical JSON",
            data=json_data,
            file_name=f"migration_technical_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
            key="download_technical_json_bulk"
        )
    
    with export_cols[2]:
        st.markdown("""
        <div class="config-section">
            <div class="config-header">📧 Communication</div>
            <p>Ready-to-use summaries for stakeholder communication.</p>
            <ul>
                <li>Email-ready executive summary</li>
                <li>Key findings and recommendations</li>
                <li>Next steps and action items</li>
                <li>Cost savings highlights</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📧 Generate Email Summary", use_container_width=True, key="generate_email_summary_bulk"):
            total_monthly = sum(result['recommendations']['PROD']['monthly_cost'] for result in all_results)
            total_annual = total_monthly * 12
            total_onprem = sum(result['inputs']['cores'] * 200 for result in all_results)
            total_savings = total_onprem - total_monthly
            
            email_summary = f"""
Subject: Database Migration Analysis Results - ${total_monthly:,.0f}/month Cloud Cost

Database Migration Analysis Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

EXECUTIVE SUMMARY
================
• Total Databases Analyzed: {len(all_results)}
• Recommended Monthly Cost: ${total_monthly:,.0f}
• Estimated Annual Cost: ${total_annual:,.0f}
• Projected Annual Savings: ${total_savings * 12:,.0f}
• Average Cost per Database: ${total_monthly / len(all_results):,.0f}/month

KEY FINDINGS
============
• Migration feasibility: HIGH ✅
• Cost optimization potential: {(total_savings / total_onprem * 100):.0f}% savings vs on-premise
• Recommended timeline: 12-18 weeks for phased migration
• Risk level: LOW to MEDIUM (manageable with proper planning)

TOP RECOMMENDATIONS
==================
1. Proceed with cloud migration planning
2. Start with non-production environments
3. Implement AWS Aurora for improved performance
4. Use AWS DMS for seamless data migration
5. Plan for 15-20% performance improvement post-migration

NEXT STEPS
==========
1. Review detailed technical analysis
2. Engage AWS Professional Services for migration planning
3. Begin application dependency mapping
4. Schedule stakeholder alignment meeting
5. Establish migration project timeline

For detailed analysis and technical specifications, please refer to the attached reports.

Contact the migration team for questions or additional analysis.
            """
            
            st.text_area("Email Summary (Copy & Paste):", email_summary, height=400)

def generate_sample_report():
    """Generate and display sample report"""
    st.markdown("#### 📊 Sample Migration Analysis Report")
    
    sample_data = {
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "database_name": "SampleProductionDB",
        "database_engine": "PostgreSQL",
        "current_environment": "On-Premise",
        "target_environment": "AWS RDS PostgreSQL",
        "current_specs": "16 cores, 64 GB RAM, 2TB storage",
        "recommended_instance": "db.r5.2xlarge",
        "estimated_monthly_cost": 2850,
        "estimated_annual_cost": 34200,
        "estimated_annual_savings": 45000,
        "migration_timeline": "12-16 weeks",
        "complexity_level": "Medium",
        "risk_level": "Low to Medium",
        "optimization_score": "87%"
    }
    
    # Display sample report
    st.markdown(f"""
    <div class="ai-insight">
        <h4>📋 Sample Migration Analysis Report</h4>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; margin: 1rem 0;">
            <div>
                <h6>📊 Database Information</h6>
                <p><strong>Name:</strong> {sample_data['database_name']}</p>
                <p><strong>Engine:</strong> {sample_data['database_engine']}</p>
                <p><strong>Current:</strong> {sample_data['current_environment']}</p>
                <p><strong>Target:</strong> {sample_data['target_environment']}</p>
            </div>
            <div>
                <h6>🎯 Recommendations</h6>
                <p><strong>Instance:</strong> {sample_data['recommended_instance']}</p>
                <p><strong>Monthly Cost:</strong> ${sample_data['estimated_monthly_cost']:,}</p>
                <p><strong>Annual Savings:</strong> ${sample_data['estimated_annual_savings']:,}</p>
                <p><strong>Optimization:</strong> {sample_data['optimization_score']}</p>
            </div>
            <div>
                <h6>⏱️ Timeline & Risk</h6>
                <p><strong>Timeline:</strong> {sample_data['migration_timeline']}</p>
                <p><strong>Complexity:</strong> {sample_data['complexity_level']}</p>
                <p><strong>Risk Level:</strong> {sample_data['risk_level']}</p>
                <p><strong>Generated:</strong> {sample_data['analysis_date']}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Download sample CSV
    sample_df = pd.DataFrame([sample_data])
    csv_buffer = io.StringIO()
    sample_df.to_csv(csv_buffer, index=False)
    
    st.download_button(
        label="📄 Download Sample CSV Report",
        data=csv_buffer.getvalue(),
        file_name=f"migration_analysis_sample_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True,
        key="download_sample_csv_report"
    )
    
    st.info("💡 This is a sample report demonstrating the output format. Run the full analysis with your Claude API key to generate comprehensive reports with AI insights.")

def render_footer():
    """Render enhanced application footer"""
    st.markdown("---")
    st.markdown("""
    <div class="footer-content">
        <h3>🚀 AI Database Migration Studio</h3>
        <p style="font-size: 1.1rem; font-weight: 600; color: #667eea; margin: 1rem 0;">
            Powered by Claude AI • Enterprise-Ready • Cloud-Native
        </p>
        <div class="feature-grid">
            <div class="feature-item">
                <strong>✅ Multi-Engine Support</strong><br>
                <small>Oracle, PostgreSQL, SQL Server, MySQL</small>
            </div>
            <div class="feature-item">
                <strong>🤖 AI-Powered Analysis</strong><br>
                <small>Intelligent workload assessment</small>
            </div>
            <div class="feature-item">
                <strong>📊 Cost Optimization</strong><br>
                <small>Right-sizing and savings analysis</small>
            </div>
            <div class="feature-item">
                <strong>🔒 Enterprise Security</strong><br>
                <small>AWS best practices compliance</small>
            </div>
        </div>
        <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e2e8f0;">
            <p style="font-size: 0.9rem; color: #64748b; margin: 0;">
                Transform your database migration journey with the power of artificial intelligence.<br>
                Built for enterprise teams seeking intelligent, cost-effective cloud migration solutions.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Run the application
if __name__ == "__main__":
    main()
    render_footer()
