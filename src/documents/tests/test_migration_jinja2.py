from documents.tests.utils import TestMigrations


class TestMigrateStoragePathsToJinja2_Upgrade(TestMigrations):
    migrate_from = "1052_document_transaction_id"
    migrate_to = "1053_introduce_jinja2_templates"

    def setUpBeforeMigration(self, apps):
        self.storagePaths = apps.get_model("documents", "StoragePath")
        self.storagePaths.objects.create(
            name="Path1",
            path="{title}/{ created_year}",
        )
        self.storagePaths.objects.create(
            name="Path2",
            path="{{title2}}/{{created_year }}",
        )
        self.storagePaths.objects.create(
            name="Path3",
            path="Nothing/To/Do",
        )
        self.storagePaths.objects.create(
            name="Path4",
            path="{{ title | d('Foo') }}/{{ created_year | d('test') }}",
        )
        self.storagePaths.objects.create(
            name="Path5",
            path="{title}/{tags[type]}/{tags[0]}/{ AlreadyDone['type'] }/Nonsense[foo]",
        )

    def test_simple_storage_path_upgrade(self):
        storagePath = self.storagePaths.objects.get(name="Path1")
        self.assertEqual(storagePath.path, "{{ title }}/{{ created_year }}")

    def test_already_upgraded_path(self):
        storagePath = self.storagePaths.objects.get(name="Path2")
        self.assertEqual(storagePath.path, "{{title2}}/{{created_year }}")

    def test_path_no_placeholders(self):
        storagePath = self.storagePaths.objects.get(name="Path3")
        self.assertEqual(storagePath.path, "Nothing/To/Do")

    def test_complex_jinja_untouched(self):
        storagePath = self.storagePaths.objects.get(name="Path4")
        self.assertEqual(
            storagePath.path,
            "{{ title | d('Foo') }}/{{ created_year | d('test') }}",
        )

    def test_array_access_upgraded(self):
        storagePath = self.storagePaths.objects.get(name="Path5")
        self.assertEqual(
            storagePath.path,
            "{{ title }}/{{ tags['type'] }}/{{ tags[0] }}/{{ AlreadyDone['type'] }}/Nonsense[foo]",
        )


class TestMigrateStoragePathsFromJinja2_Downgrade(TestMigrations):
    migrate_from = "1053_introduce_jinja2_templates"
    migrate_to = "1052_document_transaction_id"

    def setUpBeforeMigration(self, apps):
        self.storagePaths = apps.get_model("documents", "StoragePath")
        self.storagePaths.objects.create(
            name="Path1",
            path="{title}/{ created_year}",
        )
        self.storagePaths.objects.create(
            name="Path2",
            path="{{title2}}/{{created_year }}",
        )
        self.storagePaths.objects.create(
            name="Path3",
            path="Nothing/To/Do",
        )
        self.storagePaths.objects.create(
            name="Path4",
            path="{{ title | d('Foo') }}/{{ created_year | d('test') }}",
        )
        self.storagePaths.objects.create(
            name="Path5",
            path="{{ title }}/{{ tags['type' ] }}/{{ tags[1] }}/{ AlreadyDone[type] }/Nonsense[foo]",
        )

    def test_simple_storage_path_upgrade(self):
        storagePath = self.storagePaths.objects.get(name="Path2")
        self.assertEqual(storagePath.path, "{title2}/{created_year}")

    def test_already_downgraded_path(self):
        storagePath = self.storagePaths.objects.get(name="Path1")
        self.assertEqual(storagePath.path, "{title}/{ created_year}")

    def test_path_no_placeholders(self):
        storagePath = self.storagePaths.objects.get(name="Path3")
        self.assertEqual(storagePath.path, "Nothing/To/Do")

    def test_complex_jinja(self):
        storagePath = self.storagePaths.objects.get(name="Path4")
        self.assertEqual(
            storagePath.path,
            "{title | d('Foo')}/{created_year | d('test')}",
        )

    def test_array_access_downgraded(self):
        storagePath = self.storagePaths.objects.get(name="Path5")
        self.assertEqual(
            storagePath.path,
            "{title}/{tags[type]}/{tags[1]}/{ AlreadyDone[type] }/Nonsense[foo]",
        )
