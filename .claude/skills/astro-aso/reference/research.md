# Astro ASO Research System

This uses the `Astro Skill` from `@.claude/skills/astro-aso/SKILL.md` instead of the Astro Mac App. It reads the db from the Astro app.

### **The "Golden Ratio" Baselines**

Before you start your research in Astro, you must memorize these two numbers. This is the filter that separates "good ideas" from "waste of time" ideas.

*   **Popularity (Search Volume): Minimum 20**
    *   **Definition:** How many people are searching for this.
    *   **Rule:** If the score is below 20, the traffic is too low to sustain an app.
*   **Difficulty (Competition): Maximum 60-70 (Ideally < 30)**
    *   **Definition:** How hard it is to rank against existing apps.
    *   **Rule:** You set your filter to max 70 to remove the "impossible" keywords. However, your **Target** is to find keywords in the **Green Zone (20-40)**.
    *   *Visual Proof:* In the video, the developer rejected a keyword with Difficulty 65 ("what plant is this free") and chose a keyword with **Difficulty 19** ("wood identification").

---

### **Part 1: Research Protocol for NEW Apps**

**Phase 1: Seed & Expand**
1.  **Open Astro:** Create a "Temporary App" project (a sandbox to test keywords without affecting live data).
2.  **Input Root Keyword:** Type in a broad term (e.g., "Tree Identifier").
3.  **Load Suggestions:** Let Astro generate the list of long-tail keywords.

**Phase 2: The "Golden Ratio" Filter**
*This is the most critical step to systematize.*

1.  **Set Popularity Filter:**
    *   Set **Min** to **20**.
    *   *Action:* Hide any result that is 0–19.
2.  **Set Difficulty Filter:**
    *   Set **Max** to **70**.
    *   *Action:* Hide any result that is 71–100 (Red Zone).
3.  **Sort the List:**
    *   Sort the remaining list by **Popularity (High to Low)**.

**Phase 3: The Selection (The "Gap" Strategy)**
Now that you have a filtered list, you are looking for a specific anomaly: **High Popularity + Low Difficulty.**

1.  **Scan the List:** Look for keywords that survived the filter.
2.  **Identify the "Green" Opportunities:**
    *   Look for Difficulty scores that are surprisingly low (e.g., 20, 30, or low 40s).
    *   *Example from Video:*
        *   *Keyword A:* "what plant is this free" (Pop: 26 / **Diff: 65**) -> **REJECT** (Too hard).
        *   *Keyword B:* "wood identification" (Pop: 23 / **Diff: 19**) -> **SELECT** (Easy win).
3.  **Final Selection:** Add the keywords with the lowest difficulty score to your target list.

---

### **Part 2: Research Protocol for EXISTING Apps**

If you already have an app, use the exact same metrics to find "low hanging fruit" keywords you are currently missing.

**Phase 1: Audit Current Rankings**
1.  **Load App in Astro:** Open your live app dashboard.
2.  **Check Current Keywords:** Look at the keywords you currently target.
3.  **The "Kill" List:** Identify keywords where:
    *   **Difficulty is > 70:** You are likely not ranking for these. Remove them to free up space.
    *   **Popularity is < 20:** Even if you rank #1, nobody is searching. Remove them.

**Phase 2: Find "Sibling" Keywords**
1.  **Input Your Core Keyword:** Type your main keyword into the discovery tool.
2.  **Apply the Golden Ratio:**
    *   Filter: **Pop > 20**, **Diff < 70**.
3.  **The "Pivot" Move:**
    *   Look for keywords that are *slightly* different from what you currently have but have a **lower Difficulty score** than your current keywords.
    *   *Action:* Swap out high-difficulty keywords in your metadata (Title/Subtitle) for these lower-difficulty variants.

### **Summary Cheat Sheet**

| Metric | Safe Zone | Danger Zone | Meaning |
| :--- | :--- | :--- | :--- |
| **Popularity** | **20 - 100** | 0 - 19 | < 20 means "Ghost Town" (No users) |
| **Difficulty** | **0 - 40** | 70 - 100 | > 70 means "War Zone" (Too competitive) |
| **Strategy** | **High Pop / Low Diff** | Low Pop / High Diff | Build where the bars are green. |