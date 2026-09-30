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

    // Only handle ENTER
    if (event.key !== "Enter") {
        return;
    }

    // Find the currently focused element
    const input = event.target;

    // Only work with the Patient Search field
    if (
        !input ||
        input.getAttribute("name") !== "search_patient"
    ) {
        return;
    }

    // Find the Hospital Appointment form
    const form = input.closest(
        ".hospital_appointment_form"
    );

    if (!form) {
        return;
    }

    // Prevent normal browser/form Enter behavior
    event.preventDefault();
    event.stopPropagation();

    // Find the existing Search button
    const searchButton = form.querySelector(
        'button[name="action_search_patient"]'
    );

    if (!searchButton) {
        return;
    }

    // Trigger the exact same action as clicking Search
    searchButton.click();

});
