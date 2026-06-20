"""STATION 1 — Brain: idea -> draft.

Reads:  status == captured  (uses seed_idea)
Writes: status == drafted   (sets pillar, angle, hook, body)

Signature: run(post_id: str, auto_approve: bool = False) -> None

The Brain is a chain of "bricks", each one transforming the post a little:
    Intake -> Topic -> Angle -> Hook -> Story
The real version grounds every brick in the client's 6-layer context
(client-data/<client>/*.md) and calls Claude. The stub returns short canned
strings derived from the seed_idea so the loop runs with zero dependencies.
"""

from db import Status, get_post, advance


def run(post_id: str, auto_approve: bool = False) -> None:
    post = get_post(post_id)
    seed = post["seed_idea"]

    # TODO(builder): load client-data/<client>/*.md (the 6-layer context) and
    # pass it to each brick below. Each brick should call Claude with that
    # context so output is grounded in real positioning/voice/guardrails.

    # --- Brick: Intake ---------------------------------------------------
    # TODO(builder): normalize the raw seed into a clean content premise.
    premise = seed.strip()

    # --- Brick: Topic ----------------------------------------------------
    # TODO(builder): map the premise to a content pillar from strategy.md.
    pillar = "Education"

    # --- Brick: Angle ----------------------------------------------------
    # TODO(builder): pick a sharp, on-brand angle the competitors aren't using.
    angle = f"Most brands get '{premise}' wrong. Here is the simpler truth."

    # --- Brick: Hook -----------------------------------------------------
    # TODO(builder): write a scroll-stopping first line (voice.md rules).
    hook = f"{premise} is not a skincare problem. It is a routine problem."

    # --- Brick: Story ----------------------------------------------------
    # TODO(builder): write the full post body in the client's voice.
    body = (
        f"{premise}\n\n"
        "Here is what actually moves the needle for your skin, without the "
        "10-step routine. Pick three things, do them every day, give it four "
        "weeks. That is the whole secret.\n\n"
        "Simple beats fancy. Every time."
    )

    advance(
        post_id,
        Status.DRAFTED,
        pillar=pillar,
        angle=angle,
        hook=hook,
        body=body,
    )
