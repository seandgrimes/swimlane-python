import itertools

import pendulum

from swimlane.core.resources.base import APIResource, SwimlaneResolver
from swimlane.core.search import CONTAINS, EQ, EXCLUDES, NOT_EQ


class ReportAdapter(SwimlaneResolver):

    def __init__(self, app):
        super(ReportAdapter, self).__init__(app._swimlane)

        self.app = app

    def list(self):
        """Retrieve all reports

        If app is specified, only reports that are a member of that App
        will be returned. By default, all reports in the system are returned.
        """
        raw_reports = self._swimlane.request('get', "reports?appId={}".format(self.app.id)).json()
        results = []
        for raw_report in raw_reports:
            try:
                results.append(Report(self.app, raw_report))
            except TypeError:
                # Ignore StatsReports for now
                pass

        return results

    def get(self, report_id):
        """Retrieve report by ID"""
        return Report(
            self.app,
            self._swimlane.request('get', "reports/{0}".format(report_id))
        )

    def create(self, name):
        """Get a new Report for the App designated by app_id.

        Args:
            app (str): The App or app id to search in.
            name (str): The name of the Report.

        Return:
            A prefilled Report.
        """
        #pylint: disable=protected-access
        created = pendulum.now().to_rfc3339_string()
        user_model = self._swimlane.user.get_usergroup_selection()

        return Report(self.app, {
            "$type": Report._type,
            "groupBys": [],
            "aggregates": [],
            "applicationIds": [self.app.id],
            "columns": list(self.app._fields_by_id.keys()),
            "sorts": {
                "$type": "System.Collections.Generic.Dictionary`2"
                         "[[System.String, mscorlib],"
                         "[Core.Models.Search.SortTypes, Core]], mscorlib",
            },
            "filters": [],
            "pageSize": Report._page_size,
            "offset": 0,
            "defaultSearchReport": False,
            "allowed": [],
            "permissions": {
                "$type": "Core.Models.Security.PermissionMatrix, Core"
            },
            "createdDate": created,
            "modifiedDate": created,
            "createdByUser": user_model,
            "modifiedByUser": user_model,
            "id": None,
            "name": name,
            "disabled": False,
            "keywords": ""
        })


class Report(APIResource):
    """A report class used for searching."""

    _type = "Core.Models.Search.Report, Core"

    _FILTER_OPERANDS = (
        EQ,
        NOT_EQ,
        CONTAINS,
        EXCLUDES
    )

    _page_size = 50

    def __init__(self, app, raw):
        super(Report, self).__init__(app._swimlane, raw)

        self.app = app
        self.name = self._raw['name']

        self.__records = []

    def __str__(self):
        return self.name

    def __iter__(self):
        if self.__records:
            for record in self.__records:
                yield record
        else:
            for page in itertools.count():
                result_data = self._retrieve_report_page(page)
                count = result_data['count']
                records = [self._build_record(raw_data) for raw_data in result_data['results'].get(self.app.id, [])]

                for result in records:
                    self.__records.append(result)
                    yield result

                if not records or page * self._page_size >= count:
                    break

    def save(self):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError

    def filter(self, field, operand, value):
        """Adds a filter to report from field name, comparison operand, and value"""
        if operand not in self._FILTER_OPERANDS:
            raise ValueError('Operand must be one of {}'.format(', '.join(self._FILTER_OPERANDS)))

        self._raw['filters'].append({
            "fieldId": self.app.get_field_definition_by_name(field)['id'],
            "filterType": operand,
            "value": value,
        })

    def aggregate(self, field, aggregation):
        raise NotImplementedError

    def group_by(self, field, period):
        raise NotImplementedError

    def clear_results(self):
        """Clear cached results from execution, allowing report to be rerun"""
        self.__records = []

    def _retrieve_report_page(self, page=0):
        """Retrieve paginated report results for an individual page"""
        report_data = self._swimlane.request('post', 'search', json=self._get_paginated_body(page)).json()

        return report_data

    def _build_record(self, raw_record_data):
        # Avoid circular imports
        from swimlane.core.resources import Record
        return Record(self.app, raw_record_data)

    def _get_paginated_body(self, page):
        """Return raw body content formatted with correct pagination and offset values for provided page"""
        body = self._raw.copy()

        body['pageSize'] = self._page_size
        body['offset'] = page

        return body
