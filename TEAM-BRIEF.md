# Team Brief: AI CMO Hackathon

Read this first. It explains what we're building, what's already done, what your job is, and what we walk away with.

---

## What we're building

An **AI CMO**: a marketing department that runs as software. One seed idea goes in, and the system thinks, writes, designs, quality-checks, waits for a human to approve, then publishes and measures. Six steps run themselves. One step is a person. That one human decision is the whole point.

We are rebuilding the AI CMO reference so we all walk away with a working copy.

---

## What's already built (so nobody starts from zero)

The repo is live: **https://github.com/revaya-ai/aicmo-core**

It already runs the entire pipeline end to end using "stubs" (fake placeholder logic). Clone it and run this right now:

```bash
git clone https://github.com/revaya-ai/aicmo-core.git
cd aicmo-core
python3 run.py "why your competitors all sound the same"
```

You'll watch one post move through every stage:

```
captured → drafted → qc_review → approved → scheduled → published → analyzed → ad_live
```

That means the skeleton works today. Your job is not to build the machine. It is to **replace your one fake part with the real thing.** The machine keeps running the whole time.

The shared brain is a file called `db.py`. It holds the content record every stage reads and writes. **It is frozen. Nobody changes it.** That is what lets three people build at once and have it fit together at the end.

---

## How the work is split (3 cards, 1 each)

Think of it as an assembly line in three sections. Each person owns one section, builds it on their own branch, and we bolt them together at the end of the day. Full detail is in `ASSIGNMENTS.md`. Short version:

### Card 1: BRAIN (Think + Write)
You make the words. Take a seed idea, understand the client's brand, and write an on-brand post.
- You own: `engine/brain/` and the client brand context files.
- Your handoff: takes a `captured` idea, returns a `drafted` post.
- Done when: a real, on-brand post comes out (not generic AI mush).

### Card 2: STUDIO (Design + Check)
You make the picture and you are the brand police. Render the on-brand graphic, then a vision model scores it. Anything off-brand gets bounced before a human ever sees it.
- You own: `engine/studio/`, the image template, and the visual brand spec.
- Your handoff: takes a `drafted` post, attaches an image, marks it `qc_review` (pass) or `needs_revision` (fail).
- Done when: a real branded image comes out with a real quality score, and the gate actually rejects a bad image.

### Card 3: MISSION CONTROL (Approve + Publish + Measure + Ads)
You run the control room. Build the approve/reject button a client taps, publish the approved post, pull the numbers back, and run the recommend-only ads agent. You are also the person who merges everything at the end.
- You own: `engine/mission/`, `engine/ads/`, `run.py`, and you are custodian of `db.py`.
- Your handoff: takes a `qc_review` post, walks it through `approved → published → analyzed`, then `ad_recommended → ad_approved → ad_live`.
- Done when: you approve on the gate and the post goes live, gets measured, and the ads agent proposes promoting the winner.

The ads piece is shared: Brain writes the ad copy, Studio makes the ad image, Mission Control wires it together. So it is a fourth station built from all three of us, not a fourth person.

---

## What you need to do (today)

1. **Clone the repo and run it once** (commands above). See the loop go green. This proves your setup works.
2. **Make your branch:** `git checkout -b brain` (or `studio` or `mission`).
3. **Open your station folder** and find the `# TODO(builder):` markers. That is exactly where your real code goes.
4. **Build your part.** Keep the same function shape, read your input stage, write your output stage. Run `python3 run.py "..."` often to confirm the whole loop is still green with your real part plugged in.
5. **Do not touch `db.py` or other people's folders.** If you think the shared record needs a new field, say so out loud and we all agree first.
6. **Push your branch** when your part hits "done."

```bash
git add -A && git commit -m "brain: real writer" && git push -u origin <your-branch>
```

---

## What happens at the end of the day

1. Everyone pushes their branch.
2. Mission Control merges all three into `main`. Because each station is its own folder, this is clean, not a merge nightmare.
3. We run the full pipeline live, one real seed idea, end to end, with a human approving in the middle.
4. Everyone clones `main`.

**The outcome:** every one of us leaves with a working AI CMO. Clone it, drop in any client's brand files, run it, approve a post from your phone, and it ships. That is the thing we demo to the group, and the thing each person keeps.
