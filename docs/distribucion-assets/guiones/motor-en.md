# Script — Motor Video (5 min) — English

## Objective
Deep-dive into Whetzy's tech: BKT, FSRS, adaptive selection. Target: technical audiences, educators, investors.

## Structure

### Intro (0:00-0:20)
- **Visual:** Code compiling, clean terminal output
- **Narration:** "How does a learning platform with millions of users teach each person differently? Today we reveal the engine."
- **Overlay:** "The Adaptive Brain of Whetzy"

### 1. The Scale Problem (0:20-0:45)
- **Visual:** Graph: 1,000 students in a line (all identical arrows)
- **Narration:** "A tutor with 30 students sees when Maria needs more practice with loops and when Johan is ready for functions. But with 10,000 students, how does that scale?"
- **Transition:** Zoom out to 10,000+ students

### 2. Bayesian Knowledge Tracing (0:45-2:15)
- **Visual:** Animated BKT equation on screen:
  - p_known (probability of mastery)
  - p_guess (probability of guessing)
  - p_slip (probability of careless mistake)
- **Narration:** "We use Bayesian Knowledge Tracing. For each skill—say, 'functions in Python'—we estimate: What's the probability Johan has mastered it?"
- **Visual:** Skill graph → questions → responses
- **Narration:** "Every answer tells us something: Did he get it wrong because he doesn't understand, or just a lapse? Bayes updates the belief."
- **Example on screen:**
  - "Johan answers Q1 correctly: p_known goes to 0.65"
  - "Johan answers Q2 wrong: Genuine failure? → p_known drops to 0.55"
  - "Johan answers Q3 correctly: p_known rises to 0.72"

### 3. Spacing: FSRS (2:15-3:45)
- **Visual:** Classic forgetting curve vs. FSRS curve (red vs. blue)
- **Narration:** "Knowing something today doesn't mean you'll remember it in 3 months. Ebbinghaus documented the forgetting curve 140 years ago. FSRS—Free Spaced Repetition Scheduler—solves it."
- **Animation:** Questions reappearing at optimal intervals
  - "Question answered correctly today"
  - "Reappears in 3 days (if hard) or 10 days (if easy)"
  - "Each review extends the interval"
- **Narration:** "Instead of a fixed calendar, we calculate: Given Johan masters this at 72%, when might he forget it? We schedule review just before."
- **Graph:** Difficulty vs. Stability matrix

### 4. Adaptive Selection (3:45-4:30)
- **Visual:** Quiz screen with 3 question options visible
- **Narration:** "Now that we know Johan's state in each skill, which question do we ask?"
- **Options visible:**
  - "Option A: Easy (p_known=0.9) — Boring"
  - "Option B: Medium (p_known=0.5) — Just right"
  - "Option C: Hard (p_known=0.2) — Frustrating"
- **Narration:** "We select the one that's challenging but not impossible. That maximizes learning. Whetzy targets a 50% success rate."

### 5. Verification: E2E Testing (4:30-4:55)
- **Visual:** Terminal running `pytest tests/content/test_exec_questions.py` — PASS
- **Narration:** "How do we know it works? Tests. Every executable question is validated: Does the test code reject bad answers and accept good ones?"
- **SFX:** Fast typing, test passing bell

### Closing (4:55-5:00)
- **Visual:** Whetzy logo + URL
- **Narration:** "That's Whetzy. Science in code. Adaptivity at scale."
- **Overlay:** `whetzy.com` + `YT-EN-MOTOR`

## Technical Notes
- **Duration:** 4:58-5:02
- **Resolution:** 1080p 16:9
- **Visual style:** Motion graphics + real platform screenshots
- **Campaign Code:** `YT-EN-MOTOR` (final screen)
- **Subtitles:** EN, technical terms clarified
- **Audio:** Technical but accessible narration, subtle music (sine wave + ambient)
