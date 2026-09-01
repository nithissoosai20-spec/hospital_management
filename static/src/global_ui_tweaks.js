// HELPER: Get a clean, human-readable page name
function getPageName() {
    let text = document.title.split(' - ')[0].trim();
    if (!text || text === 'Odoo') return null;
    return text;
}

// PAGE TITLE BANNER
// Injects a centered page title banner below the nav menu
let lastPageTitle = null;

function injectPageTitle() {
    // Don't show on dashboards or form views (sub-pages)
    if (document.querySelector('.adb, .ddb, .pdb, .rdb') || document.querySelector('.o_form_view') || window.location.hash.includes('view_type=form')) {
        const existing = document.getElementById('hospital-page-title-banner');
        if (existing) existing.remove();
        lastPageTitle = null;
        return;
    }

    const pageName = getPageName();
    if (!pageName) return;

    // Don't re-inject if the title hasn't changed
    if (pageName === lastPageTitle) return;
    lastPageTitle = pageName;

    // Remove any existing banner
    const existing = document.getElementById('hospital-page-title-banner');
    if (existing) existing.remove();

    // Find the right container to insert into (just before the content)
    const target = document.querySelector('.o_action_manager') ||
                   document.querySelector('.o_content') ||
                   document.querySelector('.o_main_content');
    if (!target) return;

    const banner = document.createElement('div');
    banner.id = 'hospital-page-title-banner';
    // Position statically so it sits naturally below the menu, above the list/form
    banner.style.cssText = `
        width: 100%;
        text-align: center;
        padding: 4px 0 0 0;
        background: transparent;
        pointer-events: none;
    `;
    banner.innerHTML = `
        <span style="
            font-size: 14px;
            font-weight: 800;
            color: #29398f;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            font-family: Arial, sans-serif;
            background: rgba(255, 255, 255, 0.85);
            padding: 3px 10px;
            border-radius: 4px;
        ">${pageName}</span>
    `;

    target.insertBefore(banner, target.firstChild);
}

// "Add New ..." BUTTON LABEL FIXER
const observer = new MutationObserver(() => {
    // --- Page Title ---
    injectPageTitle();

    // --- Button text ---
    const addBtns = document.querySelectorAll('.o_control_panel .o_list_button_add, .o_control_panel .o_form_button_create');
    if (addBtns.length > 0) {
        let contextName = "Item";
        let text = document.title.split(' - ')[0].trim();

        if (text) {
            if (text.toLowerCase() === "patients") text = "Patient";
            else if (text.toLowerCase() === "appointments") text = "Appointment";
            else if (text.toLowerCase() === "doctors") text = "Doctor";
            else if (text.toLowerCase() === "users") text = "User";
            else if (text.toLowerCase() === "departments") text = "Department";
            else if (text.toLowerCase().includes("billing")) text = "Bill";
            else if (text.toLowerCase().includes("purchase")) text = "Purchase";
            else if (text.endsWith('s')) text = text.slice(0, -1);

            if (text !== "Odoo") contextName = text;
        }

        addBtns.forEach(btn => {
            if (btn.textContent.trim() === 'New') {
                btn.textContent = `Add New ${contextName}`;
            }
        });
    }
});

const startObserving = () => {
    if (document.body) {
        observer.observe(document.body, { childList: true, subtree: true });
        injectPageTitle(); // Run once on load
    } else {
        setTimeout(startObserving, 50);
    }
};

if (document.readyState === 'loading') {
    window.addEventListener('DOMContentLoaded', startObserving);
} else {
    startObserving();
}
