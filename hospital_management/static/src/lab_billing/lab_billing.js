/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, onWillDestroy } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class LabBilling extends Component {
    static template = "hospital_management.LabBilling";

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.notification = useService("notification");

        this.state = useState({
            admissionType: "with_admission",
            patientSearchTerm: "",
            patient: null,
            testSearchTerm: "",
            tests: [],
            testSuggestions: [],
            showTestSuggestions: false,
            selectedTest: null,
            focusedSuggestionIndex: -1,

            showPaymentModal: false,
            paymentSuccess: false,
            lastBillId: false,
            currentBillId: false,
            billState: "draft",
            isReadOnly: false,

            billDiscount: 0,
            paidAmount: 0,
            paymentMode: "none",
            transactionId: "",
            remarks: "",

            subTotal: 0,
            discountAmount: 0,
            autoRoundOff: 0,
            netAmount: 0,
            grandTotal: 0,
            totalQuantity: 0,
            invoiceNo: "Draft",

            billDate: new Date().toISOString().split("T")[0],
            billTime: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false }),

            doctors: [],
            selectedDoctor: "",
            departments: [],
            selectedDepartment: "",

            walkinName: "",
            walkinPhone: "",
            walkinAge: "",
            walkinGender: "male",
            walkinAddress: "",

            // Denominations
            d500r: 0, d500p: 0,
            d200r: 0, d200p: 0,
            d100r: 0, d100p: 0,
            d50r: 0, d50p: 0,
            d20r: 0, d20p: 0,
            d10r: 0, d10p: 0,
            coinsR: 0, coinsP: 0,
            denomTotalReceived: 0,
            denomTotalRepay: 0,
            totalAmountPaid: 0,
            balanceAmount: 0,
        });

        this.timeInterval = setInterval(() => {
            if (this.state && !this.state.currentBillId && !this.state.isReadOnly) {
                this.state.billTime = new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false });
                this.state.billDate = new Date().toISOString().split("T")[0];
            }
        }, 1000);

        onWillDestroy(() => {
            if (this.timeInterval) clearInterval(this.timeInterval);
        });

        onWillStart(async () => {
            await this.fetchDepartments();
            await this.fetchDoctors();

            const activeId = this.props.action && this.props.action.context && this.props.action.context.active_id;
            if (activeId) {
                await this.loadExistingBill(activeId);
            }
        });
    }

    async fetchDepartments() {
        try {
            const depts = await this.orm.call("hospital.department", "search_read", [], { fields: ["id", "name"] });
            this.state.departments = depts;
        } catch (e) {
            console.warn("Could not fetch departments", e);
        }
    }

    async fetchDoctors() {
        try {
            const all_users = await this.orm.call("hospital.user", "search_read", [], { fields: ["id", "name", "department_id", "role_id"] });
            this.state.doctors = all_users.filter(u => u.role_id && u.role_id[1] && u.role_id[1].toLowerCase().includes("doctor"));
        } catch (e) {
            console.warn("Could not fetch doctors", e);
        }
    }

    onPatientSearchKeyDown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.searchPatient();
        }
    }

    async searchPatient() {
        const term = (this.state.patientSearchTerm || "").trim();
        if (!term) return;

        const patients = await this.orm.call("hospital.patient", "search_read", [
            ["|", ["patient_id", "ilike", term], ["phone", "ilike", term]]
        ], { limit: 1, fields: ["id", "name", "patient_id", "phone", "age", "gender", "address"] });

        if (patients.length > 0) {
            let p = patients[0];
            this.state.patient = {
                id: p.id,
                seq: p.patient_id,
                name: p.name,
                phone: p.phone,
                age: p.age,
                gender: p.gender,
                address: p.address || "--",
            };

            // Fetch last appointment doctor and department
            const apps = await this.orm.call("hospital.appointment", "search_read", [
                [["patient_id", "=", p.id]]
            ], { limit: 1, order: "id desc", fields: ["doctor_id", "department_id"] });

            if (apps.length > 0 && apps[0].doctor_id) {
                this.state.selectedDoctor = apps[0].doctor_id[0];
                if (apps[0].department_id) {
                    this.state.selectedDepartment = apps[0].department_id[0];
                }
            }

            // AUTO-FETCH DOCTOR PRESCRIBED LAB TESTS
            try {
                const labAppointments = await this.orm.call("hospital.lab.appointment", "search_read", [
                    [["patient_id", "=", p.id], ["payment_status", "=", "pending"]]
                ], { limit: 1, order: "id desc", fields: ["id", "doctor_id"] });

                if (labAppointments.length > 0) {
                    const labAppId = labAppointments[0].id;
                    if (labAppointments[0].doctor_id && !this.state.selectedDoctor) {
                        this.state.selectedDoctor = labAppointments[0].doctor_id[0];
                    }

                    const bLines = await this.orm.call("hospital.lab.appointment.line", "search_read", [
                        [["lab_appointment_id", "=", labAppId], ["is_parameter", "=", false]]
                    ], { fields: ["lab_test_id", "price"] });

                    let tests_added = 0;
                    for (let b of bLines) {
                        if (b.lab_test_id) {
                            const testDetails = await this.orm.call("hospital.lab.test", "search_read", [
                                [["id", "=", b.lab_test_id[0]]]
                            ], { fields: ["id", "name", "code", "lab_category_id", "price"] });

                            if (testDetails.length > 0) {
                                let t = testDetails[0];
                                let existing = this.state.tests.find(x => x.id === t.id);
                                if (!existing) {
                                    const testPrice = b.price || t.price || 0;
                                    this.state.tests.push({
                                        id: t.id,
                                        code: t.code || "--",
                                        name: t.name,
                                        category: t.lab_category_id ? t.lab_category_id[1] : "--",
                                        price: testPrice,
                                        discount: 0,
                                        discountVal: 0,
                                        total_amount: testPrice,
                                    });
                                    tests_added++;
                                }
                            }
                        }
                    }

                    if (tests_added > 0) {
                        this.calculateTotals();
                        this.notification.add(`${tests_added} prescribed lab test(s) auto-loaded!`, { type: "info" });
                    } else {
                        this.notification.add("Patient linked!", { type: "success" });
                    }
                } else {
                    this.notification.add("Patient linked! (No pending lab prescriptions found)", { type: "success" });
                }
            } catch (e) {
                console.error("Failed to auto-fetch lab tests", e);
                this.notification.add("Patient linked!", { type: "success" });
            }
        } else {
            this.notification.add(`No patient found with ID: ${term}`, { type: "warning" });
        }
    }

    async onTestSearchInput(ev) {
        this.state.testSearchTerm = ev.target.value;
        if (this.state.testSearchTerm.length < 2) {
            this.state.testSuggestions = [];
            this.state.showTestSuggestions = false;
            this.state.focusedSuggestionIndex = -1;
            return;
        }
        const tests = await this.orm.call("hospital.lab.test", "search_read", [
            ["|", ["name", "ilike", this.state.testSearchTerm], ["code", "ilike", this.state.testSearchTerm]]
        ], { limit: 10, fields: ["id", "name", "code", "lab_category_id", "price"] });

        this.state.testSuggestions = tests;
        this.state.showTestSuggestions = true;
        this.state.focusedSuggestionIndex = -1;
    }

    selectTest(test) {
        this.state.selectedTest = {
            id: test.id,
            code: test.code || "--",
            name: test.name,
            category: test.lab_category_id ? test.lab_category_id[1] : "--",
            price: test.price || 0,
            discount: 0,
            discountVal: 0,
            total_amount: test.price || 0,
        };
        this.state.testSearchTerm = test.name;
        this.state.testSuggestions = [];
        this.state.showTestSuggestions = false;
        this.state.focusedSuggestionIndex = -1;
    }

    addSelectedTestToBill() {
        if (!this.state.selectedTest) {
            this.notification.add("Please search and select a lab test first.", { type: "warning" });
            return;
        }
        const t = this.state.selectedTest;
        const existing = this.state.tests.find(x => x.id === t.id);
        if (existing) {
            this.notification.add("Test is already added to bill.", { type: "warning" });
            return;
        }
        this.state.tests.push({ ...t });
        this.state.selectedTest = null;
        this.state.testSearchTerm = "";
        this.calculateTotals();
    }

    removeTest(id) {
        this.state.tests = this.state.tests.filter(t => t.id !== id);
        this.calculateTotals();
    }

    updateLineDiscount(id, val) {
        const t = this.state.tests.find(x => x.id === id);
        if (t) {
            t.discount = parseFloat(val) || 0;
            this.calculateTotals();
        }
    }

    onBillDiscountChange(val) {
        this.state.billDiscount = parseFloat(val) || 0;
        this.calculateTotals();
    }

    calculateTotals() {
        let subTotal = 0;
        let lineDiscount = 0;

        for (let t of this.state.tests) {
            const discVal = t.price * ((t.discount || 0) / 100);
            t.discountVal = discVal;
            t.total_amount = Math.max(0, t.price - discVal);
            subTotal += t.price;
            lineDiscount += discVal;
        }

        const billDisc = parseFloat(this.state.billDiscount) || 0;
        const totalDisc = lineDiscount + billDisc;
        const rawNet = Math.max(0, subTotal - totalDisc);
        const roundedNet = Math.round(rawNet);

        this.state.subTotal = subTotal;
        this.state.discountAmount = totalDisc;
        this.state.autoRoundOff = Math.round((roundedNet - rawNet) * 100) / 100;
        this.state.netAmount = roundedNet;
        this.state.grandTotal = roundedNet;
        this.state.totalQuantity = this.state.tests.length;
    }

    openPaymentModal() {
        if (this.state.admissionType === "with_admission" && !this.state.patient) {
            this.notification.add("Please enter and search Patient ID first.", { type: "danger" });
            return;
        }
        if (this.state.admissionType === "without_admission" && !this.state.walkinName) {
            this.notification.add("Please enter patient name for walk-in billing.", { type: "danger" });
            return;
        }
        if (this.state.tests.length === 0) {
            this.notification.add("Please add at least one lab test to the bill.", { type: "warning" });
            return;
        }

        for (const k of ["d500r","d500p","d200r","d200p","d100r","d100p","d50r","d50p","d20r","d20p","d10r","d10p","coinsR","coinsP"]) {
            this.state[k] = 0;
        }
        this.state.paymentMode = "none";
        this.state.paidAmount = 0;
        this.state.transactionId = "";
        this.state.denomTotalReceived = 0;
        this.state.denomTotalRepay = 0;
        this.state.totalAmountPaid = 0;
        this.state.balanceAmount = this.state.netAmount;

        this.state.paymentSuccess = false;
        this.state.showPaymentModal = true;
    }

    closePaymentModal() {
        this.state.showPaymentModal = false;
    }

    onDenomInput(field, rawVal) {
        this.state[field] = parseInt(rawVal) || 0;
        this.calcTotalAmountPaid();
    }

    onDigiPayInput(rawVal) {
        this.state.paidAmount = parseFloat(rawVal) || 0;
        this.calcTotalAmountPaid();
    }

    calcTotalAmountPaid() {
        const s = this.state;
        const totalR = s.d500r * 500 + s.d200r * 200 + s.d100r * 100 + s.d50r * 50 + s.d20r * 20 + s.d10r * 10 + s.coinsR;
        const totalP = s.d500p * 500 + s.d200p * 200 + s.d100p * 100 + s.d50p * 50 + s.d20p * 20 + s.d10p * 10 + s.coinsP;
        s.denomTotalReceived = totalR;
        s.denomTotalRepay = totalP;

        s.totalAmountPaid = Math.round((s.paidAmount + totalR - totalP) * 100) / 100;
        s.balanceAmount = Math.round((s.netAmount - s.totalAmountPaid) * 100) / 100;
    }

    async collectPayment() {
        if (this.state.admissionType === "with_admission" && !this.state.patient) {
            this.notification.add("Please search a valid Patient ID first.", { type: "danger" });
            return;
        }
        if (this.state.admissionType === "without_admission" && !this.state.walkinName) {
            this.notification.add("Please enter patient name.", { type: "danger" });
            return;
        }
        if (this.state.tests.length === 0) {
            this.notification.add("Please add at least one lab test.", { type: "danger" });
            return;
        }

        if (this.state.paymentMode !== "none") {
            if (!this.state.transactionId) {
                this.notification.add("Please enter a valid Transaction ID for digital payment.", { type: "danger" });
                return;
            }
            if (this.state.paidAmount <= 0) {
                this.notification.add("Please enter online paid amount.", { type: "danger" });
                return;
            }
        }

        if (this.state.balanceAmount !== 0) {
            this.notification.add("Transaction incomplete: The total received payment must match the net bill amount.", { type: "danger" });
            return;
        }

        const line_ids = this.state.tests.map(t => [0, 0, {
            lab_test_id: t.id,
            test_name: t.name,
            test_code: t.code,
            category_name: t.category,
            price: t.price,
            discount: t.discount || 0,
            discount_amount: t.discountVal || 0,
            total_amount: t.total_amount || t.price,
        }]);

        try {
            const vals = {
                admission_type: this.state.admissionType,
                patient_id: this.state.patient ? this.state.patient.id : false,
                walkin_name: this.state.walkinName,
                walkin_phone: this.state.walkinPhone,
                walkin_age: parseInt(this.state.walkinAge) || 0,
                walkin_gender: this.state.walkinGender,
                walkin_address: this.state.walkinAddress,
                doctor_id: this.state.selectedDoctor ? parseInt(this.state.selectedDoctor) : false,
                doctor_department_id: this.state.selectedDepartment ? parseInt(this.state.selectedDepartment) : false,
                payment_mode: this.state.paymentMode === "none" ? "cash" : this.state.paymentMode,
                paid_amount: this.state.totalAmountPaid,
                bill_discount: this.state.billDiscount,
                state: "paid",
            };

            if (this.state.currentBillId) {
                vals.line_ids = [[5, 0, 0]].concat(line_ids);
                await this.orm.write("hospital.lab.bill", [this.state.currentBillId], vals);
                const bill = await this.orm.read("hospital.lab.bill", [this.state.currentBillId], ["name"]);
                this.state.invoiceNo = bill[0].name;
                this.state.lastBillId = this.state.currentBillId;
            } else {
                vals.line_ids = line_ids;
                const bill_id = await this.orm.create("hospital.lab.bill", [vals]);
                const bill = await this.orm.read("hospital.lab.bill", [bill_id[0]], ["name"]);
                this.state.invoiceNo = bill[0].name;
                this.state.lastBillId = bill_id[0];
                this.state.currentBillId = bill_id[0];
            }

            this.state.billState = "paid";
            this.state.paymentSuccess = true;
            this.state.isReadOnly = true;
        } catch (e) {
            this.notification.add("Error saving bill: " + e.message, { type: "danger" });
        }
    }

    async saveAsHold() {
        if (this.state.admissionType === "with_admission" && !this.state.patient) {
            this.notification.add("Please search a valid Patient ID first.", { type: "danger" });
            return;
        }
        if (this.state.admissionType === "without_admission" && !this.state.walkinName) {
            this.notification.add("Please enter patient name.", { type: "danger" });
            return;
        }
        if (this.state.tests.length === 0) {
            this.notification.add("Please add at least one lab test.", { type: "danger" });
            return;
        }

        const line_ids = this.state.tests.map(t => [0, 0, {
            lab_test_id: t.id,
            test_name: t.name,
            test_code: t.code,
            category_name: t.category,
            price: t.price,
            discount: t.discount || 0,
            discount_amount: t.discountVal || 0,
            total_amount: t.total_amount || t.price,
        }]);

        try {
            const vals = {
                admission_type: this.state.admissionType,
                patient_id: this.state.patient ? this.state.patient.id : false,
                walkin_name: this.state.walkinName,
                walkin_phone: this.state.walkinPhone,
                walkin_age: parseInt(this.state.walkinAge) || 0,
                walkin_gender: this.state.walkinGender,
                walkin_address: this.state.walkinAddress,
                doctor_id: this.state.selectedDoctor ? parseInt(this.state.selectedDoctor) : false,
                doctor_department_id: this.state.selectedDepartment ? parseInt(this.state.selectedDepartment) : false,
                payment_mode: this.state.paymentMode === "none" ? "cash" : this.state.paymentMode,
                paid_amount: 0,
                bill_discount: this.state.billDiscount,
                state: "held",
            };

            if (this.state.currentBillId) {
                vals.line_ids = [[5, 0, 0]].concat(line_ids);
                await this.orm.write("hospital.lab.bill", [this.state.currentBillId], vals);
                this.state.lastBillId = this.state.currentBillId;
            } else {
                vals.line_ids = line_ids;
                const bill_id = await this.orm.create("hospital.lab.bill", [vals]);
                this.state.lastBillId = bill_id[0];
                this.state.currentBillId = bill_id[0];
            }

            this.state.billState = "held";
            this.notification.add("Lab Bill Held Successfully!", { type: "success" });
            this.state.showPaymentModal = false;
            this.clearBill();
        } catch (e) {
            this.notification.add("Error holding bill: " + e.message, { type: "danger" });
        }
    }

    startNewBill() {
        this.state.showPaymentModal = false;
        this.clearBill();
    }

    async clearBill() {
        if (this.state.currentBillId && this.state.billState === "draft") {
            try { await this.orm.unlink("hospital.lab.bill", [this.state.currentBillId]); } catch (e) {}
        }
        this.state.patient = null;
        this.state.patientSearchTerm = "";
        this.state.walkinName = "";
        this.state.walkinPhone = "";
        this.state.walkinAge = "";
        this.state.walkinAddress = "";
        this.state.tests = [];
        this.state.selectedTest = null;
        this.state.testSearchTerm = "";
        this.state.paidAmount = 0;
        this.state.billDiscount = 0;
        this.state.invoiceNo = "Draft";
        this.state.currentBillId = false;
        this.state.billState = "draft";
        this.state.isReadOnly = false;
        this.calculateTotals();
    }

    closePOS() {
        this.action.doAction("hospital_management.action_hospital_lab_bill_window");
    }

    printReceipt() {
        if (!this.state.lastBillId) return;
        this.state.showPaymentModal = false;
        this.action.doAction({
            type: "ir.actions.report",
            report_type: "qweb-pdf",
            report_name: "hospital_management.report_hospital_lab_bill",
            report_file: "hospital_management.report_hospital_lab_bill",
            context: { active_ids: [this.state.lastBillId] },
        });
    }

    async loadExistingBill(billId) {
        const bills = await this.orm.searchRead("hospital.lab.bill", [["id", "=", billId]], []);
        if (bills.length > 0) {
            const bill = bills[0];
            this.state.currentBillId = bill.id;
            this.state.lastBillId = bill.id;
            this.state.billState = bill.state;
            this.state.isReadOnly = (bill.state === "paid");
            this.state.invoiceNo = bill.name;

            this.state.admissionType = bill.admission_type;
            if (bill.admission_type === "with_admission" && bill.patient_id) {
                this.state.patientSearchTerm = bill.patient_id_display || bill.patient_id[1];
                this.state.patient = {
                    id: bill.patient_id[0],
                    name: bill.patient_id[1],
                    seq: bill.patient_id_display || "",
                    phone: bill.patient_phone || "",
                    gender: bill.patient_gender || "",
                    age: bill.patient_age || "",
                    address: bill.patient_address || "",
                };
            } else {
                this.state.walkinName = bill.walkin_name || "";
                this.state.walkinPhone = bill.walkin_phone || "";
                this.state.walkinAge = bill.walkin_age || "";
                this.state.walkinGender = bill.walkin_gender || "male";
                this.state.walkinAddress = bill.walkin_address || "";
            }

            if (bill.doctor_id) this.state.selectedDoctor = bill.doctor_id[0];
            if (bill.doctor_department_id) this.state.selectedDepartment = bill.doctor_department_id[0];

            this.state.billDate = bill.bill_date ? bill.bill_date.split(" ")[0] : this.state.billDate;
            this.state.paymentMode = bill.payment_mode;
            this.state.paidAmount = bill.paid_amount;
            this.state.billDiscount = bill.bill_discount;
            this.state.remarks = bill.notes || "";

            // Load lines
            const lines = await this.orm.searchRead("hospital.lab.bill.line", [["bill_id", "=", bill.id]], []);
            let tests = [];
            for (let line of lines) {
                tests.push({
                    id: line.lab_test_id[0],
                    code: line.test_code || "--",
                    name: line.test_name || line.lab_test_id[1],
                    category: line.category_name || "--",
                    price: line.price || 0,
                    discount: line.discount || 0,
                    discountVal: line.discount_amount || 0,
                    total_amount: line.total_amount || line.price || 0,
                });
            }
            this.state.tests = tests;
            this.calculateTotals();
        }
    }
}

registry.category("actions").add("hospital_lab_billing", LabBilling);
