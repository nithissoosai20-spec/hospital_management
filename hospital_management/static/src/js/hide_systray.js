/** @odoo-module **/

import { registry } from "@web/core/registry";

const systrayRegistry = registry.category("systray");

// Remove Discuss (Messaging) Menu
systrayRegistry.remove("mail.messaging_menu");

// Remove Activity Menu
systrayRegistry.remove("mail.activity_menu");
