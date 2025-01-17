import pendulum

from swimlane.core.resolver import SwimlaneResolver
from swimlane.utils.version import requires_swimlane_version
from swimlane.utils.list_validator import validate_str_list
from swimlane.utils.str_validator import validate_str


class HelperAdapter(SwimlaneResolver):
    """Adapter providing any miscellaneous API calls not better suited for another adapter"""

    @requires_swimlane_version('2.15')
    def add_record_references(self, app_id, record_id, field_id, target_record_ids):
        """Bulk operation to directly add record references without making any additional requests

        Warnings:
            Does not perform any app, record, or target app/record validation

        Args:
            app_id (str): Full App ID string
            record_id (str): Full parent Record ID string
            field_id (str): Full field ID to target reference field on parent Record string
            target_record_ids (List(str)): List of full target reference Record ID strings
        """
        validate_str_list(target_record_ids, "target_record_ids")

        self._swimlane.request(
            'post',
            'app/{0}/record/{1}/add-references'.format(app_id, record_id),
            json={
                'fieldId': field_id,
                'targetRecordIds': target_record_ids
            }
        )

    def add_comment(self, app_id, record_id, field_id, message, rich_text=False):
        """Directly add a comment to a record without retrieving the app or record first

        Warnings:
            Does not perform any app, record, or field ID validation

        Args:
            app_id (str): Full App ID string
            record_id (str): Full parent Record ID string
            field_id (str): Full field ID to target reference field on parent Record string
            message (str): New comment message body
            rich_text (bool): Declare the message as being rich text, default is False
        """
        validate_str(app_id, 'app_id')
        validate_str(record_id, 'record_id')
        validate_str(field_id, 'field_id')
        validate_str(message, 'message')
        
        if not isinstance(rich_text, bool):
            raise ValueError("rich_text must be a boolean value.")

        self._swimlane.request(
            'post',
            'app/{0}/record/{1}/{2}/comment'.format(
                app_id,
                record_id,
                field_id
            ),
            json={
                'message': message,
                'isRichText': rich_text,
                'createdDate': pendulum.now().to_rfc3339_string()
            }
        )

    def check_bulk_job_status(self, job_id):
        """Check status of bulk_delete or bulk_modify jobs
        .. versionadded:: 2.17.0
        Args:
            job_id (str): Job ID

        Returns:
            :class:`list` of :class:`dict`: List of dictionaries containing job history

        """
        
        validate_str(job_id, 'job_id')

        return self._swimlane.request('get', "logging/job/{0}".format(job_id)).json()
