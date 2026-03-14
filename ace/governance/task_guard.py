MAX_ATTEMPTS = 3

task_attempts = {}

def allow_task(task_id):

    count = task_attempts.get(task_id,0)

    if count >= MAX_ATTEMPTS:
        return False

    task_attempts[task_id] = count + 1
    return True
