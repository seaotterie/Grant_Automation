"""
Real Data AI Processor Testing Framework
Tests all 4 AI processors with live OpenAI API calls and comprehensive logging.
Organized by tab with complete input/output capture for validation.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass, asdict

# Cost tracking and safety controls
@dataclass
class CostControls:
    max_total_test_cost: float = 5.00
    max_cost_per_processor: float = 1.25
    token_limits: Dict[str, int] = None
    timeout_seconds: int = 300  # Increased to 5 minutes for APPROACH tab complexity
    retry_attempts: int = 2
    
    def __post_init__(self):
        if self.token_limits is None:
            self.token_limits = {
                "gpt-5-nano": 4000,
                "gpt-5-mini": 8000,  # Increased for comprehensive analysis
            }

@dataclass
class ProcessorMetrics:
    processor_name: str
    tab_name: str
    cost_usd: float
    tokens_used: int
    response_time_seconds: float
    success: bool
    api_calls: int
    retry_count: int
    timestamp: str
    error_message: Optional[str] = None

class CostTracker:
    """Tracks API costs and enforces budget limits"""
    
    def __init__(self, max_budget: float = 5.00):
        self.max_budget = max_budget
        self.total_cost = 0.0
        self.processor_costs = {}
        self.controls = CostControls()
    
    def check_budget_available(self, estimated_cost: float, processor_name: str) -> bool:
        """Check if we have budget for the estimated cost"""
        if self.total_cost + estimated_cost > self.max_budget:
            return False
        
        processor_total = self.processor_costs.get(processor_name, 0.0)
        if processor_total + estimated_cost > self.controls.max_cost_per_processor:
            return False
            
        return True
    
    def record_cost(self, cost: float, processor_name: str):
        """Record actual cost after API call"""
        self.total_cost += cost
        self.processor_costs[processor_name] = self.processor_costs.get(processor_name, 0.0) + cost
    
    def get_remaining_budget(self) -> float:
        return max(0.0, self.max_budget - self.total_cost)

class ResultsLogger:
    """Captures and saves all AI interactions for review"""
    
    def __init__(self, results_dir: str = "test_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.results_dir / self.session_id
        self.session_dir.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.session_dir / "test_log.txt"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("RealDataAITester")
    
    def save_input_package(self, tab_name: str, processor_name: str, input_data: Dict[str, Any]):
        """Save complete AI input package"""
        filename = f"processor_input_{tab_name.lower()}.json"
        filepath = self.session_dir / filename
        
        package = {
            "processor": processor_name,
            "tab": tab_name,
            "timestamp": datetime.now().isoformat(),
            "input_data": input_data,
            "session_id": self.session_id
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(package, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved input package: {filename}")
    
    def save_ai_prompt(self, tab_name: str, prompt: str):
        """Save raw AI prompt"""
        filename = f"processor_prompt_{tab_name.lower()}.txt"
        filepath = self.session_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"=== AI PROMPT FOR {tab_name} TAB ===\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Session: {self.session_id}\n")
            f.write("=" * 50 + "\n\n")
            f.write(prompt)
        
        self.logger.info(f"Saved AI prompt: {filename}")
    
    def save_ai_response(self, tab_name: str, response: Dict[str, Any]):
        """Save raw AI response"""
        filename = f"processor_response_{tab_name.lower()}.json"
        filepath = self.session_dir / filename
        
        response_package = {
            "tab": tab_name,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "raw_response": response
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(response_package, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved AI response: {filename}")
    
    def save_processed_output(self, tab_name: str, output: Dict[str, Any]):
        """Save final processed output"""
        filename = f"processor_output_{tab_name.lower()}.json"
        filepath = self.session_dir / filename
        
        output_package = {
            "tab": tab_name,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "processed_output": output
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_package, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved processed output: {filename}")
    
    def save_metrics(self, metrics: ProcessorMetrics):
        """Save performance metrics"""
        filename = "test_metrics.json"
        filepath = self.session_dir / filename
        
        # Load existing metrics or create new
        if filepath.exists():
            with open(filepath, 'r') as f:
                all_metrics = json.load(f)
        else:
            all_metrics = {"session_id": self.session_id, "metrics": []}
        
        all_metrics["metrics"].append(asdict(metrics))
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(all_metrics, f, indent=2)
        
        self.logger.info(f"Saved metrics for {metrics.processor_name}")

class RealDataAITester:
    """Main testing framework for AI processors with real data"""
    
    def __init__(self):
        self.cost_tracker = CostTracker(max_budget=5.00)
        self.results_logger = ResultsLogger("test_results")
        self.test_data = self._load_test_data()
        self.processors = self._get_processor_configs()
        
        # OpenAI API configuration - LIVE API MODE
        self.simulate_api = False  # Set to True for simulation mode
        
        # Initialize OpenAI client
        try:
            import openai
            import os
            
            # Load environment variables from .env file
            try:
                from dotenv import load_dotenv
                load_dotenv()
                print("[INFO] Loaded environment variables from .env file")
            except ImportError:
                print("[INFO] python-dotenv not available, using system environment variables")
            
            # Get API key from environment or prompt user
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("\n[WARNING] OpenAI API key not found in environment variables.")
                print("Please provide your OpenAI API key (starts with 'sk-'):")
                api_key = input("API Key: ").strip()
                
                if not api_key or not api_key.startswith('sk-'):
                    raise ValueError("Invalid OpenAI API key. Key should start with 'sk-'")
                
                print("[SUCCESS] API key provided. Setting for this session...")
            
            self.openai_client = openai.OpenAI(api_key=api_key)
            self.results_logger.logger.info("[SUCCESS] OpenAI API client initialized successfully")
            
        except ImportError:
            self.results_logger.logger.error("[ERROR] OpenAI library not installed. Run: pip install openai")
            raise
        except Exception as e:
            self.results_logger.logger.error(f"[ERROR] OpenAI API initialization failed: {e}")
            raise
        
        self.results_logger.logger.info("=== Real Data AI Processor Testing Started ===")
        self.results_logger.logger.info(f"Budget: ${self.cost_tracker.max_budget}")
        self.results_logger.logger.info(f"Test data loaded: {len(self.test_data)} entities")
    
    def _load_test_data(self) -> Dict[str, Any]:
        """Load real test data from the system"""
        test_data = {}
        
        # Load real nonprofit data - Grantmakers In Aging Inc
        nonprofit_path = Path("data/source_data/nonprofits/134014982/propublica.json")
        if nonprofit_path.exists():
            with open(nonprofit_path, 'r') as f:
                test_data['nonprofit'] = json.load(f)
            self.results_logger.logger.info("Loaded nonprofit data: Grantmakers In Aging Inc")
        else:
            # Fallback test data
            test_data['nonprofit'] = {
                "organization": {
                    "ein": 134014982,
                    "name": "Grantmakers In Aging Inc",
                    "city": "Arlington",
                    "state": "VA",
                    "ntee_code": "P81",
                    "revenue_amount": 2208858,
                    "asset_amount": 2481115
                }
            }
            self.results_logger.logger.warning("Using fallback nonprofit data")
        
        # Load real government opportunity data
        opportunity_path = Path("data/source_data/government/opportunities/TEST-GRANTS-2024-001/grants_gov_data.json")
        if opportunity_path.exists():
            with open(opportunity_path, 'r') as f:
                test_data['opportunity'] = json.load(f)
            self.results_logger.logger.info("Loaded opportunity data: TEST-GRANTS-2024-001")
        else:
            # Fallback test data
            test_data['opportunity'] = {
                "data": {
                    "opportunity_id": "TEST-GRANTS-2024-001",
                    "funding_opportunity_title": "Test Grant Program",
                    "agency_code": "DOE",
                    "funding_instrument_type": "Grant",
                    "category_of_funding_activity": "Environment",
                    "eligibility": {"codes": ["25"]}
                }
            }
            self.results_logger.logger.warning("Using fallback opportunity data")
        
        return test_data
    
    def _get_processor_configs(self) -> Dict[str, Dict[str, Any]]:
        """Define processor configurations by tab"""
        return {
            "PLAN": {
                "name": "ai_lite_unified_processor",
                "file": "src/processors/analysis/ai_lite_unified_processor.py",
                "model": "gpt-5-mini",
                "estimated_cost": 0.010,
                "purpose": "Comprehensive opportunity screening and strategic assessment"
            },
            "ANALYZE": {
                "name": "ai_heavy_light_analyzer", 
                "file": "src/processors/analysis/ai_heavy_light_analyzer.py",
                "model": "gpt-5-mini",
                "estimated_cost": 0.04,
                "purpose": "Enhanced screening and intelligent filtering with comprehensive evaluation"
            },
            "EXAMINE": {
                "name": "ai_heavy_deep_researcher",
                "file": "src/processors/analysis/ai_heavy_deep_researcher.py", 
                "model": "gpt-5-mini",
                "estimated_cost": 0.15,
                "purpose": "Comprehensive strategic intelligence and relationship analysis"
            },
            "APPROACH": {
                "name": "ai_heavy_researcher",
                "file": "src/processors/analysis/ai_heavy_researcher.py",
                "model": "gpt-5-mini",
                "estimated_cost": 0.20,
                "purpose": "Grant application decision-making and implementation planning"
            }
        }
    
    def _simulate_openai_api_call(self, prompt: str, model: str, tab_name: str) -> Dict[str, Any]:
        """Simulate OpenAI API call for testing (replace with real API)"""
        
        # Simulate processing time
        time.sleep(2)
        
        # Simulate different responses by tab
        if tab_name == "PLAN":
            response_content = {
                "viability_score": 78,
                "recommendation": "pursue",
                "key_insights": [
                    "Strong alignment with nonprofit's aging focus",
                    "DOE environmental grants match sustainability goals",
                    "Financial capacity appears adequate"
                ],
                "risk_flags": ["Limited environmental expertise"],
                "confidence": 0.82
            }
        elif tab_name == "ANALYZE":
            response_content = {
                "strategic_alignment": 85,
                "competitive_advantage": "Unique aging + environment niche",
                "resource_requirements": {
                    "staff": "2-3 FTE",
                    "budget": "$150,000-200,000",
                    "timeline": "18 months"
                },
                "success_probability": 0.73
            }
        elif tab_name == "EXAMINE":
            response_content = {
                "comprehensive_analysis": "Deep research shows strong potential...",
                "risk_matrix": {
                    "technical": "medium",
                    "financial": "low", 
                    "regulatory": "high"
                },
                "implementation_roadmap": ["Phase 1: Team building", "Phase 2: Pilot program"],
                "market_analysis": "Limited competition in aging-environment intersection"
            }
        else:  # APPROACH
            response_content = {
                "implementation_strategy": "Phased approach with early wins...",
                "detailed_timeline": "12-month implementation with 6 milestones",
                "resource_allocation": {"personnel": 60, "equipment": 25, "overhead": 15},
                "success_metrics": ["participant satisfaction", "environmental impact"],
                "risk_mitigation": "Comprehensive risk management plan"
            }
        
        return {
            "content": json.dumps(response_content, indent=2),
            "usage": {
                "prompt_tokens": len(prompt) // 4,  # Rough token estimation
                "completion_tokens": len(str(response_content)) // 4,
                "total_tokens": (len(prompt) + len(str(response_content))) // 4
            },
            "model": model
        }
    
    def test_processor_by_tab(self, tab_name: str, previous_results: Optional[Dict] = None) -> Dict[str, Any]:
        """Test individual processor with complete logging"""
        
        processor_config = self.processors[tab_name]
        processor_name = processor_config["name"]
        
        self.results_logger.logger.info(f"\n=== Testing {tab_name} Tab - {processor_name} ===")
        
        # Check budget
        estimated_cost = processor_config["estimated_cost"]
        if not self.cost_tracker.check_budget_available(estimated_cost, processor_name):
            error_msg = f"Insufficient budget for {processor_name}. Remaining: ${self.cost_tracker.get_remaining_budget():.4f}"
            self.results_logger.logger.error(error_msg)
            return {"error": error_msg, "success": False}
        
        start_time = time.time()
        
        try:
            # Prepare input data
            input_data = self._prepare_input_data(tab_name, previous_results)
            self.results_logger.save_input_package(tab_name, processor_name, input_data)
            
            # Generate AI prompt
            prompt = self._generate_ai_prompt(tab_name, input_data)
            self.results_logger.save_ai_prompt(tab_name, prompt)
            
            # Make API call (simulated or real)
            if self.simulate_api:
                api_response = self._simulate_openai_api_call(prompt, processor_config["model"], tab_name)
            else:
                # Real OpenAI API call
                api_response = self._make_real_openai_api_call(prompt, processor_config["model"], tab_name)
            
            self.results_logger.save_ai_response(tab_name, api_response)
            
            # Process response
            processed_output = self._process_ai_response(tab_name, api_response)
            self.results_logger.save_processed_output(tab_name, processed_output)
            
            # Calculate metrics
            end_time = time.time()
            response_time = end_time - start_time
            
            # Calculate actual cost based on OpenAI pricing (as of 2024)
            usage = api_response["usage"]
            prompt_tokens = usage["prompt_tokens"]
            completion_tokens = usage["completion_tokens"]
            
            if processor_config["model"] == "gpt-5-nano":
                # GPT-5-nano: Estimated pricing (fallback to GPT-4o-mini if not available)
                cost = (prompt_tokens * 0.00015 / 1000) + (completion_tokens * 0.0006 / 1000)
            elif processor_config["model"] == "gpt-5-mini":
                # GPT-5-mini: Estimated pricing (fallback to GPT-4o if not available)
                cost = (prompt_tokens * 0.005 / 1000) + (completion_tokens * 0.015 / 1000)
            else:  # Default to gpt-5-nano for unknown models
                # GPT-5-nano: $0.00025/1K input tokens, $0.002/1K output tokens  
                cost = (prompt_tokens * 0.00025 / 1000) + (completion_tokens * 0.002 / 1000)
            
            tokens_used = usage["total_tokens"]
            
            self.cost_tracker.record_cost(cost, processor_name)
            
            # Save metrics
            metrics = ProcessorMetrics(
                processor_name=processor_name,
                tab_name=tab_name,
                cost_usd=cost,
                tokens_used=tokens_used,
                response_time_seconds=response_time,
                success=True,
                api_calls=1,
                retry_count=0,
                timestamp=datetime.now().isoformat()
            )
            self.results_logger.save_metrics(metrics)
            
            self.results_logger.logger.info(f"[SUCCESS] {tab_name} tab completed successfully")
            self.results_logger.logger.info(f"   Cost: ${cost:.4f}, Tokens: {tokens_used}, Time: {response_time:.1f}s")
            
            return {
                "success": True,
                "tab": tab_name,
                "processor": processor_name,
                "output": processed_output,
                "metrics": asdict(metrics)
            }
            
        except Exception as e:
            end_time = time.time()
            error_msg = f"Error testing {processor_name}: {str(e)}"
            self.results_logger.logger.error(error_msg)
            
            # Save error metrics
            metrics = ProcessorMetrics(
                processor_name=processor_name,
                tab_name=tab_name,
                cost_usd=0.0,
                tokens_used=0,
                response_time_seconds=end_time - start_time,
                success=False,
                api_calls=0,
                retry_count=0,
                timestamp=datetime.now().isoformat(),
                error_message=str(e)
            )
            self.results_logger.save_metrics(metrics)
            
            return {"success": False, "error": error_msg}
    
    def _prepare_input_data(self, tab_name: str, previous_results: Optional[Dict] = None) -> Dict[str, Any]:
        """Prepare input data for specific tab/processor"""
        
        input_data = {
            "nonprofit": self.test_data["nonprofit"],
            "opportunity": self.test_data["opportunity"]
        }
        
        if previous_results:
            input_data["previous_results"] = previous_results
        
        # Add tab-specific data
        if tab_name == "PLAN":
            # Comprehensive strategic intelligence data
            input_data["comprehensive_analysis_context"] = {
                "purpose": "Comprehensive opportunity screening and strategic assessment",
                "coverage_areas": [
                    "funding_source_verification", "program_status_intelligence", 
                    "eligibility_prescreening", "strategic_assessment", "risk_assessment_matrix",
                    "web_intelligence", "batch_processing_intelligence", "quality_assurance",
                    "downstream_integration", "success_factor_modeling", "competitive_intelligence",
                    "relationship_mapping"
                ]
            }
            
            # Enhanced opportunity data for complete analysis
            input_data["enhanced_opportunity_data"] = {
                "funding_details": {
                    "estimated_award_range": "To be determined from opportunity data",
                    "application_deadline": "To be extracted from program information", 
                    "program_duration": "To be determined from grant specifications",
                    "matching_requirements": "To be assessed from eligibility criteria"
                },
                "application_process": {
                    "complexity_indicators": ["multi-stage", "single-submission", "collaborative"],
                    "required_documents": ["proposal", "budget", "sustainability_plan"],
                    "technical_requirements": "Environmental project expertise required",
                    "evaluation_criteria": "To be extracted from program guidelines"
                },
                "competitive_context": {
                    "typical_applicant_profile": "Environmental organizations, research institutions",
                    "historical_award_patterns": "Federal environmental grants typically competitive",
                    "success_factors": ["technical_expertise", "past_performance", "innovation"]
                }
            }
            
            # Board and network data for relationship mapping
            input_data["relationship_data"] = {
                "board_information": "Available from nonprofit filings for network analysis",
                "institutional_connections": "To be analyzed from organizational data",
                "geographic_networks": "Arlington, VA area connections and federal proximity",
                "sector_relationships": "Aging sector vs environmental sector analysis"
            }
            
            # Quality assurance context
            input_data["data_quality_context"] = {
                "available_data_sources": ["propublica_990s", "grants_gov", "entity_cache"],
                "data_completeness_areas": ["financial", "programmatic", "governance", "compliance"],
                "missing_data_indicators": ["program_details", "application_requirements", "contact_info"],
                "reliability_factors": ["data_age", "source_authority", "cross_validation"]
            }
        elif tab_name == "ANALYZE":
            # Strategic analysis data
            input_data["analysis_context"] = {
                "purpose": "Strategic alignment analysis",
                "focus": ["competitive_advantage", "resource_requirements", "market_position"]
            }
        elif tab_name == "EXAMINE":
            # Deep research data
            input_data["research_context"] = {
                "purpose": "Comprehensive research and risk analysis",
                "focus": ["implementation_feasibility", "risk_assessment", "success_modeling"]
            }
        elif tab_name == "APPROACH":
            # Implementation strategy data
            input_data["strategy_context"] = {
                "purpose": "Implementation strategy and approach",
                "focus": ["detailed_planning", "resource_allocation", "execution_roadmap"]
            }
        
        return input_data
    
    def _generate_ai_prompt(self, tab_name: str, input_data: Dict[str, Any]) -> str:
        """Generate AI prompt for specific tab/processor"""
        
        nonprofit = input_data["nonprofit"]["organization"]
        opportunity = input_data["opportunity"]["data"]
        
        base_context = f"""
