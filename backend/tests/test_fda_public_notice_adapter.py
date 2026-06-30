import httpx
import pytest

from app.services.safety_source_adapters.fda_public import FDAPublicRecallsAdapter


TABLE_HTML = """
<table>
  <tr>
    <th>Date</th><th>Brand Name</th><th>Product Description</th>
    <th>Product Type</th><th>Recall Reason Description</th>
    <th>Company Name</th><th>Terminated Recall</th>
  </tr>
  <tr>
    <td>06/10/2026</td>
    <td>Fry Pie Factory</td>
    <td><a href="/safety/notices/pepperoni-rolls">Pepperoni Rolls</a></td>
    <td>Food &amp; Beverages</td>
    <td>Labeling issue</td>
    <td>Fry Pie Factory LLC</td>
    <td>No</td>
  </tr>
</table>
"""

DETAIL_HTML = """
<html><body><main>
  <h1>Fry Pie Factory recalls Pepperoni Rolls</h1>
  <p>The company recalled the product due to undeclared milk, a known allergen.</p>
  <p>Consumers should return the product to the place of purchase for a refund.</p>
  <p>The affected packages were distributed through retail stores and should not be consumed.
  Customers can compare the exact product and package details on the official notice before
  returning the item.</p>
</main></body></html>
"""


@pytest.mark.anyio
async def test_fda_public_notice_matches_official_detail_body_text(monkeypatch):
    async def fake_get(self, url, params=None):
        request = httpx.Request("GET", str(url))
        if str(url).endswith("/safety/notices/pepperoni-rolls"):
            return httpx.Response(200, text=DETAIL_HTML, request=request)
        return httpx.Response(200, text=TABLE_HTML, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    result = await FDAPublicRecallsAdapter().search(
        query="undeclared milk",
        limit=5,
    )

    assert result.upstream_status == "success"
    assert len(result.records) == 1
    record = result.records[0]
    assert record.source_kind == "normalized_public_notice"
    assert record.product_name == "Pepperoni Rolls"
    assert record.record_url == "https://www.fda.gov/safety/notices/pepperoni-rolls"
    assert "undeclared milk" in (record.reason or "").lower()
    assert "return the product" in (record.remedy or "").lower()
    assert record.extraction_confidence in {"high", "medium"}
