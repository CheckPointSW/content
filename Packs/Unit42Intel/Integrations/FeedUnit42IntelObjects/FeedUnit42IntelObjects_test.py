import json

import pytest
from FeedUnit42IntelObjects import Client, fetch_indicators_command, incremental_level_fetch


def util_load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.loads(f.read())


def test_build_iterator(mocker):
    """
    Given:
        - Output of the feed API
    When:
        - When calling fetch_indicators or get_indicators
    Then:
        - Returns a list of the indicators parsed from the API's response
    """

    client = Client(api_key="1234", base_url="url", verify=False, proxy=False)
    mocker.patch.object(client, "get_tags", return_value=util_load_json("test_data/all_tags_result.json"))
    mocker.patch.object(client, "get_tag_details", return_value={"tag": []})
    indicators = client.build_iterator(is_get_command=True)
    assert len(indicators) == 2


def test_fetch_indicators(mocker):
    """
    Given:
        - Output of the feed API as list
    When:
        - Fetching indicators from the API
    Then:
        - Create indicator objects list
    """

    client = Client(api_key="1234", base_url="url", verify=False, proxy=False)
    mocker.patch.object(client, "build_iterator", return_value=util_load_json("test_data/build_iterator_results.json"))
    actual_results = fetch_indicators_command(client, params={"tlp_color": "RED"})[0]
    expected_results = util_load_json("test_data/fetch_indicators_results.json")[0]
    assert actual_results["type"] == expected_results["type"]
    assert actual_results["value"] == expected_results["value"]
    assert actual_results["fields"] == expected_results["fields"]


def test_incremental_level_fetch(mocker):
    context = {"tags_need_to_be_fetched": [], "time_of_first_fetch": 133033333}
    client = Client(api_key="1234", base_url="url", verify=False, proxy=False)
    mocker.patch("FeedUnit42IntelObjects.get_integration_context", return_value=context)
    mocker.patch(
        "FeedUnit42IntelObjects.get_all_updated_tags_since_last_fetch", return_value=[{"publictag_name": "Mock.mocktag1"}]
    )  # noqa: E501
    mocker.patch.object(client, "get_tag_details", return_value=util_load_json("test_data/tag_details_result.json"))
    actual_result = incremental_level_fetch(client)
    assert actual_result == [util_load_json("test_data/tag_details_result.json")]


def test_user_secrets():
    from FeedUnit42IntelObjects import LOG, Client

    client = Client(api_key="%%This_is_API_key%%", base_url="url", verify=False, proxy=False)
    res = LOG(client.headers)
    assert "%%This_is_API_key%%" not in res


def test_validate_created_time_from_refs():
    from FeedUnit42IntelObjects import validate_created_time_from_refs

    tags = util_load_json("test_data/build_iterator_results.json")
    for tag in tags:
        refs = json.loads(tag.get("tag", {}).get("refs", ""))[0]
        created = refs.get("created", "")
        res = validate_created_time_from_refs(created)
        assert res == f"{created}Z"


@pytest.mark.parametrize(
    "created, expected_result",
    [
        ("2016--08-10T14:27:05", "2016-08-10T14:27:05Z"),
        ("2016", "2016-01-01T00:00:00Z"),
        ("1-1", "1970-01-01T00:00:00Z"),
        ("Test wrong format", ""),
    ],
)
def test_validate_created_time_from_refs_incorrect_format(created, expected_result):
    from FeedUnit42IntelObjects import validate_created_time_from_refs

    res = validate_created_time_from_refs(created)
    assert res == expected_result