You are an expert grant research analyst helping nonprofits identify and pursue funding opportunities.

NONPROFIT PROFILE:
- Name: {nonprofit.get('name', 'Unknown')}
- EIN: {nonprofit.get('ein', 'Unknown')}
- Location: {nonprofit.get('city', 'Unknown')}, {nonprofit.get('state', 'Unknown')}
- NTEE Code: {nonprofit.get('ntee_code', 'Unknown')}
- Annual Revenue: ${nonprofit.get('revenue_amount', 0):,}
- Total Assets: ${nonprofit.get('asset_amount', 0):,}

FUNDING OPPORTUNITY:
- Title: {opportunity.get('funding_opportunity_title', 'Unknown')}
- Agency: {opportunity.get('agency_code', 'Unknown')}
- Category: {opportunity.get('category_of_funding_activity', 'Unknown')}
- Type: {opportunity.get('funding_instrument_type', 'Grant')}
"""
        
        if tab_name == "PLAN":
            prompt = base_context + """
TASK - PLAN TAB (Comprehensive Strategic Intelligence):
You are conducting comprehensive opportunity screening and strategic assessment as described in the AI_PROCESSOR_TAB_GUIDE. This analysis must cover ALL 15 capability areas with detailed intelligence.

REQUIRED ANALYSIS AREAS:

