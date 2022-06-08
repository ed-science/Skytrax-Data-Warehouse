from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.contrib.hooks.aws_hook import AwsHook


class SourceToRedshiftOperator(BaseOperator):
    ui_color = '#358140'
    copy_sql = """
            COPY {} {}
            FROM '{}'
            ACCESS_KEY_ID '{}'
            SECRET_ACCESS_KEY '{}'
            {};
        """

    @apply_defaults
    def __init__(self,
                 table="",
                 columns="",
                 redshift_conn_id="",
                 aws_credentials_id="",
                 s3_bucket="",
                 s3_key="",
                 copy_extra="",
                 # Define your operators params (with defaults) here
                 # Example:
                 # redshift_conn_id=your-connection-name
                 *args, **kwargs):
        super(SourceToRedshiftOperator, self).__init__(*args, **kwargs)

        self.table = table
        self.columns = columns
        self.redshift_conn_id = redshift_conn_id
        self.aws_credentials_id = aws_credentials_id
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.copy_extra = copy_extra

    # Map params here
    # Example:
    # self.conn_id = conn_id

    def execute(self, context):
        aws_hook = AwsHook(aws_conn_id=self.aws_credentials_id)
        credentials = aws_hook.get_credentials()
        redshift = PostgresHook(postgres_conn_id=self.redshift_conn_id)

        self.log.info("Clearing data from destination Redshift table")
        redshift.run(f"DELETE FROM {self.table}")

        self.log.info("Copying data from S3 to Redshift")
        rendered_key = self.s3_key.format(**context)
        s3_path = f"s3://{self.s3_bucket}/{rendered_key}"
        cols = f"({self.columns})"
        formatted_sql = SourceToRedshiftOperator.copy_sql.format(
            self.table,
            cols,
            s3_path,
            credentials.access_key,
            credentials.secret_key,
            self.copy_extra
        )
        redshift.run(formatted_sql)