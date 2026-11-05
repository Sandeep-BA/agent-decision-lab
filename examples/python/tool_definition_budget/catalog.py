"""A synthetic help-desk tool catalog for Belgavi's Book Store. Author: Sandeep Belgavi.

Each tool has a concise description and a verbose one (the kind that grows after a few incidents:
examples, caveats, field-by-field notes). Schemas are JSON Schema objects in the shape most
providers accept: name, description, and an input schema."""

S = lambda **p: {'type': 'string', **p}
I = lambda **p: {'type': 'integer', **p}
ORDER = S(description='Order id, for example BK-40101', pattern='^BK-[0-9]{5}$')
CASE = S(description='Help-desk case id, for example CASE-4101', pattern='^CASE-[0-9]{4}$')

SPECS = [
 ('get_order', 'Look up one order by id.', {'order_id': ORDER}, ['order_id']),
 ('list_orders', 'List a customer\'s recent orders, newest first.', {'customer_id': S(description='Customer id'), 'limit': I(minimum=1, maximum=50)}, ['customer_id']),
 ('get_shipment', 'Get carrier tracking events for an order.', {'order_id': ORDER}, ['order_id']),
 ('create_return', 'Open a return for items in a delivered order.', {'order_id': ORDER, 'lines': {'type': 'array', 'items': {'type': 'object', 'properties': {'sku': S(), 'quantity': I(minimum=1)}, 'required': ['sku', 'quantity']}}, 'reason': S(enum=['damaged', 'wrong_item', 'not_needed', 'late'])}, ['order_id', 'lines', 'reason']),
 ('get_return', 'Get the status of a return.', {'return_id': S(pattern='^RET-[0-9]{3,6}$')}, ['return_id']),
 ('issue_refund', 'Refund a delivered order or part of it to the original payment method.', {'order_id': ORDER, 'amount_inr': {'type': 'number', 'minimum': 1}, 'case_id': CASE}, ['order_id', 'amount_inr', 'case_id']),
 ('grant_store_credit', 'Grant goodwill store credit within the monthly limit.', {'customer_id': S(), 'amount_inr': {'type': 'number', 'minimum': 1, 'maximum': 2000}, 'case_id': CASE}, ['customer_id', 'amount_inr', 'case_id']),
 ('search_catalog', 'Search books by title, author or ISBN.', {'query': S(), 'in_stock_only': {'type': 'boolean'}}, ['query']),
 ('get_stock', 'Get stock by warehouse for one ISBN.', {'isbn': S(pattern='^97[89][0-9]{10}$')}, ['isbn']),
 ('reserve_copy', 'Hold one copy of a book for a customer for 48 hours.', {'isbn': S(), 'customer_id': S()}, ['isbn', 'customer_id']),
 ('update_address', 'Change the delivery address of an order that has not shipped.', {'order_id': ORDER, 'address': {'type': 'object', 'properties': {'line1': S(), 'line2': S(), 'city': S(), 'pin': S(pattern='^[0-9]{6}$')}, 'required': ['line1', 'city', 'pin']}}, ['order_id', 'address']),
 ('cancel_order', 'Cancel an order that has not shipped.', {'order_id': ORDER, 'case_id': CASE}, ['order_id', 'case_id']),
 ('get_customer', 'Get a customer profile and loyalty tier.', {'customer_id': S()}, ['customer_id']),
 ('add_case_note', 'Add an internal note to a help-desk case.', {'case_id': CASE, 'note': S(maxLength=2000)}, ['case_id', 'note']),
 ('escalate_case', 'Hand a case to a person with a reason.', {'case_id': CASE, 'queue': S(enum=['payments', 'warehouse', 'supervisor']), 'reason': S()}, ['case_id', 'queue', 'reason']),
 ('check_gift_card', 'Check the balance of a gift card.', {'card_number': S(pattern='^[0-9]{16}$')}, ['card_number']),
]

VERBOSE_TAIL = (' Use this tool only when the customer has given enough detail to identify the record; if not, ask a'
                ' short question first. The tool returns a JSON object; fields that are unknown are null, not missing.'
                ' Errors come back as {"error": code, "message": text}; retry only when code is "unavailable".'
                ' Do not call it more than once for the same arguments in one conversation. Example: a customer'
                ' writes "where is my order BK-40101?"; call it with that id and summarise the result in one sentence.')


def tools(style='concise'):
    out = []
    for name, desc, props, required in SPECS:
        props = {k: dict(v) for k, v in props.items()}
        if style == 'verbose':
            desc = desc + VERBOSE_TAIL
            for key, value in props.items():
                value.setdefault('description', key.replace('_', ' ').capitalize() + '. Required format is enforced by the server.')
        out.append({'name': name, 'description': desc,
                    'input_schema': {'type': 'object', 'properties': props, 'required': required, 'additionalProperties': False}})
    return out
