from openerp.osv import fields, osv
from openerp import api, models
from openerp.tools.translate import _

class custom_invoice(models.Model):
    _name = "account.invoice"
    _inherit = "account.invoice"

    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
            payment_term=False, partner_bank_id=False, company_id=False):
	res = super(custom_invoice, self).onchange_partner_id(type=type, partner_id=partner_id, date_invoice=date_invoice, payment_term=payment_term, partner_bank_id=partner_bank_id, company_id=company_id)

	pricelist = False

	if partner_id:
            p = self.env['res.partner'].browse(partner_id)
            pricelist = p.property_product_pricelist and p.property_product_pricelist.id or False

	if pricelist:
	    res['value'].update({'pricelist_id': pricelist})

	return res


    def onchange_pricelist_id(self, cr, uid, ids, pricelist_id, invoice_lines, context=None):
        context = context or {}

        if not pricelist_id:
            return {}
        value = {
            'currency_id': self.pool.get('product.pricelist').browse(cr, uid, pricelist_id, context=context).currency_id.id
        }
        if not invoice_lines or invoice_lines == [(6, 0, [])]:
            return {'value': value}
        warning = {
            'title': _('Pricelist Warning!'),
            'message' : _('If you change the pricelist of this order (and eventually the currency), prices of existing order lines will not be updated.')
        }
        return {'warning': warning, 'value': value}


    _columns = {
        'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Pricelist for current customer invoice."),
    }


class custom_invoice_line(models.Model):
    _name = "account.invoice.line"
    _inherit = "account.invoice.line"


    @api.multi
    def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice',
            partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
            company_id=None):

	res = super(custom_invoice_line, self).product_id_change(product=product, uom_id=uom_id, qty=qty, name=name, type=type, partner_id=partner_id, fposition_id=fposition_id, price_unit=price_unit, currency_id=currency_id, company_id=company_id)

	warning_msgs = ''
	context = self._context

	pricelist = context.get('pricelist_id')
        if not pricelist:
            warn_msg = _('You have to select a pricelist or a customer in the sales form !\n'
                    'Please set one before choosing a product.')
            warning_msgs += _("No Pricelist ! : ") + warn_msg +"\n\n"
        else:
            price = self.pool.get('product.pricelist').price_get(self._cr, self._uid, [pricelist],
                    product, qty or 1.0, partner_id)[pricelist]


            if price is False:
                warn_msg = _("Cannot find a pricelist line matching this product and quantity.\n"
                        "You have to change either the product, the quantity or the pricelist.")

                warning_msgs += _("No valid pricelist line found ! :") + warn_msg +"\n\n"
            else:
		res.get('value').update({'price_unit': price})
                #result.update({'price_unit': price})
        if warning_msgs:
            warning = {
                       'title': _('Configuration Error!'),
                       'message' : warning_msgs
		    }

	return res


class account_journal(models.Model):
    _name = "account.journal"
    _inherit = "account.journal"

    def write(self, cr, uid, ids, vals, context=None):
	res = super(account_journal, self).write(cr, uid, ids, vals, context=context)

	if 'code' in vals:
	    prefix = vals['code'].upper()
	    seq = {'prefix': prefix + "/%(year)s/"}
	    seq_obj = self.browse(cr, uid, ids, context).sequence_id
	    seq_obj.update(seq)

	return res
