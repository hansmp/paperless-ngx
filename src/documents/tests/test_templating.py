from django.test import TestCase
from jinja2 import Environment
from jinja2 import StrictUndefined
from jinja2 import TemplateSyntaxError
from jinja2 import UndefinedError

from documents import templating
from documents.models import Document
from documents.models import Tag


class TestTemplating(TestCase):
    ########## TEST GENERIC TEMPLATE RENDERING ##########

    def test_simple_generic_template(self):
        testString = "{{foo}}"
        testGlobals = {"foo": "SomeText"}
        jinjaRenderEnv = Environment(undefined=StrictUndefined)

        result = templating.loadTemplateWithJinja2(
            testString,
            jinjaRenderEnv,
            testGlobals,
        )
        self.assertEqual(result, "SomeText")
        return

    def test_generic_template_with_unset_var(self):
        testString = "{{foo}}"
        testGlobals = {"bar": "SomeText"}
        jinjaRenderEnv = Environment(undefined=StrictUndefined)

        with self.assertRaises(UndefinedError):
            templating.loadTemplateWithJinja2(
                testString,
                jinjaRenderEnv,
                testGlobals,
            )
        return

    def test_generic_template_with_syntax_error(self):
        testString = "{{foo"
        testGlobals = {"bar": "SomeText"}
        jinjaRenderEnv = Environment(undefined=StrictUndefined)

        with self.assertRaises(TemplateSyntaxError):
            templating.loadTemplateWithJinja2(
                testString,
                jinjaRenderEnv,
                testGlobals,
            )
        return

    ########## TEST TEMPLATE RENDERING ##########
    # NOTE: Not testing all identifiers here as test_file_handling already covering them!

    def test_rendering_with_valid_doc(self):
        doc = Document()
        doc.mime_type = "application/pdf"
        doc.storage_type = Document.STORAGE_TYPE_UNENCRYPTED
        doc.save()
        doc.title = "FooBar"

        tag = Tag.objects.create(name="t", pk=85)
        doc.tags.add(tag)

        testString = "{{title}}/{{tags[0]}}"

        rendered = templating.renderTemplate(testString, doc)

        self.assertEqual(rendered, "FooBar/t")
        return

    def test_rendering_without_doc(self):
        rendered = templating.renderTemplate("{{someText}}", None)
        self.assertIsNone(rendered)

        return

    def test_rendering_invalid_string(self):
        doc = Document()
        doc.mime_type = "application/pdf"
        doc.storage_type = Document.STORAGE_TYPE_UNENCRYPTED
        doc.save()

        testString = "{{title"
        renderedSyntaxError = templating.renderTemplate(testString, doc)
        self.assertIsNone(renderedSyntaxError)

        return

    def test_rendering_invalid_string_undef_var(self):
        doc = Document()
        doc.mime_type = "application/pdf"
        doc.storage_type = Document.STORAGE_TYPE_UNENCRYPTED
        doc.save()

        testString = "FooBar/{{NotExisting}}"
        renderedUnknownVar = templating.renderTemplate(testString, doc)
        self.assertIsNone(renderedUnknownVar)

        testString2 = "FooBar/{{NotExisting.Foo}}"
        renderedUnknownVar2 = templating.renderTemplate(testString2, doc)
        self.assertIsNone(renderedUnknownVar2)

        return

    def test_rendering_undef_var_with_handling(self):
        doc = Document()
        doc.mime_type = "application/pdf"
        doc.storage_type = Document.STORAGE_TYPE_UNENCRYPTED
        doc.save()

        testString = "FooBar/{{NotExisting | d('123')}}"
        rendered1 = templating.renderTemplate(testString, doc)
        self.assertEqual(rendered1, "FooBar/123")

        testString = "FooBar/{{(NotExisting | d('123') ).Test | d('456')}}"
        rendered2 = templating.renderTemplate(testString, doc)
        self.assertEqual(rendered2, "FooBar/456")

        testString = "FooBar/{{(title | d('123') ).Test | d('456')}}"
        rendered3 = templating.renderTemplate(testString, doc)
        self.assertEqual(rendered3, "FooBar/456")

        return

    ########## TEST TEMPLATE VALIDATION ##########

    def test_validate_valid_template(self):
        testString = "{{title}}{{tags['foo'] | d('NONE')}}"
        result = templating.validateTemplate(testString, False)

        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 0)
        self.assertNotEqual(result.preview, "")

        return

    def test_validate_unknown_vars(self):
        testString = "{{title}}{{UNKNOWN}}{{BAR}}"
        result = templating.validateTemplate(testString, False)

        self.assertEqual(len(result.errors), 2)
        self.assertEqual(len(result.warnings), 0)
        self.assertEqual(result.preview, "title")

        firstMatch = any("UNKNOWN" in ele for ele in result.errors)
        self.assertTrue(firstMatch)

        secondMatch = any("BAR" in ele for ele in result.errors)
        self.assertTrue(secondMatch)
        return

    def test_validate_empty_output(self):
        testString = ""
        result1 = templating.validateTemplate(testString, False)

        self.assertEqual(len(result1.errors), 1)
        self.assertEqual(len(result1.warnings), 0)

        result2 = templating.validateTemplate(testString, True)

        self.assertEqual(len(result2.errors), 0)
        self.assertEqual(len(result2.warnings), 0)
        return

    def test_validate_syntax_error(self):
        testString = "{{title"
        result = templating.validateTemplate(testString, False)

        self.assertEqual(len(result.errors), 1)
        self.assertEqual(len(result.warnings), 0)

        matchMsg = any("syntax error:" in ele.lower() for ele in result.errors)
        self.assertTrue(matchMsg)

        return
