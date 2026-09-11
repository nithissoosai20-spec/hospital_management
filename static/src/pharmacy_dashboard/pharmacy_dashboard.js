/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, onWillDestroy } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";


// COMMON PHARMACY COMPONENT

class PharmacyBase extends Component {

    setup() {
        this.action = useService("action");
        this.notification = useService("notification");
    }

    goTo(xmlid) {
        this.action.doAction(xmlid);
    }

    notify(message, type = "success") {
        this.notification.add(message, {
            type: type,
        });
    }
}


// PHARMACY DASHBOARD

class PharmacyDashboard extends PharmacyBase {

    static template = "hospital_management.PharmacyDashboard";

    openBilling() {
        this.goTo("hospital_management.action_hospital_pharmacy_billing");
    }

    openPurchase() {
        this.goTo("hospital_management.action_hospital_pharmacy_purchase_list");
    }

    openStock() {
        this.goTo("hospital_management.action_hospital_pharmacy_stock");
    }

    openDetails() {
        this.goTo("hospital_management.action_hospital_pharmacy_details");
    }
}


// PHARMACY BILLING

class PharmacyBilling extends PharmacyBase {
    static template = "hospital_management.PharmacyBilling";
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
                this.state = useState({
            customerType: "patient",
            patientSearchTerm: "", patient: null, medicineSearchTerm: "", medicines: [], medicineSuggestions: [], showMedicineSuggestions: false,
            selectedMedicine: null, showPaymentModal: false, paymentSuccess: false, lastBillId: false, focusedSuggestionIndex: -1,
            billDiscount: 0, paidAmount: 0, paymentMode: "cash", remarks: "", roundOff: 0,
            grossAmount: 0, subTotal: 0, totalDiscount: 0, totalGst: 0, taxableAmount: 0, grandTotal: 0, netAmount: 0,
            changeReturn: 0, invoiceNo: "Draft", totalQuantity: 0, billDate: new Date().toISOString().split('T')[0], billTime: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
            doctors: [], selectedDoctor: "", departments: [], selectedDepartment: "",
            walkinName: "", walkinPhone: "", walkinAddress: "",
            isReadOnly: false, currentBillId: false, billState: 'draft',
            d2000c: 0, d500c: 0, d200c: 0, d100c: 0, d50c: 0, d20c: 0, d10c: 0,
            payCash: 0, payUpi: 0, payCard: 0, payCredit: 0, totalAmountPaid: 0, balanceAmount: 0,
        });
        this.timeInterval = setInterval(() => {
            if (this.state && !this.state.currentBillId && !this.state.isReadOnly) {
                this.state.billTime = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
                this.state.billDate = new Date().toISOString().split('T')[0];
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

    openDashboard() { this.goTo("hospital_management.action_hospital_pharmacy_dashboard_form"); }
    openPurchase() { this.goTo("hospital_management.action_hospital_pharmacy_purchase_list"); }
    openStock() { this.goTo("hospital_management.action_hospital_pharmacy_stock"); }
    openDetails() { this.goTo("hospital_management.action_hospital_pharmacy_details"); }
    closePOS() { this.goTo("hospital_management.action_hospital_pharmacy_bill_window"); }



        async loadExistingBill(billId) {
        const bills = await this.orm.searchRead("hospital.pharmacy.bill", [["id", "=", billId]], []);
        if (bills.length > 0) {
            const bill = bills[0];
            this.state.currentBillId = bill.id;
            this.state.lastBillId = bill.id;
            this.state.billState = bill.state;
            this.state.isReadOnly = (bill.state === 'paid');

            this.state.customerType = bill.customer_type;
            if (bill.customer_type === 'patient' && bill.patient_id) {
                this.state.patientSearchTerm = bill.patient_id[1];
                this.state.patient = {
                    id: bill.patient_id[0],
                    name: bill.patient_id[1],
                    patient_id: bill.patient_id_display || "",
                    gender: bill.patient_gender || "",
                    age: bill.patient_age || "",
                    address: bill.patient_address || ""
                };
            } else {
                this.state.walkinName = bill.walkin_name || "";
                this.state.walkinPhone = bill.walkin_phone || "";
                this.state.walkinAddress = bill.walkin_address || "";
            }

            if (bill.doctor_id) this.state.selectedDoctor = bill.doctor_id[0];
            if (bill.doctor_department_id) this.state.selectedDepartment = bill.doctor_department_id[0];

            this.state.billDate = bill.bill_date ? bill.bill_date.split(" ")[0] : this.state.billDate;
            this.state.paymentMode = bill.payment_mode;
            this.state.paidAmount = bill.paid_amount;
            this.state.billDiscount = bill.bill_discount;
            this.state.remarks = bill.notes || "";

            // load lines
            const lines = await this.orm.searchRead("hospital.pharmacy.bill.line", [["bill_id", "=", bill.id]], []);
            let medicines = [];
            for (let i = 0; i < lines.length; i++) {
                let line = lines[i];
                medicines.push({
                    id: line.stock_id[0],
                    stock_id: line.stock_id[0],
                    code: line.medicine_code || "",
                    name: line.medicine_name || line.stock_id[1],
                    batch: line.batch || "",
                    expiry: line.expiry || "",
                    unit: line.unit || "",
                    mrp: line.mrp || 0,
                    price: line.selling_price || line.mrp || 0,
                    qty: line.qty || 1,
                    free_qty: line.free_qty || 0,
                    discount: line.discount || 0,
                    cgst_percent: line.cgst_percent || 0,
                    sgst_percent: line.sgst_percent || 0,
                    igst_percent: line.igst_percent || 0,
                    cgst_val: line.cgst || 0,
                    sgst_val: line.sgst || 0,
                    igst_val: line.igst || 0,
                    amount: line.amount || 0,
                    total_amount: line.total_amount || 0,
                    gst: line.gst || 0,
                    stock: line.available_stock || 0
                });
            }
            this.state.medicines = medicines;
            this.calculateTotals();
        }
    }

    updateFreeQty(id, val) {
        let m = this.state.medicines.find(x => x.id === id);
        if (m) {
            m.free_qty = parseInt(val) || 0;
            this.calculateTotals();
            this.syncCart();
        }
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
            this.state.doctors = all_users.filter(u => u.role_id && u.role_id[1] && u.role_id[1].toLowerCase().includes('doctor'));
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
        if (!this.state.patientSearchTerm) return;
        const patients = await this.orm.call("hospital.patient", "search_read", [
            ['|', ['patient_id', 'ilike', this.state.patientSearchTerm], ['phone', 'ilike', this.state.patientSearchTerm]]
        ], { limit: 1, fields: ['id', 'name', 'patient_id', 'phone', 'age', 'gender', 'address'] });

        if (patients.length > 0) {
            let p = patients[0];
            this.state.patient = { id: p.id, seq: p.patient_id, name: p.name, phone: p.phone, age: p.age, gender: p.gender, address: p.address || '--' };

            // Automatically fetch last appointment doctor and department
            const apps = await this.orm.call("hospital.appointment", "search_read", [
                [['patient_id', '=', p.id]]
            ], { limit: 1, order: 'id desc', fields: ['doctor_id', 'department_id'] });

            if (apps.length > 0 && apps[0].doctor_id) {
                this.state.selectedDoctor = apps[0].doctor_id[0];
                if (apps[0].department_id) {
                    this.state.selectedDepartment = apps[0].department_id[0];
                }
                this.notification.add("Patient linked & last doctor loaded!", { type: "success" });
            } else {
                this.notification.add("Patient linked!", { type: "success" });
            }
        } else {
            this.notification.add("Patient not found.", { type: "warning" });
        }
    }


    async onMedicineSearchInput(ev) {
        this.state.medicineSearchTerm = ev.target.value;
        if (this.state.medicineSearchTerm.length < 2) {
            this.state.medicineSuggestions = [];
            this.state.showMedicineSuggestions = false;
        this.state.focusedSuggestionIndex = -1;
            return;
        }
        const meds = await this.orm.call("hospital.pharmacy.stock", "search_read", [
            ['|', ['medicine_name', 'ilike', this.state.medicineSearchTerm], ['medicine_code', 'ilike', this.state.medicineSearchTerm]]
        ], { limit: 10, fields: ['id', 'medicine_name', 'medicine_code', 'batch_number', 'expiry_date', 'selling_price', 'quantity', 'cgst', 'sgst', 'igst'] });
        this.state.medicineSuggestions = meds;
        this.state.showMedicineSuggestions = true;
        this.state.focusedSuggestionIndex = -1;
    }


    onDoctorChange(val) {
        this.state.selectedDoctor = val;
        let doc = this.state.doctors.find(d => d.id == val);
        if (doc && doc.department_id) {
            this.state.selectedDepartment = doc.department_id[0];
        } else {
            this.state.selectedDepartment = "";
        }
    }

    onMedicineSearchKeyDown(ev) {
        if (!this.state.showMedicineSuggestions || this.state.medicineSuggestions.length === 0) return;

        if (ev.key === "ArrowDown") {
            ev.preventDefault();
            this.state.focusedSuggestionIndex = (this.state.focusedSuggestionIndex + 1) % this.state.medicineSuggestions.length;
        } else if (ev.key === "ArrowUp") {
            ev.preventDefault();
            let newIndex = this.state.focusedSuggestionIndex - 1;
            if (newIndex < 0) newIndex = this.state.medicineSuggestions.length - 1;
            this.state.focusedSuggestionIndex = newIndex;
        } else if (ev.key === "Enter") {
            ev.preventDefault();
            if (this.state.focusedSuggestionIndex >= 0 && this.state.focusedSuggestionIndex < this.state.medicineSuggestions.length) {
                this.selectMedicine(this.state.medicineSuggestions[this.state.focusedSuggestionIndex]);
            } else if (this.state.medicineSuggestions.length > 0) {
                this.selectMedicine(this.state.medicineSuggestions[0]);
            }
        }
    }

    async syncCart() {
        if (this.state.medicines.length === 0 && !this.state.currentBillId) return;

        let line_ids = this.state.medicines.map(m => [0, 0, {
            stock_id: m.id, medicine_name: m.name, composition: m.composition, batch: m.batch, expiry: m.expiry,
            qty: m.qty, free_qty: m.free_qty || 0, unit: m.unit, mrp: m.price, discount: m.discount,
            cgst_percent: m.cgst_percent, sgst_percent: m.sgst_percent, igst_percent: m.igst_percent
        }]);

        let vals = {
            customer_type: this.state.customerType === 'walk-in' ? 'walkin' : 'patient',
            patient_id: this.state.patient ? this.state.patient.id : false,
            walkin_name: this.state.walkinName, walkin_phone: this.state.walkinPhone, walkin_address: this.state.walkinAddress,
            doctor_id: this.state.selectedDoctor ? parseInt(this.state.selectedDoctor) : false,
            doctor_department_id: this.state.selectedDepartment ? parseInt(this.state.selectedDepartment) : false,
            payment_mode: this.state.paymentMode, paid_amount: this.state.paidAmount,
            bill_discount: this.state.billDiscount, state: "draft"
        };

        if (this.state.currentBillId) {
            vals.line_ids = [[5, 0, 0]].concat(line_ids);
            try { await this.orm.write("hospital.pharmacy.bill", [this.state.currentBillId], vals); } catch(e) {}
        } else {
            vals.line_ids = line_ids;
            try {
                let bill_id = await this.orm.create("hospital.pharmacy.bill", [vals]);
                this.state.currentBillId = bill_id[0];
                this.state.lastBillId = bill_id[0];
            } catch(e) {}
        }
    }

    async selectMedicine(m) {
        this.state.selectedMedicine = {
            id: m.id, code: m.medicine_code, name: m.medicine_name, composition: "--", batch: m.batch_number || "--",
            expiry: m.expiry_date || "--", stock: m.quantity || 0, qty: 1, unit: "Tab", mrp: m.selling_price || 0, price: m.selling_price || 0, 
            discount: 0, discountVal: 0, 
            cgst_percent: m.cgst || 0, sgst_percent: m.sgst || 0, igst_percent: m.igst || 0,
            cgst_val: 0, sgst_val: 0, igst_val: 0, amount: 0, total_amount: 0
        };
        this.state.medicineSearchTerm = m.medicine_name;
        this.state.medicineSuggestions = [];
        this.state.showMedicineSuggestions = false;
        this.state.focusedSuggestionIndex = -1;
    }

    async addSelectedMedicineToBill() {
        if (!this.state.selectedMedicine) {
            this.notification.add("Please search and select a medicine first.", { type: "warning" });
            return;
        }
        let m = this.state.selectedMedicine;

        let stock_req = await this.orm.read("hospital.pharmacy.stock", [m.id], ["quantity"]);
        let available = stock_req[0].quantity;

        if (available < 1) {
            this.notification.add("your stock is exceeding stock on hand", { type: "danger" });
            return;
        }

        let existing = this.state.medicines.find(x => x.id === m.id);
        if (existing) {
            existing.qty += 1;
        } else {
            this.state.medicines.push({...m});
        }
        this.state.selectedMedicine = null;
        this.state.medicineSearchTerm = "";
        this.calculateTotals();
        await this.syncCart();
    }

    async searchMedicine() {
        if (!this.state.medicineSearchTerm) return;
        const meds = await this.orm.call("hospital.pharmacy.stock", "search_read", [
            ['|', ['medicine_name', 'ilike', this.state.medicineSearchTerm], ['medicine_code', 'ilike', this.state.medicineSearchTerm]]
        ], { limit: 1, fields: ['id', 'medicine_name', 'batch_number', 'expiry_date', 'selling_price', 'cgst', 'sgst', 'igst'] });

        if (meds.length > 0) {
            let m = meds[0];
            this.state.medicines.push({
                id: m.id, name: m.medicine_name, composition: "--", batch: m.batch_number || "--",
                expiry: m.expiry_date || "--", qty: 1, unit: "Tab", mrp: m.selling_price || 0, price: m.selling_price || 0, 
                discount: 0, discountVal: 0, 
                cgst_percent: m.cgst || 0, sgst_percent: m.sgst || 0, igst_percent: m.igst || 0,
                cgst_val: 0, sgst_val: 0, igst_val: 0, amount: 0, total_amount: 0
            });
            this.state.medicineSearchTerm = "";
            this.calculateTotals();
        } else {
            this.notification.add("Medicine not found.", { type: "warning" });
        }
    }

    async removeMedicine(id) { this.state.medicines = this.state.medicines.filter(m => m.id !== id); this.calculateTotals(); await this.syncCart(); }
    async changeQty(id, delta) {
        let m = this.state.medicines.find(x => x.id === id);
        if (m) {
            let newQty = m.qty + delta;
            if (newQty > 0) {
                if (delta > 0) {
                    let stock = await this.orm.read("hospital.pharmacy.stock", [m.id], ["quantity"]);
                    let available = stock[0].quantity;
                    if (delta > available) {
                        this.notification.add("your stock is exceeding stock on hand", { type: "danger" });
                        return;
                    }
                }
                m.qty = newQty;
                this.calculateTotals();
                await this.syncCart();
            }
        }
    }
    async updateQty(id, qty) {
        let m = this.state.medicines.find(x => x.id === id);
        if(m) {
            let newQty = parseFloat(qty) || 1;
            let delta = newQty - m.qty;
            if (delta > 0) {
                let stock = await this.orm.read("hospital.pharmacy.stock", [m.id], ["quantity"]);
                let available = stock[0].quantity;
                if (delta > available) {
                    this.notification.add("your stock is exceeding stock on hand", { type: "danger" });
                    // reset visual input
                    let oldQty = m.qty;
                    m.qty = 0; // force reactivity
                    await Promise.resolve();
                    m.qty = oldQty;
                    return;
                }
            }
            m.qty = newQty;
            this.calculateTotals();
            await this.syncCart();
        }
    }
    updatePaidAmount(val) { this.state.paidAmount = parseFloat(val) || 0; this.calculateTotals(); }

    calculateTotals() {
        let grossAmount = 0; let totalDiscount = 0; let totalGst = 0; let totalQty = 0;
        for (let m of this.state.medicines) {
            let itemGross = m.qty * m.price;
            let itemDiscVal = itemGross * (m.discount / 100);
            m.discountVal = itemDiscVal;
            let taxable = itemGross - itemDiscVal;
            
            let cgst_val = taxable * ((m.cgst_percent || 0) / 100);
            let sgst_val = taxable * ((m.sgst_percent || 0) / 100);
            let igst_val = taxable * ((m.igst_percent || 0) / 100);
            
            m.cgst_val = cgst_val;
            m.sgst_val = sgst_val;
            m.igst_val = igst_val;
            
            let lineGst = cgst_val + sgst_val + igst_val;
            
            m.amount = itemGross;
            m.total_amount = taxable + lineGst;
            
            grossAmount += itemGross;
            totalDiscount += itemDiscVal;
            totalGst += lineGst;
            totalQty += m.qty;
        }
        totalDiscount += parseFloat(this.state.billDiscount) || 0;
        this.state.grossAmount = grossAmount;
        this.state.totalDiscount = totalDiscount;
        this.state.totalGst = totalGst;
        this.state.subTotal = grossAmount - totalDiscount;
        this.state.netAmount = this.state.subTotal + totalGst + (parseFloat(this.state.roundOff) || 0);
        this.state.grandTotal = this.state.netAmount;
        this.state.totalQuantity = totalQty;
        this.state.changeReturn = (this.state.paidAmount - this.state.netAmount) > 0 ? (this.state.paidAmount - this.state.netAmount) : 0;
    }

    setPaymentMode(mode) { this.state.paymentMode = mode; }


    openPaymentModal() {
        if (this.state.customerType === 'patient' && !this.state.patient) { 
            this.notify("Select a patient first.", "danger"); 
            return; 
        }
        if (this.state.customerType === 'walk-in' && !this.state.walkinName) { 
            this.notify("Enter walk-in name.", "danger"); 
            return; 
        }
        if (this.state.medicines.length === 0) {
            this.notify("Please add medicines to the bill before generating.", "warning");
            return;
        }
        
        for (const k of ['d500r','d500p','d200r','d200p','d100r','d100p','d50r','d50p','d20r','d20p','d10r','d10p','coinsR','coinsP']) {
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
        const totalR = s.d500r*500 + s.d200r*200 + s.d100r*100 + s.d50r*50 + s.d20r*20 + s.d10r*10 + s.coinsR;
        const totalP = s.d500p*500 + s.d200p*200 + s.d100p*100 + s.d50p*50 + s.d20p*20 + s.d10p*10 + s.coinsP;
        s.denomTotalReceived = totalR;
        s.denomTotalRepay = totalP;
        
        s.totalAmountPaid = s.paidAmount + totalR - totalP;
        s.balanceAmount = s.netAmount - s.totalAmountPaid;
    }


    printLatestBill() {
        if (!this.state.lastBillId) {
            this.notification.add("Please generate a bill first.", { type: "warning" });
            return;
        }
        this.printReceipt();
    }

    printReceipt() {
        if (!this.state.lastBillId) return;
        this.state.showPaymentModal = false;
        this.action.doAction({
            type: 'ir.actions.report',
            report_type: 'qweb-pdf',
            report_name: 'hospital_management.report_hospital_pharmacy_bill',
            report_file: 'hospital_management.report_hospital_pharmacy_bill',
            context: { active_ids: [this.state.lastBillId] },
        });
    }

    async collectPayment() {
        if (this.state.customerType === 'patient' && !this.state.patient) { this.notification.add("Select a patient first.", { type: "danger" }); return; }
        if (this.state.customerType === 'walk-in' && !this.state.walkinName) { this.notification.add("Enter walk-in name.", { type: "danger" }); return; }
        if (this.state.medicines.length === 0) { this.notification.add("Add at least one medicine.", { type: "danger" }); return; }

        if (this.state.paymentMode !== 'none') {
            if (!this.state.transactionId) {
                this.notification.add("Please enter a valid Transaction ID for the digital payment.", { type: "danger" });
                return;
            }
            if (this.state.paidAmount <= 0) {
                this.notification.add("Digital payment selected but no online amount entered. Please provide the online paid amount.", { type: "danger" });
                return;
            }
        }
        
        if (this.state.balanceAmount !== 0) {
            this.notification.add("Transaction incomplete: The total received payment must exactly match the net bill amount.", { type: "danger" });
            return;
        }

        let line_ids = this.state.medicines.map(m => [0, 0, {
            stock_id: m.id, medicine_name: m.name, composition: m.composition, batch: m.batch, expiry: m.expiry,
            qty: m.qty, unit: m.unit, mrp: m.mrp, discount: m.discount, gst: m.gst
        }]);

        try {
            let vals = {
                customer_type: this.state.customerType === 'walk-in' ? 'walkin' : 'patient',
                patient_id: this.state.patient ? this.state.patient.id : false,
                walkin_name: this.state.walkinName, walkin_phone: this.state.walkinPhone, walkin_address: this.state.walkinAddress,
                doctor_id: this.state.selectedDoctor ? parseInt(this.state.selectedDoctor) : false,
                doctor_department_id: this.state.selectedDepartment ? parseInt(this.state.selectedDepartment) : false,
                payment_mode: this.state.paymentMode === 'none' ? 'cash' : this.state.paymentMode, 
                paid_amount: this.state.totalAmountPaid,
                bill_discount: this.state.billDiscount, state: "paid"
            };
            if (this.state.currentBillId) {
                vals.line_ids = [[5, 0, 0]].concat(line_ids);
                await this.orm.write("hospital.pharmacy.bill", [this.state.currentBillId], vals);
                let bill = await this.orm.read("hospital.pharmacy.bill", [this.state.currentBillId], ["name"]);
                this.state.invoiceNo = bill[0].name;
                this.state.lastBillId = this.state.currentBillId;
            } else {
                vals.line_ids = line_ids;
                let bill_id = await this.orm.create("hospital.pharmacy.bill", [vals]);
                let bill = await this.orm.read("hospital.pharmacy.bill", [bill_id[0]], ["name"]);
                this.state.invoiceNo = bill[0].name;
                this.state.lastBillId = bill_id[0];
                this.state.currentBillId = bill_id[0];
            }
            this.state.billState = 'paid';
            this.state.paymentSuccess = true;
        } catch(e) {
            this.notification.add("Error: " + e.message, { type: "danger" });
        }
    }


    async saveAsHold() {
        if (this.state.customerType === 'patient' && !this.state.patient) { this.notification.add("Select a patient first.", { type: "danger" }); return; }
        if (this.state.customerType === 'walk-in' && !this.state.walkinName) { this.notification.add("Enter walk-in name.", { type: "danger" }); return; }
        if (this.state.medicines.length === 0) { this.notification.add("Add at least one medicine.", { type: "danger" }); return; }

        let line_ids = this.state.medicines.map(m => [0, 0, {
            stock_id: m.id, medicine_name: m.name, composition: m.composition, batch: m.batch, expiry: m.expiry,
            qty: m.qty, unit: m.unit, mrp: m.mrp, discount: m.discount, gst: m.gst
        }]);

        try {
            let vals = {
                customer_type: this.state.customerType === 'walk-in' ? 'walkin' : 'patient',
                patient_id: this.state.patient ? this.state.patient.id : false,
                walkin_name: this.state.walkinName, walkin_phone: this.state.walkinPhone, walkin_address: this.state.walkinAddress,
                doctor_id: this.state.selectedDoctor ? parseInt(this.state.selectedDoctor) : false,
                doctor_department_id: this.state.selectedDepartment ? parseInt(this.state.selectedDepartment) : false,
                payment_mode: this.state.paymentMode === 'none' ? 'cash' : this.state.paymentMode, 
                paid_amount: 0,
                bill_discount: this.state.billDiscount, state: "held"
            };
            if (this.state.currentBillId) {
                vals.line_ids = [[5, 0, 0]].concat(line_ids);
                await this.orm.write("hospital.pharmacy.bill", [this.state.currentBillId], vals);
                this.state.lastBillId = this.state.currentBillId;
            } else {
                vals.line_ids = line_ids;
                let bill_id = await this.orm.create("hospital.pharmacy.bill", [vals]);
                this.state.lastBillId = bill_id[0];
                this.state.currentBillId = bill_id[0];
            }
            this.state.billState = 'held';
            this.notification.add("Bill Hold Successfully!", { type: "success" });
            this.state.showPaymentModal = false;
            this.clearBill();
        } catch(e) {
            this.notification.add("Error holding bill: " + e.message, { type: "danger" });
        }
    }

    startNewBill() {
        this.state.showPaymentModal = false;
        this.clearBill();
    }


    async clearBill() {
        if (this.state.currentBillId && this.state.billState === 'draft') {
            try { await this.orm.unlink("hospital.pharmacy.bill", [this.state.currentBillId]); } catch(e) {}
        }
        this.state.patient = null; this.state.patientSearchTerm = ""; this.state.medicines = [];
        this.state.paidAmount = 0; this.state.billDiscount = 0; this.state.invoiceNo = "Draft";
        this.state.currentBillId = false; this.state.billState = 'draft'; this.state.isReadOnly = false;
        this.calculateTotals();
    }
}


class PharmacyPurchase extends PharmacyBase {
    static template = "hospital_management.PharmacyPurchase";
    openDashboard() { this.goTo("hospital_management.action_hospital_pharmacy_dashboard_form"); }
    openBilling() { this.goTo("hospital_management.action_hospital_pharmacy_billing"); }
    openStock() { this.goTo("hospital_management.action_hospital_pharmacy_stock"); }
    openDetails() { this.goTo("hospital_management.action_hospital_pharmacy_details"); }
    closePOS() { this.goTo("hospital_management.action_hospital_pharmacy_bill_window"); }
}

class PharmacyStock extends PharmacyBase {
    static template = "hospital_management.PharmacyStock";
    openDashboard() { this.goTo("hospital_management.action_hospital_pharmacy_dashboard_form"); }
    openBilling() { this.goTo("hospital_management.action_hospital_pharmacy_billing"); }
    openPurchase() { this.goTo("hospital_management.action_hospital_pharmacy_purchase_list"); }
    openDetails() { this.goTo("hospital_management.action_hospital_pharmacy_details"); }
    closePOS() { this.goTo("hospital_management.action_hospital_pharmacy_bill_window"); }
}

class PharmacyDetails extends PharmacyBase {
    static template = "hospital_management.PharmacyDetails";
    openDashboard() { this.goTo("hospital_management.action_hospital_pharmacy_dashboard_form"); }
    openBilling() { this.goTo("hospital_management.action_hospital_pharmacy_billing"); }
    openPurchase() { this.goTo("hospital_management.action_hospital_pharmacy_purchase_list"); }
    openStock() { this.goTo("hospital_management.action_hospital_pharmacy_stock"); }
}

// REGISTER ALL PHARMACY CLIENT ACTIONS


registry.category("actions").add(
    "hospital_pharmacy_dashboard",
    PharmacyDashboard
);

registry.category("actions").add(
    "hospital_pharmacy_billing",
    PharmacyBilling
);

registry.category("actions").add(
    "hospital_pharmacy_purchase",
    PharmacyPurchase
);

registry.category("actions").add(
    "hospital_pharmacy_stock",
    PharmacyStock
);

registry.category("actions").add(
    "hospital_pharmacy_details",
    PharmacyDetails
);