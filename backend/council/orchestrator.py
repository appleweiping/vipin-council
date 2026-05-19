"""
Orchestrator v2.0: Integrates SmartRouter + TaskDecomposer + SelfRefine + ToT.
Flow: Route -> Decompose (if complex) -> Protocol -> Refine -> Return
"""
from ..config import CouncilConfig
from ..council.session import Session, SessionResult
from ..protocols.council_protocol import CouncilProtocol
from ..protocols.debate_protocol import DebateProtocol
from ..protocols.redteam_protocol import RedTeamProtocol
from ..protocols.consensus_protocol import ConsensusProtocol
from ..protocols.specialist_protocol import SpecialistProtocol
from ..protocols.tournament_protocol import TournamentProtocol
from ..providers.router import ModelRouter
from ..engine.smart_router import SmartRouter, RoutingDecision
from ..engine.self_refine import SelfRefineEngine
from ..engine.tree_of_thoughts import TreeOfThoughts
from ..engine.task_decomposer import TaskDecomposer


class Orchestrator:
    """v2.0 orchestrator with full algorithm pipeline."""

    def __init__(self, config: CouncilConfig):
        self.config = config
        self.router = ModelRouter(config)
        self.smart_router = SmartRouter(config, self.router)
        self.refiner = SelfRefineEngine(self.router, max_iterations=3, quality_threshold=8.0)
        self.tot = TreeOfThoughts(config, self.router, beam_width=5, max_depth=3, vote_samples=3)
        self.decomposer = TaskDecomposer(config, self.router)

        self.protocols = {
            "council": CouncilProtocol(config, self.router),
            "debate": DebateProtocol(config, self.router),
            "redteam": RedTeamProtocol(config, self.router),
            "consensus": ConsensusProtocol(config, self.router),
            "specialist": SpecialistProtocol(config, self.router),
            "tournament": TournamentProtocol(config, self.router),
        }

    async def run(self, session: Session) -> SessionResult:
        """Full pipeline: route -> decompose -> protocol -> refine."""

        # Step 1: Smart routing (classify difficulty)
        routing = await self.smart_router.classify(session.query)

        # Step 2: Fast path — simple queries skip the full council
        if routing.tier == "fast":
            return await self._fast_path(session, routing)

        # Step 3: Task decomposition (for complex queries)
        decomposition = await self.decomposer.process(session.query, routing.difficulty)

        if decomposition.was_decomposed:
            # Complex query was broken into sub-tasks and solved
            result = SessionResult(
                id=session.id, query=session.query,
                protocol=session.protocol, created_at=session.created_at,
            )
            result.stages.append({
                "name": "Task Decomposition",
                "subtasks": [{"desc": t.description, "model": t.assigned_to, "result": t.result[:200]} for t in decomposition.subtasks]
            })
            result.final_answer = decomposition.synthesis
            result.confidence = 0.8
            result.audit_trail.append({"step": "decompose", "subtask_count": len(decomposition.subtasks)})

            # Refine the synthesis
            architect = next(m for m in self.config.models if m.role == "architect")
            critic = next(m for m in self.config.models if m.role == "reviewer")
            refined = await self.refiner.refine(architect, critic, session.query, decomposition.synthesis)
            if refined.iterations > 0:
                result.final_answer = refined.final
                result.stages.append({"name": "Self-Refine", "iterations": refined.iterations, "converged": refined.converged, "scores": refined.scores})
                result.audit_trail.append({"step": "refine", "iterations": refined.iterations})

            return result

        # Step 4: Run the selected protocol
        protocol = self.protocols.get(session.protocol, self.protocols["council"])
        result = await protocol.execute(session)

        # Step 5: Self-refine the final answer (if not already high confidence)
        if result.confidence < 0.85 and result.final_answer:
            architect = next(m for m in self.config.models if m.role == "architect")
            critic = next(m for m in self.config.models if m.role == "reviewer")
            refined = await self.refiner.refine(architect, critic, session.query, result.final_answer)
            if refined.iterations > 0 and refined.scores and refined.scores[-1] > 7.0:
                result.final_answer = refined.final
                result.stages.append({"name": "Self-Refine", "iterations": refined.iterations, "converged": refined.converged, "scores": refined.scores})
                result.audit_trail.append({"step": "post_refine", "iterations": refined.iterations, "final_score": refined.scores[-1]})
                result.confidence = min(0.95, result.confidence + 0.1)

        # Add routing info to audit trail
        result.audit_trail.insert(0, {"step": "routing", "tier": routing.tier, "difficulty": routing.difficulty, "reason": routing.reason})

        return result

    async def _fast_path(self, session: Session, routing: RoutingDecision) -> SessionResult:
        """Handle simple queries with a single fast model."""
        model = next((m for m in self.config.models if m.id == routing.assigned_models[0]), self.config.models[-1])
        messages = [{"role": "user", "content": session.query}]
        if session.context:
            messages.insert(0, {"role": "system", "content": session.context})

        response = await self.router.query(model, messages)

        result = SessionResult(
            id=session.id, query=session.query,
            protocol="fast_path", created_at=session.created_at,
        )
        result.final_answer = response
        result.confidence = 0.6  # Lower confidence for single-model fast path
        result.stages.append({"name": "Fast Path", "model": model.name, "response": response})
        result.audit_trail.append({"step": "fast_path", "model": model.id, "difficulty": routing.difficulty})
        return result
