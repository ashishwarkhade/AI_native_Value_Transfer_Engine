import json
from typing import Any, Dict, List

from ai.model_interface import AIModel, build_structured_context
from intent.value_transfer_intent import ValueTransferIntent
from models.contracts import CandidateRoute, RouteEndpoint


SYSTEM_PROMPT = """
You are the Route Discovery Agent of a Value Transfer Engine.

Your responsibility is to discover and expand possible candidate
routes for a user's value-transfer intent.

You are a DISCOVERY agent.

You must:
- identify plausible value-transfer mechanisms
- identify different payment rails
- identify different funding methods
- identify different delivery methods
- identify different provider/network paths where appropriate
- expand the candidate route universe beyond routes already known

You must NOT:
- declare a route legally permissible
- declare a route compliant
- declare a route eligible
- declare a route recommended
- invent provider capabilities as established facts
- treat a candidate as verified merely because it is plausible

Every route you return is only a CANDIDATE.

Candidate routes will subsequently be evaluated by:
1. Route Intelligence
2. Compliance
3. Eligibility

IMPORTANT OUTPUT CONTRACT:

Return ONLY valid JSON.

The top-level JSON value MUST be an object.

The object MUST contain exactly this primary structure:

{
  "routes": [
    {
      "route_id": "unique-route-id",
      "rail": "the operational payment or settlement rail actually used by this candidate",
      "source_country": "source country",
      "source_currency": "source currency",
      "destination_country": "destination country",
      "destination_currency": "destination currency",
      "funding_method": "funding mechanism used to initiate the transfer",
      "transfer_path": [
        "ordered operational step 1",
        "ordered operational step 2"
      ],
      "delivery_method": "how value is delivered to the destination",
      "corridor_availability": "CANDIDATE_DISCOVERED",
      "route_requirements": [
        "requirements that the candidate route actually depends on"
      ]
    }
  ]
}

Do NOT return the routes array directly.

SEMANTIC FIELD RULES:

- "rail" must identify the operational payment or settlement rail used by the candidate.
- "transfer_path" must describe the ordered operational path of the candidate.
- "route_requirements" must contain requirements the candidate route actually depends on.
- Do not describe a mechanism as used in one field and simultaneously describe it as
  excluded or unused in another field.
- If a mechanism is mentioned only as an alternative, exclusion, limitation, or
  comparison, do not represent it as the selected rail or an operational step.

Incorrect:
[
  {
    "route_id": "..."
  }
]

Correct:
{
  "routes": [
    {
      "route_id": "..."
    }
  ]
}
"""


def build_route_discovery_context(
    intent: ValueTransferIntent,
) -> Dict[str, Any]:
    """
    Build structured context for the Route Discovery Agent.

    This function does not determine whether any route is valid.
    """

    return {
        "intent": {
            "intent_id": intent.intent_id,
            "from_country": intent.from_country,
            "to_country": intent.to_country,
            "amount": intent.amount,
            "source_currency": intent.source_currency,
            "destination_currency": intent.destination_currency,
            "required_delivery_time": intent.required_delivery_time,
        }
    }


