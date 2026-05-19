"""Orchestrator: routes queries to the appropriate protocol."""
from ..config import CouncilConfig
from .session import Session, SessionResult
from ..protocols.council_protocol import CouncilProtocol
from ..protocols.debate_protocol import DebateProtocol
from ..protocols.redteam_protocol import RedTeamProtocol
from ..protocols.consensus_protocol import ConsensusProtocol
from ..protocols.specialist_protocol import SpecialistProtocol
from ..protocols.tournament_protocol import TournamentProtocol
from ..providers.router import ModelRouter


class Orchestrator:
    def __init__(self, config: CouncilConfig):
        self.config = config
        self.router = ModelRouter(config)
        self.protocols = {
            "council": CouncilProtocol(config, self.router),
            "debate": DebateProtocol(config, self.router),
            "redteam": RedTeamProtocol(config, self.router),
            "consensus": ConsensusProtocol(config, self.router),
            "specialist": SpecialistProtocol(config, self.router),
            "tournament": TournamentProtocol(config, self.router),
        }

    async def run(self, session: Session) -> SessionResult:
        protocol = self.protocols.get(session.protocol, self.protocols["council"])
        return await protocol.execute(session)
