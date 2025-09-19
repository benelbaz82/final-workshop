import re

with open('/app/statuspage/statuspage/settings.py', 'r') as f:
    content = f.read()

# Replace the ElastiCache check with always true
content = re.sub(r'if not TASKS_REDIS_HOST\.endswith\(\'\.cache\.amazonaws\.com\'\):', 'if True:  # Force RQ setup for ElastiCache', content)

# Remove the else block that sets RQ_QUEUES to empty
content = re.sub(r'else:\s*# For ElastiCache, don\'t set up any RQ queues to avoid authentication issues\s*RQ_QUEUES = \{\}\s*print\(\"Warning: Skipping RQ queue setup for ElastiCache \(no authentication support\)\"\)', '', content, flags=re.MULTILINE | re.DOTALL)

with open('/app/statuspage/statuspage/settings.py', 'w') as f:
    f.write(content)

print('Settings.py modified successfully')