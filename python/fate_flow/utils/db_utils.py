def get_dynamic_db_model(base, job_id):
    return type(base.model(table_index=get_dynamic_tracking_table_index(job_id=job_id)))


def get_dynamic_tracking_table_index(job_id):
    return job_id[:8]