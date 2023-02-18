import pytest
import external_bulk_ingest


def test_can_load_gzip_file_and_read_lines():
    bucket =  "raw-products-amazon"
    name = "Books_small.json.gz"

    bulk_ingest = external_bulk_ingest.BulkIngest()
    blob = bulk_ingest.get_blob_reference(bucket, name)

