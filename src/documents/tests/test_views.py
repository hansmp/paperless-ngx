import json
import os
import tempfile
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from documents.models import Document
from documents.models import ShareLink
from documents.tests.utils import DirectoriesMixin


class TestViews(DirectoriesMixin, TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user("testuser")
        super().setUp()

    def test_login_redirect(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, "/accounts/login/?next=/")

    def test_index(self):
        self.client.force_login(self.user)
        for language_given, language_actual in [
            ("", "en-US"),
            ("en-US", "en-US"),
            ("de", "de-DE"),
            ("en", "en-US"),
            ("en-us", "en-US"),
            ("fr", "fr-FR"),
            ("jp", "en-US"),
        ]:
            if language_given:
                self.client.cookies.load(
                    {settings.LANGUAGE_COOKIE_NAME: language_given},
                )
            elif settings.LANGUAGE_COOKIE_NAME in self.client.cookies:
                self.client.cookies.pop(settings.LANGUAGE_COOKIE_NAME)

            response = self.client.get(
                "/",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                response.context_data["webmanifest"],
                f"frontend/{language_actual}/manifest.webmanifest",
            )
            self.assertEqual(
                response.context_data["styles_css"],
                f"frontend/{language_actual}/styles.css",
            )
            self.assertEqual(
                response.context_data["runtime_js"],
                f"frontend/{language_actual}/runtime.js",
            )
            self.assertEqual(
                response.context_data["polyfills_js"],
                f"frontend/{language_actual}/polyfills.js",
            )
            self.assertEqual(
                response.context_data["main_js"],
                f"frontend/{language_actual}/main.js",
            )

    def test_share_link_views(self):
        """
        GIVEN:
            - Share link created
        WHEN:
            - Valid request for share link is made
            - Invalid request for share link is made
            - Request for expired share link is made
        THEN:
            - Document is returned without need for login
            - User is redirected to login with error
            - User is redirected to login with error
        """

        _, filename = tempfile.mkstemp(dir=self.dirs.originals_dir)

        content = b"This is a test"

        with open(filename, "wb") as f:
            f.write(content)

        doc = Document.objects.create(
            title="none",
            filename=os.path.basename(filename),
            mime_type="application/pdf",
        )

        sharelink_permissions = Permission.objects.filter(
            codename__contains="sharelink",
        )
        self.user.user_permissions.add(*sharelink_permissions)
        self.user.save()

        self.client.force_login(self.user)

        self.client.post(
            "/api/share_links/",
            {
                "document": doc.pk,
                "file_version": "original",
            },
        )
        sl1 = ShareLink.objects.get(document=doc)

        self.client.logout()

        # Valid
        response = self.client.get(f"/share/{sl1.slug}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content, content)

        # Invalid
        response = self.client.get("/share/123notaslug", follow=True)
        response.render()
        self.assertEqual(response.request["PATH_INFO"], "/accounts/login/")
        self.assertContains(response, b"Share link was not found")

        # Expired
        sl1.expiration = timezone.now() - timedelta(days=1)
        sl1.save()

        response = self.client.get(f"/share/{sl1.slug}", follow=True)
        response.render()
        self.assertEqual(response.request["PATH_INFO"], "/accounts/login/")
        self.assertContains(response, b"Share link has expired")


class TestTemplatingPreviewView(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_superuser("testuser")
        self.doc = Document.objects.create()
        self.doc.title = "TestTitle"
        self.doc.save()
        super().setUp()

    def test_lists_all_docs_for_preview(self):
        self.client.force_login(self.user)
        response = self.client.get("/api/templating_preview/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resultJson = json.loads(response.content)
        self.assertEqual(len(resultJson["DocsForPreview"]), 1)
        self.assertEqual(resultJson["DocsForPreview"][0][1], self.doc.title)

    def test_preview_with_no_doc(self):
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/templating_preview/",
            {"template": "{{title}}"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resultJson = json.loads(response.content)
        self.assertEqual(resultJson["result"], "OK")
        self.assertEqual(resultJson["preview"], "title")
        self.assertEqual(len(resultJson["errors"]), 0)
        self.assertEqual(len(resultJson["warnings"]), 0)

    def test_preview_with_no_doc_newlines(self):
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/templating_preview/",
            {"template": "{{title}}\nBar"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resultJson = json.loads(response.content)
        self.assertEqual(resultJson["result"], "OK")
        self.assertEqual(resultJson["preview"], "title\nBar")
        self.assertEqual(len(resultJson["errors"]), 0)
        self.assertEqual(len(resultJson["warnings"]), 0)

        response2 = self.client.post(
            "/api/templating_preview/",
            {"template": "{{title}}\nBar", "remove_new_lines": "true"},
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        resultJson2 = json.loads(response2.content)
        self.assertEqual(resultJson2["result"], "OK")
        self.assertEqual(resultJson2["preview"], "titleBar")
        self.assertEqual(len(resultJson2["errors"]), 0)
        self.assertEqual(len(resultJson2["warnings"]), 0)

    def test_preview_with_valid_doc(self):
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/templating_preview/",
            {"template": "{{title}}", "doc_id": 1},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resultJson = json.loads(response.content)
        self.assertEqual(resultJson["result"], "OK")
        self.assertEqual(resultJson["preview"], f"{self.doc.title}")
        self.assertEqual(len(resultJson["errors"]), 0)
        self.assertEqual(len(resultJson["warnings"]), 0)

    def test_preview_with_invalid_doc(self):
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/templating_preview/",
            {"template": "{{title}}", "doc_id": 99},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.content,
            b'{"detail":"Document (id=99) for preview does not exists!"}',
        )

    def test_preview_with_invalid_template(self):
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/templating_preview/",
            {"template": "{{title", "doc_id": 1},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resultJson = json.loads(response.content)
        self.assertEqual(len(resultJson["errors"]), 1)
        self.assertEqual(len(resultJson["warnings"]), 0)
        self.assertEqual(resultJson["result"], "OK")
        self.assertEqual(resultJson["preview"], "<NOT RENDERED>")
        self.assertTrue(resultJson["errors"][0].startswith("Syntax error:"))

    def test_preview_with_missing_template(self):
        self.client.force_login(self.user)
        response = self.client.post("/api/templating_preview/", {"doc_id": 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content, b'{"template":["This field is required."]}')
