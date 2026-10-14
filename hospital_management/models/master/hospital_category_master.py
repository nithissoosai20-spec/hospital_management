from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HospitalCategoryMaster(models.Model):
    _name = 'hospital.category.master'
    _description = 'Master Category Configuration'
    _order = 'parent_id, name'

    name = fields.Char(string='Category Name', required=False)
    category_type = fields.Selection([
        ('item_primary_category', 'Primary Category'),
        ('pharmacy_item_category', 'Category (Packaging)'),
        ('lab_category', 'Lab Category'),
        ('asset_category', 'Asset Category'),
    ], string='Module / Type', default='item_primary_category', required=True)

    category_level = fields.Selection([
        ('primary', 'Primary Category (Department)'),
        ('secondary', 'Secondary Category (Group)'),
        ('item', 'Item Category (Classification)'),
    ], string='Category Level', compute='_compute_category_level', store=True)

    parent_id = fields.Many2one('hospital.category.master', string='Parent Category', ondelete='cascade', index=True)
    child_ids = fields.One2many('hospital.category.master', 'parent_id', string='Sub Categories')
    primary_parent_id = fields.Many2one('hospital.category.master', string='Primary Category', compute='_compute_primary_parent', store=True, index=True)
    item_category_ids = fields.Many2many('hospital.category.master', compute='_compute_item_category_ids', string='Item Categories')
    active = fields.Boolean(default=True)

    # Cascading Dropdown Fields on Form View
    selected_primary_id = fields.Many2one(
        'hospital.category.master',
        string='Primary Category',
        domain="[('parent_id', '=', False), ('category_type', 'not in', ['lab_category', 'pharmacy_item_category'])]",
        compute='_compute_selected_categories',
        store=True,
        readonly=False,
    )

    selected_secondary_id = fields.Many2one(
        'hospital.category.master',
        string='Secondary Category',
        domain="[('parent_id', '=', selected_primary_id), ('parent_id', '!=', False)]",
        compute='_compute_selected_categories',
        store=True,
        readonly=False,
    )

    selected_item_id = fields.Many2one(
        'hospital.category.master',
        string='Item Category',
        domain="[('parent_id', '=', selected_secondary_id), ('parent_id', '!=', False)]",
        compute='_compute_selected_categories',
        store=True,
        readonly=False,
    )

    _sql_constraints = [
        ('name_parent_uniq', 'unique (name, parent_id)', 'Category name must be unique within the same parent category!')
    ]

    @api.constrains('name', 'parent_id')
    def _check_unique_name(self):
        if self.env.context.get('install_mode'):
            return
        for rec in self:
            if rec.name:
                domain = [
                    ('name', '=ilike', rec.name.strip()),
                    ('id', '!=', rec.id),
                    ('parent_id', '=', rec.parent_id.id if rec.parent_id else False)
                ]
                if self.search(domain, limit=1):
                    raise ValidationError(f"A category named '{rec.name.strip()}' already exists under this parent!")

    @api.depends('parent_id')
    def _compute_category_level(self):
        for rec in self:
            if not rec.parent_id:
                rec.category_level = 'primary'
            elif not rec.parent_id.parent_id:
                rec.category_level = 'secondary'
            else:
                rec.category_level = 'item'

    @api.depends('parent_id', 'parent_id.parent_id')
    def _compute_primary_parent(self):
        for rec in self:
            if rec.parent_id and rec.parent_id.parent_id:
                rec.primary_parent_id = rec.parent_id.parent_id
            elif rec.parent_id:
                rec.primary_parent_id = rec.parent_id
            else:
                rec.primary_parent_id = False

    def _compute_item_category_ids(self):
        for rec in self:
            if rec.category_level == 'primary':
                rec.item_category_ids = self.search([('parent_id.parent_id', '=', rec.id)])
            elif rec.category_level == 'secondary':
                rec.item_category_ids = rec.child_ids
            else:
                rec.item_category_ids = False

    @api.depends('parent_id', 'parent_id.parent_id')
    def _compute_selected_categories(self):
        for rec in self:
            if not rec.parent_id:
                rec.selected_primary_id = rec.id if isinstance(rec.id, int) else False
                rec.selected_secondary_id = False
                rec.selected_item_id = False
            elif not rec.parent_id.parent_id:
                rec.selected_primary_id = rec.parent_id
                rec.selected_secondary_id = rec.id if isinstance(rec.id, int) else False
                rec.selected_item_id = False
            else:
                rec.selected_primary_id = rec.parent_id.parent_id
                rec.selected_secondary_id = rec.parent_id
                rec.selected_item_id = rec.id if isinstance(rec.id, int) else False

    @api.onchange('selected_primary_id')
    def _onchange_selected_primary_id(self):
        if self.selected_secondary_id and self.selected_secondary_id.parent_id != self.selected_primary_id:
            self.selected_secondary_id = False
            self.selected_item_id = False
        if self.category_type == 'item_primary_category':
            if not self.parent_id:
                if self.selected_primary_id:
                    self.name = self.selected_primary_id.name

    @api.onchange('selected_secondary_id')
    def _onchange_selected_secondary_id(self):
        if self.selected_item_id and self.selected_item_id.parent_id != self.selected_secondary_id:
            self.selected_item_id = False
        if self.category_type == 'item_primary_category':
            if self.selected_secondary_id:
                self.name = self.selected_secondary_id.name

    @api.onchange('selected_item_id')
    def _onchange_selected_item_id(self):
        if self.category_type == 'item_primary_category':
            if self.selected_item_id:
                self.name = self.selected_item_id.name

    @api.onchange('category_type')
    def _onchange_category_type(self):
        if self.category_type != 'item_primary_category':
            self.parent_id = False
            self.selected_primary_id = False
            self.selected_secondary_id = False
            self.selected_item_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            cat_type = vals.get('category_type', 'item_primary_category')
            if cat_type == 'item_primary_category':
                if self.env.context.get('is_secondary_create'):
                    if vals.get('selected_primary_id'):
                        vals['parent_id'] = vals['selected_primary_id']
                    elif self.env.context.get('default_parent_id'):
                        vals['parent_id'] = self.env.context.get('default_parent_id')
                elif self.env.context.get('is_item_create'):
                    if vals.get('selected_secondary_id'):
                        vals['parent_id'] = vals['selected_secondary_id']
                    elif self.env.context.get('default_parent_id'):
                        vals['parent_id'] = self.env.context.get('default_parent_id')
                elif self.env.context.get('is_primary_create'):
                    vals['parent_id'] = False
                else:
                    if not vals.get('name'):
                        if vals.get('selected_item_id'):
                            vals['parent_id'] = vals.get('selected_secondary_id')
                            vals['name'] = self.browse(vals['selected_item_id']).name
                        elif vals.get('selected_secondary_id'):
                            vals['parent_id'] = vals.get('selected_primary_id')
                            vals['name'] = self.browse(vals['selected_secondary_id']).name
                        elif vals.get('selected_primary_id'):
                            vals['parent_id'] = False
                            vals['name'] = self.browse(vals['selected_primary_id']).name

            # Fallback if name is still empty
            if not vals.get('name'):
                vals['name'] = 'New Category'
            if not vals.get('category_type'):
                vals['category_type'] = 'item_primary_category'
        return super().create(vals_list)

    def write(self, vals):
        for rec in self:
            cat_type = vals.get('category_type', rec.category_type)
            if cat_type == 'item_primary_category':
                if not vals.get('name'):
                    if 'selected_item_id' in vals and vals['selected_item_id']:
                        vals['name'] = self.browse(vals['selected_item_id']).name
                        if 'selected_secondary_id' in vals:
                            vals['parent_id'] = vals.get('selected_secondary_id')
                    elif 'selected_secondary_id' in vals and vals['selected_secondary_id']:
                        vals['name'] = self.browse(vals['selected_secondary_id']).name
                        if 'selected_primary_id' in vals:
                            vals['parent_id'] = vals.get('selected_primary_id')
                    elif 'selected_primary_id' in vals and vals['selected_primary_id']:
                        vals['name'] = self.browse(vals['selected_primary_id']).name
                        vals['parent_id'] = False
        return super().write(vals)

    pharmacy_category_type = fields.Selection([
        ('item_primary_category', 'Primary Category'),
        ('pharmacy_item_category', 'Category (Packaging)')
    ], string='Module / Type', compute='_compute_pharmacy_type', inverse='_inverse_pharmacy_type')

    @api.depends('category_type')
    def _compute_pharmacy_type(self):
        for rec in self:
            if rec.category_type in ['item_primary_category', 'pharmacy_item_category']:
                rec.pharmacy_category_type = rec.category_type
            else:
                rec.pharmacy_category_type = False

    def _inverse_pharmacy_type(self):
        for rec in self:
            if rec.pharmacy_category_type:
                rec.category_type = rec.pharmacy_category_type

    # 3 Action Buttons for Bottom-Right Corner
    def action_clear(self):
        for rec in self:
            rec.selected_primary_id = False
            rec.selected_secondary_id = False
            rec.selected_item_id = False
            rec.name = False

    def action_close(self):
        return self.env.ref('hospital_management.action_hospital_category_master').sudo().read()[0]

    def action_save(self):
        self.ensure_one()
        if not self.name:
            if self.selected_item_id:
                self.name = self.selected_item_id.name
            elif self.selected_secondary_id:
                self.name = self.selected_secondary_id.name
            elif self.selected_primary_id:
                self.name = self.selected_primary_id.name
            else:
                raise ValidationError("Please select or type a Category before saving!")

        action = self.env.ref('hospital_management.action_hospital_category_master').sudo().read()[0]
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Category saved successfully!',
                'type': 'success',
                'sticky': False,
                'next': action,
            }
        }
