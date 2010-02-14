import unittest

from zope.interface import alsoProvides
from zope.interface import directlyProvides
from zope.interface import noLongerProvides

from Products.CMFPlone.interfaces import INonStructuralFolder

from plone.app.layout.viewlets.tests.base import ViewletsTestCase
from plone.app.layout.viewlets.common import ViewletBase
from plone.app.layout.viewlets.common import ContentViewsViewlet
from plone.app.layout.navigation.interfaces import INavigationRoot


class TestViewletBase(ViewletsTestCase):
    """Test the base class for the viewlets.
    """

    def test_update(self):
        request = self.app.REQUEST
        self.setRoles(['Manager', 'Member'])
        self.portal.invokeFactory('Folder', 'f1')
        context = getattr(self.portal, 'f1')
        alsoProvides(context, INavigationRoot)
        viewlet = ViewletBase(context, request, None, None)
        viewlet.update()
        self.assertEqual(viewlet.site_url, "http://nohost/plone")
        self.assertEqual(viewlet.navigation_root_url, "http://nohost/plone/f1")


class TestContentViewsViewlet(ViewletsTestCase):
    """Test the content views viewlet.
    """

    def afterSetUp(self):
        self.folder.invokeFactory('Document', 'test',
                                  title='Test default page')

    def _invalidateRequestMemoizations(self):
        try:
            del self.app.REQUEST.__annotations__
        except AttributeError:
            pass

    def testPrepareObjectTabsOnPortalRoot(self):
        self._invalidateRequestMemoizations()
        self.loginAsPortalOwner()
        self.app.REQUEST['ACTUAL_URL'] = self.portal.absolute_url()
        view = ContentViewsViewlet(self.portal, self.app.REQUEST, None)
        tabs = view.prepareObjectTabs()
        self.assertEquals(tabs[0]['id'], 'folderContents')
        self.assertEquals(['view'], [t['id'] for t in tabs if t['selected']])

    def testPrepareObjectTabsNonFolder(self):
        self._invalidateRequestMemoizations()
        self.loginAsPortalOwner()
        self.app.REQUEST['ACTUAL_URL'] = self.folder.test.absolute_url()
        view = ContentViewsViewlet(self.folder.test, self.app.REQUEST, None)
        tabs = view.prepareObjectTabs()
        self.assertEquals(0, len([t for t in tabs if t['id'] == 'folderContents']))
        self.assertEquals(['view'], [t['id'] for t in tabs if t['selected']])

    def testPrepareObjectTabsNonStructuralFolder(self):
        self._invalidateRequestMemoizations()
        self.loginAsPortalOwner()
        self.app.REQUEST['ACTUAL_URL'] = self.folder.absolute_url()
        directlyProvides(self.folder, INonStructuralFolder)
        view = ContentViewsViewlet(self.folder, self.app.REQUEST, None)
        tabs = view.prepareObjectTabs()
        noLongerProvides(self.folder, INonStructuralFolder)
        self.assertEquals(0, len([t for t in tabs if t['id'] == 'folderContents']))
        self.assertEquals(['view'], [t['id'] for t in tabs if t['selected']])

    def testPrepareObjectTabsDefaultView(self):
        self._invalidateRequestMemoizations()
        self.loginAsPortalOwner()
        self.app.REQUEST['ACTUAL_URL'] = self.folder.test.absolute_url() + '/edit'
        view = ContentViewsViewlet(self.folder.test, self.app.REQUEST, None)
        tabs = view.prepareObjectTabs()
        self.assertEquals(0, len([t for t in tabs if t['id'] == 'folderContents']))
        self.assertEquals(['edit'], [t['id'] for t in tabs if t['selected']])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestViewletBase))
    suite.addTest(unittest.makeSuite(TestContentViewsViewlet))
    return suite
