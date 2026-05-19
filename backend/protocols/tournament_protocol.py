"""Tournament Protocol: Bracket elimination, best answer wins."""
from .base import BaseProtocol
from ..council.session import Session, SessionResult


class TournamentProtocol(BaseProtocol):
    async def execute(self, session: Session) -> SessionResult:
        result = SessionResult(
            id=session.id, query=session.query,
            protocol="tournament", created_at=session.created_at,
        )

        models = self.config.models
        if len(models) < 2:
            result.final_answer = "Need at least 2 models for tournament protocol."
            return result

        # Stage 1: All models answer
        messages = [{"role": "user", "content": session.query}]
        answers = {}
        for model in models:
            answers[model.id] = await self.router.query(model, messages)

        result.stages.append({"name": "Initial Answers", "responses": answers})
        result.audit_trail.append({"stage": 1, "action": "initial_answers", "count": len(answers)})

        # Stage 2: Bracket elimination
        judge = next((m for m in models if m.id == self.config.chairman), models[0])
        remaining = list(answers.items())
        round_num = 2

        while len(remaining) > 1:
            next_round = []
            matchups = []

            for i in range(0, len(remaining) - 1, 2):
                a_id, a_answer = remaining[i]
                b_id, b_answer = remaining[i + 1]

                judge_msg = [{"role": "user", "content": f"""You are judging a tournament match for the query: "{session.query}"

CONTESTANT A ({a_id}):
{a_answer}

CONTESTANT B ({b_id}):
{b_answer}

Which response is better? Consider accuracy, completeness, clarity, and usefulness.
Reply with WINNER: A or WINNER: B, followed by a brief justification."""}]

                verdict = await self.router.query(judge, judge_msg)
                winner = remaining[i] if "WINNER: A" in verdict.upper() else remaining[i + 1]
                next_round.append(winner)
                matchups.append({"a": a_id, "b": b_id, "winner": winner[0], "verdict": verdict})

            # If odd number, last one gets a bye
            if len(remaining) % 2 == 1:
                next_round.append(remaining[-1])

            result.stages.append({"name": f"Round {round_num} - Elimination", "matchups": matchups})
            result.audit_trail.append({"stage": round_num, "action": "elimination_round", "remaining": len(next_round)})
            remaining = next_round
            round_num += 1

        # Winner
        winner_id, winner_answer = remaining[0]
        result.final_answer = winner_answer
        result.confidence = 0.75
        result.stages.append({"name": "Tournament Winner", "winner": winner_id})
        result.audit_trail.append({"stage": round_num, "action": "tournament_winner", "winner": winner_id})

        return result