1. FUNDING SOURCE VERIFICATION:
   - Assess DOE as legitimate federal funder with confirmed funding capacity
   - Determine if this is direct funding, fiscal sponsor, aggregator, or service provider
   - Evaluate funding provider reliability and classification confidence (0.0-1.0)
   - Verify actual grant-making vs information aggregation

2. PROGRAM STATUS INTELLIGENCE:
   - Evaluate current program status (active/seasonal/archived/ambiguous)
   - Assess if program is currently accepting applications
   - Analyze application timeline and deadline proximity
   - Determine seasonal patterns or cyclical nature

3. ELIGIBILITY PRE-SCREENING:
   - Parse comprehensive qualification criteria
   - Assess organizational fit (entity type, status, structure)
   - Evaluate geographic compliance and location-based restrictions
   - Analyze financial thresholds and capacity requirements
   - Identify requirement gaps and potential solutions

4. STRATEGIC ASSESSMENT FRAMEWORK:
   - Mission alignment scoring using NLP-powered semantic analysis (0.0-1.0)
   - Strategic value classification (Exceptional/High/Medium/Low/Minimal Value)
   - Priority mapping between nonprofit and funder objectives
   - Geographic scope compatibility analysis
   - Contextual understanding of organizational mission fit

5. RISK ASSESSMENT MATRIX (All 6 Categories):
   - Competition Risk: competitive pressure and application volume assessment
   - Technical Requirements: specialized requirement complexity evaluation
   - Geographic Constraints: location-based restrictions and compliance
   - Capacity Limitations: organizational capability and resource gaps
   - Timeline Pressures: deadline constraints and preparation requirements
   - Compliance Complexity: regulatory and administrative burden

6. ENHANCED WEB INTELLIGENCE:
   - Extract and analyze contact information (program officers, departments)
   - Assess application process complexity (simple/moderate/complex)
   - Map step-by-step application workflow and requirements
   - Identify critical success factors for application completion

7. BATCH PROCESSING INTELLIGENCE:
   - Assign batch priority score (0.0-1.0) for processing optimization
   - Recommend processing approach (immediate/batched/deferred)
   - Suggest optimal batch grouping with similar opportunities
   - Calculate resource allocation weight as percentage of total effort

8. QUALITY ASSURANCE SCORING:
   - Evaluate data completeness score (0.0-1.0) for input information
   - Assess analysis reliability score (0.0-1.0) for confidence in findings
   - Identify missing data gaps and their impact on analysis accuracy
   - Recommend specific additional data needed for quality improvement

9. DOWNSTREAM INTEGRATION:
   - Assess readiness for next stage analysis (ready/needs_data/skip)
   - Evaluate quality gate status (pass/conditional/fail) for ANALYZE tab
   - Prepare data package requirements for ANALYZE tab processing
   - Recommend optimal processing path (standard/expedited/enhanced)

10. SUCCESS FACTOR MODELING:
    - Calculate statistical success probability (0.0-1.0) based on analysis
    - Identify and rank top 5 critical success factors
    - Assess top 3 failure risk factors and mitigation strategies
    - Recommend specific optimization opportunities for success improvement

11. COMPETITIVE INTELLIGENCE:
    - Assess competitive pressure level (low/medium/high)
    - Identify likely competing organizations and organization types
    - Analyze nonprofit's unique competitive advantages and differentiators
    - Recommend differentiation strategy and positioning approach

12. RELATIONSHIP MAPPING:
    - Analyze board network connections and potential pathways
    - Identify strategic partnership and collaboration opportunities
    - Map introduction pathways to key decision makers and contacts
    - Calculate relationship leverage score (0.0-1.0) for existing connections

Respond in comprehensive JSON format with ALL sections:
{
    "funding_source_verification": {
        "funder_type": "direct_federal|fiscal_sponsor|aggregator|service_provider",
        "legitimacy_score": 0.0-1.0,
        "funding_capacity_confirmed": true/false,
        "confidence_assessment": "detailed reliability analysis"
    },
    "program_status_intelligence": {
        "status": "active|seasonal|archived|ambiguous",
        "accepting_applications": true/false,
        "timeline_analysis": "deadline proximity and timing assessment",
        "application_window": "current status and availability analysis"
    },
    "eligibility_prescreening": {
        "organizational_fit": "detailed entity type and structure assessment",
        "geographic_compliance": "location-based eligibility analysis", 
        "financial_thresholds": "revenue and capacity requirement evaluation",
        "requirement_gaps": ["identified gaps and solutions"],
        "eligibility_score": 0.0-1.0
    },
    "strategic_assessment": {
        "mission_alignment_score": 0.0-1.0,
        "strategic_value_tier": "Exceptional|High|Medium|Low|Minimal",
        "priority_mapping": "detailed alignment analysis between nonprofit and funder",
        "geographic_compatibility": "location-based strategic fit assessment",
        "contextual_understanding": "deep mission comprehension analysis"
    },
    "risk_assessment_matrix": {
        "competition_risk": {"level": "low|medium|high", "analysis": "detailed assessment"},
        "technical_requirements": {"level": "low|medium|high", "analysis": "complexity evaluation"},
        "geographic_constraints": {"level": "low|medium|high", "analysis": "location restrictions"},
        "capacity_limitations": {"level": "low|medium|high", "analysis": "organizational capability gaps"},
        "timeline_pressures": {"level": "low|medium|high", "analysis": "deadline and preparation constraints"},
        "compliance_complexity": {"level": "low|medium|high", "analysis": "regulatory burden assessment"}
    },
    "web_intelligence": {
        "contact_information": ["extracted contacts with roles and relevance"],
        "application_complexity": "simple|moderate|complex",
        "process_requirements": ["step-by-step application workflow"],
        "success_factors": ["critical elements for application completion"]
    },
    "batch_processing_intelligence": {
        "batch_priority_score": 0.0-1.0,
        "processing_recommendation": "immediate|batched|deferred",
        "optimal_batch_grouping": "suggested categorization with similar opportunities",
        "resource_allocation_weight": "percentage of total effort recommended"
    },
    "quality_assurance": {
        "data_completeness_score": 0.0-1.0,
        "analysis_reliability_score": 0.0-1.0,
        "missing_data_impact": "assessment of information gaps on analysis quality",
        "quality_improvement_recommendations": ["specific additional data needed"]
    },
    "downstream_integration": {
        "next_stage_readiness": "ready|needs_data|skip",
        "quality_gate_status": "pass|conditional|fail",
        "analyze_tab_data_package": "prepared information requirements for next stage",
        "recommended_processing_path": "standard|expedited|enhanced"
    },
    "success_factor_modeling": {
        "success_probability": 0.0-1.0,
        "critical_success_factors": ["top 5 ranked factors for success"],
        "failure_risk_factors": ["top 3 risk factors with mitigation strategies"],
        "optimization_opportunities": ["specific actionable improvement recommendations"]
    },
    "competitive_intelligence": {
        "competitive_pressure_assessment": "low|medium|high",
        "likely_competitors": ["organization types and potential competitor analysis"],
        "competitive_advantages": ["nonprofit's unique strengths and differentiators"],
        "differentiation_strategy": "recommended strategic positioning approach"
    },
    "relationship_mapping": {
        "board_network_connections": ["potential connections identified from board analysis"],
        "partnership_opportunities": ["strategic collaboration possibilities"],
        "introduction_pathways": ["routes to key decision makers and contacts"],
        "relationship_leverage_score": 0.0-1.0
    },
    "final_recommendation": {
        "viability_score": 0.0-1.0,
        "recommendation": "pursue|skip|investigate_further",
        "confidence": 0.0-1.0,
        "comprehensive_reasoning": "detailed analysis summary integrating all assessment areas"
    }
}
"""
        
        elif tab_name == "ANALYZE":
            prompt = base_context + """
