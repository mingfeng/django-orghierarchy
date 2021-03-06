from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission
from django.test import TestCase, RequestFactory

from django_orghierarchy.admin import AffiliatedOrganizationInline, OrganizationAdmin, SubOrganizationInline
from django_orghierarchy.forms import OrganizationForm
from django_orghierarchy.models import DataSource, Organization
from .factories import OrganizationClassFactory, OrganizationFactory
from .utils import clear_user_perm_cache, make_admin


class TestDataSourceAdmin(TestCase):

    def test_data_source_admin_is_registered(self):
        is_registered = admin.site.is_registered(DataSource)
        self.assertTrue(is_registered)


class TestSubOrganizationInline(TestCase):

    def setUp(self):
        self.admin = make_admin()
        self.site = AdminSite()
        self.factory = RequestFactory()

        self.normal_org = OrganizationFactory(internal_type=Organization.NORMAL)
        self.affiliated_org = OrganizationFactory(internal_type=Organization.AFFILIATED)

    def test_get_queryset(self):
        sub_org_inline = SubOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        qs = sub_org_inline.get_queryset(request)
        self.assertQuerysetEqual(qs, [repr(self.normal_org)])


class TestAffiliatedOrganizationInline(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.normal_admin = make_admin(username='normal_admin', is_superuser=False)

        self.site = AdminSite()
        self.factory = RequestFactory()

        self.normal_org = OrganizationFactory(internal_type=Organization.NORMAL)
        self.affiliated_org = OrganizationFactory(internal_type=Organization.AFFILIATED)

    def test_get_queryset(self):
        aff_org_inline = AffiliatedOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        qs = aff_org_inline.get_queryset(request)
        self.assertQuerysetEqual(qs, [repr(self.affiliated_org)])

    def test_has_add_permission(self):
        aff_org_inline = AffiliatedOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.normal_admin

        has_perm = aff_org_inline.has_add_permission(request)
        self.assertFalse(has_perm)

        clear_user_perm_cache(self.normal_admin)
        perm = Permission.objects.get(codename='add_affiliated_organization')
        self.normal_admin.user_permissions.add(perm)

        has_perm = aff_org_inline.has_add_permission(request)
        self.assertTrue(has_perm)

    def test_has_change_permission(self):
        aff_org_inline = AffiliatedOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.normal_admin

        has_perm = aff_org_inline.has_change_permission(request)
        self.assertFalse(has_perm)

        clear_user_perm_cache(self.normal_admin)
        perm = Permission.objects.get(codename='change_affiliated_organization')
        self.normal_admin.user_permissions.add(perm)

        has_perm = aff_org_inline.has_change_permission(request)
        self.assertTrue(has_perm)

    def test_has_delete_permission(self):
        aff_org_inline = AffiliatedOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.normal_admin

        has_perm = aff_org_inline.has_delete_permission(request)
        self.assertFalse(has_perm)

        clear_user_perm_cache(self.normal_admin)
        perm = Permission.objects.get(codename='delete_affiliated_organization')
        self.normal_admin.user_permissions.add(perm)

        has_perm = aff_org_inline.has_delete_permission(request)
        self.assertTrue(has_perm)


class TestOrganizationAdmin(TestCase):

    def setUp(self):
        self.admin = make_admin()
        self.site = AdminSite()
        self.factory = RequestFactory()

        self.organization = OrganizationFactory()

    def test_get_queryset(self):
        org = OrganizationFactory()
        normal_admin = make_admin(username='normal_admin', is_superuser=False)

        oa = OrganizationAdmin(Organization, self.site)
        request = self.factory.get('/fake-url/')

        # test against superuser admin
        request.user = self.admin
        qs = oa.get_queryset(request)
        self.assertQuerysetEqual(qs, [repr(self.organization), repr(org)], ordered=False)

        # test against non-superuser admin
        request.user = normal_admin
        qs = oa.get_queryset(request)
        self.assertQuerysetEqual(qs, [])

        self.organization.admin_users.add(normal_admin)
        qs = oa.get_queryset(request)
        self.assertQuerysetEqual(qs, [repr(self.organization)])

        org.admin_users.add(normal_admin)
        qs = oa.get_queryset(request)
        self.assertQuerysetEqual(qs, [repr(self.organization), repr(org)], ordered=False)

    def test_save_model(self):
        oa = OrganizationAdmin(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        organization_class = OrganizationClassFactory()
        organization = OrganizationFactory.build(classification=organization_class)
        oa.save_model(request, organization, None, None)
        self.assertEqual(organization.created_by, self.admin)
        self.assertEqual(organization.last_modified_by, self.admin)

        another_admin = make_admin(username='another_admin')
        request.user = another_admin
        oa.save_model(request, organization, None, None)
        self.assertEqual(organization.created_by, self.admin)
        self.assertEqual(organization.last_modified_by, another_admin)

    def test_indented_title(self):
        oa = OrganizationAdmin(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        self.assertNotIn('color: red;', oa.indented_title(self.organization))

        affiliated_org = OrganizationFactory(internal_type=Organization.AFFILIATED, parent=self.organization)
        self.assertIn('color: red;', oa.indented_title(affiliated_org))

    def test_has_change_permission(self):
        normal_admin = make_admin(username='normal_admin', is_superuser=False)

        oa = OrganizationAdmin(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = normal_admin

        has_perm = oa.has_change_permission(request)
        self.assertFalse(has_perm)

        clear_user_perm_cache(normal_admin)
        perm = Permission.objects.get(codename='change_affiliated_organization')
        normal_admin.user_permissions.add(perm)

        has_perm = oa.has_change_permission(request)
        self.assertTrue(has_perm)

    def test_get_actions(self):
        normal_admin = make_admin(username='normal_admin', is_superuser=False)

        oa = OrganizationAdmin(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = normal_admin

        actions = oa.get_actions(request)
        self.assertNotIn('delete_selected', actions)

        clear_user_perm_cache(normal_admin)
        perm = Permission.objects.get(codename='delete_organization')
        normal_admin.user_permissions.add(perm)

        actions = oa.get_actions(request)
        self.assertIn('delete_selected', actions)

    def test_get_readonly_fields(self):
        normal_admin = make_admin(username='normal_admin', is_superuser=False)

        oa = OrganizationAdmin(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = normal_admin

        form_base_fields = OrganizationForm.base_fields
        oa_readonly_fields = OrganizationAdmin.readonly_fields

        fields = oa.get_readonly_fields(request)
        self.assertEqual(fields, oa_readonly_fields)

        fields = oa.get_readonly_fields(request, self.organization)
        self.assertEqual(fields, form_base_fields)

        clear_user_perm_cache(normal_admin)
        perm = Permission.objects.get(codename='change_organization')
        normal_admin.user_permissions.add(perm)

        fields = oa.get_readonly_fields(request)
        self.assertEqual(fields, oa_readonly_fields)

        fields = oa.get_readonly_fields(request, self.organization)
        self.assertEqual(fields, oa_readonly_fields)
