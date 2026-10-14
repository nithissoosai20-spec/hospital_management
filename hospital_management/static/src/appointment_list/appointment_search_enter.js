/** @odoo-module **/

/*
 * =========================================================
 * HOSPITAL APPOINTMENT SEARCH - ENTER KEY
 * =========================================================
 *
 * When the user enters a Patient ID / Mobile Number
 * and presses ENTER, trigger the existing Search button.
 *
 * This keeps the existing Python search logic unchanged.
 */

document.addEventListener("keydown", function (event) {
    if (event.key !== "Enter") {
        return;
    }

    const input = event.target;
    if (!input) {
        return;
    }

    // Check if the focused element is the Patient Search field
    const isSearchInput = (
        input.getAttribute && (
            input.getAttribute("name") === "search_patient" ||
            input.getAttribute("placeholder") === "Patient ID or Mobile Number"
        )
    ) || Boolean(input.closest && input.closest('[name="search_patient"]'));

    if (!isSearchInput) {
        return;
    }

    const form = input.closest(".hospital_appointment_form") || document.querySelector(".hospital_appointment_form");
    if (!form) {
        return;
    }

    // Prevent default form Enter submission
    event.preventDefault();
    event.stopPropagation();

    // Commit input value to model
    input.dispatchEvent(new Event("change", { bubbles: true }));

    // Trigger Search button
    const searchButton = form.querySelector('button[name="action_search_patient"]');
    if (searchButton) {
        searchButton.click();
    }
}, true);
