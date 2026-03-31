/* ------------------------------------------------------------
   Prints each card's raw data attribute values to the browser
   console so you can verify they are being read correctly. 
   The square brackets make whitespace visible:
   "[  garrett comer]" reveals a leading space problem immediately.
   Delete this function once sorting works as expected.
------------------------------------------------------------ */
function debugCardData() {
    const cards = document.querySelectorAll(".athlete-card");
    console.log("main.js loaded — found", cards.length, "athlete card(s).");
    cards.forEach(function(card, index) {
        console.log(
            "Card " + (index + 1) + ":",
            "name=[" + (card.getAttribute("data-name")  || "MISSING") + "]",
            "grade=[" + (card.getAttribute("data-grade") || "MISSING") + "]",
            "sr=["    + (card.getAttribute("data-sr")    || "MISSING") + "]",
            "pr=["    + (card.getAttribute("data-pr")    || "MISSING") + "]"
        );
    });
}


/* ------------------------------------------------------------
   TIME CONVERSION UTILITY
   Converts strings to total seconds
   for accurate numeric comparison.

   Returns Infinity for any of these cases so the card sorts last:
     - null / undefined / empty string
     - No colon (not a time string)
     - "00:00.0" placeholder value (zero would sort first — wrong)
     - Anything that produces NaN after parsing
------------------------------------------------------------ */
function timeToSeconds(timeStr) {
    if (!timeStr) return Infinity;

    // Strip the "PR" label that athletic.net appends to personal record times
    const clean = timeStr.replace("PR", "").trim();

    if (!clean.includes(":")) return Infinity;

    const parts = clean.split(":");
    if (parts.length !== 2) return Infinity;

    const minutes = parseInt(parts[0], 10);
    const seconds = parseFloat(parts[1]);

    if (isNaN(minutes) || isNaN(seconds)) return Infinity;

    const total = (minutes * 60) + seconds;

    if (total === 0) return Infinity;

    return total;
}


/* ------------------------------------------------------------
   SORT COMPARATOR FACTORY
   Returns the correct comparator function for the selected field.
   sort(comparator) calls comparator(a, b) for each pair and expects:
     negative → a sorts before b
     positive → b sorts before a
     zero     → maintain current relative order

   getAttribute() is used instead of dataset.property because
   getAttribute returns the exact raw attribute string, making
   whitespace issues immediately visible in the debug output.
------------------------------------------------------------ */
function getComparator(sortField) {

    /* ----------------------------------------------------------
       NAME — Alphabetical A → Z, case-insensitive
       .trim() removes whitespace that can appear when HTML attribute
       values span multiple lines in Python-generated markup.
       .toLowerCase() ensures "Garrett" and "garrett" compare equally.
       localeCompare handles accented characters correctly.
    ---------------------------------------------------------- */
    if (sortField === "name") {
        return function(cardA, cardB) {
            const nameA = (cardA.getAttribute("data-name") || "").trim().toLowerCase();
            const nameB = (cardB.getAttribute("data-name") || "").trim().toLowerCase();
            return nameA.localeCompare(nameB);
        };
    }

    /* ----------------------------------------------------------
       GRADE — Numeric ascending: 9 → 10 → 11 → 12
       Cards with no valid grade use Infinity (sort last) rather
       than 0 (which would sort them first, above grade 9).
    ---------------------------------------------------------- */
    if (sortField === "grade") {
        return function(cardA, cardB) {
            const rawA  = (cardA.getAttribute("data-grade") || "").trim();
            const rawB  = (cardB.getAttribute("data-grade") || "").trim();
            const parsedA = parseInt(rawA, 10);
            const parsedB = parseInt(rawB, 10);

            // FIX: Infinity pushes invalid/placeholder grades to end of list
            const gradeA = isNaN(parsedA) ? Infinity : parsedA;
            const gradeB = isNaN(parsedB) ? Infinity : parsedB;

            return gradeA - gradeB;
        };
    }

    /* ----------------------------------------------------------
       SEASON RECORD — Fastest time first (lowest seconds = first)
       Invalid or placeholder "00:00.0" times return Infinity → last.
    ---------------------------------------------------------- */
    if (sortField === "season-record") {
        return function(cardA, cardB) {
            const secsA = timeToSeconds((cardA.getAttribute("data-sr") || "").trim());
            const secsB = timeToSeconds((cardB.getAttribute("data-sr") || "").trim());
            return secsA - secsB;
        };
    }

    /* ----------------------------------------------------------
       PERSONAL RECORD — Fastest time first (same logic as SR)
    ---------------------------------------------------------- */
    if (sortField === "personal-record") {
        return function(cardA, cardB) {
            const secsA = timeToSeconds((cardA.getAttribute("data-pr") || "").trim());
            const secsB = timeToSeconds((cardB.getAttribute("data-pr") || "").trim());
            return secsA - secsB;
        };
    }

    // Fallback: unrecognized sort field — log it and do nothing
    console.warn("main.js: unrecognized sort field received:", sortField);
    return function() { return 0; };
}


/* ------------------------------------------------------------
   MAIN SORT FUNCTION
   1. Reads the current dropdown selection
   2. Collects all .athlete-card elements into an Array
   3. Sorts the Array in place using the matching comparator
   4. Re-appends each card to #athlete-roster in sorted order

   Key detail: appendChild() on a node that already exists in the
   DOM MOVES it rather than duplicating it, so this is a clean
   reorder with no cloning or innerHTML manipulation.

   The <h3>Athlete Roster:</h3> inside #athlete-roster is ignored
   because querySelectorAll(".athlete-card") only selects elements
   with that class — the h3 stays put at the top automatically.
------------------------------------------------------------ */
function sortAthletes() {
    const sortSelect = document.getElementById("sort-by");
    const roster     = document.getElementById("athlete-roster");

    if (!sortSelect || !roster) {
        console.error("main.js: Required elements not found — check HTML IDs.");
        return;
    }

    const sortField = sortSelect.value;
    const cards     = Array.from(roster.querySelectorAll(".athlete-card"));

    if (cards.length === 0) {
        console.warn("main.js: No .athlete-card elements found.");
        return;
    }

    cards.sort(getComparator(sortField));

    // Re-append in sorted order — moves existing nodes, no duplication
    cards.forEach(function(card) {
        roster.appendChild(card);
    });

    console.log("main.js: Sorted", cards.length, "cards by '" + sortField + "'.");
}


/* ------------------------------------------------------------
   INITIALIZATION
   No DOMContentLoaded wrapper. This script uses the 'defer'
   attribute in the HTML, which guarantees it runs only after the
   full HTML document has been parsed. The DOM is ready the moment
   this file executes — wrapping in DOMContentLoaded was redundant
   and created a race condition that caused page-load sort to fail.
------------------------------------------------------------ */
const sortSelectEl = document.getElementById("sort-by");

if (!sortSelectEl) {
    console.error("main.js: #sort-by not found. Ensure the script is loaded on a page with the sort dropdown.");
} else {
    // Print raw attribute values to console for debugging
    debugCardData();

    // Re-sort on every dropdown change
    sortSelectEl.addEventListener("change", sortAthletes);

    // Apply the default sort (Name, A→Z) immediately on page load
    sortAthletes();
}