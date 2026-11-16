# THE WHITEBOARD DRILL (Self-Test & Defense Practice)

> **Habit 25: Teach Back Drill**
> Pick any customer-facing system you are preparing to ship.
> Answer these 12 questions out loud, with **no notes**.
> Where you hesitate, that is your homework.

---

### The 12 Whiteboard Questions

1. **High-Level Purpose:** What does this system do, in two sentences a new teammate would understand?
2. **Request Trace:** Walk me through one request/frame from entry to response.
3. **Alternative Justification:** Why did you choose this approach instead of the obvious alternative?
4. **Data Structure Fit:** What is the most important data structure here and why does it fit?
5. **Anonymous Actor Abuse:** What is the worst thing an anonymous or external user could try?
6. **Malicious Authenticated Actor:** What about an authenticated or internal actor who turns malicious?
7. **Dependency Downtime:** What happens if your primary dependency (hardware camera / ML model runtime / external API) goes down or lags for an hour?
8. **Scale Limit:** What is the first limit you expect to hit as usage grows (FPS drop, memory leak, CPU saturation)?
9. **Observability:** How would you know the system broke before a customer or user told you?
10. **Reversibility:** How do you safely undo your last change in production without downtime?
11. **Unverified Assumptions:** What did the AI assume that you never explicitly verified?
12. **Future Iteration:** What architectural change would you make if you had another week?

---

### Scoring Guide

- **10 to 12 Confident Answers:** Ready to ship to Lane B (Customer Facing).
- **Fewer than 10 Answers:** Not ready. Close the identified gaps in `docs/` before shipping.
