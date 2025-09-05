# API Endpoints & User Interface Design
## Modular Grant Intelligence Service

**Document Version**: 1.0  
**Date**: August 31, 2025  
**Integration**: FastAPI backend + Alpine.js frontend  
**Foundation**: Existing web interface at http://localhost:8000

---

## **API ENDPOINT SPECIFICATIONS**

### **Core Tier Selection API**

#### **POST /api/profiles/{profile_id}/intelligence-analysis**
*Primary endpoint for generating tiered intelligence analysis*

```python
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class ServiceTier(str, Enum):
    CURRENT = "current"
    STANDARD = "standard"
    ENHANCED = "enhanced" 
    COMPLETE = "complete"

class AddOnModule(str, Enum):
    BOARD_NETWORK = "board_network_analysis"
    DECISION_MAKER = "decision_maker_intelligence"
    RFP_ANALYSIS = "complete_rfp_analysis"
    HISTORICAL_PATTERNS = "historical_success_patterns"
    WARM_INTRODUCTIONS = "warm_introduction_pathways"
    COMPETITIVE_ANALYSIS = "competitive_deep_dive"

class IntelligenceRequest(BaseModel):
    opportunity_id: str
    tier: ServiceTier
    add_ons: Optional[List[AddOnModule]] = []
    custom_priorities: Optional[dict] = None

class IntelligenceResponse(BaseModel):
    task_id: Optional[str] = None  # For async processing
    result: Optional[dict] = None  # For immediate results
    estimated_cost: float
    actual_cost: Optional[float] = None
    estimated_completion_time: str
    status: str  # "processing", "completed", "failed"
    
@app.post("/api/profiles/{profile_id}/intelligence-analysis", response_model=IntelligenceResponse)
async def generate_intelligence_analysis(
    profile_id: str,
    request: IntelligenceRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate tiered intelligence analysis
    
    Flow:
    1. Validate profile and opportunity
    2. Calculate estimated cost
    3. Route to appropriate processor based on tier
    4. Return immediate results (Current/Standard) or task ID (Enhanced/Complete)
    """
    # Cost calculation
    cost_calculator = TierCostCalculator()
    estimated_cost = cost_calculator.calculate_cost(request.tier, request.add_ons)
    
    # Processor selection
    processor_factory = ProcessorFactory()
    processor = processor_factory.get_processor(request.tier)
    
    # Async processing for complex tiers
    if request.tier in [ServiceTier.ENHANCED, ServiceTier.COMPLETE]:
        task_id = await queue_analysis_task(profile_id, request)
        background_tasks.add_task(process_analysis_task, task_id, processor, profile_id, request)
        
        return IntelligenceResponse(
            task_id=task_id,
            estimated_cost=estimated_cost,
            estimated_completion_time=get_tier_time_estimate(request.tier),
            status="processing"
        )
    
    # Immediate processing for simple tiers
    result = await processor.process_opportunity(profile_id, request.opportunity_id, request.add_ons)
    
    return IntelligenceResponse(
        result=result.to_dict(),
        estimated_cost=estimated_cost,
        actual_cost=result.processing_cost,
        estimated_completion_time="completed",
        status="completed"
    )
```

#### **GET /api/intelligence-analysis/{task_id}**
*Check status and retrieve results for background tasks*

```python
class TaskStatus(BaseModel):
    task_id: str
    status: str  # "queued", "processing", "completed", "failed"
    progress_percentage: int
    estimated_completion: Optional[str] = None
    result: Optional[dict] = None
    error_message: Optional[str] = None
    processing_cost: Optional[float] = None

@app.get("/api/intelligence-analysis/{task_id}", response_model=TaskStatus)
async def get_analysis_status(task_id: str):
    """
    Get processing status and results for background analysis tasks
    """
    task_manager = TaskManager()
    task_status = await task_manager.get_task_status(task_id)
    
    return TaskStatus(
        task_id=task_id,
        status=task_status.status,
        progress_percentage=task_status.progress,
        estimated_completion=task_status.eta.isoformat() if task_status.eta else None,
        result=task_status.result.to_dict() if task_status.result else None,
        error_message=task_status.error_message,
        processing_cost=task_status.actual_cost
    )
```

### **Cost Calculation & Recommendations API**

#### **POST /api/cost-estimate**
*Real-time cost calculation for tier selection interface*