TASK - ANALYZE TAB (Enhanced Screening and Intelligent Filtering):
You are conducting comprehensive enhanced screening as described in the AI_PROCESSOR_TAB_GUIDE. This analysis must cover ALL capability areas with detailed intelligence for cost-effective filtering before expensive deep analysis.

Previous Results:
""" + json.dumps(input_data.get("previous_results", {}), indent=2) + """

REQUIRED ANALYSIS AREAS:

1. ENHANCED SCREENING FRAMEWORK:

   A. VIABILITY ASSESSMENT ENGINE:
   - Strategic Viability: Long-term strategic value and organizational impact assessment (0.0-1.0)
   - Financial Viability: Revenue compatibility and funding capacity evaluation (0.0-1.0)  
   - Operational Viability: Implementation feasibility and resource requirement analysis (0.0-1.0)
   - Timeline Viability: Deadline feasibility and preparation time assessment (0.0-1.0)
   - Success Viability: Funding probability and competitive advantage evaluation (0.0-1.0)

   B. RISK ASSESSMENT & MITIGATION:
   - Competition Analysis: Competitive landscape evaluation and positioning assessment
   - Technical Risk: Complex requirement identification and capability gaps
   - Financial Risk: Budget constraints and resource allocation challenges
   - Timeline Risk: Deadline pressure and preparation time limitations
   - Compliance Risk: Regulatory and administrative complexity assessment

   C. MARKET INTELLIGENCE INTEGRATION:
   - Funding Trends: Sector-specific funding pattern analysis
   - Competitive Positioning: Market position and differentiation opportunities
   - Strategic Timing: Optimal application timing and market conditions
   - Partnership Opportunities: Collaborative advantage and alliance potential
   - Innovation Assessment: Unique value proposition and differentiation factors

2. SUCCESS PROBABILITY MODELING:

   A. MULTI-DIMENSIONAL SCORING:
   - Overall Compatibility: Comprehensive fit assessment (0.0-1.0 scale)
   - Strategic Fit: Mission alignment and organizational priority matching (0.0-1.0)
   - Competitive Advantage: Unique strengths and differentiating factors (0.0-1.0)
   - Resource Alignment: Capacity and capability matching with requirements (0.0-1.0)
   - Historical Patterns: Learning from past funding decisions and outcomes (0.0-1.0)

   B. DECISION SUPPORT ANALYTICS:
   - Go/No-Go Recommendations: Data-driven decision framework with confidence levels
   - Resource Allocation: Optimal effort distribution across opportunities
   - Priority Ranking: Comparative assessment within analysis batches
   - Timeline Optimization: Strategic sequencing and application scheduling
   - Success Optimization: Probability enhancement strategies and recommendations

Respond in comprehensive JSON format with ALL sections:
{
    "enhanced_screening_framework": {
        "viability_assessment_engine": {
            "strategic_viability": 0.0-1.0,
            "financial_viability": 0.0-1.0,
            "operational_viability": 0.0-1.0,
            "timeline_viability": 0.0-1.0,
            "success_viability": 0.0-1.0,
            "overall_viability_score": 0.0-1.0,
            "viability_tier": "exceptional|high|medium|low|critical",
            "viability_reasoning": "detailed assessment explanation"
        },
        "risk_assessment_mitigation": {
            "competition_analysis": {
                "level": "low|medium|high|extreme",
                "assessment": "detailed competitive landscape evaluation",
                "positioning_strategy": "recommended competitive positioning"
            },
            "technical_risk": {
                "level": "low|medium|high|critical", 
                "assessment": "complex requirement and capability gap analysis",
                "mitigation_strategy": "recommended technical risk mitigation"
            },
            "financial_risk": {
                "level": "low|medium|high|critical",
                "assessment": "budget constraints and resource allocation analysis",
                "mitigation_strategy": "recommended financial risk mitigation"
            },
            "timeline_risk": {
                "level": "low|medium|high|critical",
                "assessment": "deadline pressure and preparation time analysis",
                "mitigation_strategy": "recommended timeline risk mitigation"
            },
            "compliance_risk": {
                "level": "low|medium|high|critical",
                "assessment": "regulatory and administrative complexity analysis",
                "mitigation_strategy": "recommended compliance risk mitigation"
            },
            "overall_risk_level": "low|medium|high|critical",
            "risk_mitigation_priority": ["top 3 risk mitigation priorities"]
        },
        "market_intelligence_integration": {
            "funding_trends": "sector-specific funding pattern analysis",
            "competitive_positioning": "market position and differentiation opportunities",
            "strategic_timing": "optimal application timing and market conditions",
            "partnership_opportunities": ["collaborative advantage and alliance potential"],
            "innovation_assessment": "unique value proposition and differentiation analysis",
            "market_opportunity_score": 0.0-1.0
        }
    },
    "success_probability_modeling": {
        "multi_dimensional_scoring": {
            "overall_compatibility": 0.0-1.0,
            "strategic_fit": 0.0-1.0,
            "competitive_advantage": 0.0-1.0,
            "resource_alignment": 0.0-1.0,
            "historical_patterns": 0.0-1.0,
            "composite_score": 0.0-1.0,
            "scoring_confidence": 0.0-1.0
        },
        "decision_support_analytics": {
            "go_no_go_recommendation": "proceed|proceed_with_caution|monitor|reject",
            "recommendation_confidence": 0.0-1.0,
            "recommendation_reasoning": "detailed decision framework analysis",
            "resource_allocation": {
                "effort_level": "minimal|moderate|high|intensive",
                "resource_priority": "low|medium|high|critical",
                "estimated_effort_hours": 0,
                "cost_benefit_ratio": 0.0-10.0
            },
            "priority_ranking": {
                "priority_score": 0.0-1.0,
                "ranking_rationale": "comparative assessment explanation",
                "batch_position": "top_tier|high_priority|medium_priority|low_priority"
            },
            "timeline_optimization": {
                "optimal_timing": "immediate|short_term|medium_term|long_term",
                "preparation_timeline": "preparation time recommendation",
                "deadline_feasibility": 0.0-1.0,
                "scheduling_recommendation": "strategic sequencing advice"
            },
            "success_optimization": {
                "probability_enhancement_strategies": ["top 5 enhancement strategies"],
                "competitive_advantage_amplification": ["strategies to amplify advantages"],
                "weakness_mitigation": ["strategies to address weaknesses"],
                "success_probability_improvement": 0.0-1.0
            }
        }
    },
    "comprehensive_recommendation": {
        "overall_assessment": "exceptional|high_potential|moderate_potential|low_potential|not_recommended",
        "confidence_level": 0.0-1.0,
        "key_success_factors": ["top 5 critical success factors"],
        "key_risk_factors": ["top 3 critical risk factors"],
        "next_steps": ["specific actionable next steps"],
        "examine_tab_readiness": "ready|conditional|not_ready",
        "resource_investment_justification": "detailed ROI and strategic value analysis"
    }
}
"""
        
        elif tab_name == "EXAMINE":
            prompt = base_context + """
