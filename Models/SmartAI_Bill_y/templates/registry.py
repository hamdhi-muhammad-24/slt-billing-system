from templates.nonvat_home.renderer import NonVATHomeRenderer
from templates.nonvat_home.parser import parse_nonvat_home

from templates.nonvat_enterprise.renderer import NonVATEnterpriseRenderer
from templates.nonvat_enterprise.parser import parse_nonvat_enterprise

from templates.product_label_grouping.renderer import ProductLabelGroupingRenderer
from templates.product_label_grouping.parser import parse_product_label_grouping

from templates.subscription_ref_grouping.renderer import SubscriptionRefGroupingRenderer
from templates.subscription_ref_grouping.parser import parse_subscription_ref_grouping

from templates.summary_statement.renderer import SummaryStatementRenderer
from templates.summary_statement.parser import parse_summary_statement

from templates.invoice_of_summary.renderer import InvoiceOfSummaryRenderer
from templates.invoice_of_summary.parser import parse_invoice_of_summary


TEMPLATE_REGISTRY = {
    "nonvat_home": {
        "name": "NonVAT Home Invoice",
        "description": "Sheet 19 - Non-VAT, Home customer",
        "renderer": NonVATHomeRenderer,
        "parser": parse_nonvat_home,
        "ready": True,
    },
    "nonvat_enterprise": {
        "name": "NonVAT Enterprise Invoice",
        "description": "Sheet 19 - Non-VAT, Enterprise customer",
        "renderer": NonVATEnterpriseRenderer,
        "parser": parse_nonvat_enterprise,
        "ready": True,
    },
    "product_label_grouping": {
        "name": "Product Label Level Grouping",
        "description": "Sheet 22 - BILLSTYLE=19",
        "renderer": ProductLabelGroupingRenderer,
        "parser": parse_product_label_grouping,
        "ready": True,
    },
    "subscription_ref_grouping": {
        "name": "Subscription Ref Level Grouping",
        "description": "Sheet 23 - BILLSTYLE=20",
        "renderer": SubscriptionRefGroupingRenderer,
        "parser": parse_subscription_ref_grouping,
        "ready": True,
    },
    "summary_statement": {
        "name": "Summary Statement",
        "description": "Sheet 7 - DOCTYPE=SUMMARYSTATEMENT",
        "renderer": SummaryStatementRenderer,
        "parser": parse_summary_statement,
        "ready": True,
    },
    "invoice_of_summary": {
        "name": "Invoice of Summary",
        "description": "BILLSTYLE=18 - PLACEHOLDER (GMF labels TBD)",
        "renderer": InvoiceOfSummaryRenderer,
        "parser": parse_invoice_of_summary,
        "ready": False,
    },
}


def get_template_info(template_id):
    return TEMPLATE_REGISTRY.get(template_id)


def get_renderer(template_id):
    info = TEMPLATE_REGISTRY.get(template_id)
    if not info:
        raise ValueError(f"Unknown template: {template_id}")
    return info["renderer"]


def get_parser(template_id):
    info = TEMPLATE_REGISTRY.get(template_id)
    if not info:
        raise ValueError(f"Unknown template: {template_id}")
    return info["parser"]


def list_templates(only_ready=False):
    templates = []
    for tid, info in TEMPLATE_REGISTRY.items():
        if only_ready and not info.get("ready", False):
            continue
        templates.append({
            "id": tid,
            "name": info["name"],
            "description": info["description"],
            "ready": info.get("ready", False),
        })
    return templates