```python
class CostEstimateRequest(BaseModel):
    tier: ServiceTier
    add_ons: Optional[List[AddOnModule]] = []
    opportunity_type: Optional[str] = None  # "government", "foundation", "corporate"
    opportunity_size: Optional[str] = None  # "small", "medium", "large"

class CostBreakdown(BaseModel):
    api_tokens: float
    infrastructure: float
    platform_margin: float
    total: float

class ValueComparison(BaseModel):
    consultant_equivalent_hours: float
    consultant_cost_range: dict  # {"min": 200, "max": 400}
    savings_range: dict  # {"min": 175, "max": 375}
    roi_multiplier: float  # 27x-53x savings

class CostEstimateResponse(BaseModel):
    tier: ServiceTier
    add_ons: List[AddOnModule]
    cost_breakdown: CostBreakdown
    estimated_delivery_time: str
    poc_effort_required: str  # "0 hours", "1-2 hours", etc.
    value_comparison: ValueComparison

@app.post("/api/cost-estimate", response_model=CostEstimateResponse)
async def calculate_cost_estimate(request: CostEstimateRequest):
    """
    Calculate detailed cost estimate for tier selection
    """
    calculator = TierCostCalculator()
    
    # Base tier cost
    tier_cost = calculator.get_tier_cost(request.tier)
    
    # Add-on costs
    addon_costs = [calculator.get_addon_cost(addon) for addon in request.add_ons]
    
    # Adjustments based on opportunity characteristics
    adjustments = calculator.calculate_adjustments(request.opportunity_type, request.opportunity_size)
    
    total_cost = tier_cost + sum(addon_costs) + adjustments
    
    # Value comparison
    consultant_hours = calculator.estimate_consultant_hours(request.tier, request.add_ons)
    consultant_cost_range = {
        "min": consultant_hours * 50,  # $50/hour junior researcher
        "max": consultant_hours * 100  # $100/hour senior consultant
    }
    
    return CostEstimateResponse(
        tier=request.tier,
        add_ons=request.add_ons,
        cost_breakdown=CostBreakdown(
            api_tokens=calculator.get_api_cost(request.tier, request.add_ons),
            infrastructure=calculator.get_infrastructure_cost(request.tier, request.add_ons),
            platform_margin=calculator.get_platform_margin(request.tier, request.add_ons),
            total=total_cost
        ),
        estimated_delivery_time=calculator.get_delivery_time(request.tier),
        poc_effort_required=calculator.get_poc_effort(request.tier),
        value_comparison=ValueComparison(
            consultant_equivalent_hours=consultant_hours,
            consultant_cost_range=consultant_cost_range,
            savings_range={
                "min": consultant_cost_range["min"] - total_cost,
                "max": consultant_cost_range["max"] - total_cost
            },
            roi_multiplier=consultant_cost_range["min"] / total_cost
        )
    )
```

#### **GET /api/profiles/{profile_id}/tier-recommendations**
*Smart tier recommendations based on profile and opportunity characteristics*

```python
class TierRecommendation(BaseModel):
    recommended_tier: ServiceTier
    recommended_add_ons: List[AddOnModule]
    confidence_score: float  # 0.0-1.0
    reasoning: str
    cost_estimate: float
    alternative_configurations: List[dict]

@app.get("/api/profiles/{profile_id}/tier-recommendations")
async def get_tier_recommendations(
    profile_id: str,
    opportunity_id: str
) -> TierRecommendation:
    """
    AI-powered tier recommendations based on profile and opportunity analysis
    """
    # Analyze profile characteristics
    profile_analyzer = ProfileAnalyzer()
    profile_analysis = await profile_analyzer.analyze_profile(profile_id)
    
    # Analyze opportunity characteristics  
    opportunity_analyzer = OpportunityAnalyzer()
    opportunity_analysis = await opportunity_analyzer.analyze_opportunity(opportunity_id)
    
    # Generate recommendations
    recommender = TierRecommendationEngine()
    recommendation = recommender.generate_recommendation(profile_analysis, opportunity_analysis)
    
    return TierRecommendation(
        recommended_tier=recommendation.tier,
        recommended_add_ons=recommendation.add_ons,
        confidence_score=recommendation.confidence,
        reasoning=recommendation.rationale,
        cost_estimate=recommendation.estimated_cost,
        alternative_configurations=recommendation.alternatives
    )
```

### **Tier Configuration & Defaults API**

