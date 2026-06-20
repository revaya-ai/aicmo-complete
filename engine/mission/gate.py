"""STATION 3, Mission: the human approval gate.

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


def approve(post_id: str, note: str = "Approved by human.") -> None:
    """Human says ship it. Advance qc_review -> approved with a note."""
    advance(post_id, Status.APPROVED, human_note=note)


def reject(post_id: str, note: str = "Rejected by human.") -> None:
    """Human kills it. Advance qc_review -> rejected with a note."""
    advance(post_id, Status.REJECTED, human_note=note)


def request_revision(post_id: str, note: str = "Revision requested by human.") -> None:
    """Human wants changes. Route qc_review -> needs_revision with a note."""
    advance(post_id, Status.NEEDS_REVISION, human_note=note)


def run(post_id: str, auto_approve: bool = False) -> None:
    post = get_post(post_id)

    if auto_approve:
        approve(post_id, note="AUTO-APPROVED (demo loop).")
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
                  <p><em>QC score: {p['qc_score']}. {p['qc_notes']}</em></p>
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

    @app.route("/spend")
    def spend_index():
        rows = db.list_by_status(Status.AD_RECOMMENDED)
        if not rows:
            return "<h1>AI CMO Spend Gate</h1><p>No ad recommendations waiting.</p>"
        items = []
        for p in rows:
            items.append(
                f"""
                <div style="border:1px solid #ccc;padding:16px;margin:16px 0;">
                  <h3>{p['hook']}</h3>
                  <p>Recommended budget: ${p['ad_budget']}</p>
                  <p>Audience: {p['ad_audience']}</p>
                  <form method="post" action="/spend/decide/{p['id']}">
                    <button name="decision" value="ad_approved">Approve spend</button>
                    <button name="decision" value="rejected">Reject</button>
                  </form>
                </div>
                """
            )
        return "<h1>AI CMO Spend Gate</h1>" + "".join(items)

    @app.route("/spend/decide/<post_id>", methods=["POST"])
    def spend_decide(post_id):
        decision = request.form["decision"]
        if decision == Status.AD_APPROVED:
            approve_spend(post_id, approver="Human (spend gate)")
        elif decision == Status.REJECTED:
            db.advance(post_id, Status.REJECTED, human_note="Spend rejected by human.")
        else:
            return "bad decision", 400
        return redirect("/spend")

    return app


def approve_spend(post_id: str, approver: str = "Human (spend gate)") -> None:
    """Spend gate. Advance ad_recommended -> ad_approved, recording the approver."""
    advance(post_id, Status.AD_APPROVED, ad_spend_approved_by=approver)


def mirror_to_notion(path: str = None) -> str:
    """Mirror the qc_review queue to the Notion board so a human can approve from
    their phone instead of the Flask page.

    Offline (no NOTION_TOKEN) this writes the stub board JSON. With NOTION_TOKEN
    set it pushes to a real Notion database. This is optional: the Flask gate and
    the run.py auto_approve path both work without it. Notion is never required to
    run the loop.

    Returns the path the board was written to.
    """
    from engine.dashboard import notion_mirror

    if path is None:
        return notion_mirror.mirror_gate()
    return notion_mirror.mirror_gate(path)


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
