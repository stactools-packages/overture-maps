INSTALL SPATIAL;
INSTALL azure;

LOAD spatial; --noqa

SET azure_storage_connection_string = 'DefaultEndpointsProtocol=https;AccountName=overturemapswestus2;AccountKey=;EndpointSuffix=core.windows.net';
SET azure_transport_option_type = 'curl';

COPY(
  SELECT
    *
  FROM read_parquet('azure://release/2024-12-18.0/theme=buildings/type=building/*', filename=true, hive_partitioning=1)
  WHERE filename = 'azure://release/2024-12-18.0/theme=buildings/type=building/part-00000-35685b01-5d46-4cb5-8449-5b27bcbfe445-c000.zstd.parquet'
  LIMIT 1000
) TO '/tmp/buildings.zstd.parquet';

