# This Python file uses the following encoding: utf-8
"""
api.py is an interface module for Python-level integration with the
edx-organizations app.

In the current incarnation of this particular application, the API
operations are equivalent to the orchestration layer, which manages
the application's workflows.
"""
import logging

from django.conf import settings

from . import data
from . import exceptions
from . import validators


log = logging.getLogger(__name__)


# PRIVATE/INTERNAL FUNCTIONS

def _validate_course_key(course_key):
    """ Validation helper """
    if not validators.course_key_is_valid(course_key):
        exceptions.raise_exception(
            "CourseKey",
            course_key,
            exceptions.InvalidCourseKeyException
        )


def _validate_organization_data(organization_data):
    """ Validation helper """
    if not validators.organization_data_is_valid(organization_data):
        exceptions.raise_exception(
            "Organization",
            organization_data,
            exceptions.InvalidOrganizationException
        )


# PUBLIC FUNCTIONS
def add_organization(organization_data):
    """
    Passes a new organization to the data layer for storage
    """
    _validate_organization_data(organization_data)
    organization = data.create_organization(organization_data)
    return organization


def edit_organization(organization_data):
    """
    Passes an updated organization to the data layer for storage
    """
    _validate_organization_data(organization_data)
    return data.update_organization(organization_data)


def get_organization(organization_id):
    """
    Retrieves the specified organization
    """
    return data.fetch_organization(organization_id)


def get_organization_by_short_name(organization_short_name):
    """
    Retrieves the organization filtered by short name
    """
    return data.fetch_organization_by_short_name(organization_short_name)


def get_organizations():
    """
    Retrieves the active organizations managed by the system
    """
    return data.fetch_organizations()


def remove_organization(organization_id):
    """
    Removes the specified organization
    """
    organization = {
        'id': organization_id,
    }
    data.delete_organization(organization)


def add_organization_course(organization_data, course_key):
    """
    Adds a organization-course link to the system
    """
    _validate_course_key(course_key)
    _validate_organization_data(organization_data)
    data.create_organization_course(
        organization=organization_data,
        course_key=course_key
    )


def get_organization_courses(organization_data):
    """
    Retrieves the set of courses for a given organization
    Returns an array of course identifiers
    """
    _validate_organization_data(organization_data)
    return data.fetch_organization_courses(organization=organization_data)


def remove_organization_course(organization, course_key):
    """
    Removes the specfied course from the specified organization
    """
    _validate_organization_data(organization)
    _validate_course_key(course_key)
    return data.delete_organization_course(course_key=course_key, organization=organization)


def get_course_organizations(course_key):
    """
    Retrieves the set of organizations for a given course
    Returns an array of dicts containing organizations
    """
    _validate_course_key(course_key)
    return data.fetch_course_organizations(course_key=course_key)


def get_course_organization(course_key):
    """
    Returns the first organization linked to a given course,
    or None if the course is not linked to any organizations.
    """
    _validate_course_key(course_key)
    course_organization = get_course_organizations(course_key)
    if course_organization:
        return course_organization[0]
    return None


def get_course_organization_id(course_key):
    """
    Returns the id of the first organization linked to a given course,
    or None if the course is not linked to any organizations.
    """
    course_org = get_course_organization(course_key)
    return course_org["id"] if course_org else None


def remove_course_references(course_key):
    """
    Removes course references from application state
    See edx-platform/lms/djangoapps/courseware/management/commands/delete_course_references.py
    """
    _validate_course_key(course_key)
    data.delete_course_references(course_key)


def ensure_organization(organization_short_name):
    """
    Ensure that an organization with the given short name exists.

    If the organization exists, then return it.
    If the organization does not exist, then:
        (a) If auto-create is enabled, create & return a new organization.
        (b) If auto-create is disabled, raise an InvalidOrganizationException.

    Arguments:
        organization_short_name (str)

    Returns: dict
        dictionary containing organization data

    Raises:
        InvalidOrganizationException (only if auto-create is disabled)
    """
    try:
        return get_organization_by_short_name(organization_short_name)
    except exceptions.InvalidOrganizationException:
        if not is_autocreate_enabled():
            raise
    log.info("Automatically creating new organization '%s'.", organization_short_name)
    return add_organization({
        "short_name": organization_short_name,
        "name": organization_short_name,
    })


def is_autocreate_enabled():
    """
    Return whether automatic organization creation is enabled.

    If True (default), calls to ``ensure_organization`` will auto-create organizations
    that do not already exist in the database.

    If False, calls to ``ensure_organization`` will fail for organizations that are not
    already in the database.
    """
    try:
        return bool(settings.ORGANIZATIONS_AUTOCREATE)
    except AttributeError:
        pass
    # TODO DEPR-117
    # ORGANIZATIONS_APP is the (soon-to-be-)deprecated feature flag
    # that enabled edx-organizations in edx-platform.
    # To ease migration, we accept the enabling of the old feature flag as a way of
    # disabling automatic organization creation.
    try:
        features = settings.FEATURES
    except AttributeError:
        features = {}
    old_organizations_flag_enabled = bool(features.get('ORGANIZATIONS_APP', False))
    return not old_organizations_flag_enabled