#### **GET /api/tier-configurations**
*Available tiers, features, and pricing information*

```python
class TierFeature(BaseModel):
    name: str
    description: str
    included: bool

class TierConfiguration(BaseModel):
    tier: ServiceTier
    name: str
    price: float
    delivery_time: str
    poc_effort: str
    features: List[TierFeature]
    best_for: List[str]  # Use cases this tier is optimized for

@app.get("/api/tier-configurations")
async def get_tier_configurations() -> List[TierConfiguration]:
    """
    Get all available tier configurations and features
    """
    return [
        TierConfiguration(
            tier=ServiceTier.CURRENT,
            name="Current Intelligence",
            price=0.75,
            delivery_time="5-10 minutes",
            poc_effort="0 hours",
            features=[
                TierFeature(name="4-Stage AI Analysis", description="PLAN → ANALYZE → EXAMINE → APPROACH", included=True),
                TierFeature(name="Strategic Scoring", description="Multi-dimensional fit analysis", included=True),
                TierFeature(name="Risk Assessment", description="Competition, technical, compliance risks", included=True),
                TierFeature(name="Success Probability", description="75-80% likelihood modeling", included=True),
                TierFeature(name="Implementation Roadmap", description="Resource allocation and timeline", included=True),
                TierFeature(name="Historical Analysis", description="Funding patterns and trends", included=False),
                TierFeature(name="RFP Analysis", description="Complete requirements extraction", included=False),
                TierFeature(name="Network Intelligence", description="Board member relationship mapping", included=False)
            ],
            best_for=["Quick opportunity assessment", "Initial screening", "Budget-conscious analysis"]
        ),
        TierConfiguration(
            tier=ServiceTier.STANDARD,
            name="Standard Intelligence",
            price=7.50,
            delivery_time="15-20 minutes",
            poc_effort="0 hours",
            features=[
                TierFeature(name="4-Stage AI Analysis", description="PLAN → ANALYZE → EXAMINE → APPROACH", included=True),
                TierFeature(name="Strategic Scoring", description="Multi-dimensional fit analysis", included=True),
                TierFeature(name="Risk Assessment", description="Competition, technical, compliance risks", included=True),
                TierFeature(name="Success Probability", description="75-80% likelihood modeling", included=True),
                TierFeature(name="Implementation Roadmap", description="Resource allocation and timeline", included=True),
                TierFeature(name="Historical Analysis", description="5-year funding patterns and trends", included=True),
                TierFeature(name="Geographic Intelligence", description="Regional funding distribution", included=True),
                TierFeature(name="Success Factor Analysis", description="Common winning characteristics", included=True),
                TierFeature(name="RFP Analysis", description="Complete requirements extraction", included=False),
                TierFeature(name="Network Intelligence", description="Board member relationship mapping", included=False)
            ],
            best_for=["Serious opportunity pursuit", "Proposal development", "Competitive intelligence"]
        ),
        # ... Enhanced and Complete tier configurations
    ]
```

---

## **USER INTERFACE DESIGN SPECIFICATIONS**

### **Tier Selection Interface**