TASK - EXAMINE TAB (Comprehensive Strategic Intelligence and Relationship Analysis):
You are conducting comprehensive strategic intelligence as described in the AI_PROCESSOR_TAB_GUIDE. This analysis must deliver multi-thousand token intelligence reports with actionable insights across ALL capability areas.

Previous Results:
""" + json.dumps(input_data.get("previous_results", {}), indent=2) + """

REQUIRED INTELLIGENCE FRAMEWORKS:

1. 🕸️ RELATIONSHIP INTELLIGENCE FRAMEWORK:

   A. BOARD NETWORK ANALYSIS:
   - Network Mapping: Comprehensive relationship structure documentation
   - Influence Assessment: Power dynamics and decision-making pathway analysis (0.0-1.0)
   - Connection Quality: Relationship strength and reliability evaluation (0.0-1.0)
   - Strategic Positioning: Optimal relationship leverage and development strategies
   - Introduction Pathways: Systematic relationship building approaches

   B. KEY DECISION MAKER IDENTIFICATION:
   - Primary Contact Recognition: Critical decision-maker identification and analysis
   - Authority Assessment: Decision-making power and influence evaluation (0.0-1.0)
   - Communication Channels: Effective contact and engagement pathway mapping
   - Engagement Strategy: Optimal approach and relationship building tactics
   - Trust Development: Credibility building and relationship strengthening plans

   C. STRATEGIC PARTNERSHIP ASSESSMENT:
   - Partnership Potential: Comprehensive compatibility evaluation and scoring (0.0-1.0)
   - Mission Alignment: Deep strategic fit and value alignment analysis (0.0-1.0)
   - Synergy Opportunities: Collaborative enhancement and value creation mapping
   - Historical Patterns: Past partnership success factors and best practices
   - Risk Evaluation: Partnership challenges and mitigation strategies

2. 💰 FINANCIAL INTELLIGENCE ANALYSIS:

   A. FUNDING CAPACITY ASSESSMENT:
   - Financial Health Evaluation: Organizational stability and sustainability analysis (0.0-1.0)
   - Historical Giving Patterns: Funding trend identification and preference analysis
   - Grant Size Optimization: Optimal funding request strategy and justification
   - Multi-year Potential: Long-term funding relationship prospects (0.0-1.0)
   - Sustainability Planning: Ongoing partnership and funding continuity assessment

   B. COMPETITIVE FINANCIAL INTELLIGENCE:
   - Market Positioning: Financial standing and competitive comparison (0.0-1.0)
   - Resource Allocation: Strategic funding distribution and priority analysis
   - Investment Patterns: Historical funding decisions and strategic focus areas
   - Growth Trajectories: Financial development and expansion patterns
   - Strategic Implications: Financial intelligence impact on partnership strategies

3. 🏢 COMPETITIVE INTELLIGENCE CAPABILITIES:

   A. MARKET ANALYSIS FRAMEWORK:
   - Competitive Landscape: Comprehensive competitor identification and profiling
   - Market Share Assessment: Position evaluation and competitive standing analysis (0.0-1.0)
   - Differentiation Analysis: Unique value propositions and competitive advantages
   - Threat Assessment: Competitive risks and strategic vulnerabilities (0.0-1.0)
   - Opportunity Identification: Market gaps and strategic positioning opportunities

   B. STRATEGIC POSITIONING INTELLIGENCE:
   - Market Leadership: Industry positioning and thought leadership assessment (0.0-1.0)
   - Innovation Analysis: Unique approaches and competitive differentiation
   - Strategic Advantages: Organizational strengths and leverage opportunities
   - Competitive Response: Market reaction prediction and strategic preparation
   - Long-term Positioning: Sustainable competitive advantage development

Respond in comprehensive JSON format with ALL intelligence frameworks:
{
    "relationship_intelligence_framework": {
        "board_network_analysis": {
            "network_mapping": "comprehensive relationship structure documentation",
            "influence_assessment_score": 0.0-1.0,
            "connection_quality_score": 0.0-1.0,
            "key_influencers": ["identified key influencers and their roles"],
            "power_dynamics": "decision-making pathway analysis",
            "strategic_positioning_opportunities": ["optimal relationship leverage strategies"],
            "introduction_pathways": ["systematic relationship building approaches"],
            "network_strength_assessment": 0.0-1.0
        },
        "key_decision_maker_identification": {
            "primary_contacts": [
                {
                    "name": "decision maker name",
                    "title": "decision maker title",
                    "authority_level": 0.0-1.0,
                    "influence_score": 0.0-1.0,
                    "accessibility": "low|medium|high",
                    "engagement_strategy": "optimal approach strategy"
                }
            ],
            "decision_making_hierarchy": "organizational decision structure analysis",
            "communication_channels": ["effective contact pathways"],
            "engagement_timeline": "optimal timing for engagement",
            "trust_development_plan": ["credibility building strategies"],
            "relationship_priority_score": 0.0-1.0
        },
        "strategic_partnership_assessment": {
            "partnership_potential_score": 0.0-1.0,
            "mission_alignment_score": 0.0-1.0,
            "strategic_fit_analysis": "deep alignment evaluation",
            "synergy_opportunities": ["collaborative enhancement possibilities"],
            "value_creation_potential": 0.0-1.0,
            "historical_partnership_patterns": "past partnership success analysis",
            "partnership_risks": ["identified partnership challenges"],
            "mitigation_strategies": ["partnership risk mitigation approaches"],
            "long_term_partnership_viability": 0.0-1.0
        }
    },
    "financial_intelligence_analysis": {
        "funding_capacity_assessment": {
            "financial_health_score": 0.0-1.0,
            "organizational_stability": "comprehensive stability analysis",
            "sustainability_assessment": "long-term viability evaluation",
            "historical_giving_patterns": "funding trend and preference analysis",
            "funding_priorities": ["identified strategic funding focus areas"],
            "grant_size_optimization": "optimal funding request strategy",
            "multi_year_potential_score": 0.0-1.0,
            "funding_continuity_assessment": "ongoing partnership prospects",
            "financial_capacity_tier": "exceptional|high|medium|low|limited"
        },
        "competitive_financial_intelligence": {
            "market_positioning_score": 0.0-1.0,
            "financial_standing_analysis": "competitive financial comparison",
            "resource_allocation_patterns": "strategic funding distribution analysis",
            "investment_strategy_analysis": "historical funding decision patterns",
            "growth_trajectory_assessment": "financial development patterns",
            "funding_competition_analysis": "competitive funding landscape",
            "strategic_financial_implications": "financial intelligence impact on strategy",
            "funding_opportunity_score": 0.0-1.0
        }
    },
    "competitive_intelligence_capabilities": {
        "market_analysis_framework": {
            "competitive_landscape_mapping": "comprehensive competitor identification and profiling",
            "market_share_assessment_score": 0.0-1.0,
            "competitor_profiles": [
                {
                    "competitor_name": "identified competitor",
                    "competitive_threat_level": "low|medium|high|critical",
                    "competitive_advantages": ["competitor strengths"],
                    "competitive_weaknesses": ["competitor vulnerabilities"]
                }
            ],
            "differentiation_analysis": "unique value propositions and competitive advantages",
            "threat_assessment_score": 0.0-1.0,
            "strategic_vulnerabilities": ["identified competitive risks"],
            "market_opportunities": ["strategic positioning opportunities"],
            "competitive_positioning_score": 0.0-1.0
        },
        "strategic_positioning_intelligence": {
            "market_leadership_score": 0.0-1.0,
            "industry_positioning_analysis": "thought leadership assessment",
            "innovation_differentiation": "unique approaches and competitive differentiation",
            "strategic_advantages": ["organizational strengths and leverage opportunities"],
            "competitive_response_prediction": "market reaction prediction and strategic preparation",
            "long_term_positioning_strategy": "sustainable competitive advantage development",
            "positioning_optimization_opportunities": ["strategic positioning enhancements"],
            "strategic_positioning_confidence": 0.0-1.0
        }
    },
    "comprehensive_strategic_intelligence_summary": {
        "overall_intelligence_assessment": "exceptional|high_intelligence|moderate_intelligence|limited_intelligence|insufficient_data",
        "strategic_intelligence_confidence": 0.0-1.0,
        "key_strategic_insights": ["top 5 critical strategic insights"],
        "relationship_leverage_opportunities": ["top 3 relationship leverage strategies"],
        "financial_intelligence_highlights": ["key financial intelligence findings"],
        "competitive_intelligence_priorities": ["top 3 competitive intelligence priorities"],
        "actionable_intelligence_recommendations": ["specific actionable intelligence-based strategies"],
        "intelligence_gaps": ["identified intelligence gaps requiring further research"],
        "approach_tab_readiness": "ready|conditional|insufficient_intelligence",
        "strategic_intelligence_value_score": 0.0-1.0
    }
}
"""
        
        elif tab_name == "APPROACH":
            prompt = base_context + """
