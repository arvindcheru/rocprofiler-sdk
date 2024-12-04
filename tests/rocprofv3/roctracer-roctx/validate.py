#!/usr/bin/env python3

import sys
import pytest


def test_marker_api_trace(json_data):
    data = json_data["rocprofiler-sdk-tool"]

    def get_kind_name(kind_id):
        return data["strings"]["buffer_records"][kind_id]["kind"]

    def get_region_name(corr_id):
        for itr in data["strings"]["marker_api"]:
            if itr.key == corr_id:
                return itr.value
        return None

    valid_domain = ("MARKER_CORE_API", "MARKER_CONTROL_API", "MARKER_NAME_API")

    buffer_records = data["buffer_records"]
    marker_data = buffer_records["marker_api"]
    tot_data = {}
    thr_data = {}
    for marker in marker_data:
        assert get_kind_name(marker["kind"]) in valid_domain
        assert marker.thread_id >= data["metadata"]["pid"]
        assert marker.end_timestamp >= marker.start_timestamp

        if marker.thread_id not in thr_data.keys():
            thr_data[marker.thread_id] = {}

        corr_id = marker.correlation_id.internal
        assert corr_id > 0, f"{marker}"
        name = get_region_name(corr_id)
        if not name.startswith("roctracer/roctx"):
            assert "run" in name, f"{marker}"
            if name not in thr_data[marker.thread_id].keys():
                thr_data[marker.thread_id][name] = 1
            else:
                thr_data[marker.thread_id][name] += 1

        if name not in tot_data.keys():
            tot_data[name] = 1
        else:
            tot_data[name] += 1

    assert tot_data["roctracer/roctx v4.1"] == 1
    assert tot_data["run"] == 2
    assert tot_data["run/iteration"] == 1000
    assert tot_data["run/iteration/sync"] == 100
    assert tot_data["run/rank-0/thread-0/device-0/begin"] == 1
    assert tot_data["run/rank-0/thread-0/device-0/end"] == 1
    assert len(tot_data.keys()) >= 8

    for tid, titr in thr_data.items():
        assert titr["run"] == 1
        assert titr["run/iteration"] == 500
        assert titr["run/iteration/sync"] == 50
        assert len(titr.keys()) >= 5


def test_perfetto_data(pftrace_data, json_data):
    import rocprofiler_sdk.tests.rocprofv3 as rocprofv3

    rocprofv3.test_perfetto_data(pftrace_data, json_data, ("memory_copy", "marker"))


def test_otf2_data(otf2_data, json_data):
    import rocprofiler_sdk.tests.rocprofv3 as rocprofv3

    rocprofv3.test_otf2_data(otf2_data, json_data, ("memory_copy", "marker"))


if __name__ == "__main__":
    exit_code = pytest.main(["-x", __file__] + sys.argv[1:])
    sys.exit(exit_code)