#### **Main Tier Selection Component**
```html
<!-- Alpine.js Tier Selection Interface -->
<div x-data="tierSelector()" x-init="loadRecommendations()" class="tier-selection-container">
    
    <!-- Header Section -->
    <div class="tier-header">
        <h2>Select Intelligence Level</h2>
        <p class="opportunity-context">
            Analysis for: <strong x-text="opportunityName"></strong>
        </p>
        <div class="recommendation-badge" x-show="recommendedTier" 
             :class="'recommended-' + recommendedTier">
            <span class="badge-text">Recommended: </span>
            <span class="tier-name" x-text="getTierName(recommendedTier)"></span>
        </div>
    </div>
    
    <!-- Tier Selection Cards -->
    <div class="tier-cards-grid">
        <template x-for="tier in tierOptions" :key="tier.value">
            <div :class="['tier-card', { 
                'selected': selectedTier === tier.value,
                'recommended': recommendedTier === tier.value 
            }]"
                 @click="selectTier(tier.value)">
                
                <!-- Tier Header -->
                <div class="tier-card-header">
                    <h3 class="tier-name" x-text="tier.name"></h3>
                    <div class="tier-price">$<span x-text="tier.price"></span></div>
                    <div class="tier-time" x-text="tier.deliveryTime"></div>
                </div>
                
                <!-- Tier Features -->
                <div class="tier-features">
                    <template x-for="feature in tier.features">
                        <div :class="['feature-item', { 
                            'included': feature.included,
                            'excluded': !feature.included 
                        }]">
                            <span class="feature-icon" 
                                  x-text="feature.included ? '✓' : '○'"></span>
                            <span class="feature-name" x-text="feature.name"></span>
                        </div>
                    </template>
                </div>
                
                <!-- Best For Section -->
                <div class="tier-best-for">
                    <strong>Best For:</strong>
                    <ul>
                        <template x-for="useCase in tier.bestFor">
                            <li x-text="useCase"></li>
                        </template>
                    </ul>
                </div>
                
                <!-- Selection Button -->
                <button :class="['select-tier-btn', { 
                    'selected': selectedTier === tier.value 
                }]"
                        @click="selectTier(tier.value)">
                    <span x-show="selectedTier !== tier.value">Select This Tier</span>
                    <span x-show="selectedTier === tier.value">✓ Selected</span>
                </button>
            </div>
        </template>
    </div>
    
    <!-- Add-On Modules Section -->
    <div class="add-ons-section" x-show="selectedTier">
        <h3>Additional Intelligence Modules</h3>
        <p class="add-ons-description">
            Enhance your analysis with specialized modules (optional)
        </p>
        
        <div class="add-ons-grid">
            <template x-for="addon in availableAddOns" :key="addon.value">
                <label :class="['addon-checkbox-card', { 
                    'selected': selectedAddOns.includes(addon.value),
                    'recommended': recommendedAddOns.includes(addon.value)
                }]">
                    <input type="checkbox" 
                           :value="addon.value" 
                           x-model="selectedAddOns"
                           @change="updateCostEstimate()"
                           class="addon-checkbox">
                    
                    <div class="addon-content">
                        <div class="addon-header">
                            <strong class="addon-name" x-text="addon.name"></strong>
                            <span class="addon-price">+$<span x-text="addon.price"></span></span>
                            <div class="addon-impact-badge" 
                                 :class="'impact-' + addon.impact.toLowerCase()"
                                 x-text="addon.impact + ' Impact'">
                            </div>
                        </div>
                        
                        <p class="addon-description" x-text="addon.description"></p>
                        
                        <div class="addon-value">
                            <strong>Value:</strong> <span x-text="addon.valueProposition"></span>
                        </div>
                    </div>
                </label>
            </template>
        </div>
    </div>
    
    <!-- Cost Summary & Checkout -->
    <div class="cost-summary-section" x-show="selectedTier">
        <div class="cost-summary-card">
            <h3>Analysis Summary</h3>
            
            <!-- Cost Breakdown -->
            <div class="cost-breakdown">
                <div class="cost-line-item">
                    <span class="item-name" x-text="getTierName(selectedTier) + ' Tier'"></span>
                    <span class="item-cost">$<span x-text="getBaseTierCost()"></span></span>
                </div>
                
                <template x-for="addon in selectedAddOns">
                    <div class="cost-line-item add-on-item">
                        <span class="item-name" x-text="getAddOnName(addon)"></span>
                        <span class="item-cost">+$<span x-text="getAddOnCost(addon)"></span></span>
                    </div>
                </template>
                
                <div class="cost-total-line">
                    <strong>
                        <span>Total Cost:</span>
                        <span>$<span x-text="totalCost"></span></span>
                    </strong>
                </div>
            </div>
            
            <!-- Value Comparison -->
            <div class="value-comparison" x-show="costEstimate">
                <div class="comparison-item">
                    <span class="comparison-label">vs Professional Consultant:</span>
                    <span class="comparison-value">
                        $<span x-text="costEstimate?.value_comparison?.consultant_cost_range?.min"></span>-
                        <span x-text="costEstimate?.value_comparison?.consultant_cost_range?.max"></span>
                    </span>
                </div>
                <div class="savings-highlight">
                    <span class="savings-label">Your Savings:</span>
                    <span class="savings-amount">
                        $<span x-text="costEstimate?.value_comparison?.savings_range?.min"></span>-
                        <span x-text="costEstimate?.value_comparison?.savings_range?.max"></span>
                    </span>
                    <span class="savings-multiplier">
                        (<span x-text="Math.floor(costEstimate?.value_comparison?.roi_multiplier || 0)"></span>x savings)
                    </span>
                </div>
            </div>
            
            <!-- Delivery Information -->
            <div class="delivery-info">
                <div class="delivery-item">
                    <span class="delivery-label">Estimated Delivery:</span>
                    <span class="delivery-value" x-text="getEstimatedTime()"></span>
                </div>
                <div class="delivery-item">
                    <span class="delivery-label">Your Effort Required:</span>
                    <span class="delivery-value" x-text="getPOCEffort()"></span>
                </div>
            </div>
            
            <!-- Action Buttons -->
            <div class="action-buttons">
                <button class="preview-analysis-btn" 
                        @click="previewAnalysis()"
                        :disabled="loading">
                    Preview Analysis Scope
                </button>
                
                <button class="generate-analysis-btn primary-btn" 
                        @click="generateAnalysis()"
                        :disabled="loading || !selectedTier">
                    <span x-show="!loading">Generate Intelligence Analysis</span>
                    <span x-show="loading" class="loading-spinner">
                        <span class="spinner"></span> Processing...
                    </span>
                </button>
            </div>
        </div>
    </div>
</div>
```

