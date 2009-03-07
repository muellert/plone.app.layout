import warnings
from zope.component import queryAdapter
from zope.component import queryUtility
from zope.interface import implements
from zope.publisher.browser import BrowserView

from Acquisition import aq_base
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFDynamicViewFTI.interface import IBrowserDefault
from Products.CMFDynamicViewFTI.interface import IDynamicViewTypeInformation
from Products.CMFPlone import utils

from plone.app.layout.navigation.interfaces import IDefaultPage

class DefaultPage(BrowserView):
    implements(IDefaultPage)

    def isDefaultPage(self, obj, context_=None):
        if context_ is not None:
            warnings.warn("The context_ parameter for isDefaultPage was never "
                          "implemented and will be removed in Plone 4.",
                          DeprecationWarning, 1)

        return isDefaultPage(self.context, obj)

    def getDefaultPage(self, context_=None):
        if context_ is not None:
            warnings.warn("The context_ parameter for getDefaultPage was "
                          "never implemented and will be removed in Plone 4.",
                          DeprecationWarning, 1)

        return getDefaultPage(self.context)


def isDefaultPage(container, obj):
    """Finds out if the given obj is the default page in its parent folder.

    Only considers explicitly contained objects, either set as index_html,
    with the default_page property, or using IBrowserDefault.
    """
    parentDefaultPage = getDefaultPage(container)
    if parentDefaultPage is None or '/' in parentDefaultPage:
        return False
    return (parentDefaultPage == obj.getId())


def getDefaultPage(context):
    """Given a folderish item, find out if it has a default-page using
    the following lookup rules:

        1. A content object called 'index_html' wins
        2. If the folder implements IBrowserDefault, query this
        3. Else, look up the property default_page on the object
            - Note that in this case, the returned id may *not* be of an
              object in the folder, since it could be acquired from a
              parent folder or skin layer
        4. Else, look up the property default_page in site_properties for
            magic ids and test these

    The id of the first matching item is then used to lookup a translation
    and if found, its id is returned. If no default page is set, None is
    returned. If a non-folderish item is passed in, return None always.
    """
    # The list of ids where we look for default
    ids = {}

    # For BTreeFolders we just use the has_key, otherwise build a dict
    if hasattr(aq_base(context), 'has_key'):
        ids = context
    else:
        for id in context.objectIds():
            ids[id] = 1

    # Inline function with default argument.
    def lookupTranslationId(obj, page):
        return utils.lookupTranslationId(obj, page, ids)

    # 1. test for contentish index_html
    if ids.has_key('index_html'):
        return lookupTranslationId(context, 'index_html')

    # 2. Test for IBrowserDefault
    if IBrowserDefault.providedBy(context):
        browserDefault = context
    else:
        browserDefault = queryAdapter(context, IBrowserDefault)

    if browserDefault is not None:
        fti = context.getTypeInfo()
        if fti is not None:
            if IDynamicViewTypeInformation.providedBy(fti):
                dynamicFTI = fti
            else:
                dynamicFTI = queryAdapter(fti, IDynamicViewTypeInformation)
            if dynamicFTI is not None:
                page = dynamicFTI.getDefaultPage(context, check_exists=True)
                if page is not None:
                    return lookupTranslationId(context, page)

    # 3. Test for default_page property in folder, then skins
    pages = getattr(aq_base(context), 'default_page', [])
    if isinstance(pages, basestring):
        pages = [pages]
    for page in pages:
        if page and ids.has_key(page):
            return lookupTranslationId(context, page)

    portal = queryUtility(ISiteRoot)
    # Might happen during portal creation
    if portal is not None:
        for page in pages:
            if portal.unrestrictedTraverse(page, None):
                return lookupTranslationId(context, page)

        # 4. Test for default sitewide default_page setting
        pp = getattr(portal, 'portal_properties', None)
        if pp is not None:
            site_properties = getattr(pp, 'site_properties', None)
            if site_properties is not None:
                for page in site_properties.getProperty('default_page', []):
                    if ids.has_key(page):
                        return lookupTranslationId(context, page)

    return None
