/* ------------------------------------------------------------
   FILTER FUNCTION
   The single function that does all the work. It reads both
   input values, then iterates every tbody row and decides
   whether to show or hide it based on whether it satisfies
   both the meet name filter AND the date filter.
------------------------------------------------------------ */
function filterResults() {

    // Read and normalize both filter inputs.
    // .toLowerCase() makes matching case-insensitive.
    // .trim() removes accidental leading/trailing whitespace.
    const meetQuery = document.getElementById("filter-meet").value.toLowerCase().trim();
    const dateQuery = document.getElementById("filter-date").value.toLowerCase().trim();

    // All data rows — the <thead> row is not included because querySelectorAll
    // targets only inside <tbody>
    const rows = document.querySelectorAll("#results-table tbody tr");

    // Track how many rows are currently visible after filtering
    let visibleCount = 0;

    rows.forEach(function(row) {

        // Skip the "no results" message row if it somehow gets selected.
        // It has the id "no-results-row" so we can identify and skip it.
        if (row.id === "no-results-row") return;

        // COLUMN INDICES (matching the table header order in the HTML):
        //   0: Race Name
        //   1: Date
        //   2: Location
        //   3: Distance
        //   4: Time
        //   5: Place
        //   6: Grade
        //   7: Results link

        // Read the race name from column 0 and normalize to lowercase
        const raceName = (row.cells[0]?.textContent || "").toLowerCase();

        // Read the date from column 1 and normalize to lowercase.
        // Dates are stored as "Aug 31 2023" — lowercased becomes "aug 31 2023"
        const raceDate = (row.cells[1]?.textContent || "").toLowerCase();

        // CHECK MEET FILTER:
        // If the user typed something, the race name must contain it.
        // If the field is empty, the condition is always true (no constraint).
        const meetMatch = meetQuery === "" || raceName.includes(meetQuery);

        // CHECK DATE FILTER:
        // Same partial match logic applied to the date string.
        // "2023" matches "aug 31 2023", "sep 13 2023", etc.
        // "aug" matches any race in August regardless of year.
        const dateMatch = dateQuery === "" || raceDate.includes(dateQuery);

        // SHOW OR HIDE:
        // Row is visible only if it satisfies BOTH filters
        if (meetMatch && dateMatch) {
            row.style.display = "";     // Restore default display (table-row)
            visibleCount++;
        } else {
            row.style.display = "none"; // Hide row completely
        }
    });

    // HANDLE EMPTY STATE:
    // If all rows are hidden, show a helpful message so the table doesn't
    // appear broken. The message row is created once and reused.
    handleNoResults(rows, visibleCount);
}


/* ------------------------------------------------------------
   NO-RESULTS MESSAGE
   Creates (or shows/hides) a single message row in the table
   when the current filter combination matches nothing.
   This is much cleaner than showing an empty table body.
------------------------------------------------------------ */
function handleNoResults(rows, visibleCount) {

    const tbody = document.querySelector("#results-table tbody");
    if (!tbody) return;

    // Check if the message row already exists from a previous filter action
    let noResultsRow = document.getElementById("no-results-row");

    if (visibleCount === 0) {
        // No rows match — show the message
        if (!noResultsRow) {
            // First time: create the row and insert it
            noResultsRow = document.createElement("tr");
            noResultsRow.id = "no-results-row";

            // colspan="8" spans all 8 columns so the message is centered
            noResultsRow.innerHTML =
                '<td colspan="8" style="text-align:center; padding: 1.5rem; font-style:italic; opacity: 0.7;">' +
                'No races match your filter. Try clearing one of the fields.' +
                '</td>';

            tbody.appendChild(noResultsRow);
        } else {
            // Row already exists from before — just make it visible
            noResultsRow.style.display = "";
        }
    } else {
        // Rows are visible — hide the no-results message if it exists
        if (noResultsRow) {
            noResultsRow.style.display = "none";
        }
    }
}


/* ------------------------------------------------------------
   RESET FUNCTION
   Clears both filter inputs and resets all rows to visible.
   Called by the Reset button (added below in event binding).
------------------------------------------------------------ */
function resetFilters() {
    document.getElementById("filter-meet").value = "";
    document.getElementById("filter-date").value = "";
    filterResults(); // Re-run with empty queries — all rows become visible
}


/* ------------------------------------------------------------
   EVENT BINDING
   Attach listeners once the DOM is fully ready.
   'input' fires on every keystroke — gives real-time filtering
   as the user types, which is much more responsive than waiting
   for a form submit or pressing Enter.
------------------------------------------------------------ */
document.addEventListener("DOMContentLoaded", function() {

    const meetInput = document.getElementById("filter-meet");
    const dateInput = document.getElementById("filter-date");

    // Confirm both inputs exist before attaching listeners.
    // This prevents silent errors if the page structure changes.
    if (!meetInput || !dateInput) {
        console.warn("player.js: Filter inputs not found. Filter feature inactive.");
        return;
    }

    // 'input' event fires on every character typed or deleted —
    // gives instant feedback as the user types (no button needed)
    meetInput.addEventListener("input", filterResults);
    dateInput.addEventListener("input", filterResults);

    /* --------------------------------------------------------
       RESET BUTTON —  after the filter fieldset
       Rather than requiring an HTML change, we create the reset 
       button in JavaScript and insert it after the fieldset. 
       This keeps the HTML clean and self-contained in this file.
    -------------------------------------------------------- */
    const fieldset = document.querySelector(".results-filters fieldset");

    if (fieldset) {
        const resetBtn = document.createElement("button");
        resetBtn.type    = "button";           // type="button" prevents any form submit
        resetBtn.id      = "reset-filters-btn";
        resetBtn.textContent = "Reset Filters";

        // Inline styles keep this self-contained — no CSS file change needed
        // for a single utility button
        resetBtn.style.cssText = [
            "margin-top: 0.75rem",
            "background-color: var(--primary-blue)",
            "color: white",
            "border: none",
            "border-radius: 6px",
            "padding: 0.4rem 1rem",
            "font-size: 0.85rem",
            "cursor: pointer",
            "display: block",
            "transition: opacity 0.2s ease"
        ].join(";");

        // Dim button slightly on hover for visual feedback
        resetBtn.addEventListener("mouseover", function() { this.style.opacity = "0.8"; });
        resetBtn.addEventListener("mouseout",  function() { this.style.opacity = "1"; });

        resetBtn.addEventListener("click", resetFilters);
        fieldset.appendChild(resetBtn);
    }

    // Run once on load so any pre-filled inputs (e.g. from browser autofill)
    // are applied immediately rather than waiting for user interaction
    filterResults();
});