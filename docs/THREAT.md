# THREAT (Security & Adversarial Boundaries)

> **Answers:** "What happens if this actor behaves maliciously?"
> AI writes code that works for the happy path. Attackers live on every other path.
> An admitted gap beats a hidden one.

---

## 1. Actors & Entry Points

| Actor | Entry Point | Capability |
| :--- | :--- | :--- |
| **Local Webcam User / Attacker** | Physical camera feed | Inject adversarial clothing, patterns, occlusion, or malicious video stream via virtual webcam. |
| **Client / API Consumer** | REST / WebSocket endpoint | Flood inference server with high-resolution video streams (DDoS / GPU memory exhaustion). |
| **File Uploader** | Video upload endpoint | Upload oversized files, zip bombs, or exploit video decoding codecs (FFmpeg vulnerabilities). |
| **Third-Party Dependency** | `pip` package ecosystem | Malicious package update (supply-chain attack) executing arbitrary code or exfiltrating data. |

---

## 2. Threat Scenarios & Mitigations

### Threat 1: Denial of Service via Huge Payloads / Stream Flooding
- **Worst Realistic Abuse:** Sending 4K 120fps video streams repeatedly until host runs out of memory or inference stalls.
- **Mitigation:**
  - Enforce maximum frame dimensions (e.g. downscale to 640x480 before processing).
  - Rate-limiting per client IP/session.
  - Hard timeout on frame processing (e.g., abort if frame takes > 100ms).

### Threat 2: Malformed or Corrupt Video Containers (FFmpeg / OpenCV Exploit)
- **Worst Realistic Abuse:** Crafted video header triggers buffer overflow in underlying C++ video decoders.
- **Mitigation:**
  - Strict file extension and MIME type validation.
  - Sandbox file processing in isolated container/worker.
  - Limit max uploaded video length to 30 seconds / 25MB.

### Threat 3: Supply Chain / Malicious PyPI Packages
- **Worst Realistic Abuse:** AI or developer imports typo-squatted package that steals `.env` secrets or SSH keys.
- **Mitigation:**
  - Pin exact versions in `requirements.txt` / `pyproject.toml` with hash verification.
  - Ban automatic dependency installation without reviewing package author and download volume.

---

## 3. Admitted Known Gaps

- *Gap 1:* Virtual webcam software (e.g. OBS Virtual Camera) cannot be blocked easily at the OS level; software trusts the OS-provided video device handle.
- *Gap 2:* Adversarial perturbation patches on physical shirts or background boards can potentially fool keypoint landmark detectors; mitigation is multi-frame consensus thresholding.