TASK - APPROACH TAB (Strategic Decision Framework & Implementation Planning):
You are conducting comprehensive grant application decision-making and implementation planning as described in the AI_PROCESSOR_TAB_GUIDE. This analysis must deliver comprehensive planning with resource optimization and success modeling across ALL capability areas.

Previous Results:
""" + json.dumps(input_data.get("previous_results", {}), indent=2) + """

REQUIRED IMPLEMENTATION FRAMEWORKS:

1. 🎯 GRANT APPLICATION INTELLIGENCE:

   A. ELIGIBILITY & REQUIREMENTS ANALYSIS:
   - Compliance Assessment: Organizational, programmatic, financial, and geographic requirements
   - Documentation Planning: Required evidence, certifications, and supporting materials
   - Application Mapping: Document types, formats, deadlines, and submission requirements
   - Quality Standards: Excellence criteria and competitive positioning requirements
   - Success Factors: Critical elements for funding success and competitive advantage

   B. EFFORT ESTIMATION & RESOURCE PLANNING:
   - Time Requirements: Comprehensive work hour estimation and personnel allocation
   - Resource Assessment: Staff, expertise, materials, and budget needs analysis
   - Capacity Planning: Workload distribution and organizational impact evaluation
   - Cost-Benefit Analysis: Investment requirements vs expected returns and impact (0.0-10.0)
   - Efficiency Optimization: Resource utilization and productivity maximization strategies

2. 📋 IMPLEMENTATION BLUEPRINT CREATION:

   A. STRATEGIC IMPLEMENTATION PLANNING:
   - Project Execution: Comprehensive implementation roadmaps and delivery strategies
   - Workflow Development: Process optimization and efficiency enhancement
   - Milestone Definition: Key achievement points and progress measurement criteria
   - Deliverable Specification: Clear output definitions and quality standards
   - Integration Coordination: Alignment with existing operations and strategic initiatives

   B. RISK MITIGATION & CONTINGENCY PLANNING:
   - Risk Assessment: Comprehensive challenge and obstacle identification (0.0-1.0)
   - Mitigation Strategies: Proactive prevention and risk management approaches
   - Contingency Planning: Alternative approaches and backup strategies
   - Monitoring Systems: Early warning indicators and performance tracking
   - Recovery Planning: Error correction and project recovery procedures

3. 🤝 STRATEGIC PARTNERSHIP & COLLABORATION FRAMEWORK:

   A. PARTNERSHIP DEVELOPMENT PLANNING:
   - Stakeholder Coordination: Multi-party engagement and relationship management
   - Communication Strategy: Information sharing protocols and coordination systems
   - Responsibility Matrix: Role definitions and accountability structures
   - Collaboration Framework: Partnership structures and working relationships
   - Conflict Resolution: Dispute prevention and resolution mechanisms

   B. STRATEGIC ADVANTAGE OPTIMIZATION:
   - Competitive Differentiation: Unique value proposition development and positioning
   - Market Positioning: Strategic placement and competitive landscape navigation (0.0-1.0)
   - Value Creation: Combined capability enhancement and impact maximization (0.0-1.0)
   - Success Probability: Statistical modeling and outcome optimization (0.0-1.0)
   - Long-term Strategy: Sustainable advantage development and relationship building

4. ✅ DECISION SUPPORT & GO/NO-GO FRAMEWORK:

   A. MULTI-CRITERIA DECISION ANALYSIS:
   - Success Probability Modeling: Statistical assessment based on comprehensive analysis (0.0-1.0)
   - Resource Impact Evaluation: Organizational capacity and strategic priority alignment (0.0-1.0)
   - Risk-Benefit Assessment: Comprehensive opportunity and challenge evaluation
   - Strategic Alignment: Mission compatibility and organizational priority matching (0.0-1.0)
   - ROI Optimization: Return on investment maximization and value creation

   B. IMPLEMENTATION PACKAGE DEVELOPMENT:
   - Application Coordination: Complete submission package management and optimization
   - Timeline Management: Strategic scheduling and milestone coordination
   - Quality Assurance: Review processes and excellence verification systems
   - Success Optimization: Competitive advantage enhancement and positioning strategies
   - Performance Monitoring: Success tracking and continuous improvement integration

