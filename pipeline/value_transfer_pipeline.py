from dataclasses import dataclass
from typing import Dict, List, Optional

from compliance.compliance_agent import ComplianceAgent
from compliance.compliance_models import (
    ComplianceContext,
    ComplianceDecision,
)
from eligibility.eligibility_agent import EligibilityAgent
from eligibility.eligibility_models import EligibilityDecision
from intelligence.intelligence_models import (
    Evidence,
    RouteIntelligence,
)
from intelligence.route_intelligence_agent import RouteIntelligenceAgent
from intent.value_transfer_intent import ValueTransferIntent
from models.contracts import CandidateRoute
from recommendation.recommendation_agent import RecommendationAgent
from recommendation.recommendation_models import RecommendationDecision
from route_discovery.route_discovery_agent import RouteDiscoveryAgent
from route_selection.route_selection_agent import RouteSelectionAgent
from route_selection.route_selection_models import RouteSelectionDecision


@dataclass(frozen=True)
class ValueTransferPipelineResult:
    """
    Complete output of the Value Transfer Engine AI pipeline.

    The result preserves the outputs of every AI stage so that the complete
    decision path remains inspectable and traceable.
    """

    intent: ValueTransferIntent
    candidate_routes: List[CandidateRoute]
    route_intelligence: Dict[str, RouteIntelligence]
    compliance_decisions: Dict[str, ComplianceDecision]
    eligibility_decisions: Dict[str, EligibilityDecision]
    selection: RouteSelectionDecision
    recommendation: RecommendationDecision


class ValueTransferPipeline:
    """
    Coordinates the AI stages of the Value Transfer Engine.

    This class performs orchestration only.

    It does not perform route discovery, intelligence investigation,
    compliance evaluation, eligibility determination, route selection,
    or recommendation reasoning itself.
    """

    def __init__(
        self,
        discovery_agent: RouteDiscoveryAgent,
        intelligence_agent: RouteIntelligenceAgent,
        compliance_agent: ComplianceAgent,
        eligibility_agent: EligibilityAgent,
        selection_agent: RouteSelectionAgent,
        recommendation_agent: RecommendationAgent,
    ):
        self.discovery_agent = discovery_agent
        self.intelligence_agent = intelligence_agent
        self.compliance_agent = compliance_agent
        self.eligibility_agent = eligibility_agent
        self.selection_agent = selection_agent
        self.recommendation_agent = recommendation_agent

    def run(
        self,
        intent: ValueTransferIntent,
        compliance_context: ComplianceContext,
        evidence: Optional[List[Evidence]] = None,
    ) -> ValueTransferPipelineResult:

        # --------------------------------------------------------------
        # 1. AI ROUTE DISCOVERY
        # --------------------------------------------------------------
        candidate_routes = self.discovery_agent.discover(
            intent=intent,
        )

        # --------------------------------------------------------------
        # 2. AI ROUTE INTELLIGENCE
        # --------------------------------------------------------------
        route_intelligence: Dict[str, RouteIntelligence] = {}

        for route in candidate_routes:
            route_intelligence[route.route_id] = (
                self.intelligence_agent.investigate(
                    intent=intent,
                    route=route,
                    evidence=evidence,
                )
            )

        # --------------------------------------------------------------
        # 3. AI COMPLIANCE EVALUATION
        # --------------------------------------------------------------
        compliance_decisions: Dict[str, ComplianceDecision] = {}

        for route in candidate_routes:
            compliance_decisions[route.route_id] = (
                self.compliance_agent.evaluate(
                    intent=intent,
                    route=route,
                    route_intelligence=route_intelligence[route.route_id],
                    compliance_context=compliance_context,
                    evidence=evidence,
                )
            )

        # --------------------------------------------------------------
        # 4. AI ELIGIBILITY DECISION
        # --------------------------------------------------------------
        eligibility_decisions: Dict[str, EligibilityDecision] = {}

        for route in candidate_routes:
            eligibility_decisions[route.route_id] = (
                self.eligibility_agent.evaluate(
                    intent=intent,
                    route=route,
                    compliance=compliance_decisions[route.route_id],
                    intelligence=route_intelligence[route.route_id],
                )
            )

        # --------------------------------------------------------------
        # 5. AI ROUTE SELECTION
        # --------------------------------------------------------------
        selection = self.selection_agent.select(
            intent=intent,
            routes=candidate_routes,
            intelligence=route_intelligence,
            compliance=compliance_decisions,
            eligibility=eligibility_decisions,
        )

        # --------------------------------------------------------------
        # 6. AI RECOMMENDATION
        # --------------------------------------------------------------
        recommendation = self.recommendation_agent.recommend(
            intent=intent,
            routes=candidate_routes,
            intelligence=route_intelligence,
            compliance=compliance_decisions,
            eligibility=eligibility_decisions,
            selection=selection,
        )

        # --------------------------------------------------------------
        # COMPLETE PIPELINE RESULT
        # --------------------------------------------------------------
        return ValueTransferPipelineResult(
            intent=intent,
            candidate_routes=candidate_routes,
            route_intelligence=route_intelligence,
            compliance_decisions=compliance_decisions,
            eligibility_decisions=eligibility_decisions,
            selection=selection,
            recommendation=recommendation,
        )