#### **Alpine.js Component Logic**
```javascript
function tierSelector() {
    return {
        // Data Properties
        selectedTier: null,
        selectedAddOns: [],
        recommendedTier: null,
        recommendedAddOns: [],
        tierOptions: [],
        availableAddOns: [],
        costEstimate: null,
        loading: false,
        opportunityName: '',
        profileId: null,
        opportunityId: null,
        
        // Computed Properties
        get totalCost() {
            if (!this.costEstimate) return 0;
            return this.costEstimate.cost_breakdown.total;
        },
        
        // Initialization
        async init() {
            await this.loadTierConfigurations();
            await this.loadRecommendations();
            this.setDefaultSelections();
        },
        
        // API Integration Methods
        async loadTierConfigurations() {
            try {
                const response = await fetch('/api/tier-configurations');
                this.tierOptions = await response.json();
                
                const addOnsResponse = await fetch('/api/add-on-modules');
                this.availableAddOns = await addOnsResponse.json();
            } catch (error) {
                console.error('Failed to load tier configurations:', error);
                this.showError('Failed to load tier options. Please refresh the page.');
            }
        },
        
        async loadRecommendations() {
            if (!this.profileId || !this.opportunityId) return;
            
            try {
                const response = await fetch(
                    `/api/profiles/${this.profileId}/tier-recommendations?opportunity_id=${this.opportunityId}`
                );
                const recommendations = await response.json();
                
                this.recommendedTier = recommendations.recommended_tier;
                this.recommendedAddOns = recommendations.recommended_add_ons;
                
                // Auto-select recommended options
                this.selectedTier = this.recommendedTier;
                this.selectedAddOns = [...this.recommendedAddOns];
                
                await this.updateCostEstimate();
            } catch (error) {
                console.error('Failed to load recommendations:', error);
                // Continue with manual selection
            }
        },
        
        async updateCostEstimate() {
            if (!this.selectedTier) return;
            
            this.loading = true;
            try {
                const response = await fetch('/api/cost-estimate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        tier: this.selectedTier,
                        add_ons: this.selectedAddOns,
                        opportunity_type: this.getOpportunityType()
                    })
                });
                
                this.costEstimate = await response.json();
            } catch (error) {
                console.error('Failed to calculate cost estimate:', error);
                this.showError('Failed to calculate cost. Please try again.');
            } finally {
                this.loading = false;
            }
        },
        
        async generateAnalysis() {
            if (!this.selectedTier) return;
            
            this.loading = true;
            try {
                const response = await fetch(`/api/profiles/${this.profileId}/intelligence-analysis`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        opportunity_id: this.opportunityId,
                        tier: this.selectedTier,
                        add_ons: this.selectedAddOns
                    })
                });
                
                const result = await response.json();
                
                if (result.task_id) {
                    // Redirect to processing status page
                    window.location.href = `/analysis-status/${result.task_id}`;
                } else {
                    // Show immediate results
                    this.showResults(result.result);
                }
            } catch (error) {
                console.error('Failed to generate analysis:', error);
                this.showError('Failed to generate analysis. Please try again.');
            } finally {
                this.loading = false;
            }
        },
        
        // Helper Methods
        selectTier(tierValue) {
            this.selectedTier = tierValue;
            this.updateCostEstimate();
        },
        
        getTierName(tierValue) {
            const tier = this.tierOptions.find(t => t.tier === tierValue);
            return tier ? tier.name : '';
        },
        
        getBaseTierCost() {
            const tier = this.tierOptions.find(t => t.tier === this.selectedTier);
            return tier ? tier.price : 0;
        },
        
        getAddOnName(addOnValue) {
            const addon = this.availableAddOns.find(a => a.value === addOnValue);
            return addon ? addon.name : '';
        },
        
        getAddOnCost(addOnValue) {
            const addon = this.availableAddOns.find(a => a.value === addOnValue);
            return addon ? addon.price : 0;
        },
        
        getEstimatedTime() {
            if (!this.costEstimate) return 'Calculating...';
            return this.costEstimate.estimated_delivery_time;
        },
        
        getPOCEffort() {
            if (!this.costEstimate) return 'Calculating...';
            return this.costEstimate.poc_effort_required;
        },
        
        getOpportunityType() {
            // Determine opportunity type based on opportunity data
            // This would be passed in from the parent component
            return this.opportunityType || 'unknown';
        },
        
        showError(message) {
            // Integration with existing error handling system
            this.$dispatch('show-error', { message });
        },
        
        showResults(results) {
            // Integration with existing results display system
            this.$dispatch('show-results', { results });
        }
    }
}
```

