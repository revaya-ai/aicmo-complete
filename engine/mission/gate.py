"""STATION 3 — Mission: the human approval gate.

Reads:  status == qc_review
Writes: status == approved          (human says ship it)
        status == rejected          (human kills it)
        status == needs_revision    (human wants changes)
        (optionally sets human_note)

Signature: run(post_id: str, auto_approve: bool = False) -> None

This is the one true human-in-the-loop step. The real gate is a person clicking
in the Flask app below. For the unattended demo loop, run.py passes
auto_approve=True and this function approves automatically.
"""

from db import Status, get_post, advance


def run(post_id: str, auto_approve: bool = False) -> None:
    post = get_post(post_id)

    if auto_approve:
        advance(
            post_id,
            Status.APPROVED,
            human_note="AUTO-APPROVED (demo loop).",
        )
        return

    # TODO(builder): without auto_approve, this should block until a human
    # decides. In practice the human acts through the Flask app below and this
    # function is not called directly. Raise so a misconfigured loop is loud.
    raise RuntimeError(
        f"Post {post_id} is at {post['status']} and needs human review. "
        "Run the Flask gate app or pass auto_approve=True."
    )


# --------------------------------------------------------------------------
# Minimal Flask app for the REAL human gate. Run with:  python -m flask ...
# or just `python engine/mission/gate.py`. Lists posts at qc_review and lets a
# human approve / reject / request revision. TODO(builder): add auth + styling.
# --------------------------------------------------------------------------
def create_app():
    from flask import Flask, request, redirect

    import db

    app = Flask(__name__)

    @app.route("/")
    def index():
        rows = db.list_by_status(Status.QC_REVIEW)
        if not rows:
            return "<h1>AI CMO Gate</h1><p>Nothing waiting for review.</p>"
        items = []
        for p in rows:
            items.append(
                f"""
                <div style="border:1px solid #ccc;padding:16px;margin:16px 0;">
                  <h3>{p['hook']}</h3>
                  <p>{p['body']}</p>
                  <p><em>QC score: {p['qc_score']} — {p['qc_notes']}</em></p>
                  <img src="/{p['image_path']}" style="max-width:300px;" />
                  <form method="post" action="/decide/{p['id']}">
                    <button name="decision" value="approved">Approve</button>
                    <button name="decision" value="rejected">Reject</button>
                    <button name="decision" value="needs_revision">Revise</button>
                  </form>
                </div>
                """
            )
        return "<h1>AI CMO Gate</h1>" + "".join(items)

    @app.route("/decide/<post_id>", methods=["POST"])
    def decide(post_id):
        decision = request.form["decision"]
        if decision not in (Status.APPROVED, Status.REJECTED, Status.NEEDS_REVISION):
            return "bad decision", 400
        db.advance(post_id, decision, human_note=f"Human chose: {decision}")
        return redirect("/")

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
