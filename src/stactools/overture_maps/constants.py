from datetime import datetime, timezone

AZURE_NETLOC = "overturemapswestus2.blob.core.windows.net"
S3_NETLOC = "overturemaps-us-west-2"
FIRST_RELEASE_DATE = datetime(year=2023, month=7, day=26, tzinfo=timezone.utc)
PARTITION_FORMAT = (
    "/release/{release}/theme={theme}/type={type}/part-{part}-{uid}.zstd.parquet"
)
COLLECTION_ID_FORMAT = "overture-maps-{theme}"

ODBL_LICENSE_ATTRIBUTES = {
    "href": "https://opendatacommons.org/licenses/odbl/1.0/",
    "title": "ODbL 1.0",
    "type": "text/html",
}