### **Processing Status Interface**
```html
<!-- Analysis Processing Status Page -->
<div x-data="analysisStatus()" x-init="startStatusPolling()" class="analysis-status-container">
    
    <!-- Status Header -->
    <div class="status-header">
        <h2>Generating Intelligence Analysis</h2>
        <p class="analysis-details">
            <strong x-text="tierName"></strong> analysis for <strong x-text="opportunityName"></strong>
        </p>
    </div>
    
    <!-- Progress Indicator -->
    <div class="progress-section">
        <div class="progress-bar-container">
            <div class="progress-bar" :style="`width: ${progressPercentage}%`"></div>
        </div>
        <div class="progress-text">
            <span x-text="progressPercentage"></span>% Complete
        </div>
        <div class="status-message" x-text="statusMessage"></div>
    </div>
    
    <!-- Processing Steps -->
    <div class="processing-steps">
        <template x-for="step in processingSteps" :key="step.id">
            <div :class="['processing-step', step.status]">
                <div class="step-icon">
                    <span x-show="step.status === 'completed'">✓</span>
                    <span x-show="step.status === 'processing'" class="spinner"></span>
                    <span x-show="step.status === 'pending'">○</span>
                </div>
                <div class="step-content">
                    <h4 x-text="step.name"></h4>
                    <p x-text="step.description"></p>
                    <div x-show="step.status === 'processing'" class="step-details">
                        <span x-text="step.current_action"></span>
                    </div>
                </div>
            </div>
        </template>
    </div>
    
    <!-- Estimated Completion -->
    <div class="completion-estimate" x-show="estimatedCompletion">
        <strong>Estimated Completion:</strong> <span x-text="estimatedCompletion"></span>
    </div>
    
    <!-- Results Section (shown when complete) -->
    <div x-show="status === 'completed'" class="results-section">
        <div class="results-header">
            <h3>Analysis Complete!</h3>
            <div class="cost-summary">
                Final Cost: $<span x-text="actualCost"></span>
            </div>
        </div>
        
        <div class="results-actions">
            <button @click="viewResults()" class="view-results-btn primary-btn">
                View Intelligence Report
            </button>
            <button @click="downloadReport()" class="download-btn secondary-btn">
                Download PDF Report
            </button>
            <button @click="shareResults()" class="share-btn secondary-btn">
                Share with Team
            </button>
        </div>
    </div>
    
    <!-- Error Handling -->
    <div x-show="status === 'failed'" class="error-section">
        <div class="error-header">
            <h3>Analysis Failed</h3>
        </div>
        <div class="error-message" x-text="errorMessage"></div>
        <div class="error-actions">
            <button @click="retryAnalysis()" class="retry-btn primary-btn">
                Retry Analysis
            </button>
            <button @click="contactSupport()" class="support-btn secondary-btn">
                Contact Support
            </button>
        </div>
    </div>
</div>
```

---

## **CSS STYLING SPECIFICATIONS**