Respond in comprehensive JSON format with ALL implementation frameworks:
{
    "grant_application_intelligence": {
        "eligibility_requirements_analysis": {
            "compliance_assessment": {
                "organizational_compliance": "organizational requirement evaluation",
                "programmatic_compliance": "programmatic requirement evaluation",
                "financial_compliance": "financial requirement evaluation",
                "geographic_compliance": "geographic requirement evaluation",
                "compliance_confidence_score": 0.0-1.0
            },
            "documentation_planning": {
                "required_evidence": ["list of required evidence documents"],
                "certifications_needed": ["required certifications"],
                "supporting_materials": ["supporting documentation requirements"],
                "document_preparation_timeline": "documentation timeline",
                "document_quality_standards": "excellence criteria for documents"
            },
            "application_mapping": {
                "document_types": ["required document types"],
                "submission_formats": ["required formats and specifications"],
                "deadline_schedule": "comprehensive deadline mapping",
                "submission_requirements": ["submission process requirements"],
                "application_complexity_score": 0.0-1.0
            },
            "quality_standards": {
                "excellence_criteria": ["competitive positioning requirements"],
                "quality_benchmarks": ["quality measurement standards"],
                "competitive_positioning": "positioning requirements analysis",
                "differentiation_requirements": ["unique positioning requirements"],
                "quality_assurance_score": 0.0-1.0
            },
            "success_factors": {
                "critical_success_elements": ["top 5 critical success elements"],
                "competitive_advantages": ["funding success competitive advantages"],
                "success_probability_factors": ["probability enhancement factors"],
                "funding_success_score": 0.0-1.0
            }
        },
        "effort_estimation_resource_planning": {
            "time_requirements": {
                "work_hour_estimation": 0,
                "personnel_allocation": "comprehensive personnel allocation plan",
                "timeline_breakdown": "detailed time requirement breakdown",
                "critical_path_analysis": "critical path and time dependencies",
                "time_optimization_opportunities": ["time efficiency improvements"]
            },
            "resource_assessment": {
                "staff_requirements": ["staffing needs analysis"],
                "expertise_requirements": ["required expertise and skills"],
                "materials_budget": "materials and equipment needs",
                "budget_requirements": "comprehensive budget needs analysis",
                "resource_optimization_score": 0.0-1.0
            },
            "capacity_planning": {
                "workload_distribution": "organizational workload impact",
                "organizational_impact": "capacity and operations impact",
                "resource_conflict_analysis": "potential resource conflicts",
                "capacity_utilization_optimization": "capacity optimization strategies",
                "capacity_feasibility_score": 0.0-1.0
            },
            "cost_benefit_analysis": {
                "investment_requirements": "total investment analysis",
                "expected_returns": "expected return analysis",
                "impact_assessment": "expected impact evaluation",
                "cost_benefit_ratio": 0.0-10.0,
                "roi_optimization_strategies": ["ROI maximization approaches"]
            },
            "efficiency_optimization": {
                "resource_utilization_strategies": ["resource optimization approaches"],
                "productivity_maximization": ["productivity enhancement strategies"],
                "efficiency_improvements": ["process efficiency improvements"],
                "optimization_opportunities": ["comprehensive optimization opportunities"],
                "efficiency_score": 0.0-1.0
            }
        }
    },
    "implementation_blueprint_creation": {
        "strategic_implementation_planning": {
            "project_execution": {
                "implementation_roadmap": ["comprehensive implementation phases"],
                "delivery_strategies": ["project delivery approaches"],
                "execution_framework": "project execution methodology",
                "implementation_timeline": "detailed implementation timeline",
                "execution_confidence_score": 0.0-1.0
            },
            "workflow_development": {
                "process_optimization": "workflow optimization strategies",
                "efficiency_enhancement": ["efficiency improvement approaches"],
                "workflow_integration": "workflow integration with existing operations",
                "process_improvement_opportunities": ["process enhancement opportunities"],
                "workflow_efficiency_score": 0.0-1.0
            },
            "milestone_definition": {
                "key_milestones": ["major achievement milestones"],
                "progress_measurement": ["progress tracking criteria"],
                "milestone_timeline": "milestone scheduling",
                "achievement_criteria": ["milestone success criteria"],
                "milestone_feasibility_score": 0.0-1.0
            },
            "deliverable_specification": {
                "output_definitions": ["clear deliverable definitions"],
                "quality_standards": ["deliverable quality requirements"],
                "deliverable_timeline": "deliverable schedule",
                "quality_assurance": ["quality verification processes"],
                "deliverable_confidence_score": 0.0-1.0
            },
            "integration_coordination": {
                "operational_alignment": "alignment with existing operations",
                "strategic_integration": "integration with strategic initiatives",
                "coordination_framework": "integration coordination approach",
                "integration_challenges": ["potential integration challenges"],
                "integration_success_score": 0.0-1.0
            }
        },
        "risk_mitigation_contingency_planning": {
            "risk_assessment": {
                "challenge_identification": ["comprehensive challenge analysis"],
                "obstacle_analysis": ["potential obstacle identification"],
                "risk_probability_assessment": ["risk probability evaluation"],
                "impact_assessment": ["risk impact analysis"],
                "overall_risk_score": 0.0-1.0
            },
            "mitigation_strategies": {
                "prevention_approaches": ["proactive risk prevention strategies"],
                "risk_management": ["comprehensive risk management approaches"],
                "mitigation_timeline": "risk mitigation implementation timeline",
                "mitigation_effectiveness": ["mitigation strategy effectiveness"],
                "mitigation_confidence_score": 0.0-1.0
            },
            "contingency_planning": {
                "alternative_approaches": ["backup strategy alternatives"],
                "contingency_strategies": ["comprehensive contingency plans"],
                "contingency_triggers": ["contingency activation criteria"],
                "backup_resource_allocation": "contingency resource planning",
                "contingency_readiness_score": 0.0-1.0
            },
            "monitoring_systems": {
                "early_warning_indicators": ["risk monitoring indicators"],
                "performance_tracking": ["performance monitoring systems"],
                "monitoring_framework": "comprehensive monitoring approach",
                "alert_mechanisms": ["early warning alert systems"],
                "monitoring_effectiveness_score": 0.0-1.0
            },
            "recovery_planning": {
                "error_correction": ["error correction procedures"],
                "recovery_procedures": ["project recovery strategies"],
                "recovery_timeline": "recovery implementation timeline",
                "recovery_resource_requirements": "recovery resource needs",
                "recovery_confidence_score": 0.0-1.0
            }
        }
    },
    "strategic_partnership_collaboration_framework": {
        "partnership_development_planning": {
            "stakeholder_coordination": {
                "multi_party_engagement": "stakeholder engagement strategy",
                "relationship_management": "partnership relationship management",
                "coordination_framework": "stakeholder coordination approach",
                "engagement_timeline": "stakeholder engagement timeline",
                "coordination_effectiveness_score": 0.0-1.0
            },
            "communication_strategy": {
                "information_sharing_protocols": ["communication protocols"],
                "coordination_systems": ["coordination system frameworks"],
                "communication_channels": ["communication channel strategy"],
                "information_management": "information sharing management",
                "communication_effectiveness_score": 0.0-1.0
            },
            "responsibility_matrix": {
                "role_definitions": ["partnership role definitions"],
                "accountability_structures": ["accountability framework"],
                "responsibility_allocation": "responsibility distribution",
                "oversight_mechanisms": ["partnership oversight systems"],
                "responsibility_clarity_score": 0.0-1.0
            },
            "collaboration_framework": {
                "partnership_structures": ["partnership organizational structures"],
                "working_relationships": "partnership working relationship framework",
                "collaboration_processes": ["collaboration process frameworks"],
                "partnership_governance": "partnership governance structure",
                "collaboration_effectiveness_score": 0.0-1.0
            },
            "conflict_resolution": {
                "dispute_prevention": ["conflict prevention strategies"],
                "resolution_mechanisms": ["conflict resolution processes"],
                "mediation_processes": ["dispute mediation approaches"],
                "escalation_procedures": ["conflict escalation procedures"],
                "conflict_management_score": 0.0-1.0
            }
        },
        "strategic_advantage_optimization": {
            "competitive_differentiation": {
                "unique_value_proposition": "unique value proposition development",
                "differentiation_strategy": "competitive differentiation approach",
                "positioning_strategy": "market positioning strategy",
                "competitive_advantages": ["strategic competitive advantages"],
                "differentiation_strength_score": 0.0-1.0
            },
            "market_positioning": {
                "strategic_placement": "market positioning strategy",
                "competitive_landscape_navigation": "competitive navigation approach",
                "positioning_optimization": ["positioning optimization strategies"],
                "market_advantage": "market advantage development",
                "market_positioning_score": 0.0-1.0
            },
            "value_creation": {
                "capability_enhancement": "combined capability enhancement",
                "impact_maximization": "impact maximization strategies",
                "value_optimization": ["value creation optimization"],
                "synergy_realization": "partnership synergy realization",
                "value_creation_score": 0.0-1.0
            },
            "success_probability": {
                "statistical_modeling": "statistical success modeling",
                "outcome_optimization": "outcome optimization strategies",
                "probability_enhancement": ["success probability improvements"],
                "success_factors": ["critical success probability factors"],
                "success_probability_score": 0.0-1.0
            },
            "long_term_strategy": {
                "sustainable_advantage": "sustainable advantage development",
                "relationship_building": "long-term relationship building",
                "strategic_sustainability": "long-term strategic sustainability",
                "future_opportunity_development": ["future opportunity strategies"],
                "long_term_viability_score": 0.0-1.0
            }
        }
    },
    "decision_support_go_no_go_framework": {
        "multi_criteria_decision_analysis": {
            "success_probability_modeling": {
                "statistical_assessment": "comprehensive statistical assessment",
                "probability_modeling": "success probability modeling approach",
                "outcome_prediction": "outcome prediction analysis",
                "confidence_intervals": ["probability confidence analysis"],
                "success_probability_score": 0.0-1.0
            },
            "resource_impact_evaluation": {
                "organizational_capacity": "organizational capacity impact",
                "strategic_priority_alignment": "strategic priority alignment analysis",
                "resource_allocation_impact": "resource impact assessment",
                "capacity_optimization": ["capacity optimization strategies"],
                "resource_impact_score": 0.0-1.0
            },
            "risk_benefit_assessment": {
                "opportunity_evaluation": "comprehensive opportunity analysis",
                "challenge_evaluation": "comprehensive challenge analysis",
                "risk_benefit_ratio": 0.0-10.0,
                "assessment_confidence": "risk-benefit assessment confidence",
                "risk_benefit_optimization": ["risk-benefit optimization strategies"]
            },
            "strategic_alignment": {
                "mission_compatibility": "mission alignment assessment",
                "organizational_priority_matching": "priority alignment analysis",
                "strategic_fit": "strategic fit evaluation",
                "alignment_optimization": ["alignment optimization strategies"],
                "strategic_alignment_score": 0.0-1.0
            },
            "roi_optimization": {
                "investment_maximization": "return on investment maximization",
                "value_creation_optimization": "value creation optimization strategies",
                "roi_enhancement": ["ROI improvement strategies"],
                "investment_efficiency": "investment efficiency optimization",
                "roi_optimization_score": 0.0-1.0
            }
        },
        "implementation_package_development": {
            "application_coordination": {
                "submission_package_management": "complete submission package coordination",
                "package_optimization": "submission package optimization",
                "coordination_framework": "application coordination approach",
                "submission_excellence": ["submission excellence strategies"],
                "coordination_effectiveness_score": 0.0-1.0
            },
            "timeline_management": {
                "strategic_scheduling": "strategic timeline scheduling",
                "milestone_coordination": "milestone coordination framework",
                "timeline_optimization": ["timeline optimization strategies"],
                "schedule_risk_management": "timeline risk management",
                "timeline_feasibility_score": 0.0-1.0
            },
            "quality_assurance": {
                "review_processes": ["comprehensive review processes"],
                "excellence_verification": ["excellence verification systems"],
                "quality_control": "quality control framework",
                "quality_optimization": ["quality improvement strategies"],
                "quality_assurance_score": 0.0-1.0
            },
            "success_optimization": {
                "competitive_advantage_enhancement": ["advantage enhancement strategies"],
                "positioning_strategies": ["positioning optimization strategies"],
                "success_maximization": ["success maximization approaches"],
                "optimization_framework": "comprehensive optimization framework",
                "success_optimization_score": 0.0-1.0
            },
            "performance_monitoring": {
                "success_tracking": "success tracking framework",
                "continuous_improvement": "continuous improvement integration",
                "performance_metrics": ["performance monitoring metrics"],
                "monitoring_optimization": ["monitoring system optimization"],
                "monitoring_effectiveness_score": 0.0-1.0
            }
        }
    },
    "comprehensive_implementation_decision": {
        "final_go_no_go_recommendation": "proceed|proceed_with_modifications|defer|reject",
        "recommendation_confidence": 0.0-1.0,
        "decision_rationale": "comprehensive decision reasoning",
        "implementation_priority": "immediate|high|medium|low",
        "resource_commitment_level": "minimal|moderate|substantial|comprehensive",
        "success_probability_final": 0.0-1.0,
        "roi_projection": 0.0-10.0,
        "strategic_value_assessment": "exceptional|high|medium|limited|minimal",
        "implementation_readiness": "ready|conditional|preparation_needed|not_ready",
        "key_success_factors": ["top 5 critical implementation success factors"],
        "critical_risks": ["top 3 critical implementation risks"],
        "next_steps": ["specific actionable next steps"],
        "implementation_timeline": "immediate|1-3_months|3-6_months|6-12_months|long_term",
        "decision_confidence_level": 0.0-1.0
    }
}
"""
        
        return prompt
    
    def _make_real_openai_api_call(self, prompt: str, model: str, tab_name: str) -> Dict[str, Any]:
        """Make real OpenAI API call"""
        
        try:
            self.results_logger.logger.info(f"Making real OpenAI API call with model: {model}")
            
            # Use GPT-5 models directly (no mapping needed)
            actual_model = model
            self.results_logger.logger.info(f"Using model: {actual_model}")
            
            # Build API parameters
            api_params = {
                "model": actual_model,
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are an expert grant research analyst. Respond only in valid JSON format as requested."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "timeout": self.cost_tracker.controls.timeout_seconds
            }
            
            # Add temperature for supported models
            if not actual_model.startswith("o1"):
                api_params["temperature"] = 0.3
            
            # Use appropriate token parameter based on model
            if actual_model.startswith("o1"):
                api_params["max_completion_tokens"] = self.cost_tracker.controls.token_limits.get(model, 2000)
            else:
                api_params["max_tokens"] = self.cost_tracker.controls.token_limits.get(model, 2000)
            
            response = self.openai_client.chat.completions.create(**api_params)
            
            # Extract response data
            api_response = {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason,
                "response_id": response.id
            }
            
            self.results_logger.logger.info(f"[SUCCESS] API call successful - Tokens: {api_response['usage']['total_tokens']}")
            return api_response
            
        except Exception as e:
            self.results_logger.logger.error(f"[ERROR] OpenAI API call failed: {e}")
            raise
    
    def _process_ai_response(self, tab_name: str, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate AI response"""
        
        try:
            # Extract content from API response
            content = api_response.get("content", "")
            
            # Parse JSON response
            if content.startswith("{") and content.endswith("}"):
                parsed_response = json.loads(content)
            else:
                # Handle non-JSON responses
                parsed_response = {"raw_response": content}
            
            # Add metadata
            processed_output = {
                "tab": tab_name,
                "timestamp": datetime.now().isoformat(),
                "model_used": api_response.get("model", "unknown"),
                "tokens_used": api_response.get("usage", {}).get("total_tokens", 0),
                "parsed_response": parsed_response,
                "processing_success": True
            }
            
            return processed_output
            
        except Exception as e:
            return {
                "tab": tab_name,
                "timestamp": datetime.now().isoformat(),
                "processing_success": False,
                "error": str(e),
                "raw_content": api_response.get("content", "")
            }
    
    def test_complete_workflow(self) -> Dict[str, Any]:
        """Test all 4 processors in sequence"""
        
        self.results_logger.logger.info("\nStarting Complete Workflow Test (All 4 Processors)")
        
        workflow_results = {
            "session_id": self.results_logger.session_id,
            "start_time": datetime.now().isoformat(),
            "processors": {},
            "total_cost": 0.0,
            "success": True
        }
        
        previous_results = None
        
        # Test each processor in sequence
        for tab_name in ["PLAN", "ANALYZE", "EXAMINE", "APPROACH"]:
            self.results_logger.logger.info(f"\n--- Processing {tab_name} Tab ---")
            
            result = self.test_processor_by_tab(tab_name, previous_results)
            workflow_results["processors"][tab_name] = result
            
            if result["success"]:
                # Pass results to next processor
                previous_results = result.get("output", {})
                workflow_results["total_cost"] += result["metrics"]["cost_usd"]
            else:
                workflow_results["success"] = False
                self.results_logger.logger.error(f"[FAILED] Workflow failed at {tab_name} tab")
                break
        
        workflow_results["end_time"] = datetime.now().isoformat()
        workflow_results["final_budget_remaining"] = self.cost_tracker.get_remaining_budget()
        
        # Save complete workflow results
        workflow_file = self.results_logger.session_dir / "complete_workflow_results.json"
        with open(workflow_file, 'w', encoding='utf-8') as f:
            json.dump(workflow_results, f, indent=2, ensure_ascii=False)
        
        if workflow_results["success"]:
            self.results_logger.logger.info(f"[SUCCESS] Complete workflow test successful!")
            self.results_logger.logger.info(f"   Total cost: ${workflow_results['total_cost']:.4f}")
            self.results_logger.logger.info(f"   Budget remaining: ${workflow_results['final_budget_remaining']:.4f}")
        else:
            self.results_logger.logger.error("[FAILED] Complete workflow test failed")
        
        return workflow_results
    
    def generate_review_report(self) -> Dict[str, Any]:
        """Generate comprehensive report for validation"""
        
        report = {
            "session_id": self.results_logger.session_id,
            "test_summary": "Real Data AI Processor Testing",
            "timestamp": datetime.now().isoformat(),
            "test_data_used": {
                "nonprofit": self.test_data["nonprofit"]["organization"]["name"],
                "opportunity": self.test_data["opportunity"]["data"]["funding_opportunity_title"]
            },
            "budget_analysis": {
                "total_budget": self.cost_tracker.max_budget,
                "total_spent": self.cost_tracker.total_cost,
                "remaining": self.cost_tracker.get_remaining_budget(),
                "processor_costs": self.cost_tracker.processor_costs
            },
            "files_generated": [],
            "review_instructions": {
                "input_packages": "Review processor_input_[tab].json files for complete AI input data",
                "ai_prompts": "Review processor_prompt_[tab].txt files for exact prompts sent to AI",
                "ai_responses": "Review processor_response_[tab].json files for raw AI responses", 
                "processed_outputs": "Review processor_output_[tab].json files for final results",
                "performance": "Review test_metrics.json for cost and performance data"
            }
        }
        
        # List all generated files
        for file_path in self.results_logger.session_dir.iterdir():
            if file_path.is_file():
                report["files_generated"].append(file_path.name)
        
        # Save review report
        report_file = self.results_logger.session_dir / "REVIEW_REPORT.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.results_logger.logger.info(f"[REPORT] Review report generated: {report_file}")
        self.results_logger.logger.info(f"[RESULTS] All test results saved in: {self.results_logger.session_dir}")
        
        return report


