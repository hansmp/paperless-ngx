import logging
from pathlib import PurePath

import pathvalidate
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.translation import gettext as _
from jinja2 import ChainableUndefined
from jinja2 import DebugUndefined
from jinja2 import Environment
from jinja2 import StrictUndefined
from jinja2 import TemplateSyntaxError
from jinja2 import UndefinedError
from jinja2.meta import find_undeclared_variables

from documents.models import Document
from documents.templating_helper import defaultdictNoStr
from documents.templating_helper import many_to_dictionary


###############################################################################
class DebugChainableUndefined(ChainableUndefined, DebugUndefined):
    pass


###############################################################################
class TemplatingValidationResult:
    debugString: str = "<NOT RENDERED>"
    preview: str = "<NOT RENDERED>"

    def __init__(self):
        self.warnings: list[str] = []
        self.errors: list[str] = []


###############################################################################
# Privates
logger = logging.getLogger("paperless.templating")
jinjaDebugEnv = Environment(undefined=DebugChainableUndefined)
jinjaRenderEnv = Environment(undefined=ChainableUndefined)
jinjaRenderEnvStrict = Environment(undefined=StrictUndefined)


###############################################################################
def createDummyGlobals():
    dummyGlobals = {
        "title": "title",
        "correspondent": "correspondent",
        "document_type": "document_type",
        "created": "created",
        "created_year": "created_year",
        "created_year_short": "created_year_short",
        "created_month": "created_month",
        "created_month_name": "created_month_name",
        "created_month_name_short": "created_month_name_short",
        "created_day": "created_day",
        "added": "added",
        "added_year": "added_year",
        "added_year_short": "added_year_short",
        "added_month": "added_month",
        "added_month_name": "added_month_name",
        "added_month_name_short": "added_month_name_short",
        "added_day": "added_day",
        "asn": "asn",
        "tags": "tags",
        "tag_list": "tag_list",
        "owner_username": "someone",
        "original_name": "testfile",
        "doc_pk": "doc_pk",
    }
    return dummyGlobals


###############################################################################
def createGlobals(
    doc: Document,
):
    tags = defaultdictNoStr(
        lambda: slugify(None),
        many_to_dictionary(doc.tags),
    )

    tag_list = pathvalidate.sanitize_filename(
        ",".join(
            sorted(tag.name for tag in doc.tags.all()),
        ),
        replacement_text="-",
    )

    no_value_default = "-none-"

    if doc.correspondent:
        correspondent = pathvalidate.sanitize_filename(
            doc.correspondent.name,
            replacement_text="-",
        )
    else:
        correspondent = no_value_default

    if doc.document_type:
        document_type = pathvalidate.sanitize_filename(
            doc.document_type.name,
            replacement_text="-",
        )
    else:
        document_type = no_value_default

    if doc.archive_serial_number:
        asn = str(doc.archive_serial_number)
    else:
        asn = no_value_default

    if doc.owner is not None:
        owner_username_str = str(doc.owner.username)
    else:
        owner_username_str = no_value_default

    if doc.original_filename is not None:
        # No extension
        original_name = PurePath(doc.original_filename).with_suffix("").name
    else:
        original_name = no_value_default

    # Convert UTC database datetime to localized date
    local_added = timezone.localdate(doc.added)
    local_created = timezone.localdate(doc.created)

    templateGlobals = {
        "title": pathvalidate.sanitize_filename(doc.title, replacement_text="-"),
        "correspondent": correspondent,
        "document_type": document_type,
        "created": local_created.isoformat(),
        "created_year": local_created.strftime("%Y"),
        "created_year_short": local_created.strftime("%y"),
        "created_month": local_created.strftime("%m"),
        "created_month_name": local_created.strftime("%B"),
        "created_month_name_short": local_created.strftime("%b"),
        "created_day": local_created.strftime("%d"),
        "added": local_added.isoformat(),
        "added_year": local_added.strftime("%Y"),
        "added_year_short": local_added.strftime("%y"),
        "added_month": local_added.strftime("%m"),
        "added_month_name": local_added.strftime("%B"),
        "added_month_name_short": local_added.strftime("%b"),
        "added_day": local_added.strftime("%d"),
        "asn": asn,
        "tags": tags,
        "tag_list": tag_list,
        "owner_username": owner_username_str,
        "original_name": original_name,
        "doc_pk": f"{doc.pk:07}",
    }
    return templateGlobals


###############################################################################
def validateTemplate(
    templatedString: str,
    allowEmptyOuptut: bool,
    removeNewLines: bool = False,
    documentForGlobals: Document = None,
):
    result = TemplatingValidationResult()
    try:
        validationGlobals = (
            createDummyGlobals()
            if documentForGlobals is None
            else createGlobals(documentForGlobals)
        )

        resolvedStringWithDebug = loadTemplateWithJinja2(
            templatedString,
            jinjaDebugEnv,
            validationGlobals,
            removeNewLines,
        )
        result.debugString = resolvedStringWithDebug

        ast = jinjaDebugEnv.parse(resolvedStringWithDebug)
        undef = find_undeclared_variables(ast)

        if undef:
            logger.debug(
                f"Undeclared variables in template found. template: '{templatedString}' / undefined Variables: {undef!r}",
            )
            for var in undef:
                result.errors.append(_(f"Undefined variable: {var}"))

        resolvedString = loadTemplateWithJinja2(
            templatedString,
            jinjaRenderEnv,
            validationGlobals,
            removeNewLines,
        )
        result.preview = resolvedString

        if not allowEmptyOuptut and not resolvedString and not resolvedString.isspace():
            result.errors.append(_("Template results in empty string!"))

    except UndefinedError as err:
        result.errors.append(_(f"Exception: {err}"))

    except TemplateSyntaxError as err:
        result.errors.append(_(f"Syntax error: {err}"))

    return result


###############################################################################
def renderTemplate(
    templatedString: str,
    doc: Document,
    removeNewLines: bool = False,
):
    if doc is None:
        logger.error("Can't render template without document!")
        return None
    try:
        globals = createGlobals(doc)
        resolvedString = loadTemplateWithJinja2(
            templatedString,
            jinjaRenderEnvStrict,
            globals,
            removeNewLines,
        )

    except Exception as err:
        logger.error(f"Failed to render template: '{templatedString}' : {err}")
        return None

    return resolvedString


###############################################################################
def loadTemplateWithJinja2(
    templatedString: str,
    usedEnv: Environment,
    globals: dict,
    removeNewLines: bool = False,
):
    try:
        template = usedEnv.from_string(templatedString, globals)
        resolvedString = template.render()

        if removeNewLines:
            resolvedString = resolvedString.replace("\n", "")

        logger.debug("Rendered string: %s", resolvedString)
        return resolvedString

    except Exception as e:
        logger.info("Error rendering jinja template: %s", e)
        raise e

    return None