### **Tier Selection Styling**
```css
/* Tier Selection Container */
.tier-selection-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 24px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Tier Cards Grid */
.tier-cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 24px;
    margin: 32px 0;
}

.tier-card {
    background: white;
    border: 2px solid #e5e7eb;
    border-radius: 12px;
    padding: 24px;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
}

.tier-card:hover {
    border-color: #3b82f6;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
    transform: translateY(-2px);
}

.tier-card.selected {
    border-color: #3b82f6;
    background: #f8faff;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
}

.tier-card.recommended::before {
    content: "Recommended";
    position: absolute;
    top: -8px;
    left: 24px;
    background: #10b981;
    color: white;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
}

/* Tier Card Content */
.tier-card-header {
    text-align: center;
    margin-bottom: 24px;
}

.tier-name {
    font-size: 24px;
    font-weight: 700;
    color: #1f2937;
    margin: 0 0 8px 0;
}

.tier-price {
    font-size: 32px;
    font-weight: 800;
    color: #3b82f6;
    margin-bottom: 4px;
}

.tier-time {
    color: #6b7280;
    font-size: 14px;
}

/* Feature List */
.tier-features {
    margin: 24px 0;
}

.feature-item {
    display: flex;
    align-items: center;
    padding: 8px 0;
    font-size: 14px;
}

.feature-item.included {
    color: #374151;
}

.feature-item.excluded {
    color: #9ca3af;
}

.feature-icon {
    width: 20px;
    margin-right: 12px;
    font-weight: bold;
}

.feature-item.included .feature-icon {
    color: #10b981;
}

.feature-item.excluded .feature-icon {
    color: #d1d5db;
}

/* Add-On Modules */
.add-ons-section {
    margin: 48px 0;
    padding: 32px;
    background: #f9fafb;
    border-radius: 12px;
}

.add-ons-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 16px;
    margin-top: 24px;
}

.addon-checkbox-card {
    display: block;
    background: white;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    padding: 20px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.addon-checkbox-card:hover {
    border-color: #3b82f6;
}

.addon-checkbox-card.selected {
    border-color: #3b82f6;
    background: #f8faff;
}

.addon-checkbox-card.recommended {
    border-color: #10b981;
    background: #f0fdf4;
}

.addon-checkbox {
    position: absolute;
    opacity: 0;
}

.addon-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.addon-impact-badge {
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}

.addon-impact-badge.impact-high {
    background: #fee2e2;
    color: #dc2626;
}

.addon-impact-badge.impact-medium {
    background: #fef3c7;
    color: #d97706;
}

.addon-impact-badge.impact-low {
    background: #e0e7ff;
    color: #3730a3;
}

/* Cost Summary */
.cost-summary-section {
    position: sticky;
    bottom: 24px;
    margin-top: 48px;
}

.cost-summary-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 32px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.cost-breakdown {
    margin: 24px 0;
}

.cost-line-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #f3f4f6;
}

.cost-total-line {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 0;
    border-top: 2px solid #e5e7eb;
    margin-top: 16px;
    font-size: 18px;
    font-weight: 700;
}

/* Value Comparison */
.value-comparison {
    background: #f0f9ff;
    border: 1px solid #0ea5e9;
    border-radius: 8px;
    padding: 16px;
    margin: 24px 0;
}

.savings-highlight {
    color: #10b981;
    font-weight: 600;
}

/* Action Buttons */
.action-buttons {
    display: flex;
    gap: 16px;
    margin-top: 32px;
}

.primary-btn {
    background: #3b82f6;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    flex: 1;
    transition: background 0.2s ease;
}

.primary-btn:hover {
    background: #2563eb;
}

.primary-btn:disabled {
    background: #9ca3af;
    cursor: not-allowed;
}

.secondary-btn {
    background: white;
    color: #374151;
    border: 1px solid #d1d5db;
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
}

.secondary-btn:hover {
    background: #f9fafb;
    border-color: #9ca3af;
}

/* Loading States */
.spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid #f3f4f6;
    border-top: 2px solid #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Responsive Design */
@media (max-width: 768px) {
    .tier-cards-grid {
        grid-template-columns: 1fr;
    }
    
    .add-ons-grid {
        grid-template-columns: 1fr;
    }
    
    .action-buttons {
        flex-direction: column;
    }
    
    .cost-summary-card {
        padding: 24px 20px;
    }
}
```

This comprehensive API and UI design provides a complete foundation for the modular grant intelligence service, with intuitive tier selection, real-time cost calculation, and professional presentation that guides users toward the optimal intelligence level for their needs.