def main():
    """Main execution function"""
    
    print("Real Data AI Processor Testing Framework")
    print("=" * 50)
    
    # Check for API key argument
    import sys
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        if api_key.startswith('sk-'):
            import os
            os.environ['OPENAI_API_KEY'] = api_key
            print("[INFO] Using API key from command line argument")
        else:
            print("[ERROR] Invalid API key format. Must start with 'sk-'")
            return
    
    # Initialize tester
    tester = RealDataAITester()
    
    # Test options
    print("\nTest Options:")
    print("1. Test individual processor by tab")
    print("2. Test complete workflow (all 4 processors)")
    print("3. Generate review report only")
    
    # Auto-select complete workflow test for demonstration
    choice = "2"
    print(f"\nAuto-selecting option {choice}: Complete workflow test")
    
    if choice == "1":
        print("\nAvailable tabs:")
        for i, tab in enumerate(["PLAN", "ANALYZE", "EXAMINE", "APPROACH"], 1):
            config = tester.processors[tab]
            print(f"{i}. {tab} - {config['name']} (${config['estimated_cost']:.4f})")
        
        tab_choice = input("Select tab (1-4): ").strip()
        tab_map = {"1": "PLAN", "2": "ANALYZE", "3": "EXAMINE", "4": "APPROACH"}
        
        if tab_choice in tab_map:
            tab_name = tab_map[tab_choice]
            result = tester.test_processor_by_tab(tab_name)
            
            if result["success"]:
                print(f"\n[SUCCESS] {tab_name} tab test completed successfully!")
            else:
                print(f"\n[FAILED] {tab_name} tab test failed: {result.get('error', 'Unknown error')}")
        else:
            print("Invalid selection")
    
    elif choice == "2":
        result = tester.test_complete_workflow()
        
        if result["success"]:
            print(f"\n[SUCCESS] Complete workflow test successful!")
            print(f"Total cost: ${result['total_cost']:.4f}")
        else:
            print("\n[FAILED] Workflow test failed")
    
    elif choice == "3":
        report = tester.generate_review_report()
        print(f"\n[REPORT] Review report generated")
        print(f"Files: {len(report['files_generated'])} files created")
    
    else:
        print("Invalid selection")
    
    # Generate final review report
    final_report = tester.generate_review_report()
    print(f"\n[RESULTS] All results saved in: {tester.results_logger.session_dir}")
    print(f"[REPORT] Review report: REVIEW_REPORT.json")
    
    print("\n" + "=" * 50)
    print("Testing complete! Review the generated files to validate processor performance.")


if __name__ == "__main__":
    main()