class RouteDiscoveryAgent:
    """
    AI-driven Route Discovery Agent.

    The model provider is injected through the AIModel interface.
    """

    def __init__(self, model: AIModel):
        self.model = model

    def discover(
        self,
        intent: ValueTransferIntent,
    ) -> List[CandidateRoute]:
        """
        Ask the AI model to discover candidate routes.
        """

        context = build_route_discovery_context(intent)

        user_prompt = (
            "Discover candidate value-transfer routes for this "
            "intent.\n\n"
            "Every returned route is a candidate only and must be "
            "verified by downstream intelligence, compliance and "
            "eligibility stages.\n\n"
            "IMPORTANT: Return the JSON object containing the "
            "'routes' array. Do not return the routes array directly.\n\n"
            "Structured transfer context:\n"
            f"{build_structured_context(context)}"
        )

        response = self.model.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        return self._parse_response(
            intent=intent,
            response=response,
        )

    @staticmethod
    def _normalize_json_response(response: str) -> str:
        """
        Extract the JSON object from a model response.

        Accepts raw JSON, Markdown-fenced JSON, or explanatory
        text surrounding a JSON object.
        """
        if not isinstance(response, str):
            raise ValueError(
                "Route Discovery Agent response must be a string."
            )

        normalized = response.strip()

        if not normalized:
            raise ValueError(
                "Route Discovery Agent returned an empty response."
            )

        # Pure JSON
        if normalized.startswith("{") and normalized.endswith("}"):
            return normalized

        # JSON inside ```json ... ``` with possible prose before it
        fence_start = normalized.find("```json")

        if fence_start != -1:
            content_start = fence_start + len("```json")
            fence_end = normalized.find("```", content_start)

            if fence_end != -1:
                candidate = normalized[
                    content_start:fence_end
                ].strip()

                if candidate.startswith("{") and candidate.endswith("}"):
                    return candidate

        # JSON object surrounded by ordinary text
        object_start = normalized.find("{")
        object_end = normalized.rfind("}")

        if object_start != -1 and object_end > object_start:
            candidate = normalized[
                object_start:object_end + 1
            ].strip()

            if candidate.startswith("{") and candidate.endswith("}"):
                return candidate

        return normalized

    @staticmethod
    def _parse_response(
        intent: ValueTransferIntent,
        response: str,
    ) -> List[CandidateRoute]:
        """
        Convert the AI response into CandidateRoute contracts.

        The AI must return a top-level JSON object containing a
        'routes' list. Invalid structures are rejected rather than
        silently transformed.
        """

        normalized_response = RouteDiscoveryAgent._normalize_json_response(
            response
        )

        try:
            data = json.loads(normalized_response)
        
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Route Discovery Agent returned invalid JSON."
            ) from exc

        # --------------------------------------------------------------
        # TOP-LEVEL CONTRACT
        # --------------------------------------------------------------

        if not isinstance(data, dict):
            received_type = type(data).__name__

            raise ValueError(
                "Route Discovery Agent returned an invalid "
                "top-level JSON structure. "
                "Expected a JSON object containing a 'routes' list; "
                f"received a JSON {received_type}."
            )

        routes_data = data.get("routes")

        if not isinstance(routes_data, list):
            raise ValueError(
                "Route Discovery Agent 'routes' must be a list."
            )

        routes: List[CandidateRoute] = []

        # --------------------------------------------------------------
        # ROUTE CONTRACT
        # --------------------------------------------------------------

        for index, route_data in enumerate(
            routes_data,
            start=1,
        ):

            if not isinstance(route_data, dict):
                raise ValueError(
                    f"Route {index} must be a JSON object."
                )

            required_fields = [
                "route_id",
                "rail",
                "source_country",
                "source_currency",
                "destination_country",
                "destination_currency",
                "funding_method",
                "transfer_path",
                "delivery_method",
                "corridor_availability",
                "route_requirements",
            ]

            missing_fields = [
                field
                for field in required_fields
                if field not in route_data
            ]

            if missing_fields:
                raise ValueError(
                    f"Route {index} is missing required fields: "
                    f"{missing_fields}"
                )

            route_id = str(
                route_data["route_id"]
            )

            source_country = str(
                route_data["source_country"]
            )

            source_currency = str(
                route_data["source_currency"]
            )

            destination_country = str(
                route_data["destination_country"]
            )

            destination_currency = str(
                route_data["destination_currency"]
            )

            # ----------------------------------------------------------
            # INTENT PRESERVATION
            # ----------------------------------------------------------

            if source_country != intent.from_country:
                raise ValueError(
                    f"Route {route_id} changes the source country "
                    "from the user intent."
                )

            if source_currency != intent.source_currency:
                raise ValueError(
                    f"Route {route_id} changes the source currency "
                    "from the user intent."
                )

            if destination_country != intent.to_country:
                raise ValueError(
                    f"Route {route_id} changes the destination "
                    "country from the user intent."
                )

            if destination_currency != intent.destination_currency:
                raise ValueError(
                    f"Route {route_id} changes the destination "
                    "currency from the user intent."
                )

            # ----------------------------------------------------------
            # TRANSFER PATH
            # ----------------------------------------------------------

            transfer_path = route_data[
                "transfer_path"
            ]

            if not isinstance(
                transfer_path,
                list,
            ):
                raise ValueError(
                    f"Route {route_id} transfer_path "
                    "must be a list."
                )

            # ----------------------------------------------------------
            # ROUTE REQUIREMENTS
            # ----------------------------------------------------------

            route_requirements = route_data[
                "route_requirements"
            ]

            if not isinstance(
                route_requirements,
                list,
            ):
                raise ValueError(
                    f"Route {route_id} route_requirements "
                    "must be a list."
                )

            # ----------------------------------------------------------
            # CANDIDATE CONTRACT
            # ----------------------------------------------------------

            routes.append(
                CandidateRoute(
                    route_id=route_id,
                    rail=str(
                        route_data["rail"]
                    ),
                    source=RouteEndpoint(
                        country=source_country,
                        currency=source_currency,
                    ),
                    destination=RouteEndpoint(
                        country=destination_country,
                        currency=destination_currency,
                    ),
                    funding_method=str(
                        route_data["funding_method"]
                    ),
                    transfer_path=[
                        str(step)
                        for step in transfer_path
                    ],
                    delivery_method=str(
                        route_data["delivery_method"]
                    ),
                    corridor_availability=str(
                        route_data[
                            "corridor_availability"
                        ]
                    ),
                    route_requirements=[
                        str(requirement)
                        for requirement
                        in route_requirements
                    ],
                )
            )

        # --------------------------------------------------------------
        # DUPLICATE ROUTE IDs
        # --------------------------------------------------------------

        route_ids = [
            route.route_id
            for route in routes
        ]

        if len(route_ids) != len(
            set(route_ids)
        ):
            raise ValueError(
                "Route Discovery Agent returned "
                "duplicate route IDs."
            )

        return routes
